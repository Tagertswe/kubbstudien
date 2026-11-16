"""Fill page/template.html with the numbers from work/stats.json.

Usage: python3 scripts/build_page.py
Writes page/kubb-onset-study.html. Every figure in the text comes from stats.json.
"""
import json
import math
import re
from pathlib import Path

from stats import BOOTSTRAP_DRAWS, clock, photo_clock

ROOT = Path(__file__).resolve().parent.parent
MINUS = "−"
NBSP = " "
EARTH_ORBIT_KM_S = 29.78
MOON_KM = 384_400
FROG_SONG_S = 40   # one round of "Små grodorna", assumed
WALK_KM_H = 5
# shown in Table 1 for years that deserve a remark
NOTES = {2015: "firades i Rom; ingen kubb vid Colosseum"}


def sv(x, digits=0):
    """A number the Swedish way: decimal comma, space between thousands."""
    return f"{x:,.{digits}f}".replace(",", NBSP).replace(".", ",").replace("-", MINUS)


def in_words(n):
    """Small counts read better spelled out; anything else stays a figure."""
    words = "noll en två tre fyra fem sex sju åtta nio tio elva tolv tretton fjorton femton sexton sjutton arton nitton tjugo".split()
    return words[n] if 0 <= n < len(words) else str(n)


def duration(mins):
    mins = int(round(mins))
    h, m = divmod(mins, 60)
    hours = f"{h} tim " if h else ""
    return f"{hours}{m} min"


def pvalue(p):
    if p >= 0.01:
        return sv(p, 2)
    return sv(p, max(3, -int(f"{p:e}".split("e")[1])))


def signed(x, digits=1):
    return f"{'+' if x >= 0 else MINUS}{sv(abs(x), digits)}"


def years_list(years):
    years = [str(y) for y in years]
    return years[0] if len(years) == 1 else ", ".join(years[:-1]) + " och " + years[-1]


def heads_in_a_row(p):
    """Largest run of heads whose probability is still above p."""
    return math.floor(math.log2(1 / p))


def one_in(p):
    """A probability as 'one time in N', N rounded to two significant figures."""
    n = 1 / p
    scale = 10 ** max(0, math.floor(math.log10(n)) - 1)
    return f"1 på {sv(round(n / scale) * scale)}"


def one_significant(x):
    """Round to one significant figure and spell out the magnitude."""
    exponent = math.floor(math.log10(x))
    lead = round(x / 10 ** exponent)
    if lead == 10:
        lead, exponent = 1, exponent + 1
    names = {6: ("miljon", "miljoner"), 9: ("miljard", "miljarder"), 12: ("biljon", "biljoner"),
             18: ("triljon", "triljoner"), 24: ("kvadriljon", "kvadriljoner")}
    group = max((e for e in names if e <= exponent), default=None)
    if group is None:
        return sv(lead * 10 ** exponent)
    count = lead * 10 ** (exponent - group)
    return f"{sv(count)} {names[group][count != 1]}"


def luck(p):
    """How often chance alone gives data this far from a guess, if the guess is right."""
    return f"{sv(p * 100)} av 100" if p >= 0.05 else one_in(p)


def luck_row(name, p):
    """One row of the coin box: the run of heads a guess needs, drawn as coins."""
    heads = heads_in_a_row(p)
    times = "en gång" if heads == 1 else f"{heads} gånger i rad"
    if heads == 0:
        return f'<div class="row"><span class="who">{name} behöver ingen tur alls ({luck(p)}). Inga enkronor går åt.</span></div>'
    coins = '<span class="coin">kr</span>' * heads
    return (f'<div class="row"><span class="who">{name} behöver mer tur än att singla krona {times} '
            f'({luck(p)}):</span>{coins}</div>')


def wrongness_rows(errors, years):
    """errors: list of (name, minutes off). One table row per unit, one column per person."""
    orbit = lambda err: err * 60 * EARTH_ORBIT_KM_S
    units = [
        ("Minuter", lambda e: sv(e)),
        ("Grader som jordklotet hann snurra under tiden", lambda e: f"{sv(e / 4, 1)}°"),
        ("Kilometer man hinner promenera medan man väntar", lambda e: sv(e / 60 * WALK_KM_H, 1)),
        ("Kilometer jorden hann färdas runt solen", lambda e: sv(orbit(e))),
        ("Samma sträcka, mätt i resor till månen", lambda e: sv(orbit(e) / MOON_KM, 2)),
        ("Varv av ”Små grodorna” man hinner sjunga", lambda e: sv(e * 60 / FROG_SONG_S)),
        ("Andel av ett helt dygn", lambda e: f"{sv(e / 1440 * 100, 1)}{NBSP}%"),
        (f"Timmar, hopräknat över de {years} midsomrarna", lambda e: sv(e * years / 60, 1)),
    ]
    return "".join("<tr><td>" + label + "</td>" + "".join(f'<td class="r">{fmt(err)}</td>' for _, err in errors) + "</tr>"
                   for label, fmt in units)


