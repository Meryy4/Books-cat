"""Writing style and setting, measured directly on the text (no model needed)."""

import re
from collections import Counter

import numpy as np

_SENT = re.compile(r"[^.!?]+[.!?]+")
_QUOTED = re.compile(r"“[^”]{1,2000}”|\"[^\"\n]{1,2000}\"")
_WORD = re.compile(r"[a-z]+")

# Keyword families used to guess where the story takes place.
SETTINGS: dict[str, set[str]] = {
    "gothic": {"castle", "tomb", "crypt", "vault", "coffin", "grave", "graves", "churchyard",
               "ruin", "ruins", "chapel", "candle", "candles", "bat", "bats", "wolves", "mist"},
    "sea": {"sea", "ship", "ships", "waves", "sail", "sailed", "ocean", "shore", "harbour",
            "deck", "voyage", "boat", "tide", "captain"},
    "wild": {"jungle", "forest", "trees", "wolf", "wolves", "hills", "rocks", "river",
             "cave", "leaves", "grass", "hunting", "pack", "den", "mountains", "glacier"},
    "city": {"street", "streets", "london", "paris", "crowd", "shop", "shops", "carriage",
             "cab", "square", "lamps", "bridge", "prison", "mob", "barrier"},
    "drawing_room": {"ball", "dance", "dancing", "drawing", "parlour", "visit", "visits",
                     "dinner", "tea", "estate", "neighbourhood", "sisters", "gentleman", "manners"},
    "wonder": {"rabbit", "queen", "king", "dream", "curious", "hatter", "caterpillar",
               "wonderland", "cat", "tarts", "croquet", "tea-party", "magic"},
    "machine": {"machine", "experiment", "science", "laboratory", "invention", "future",
                "engine", "lever", "apparatus", "electricity", "dimension", "traveller"},
}


# Literal light/dark imagery. The emotion lexicon alone misses that Dracula is a
# dark book: its letters and diaries are full of "dear", "friend", "love".
DARK_IMAGERY = {"night", "nights", "dark", "darkness", "darkly", "black", "blood", "bloody", "death",
                "dead", "grave", "graves", "tomb", "shadow", "shadows", "shadowy", "gloom", "gloomy",
                "cold", "ghost", "ghastly", "horror", "terror", "despair", "midnight", "storm", "grim",
                "corpse", "wolf", "wolves", "dread", "fearful", "doom", "cruel"}
LIGHT_IMAGERY = {"light", "bright", "brightly", "sun", "sunshine", "sunny", "sunlight", "morning",
                 "dawn", "golden", "smile", "smiled", "smiling", "laugh", "laughed", "laughing", "warm",
                 "flowers", "spring", "summer", "joy", "happy", "happiness", "delight", "delighted",
                 "cheerful", "merry", "glad", "lovely", "pretty", "charming"}


def imagery(text: str) -> dict[str, float]:
    counts = Counter(_WORD.findall(text.lower()))
    dark = sum(counts[w] for w in DARK_IMAGERY)
    light = sum(counts[w] for w in LIGHT_IMAGERY)
    return {"dark": dark, "light": light, "dark_ratio": dark / max(dark + light, 1)}


def style_features(text: str) -> dict[str, float]:
    words = text.split()
    n_words = max(len(words), 1)
    sentences = _SENT.findall(text)
    sent_lens = [len(s.split()) for s in sentences if s.strip()]
    quoted_words = sum(len(q.split()) for q in _QUOTED.findall(text))

    lower = _WORD.findall(text.lower())
    window = 1000
    ttrs = [len(set(lower[i:i + window])) / window
            for i in range(0, max(len(lower) - window, 1), window)] or [0.0]

    return {
        "sentence_len": float(np.median(sent_lens)) if sent_lens else 0.0,
        "dialogue": quoted_words / n_words,
        "exclaim": 1000 * text.count("!") / n_words,
        "question": 1000 * text.count("?") / n_words,
        "richness": float(np.mean(ttrs)),
    }


def setting_scores(text: str) -> dict[str, float]:
    """Keyword hits per 10,000 words for each setting family."""
    counts = Counter(_WORD.findall(text.lower()))
    n = max(sum(counts.values()), 1)
    return {name: 10_000 * sum(counts[w] for w in kws) / n for name, kws in SETTINGS.items()}
