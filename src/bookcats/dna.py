"""From measured features to the cat's DNA, with a human-readable reason for every trait.

Every axis is a RANK inside the corpus (0 = lowest of all books, 1 = highest).
Absolute scores from different books are hard to compare and tend to sit in a
narrow band; ranks guarantee that the darkest book gets the darkest cat.
"""

from __future__ import annotations

import colorsys
import math
from dataclasses import asdict, dataclass, field

import numpy as np

# Hue (degrees) associated with each emotional axis.
AXIS_HUES = {"tension": 355.0, "melancholy": 215.0, "warmth": 38.0, "whimsy": 290.0}
AXIS_FR = {"tension": "la tension (peur + colère)", "melancholy": "la tristesse",
           "warmth": "la chaleur (joie + confiance)", "whimsy": "l'étrangeté (surprise, exclamations, merveilleux)"}
SETTING_FR = {"gothic": "gothique (château, tombes, brume)", "sea": "maritime (mer, navires, rivages)",
              "wild": "sauvage (jungle, forêt, bêtes)", "city": "urbain (rues, foules, prisons)",
              "drawing_room": "salon (bals, visites, dîners)", "wonder": "merveilleux (rêve, reine, lapin)",
              "machine": "scientifique (machine, expérience, invention)"}


def ranks(values: list[float]) -> list[float]:
    """Percentile rank in [0, 1], ties averaged. A single book gets 0.5."""
    n = len(values)
    if n == 1:
        return [0.5]
    order = np.argsort(values, kind="mergesort")
    r = np.empty(n)
    r[order] = np.arange(n)
    # average ties
    vals = np.asarray(values)
    for v in np.unique(vals):
        idx = vals == v
        r[idx] = r[idx].mean()
    return (r / (n - 1)).tolist()


def position(values: list[float], i: int, highest_first: bool = True) -> int:
    """1-based position of book i when sorted (1 = the most)."""
    order = sorted(range(len(values)), key=lambda j: values[j], reverse=highest_first)
    return order.index(i) + 1


def nth(k: int) -> str:
    return "le" if k == 1 else f"le {k}e"


def hsl(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, min(max(l, 0), 1), min(max(s, 0), 1))
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def blend_hue(weights: dict[str, float]) -> float:
    x = sum(w * math.cos(math.radians(AXIS_HUES[a])) for a, w in weights.items())
    y = sum(w * math.sin(math.radians(AXIS_HUES[a])) for a, w in weights.items())
    return math.degrees(math.atan2(y, x)) % 360


def color_name(h: float, l: float) -> str:
    if l < 0.22:
        base = "très sombre"
    elif l < 0.35:
        base = "sombre"
    elif l < 0.5:
        base = "moyen"
    else:
        base = "clair"
    for limit, name in ((20, "rouge"), (50, "ambré"), (70, "doré"), (170, "vert"),
                        (250, "bleu"), (320, "violet"), (345, "rose"), (361, "rouge")):
        if h < limit:
            return f"{name} {base}"
    return base


