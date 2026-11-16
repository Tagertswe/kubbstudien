"""Deliberately excessive statistics on when Kubb starts on midsummer eve.

Usage: python3 scripts/stats.py
Reads work/classified.csv, writes work/stats.json. No photos or filenames are written,
only times.
"""
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"

MARTIN = 16 * 60 + 30  # "around 4-5pm"
MARTIN_WINDOW = (16 * 60, 17 * 60)
FRIEND = 18 * 60 + 30  # "half past six"; Ida first said "around 7" and moved it on 2026-10-10
FRIEND_WINDOW = (18 * 60, 19 * 60)
FRIEND_FIRST = 19 * 60  # Ida's first guess, kept to show what the change cost her
JANA = 21 * 60  # "9pm"
JANA_WINDOW = (20 * 60 + 30, 21 * 60 + 30)
# every guess under test: key, name, chart letter, point estimate, window for photo counts
CLAIMS = [("martin", "Martin", "M", MARTIN, MARTIN_WINDOW),
          ("ida", "Ida", "I", FRIEND, FRIEND_WINDOW),
          ("jana", "Jana", "J", JANA, JANA_WINDOW)]
CLAIM_SD = 30  # how much slack "around" is given in the Bayes factor, minutes
BOOTSTRAP_DRAWS = 10000
SEED = 1986
# midsummer eve is the Friday between 19 and 25 June
EVES = {2010: "2010-06-25", 2011: "2011-06-24", 2012: "2012-06-22", 2013: "2013-06-21", 2014: "2014-06-20",
        2015: "2015-06-19", 2016: "2016-06-24", 2017: "2017-06-23", 2018: "2018-06-22",
        2019: "2019-06-21", 2020: "2020-06-19", 2021: "2021-06-25", 2022: "2022-06-24",
        2023: "2023-06-23", 2024: "2024-06-21", 2025: "2025-06-20", 2026: "2026-06-19"}


def minutes(hms):
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 60 + m + s / 60


def clock(mins):
    """A derived time (mean, interval bound, forecast), rounded to the minute."""
    total = int(round(mins)) % (24 * 60)
    return f"{total // 60:02d}:{total % 60:02d}"


def photo_clock(mins):
    """A photo's capture time as a clock shows it: the minute is truncated."""
    return clock(math.floor(mins))


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def median(xs):
    s = sorted(xs)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1)
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        for num in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                    -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1 + num * d
            d = 1 / (d if abs(d) > tiny else tiny)
            c = 1 + num / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1) < 1e-14:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def t_two_sided_p(t, df):
    return betainc(df / 2, 0.5, df / (df + t * t))


