"""Unit tests for scripts/stats.py. Run: python3 -m unittest discover -s scripts"""
import math
import unittest

import stats


def row(date, time, kubb="no", outdoor="True", copy="False"):
    return {"date": date, "time": time, "kubb": kubb, "outdoor": outdoor, "copy": copy}


class TimeHelpers(unittest.TestCase):
    def test_minutes_and_clock_round_trip(self):
        self.assertAlmostEqual(stats.minutes("19:48:30"), 19 * 60 + 48.5)
        self.assertEqual(stats.clock(19 * 60 + 48.4), "19:48")

    def test_clock_rounds_derived_times(self):
        self.assertEqual(stats.clock(20 * 60 + 12.9), "20:13")

    def test_photo_clock_truncates_like_a_clock(self):
        self.assertEqual(stats.photo_clock(stats.minutes("19:43:59")), "19:43")

    def test_clock_wraps_past_midnight(self):
        self.assertEqual(stats.clock(24 * 60 + 5), "00:05")


class Distributions(unittest.TestCase):
    def test_t_p_values_match_tables(self):
        # two-sided critical values: t(6) = 2.447, t(1) = 12.706 at 5 %
        self.assertAlmostEqual(stats.t_two_sided_p(2.447, 6), 0.05, places=3)
        self.assertAlmostEqual(stats.t_two_sided_p(12.706, 1), 0.05, places=3)
        self.assertAlmostEqual(stats.t_two_sided_p(0, 6), 1.0)

    def test_t_p_is_symmetric(self):
        self.assertAlmostEqual(stats.t_two_sided_p(-3.1, 5), stats.t_two_sided_p(3.1, 5))

    def test_t_critical_matches_tables(self):
        self.assertAlmostEqual(stats.t_critical(6), 2.447, places=3)
        self.assertAlmostEqual(stats.t_critical(5), 2.571, places=3)

    def test_betainc_bounds_and_symmetry(self):
        self.assertEqual(stats.betainc(2, 3, 0), 0.0)
        self.assertEqual(stats.betainc(2, 3, 1), 1.0)
        self.assertAlmostEqual(stats.betainc(2, 3, 0.4) + stats.betainc(3, 2, 0.6), 1.0)

    def test_normal_cdf(self):
        self.assertAlmostEqual(stats.normal_cdf(0), 0.5)
        self.assertAlmostEqual(stats.normal_cdf(1.96), 0.975, places=3)


class Tests(unittest.TestCase):
    def test_one_sample_t(self):
        result = stats.one_sample_t([1, 2, 3, 4, 5], 0)
        self.assertAlmostEqual(result["t"], 3 / (math.sqrt(2.5) / math.sqrt(5)))
        self.assertEqual(result["df"], 4)
        self.assertAlmostEqual(result["cohen_d"], 3 / math.sqrt(2.5))

    def test_bayes_factor_favours_the_closer_claim(self):
        xs = [1190, 1200, 1210]
        self.assertGreater(stats.log10_bayes_factor(xs, 1140, 990), 0)
        self.assertAlmostEqual(stats.log10_bayes_factor(xs, 1140, 990),
                               -stats.log10_bayes_factor(xs, 990, 1140))
        self.assertEqual(stats.log10_bayes_factor(xs, 1000, 1000), 0)

    def test_regression_recovers_a_line(self):
        reg = stats.regression([1, 2, 3, 4], [5.1, 6.9, 9.1, 10.9])
        self.assertAlmostEqual(reg["slope"], 1.96, places=2)
        self.assertGreater(reg["r2"], 0.99)
        forecast = reg["predict"](5)
        self.assertLess(forecast["lo"], forecast["fit"])
        self.assertGreater(forecast["hi"], forecast["fit"])

    def test_prediction_interval_widens_away_from_the_data(self):
        predict = stats.regression([1, 2, 3, 4], [5.1, 6.9, 9.1, 10.9])["predict"]
        near, far = predict(3), predict(30)
        self.assertGreater(far["hi"] - far["lo"], near["hi"] - near["lo"])

    def test_circular_mean_handles_midnight(self):
        result = stats.circular([23 * 60 + 30, 30])
        self.assertAlmostEqual(result["mean"] % 1440, 0, places=6)
        self.assertLess(result["r"], 1)

    def test_clopper_pearson_zero_successes(self):
        self.assertAlmostEqual(stats.clopper_pearson_upper(0, 59), 1 - 0.05 ** (1 / 59), places=6)
        self.assertEqual(stats.clopper_pearson_upper(5, 5), 1.0)

    def test_bootstrap_is_reproducible_and_brackets_the_mean(self):
        xs = [1180, 1190, 1300, 1185, 1170, 1267, 1196]
        lo, hi = stats.bootstrap_ci(xs)
        self.assertEqual((lo, hi), stats.bootstrap_ci(xs))
        self.assertLess(lo, stats.mean(xs))
        self.assertGreater(hi, stats.mean(xs))

    def test_window_is_half_open(self):
        self.assertTrue(stats.in_window(960, (960, 1020)))
        self.assertFalse(stats.in_window(1020, (960, 1020)))


