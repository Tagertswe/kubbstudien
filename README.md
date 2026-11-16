# Kubbstudien

*[Svenska](README.sv.md)*

**When does the Kubb game actually start on Swedish Midsummer Eve?** An unnecessarily thorough study of
seventeen Midsummer Eves, made to settle a dispute between friends.

Every year at Midsummer someone gets out the Kubb set (a lawn game where you throw wooden batons at wooden
blocks) and every year there is disagreement about when that happens. Martin said "always around four or
five", Ida said half past six and Jana said nine. Instead of arguing, we looked at the timestamps of 824 photos
and videos from Midsummer Eves 2010–2026 and checked which ones show Kubb.

The answer: Kubb is under way by **19:05** on average (margin of error 18:18–19:52). Ida wins. Not a single
one of the 233 Kubb photos was taken between 16 and 17.

The study is deliberately over the top: confidence intervals, coin-toss odds, a trend line that has Kubb
starting at midnight in 2046, and errors measured in kilometres walked and trips to the Moon. Everything is
written in Swedish, in plain words, for readers who don't do statistics.

## The presentations

Open the files directly in a browser.

- [`page/kubb-onset-study.html`](page/kubb-onset-study.html): the full article, styled as a solemn journal
  paper, with charts and fine print.
- [`page/storbild.html`](page/storbild.html): the short big-screen version, 16 slides. Arrow keys, space or a
  click to move, **N** for speaker notes, **F** for full screen.

## The photos are not here

The photos stay on Martin's computer and are not in this repository. It only holds the times read from them
(`work/stats.json`) and the charts drawn from those times.

## Rebuilding

Needs Python 3 (standard library only for the statistics) and, for the chart images, Google Chrome and Pillow.

```sh
cd scripts
python3 build_page.py      # the article, from work/stats.json
python3 build_charts.py    # the charts as images, into work/charts/
python3 build_deck.py      # the big-screen version, from deck/
python3 -m unittest discover -s .
```

`inventory.py`, `classify.py` and `stats.py` produce `work/stats.json` from the photos themselves, so they
only run on Martin's machine. [`SPEC.md`](SPEC.md) records how the study was designed and what was decided.

Made by Martin Olsson and Claude.
