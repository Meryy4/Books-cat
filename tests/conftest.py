import numpy as np
import pytest


def make_features(key, valence=0.0, dark_ratio=0.5, fear=0.2, anger=0.15, sadness=0.2,
                  joy=0.2, surprise=0.1, dialogue=0.3, setting="city", arc=None, year=1880):
    disgust = max(1.0 - (fear + anger + sadness + joy + surprise), 0.0)
    if arc is None:
        arc = np.sin(np.linspace(0, 3, 100)) * 0.3
    arc = np.asarray(arc, dtype=float)
    tail = np.interp(np.linspace(0, 99, 20), np.arange(100), arc)
    settings = dict.fromkeys(["gothic", "sea", "wild", "city", "drawing_room", "wonder", "machine"], 5.0)
    settings[setting] = 40.0
    return {
        "key": key, "title": key.title(), "author": "Someone", "year": year,
        "emotion_shares": {"anger": anger, "disgust": disgust, "fear": fear, "joy": joy,
                           "sadness": sadness, "surprise": surprise},
        "trust_share": 0.3,
        "valence_mean": valence,
        "valence_start": float(arc[:14].mean()),
        "valence_end": float(arc[-14:].mean()),
        "darkest_at": float(np.argmin(arc) / 99),
        "turning_points": [20, 50],
        "arc": arc.tolist(),
        "tail": tail.tolist(),
        "style": {"sentence_len": 14, "dialogue": dialogue, "exclaim": 4.0, "question": 3.0, "richness": 0.4},
        "settings": settings,
        "imagery": {"dark": 10, "light": 10, "dark_ratio": dark_ratio},
        "top_words": {"fear": ["dread"], "sadness": ["tears"], "joy": ["glad"], "anger": [], "surprise": []},
    }


@pytest.fixture
def corpus():
    return [
        make_features("gloomy", valence=-0.3, dark_ratio=0.8, fear=0.35, sadness=0.3, joy=0.05, setting="gothic",
                      arc=np.linspace(0.2, -0.6, 100)),
        make_features("sunny", valence=0.4, dark_ratio=0.1, fear=0.1, sadness=0.1, joy=0.45, setting="drawing_room",
                      arc=np.linspace(-0.2, 0.5, 100)),
        make_features("middling", valence=0.05, dark_ratio=0.45, setting="sea"),
    ]
