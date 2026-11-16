"""Render the article's charts as pictures for the big-screen deck.

Usage: python3 scripts/build_charts.py   (after build_page.py)
Writes work/charts/<figure>.png. Each picture is the article's own chart code
drawn alone on a page of a fixed width, photographed by headless Chrome.
"""
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "charts"
SCALE = 3      # device pixels per CSS pixel, so the pictures stay sharp on a big screen
WIDTH = 640    # CSS width of every chart; the deck shows them 1100 px wide
PAD = 16       # room at the sides for axis labels that hang over the edge
# figure id -> row height for the charts that have one row per year (the article uses 26)
FIGURES = {"fig1": 20, "fig2": 18, "figt": None, "fig3": None, "fig4": None}


def harness(page, figure, width=WIDTH, row=None):
    """A page that shows one chart of the article and nothing else."""
    if f'id="{figure}"' not in page:
        raise KeyError(f"no chart with id {figure}")
    head = "".join(re.findall(r"<link[^>]*>|<style>.*?</style>", page, re.S))
    script = re.search(r"<script>.*</script>", page, re.S).group(0)
    plots = "".join(f'<div class="plot" id="{i}"{"" if i == figure else " hidden"}></div>'
                    for i in re.findall(r'<div class="plot" id="(\w+)"', page))
    config = f"<script>window.CHART = {{row: {row}}};</script>" if row else ""
    return (f'<!doctype html><html lang="sv" data-theme="light"><meta charset="utf-8">{head}'
            f"<style>html, body {{ margin: 0; }} body {{ width: {width}px; padding: 0 {PAD}px; }} [hidden] {{ display: none; }}</style>"
            f'<body>{plots}<table id="tab1" hidden><tbody></tbody></table>{config}{script}</body></html>')


def trim(path):
    """Cut the empty page below the chart."""
    from PIL import Image, ImageChops
    image = Image.open(path).convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((0, image.height - 1)))
    box = ImageChops.difference(image, background).getbbox()
    image.crop((0, 0, image.width, min(image.height, box[3] + 4 * SCALE))).save(path)
    return image.width, min(image.height, box[3] + 4 * SCALE)


def main():
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    page = (ROOT / "page" / "kubb-onset-study.html").read_text()
    OUT.mkdir(parents=True, exist_ok=True)
    for figure, row in FIGURES.items():
        source, picture = OUT / f"{figure}.html", OUT / f"{figure}.png"
        source.write_text(harness(page, figure, row=row))
        subprocess.run([chrome, "--headless=new", "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
                        f"--window-size={WIDTH + 2 * PAD},700", "--virtual-time-budget=4000",
                        f"--screenshot={picture}", source.as_uri()], check=True, capture_output=True)
        print(figure, "%d x %d" % trim(picture))


if __name__ == "__main__":
    main()
