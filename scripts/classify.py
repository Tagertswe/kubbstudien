"""Apply the manual outdoor / Kubb classification to work/inventory.csv.

Usage: python3 scripts/classify.py
Writes work/classified.csv, work/kubb_review.jpg and prints a per-year summary.
Ranges are inclusive ref numbers within a year, from reviewing work/sheets/.
Keys ending in "-J" are guest photos from the shared album (refs like 2014-J012).
"""
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"

OUTDOOR = {
    "2010-J": [(1, 4)],
    "2011-J": [(1, 54)],
    "2012-J": [(1, 4)],
    "2013-J": [(1, 20)],
    "2014-J": [(1, 64)],
    "2015-J": [(1, 28)],
    "2016-J": [(1, 13)],
    "2017-J": [(1, 7)],
    "2018-J": [(1, 10)],
    "2015": [(3, 5)],
    "2017": [(2, 11)],
    "2018": [(1, 48)],
    "2019": [(8, 16)],
    "2020": [(9, 16)],
    "2021": [(2, 22)],
    "2022": [(1, 6)],
    "2023": [(7, 17), (21, 51)],
    "2024": [(33, 45), (47, 60), (65, 72), (74, 78), (101, 106), (118, 119), (122, 189), (192, 194)],
    "2025": [(39, 77), (79, 90)],
    "2026": [(4, 61), (86, 155), (159, 169)],
}
KUBB = {
    # guest photos and videos, reviewed 2026-10-10; blocks, batons or play are visible
    "2010-J": [(1, 3)],
    "2011-J": [(1, 54)],
    "2012-J": [(1, 4)],
    "2013-J": [(1, 1), (8, 9), (11, 12)],
    "2014-J": [(1, 41), (46, 50), (53, 64)],
    "2015-J": [(1, 23), (25, 25), (28, 28)],
    "2016-J": [(2, 4), (6, 11), (13, 13)],
    "2017-J": [(1, 7)],
    "2018-J": [(1, 3), (5, 6), (8, 10)],
    "2020": [(12, 16)],
    "2021": [(9, 14)],
    "2022": [(2, 6)],
    "2023": [(21, 25), (29, 43), (48, 51)],
    "2024": [(170, 172), (175, 175), (179, 181)],
    "2025": [(79, 90)],
}
# at, or on the path to, the field where Kubb is played, with no Kubb pieces
# visible. Martin confirmed on 2026-10-09 that Kubb is played in a field.
KUBB_FIELD = {
    "2022": [(1, 1)],
    "2024": [(166, 169)],
    "2026": [(162, 169)],
}
# a lawn game is visible but no Kubb pieces can be made out
KUBB_UNSURE = {
    "2018": [(44, 47)],
}
# later re-saved copies of other photos; their timestamp is not the capture time
COPIES = {
    "2021": [(15, 22)],
}

def in_ranges(ref, table):
    year, n = ref.split("-")
    key = year + "-J" if n.startswith("J") else year
    return any(lo <= int(n.lstrip("J")) <= hi for lo, hi in table.get(key, []))


def main():
    rows = list(csv.DictReader(open(WORK / "inventory.csv")))
    for r in rows:
        copy = in_ranges(r["ref"], COPIES)
        r["copy"] = copy
        r["outdoor"] = in_ranges(r["ref"], OUTDOOR)
        r["kubb"] = "no"
        if not copy and in_ranges(r["ref"], KUBB):
            r["kubb"] = "yes"
        elif not copy and in_ranges(r["ref"], KUBB_FIELD):
            r["kubb"] = "field"
        elif not copy and in_ranges(r["ref"], KUBB_UNSURE):
            r["kubb"] = "unsure"
    with open(WORK / "classified.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("year  files outdoor  outdoor span   kubb  kubb span      field  field span     unsure")
    for year in sorted({r["date"][:4] for r in rows}):
        yr = [r for r in rows if r["date"][:4] == year]
        out = [r for r in yr if r["outdoor"] and not r["copy"]]
        kubb = [r for r in yr if r["kubb"] == "yes"]
        unsure = [r for r in yr if r["kubb"] == "unsure"]
        field = [r for r in yr if r["kubb"] == "field"]
        span = lambda rs: f"{rs[0]['time'][:5]}-{rs[-1]['time'][:5]}" if rs else "-"
        print(f"{year}  {len(yr):5d} {len(out):7d}  {span(out):13s} {len(kubb):5d}  {span(kubb):13s} {len(field):5d}  {span(field):13s} {len(unsure):3d} {span(unsure) if unsure else ''}")

    review = [r for r in rows if r["kubb"] != "no"]
    size, cols, label = 300, 8, 24
    Image.MAX_IMAGE_PIXELS = None
    sheet = Image.new("RGB", (cols * size, -(-len(review) // cols) * (size + label)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    for i, r in enumerate(review):
        x, y = (i % cols) * size, (i // cols) * (size + label)
        thumb = WORK / "thumbs" / f"{r['id']}.jpg"
        if thumb.exists():
            with Image.open(thumb) as im:
                im = ImageOps.contain(im, (size, size))
                sheet.paste(im, (x + (size - im.width) // 2, y + label + (size - im.height) // 2))
        text = f"{r['ref']} {r['time'][:5]}" + {"unsure": " ?", "field": " field"}.get(r["kubb"], "")
        color = {"unsure": "#b00020", "field": "#0b5cad"}.get(r["kubb"], "black")
        draw.text((x + 4, y + 3), text, fill=color, font=font)
    sheet.save(WORK / "kubb_review.jpg", quality=82)
    print(f"{len(review)} photos on work/kubb_review.jpg")


if __name__ == "__main__":
    main()
