"""Render a CatDNA as an SVG poster.

Every visual layer has an id (tail, eyes, ears...) so the gallery can highlight
the part of the cat that a given explanation talks about.
"""

from __future__ import annotations

import math
import random
from html import escape

from .dna import CatDNA

W, H = 500, 800
CX = 250            # horizontal centre of the cat
GROUND = 640        # y of the ground line


def f(x: float) -> str:
    return f"{x:.1f}"


def catmull_rom(points: list[tuple[float, float]]) -> str:
    """Smooth path through all points (Catmull-Rom converted to cubic Béziers)."""
    if len(points) < 2:
        return ""
    d = [f"M {f(points[0][0])} {f(points[0][1])}"]
    pts = [points[0]] + points + [points[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C {f(c1[0])} {f(c1[1])}, {f(c2[0])} {f(c2[1])}, {f(p2[0])} {f(p2[1])}")
    return " ".join(d)


# ---------------------------------------------------------------- background

def sky(c: CatDNA) -> str:
    sepia = f'<rect width="{W}" height="{H}" fill="#7a4a1c" opacity="{f(0.22 * c.sepia)}"/>' if c.sepia else ""
    return (f'<g id="sky"><rect width="{W}" height="{H}" fill="url(#skyGrad)"/>{sepia}'
            f'<rect width="{W}" height="{H}" fill="url(#vignette)"/></g>')


def setting_layer(c: CatDNA, rng: random.Random) -> str:
    # On a dark sky, dark silhouettes disappear: use a faint glow tint instead.
    dark_sky = c.axes.get("darkness", 0.5) >= 0.35
    col = c.glow if dark_sky else c.fur_dark
    op = 0.2 if dark_sky else 0.55
    s = c.setting
    parts: list[str] = []
    if s == "gothic":
        # castle on the horizon, crescent moon, bats
        parts.append(f'<path d="M 20 {GROUND} V 470 h 22 v -18 h 10 v 18 h 12 v -18 h 10 v 18 h 22 V {GROUND} Z'
                     f' M 400 {GROUND} V 430 l 25 -55 l 25 55 V {GROUND} Z M 360 {GROUND} V 500 h 40 V {GROUND} Z" '
                     f'fill="{col}" opacity="{op}"/>')
        parts.append(f'<path d="M 410 120 a 38 38 0 1 0 28 62 a 30 30 0 1 1 -28 -62 Z" fill="{c.glow}" opacity="0.35"/>')
        for _ in range(4):
            x, y, k = rng.uniform(60, 440), rng.uniform(90, 260), rng.uniform(0.7, 1.3)
            parts.append(f'<path transform="translate({f(x)} {f(y)}) scale({f(k)})" '
                         f'd="M -18 0 Q -9 -8 0 0 Q 9 -8 18 0 Q 9 -2 0 4 Q -9 -2 -18 0 Z" fill="{col}" opacity="{f(min(op * 1.6, 0.8))}"/>')
    elif s == "sea":
        for j in range(5):
            y = GROUND - 40 + j * 22
            d = f"M 0 {y} " + " ".join(f"Q {x + 25} {y - 12} {x + 50} {y}" for x in range(0, W, 50))
            parts.append(f'<path d="{d}" fill="none" stroke="{c.glow}" stroke-width="1.5" opacity="{f(0.12 + 0.06 * j)}"/>')
        parts.append(f'<path d="M 380 {GROUND - 40} l 30 -8 l -5 -60 l 10 0 l -5 60 l 30 8 Z" fill="{col}" opacity="{op}"/>')
    elif s == "wild":
        for j in range(9):
            x = 20 + j * 58 + rng.uniform(-12, 12)
            h = rng.uniform(140, 260)
            parts.append(f'<path d="M {f(x)} {GROUND} l -28 0 l 28 {f(-h)} l 28 {f(h)} Z" fill="{col}" opacity="{f(op * rng.uniform(0.6, 1))}"/>')
    elif s == "city":
        x = 0
        while x < W:
            w = rng.uniform(30, 60)
            h = rng.uniform(80, 220)
            parts.append(f'<rect x="{f(x)}" y="{f(GROUND - h)}" width="{f(w - 4)}" height="{f(h)}" fill="{col}" opacity="{op}"/>')
            for _ in range(int(h // 40)):
                wx, wy = x + rng.uniform(5, w - 12), GROUND - rng.uniform(15, h - 10)
                parts.append(f'<rect x="{f(wx)}" y="{f(wy)}" width="4" height="6" fill="{c.glow}" opacity="0.45"/>')
            x += w
    elif s == "drawing_room":
        parts.append(f'<path d="M 140 {GROUND - 20} V 230 a 110 110 0 0 1 220 0 V {GROUND - 20} Z" fill="none" '
                     f'stroke="{col}" stroke-width="10" opacity="{op}"/>')
        parts.append(f'<path d="M 250 120 V {GROUND - 20}" stroke="{col}" stroke-width="6" opacity="{op}"/>')
        parts.append(f'<path d="M 120 110 Q 150 380 110 {GROUND} H 60 V 110 Z M 380 110 Q 350 380 390 {GROUND} H 440 V 110 Z" '
                     f'fill="{col}" opacity="{f(min(op + 0.15, 0.7))}"/>')
    elif s == "wonder":
        for _ in range(7):
            x, y, r = rng.uniform(40, 460), rng.uniform(80, 560), rng.uniform(12, 55)
            parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="none" stroke="{c.glow}" stroke-width="2" '
                         f'stroke-dasharray="4 9" opacity="0.35"/>')
        for k in range(10):
            parts.append(f'<rect x="{k * 50}" y="{GROUND}" width="50" height="60" fill="{col}" opacity="{f(op if k % 2 else op * 0.4)}"/>')
    elif s == "machine":
        for x, y, r in ((90, 200, 55), (160, 270, 32), (410, 470, 70)):
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{col}" stroke-width="16" '
                         f'stroke-dasharray="9 7" opacity="{op}"/><circle cx="{x}" cy="{y}" r="{r * 0.55}" fill="none" '
                         f'stroke="{col}" stroke-width="4" opacity="{op}"/>')
        parts.append(f'<path d="M 90 200 L 90 165 M 90 200 L 115 212" stroke="{c.glow}" stroke-width="3" opacity="0.5"/>')
    ground = f'<rect y="{GROUND}" width="{W}" height="{H - GROUND}" fill="{c.fur_dark}" opacity="0.35"/>'
    return f'<g id="setting">{ground}{"".join(parts)}</g>'


def weather_layer(c: CatDNA, rng: random.Random) -> str:
    parts: list[str] = []
    if c.weather == "stars":
        for _ in range(int(25 + 50 * c.weather_amount)):
            x, y, r = rng.uniform(0, W), rng.uniform(0, 420), rng.uniform(0.6, 2.0)
            parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="#ffffff" opacity="{f(rng.uniform(0.2, 0.8))}"/>')
    elif c.weather == "rain":
        for _ in range(int(60 + 80 * c.weather_amount)):
            x, y, ln = rng.uniform(0, W + 40), rng.uniform(-20, H), rng.uniform(10, 26)
            parts.append(f'<path d="M {f(x)} {f(y)} l -5 {f(ln)}" stroke="#cfe3ff" stroke-width="1" opacity="0.28"/>')
    elif c.weather == "fog":
        for j in range(5):
            y = 380 + j * 60 + rng.uniform(-15, 15)
            parts.append(f'<ellipse cx="{f(rng.uniform(100, 400))}" cy="{f(y)}" rx="{f(rng.uniform(180, 300))}" ry="22" '
                         f'fill="#ffffff" opacity="0.07" filter="url(#blur)"/>')
    elif c.weather == "rings":
        for _ in range(int(5 + 6 * c.weather_amount)):
            x, y, r = rng.uniform(20, 480), rng.uniform(40, 600), rng.uniform(4, 14)
            parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="none" stroke="{c.glow}" stroke-width="1.5" opacity="0.5"/>')
    return f'<g id="weather">{"".join(parts)}</g>'


# ---------------------------------------------------------------- the cat

def body_geometry(c: CatDNA) -> tuple[str, float, float]:
    wb = 92 * c.body_width             # half width at the base
    ws = 52 * c.body_width + 14 * c.arch  # half width at the shoulders
    top = 395 - 28 * c.arch            # hunched shoulders rise
    d = (f"M {f(CX - ws)} {f(top)} "
         f"C {f(CX - ws - 26 - 18 * c.arch)} {f(top + 50)}, {f(CX - wb - 12)} 560, {f(CX - wb)} {GROUND} "
         f"L {f(CX + wb)} {GROUND} "
         f"C {f(CX + wb + 12)} 560, {f(CX + ws + 26 + 18 * c.arch)} {f(top + 50)}, {f(CX + ws)} {f(top)} "
         f"Q {CX} {f(top - 18 - 10 * c.arch)} {f(CX - ws)} {f(top)} Z")
    return d, wb, top


def tail_layer(c: CatDNA, wb: float) -> str:
    """The tail IS the emotional arc: base = beginning of the book, tip = the end."""
    x0, y0 = CX + wb - 18, GROUND - 12
    # baseline: a smooth sweep to the right then upwards
    def baseline(t: float) -> tuple[float, float, float, float]:
        p0, p1, p2 = (x0, y0), (465, GROUND + 5), (440, 330)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        dx = 2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0])
        dy = 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])
        norm = math.hypot(dx, dy) or 1
        return x, y, -dy / norm, dx / norm   # point + left normal

    amp = 46
    pts = []
    n = len(c.tail)
    for i, v in enumerate(c.tail):
        x, y, nx, ny = baseline(i / (n - 1))
        # positive emotion pushes the tail outward/up, negative inward/down
        px = min(max(x - nx * v * amp, 15), W - 15)
        py = min(max(y - ny * v * amp, 60), GROUND + 40)
        pts.append((px, py))
    # tip: curls up after a happier ending, droops after a darker one
    ex, ey = pts[-1]
    if c.tail_end == "up":
        pts += [(ex + 6, ey - 22), (ex - 10, ey - 34), (ex - 20, ey - 22)]
    elif c.tail_end == "down":
        pts += [(ex + 12, ey + 14), (ex + 14, ey + 34)]
    else:
        pts += [(ex + 4, ey - 18)]
    d = catmull_rom(pts)
    return (f'<g id="tail"><path d="{d}" fill="none" stroke="{c.glow}" stroke-width="20" stroke-linecap="round" '
            f'opacity="0.35" filter="url(#glow)"/>'
            f'<path d="{d}" fill="none" stroke="{c.fur}" stroke-width="15" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{c.fur_light}" stroke-width="2" stroke-linecap="round" opacity="0.6"/></g>')


