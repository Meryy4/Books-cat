import colorsys
import re
import xml.etree.ElementTree as ET

from bookcats.dna import build_corpus_dna, ranks
from bookcats.draw import GROUND, H, W, draw

LAYERS = ["sky", "weather", "setting", "tail", "body", "stripes", "ears", "head", "eyes", "whiskers", "mouth"]


def lightness(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[1]


def test_ranks():
    assert ranks([3, 1, 2]) == [1.0, 0.0, 0.5]
    assert ranks([5]) == [0.5]
    assert ranks([1, 1, 2]) == [0.25, 0.25, 1.0]


def test_darker_book_gets_darker_fur(corpus):
    cats = {c.key: c for c in build_corpus_dna(corpus, {})}
    assert lightness(cats["gloomy"].fur) < lightness(cats["middling"].fur) < lightness(cats["sunny"].fur)


def test_traits_follow_the_text(corpus):
    cats = {c.key: c for c in build_corpus_dna(corpus, {})}
    assert cats["gloomy"].setting == "gothic"
    assert cats["sunny"].setting == "drawing_room"
    assert cats["gloomy"].tail_end == "down"      # the arc falls
    assert cats["sunny"].tail_end == "up"         # the arc rises
    assert cats["sunny"].mouth == "smile"
    assert cats["gloomy"].mouth == "frown"
    assert cats["gloomy"].ear_tilt > cats["sunny"].ear_tilt


def test_every_cat_is_different(corpus):
    svgs = [draw(c) for c in build_corpus_dna(corpus, {})]
    assert len(set(svgs)) == len(svgs)


def test_svg_is_valid_and_has_every_layer(corpus):
    for cat in build_corpus_dna(corpus, {}):
        root = ET.fromstring(draw(cat))
        ids = {el.get("id") for el in root.iter()}
        assert set(LAYERS) <= ids
        assert cat.reasons and all(r["layer"] in LAYERS for r in cat.reasons)


def test_tail_stays_inside_the_poster(corpus):
    """Regression: the old tail grew with the number of chapters and covered the title."""
    for cat in build_corpus_dna(corpus, {}):
        svg = draw(cat)
        tail = re.search(r'<g id="tail"><path d="([^"]+)"', svg).group(1)
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", tail)]
        xs, ys = nums[0::2], nums[1::2]
        assert min(xs) >= 0 and max(xs) <= W
        assert min(ys) >= 0 and max(ys) <= GROUND + 60 < H - 60  # never reaches the title
