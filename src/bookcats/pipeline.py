"""Run the whole pipeline: fetch -> analyse -> DNA -> SVG -> gallery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import BOOKS, BY_KEY
from .dna import build_corpus_dna
from .draw import draw
from .features import PROCESSED_DIR, load_or_compute
from .fetch import BookError, fetch_book
from .gallery import build_gallery

OUT_DIR = Path("output")


def run(keys: list[str] | None = None, backend: str = "lexicon", force: bool = False,
        out_dir: Path = OUT_DIR) -> list[dict]:
    books = [BY_KEY[k] for k in keys] if keys else BOOKS
    features = []
    for book in books:
        try:
            text = fetch_book(book)
        except BookError as exc:
            print(f"  ! skipped {book.title}: {exc}", file=sys.stderr)
            continue
        print(f"  - {book.title}: analysing...", end="", flush=True)
        features.append(load_or_compute(book, text, backend=backend, force=force))
        print(" ok")

    if len(features) < 2:
        raise SystemExit("Need at least 2 books: every trait is relative to the rest of the corpus.")

    cats = build_corpus_dna(features, {b.key: b.gutenberg_id for b in BOOKS})
    (out_dir / "svg").mkdir(parents=True, exist_ok=True)
    records = []
    for cat, feat in zip(cats, features):
        svg = draw(cat)
        (out_dir / "svg" / f"{cat.key}.svg").write_text(svg, encoding="utf-8")
        records.append({"dna": cat.to_dict(), "arc": feat["arc"], "svg": svg})
    (PROCESSED_DIR / "dna.json").write_text(
        json.dumps([r["dna"] for r in records], indent=2, ensure_ascii=False), encoding="utf-8")
    build_gallery(records, out_dir / "index.html")
    print(f"\n{len(records)} cats drawn -> {out_dir / 'index.html'}")
    return records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bookcats", description="If this book were a cat.")
    parser.add_argument("books", nargs="*", help=f"book keys (default: all): {', '.join(BY_KEY)}")
    parser.add_argument("--backend", choices=["lexicon", "transformer"], default="lexicon",
                        help="emotion scorer (transformer needs the [transformer] extra)")
    parser.add_argument("--force", action="store_true", help="recompute the analysis even if cached")
    args = parser.parse_args(argv)
    run(args.books or None, backend=args.backend, force=args.force)


if __name__ == "__main__":
    main()