def stripes_layer(c: CatDNA, top: float) -> str:
    if c.stripes == 0:
        return '<g id="stripes"/>'
    parts = []
    span = GROUND - 30 - (top + 35)
    for k in range(c.stripes):
        y = top + 35 + span * (k + 0.5) / c.stripes
        parts.append(f'<path d="M {CX - 130} {f(y)} Q {CX} {f(y + 16)} {CX + 130} {f(y)}" stroke="{c.fur_dark}" '
                     f'stroke-width="7" fill="none" stroke-linecap="round" opacity="0.8"/>')
    return f'<g id="stripes" clip-path="url(#bodyClip)">{"".join(parts)}</g>'


def ears_layer(c: CatDNA) -> str:
    parts = []
    for side in (-1, 1):
        bx_in, bx_out, by = CX + side * 22, CX + side * 68, 300
        h = 78 * c.ear_size
        angle = side * (8 + 38 * c.ear_tilt)  # rotate outwards when tense
        tip_x, tip_y = CX + side * 60, by - h
        d = f"M {f(bx_in)} {f(by - 8)} L {f(tip_x)} {f(tip_y)} L {f(bx_out)} {f(by + 6)} Z"
        di = (f"M {f(bx_in + side * 10)} {f(by - 10)} L {f(tip_x - side * 2)} {f(tip_y + 22)} "
              f"L {f(bx_out - side * 10)} {f(by)} Z")
        pivot = f"{f((bx_in + bx_out) / 2)} {by}"
        parts.append(f'<g transform="rotate({f(angle)} {pivot})"><path d="{d}" fill="{c.fur}" stroke="{c.glow}" '
                     f'stroke-width="1.5" stroke-opacity="0.5"/><path d="{di}" fill="{c.fur_light}" opacity="0.5"/></g>')
    return f'<g id="ears">{"".join(parts)}</g>'


