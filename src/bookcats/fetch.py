"""Download books from Project Gutenberg, clean them and cache them locally."""

import re
from pathlib import Path

import requests

from .catalog import Book

RAW_DIR = Path("data/raw")

# Mirrors tried in order. The cache URL is the one Gutenberg recommends for scripts.
URL_PATTERNS = [
    "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt",
    "https://www.gutenberg.org/files/{id}/{id}-0.txt",
    "https://www.gutenberg.org/files/{id}/{id}.txt",
]

MIN_CHARS = 20_000  # anything shorter is a failed download, not a novel

_START = re.compile(r"\*{3}\s*START OF (?:THE|THIS) PROJECT GUTENBERG E-?BOOK[^*]*\*{3}", re.I)
_END = re.compile(r"\*{3}\s*END OF (?:THE|THIS) PROJECT GUTENBERG E-?BOOK", re.I)
_ILLUSTRATION = re.compile(r"\[Illustration[^\]]*\]", re.I)


class BookError(RuntimeError):
    pass


def strip_gutenberg(text: str) -> str:
    """Keep only the book itself: drop the Gutenberg header, licence and illustration tags."""
    start = _START.search(text)
    if start:
        text = text[start.end():]
    end = _END.search(text)
    if end:
        text = text[: end.start()]
    text = _ILLUSTRATION.sub("", text)
    return text.replace("\r\n", "\n").strip()


def validate(book: Book, text: str) -> None:
    """Fail loudly instead of silently analysing an empty file or the wrong book."""
    if len(text) < MIN_CHARS:
        raise BookError(f"{book.title}: text too short ({len(text)} chars), download probably failed")
    head = text[:5000].lower()
    if not any(w.lower() in head for w in book.check_words):
        raise BookError(
            f"{book.title}: none of {book.check_words} found at the start of the text, "
            "this is probably not the right book"
        )


def cache_path(book: Book, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"{book.key}.txt"


def fetch_book(book: Book, raw_dir: Path = RAW_DIR) -> str:
    path = cache_path(book, raw_dir)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        try:
            validate(book, text)
            return text
        except BookError:
            path.unlink()  # bad cache (empty file, wrong book): download again

    last_error = None
    for pattern in URL_PATTERNS:
        url = pattern.format(id=book.gutenberg_id)
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            last_error = exc
            continue
        resp.encoding = "utf-8"
        text = strip_gutenberg(resp.text)
        validate(book, text)
        raw_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    raise BookError(f"{book.title}: could not download Gutenberg #{book.gutenberg_id} ({last_error})")