@dataclass
class CatDNA:
    key: str
    title: str
    author: str
    year: int
    seed: int
    fur: str
    fur_dark: str
    fur_light: str
    glow: str
    eye: str
    sky_top: str
    sky_bottom: str
    body_width: float      # 0.75 (thin) .. 1.25 (round)
    arch: float            # 0 .. 1, hunched shoulders
    ear_tilt: float        # 0 upright .. 1 flattened
    ear_size: float        # 0.85 .. 1.25
    eye_size: float        # 0.8 .. 1.5
    eye_open: float        # 0.45 (droopy) .. 1
    pupil_slit: float      # 0 round .. 1 thin slit
    mouth: str             # grin | smile | neutral | frown
    mouth_amount: float
    fangs: bool
    whisker_len: float     # 0 .. 1
    whisker_droop: float   # 0 .. 1
    head_tilt: float       # degrees
    stripes: int
    tail: list[float]      # emotional arc, 20 points, in corpus units [-1, 1]
    tail_end: str          # up | down | flat
    setting: str
    weather: str           # stars | rain | fog | rings
    weather_amount: float
    sepia: float
    axes: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def build_corpus_dna(features: list[dict], gutenberg_ids: dict[str, int]) -> list[CatDNA]:
    n = len(features)
    get = lambda f: [f(x) for x in features]  # noqa: E731

    valence = get(lambda x: x["valence_mean"])
    tension_raw = get(lambda x: x["emotion_shares"]["fear"] + x["emotion_shares"]["anger"])
    sad_raw = get(lambda x: x["emotion_shares"]["sadness"])
    warm_raw = get(lambda x: x["emotion_shares"]["joy"] + 0.5 * x.get("trust_share", 0.0))
    surprise_raw = get(lambda x: x["emotion_shares"]["surprise"])
    exclaim = get(lambda x: x["style"]["exclaim"])
    sent_len = get(lambda x: x["style"]["sentence_len"])
    dialogue = get(lambda x: x["style"]["dialogue"])

    setting_names = list(features[0]["settings"])
    setting_means = {s: (np.mean([x["settings"][s] for x in features]) or 1.0) for s in setting_names}
    ratios = [{s: x["settings"][s] / setting_means[s] for s in setting_names} for x in features]
    wonder_ratio = [r["wonder"] for r in ratios]

    dark_ratio = get(lambda x: x["imagery"]["dark_ratio"])
    # Darkness = negative emotions AND dark imagery (night, blood, tombs...).
    # Imagery weighs more: it is a direct, less noisy signal than lexicon valence.
    darkness = ranks(list(0.3 * (1 - np.array(ranks(valence))) + 0.7 * np.array(ranks(dark_ratio))))
    tension = ranks(tension_raw)
    melancholy = ranks(sad_raw)
    warmth = ranks(warm_raw)
    # Exclamations are NOT whimsy (in The Jungle Book they are animals shouting).
    whimsy = ranks(list(np.mean([ranks(surprise_raw), ranks(wonder_ratio)], axis=0)))
    pace = ranks(list(np.mean([ranks([-s for s in sent_len]), ranks(exclaim)], axis=0)))
    talk = ranks(dialogue)

    # Tail amplitude is shared by the whole corpus so tails can be compared.
    max_dev = max(max(abs(v - np.mean(x["tail"])) for v in x["tail"]) for x in features) or 1.0

    cats = []
    for i, f in enumerate(features):
        ax = {"darkness": darkness[i], "tension": tension[i], "melancholy": melancholy[i],
              "warmth": warmth[i], "whimsy": whimsy[i], "pace": pace[i], "talk": talk[i]}
        emo = {a: ax[a] for a in AXIS_HUES}
        dominant = max(emo, key=emo.get)
        hue = blend_hue({a: v ** 3 for a, v in emo.items()})
        sat = 0.18 + 0.5 * emo[dominant]
        light = 0.56 - 0.38 * ax["darkness"]
        glow_h = AXIS_HUES[dominant]
        setting = max(ratios[i], key=ratios[i].get)

        if ax["melancholy"] >= 0.75:
            weather, w_amount = "rain", ax["melancholy"]
        elif ax["whimsy"] >= 0.85:
            weather, w_amount = "rings", ax["whimsy"]
        elif ax["tension"] >= 0.75:
            weather, w_amount = "fog", ax["tension"]
        else:
            weather, w_amount = "stars", 1 - ax["darkness"]

        mood = ax["warmth"] - max(ax["melancholy"], ax["darkness"])
        if ax["whimsy"] >= 0.85:
            mouth, amount = "grin", (ax["whimsy"] - 0.75) / 0.25
        elif mood > 0.25:
            mouth, amount = "smile", mood
        elif mood < -0.25:
            mouth, amount = "frown", -mood
        else:
            mouth, amount = "neutral", 0.5

        delta = f["valence_end"] - f["valence_start"]
        tail_end = "up" if delta > 0.06 else "down" if delta < -0.06 else "flat"
        center = float(np.mean(f["tail"]))

        cat = CatDNA(
            key=f["key"], title=f["title"], author=f["author"], year=f["year"],
            seed=gutenberg_ids.get(f["key"], i),
            fur=hsl(hue, sat, light),
            fur_dark=hsl(hue, sat, light * 0.62),
            fur_light=hsl(hue, sat * 0.8, min(light * 1.35 + 0.05, 0.85)),
            glow=hsl(glow_h, 0.95, 0.58),
            eye=hsl(glow_h, 0.95, 0.62),
            sky_top=hsl(glow_h, 0.35, 0.05 + 0.10 * (1 - ax["darkness"])),
            sky_bottom=hsl(glow_h, 0.40, 0.11 + 0.20 * (1 - ax["darkness"])),
            body_width=0.8 + 0.4 * ax["warmth"] - 0.25 * ax["melancholy"] + 0.1,
            arch=ax["tension"],
            ear_tilt=ax["tension"] ** 1.5,
            ear_size=0.85 + 0.4 * ax["whimsy"],
            eye_size=0.8 + 0.7 * ax["whimsy"],
            eye_open=1 - 0.55 * ax["melancholy"] ** 1.5,
            pupil_slit=ax["tension"],
            mouth=mouth, mouth_amount=float(min(max(amount, 0), 1)),
            fangs=ax["tension"] >= 0.7 and ax["darkness"] >= 0.6,
            whisker_len=ax["talk"], whisker_droop=ax["melancholy"],
            head_tilt=(ax["pace"] - 0.5) * 16,
            stripes=min(len(f["turning_points"]), 9),
            tail=[(v - center) / max_dev for v in f["tail"]],
            tail_end=tail_end,
            setting=setting, weather=weather, weather_amount=float(w_amount),
            sepia=float(min(max((1900 - f["year"]) / 100, 0), 1)),
            axes=ax,
        )
        cat.reasons = explain(cat, f, i, n, dict(
            valence=valence, darkness=darkness, tension_raw=tension_raw, sad_raw=sad_raw, warm_raw=warm_raw,
            dialogue=dialogue, ratios=ratios[i], dominant=dominant, delta=delta, hue=hue, light=light,
        ))
        cats.append(cat)
    return cats


