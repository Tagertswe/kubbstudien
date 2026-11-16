# Midsommarstatistik — spec

A deliberately over-engineered statistical study of when Kubb is played on
Swedish midsummer eve, based on photo timestamps from Ente. Purpose: settle a
dispute, and be funny for the people who attend.

## The dispute

- **Hypothesis Martin**: Kubb happens around 16:00–17:00.
- **Hypothesis Friend**: Kubb happens around 19:00.

## Scope

Eleven midsummer eves, this year and ten years back:

| Year | Date | Year | Date |
|---|---|---|---|
| 2016 | 24 June | 2022 | 24 June |
| 2017 | 23 June | 2023 | 23 June |
| 2018 | 22 June | 2024 | 21 June |
| 2019 | 21 June | 2025 | 20 June |
| 2020 | 19 June | 2026 | 19 June |
| 2021 | 25 June | | |

A photo is **relevant** if it was taken on one of these dates (Swedish local
time), outdoors, and shows Kubb being played or set up.

## Data source

- Ente Photos, album `kubbphotos-midsummer`.
- Ente CLI v0.3.0 in `tools/ente-cli/`, exporting to `export/`.
- Login (`ente account add`) is done by Martin; credentials never pass through Claude.

## Step 1 — Determine relevant photos and get them into the album

Requirement: find the relevant photos within the eleven dates and copy them
into `kubbphotos-midsummer`, using the Ente CLI if possible.

**Finding: the CLI cannot do the copy.** v0.3.0 is export-only. Its commands
are `account`, `admin`, `auth` and `export`; there is no command that creates
albums or adds files to one. `export` filters by album name only
(`--albums`, `--exclude-albums`, `--shared`, `--hidden`), not by date.

**Outcome (2026-10-09):** neither option below was used. The library is 170 GB
and no local disk has room, so the CLI source (AGPL-3.0, tag `cli-v0.3.0`) was
patched with `--dates`, `--tz` and `--dry-run` flags that skip the download of
every file not taken on the listed dates. Patch: `tools/ente-src/date-filter.patch`,
binary: `tools/ente-patched/ente`. Result: 623 files, 2.5 GB, in `export/`.
2016 has no photos. Classification is in `scripts/classify.py` and
`work/classified.csv`; the review sheet is `work/kubb_review.jpg`.

The original split into what the CLI can do and what must be done in the app:

1. **Get candidates (CLI).** Export photos to `export/` and keep only those
   whose capture time falls on one of the eleven dates. Two ways to limit the
   export, pick one:
   - **A (recommended):** in the Ente app, search each date and add every
     photo from it to a staging album, e.g. `midsummer-candidates`. Export
     only that album. Eleven searches, small download.
   - **B:** export the whole library and filter by date locally. No app work,
     but downloads everything and needs the disk space for it.
2. **Classify (local).** Claude looks at each candidate and marks it
   Kubb / not Kubb / unsure, with a one-line reason.
3. **Review (Martin).** A contact sheet of the Kubb and unsure photos, per
   year, for approval. The approved set is the dataset.
4. **Copy to the album (manual, in the app).** Claude produces a per-year list
   of approved photos (filename, capture time, source album) so they can be
   selected and added to `kubbphotos-midsummer` in the Ente app.

The analysis runs on the approved local set, so step 4 is for keeping the
album tidy in Ente and does not block the statistics.

## Step 2 — Extract timestamps

- Read capture time from EXIF and from Ente's exported metadata JSON.
- Convert to Europe/Stockholm.
- Flag photos with missing or suspicious timestamps (typical for files
  forwarded through chat apps) and exclude them from the numbers, but count
  them in the report.

## Step 3 — Statistics (absurd on purpose)

- **Per year:** Kubb onset (first photo), peak, last throw, density curve,
  confidence intervals regardless of sample size.
- **The trial:** Hypothesis Martin vs Hypothesis Friend, with p-values,
  bootstrap intervals, a Bayes factor and an effect size.
- **Trend:** regression of Kubb time on year, with a forecast for 2027 and an
  unreasonably wide prediction interval.
- **Limitations:** photos measure when someone held a phone, not when Kubb was
  played. Stated deadpan.

## Step 4 — Presentation

One published page styled as a solemn scientific paper: abstract, per-year
charts, forest plot, verdict, and a conflicts-of-interest note declaring that
the lead author holds one of the hypotheses.

**Outcome (2026-10-09):** steps 2–4 are built. `scripts/stats.py` writes
`work/stats.json`, `scripts/build_page.py` fills `page/template.html` into
`page/kubb-onset-study.html`, which is published as a private artifact. Tests:
`python3 -m unittest discover -s scripts` from the `scripts/` folder's parent.
Onset is defined as the earliest Kubb or Kubb-field photo of the year, since
Martin confirmed Kubb is played in a field.

