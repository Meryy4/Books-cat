"""Everything we measure about one book, cached as JSON."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks, savgol_filter

from .catalog import Book
from .emotions import CORE, score_book, top_words, valence
from .style import imagery, setting_scores, style_features

PROCESSED_DIR = Path("data/processed")
TAIL_POINTS = 20
FEATURES_VERSION = 5  # bump to invalidate old caches when the analysis changes


ARC_POINTS = 100


def smooth(x: np.ndarray, frac: float = 0.2) -> np.ndarray:
    """Savitzky-Golay smoothing over ~20% of the book."""
    window = max(5, int(round(frac * len(x))) | 1)  # odd
    window = min(window, len(x) if len(x) % 2 else len(x) - 1)
    return savgol_filter(x, window_length=window, polyorder=2) if window >= 5 else x


def resample(x: np.ndarray, n: int = TAIL_POINTS) -> np.ndarray:
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def turning_points(arc: np.ndarray) -> list[int]:
    """Indices of the main peaks and valleys of the smoothed arc (the plot twists)."""
    prominence = max(0.3 * (arc.max() - arc.min()), 0.05)
    peaks, _ = find_peaks(arc, prominence=prominence)
    valleys, _ = find_peaks(-arc, prominence=prominence)
    return sorted(int(i) for i in np.concatenate([peaks, valleys]))


def compute_features(book: Book, text: str, backend: str = "lexicon") -> dict:
    seg = score_book(text, backend)
    raw_arc = valence(seg)
    arc = resample(smooth(raw_arc), ARC_POINTS)  # same length for every book
    n = len(arc)
    k = max(n // 7, 1)  # first / last ~15%

    means = {e: float(np.mean([s[e] for s in seg])) for e in seg[0]}
    core_total = sum(means[e] for e in CORE) or 1.0
    shares = {e: means[e] / core_total for e in CORE}

    return {
        "version": FEATURES_VERSION,
        "backend": backend,
        "key": book.key,
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "n_words": len(text.split()),
        "emotion_rates": means,
        "emotion_shares": shares,
        "trust_share": means.get("trust", 0.0) / core_total,
        "valence_mean": float(raw_arc.mean()),
        "valence_start": float(arc[:k].mean()),
        "valence_end": float(arc[-k:].mean()),
        "darkest_at": float(np.argmin(arc) / (n - 1)),
        "turning_points": turning_points(arc),
        "n_segments": len(seg),
        "arc_raw": raw_arc.round(4).tolist(),
        "arc": arc.round(4).tolist(),
        "tail": resample(arc).round(4).tolist(),
        "style": style_features(text),
        "settings": setting_scores(text),
        "imagery": imagery(text),
        "top_words": {e: top_words(text, e) for e in ("fear", "sadness", "joy", "anger", "surprise")}
        if backend == "lexicon" else {},
    }


def load_or_compute(book: Book, text: str, backend: str = "lexicon",
                    out_dir: Path = PROCESSED_DIR, force: bool = False) -> dict:
    path = out_dir / f"{book.key}.features.json"
    if path.exists() and not force:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") == FEATURES_VERSION and data.get("backend") == backend:
            return data
    data = compute_features(book, text, backend)
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data
