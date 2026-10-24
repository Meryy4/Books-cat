"""A single self-contained HTML page: open output/index.html in any browser."""

from __future__ import annotations

import base64
import json
from pathlib import Path

AXES_FR = {"darkness": "Noirceur", "tension": "Tension", "melancholy": "Tristesse",
           "warmth": "Chaleur", "whimsy": "Étrangeté", "pace": "Rythme", "talk": "Dialogue"}

PAGE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Si ce livre était un chat</title>
<style>
:root{--bg:#0b0a10;--panel:#15131d;--ink:#eee9f6;--muted:#9a93ab;--line:#2a2636;--accent:#c58cff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Georgia,'Times New Roman',serif}
header{max-width:1100px;margin:0 auto;padding:48px 16px 24px}
h1{font-size:clamp(28px,5vw,48px);margin:0 0 8px;letter-spacing:.5px}
header p{color:var(--muted);max-width:720px;margin:0}
.grid{max-width:1100px;margin:0 auto;padding:16px;display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:0;cursor:pointer;overflow:hidden;transition:transform .15s,border-color .15s;color:inherit;font:inherit;text-align:left}
.card:hover,.card:focus-visible{transform:translateY(-3px);border-color:var(--accent);outline:none}
.card img{display:block;width:100%;aspect-ratio:5/8}
.card span{display:block;padding:8px 12px;font-size:14px;color:var(--muted)}
dialog{position:fixed;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:12px;padding:0;width:min(1000px,96vw);max-height:94vh}
dialog::backdrop{background:rgba(0,0,0,.75)}
.modal{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:24px;padding:20px}
@media (max-width:760px){.modal{grid-template-columns:1fr}}
.cat svg{width:100%;height:auto;display:block;border-radius:8px}
.cat svg g{transition:opacity .2s}
.cat.focus svg [data-dim]{opacity:.15}
h2{margin:0 0 4px;font-size:24px}
.sub{color:var(--muted);margin:0 0 14px;font-style:italic}
h3{font-size:13px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:18px 0 6px;font-family:Arial,sans-serif}
.arc{width:100%;height:auto;background:#0f0d16;border-radius:6px}
.bars{display:grid;grid-template-columns:90px 1fr;gap:4px 10px;font-size:13px;font-family:Arial,sans-serif;align-items:center}
.bar{height:8px;background:#26222f;border-radius:4px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent)}
ul.reasons{list-style:none;padding:0;margin:0}
.reasons li{padding:8px 10px;border-radius:6px;border:1px solid transparent;cursor:default;font-size:15px}
.reasons li:hover,.reasons li:focus{border-color:var(--line);background:#1d1a27;outline:none}
.reasons b{color:var(--accent);font-family:Arial,sans-serif;font-size:12px;letter-spacing:1px;text-transform:uppercase;display:block}
.close{position:absolute;top:10px;right:10px;z-index:2;background:rgba(21,19,29,.85);border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer}
footer{max-width:1100px;margin:30px auto;padding:16px;color:var(--muted);font-size:13px}
</style>
</head>
<body>
<header>
<h1>Si ce livre était un chat</h1>
<p>Chaque chat est dessiné par du code à partir de l'analyse complète d'un roman. Sa queue suit l'arc émotionnel du livre, ses rayures comptent les retournements du récit, ses yeux, ses oreilles et son décor viennent du texte. Cliquez sur un chat pour voir pourquoi il est comme ça.</p>
</header>
<main class="grid" id="grid"></main>
<dialog id="dlg"><button class="close" id="close" aria-label="Fermer">✕</button><div class="modal">
<div class="cat" id="cat"></div>
<div><h2 id="t"></h2><p class="sub" id="s"></p>
<h3>Arc émotionnel (début → fin)</h3><svg class="arc" id="arc" viewBox="0 0 400 120"></svg>
<h3>Profil (rang dans le corpus)</h3><div class="bars" id="bars"></div>
<h3>Pourquoi ce chat ?</h3><ul class="reasons" id="reasons"></ul></div>
</div></dialog>
<footer>Analyse : lexique d'émotions NRC sur le texte intégral (Project Gutenberg), lissage Savitzky-Golay, rangs relatifs au corpus.</footer>
<script>
const DATA = __DATA__;
const AXES = __AXES__;
const LAYERS = ["sky","weather","setting","tail","body","stripes","ears","head","eyes","whiskers","mouth"];
const grid = document.getElementById("grid"), dlg = document.getElementById("dlg");
DATA.forEach((d, i) => {
  const b = document.createElement("button");
  b.className = "card";
  b.innerHTML = `<img alt="${d.dna.title}" src="data:image/svg+xml;base64,${d.b64}"><span>${d.dna.title}</span>`;
  b.onclick = () => open(i);
  grid.appendChild(b);
});
function arcPath(arc){
  const lo = Math.min(...arc), hi = Math.max(...arc), pad = 12;
  const sx = i => pad + i * (400 - 2*pad) / (arc.length - 1);
  const sy = v => 120 - pad - (v - lo) / ((hi - lo) || 1) * (120 - 2*pad);
  const pts = arc.map((v,i) => `${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
  const k = arc.indexOf(lo);
  const zero = (lo < 0 && hi > 0) ? `<line x1="${pad}" x2="${400-pad}" y1="${sy(0)}" y2="${sy(0)}" stroke="#444" stroke-dasharray="3 4"/>` : "";
  return `${zero}<polyline points="${pts}" fill="none" stroke="#c58cff" stroke-width="2.5"/>
    <circle cx="${sx(k)}" cy="${sy(lo)}" r="4" fill="#ff6b6b"/><text x="${sx(k)}" y="${sy(lo)-8}" fill="#ff9b9b" font-size="10" text-anchor="${sx(k) > 300 ? "end" : sx(k) < 100 ? "start" : "middle"}" font-family="Arial">moment le plus sombre</text>`;
}
function open(i){
  const d = DATA[i], cat = document.getElementById("cat");
  cat.innerHTML = d.svg;
  document.getElementById("t").textContent = d.dna.title;
  document.getElementById("s").textContent = `${d.dna.author}, ${d.dna.year}`;
  document.getElementById("arc").innerHTML = arcPath(d.arc);
  document.getElementById("bars").innerHTML = Object.entries(AXES).map(([k,label]) =>
    `<span>${label}</span><div class="bar"><i style="width:${Math.round(100*d.dna.axes[k])}%"></i></div>`).join("");
  const ul = document.getElementById("reasons");
  ul.innerHTML = "";
  d.dna.reasons.forEach(r => {
    const li = document.createElement("li");
    li.tabIndex = 0;
    li.innerHTML = `<b>${r.label}</b>${r.text}`;
    const on = () => focusLayer(r.layer), off = () => focusLayer(null);
    li.onmouseenter = on; li.onfocus = on; li.onmouseleave = off; li.onblur = off;
    ul.appendChild(li);
  });
  dlg.showModal();
}
function focusLayer(layer){
  const cat = document.getElementById("cat");
  cat.classList.toggle("focus", !!layer);
  LAYERS.forEach(id => {
    const el = cat.querySelector("#" + id);
    if (!el) return;
    if (layer && id !== layer) el.setAttribute("data-dim", ""); else el.removeAttribute("data-dim");
  });
}
document.getElementById("close").onclick = () => dlg.close();
dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
</script>
</body>
</html>
"""


def build_gallery(records: list[dict], path: Path) -> None:
    data = [{"dna": r["dna"], "arc": r["arc"], "svg": r["svg"],
             "b64": base64.b64encode(r["svg"].encode("utf-8")).decode("ascii")} for r in records]
    html = (PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
                .replace("__AXES__", json.dumps(AXES_FR, ensure_ascii=False)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