class Analysis(unittest.TestCase):
    def setUp(self):
        self.rows = [
            row("2020-06-19", "16:10:00"),                      # control photo in Martin's window
            row("2020-06-19", "19:50:00", kubb="yes"),
            row("2020-06-19", "19:40:00", kubb="yes"),
            row("2021-06-25", "19:30:00", kubb="field"),
            row("2021-06-25", "19:45:00", kubb="yes"),
            row("2021-06-25", "16:30:00", kubb="yes", copy="True"),  # copy must be ignored
            row("2022-06-24", "20:00:00", kubb="yes"),
            row("2023-06-23", "19:00:00", kubb="unsure"),
            row("2024-06-21", "10:00:00", outdoor="False"),
        ]

    def test_onsets_take_the_earliest_photo_per_year(self):
        self.assertEqual(stats.onsets(self.rows[:3], {"yes"}), {2020: 1180})

    def test_scenarios_differ_in_what_counts(self):
        result = stats.analyse(self.rows)
        self.assertEqual(result["scenarios"]["strict"]["onsets"], [1180, 1185, 1200])
        self.assertEqual(result["scenarios"]["main"]["onsets"], [1180, 1170, 1200])
        self.assertEqual(result["scenarios"]["generous"]["years"], [2020, 2021, 2022, 2023])

    def test_copies_are_excluded(self):
        result = stats.analyse(self.rows)
        self.assertEqual(result["photo_level"]["in_martin"], 0)
        self.assertEqual(result["totals"]["kubb"], 4)
        self.assertEqual(result["totals"]["copies"], 1)
        self.assertEqual(result["totals"]["files"], len(self.rows) - 1)

    def test_every_searched_eve_is_a_friday_in_the_midsummer_week(self):
        from datetime import date
        self.assertEqual(stats.analyse(self.rows)["totals"]["years_searched"], 17)
        for year, eve in stats.EVES.items():
            day = date.fromisoformat(eve)
            self.assertEqual((day.year, day.month, day.weekday()), (year, 6, 4))
            self.assertTrue(19 <= day.day <= 25)

    def test_control_counts_non_kubb_outdoor_photos(self):
        result = stats.analyse(self.rows)
        self.assertEqual(result["control"]["martin_window_photos"], 1)
        self.assertEqual(result["control"]["martin_window_years"], [2020])

    def test_guesses_are_ranked_by_error(self):
        ida = stats.FRIEND
        g = stats.guesses([ida, ida + 10, ida - 10], [ida, ida + 10, ida - 10, stats.JANA + 10])
        others = sorted(["martin", "jana"], key=lambda k: abs(ida - {"martin": stats.MARTIN, "jana": stats.JANA}[k]))
        self.assertEqual([x["key"] for x in g], ["ida"] + others)
        self.assertAlmostEqual(g[0]["error"], 0)
        self.assertEqual(g[0]["log10_behind_best"], 0)
        self.assertGreater(g[2]["log10_behind_best"], g[1]["log10_behind_best"])
        self.assertEqual({x["key"]: x["photos_in_window"] for x in g}, {"ida": 3, "jana": 1, "martin": 0})
        self.assertEqual(g[0]["years_closest"], 3)

    def test_claim_inside_the_interval_is_flagged(self):
        s = stats.summarize({2020: stats.FRIEND - 10, 2021: stats.FRIEND + 10, 2022: stats.FRIEND})
        self.assertTrue(s["claims"]["ida"]["inside_ci"])
        self.assertFalse(s["claims"]["martin"]["inside_ci"])

    def test_by_source_keeps_sources_apart(self):
        rows = [dict(row("2011-06-24", "18:00:00", kubb="yes"), source="guest"),
                dict(row("2012-06-22", "18:20:00", kubb="yes"), source="guest"),
                dict(row("2020-06-19", "20:00:00", kubb="yes"), source="own"),
                dict(row("2021-06-25", "20:30:00", kubb="yes"), source="own"),
                dict(row("2022-06-24", "20:10:00", kubb="yes"), source="own")]
        result = stats.by_source(rows, {"yes"})
        self.assertEqual(result["guest"]["years"], [2011, 2012])
        self.assertAlmostEqual(result["guest"]["mean"], 1090)
        self.assertEqual(result["own"]["n"], 3)
        self.assertEqual(stats.analyse(rows)["per_year"][0]["onset_source"], "guest")

    def test_per_year_onset_basis(self):
        per_year = {p["year"]: p for p in stats.analyse(self.rows)["per_year"]}
        self.assertEqual(per_year[2020]["onset_basis"], "kubb")
        self.assertEqual(per_year[2021]["onset_basis"], "field")
        self.assertIsNone(per_year[2024]["onset"])


if __name__ == "__main__":
    unittest.main()