def eyes_layer(c: CatDNA) -> str:
    parts = []
    rx = 15 * c.eye_size
    ry = 17 * c.eye_size
    for side in (-1, 1):
        ex, ey = CX + side * 31, 330
        parts.append(f'<ellipse cx="{f(ex)}" cy="{f(ey)}" rx="{f(rx)}" ry="{f(ry)}" fill="{c.eye}" filter="url(#glow)"/>')
        pw = max(1.6, rx * 0.62 * (1 - 0.85 * c.pupil_slit))
        parts.append(f'<ellipse cx="{f(ex)}" cy="{f(ey + 1)}" rx="{f(pw)}" ry="{f(ry * 0.86)}" fill="#050505"/>')
        parts.append(f'<circle cx="{f(ex - rx * 0.35)}" cy="{f(ey - ry * 0.4)}" r="{f(2 + rx * 0.08)}" fill="#ffffff" opacity="0.85"/>')
        # eyelid: covers the top of the eye when the book is sad
        lid = (1 - c.eye_open) * 2 * ry
        if lid > 1:
            ly = ey - ry - 2
            slope = side * lid * 0.35  # outer corner lower: a sad look
            parts.append(f'<path d="M {f(ex - rx - 3)} {f(ly)} H {f(ex + rx + 3)} V {f(ly + lid + slope)} '
                         f'Q {f(ex)} {f(ly + lid + 6)} {f(ex - rx - 3)} {f(ly + lid - slope)} Z" fill="{c.fur}"/>')
            parts.append(f'<path d="M {f(ex - rx - 3)} {f(ly + lid - slope)} Q {f(ex)} {f(ly + lid + 6)} '
                         f'{f(ex + rx + 3)} {f(ly + lid + slope)}" stroke="{c.fur_dark}" stroke-width="2" fill="none"/>')
    return f'<g id="eyes">{"".join(parts)}</g>'


