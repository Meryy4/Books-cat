"""Split a book into equal-length segments.

Splitting on "CHAPTER" headings fails on books that don't use that word
(The Jungle Book, The Time Machine...) and also matches the table of contents.
Equal word windows work for every book and make arcs comparable across books.
"""

import re

N_SEGMENTS = 100
WORDS_PER_SEGMENT = 1500
_PARA_SPLIT = re.compile(r"\n\s*\n")


def n_segments(text: str) -> int:
    """About 1500 words per segment, so short and long books are equally noisy."""
    return int(min(N_SEGMENTS, max(20, len(text.split()) // WORDS_PER_SEGMENT)))


def segments(text: str, n: int = N_SEGMENTS) -> list[str]:
    words = text.split()
    if len(words) < n:
        raise ValueError(f"text has only {len(words)} words, cannot make {n} segments")
    bounds = [round(i * len(words) / n) for i in range(n + 1)]
    return [" ".join(words[bounds[i]:bounds[i + 1]]) for i in range(n)]


def paragraphs(text: str, max_words: int = 200) -> list[str]:
    """Paragraph-sized chunks for models with a short input limit (~512 tokens)."""
    chunks: list[str] = []
    for para in _PARA_SPLIT.split(text):
        words = para.split()
        for i in range(0, len(words), max_words):
            piece = " ".join(words[i:i + max_words])
            if piece:
                chunks.append(piece)
    return chunks