**Update (2026-10-10):** scope widened to sixteen eves, 2011–2026 (dates in
`EVES` in `scripts/stats.py`). 2011–2014 have no photos; 2015 has five, taken in
Rome, none of Kubb. The page is now in Swedish for a non-technical audience;
Hypothesis Friend is Ida ("Hypotes I"). A file that sits in several Ente albums
is exported once per album, so `scripts/inventory.py` keeps one row per file id.

## Presentation — locked (2026-10-10)

Martin approved the page as published in Version 3 of
https://claude.ai/artifact/5ffz3RH21WRUPc7bLhi2DA ("it looks good"). Treat the
following as fixed; change it only on request.

- **Language and audience:** Swedish, for people with no technical or
  statistical background. Decimal comma, space between thousands, times as 20:13.
- **Form:** one page styled as a solemn journal article, "Tidskrift för icke
  upprepbara midsommarresultat", title "När börjar kubben egentligen?", authors
  M. Olsson and Claude. Deadpan throughout; every joke rests on a number computed
  from the data.
- **People:** named by first name (Martin, Ida) in the text; "Hypotes M" and
  "Hypotes I" in charts. Orange is Martin, green is Ida, blue is Kubb.
- **Plain words instead of jargon:** första kubbilden (onset; called kubbstart
  until 2026-10-10, see "What the photos measure"), felmarginal (confidence
  and prediction interval), "1 på N" (p-value), hattmetoden (bootstrap),
  klockstatistik (circular statistics), strecket genom prickarna (regression).
  Raw test statistics appear only in one fine-print paragraph.
- **Order:** Sammanfattning, four headline tiles, 1 Bakgrund, 2 Hur vi gick
  till väga, Figur 1 (timeline, one row per year), 3.1 När börjar kubben,
  Tabell 1 (all years), 3.2 Rättegången, Figur 2 (förvåningskurvan), Figur 3
  (year by year and pooled), Tabell 2 (three ways of counting: sträng, normal,
  snäll), Tabell 3 (the error in other units), 3.3 the 16–17 control, Figur 4
  (photos per hour), 3.4 Framtiden och forntiden, Figur 5 (trend and forecast),
  4 discussion and weaknesses, 5 Domen, 6 Rekommendationer, fine print.
