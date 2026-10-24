"""Emotion scoring of a whole book, segment by segment.

Two backends:
- "lexicon" (default): NRC Emotion Lexicon, counts emotion words in the FULL text.
  Fast (seconds), offline, deterministic, and every score can be traced back to words.
- "transformer" (optional): j-hartmann/emotion-english-distilroberta-base.
  More context-aware, slower, needs `pip install -e ".[transformer]"`.

Why not ask an LLM for a 1-10 score per chapter? LLM ratings are poorly calibrated
(scores jump between 2 and 8), the model only saw the first 3000 characters of each
chapter, and failures silently became zeros. Counting over the whole text fixes all three.
"""

from __future__ import annotations

import importlib.util
import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from .segment import n_segments, paragraphs, segments

# Emotions available in both backends. Lexicon adds trust/anticipation.
CORE = ["anger", "disgust", "fear", "joy", "sadness", "surprise"]
LEXICON_EXTRA = ["trust", "anticipation"]

_WORD = re.compile(r"[A-Za-z][A-Za-z'’]*")
_SENT_END = set(".!?:;\"“”'‘’_(—-")


# Very frequent words in 19th-century fiction that the lexicon tags with an
# emotion although they are neutral in context ("found", "white", "mother",
# "court"...). Found by listing the top contributing words per emotion
# (see `top_words`) and removing the ones that carry no emotion.
AMBIGUOUS = {
    "found", "white", "spoke", "words", "word", "case", "passed", "present", "young",
    "mother", "father", "aunt", "daughter", "child", "baby", "court", "jury", "witness",
    "diary", "sun", "deal", "really", "talking", "talk", "question", "garden", "sea",
    "eat", "watch", "change", "changed", "feeling", "feelings", "subject", "leave",
    "immediately", "mouth", "tree", "small", "late", "fell", "wait", "waited", "full",
    "rest", "larger", "grow", "growing", "lessons", "explain", "married", "marry",
    "fortune", "spirits", "god", "scarcely", "letter", "art", "music", "money", "ground",
    "boy", "girl", "doctor", "professor", "count", "sir", "lord", "lady",
    "jungle", "youth",
}
# Tags that are wrong for an otherwise useful word.
TAG_DROP = {
    "good": {"surprise", "anticipation"},
    "hope": {"surprise", "fear"},
    "death": {"surprise"},
    "sweet": {"surprise"},
}


@lru_cache(maxsize=1)
def load_lexicon() -> dict[str, list[str]]:
    spec = importlib.util.find_spec("nrclex")
    if spec is None or not spec.submodule_search_locations:
        raise RuntimeError("Install the lexicon with: pip install nrclex")
    path = Path(spec.submodule_search_locations[0]) / "data" / "nrc_en.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    lex = {}
    for word, tags in raw.items():
        if word in AMBIGUOUS:
            continue
        drop = TAG_DROP.get(word, set())
        lex[word] = [t for t in tags if t not in drop]
    return lex


def _lookup(word: str, lex: dict[str, list[str]]) -> list[str] | None:
    """Very small lemmatizer: try the word, then common inflections."""
    if word in lex:
        return lex[word]
    for suffix, repl in (("ies", "y"), ("ied", "y"), ("es", ""), ("s", ""), ("ed", ""),
                         ("ed", "e"), ("ing", ""), ("ing", "e"), ("ly", ""), ("ness", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            base = word[: -len(suffix)] + repl
            if base in lex:
                return lex[base]
    return None


def tokens(text: str) -> list[str]:
    """Lower-cased words, skipping capitalised words in mid-sentence (proper nouns).

    Without this, names bias the scores: "Count Dracula", "Mr. Darcy",
    "the Queen" would all be read as emotion words.
    """
    out = []
    for m in _WORD.finditer(text):
        w = m.group()
        if w[0].isupper() and w != "I":
            j = m.start() - 1
            while j >= 0 and text[j].isspace():
                j -= 1
            at_sentence_start = j < 0 or text[j] in _SENT_END
            if not at_sentence_start:
                continue
        out.append(w.lower().replace("’", "'"))
    return out


def top_words(text: str, emotion: str, k: int = 6) -> list[str]:
    """The words that contribute most to an emotion: used to explain each cat."""
    from collections import Counter

    lex = load_lexicon()
    counter: Counter[str] = Counter()
    for t in tokens(text):
        tags = _lookup(t, lex)
        if tags and emotion in tags:
            counter[t] += 1
    return [w for w, _ in counter.most_common(k)]


def lexicon_scores(text: str) -> dict[str, float]:
    """Emotion words per 1000 words for one segment."""
    lex = load_lexicon()
    toks = tokens(text)
    counts = dict.fromkeys(CORE + LEXICON_EXTRA + ["positive", "negative"], 0)
    for t in toks:
        tags = _lookup(t, lex)
        if tags:
            for tag in tags:
                if tag in counts:
                    counts[tag] += 1
    n = max(len(toks), 1)
    return {k: 1000 * v / n for k, v in counts.items()}


class TransformerScorer:
    MODEL = "j-hartmann/emotion-english-distilroberta-base"

    def __init__(self):
        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError('Install the extra: pip install -e ".[transformer]"') from exc
        self.clf = pipeline("text-classification", model=self.MODEL, top_k=None, truncation=True)

    def __call__(self, text: str, sample: int | None = 8) -> dict[str, float]:
        chunks = paragraphs(text)
        if sample and len(chunks) > sample:
            idx = np.linspace(0, len(chunks) - 1, sample).round().astype(int)
            chunks = [chunks[i] for i in idx]
        return aggregate_transformer(self.clf(chunks))


def aggregate_transformer(outputs: list[list[dict]]) -> dict[str, float]:
    """Average the per-chunk probabilities, renormalised WITHOUT 'neutral'.

    'neutral' dominates most literary prose and would flatten every curve.
    """
    acc = dict.fromkeys(CORE, 0.0)
    for out in outputs:
        probs = {d["label"]: d["score"] for d in out}
        total = sum(probs.get(e, 0.0) for e in CORE) or 1.0
        for e in CORE:
            acc[e] += probs.get(e, 0.0) / total
    n = max(len(outputs), 1)
    scores = {e: v / n for e, v in acc.items()}
    scores["positive"] = scores["joy"] + 0.5 * scores["surprise"]
    scores["negative"] = scores["anger"] + scores["disgust"] + scores["fear"] + scores["sadness"]
    return scores


def score_book(text: str, backend: str = "lexicon", n: int | None = None) -> list[dict[str, float]]:
    if backend == "lexicon":
        scorer = lexicon_scores
    elif backend == "transformer":
        scorer = TransformerScorer()
    else:
        raise ValueError(f"unknown backend {backend!r}")
    return [scorer(seg) for seg in segments(text, n or n_segments(text))]


def valence(seg_scores: list[dict[str, float]]) -> np.ndarray:
    """Positive minus negative, scaled to [-1, 1] per segment."""
    pos = np.array([s["positive"] for s in seg_scores])
    neg = np.array([s["negative"] for s in seg_scores])
    return (pos - neg) / np.maximum(pos + neg, 1e-9)
