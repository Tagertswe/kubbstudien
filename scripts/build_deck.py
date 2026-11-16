"""Put the big-screen deck together as one HTML page that runs without the Slides artifact.

Usage: python3 scripts/build_deck.py   (after build_charts.py)
Reads deck/deck.json and deck/slides/<id>.html, writes page/storbild.html and copies
the chart pictures the slides use from work/charts/ to page/charts/.
Keys in the page: arrows, space or a click to move, N for speaker notes, F for full screen.
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck"
PAGE = ROOT / "page"
CHARTS = ROOT / "work" / "charts"

STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { height: 100%; background: #05080e; overflow: hidden; }
img { display: block; }
#stage { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: 0 0; }
#stage > section { position: absolute; inset: 0; width: 1920px; height: 1080px; opacity: 0; visibility: hidden; transition: opacity .35s, visibility .35s; }
#stage > section.current { opacity: 1; visibility: visible; }
#stage > section > aside { display: none; }
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 40vh; overflow: auto; padding: 16px 24px;
  background: rgba(16, 26, 43, .94); color: #e9edf4; font: 18px/1.45 'Schibsted Grotesk', Arial, sans-serif; display: none; }
#notes.on { display: block; }
#notes b { color: #ffd84d; font-weight: 600; margin-right: 12px; }
@media print {
  @page { size: 1920px 1080px; margin: 0; }
  html, body { height: auto; overflow: visible; background: none; }
  #stage { position: static; transform: none !important; height: auto; }
  #stage > section { position: relative; opacity: 1; visibility: visible; break-after: page; }
  #notes { display: none !important; }
}
"""

SCRIPT = """
const stage = document.getElementById("stage"), slides = [...stage.children], notes = document.getElementById("notes");
let at = 0;
function fit() {
  const s = Math.min(innerWidth / 1920, innerHeight / 1080);
  stage.style.transform = `scale(${s}) translate(-50%, -50%)`;
}
function show(i) {
  at = Math.max(0, Math.min(slides.length - 1, i));
  slides.forEach((el, k) => el.classList.toggle("current", k === at));
  const aside = slides[at].querySelector("aside");
  notes.innerHTML = `<b>${at + 1} / ${slides.length}</b>` + (aside ? aside.innerHTML : "");
  history.replaceState(null, "", "#" + (at + 1));
}
addEventListener("keydown", e => {
  if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(e.key)) show(at + 1);
  else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(e.key)) show(at - 1);
  else if (e.key === "Home") show(0);
  else if (e.key === "End") show(slides.length - 1);
  else if (e.key === "n" || e.key === "N") notes.classList.toggle("on");
  else if (e.key === "f" || e.key === "F") document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  else return;
  e.preventDefault();
});
stage.addEventListener("click", e => show(e.clientX > innerWidth / 2 ? at + 1 : at - 1));
addEventListener("resize", fit);
fit();
show((parseInt(location.hash.slice(1), 10) || 1) - 1);
"""


def charts_used(slides):
    """The chart pictures the slides point at, as figure names."""
    return sorted(set(re.findall(r'src="charts/(\w+)\.png"', "".join(slides))))


def page(deck, slides):
    """The whole presentation as one page, slides in the deck's order."""
    fonts = "".join(f'<link href="{html.escape(f["href"])}" rel="stylesheet">' for f in deck["faces"].values())
    return ('<!doctype html><html lang="sv"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(deck["title"])}</title>'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>{fonts}<style>{STYLE}</style></head>'
            f'<body><div id="stage">\n{"".join(slides)}</div><div id="notes"></div><script>{SCRIPT}</script></body></html>\n')


def read_slides(deck, folder):
    slides = []
    for name in deck["order"]:
        text = (folder / f"{name}.html").read_text()
        if f'id="{name}"' not in text:
            raise ValueError(f"slide {name} does not carry its own id")
        slides.append(text)
    return slides


def main():
    deck = json.loads((DECK / "deck.json").read_text())
    slides = read_slides(deck, DECK / "slides")
    (PAGE / "charts").mkdir(exist_ok=True)
    for figure in charts_used(slides):
        shutil.copyfile(CHARTS / f"{figure}.png", PAGE / "charts" / f"{figure}.png")
    out = PAGE / "storbild.html"
    out.write_text(page(deck, slides))
    print(f"wrote {out} ({len(slides)} slides, charts: {', '.join(charts_used(slides))})")


if __name__ == "__main__":
    main()