def explain(cat: CatDNA, f: dict, i: int, n: int, ctx: dict) -> list[dict]:
    words = f.get("top_words", {})
    w = lambda e: ", ".join(words.get(e, [])[:5])  # noqa: E731
    with_words = lambda e: f" Mots les plus présents : {w(e)}." if words.get(e) else ""  # noqa: E731
    dark_pos = position(ctx["darkness"], i)
    reasons = []

    reasons.append({"layer": "body", "label": "Pelage",
                    "text": f"Pelage {color_name(ctx['hue'], ctx['light'])} : {nth(dark_pos)} livre le plus sombre "
                            f"sur {n}, en combinant le ton émotionnel (valence {f['valence_mean']:+.2f}) et l'imagerie "
                            f"({round(100 * f['imagery']['dark_ratio'])} % de mots sombres comme nuit, sang, tombe, "
                            f"contre lumière, soleil, rire). La teinte vient surtout de "
                            f"{AXIS_FR[ctx['dominant']]}, l'émotion la plus marquée de ce livre par rapport aux autres."})

    pct = round(100 * f["darkest_at"])
    end_txt = {"up": "remonte : la fin est plus lumineuse que le début",
               "down": "retombe : la fin est plus sombre que le début",
               "flat": "reste au même niveau qu'au début"}[cat.tail_end]
    reasons.append({"layer": "tail", "label": "Queue",
                    "text": f"La queue trace l'arc émotionnel du livre, de la base (début) jusqu'au bout (fin). "
                            f"Le moment le plus sombre arrive à {pct} % du récit, et la courbe {end_txt} "
                            f"({ctx['delta']:+.2f})."})

    if cat.stripes:
        reasons.append({"layer": "stripes", "label": "Rayures",
                        "text": f"{cat.stripes} rayure{'s' if cat.stripes > 1 else ''} = {cat.stripes} retournement"
                                f"{'s' if cat.stripes > 1 else ''} majeur{'s' if cat.stripes > 1 else ''} "
                                f"(pics et creux) dans l'arc émotionnel."})
    else:
        reasons.append({"layer": "body", "label": "Pelage uni",
                        "text": "Aucune rayure : l'arc émotionnel n'a pas de retournement marqué."})

    t_pos = position(ctx["tension_raw"], i)
    reasons.append({"layer": "ears", "label": "Oreilles et dos",
                    "text": f"Oreilles {'couchées' if cat.ear_tilt > 0.5 else 'dressées'} et dos "
                            f"{'rond' if cat.arch > 0.6 else 'détendu'} : {nth(t_pos)} livre le plus tendu "
                            f"(peur + colère) sur {n}.{with_words('fear')}"})

    s_pos = position(ctx["sad_raw"], i)
    lids = "tombantes" if cat.eye_open < 0.8 else "ouvertes"
    pupils = "fines comme des fentes" if cat.pupil_slit > 0.6 else "rondes"
    reasons.append({"layer": "eyes", "label": "Yeux",
                    "text": f"Paupières {lids} ({nth(s_pos)} livre le plus triste), pupilles {pupils} (tension), "
                            f"yeux {'grands' if cat.eye_size > 1.15 else 'normaux'} (étrangeté).{with_words('sadness')}"})

    mouth_txt = {
        "grin": "Sourire du chat du Cheshire : l'un des livres les plus étranges et imprévisibles du corpus.",
        "smile": "Petit sourire : la chaleur (joie + confiance) domine." + with_words("joy"),
        "frown": "Bouche tombante : un livre sombre ou triste.",
        "neutral": "Bouche neutre : aucune émotion n'écrase les autres.",
    }[cat.mouth]
    if cat.fangs:
        mouth_txt += " Crocs visibles : à la fois très tendu et très sombre."
    reasons.append({"layer": "mouth", "label": "Bouche", "text": mouth_txt})

    d_pos = position(ctx["dialogue"], i)
    reasons.append({"layer": "whiskers", "label": "Moustaches",
                    "text": f"Moustaches {'longues' if cat.whisker_len > 0.6 else 'courtes'} : {nth(d_pos)} livre "
                            f"le plus bavard ({round(100 * f['style']['dialogue'])} % du texte en dialogue)."})

    ratio = ctx["ratios"][cat.setting]
    reasons.append({"layer": "setting", "label": "Décor",
                    "text": f"Décor {SETTING_FR[cat.setting]} : ce vocabulaire est {ratio:.1f} fois plus fréquent "
                            f"que la moyenne des livres du corpus."})

    weather_txt = {"rain": "Pluie : l'un des livres les plus tristes.",
                   "rings": "Cercles flottants : l'un des livres les plus étranges.",
                   "fog": "Brouillard : l'un des livres les plus tendus.",
                   "stars": "Ciel étoilé : aucune émotion extrême ne domine l'atmosphère."}[cat.weather]
    reasons.append({"layer": "weather", "label": "Ciel", "text": weather_txt})

    if cat.sepia > 0:
        reasons.append({"layer": "sky", "label": "Teinte ancienne",
                        "text": f"Voile sépia : publié en {cat.year}, plus le livre est ancien, plus le voile est marqué."})
    return reasons