DECK_ORDERS_LOG10 = math.log10(math.factorial(52))
EARTH_ATOMS_LOG10 = math.log10(1.33e50)
PEOPLE = {"own": "Martin", "guest": "Jocke"}


def earths(log10_count):
    """A count of atoms as so many Earths, or as a fraction of one."""
    ratio = 10 ** (log10_count - EARTH_ATOMS_LOG10)
    return f"{one_significant(ratio)} jordklot" if ratio >= 1.5 else "ett jordklot" if ratio >= 0.75 else f"1/{one_significant(1 / ratio)} av jordklotet"


def tokens(d):
    m = d["scenarios"]["main"]
    reg, photo, totals, claims = d["regression"], d["photo_level"], d["totals"], d["claims"]
    guess = {g["key"]: g for g in d["guesses"]}
    interval = lambda lo, hi: f"{clock(lo)}–{clock(hi)}"
    rows = []
    for name, key in (("Sträng", "strict"), ("Normal", "main"), ("Snäll", "generous")):
        s = d["scenarios"][key]
        rows.append(f"<tr><td>{name}</td><td class=\"r\">{s['n']}</td><td class=\"r\">{clock(s['mean'])}</td>"
                    f"<td>{interval(s['ci_lo'], s['ci_hi'])}</td>"
                    + "".join(f"<td class=\"r\">{luck(s['claims'][k]['p'])}</td>" for k in ("martin", "jana", "ida")) + "</tr>")
    p_future = d["future"]["p_martin_window"]
    own, guest = d["by_source"]["own"], d["by_source"]["guest"]
    df = m["claims"]["martin"]["df"]
    d["tcurve"] = {"df": df, "norm": math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi),
                   "marks": [{"key": g["key"], "name": g["name"], "letter": g["letter"], "t": m["claims"][g["key"]]["t"]}
                             for g in d["guesses"]]}
    d["notes"] = NOTES
    d["people"] = PEOPLE
    empty = [y for y in map(int, d["eves"]) if y not in {p["year"] for p in d["per_year"]}]
    no_kubb = [p["year"] for p in d["per_year"] if p["onset"] is None]
    kubb_times = sorted(t for p in d["per_year"] for t in p["kubb"])
    before = [t for t in kubb_times if t < claims["martin_window"][0]]
    out = {
        "y_first": totals["first_year"], "y_last": totals["last_year"], "y_n": totals["years_searched"],
        "y_n_word": in_words(totals["years_searched"]),
        "k_n": m["n"], "k_n_word": in_words(m["n"]).capitalize(), "k_n_low": in_words(m["n"]),
        "empty_years": years_list(empty) if empty else "inga", "no_kubb_years": years_list(no_kubb),
        "copies": totals["copies"], "guest_files": totals["guest_files"], "own_files": totals["files"] - totals["guest_files"],
        "guest_n": guest["n"], "guest_first": guest["years"][0], "guest_last": guest["years"][-1], "guest_mean": clock(guest["mean"]),
        "own_n": own["n"], "own_first": own["years"][0], "own_last": own["years"][-1], "own_mean": clock(own["mean"]),
        "src_gap": duration(own["mean"] - guest["mean"]),
        "own_once": sv(1 / own["p_martin_window"]), "own_once_bc": sv(1 / own["p_martin_window"] - reg["forecast_year"] + 1),
        "own_err_m": duration(abs(own["mean"] - claims["martin"])),
        "jocke_help": duration(abs(own["mean"] - claims["martin"]) - guess["martin"]["error"]),
        "near_gap": duration(claims["martin_window"][0] - before[-1]) if before else "–",
        "near_first": photo_clock(before[0]) if before else "–", "near_last": photo_clock(before[-1]) if before else "–",
        "near_n": len(before),
        "gap_m": duration(m["ci_lo"] - claims["martin"]), "gap_j": duration(claims["jana"] - m["ci_hi"]),
        "height_cm": sv(m["claims"]["martin"]["cohen_d"] * 7),
        "coin_rows": "".join(luck_row(g["name"], m["claims"][g["key"]]["p"]) for g in reversed(d["guesses"])),
        "bf_m": f"{guess['martin']['log10_behind_best']:.0f}", "bf_j": f"{guess['jana']['log10_behind_best']:.0f}",
        "deck_times": one_significant(10 ** (guess["martin"]["log10_behind_best"] - DECK_ORDERS_LOG10)),
        "table3": wrongness_rows([(g["name"], guess[g["key"]]["error"]) for g in (guess["martin"], guess["jana"], guess["ida"])], m["n"]),
        "frog_s": FROG_SONG_S, "moon_km": sv(MOON_KM),
        "slope_pct": sv(max(1, reg["p"] * 100)),
        "fc_width": duration(reg["forecast"]["hi"] - reg["forecast"]["lo"]),
        "files": totals["files"], "outdoor": totals["outdoor"],
        "kubb_n": photo["n"], "field_n": totals["field"],
        "mean": clock(m["mean"]), "ci": interval(m["ci_lo"], m["ci_hi"]),
        "boot": interval(m["boot_lo"], m["boot_hi"]), "boot_n": sv(BOOTSTRAP_DRAWS),
        "sd": sv(m["sd"]), "df": df, "d_m": sv(m["claims"]["martin"]["cohen_d"], 1),
        "earliest": photo_clock(photo["earliest"]), "latest": photo_clock(photo["latest"]),
        "circ": clock(d["circular"]["mean"]), "circ_r": sv(d["circular"]["r"], 2),
        "ctl_n": d["control"]["martin_window_photos"], "ctl_years": years_list(d["control"]["martin_window_years"]),
        "slope": signed(reg["slope"]), "slope_ci": f"{signed(reg['slope_lo'])} till {signed(reg['slope_hi'])}",
        "slope_p": pvalue(reg["p"]), "r2": sv(reg["r2"], 2),
        "year_m": f"{reg['year_at_martin']:.0f}", "year_midnight": f"{reg['year_at_midnight']:.0f}",
        "fc_year": reg["forecast_year"], "fc": clock(reg["forecast"]["fit"]),
        "fc_pi": interval(reg["forecast"]["lo"], reg["forecast"]["hi"]),
        "p_future_m": f"{sv(p_future * 100)}{NBSP}%", "once_m": sv(1 / p_future),
        "loo": interval(d["leave_one_out"]["min"], d["leave_one_out"]["max"]),
        "table2": "".join(rows),
        "year_i": f"{(claims['friend'] - reg['intercept']) / reg['slope']:.0f}",
        "year_j": f"{(claims['jana'] - reg['intercept']) / reg['slope']:.0f}",
        "late_m": f"{totals['last_year'] - reg['year_at_martin']:.0f}",
        "years_j": years_list([y for y, x in zip(m["years"], m["onsets"])
                               if min(("martin", "friend", "jana"), key=lambda k: abs(x - claims[k])) == "jana"]),
        "earths": earths(guess["jana"]["log10_behind_best"]),
        "claim_i": clock(claims["friend"]), "claim_i_first": clock(claims["friend_first"]),
        "err_i_first": duration(abs(m["mean"] - claims["friend_first"])),
        "err_i_cost": duration(abs(m["mean"] - claims["friend"]) - abs(m["mean"] - claims["friend_first"])),
    }
    for key, tag in (("martin", "m"), ("ida", "i"), ("jana", "j")):
        c = m["claims"][key]
        out.update({f"err_{tag}": duration(c["error"]), f"luck_{tag}": luck(c["p"]), f"t_{tag}": sv(c["t"], 2),
                    f"p_{tag}": pvalue(c["p"]), f"win_{tag}": guess[key]["photos_in_window"],
                    f"closest_{tag}": guess[key]["years_closest"]})
    out["data"] = json.dumps(d, separators=(",", ":"), ensure_ascii=False)
    return out


def render(template, values):
    missing = set(re.findall(r"\[\[(\w+)\]\]", template)) - set(values)
    if missing:
        raise KeyError(f"template tokens without a value: {sorted(missing)}")
    return re.sub(r"\[\[(\w+)\]\]", lambda match: str(values[match.group(1)]), template)


def main():
    d = json.loads((ROOT / "work" / "stats.json").read_text())
    html = render((ROOT / "page" / "template.html").read_text(), tokens(d))
    out = ROOT / "page" / "kubb-onset-study.html"
    out.write_text(html)
    print(f"wrote {out} ({len(html) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