def t_critical(df, alpha=0.05):
    """Two-sided critical value by bisection."""
    lo, hi = 0.0, 1000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_two_sided_p(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def normal_cdf(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def one_sample_t(xs, mu):
    n = len(xs)
    t = (mean(xs) - mu) / (sd(xs) / math.sqrt(n))
    return {"t": t, "df": n - 1, "p": t_two_sided_p(t, n - 1), "cohen_d": (mean(xs) - mu) / sd(xs)}


def bootstrap_ci(xs, draws=BOOTSTRAP_DRAWS, seed=SEED):
    rng = random.Random(seed)
    means = sorted(mean([rng.choice(xs) for _ in xs]) for _ in range(draws))
    return means[int(0.025 * draws)], means[int(0.975 * draws) - 1]


def log10_bayes_factor(xs, mu_a, mu_b, sigma=CLAIM_SD):
    """log10 of P(data | N(mu_a, sigma)) / P(data | N(mu_b, sigma))."""
    ll = lambda mu: sum(-((x - mu) ** 2) / (2 * sigma ** 2) for x in xs)
    return (ll(mu_a) - ll(mu_b)) / math.log(10)


def regression(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    resid = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    sse = sum(r * r for r in resid)
    sst = sum((y - my) ** 2 for y in ys)
    s = math.sqrt(sse / (n - 2))
    se_slope = s / math.sqrt(sxx)
    tcrit = t_critical(n - 2)

    def predict(x):
        fit = intercept + slope * x
        half = tcrit * s * math.sqrt(1 + 1 / n + (x - mx) ** 2 / sxx)
        return {"fit": fit, "lo": fit - half, "hi": fit + half}

    return {"slope": slope, "intercept": intercept, "r2": 1 - sse / sst if sst else 0.0,
            "se_slope": se_slope, "p": t_two_sided_p(slope / se_slope, n - 2),
            "slope_lo": slope - tcrit * se_slope, "slope_hi": slope + tcrit * se_slope,
            "residual_sd": s, "predict": predict}


def circular(xs):
    """Mean direction and resultant length of clock times on the 24 h circle."""
    angles = [2 * math.pi * x / 1440 for x in xs]
    c, s = mean([math.cos(a) for a in angles]), mean([math.sin(a) for a in angles])
    return {"mean": (math.atan2(s, c) % (2 * math.pi)) * 1440 / (2 * math.pi), "r": math.hypot(c, s)}


def clopper_pearson_upper(successes, n, alpha=0.05):
    """One-sided upper confidence bound for a binomial proportion."""
    if successes == n:
        return 1.0
    lo, hi = successes / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        # P(X <= successes | p = mid) via the beta relation
        if 1 - betainc(successes + 1, n - successes, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def in_window(x, window):
    return window[0] <= x < window[1]


def onsets(rows, kinds):
    """Earliest photo time per year among the given kubb labels."""
    first = {}
    for r in rows:
        if r["kubb"] in kinds:
            year, t = int(r["date"][:4]), minutes(r["time"])
            first[year] = min(first.get(year, t), t)
    return dict(sorted(first.items()))


def summarize(onset_by_year):
    xs = list(onset_by_year.values())
    n = len(xs)
    tcrit = t_critical(n - 1)
    half = tcrit * sd(xs) / math.sqrt(n)
    boot = bootstrap_ci(xs)
    return {
        "n": n, "years": list(onset_by_year), "onsets": xs,
        "mean": mean(xs), "median": median(xs), "sd": sd(xs),
        "ci_lo": mean(xs) - half, "ci_hi": mean(xs) + half,
        "boot_lo": boot[0], "boot_hi": boot[1],
        "vs_martin": one_sample_t(xs, MARTIN), "vs_friend": one_sample_t(xs, FRIEND),
        "error_martin": abs(mean(xs) - MARTIN), "error_friend": abs(mean(xs) - FRIEND),
        "claims": {key: {**one_sample_t(xs, point), "error": abs(mean(xs) - point),
                         "inside_ci": abs(mean(xs) - point) <= half}
                   for key, _, _, point, _ in CLAIMS},
    }


def guesses(xs, kubb_times):
    """One entry per guess, best first: how far off, and how the evidence ranks it."""
    m = mean(xs)
    best = min(CLAIMS, key=lambda c: abs(m - c[3]))
    out = []
    for key, name, letter, point, window in CLAIMS:
        out.append({
            "key": key, "name": name, "letter": letter, "point": point, "window": window,
            "error": abs(m - point),
            "photos_in_window": sum(in_window(t, window) for t in kubb_times),
            "years_closest": sum(min(CLAIMS, key=lambda c: abs(x - c[3]))[0] == key for x in xs),
            "log10_behind_best": log10_bayes_factor(xs, best[3], point),
        })
    return sorted(out, key=lambda g: g["error"])


def by_source(rows, kinds):
    """Onset statistics using only the photos of one source, for each source."""
    out = {}
    for source in sorted({r.get("source", "own") for r in rows}):
        first = onsets([r for r in rows if r.get("source", "own") == source], kinds)
        if len(first) < 2:
            continue
        xs = list(first.values())
        z = lambda t: (t - mean(xs)) / sd(xs)
        out[source] = {"n": len(xs), "years": list(first), "mean": mean(xs), "sd": sd(xs),
                       "p_martin_window": normal_cdf(z(MARTIN_WINDOW[1])) - normal_cdf(z(MARTIN_WINDOW[0]))}
    return out


def analyse(rows):
    copies = sum(r["copy"] == "True" for r in rows)
    rows = [r for r in rows if r["copy"] != "True"]
    kubb = [r for r in rows if r["kubb"] == "yes"]
    kubb_times = [minutes(r["time"]) for r in kubb]
    scenarios = {
        "strict": summarize(onsets(rows, {"yes"})),
        "main": summarize(onsets(rows, {"yes", "field"})),
        "generous": summarize(onsets(rows, {"yes", "field", "unsure"})),
    }
    main = scenarios["main"]
    xs, years = main["onsets"], main["years"]

    reg = regression(years, xs)
    predict = reg.pop("predict")
    next_year = max(years) + 1
    reg["forecast_year"] = next_year
    reg["forecast"] = predict(next_year)
    reg["line"] = [{"year": y, **predict(y)} for y in range(min(years), next_year + 1)]
    reg["year_at_martin"] = (MARTIN - reg["intercept"]) / reg["slope"] if reg["slope"] else None
    reg["year_at_midnight"] = (1440 - reg["intercept"]) / reg["slope"] if reg["slope"] else None

    z = lambda t: (t - main["mean"]) / main["sd"]
    per_year = []
    by_year = defaultdict(list)
    for r in rows:
        by_year[int(r["date"][:4])].append(r)
    for year in sorted(by_year):
        yr = by_year[year]
        k = sorted(minutes(r["time"]) for r in yr if r["kubb"] == "yes")
        field = sorted(minutes(r["time"]) for r in yr if r["kubb"] == "field")
        unsure = sorted(minutes(r["time"]) for r in yr if r["kubb"] == "unsure")
        outdoor_other = sorted(minutes(r["time"]) for r in yr if r["outdoor"] == "True" and r["kubb"] == "no")
        per_year.append({
            "year": year, "date": yr[0]["date"], "files": len(yr),
            "outdoor": sum(r["outdoor"] == "True" for r in yr),
            "kubb": k, "field": field, "unsure": unsure, "outdoor_other": outdoor_other,
            "onset": main["onsets"][years.index(year)] if year in years else None,
            "onset_source": None if year not in years else min(
                (r for r in yr if r["kubb"] in ("yes", "field")), key=lambda r: minutes(r["time"])).get("source", "own"),
            "guest_files": sum(r.get("source") == "guest" for r in yr),
            "onset_basis": None if year not in years else ("kubb" if k and (not field or k[0] <= field[0]) else "field"),
            "control_16_17": sum(in_window(t, MARTIN_WINDOW) for t in outdoor_other),
            "control_friend": sum(in_window(t, FRIEND_WINDOW) for t in outdoor_other),
        })

    hours = range(7, 24)
    hist = [{"hour": h,
             "kubb": sum(int(t // 60) == h for t in kubb_times),
             "other": sum(int(t // 60) == h for p in per_year for t in p["outdoor_other"])} for h in hours]

    in_martin = sum(in_window(t, MARTIN_WINDOW) for t in kubb_times)
    in_friend = sum(in_window(t, FRIEND_WINDOW) for t in kubb_times)
    loo = [mean(xs[:i] + xs[i + 1:]) for i in range(len(xs))]
    return {
        "guesses": guesses(xs, kubb_times),
        "by_source": by_source(rows, {"yes", "field"}),
        "claims": {"martin": MARTIN, "martin_window": MARTIN_WINDOW, "friend": FRIEND, "friend_first": FRIEND_FIRST,
                   "friend_window": FRIEND_WINDOW, "jana": JANA, "jana_window": JANA_WINDOW, "claim_sd": CLAIM_SD},
        "totals": {"files": len(rows), "outdoor": sum(r["outdoor"] == "True" for r in rows),
                   "kubb": len(kubb), "field": sum(r["kubb"] == "field" for r in rows),
                   "unsure": sum(r["kubb"] == "unsure" for r in rows),
                   "copies": copies, "guest_files": sum(r.get("source") == "guest" for r in rows), "years_searched": len(EVES), "years_with_photos": len(by_year),
                   "first_year": min(EVES), "last_year": max(EVES)},
        "eves": EVES,
        "scenarios": scenarios,
        "per_year": per_year,
        "hist": hist,
        "regression": reg,
        "circular": circular(xs),
        "bayes": {"log10_friend_over_martin": log10_bayes_factor(xs, FRIEND, MARTIN)},
        "photo_level": {
            "n": len(kubb_times), "earliest": min(kubb_times), "latest": max(kubb_times),
            "in_martin": in_martin, "martin_upper": clopper_pearson_upper(in_martin, len(kubb_times)),
            "in_friend": in_friend, "friend_upper": clopper_pearson_upper(in_friend, len(kubb_times)),
        },
        "future": {
            "p_martin_window": normal_cdf(z(MARTIN_WINDOW[1])) - normal_cdf(z(MARTIN_WINDOW[0])),
            "p_friend_window": normal_cdf(z(FRIEND_WINDOW[1])) - normal_cdf(z(FRIEND_WINDOW[0])),
        },
        "leave_one_out": {"min": min(loo), "max": max(loo)},
        "control": {"martin_window_photos": sum(p["control_16_17"] for p in per_year),
                    "martin_window_years": [p["year"] for p in per_year if p["control_16_17"]]},
    }


def main():
    rows = list(csv.DictReader(open(WORK / "classified.csv")))
    result = analyse(rows)
    (WORK / "stats.json").write_text(json.dumps(result, indent=1))
    m = result["scenarios"]["main"]
    print(f"onsets {[photo_clock(x) for x in m['onsets']]} for {m['years']}")
    print(f"mean {clock(m['mean'])} sd {m['sd']:.1f} min, 95% CI {clock(m['ci_lo'])}-{clock(m['ci_hi'])}, "
          f"bootstrap {clock(m['boot_lo'])}-{clock(m['boot_hi'])}")
    for who in ("martin", "friend"):
        t = m[f"vs_{who}"]
        print(f"vs {who}: t({t['df']}) = {t['t']:.2f}, p = {t['p']:.2g}, d = {t['cohen_d']:.2f}, "
              f"error {m[f'error_{who}']:.0f} min")
    r = result["regression"]
    print(f"trend {r['slope']:+.1f} min/year (p = {r['p']:.2f}, R2 = {r['r2']:.2f}), "
          f"{r['forecast_year']} forecast {clock(r['forecast']['fit'])} "
          f"[{clock(r['forecast']['lo'])}, {clock(r['forecast']['hi'])}]")
    print(f"log10 BF friend/martin {result['bayes']['log10_friend_over_martin']:.1f}; "
          f"kubb photos in Martin window {result['photo_level']['in_martin']}/{result['photo_level']['n']}, "
          f"in Friend window {result['photo_level']['in_friend']}; control photos 16-17: "
          f"{result['control']['martin_window_photos']} in {result['control']['martin_window_years']}")
    for name, s in result["scenarios"].items():
        print(f"  {name}: n={s['n']} mean {clock(s['mean'])} p_martin {s['vs_martin']['p']:.2g} p_friend {s['vs_friend']['p']:.2g}")


if __name__ == "__main__":
    main()