def mouth_layer(c: CatDNA) -> str:
    y = 372
    nose = f'<path d="M {CX - 7} 356 h 14 l -7 8 Z" fill="{c.fur_dark}"/>'
    a = c.mouth_amount
    if c.mouth == "grin":
        w = 34 + 34 * a
        d = (f"M {f(CX - w)} {f(y - 6)} Q {CX} {f(y + 16 + 14 * a)} {f(CX + w)} {f(y - 6)} "
             f"Q {CX} {f(y + 34 + 18 * a)} {f(CX - w)} {f(y - 6)} Z")
        teeth = "".join(f'<path d="M {f(CX + k * w / 5)} {f(y + 4)} v {f(10 + 8 * a)}" stroke="{c.fur_dark}" '
                        f'stroke-width="1.2" opacity="0.6"/>' for k in range(-3, 4))
        m = f'<path d="{d}" fill="#ffffff" opacity="0.92" filter="url(#glow)"/>{teeth}'
    elif c.mouth == "smile":
        w = 14 + 10 * a
        m = (f'<path d="M {f(CX - w)} {y - 2} Q {f(CX - w / 2)} {f(y + 8 + 4 * a)} {CX} {y} '
             f'Q {f(CX + w / 2)} {f(y + 8 + 4 * a)} {f(CX + w)} {y - 2}" stroke="{c.fur_dark}" stroke-width="2.5" '
             f'fill="none" stroke-linecap="round"/>')
    elif c.mouth == "frown":
        w = 12 + 8 * a
        m = (f'<path d="M {f(CX - w)} {f(y + 8)} Q {CX} {f(y - 4 * a)} {f(CX + w)} {f(y + 8)}" stroke="{c.fur_dark}" '
             f'stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    else:
        m = (f'<path d="M {CX - 12} {y + 2} Q {CX - 6} {y + 6} {CX} {y} Q {CX + 6} {y + 6} {CX + 12} {y + 2}" '
             f'stroke="{c.fur_dark}" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
    fangs = ""
    if c.fangs:
        fangs = "".join(f'<path d="M {f(CX + s * 9)} {y + 1} l {f(s * 3)} 11 l {f(s * 3)} -11 Z" fill="#ffffff"/>'
                        for s in (-1, 1))
    return f'<g id="mouth">{nose}{m}{fangs}</g>'


def whiskers_layer(c: CatDNA) -> str:
    parts = []
    length = 45 + 55 * c.whisker_len
    for side in (-1, 1):
        for k, base_angle in enumerate((-10, 0, 10)):
            ang = math.radians(base_angle + 14 * c.whisker_droop)
            x0, y0 = CX + side * 20, 362 + k * 4
            x1 = x0 + side * length * math.cos(ang)
            y1 = y0 + length * math.sin(ang)
            parts.append(f'<path d="M {f(x0)} {f(y0)} L {f(x1)} {f(y1)}" stroke="{c.fur_light}" stroke-width="1.3" opacity="0.75"/>')
    return f'<g id="whiskers">{"".join(parts)}</g>'


def title_layer(c: CatDNA) -> str:
    title = c.title.upper()
    size = min(28.0, 440 / (0.68 * max(len(title), 1)))
    return (f'<text x="{CX}" y="728" font-family="Georgia, \'Times New Roman\', serif" font-size="{f(size)}" '
            f'fill="#ffffff" text-anchor="middle" letter-spacing="3" opacity="0.92">{escape(title)}</text>'
            f'<text x="{CX}" y="754" font-family="Georgia, serif" font-size="13" font-style="italic" fill="#ffffff" '
            f'text-anchor="middle" opacity="0.6">{escape(c.author)} · {c.year}</text>'
            f'<text x="{CX}" y="778" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="{c.glow}" '
            f'text-anchor="middle" letter-spacing="4" opacity="0.7">EMOTIONAL DATA PORTRAIT</text>')


def draw(c: CatDNA) -> str:
    rng = random.Random(c.seed)
    body_d, wb, top = body_geometry(c)
    head = (f"M {CX} 395 C {CX - 85} 395, {CX - 92} 335, {CX - 72} 300 "
            f"Q {CX} 268 {CX + 72} 300 C {CX + 92} 335, {CX + 85} 395, {CX} 395 Z")
    paws = "".join(f'<ellipse cx="{f(CX + s * 38)}" cy="{GROUND - 6}" rx="26" ry="13" fill="{c.fur}" '
                   f'stroke="{c.fur_dark}" stroke-width="2"/>' for s in (-1, 1))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(c.title)}">
<defs>
  <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c.sky_top}"/><stop offset="1" stop-color="{c.sky_bottom}"/></linearGradient>
  <radialGradient id="vignette" cx="0.5" cy="0.45" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.6"/></radialGradient>
  <radialGradient id="furGrad" cx="0.5" cy="0.25" r="0.85"><stop offset="0" stop-color="{c.fur_light}"/><stop offset="0.55" stop-color="{c.fur}"/><stop offset="1" stop-color="{c.fur_dark}"/></radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="blur"><feGaussianBlur stdDeviation="10"/></filter>
  <clipPath id="bodyClip"><path d="{body_d}"/></clipPath>
</defs>
{sky(c)}
{weather_layer(c, rng)}
{setting_layer(c, rng)}
<ellipse cx="{CX}" cy="{GROUND + 8}" rx="{f(wb + 40)}" ry="14" fill="#000" opacity="0.45"/>
<circle cx="{CX}" cy="420" r="190" fill="{c.glow}" opacity="0.06" filter="url(#blur)"/>
{tail_layer(c, wb)}
<g id="body"><path d="{body_d}" fill="url(#furGrad)" stroke="{c.glow}" stroke-width="1.5" stroke-opacity="0.45"/>{paws}</g>
{stripes_layer(c, top)}
<g transform="rotate({f(c.head_tilt)} {CX} 340)">
{ears_layer(c)}
<g id="head"><path d="{head}" fill="url(#furGrad)" stroke="{c.glow}" stroke-width="1.5" stroke-opacity="0.45"/></g>
{eyes_layer(c)}
{whiskers_layer(c)}
{mouth_layer(c)}
</g>
{title_layer(c)}
</svg>"""
