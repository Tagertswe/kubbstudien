# Kubbstudien

*[English](README.md)*

*När börjar kubben egentligen?* En onödigt grundlig utredning av sjutton midsommaraftnar,
gjord för att avgöra en dispyt om när kubben spelas på midsommarafton.

Svaret: kubben är igång senast **19:05**, i genomsnitt.

## Presentationerna

Öppna filerna direkt i en webbläsare.

- [`page/kubb-onset-study.html`](page/kubb-onset-study.html): hela uppsatsen, med diagram och finstilt.
- [`page/storbild.html`](page/storbild.html): kortversionen för storbild. Pilar, mellanslag eller klick för att bläddra,
  **N** visar talarmanus och **F** ger helskärm.

## Bilderna finns inte här

Studien bygger på 824 bilder och filmer från midsomrar 2010–2026. De ligger kvar på Martins dator och är
inte incheckade. Repot innehåller bara klockslagen (`work/stats.json`) och diagrammen som ritats ur dem.

## Bygga om

Kräver Python 3 och, för diagrambilderna, Google Chrome och Pillow.

```sh
cd scripts
python3 build_page.py      # uppsatsen, ur work/stats.json
python3 build_charts.py    # diagrammen som bilder, till work/charts/
python3 build_deck.py      # storbildsversionen, ur deck/
python3 -m unittest discover -s .
```

`inventory.py`, `classify.py` och `stats.py` tar fram `work/stats.json` ur själva bilderna och går därför
bara att köra på Martins dator. Hur studien är tänkt och vad som bestämts står i [`SPEC.md`](SPEC.md).