- **Grey explainer boxes (Ruta 1–9):** how to read the paper (sillbiten), the
  average (stranger's height), the margin of error (fishing net), the hat
  method, clock statistics, luck in coin tosses (enkronor), odds with a deck of
  cards, the smoke alarm, the line through the dots.
- **Set pieces to keep:** the 10^75 odds against the atoms in the universe; the
  off-the-chart arrow in centimetres; the error as Earth rotation, walking
  distance, orbit distance in trips to the moon, rounds of "Små grodorna" and
  hours over all years; Rome and the Colosseum in 2015; Martin being right in
  1923 and Kubb reaching midnight in 2125; the once-in-20,096-years midsummer
  last due about 18,070 BC under the ice sheet; Kubbnormaltid (KNT); the
  confession to the tune of "Helan går".
- **Build:** `scripts/build_page.py` fills `page/template.html`; no number is
  typed into the template by hand except descriptions of single photos.

## Changes after the lock (2026-10-10, built and published as Version 4)

The structure above stands. These were added at Martin's request the same day:

- **A third guess.** Jana says 21:00 (window 20:30–21:30), shown in violet and
  always dashed. Guesses live in `CLAIMS` in `scripts/stats.py`; adding one
  more is a line there plus its wording in the template.
- **A second photo source.** Jocke put 204 photos and videos from 2010–2018 in
  the album `kubbphotos-midsummer` (Casio compact camera 2011–2016, Sony phone
  2017–2018, phone videos 2010). All were reviewed; 174 show Kubb. Guest files
  are numbered `2014-J012` so they never shift the numbering of Martin's own.
  Scope is now seventeen eves, 2010–2026.
- **The result changed.** Sixteen years with Kubb, mean onset 19:05. Ida is
  right (off by 5 minutes), Jana is off by 1 h 55 min, Martin by 2 h 35 min.
  The trend is now real (+10.4 min per year, p = 0.01), with the caveat that
  the early years are Jocke's camera and the late ones Martin's phone.
- **Set pieces that changed with the data:** the ice-age line is now told as
  what Martin's own photos implied before Jocke's arrived (once in 20,096
  years, last due 18,070 BC, now once in 17 years); Martin was right in 2003
  rather than 1923; Kubb reaches midnight in 2046; the fourth headline tile is
  Ida's error.
- **Section 7, "Källor, och hur vi kom fram till det här".** A plain-language
  list of sources and steps, including that Ente's open-source export program
  was changed on Martin's computer to fetch only given dates.
- **Not verifiable:** the clock of the compact camera (set by hand). Stated as
  a weakness on the page.

## Presentation — locked again (2026-10-10, Version 5)

Martin approved the page as published in Version 5 of
https://claude.ai/artifact/5ffz3RH21WRUPc7bLhi2DA. The same day Ida moved her
guess from 19:00 to 18:30, at Martin's request applied to both versions
(article Version 7; Version 6 briefly used 19:30, a time passed on by mistake); the bullets below describe the state after that change.
This replaces the Version 3
lock where the two differ; everything in "Changes after the lock" is now part
of the locked state. Change it only on request.

- **Guesses:** Martin 16:30 (orange), Ida 18:30 (green), Jana 21:00 (violet,
  always dashed). Blue is Kubb. Ida's first guess, 19:00, is kept as
  `FRIEND_FIRST` in `scripts/stats.py` and the page says what the change cost
  her (30 minutes; she still wins).
- **Headline tiles, five in one row on desktop:** mean onset; Ida's error;
  Kubb photos between 16 and 17 (0 of 233); how rarely chance gives these
  photos if Martin is right; odds for Ida against Martin (10^88).
- **Order:** Sammanfattning, tiles, 1 Bakgrund, 2 Hur vi gick till väga,
  Figur 1 (timeline 2010–2026), 3.1, Tabell 1 (with Fotograf column), 3.2
  Rättegången, Figur 2 (förvåningskurvan), Figur 3 (year by year and pooled),
  Tabell 2 (three ways of counting × three guesses), Tabell 3 (the error in
  other units, Martin/Jana/Ida), 3.3 the 16–17 control with the 2013 near
  miss, Figur 4 (photos per hour), 3.4 Framtiden och forntiden, Figur 5 (trend
  and forecast), 4 discussion with seven weaknesses, 5 Domen, 6
  Rekommendationer, 7 Källor och hur vi kom fram till det här, fine print.
- **Boxes:** Ruta 1–9 as in the first lock; the hat box ends on the fishing
  net and the hat agreeing, and Ruta 9 carries the photographer caveat.
- **Set pieces:** as listed under "Changes after the lock"; the ice-age story
  stays, told as what Martin's own photos implied.
- **Locked numbers (from `work/stats.json`):** 824 files, 652 outdoors, 233
  Kubb, 16 years with Kubb, mean onset 19:05, margin 18:18–19:52, Ida off 35
  min (5 with her first guess), Jana 1 h 55 min, Martin 2 h 35 min, trend +10.4 min per year, forecast
  2027 at 20:39.

## Big-screen version (2026-10-10)

A second, shorter version for showing on a big screen, made at Martin's
request: a 16:9 slide deck, "Kubbstudien – storbild", at
https://claude.ai/artifact/16VVHarUWTXCrZWvWKy8RV. The article above stays the
full version.

- Same language, people, colours and numbers as the article; far less text,
  one idea per slide, the jokes mostly in the speaker notes.
- Every chart from the article except Figur 2 (förvåningskurvan) has its own
  slide with a short "Så läser du bilden" text beside it.
- Slides 7–9 were simplified on 2026-10-10 at Martin's request, deck only:
  slide 7 is "Prispallen" (years each guess was closest: Ida 9, Jana 6,
  Martin 1) instead of förvåningskurvan; slide 8 keeps the coin tosses with
  plainer wording and an invitation for Martin to try; slide 9 is "Medan
  Martin väntar på kubben" with three big numbers instead of the unit table.
- The charts are pictures rendered from the same chart code and the same
  `work/stats.json` by `scripts/build_charts.py` (into `work/charts/`, then
  uploaded to the deck). The slide texts are written
  by hand, so the deck is a snapshot: if the data changes, the charts are
  re-rendered and the numbers on the slides are edited by hand.

## Repository (2026-11-16)

Public GitHub repo `kubbstudien`. The deck source now lives in `deck/`
(`deck.json` and `slides/<id>.html`, charts referenced as `charts/<fig>.png`), and
`scripts/build_deck.py` turns it into the standalone `page/storbild.html` with
`page/charts/`. Photos (`export/`), everything derived from them in `work/`
except `stats.json`, and `tools/` are git-ignored.

## What the photos measure (2026-10-10)

The photos do not show when the first baton was thrown, nor when the game
ended. Each year's number is the time of the first Kubb photo (or photo of the
pitch), which is the latest the game can have started; it may have started
earlier, never later. Both versions therefore say so:

- The measurement is called "första kubbilden" (or "årets första kubbild"),
  not "kubbstart", in text, tables, chart legends and tooltips.
- The headline claim is "Kubben är igång senast 19:05", not "Kubben börjar
  19:05".
- The question itself ("När börjar kubben egentligen?") and the jokes drawn
  from the trend line (2003, 2029, midnight 2046) keep "börjar".
- No numbers changed. Not done: showing which way the error points and how
  large it must be to change the winner, and relabelling the first-to-last
  photo lines, which are not the length of the game.

## Privacy

Photos stay on this machine. Only times and charts go on the page unless
Martin chooses specific photos to include.

## Open questions

1. Candidate export: option A (staging album) or B (whole library)?
2. Are photos taken by friends available, in a shared Ente album or as
   original files?
3. Should "the set time span" also mean a time-of-day window, or only the
   eleven dates? This spec assumes only the dates.
