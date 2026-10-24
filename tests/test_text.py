import pytest

from bookcats.catalog import BY_KEY
from bookcats.emotions import aggregate_transformer, lexicon_scores, tokens
from bookcats.fetch import BookError, strip_gutenberg, validate
from bookcats.segment import n_segments, segments

GUTENBERG = """The Project Gutenberg eBook of Dracula
*** START OF THE PROJECT GUTENBERG EBOOK DRACULA ***
DRACULA
[Illustration: a castle]
It was a dark and stormy night.
*** END OF THE PROJECT GUTENBERG EBOOK DRACULA ***
Licence text that must disappear."""


def test_strip_gutenberg_keeps_only_the_book():
    text = strip_gutenberg(GUTENBERG)
    assert text.startswith("DRACULA")
    assert "Licence" not in text and "START OF" not in text and "[Illustration" not in text


def test_validate_rejects_empty_and_wrong_books():
    with pytest.raises(BookError):
        validate(BY_KEY["metamorphosis"], "")               # the empty cached file
    wrong = "The Mysteries of Udolpho. " + "word " * 10_000  # the wrong book behind a title search
    with pytest.raises(BookError):
        validate(BY_KEY["war_worlds"], wrong)
    validate(BY_KEY["dracula"], "DRACULA by Bram Stoker. " + "word " * 10_000)


def test_segments_cover_the_whole_text_equally():
    text = " ".join(f"w{i}" for i in range(1000))
    segs = segments(text, 10)
    assert len(segs) == 10
    assert sum(len(s.split()) for s in segs) == 1000
    assert {len(s.split()) for s in segs} == {100}


def test_n_segments_scales_with_length():
    assert n_segments("word " * 10_000) == 20          # floor for short books
    assert n_segments("word " * 90_000) == 60
    assert n_segments("word " * 1_000_000) == 100      # cap


def test_proper_nouns_in_mid_sentence_are_skipped():
    toks = tokens("Terror filled the room. I saw Count Dracula smile.")
    assert "terror" in toks          # capitalised, but at the start of a sentence
    assert "count" not in toks and "dracula" not in toks
    assert "smile" in toks


def test_lexicon_counts_emotions_and_ignores_ambiguous_words():
    scores = lexicon_scores("terror horror dread")
    assert scores["fear"] > 0
    neutral = lexicon_scores("found white mother court")  # tagged by the lexicon, neutral in context
    assert all(v == 0 for v in neutral.values())


def test_transformer_aggregation_drops_neutral():
    out = [[{"label": "neutral", "score": 0.9}, {"label": "fear", "score": 0.08},
            {"label": "joy", "score": 0.02}]]
    scores = aggregate_transformer(out)
    assert scores["fear"] == pytest.approx(0.8)
    assert scores["joy"] == pytest.approx(0.2)
