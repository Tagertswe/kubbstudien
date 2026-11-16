"""Build an inventory of the exported midsummer eve files and contact sheets for review.

Usage: python3 scripts/inventory.py
Reads export/<album>/.meta/*.json, writes work/inventory.csv and work/sheets/<year>-NN.jpg.
"""
import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export"
WORK = ROOT / "work"
THUMBS = WORK / "thumbs"
SHEETS = WORK / "sheets"
STOCKHOLM = ZoneInfo("Europe/Stockholm")
# photos that other guests have put in the shared album; everything else is Martin's own
GUEST_ALBUM = "kubbphotos-midsummer"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".mp", ".3gp", ".mkv"}
THUMB = 400
COLS, ROWS = 5, 4
LABEL_H = 26


def exif_times(path):
    """Return (DateTimeOriginal, OffsetTimeOriginal) from EXIF, or (None, None)."""
    try:
        with Image.open(path) as im:
            exif = im.getexif().get_ifd(0x8769)
    except Exception:
        return None, None
    return exif.get(0x9003), exif.get(0x9011)


def dedupe(rows):
    """Keep one row per file id; a file that sits in several albums is exported once per album."""
    seen = {}
    for r in rows:
        seen.setdefault(r["id"], r)
    return list(seen.values())


def number(rows):
    """Give every row a ref that is stable when another source adds files to the same year.

    Martin's files are numbered 2024-001, 2024-002 ...; guest files 2014-J001, 2014-J002 ...
    """
    counters = {}
    for r in sorted(rows, key=lambda r: (r["date"], r["time"], r["id"])):
        key = (r["date"][:4], r["source"])
        counters[key] = counters.get(key, 0) + 1
        r["ref"] = f"{key[0]}-{'J' if r['source'] == 'guest' else ''}{counters[key]:03d}"
    return rows


def collect():
    rows = []
    for meta_path in sorted(EXPORT.glob("*/.meta/*.json")):
        if meta_path.name == "album_meta.json":
            continue
        meta = json.loads(meta_path.read_text())
        album_dir = meta_path.parent.parent
        names = meta["info"].get("fileNames") or []
        image = next((n for n in names if Path(n).suffix.lower() in IMAGE_EXT), None)
        video = next((n for n in names if Path(n).suffix.lower() in VIDEO_EXT), None)
        local = datetime.fromisoformat(meta["creationTime"]).astimezone(STOCKHOLM)
        exif_dt, exif_off = exif_times(album_dir / image) if image else (None, None)
        rows.append({
            "id": meta["info"]["id"],
            "date": local.strftime("%Y-%m-%d"),
            "time": local.strftime("%H:%M:%S"),
            "kind": "image" if image else "video",
            "album": album_dir.name,
            "source": "guest" if album_dir.name == GUEST_ALBUM else "own",
            "file": image or video or "",
            "title": meta["title"],
            "has_gps": bool(meta.get("location")),
            "exif_time": exif_dt or "",
            "exif_offset": exif_off or "",
        })
    rows = dedupe(rows)
    rows.sort(key=lambda r: (r["date"], r["time"], r["id"]))
    return number(rows)


def thumbnail(row):
    out = THUMBS / f"{row['id']}.jpg"
    if out.exists():
        return out
    src = EXPORT / row["album"] / row["file"]
    try:
        if row["kind"] == "image":
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((THUMB, THUMB))
                im.save(out, quality=80)
        else:
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(src), "-frames:v", "1",
                 "-vf", f"scale={THUMB}:{THUMB}:force_original_aspect_ratio=decrease", str(out)],
                check=True, timeout=60)
    except Exception as err:
        print(f"no thumbnail for {row['ref']} ({row['file']}): {err}")
        return None
    return out if out.exists() else None


def sheets(rows):
    font = ImageFont.load_default(size=18)
    per_sheet = COLS * ROWS
    for year in sorted({r["ref"][:6].rstrip("0123456789") for r in rows}):
        year_rows = [r for r in rows if r["ref"].startswith(year) and r["ref"][len(year)].isdigit()]
        for page, start in enumerate(range(0, len(year_rows), per_sheet), 1):
            sheet = Image.new("RGB", (COLS * THUMB, ROWS * (THUMB + LABEL_H)), "white")
            draw = ImageDraw.Draw(sheet)
            for i, row in enumerate(year_rows[start:start + per_sheet]):
                x, y = (i % COLS) * THUMB, (i // COLS) * (THUMB + LABEL_H)
                thumb = thumbnail(row)
                if thumb:
                    with Image.open(thumb) as im:
                        sheet.paste(im, (x + (THUMB - im.width) // 2, y + LABEL_H + (THUMB - im.height) // 2))
                label = f"{row['ref']}  {row['time'][:5]}" + ("  VIDEO" if row["kind"] == "video" else "")
                draw.text((x + 6, y + 3), label, fill="black", font=font)
            sheet.save(SHEETS / f"{year}{page:02d}.jpg", quality=82)


def main():
    THUMBS.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    rows = collect()
    fields = ["ref", "id", "date", "time", "kind", "album", "source", "file", "title", "has_gps", "exif_time", "exif_offset"]
    with open(WORK / "inventory.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    sheets(rows)
    print(f"{len(rows)} files, {len(list(SHEETS.glob('*.jpg')))} sheets")


if __name__ == "__main__":
    main()
