"""Unit tests for scripts/build_page.py. Run: python3 -m unittest discover -s scripts"""
import unittest

import build_page


class Formatting(unittest.TestCase):
    def test_sv_uses_decimal_comma_and_spaced_thousands(self):
        self.assertEqual(build_page.sv(20096.4), "20\u00a0096")
        self.assertEqual(build_page.sv(4.25, 1), "4,2")
        self.assertEqual(build_page.sv(-3, 1), "−3,0")

    def test_in_words(self):
        self.assertEqual(build_page.in_words(7), "sju")
        self.assertEqual(build_page.in_words(16), "sexton")
        self.assertEqual(build_page.in_words(21), "21")

    def test_duration(self):
        self.assertEqual(build_page.duration(223.4), "3 tim 43 min")
        self.assertEqual(build_page.duration(73), "1 tim 13 min")
        self.assertEqual(build_page.duration(45), "45 min")

    def test_pvalue_keeps_a_significant_digit(self):
        self.assertEqual(build_page.pvalue(0.84), "0,84")
        self.assertEqual(build_page.pvalue(0.0081), "0,008")
        self.assertEqual(build_page.pvalue(0.0000214), "0,00002")

    def test_signed_uses_a_real_minus(self):
        self.assertEqual(build_page.signed(2.23), "+2,2")
        self.assertEqual(build_page.signed(-24.01), "−24,0")

    def test_years_list(self):
        self.assertEqual(build_page.years_list([2021]), "2021")
        self.assertEqual(build_page.years_list([2021, 2024, 2025]), "2021, 2024 och 2025")


class Pedagogy(unittest.TestCase):
    def test_heads_in_a_row_is_still_likelier_than_p(self):
        for p in (0.0000214, 0.0081, 0.05, 0.5):
            k = build_page.heads_in_a_row(p)
            self.assertGreaterEqual(0.5 ** k, p)
            self.assertLess(0.5 ** (k + 1), p)

    def test_one_in_rounds_to_two_figures(self):
        self.assertEqual(build_page.one_in(0.0000214), "1 på 47\u00a0000")
        self.assertEqual(build_page.one_in(0.0081), "1 på 120")
        self.assertEqual(build_page.one_in(0.5), "1 på 2")

    def test_one_significant(self):
        self.assertEqual(build_page.one_significant(9.9e6), "10 miljoner")
        self.assertEqual(build_page.one_significant(1.25e6), "1 miljon")
        self.assertEqual(build_page.one_significant(3.4e9), "3 miljarder")
        self.assertEqual(build_page.one_significant(420), "400")

    def test_wrongness_rows_convert_units(self):
        html = build_page.wrongness_rows([("A", 240), ("B", 60)], 7)
        self.assertIn("60,0°", html)        # 240 minutes of rotation
        self.assertIn("20,0", html)         # km walked in four hours
        self.assertIn("28,0", html)         # hours over seven years
        self.assertIn("4,2\u00a0%", html)   # one hour as a share of a day
        self.assertIn("428\u00a0832", html) # km along the orbit in four hours
        self.assertIn(">1,12<", html)       # the same in trips to the moon
        self.assertIn(">360<", html)        # rounds of the frog song in four hours
        self.assertEqual(html.count("<tr>"), 8)
        self.assertEqual(html.count('<td class="r">'), 16)

    def test_luck_switches_wording_for_likely_results(self):
        self.assertEqual(build_page.luck(0.82), "82 av 100")
        self.assertEqual(build_page.luck(0.0001), "1 på 10\u00a0000")

    def test_luck_row_draws_one_coin_per_head(self):
        self.assertEqual(build_page.luck_row("Jana", 0.0001).count('class="coin"'), 13)
        lucky = build_page.luck_row("Ida", 0.82)
        self.assertNotIn('class="coin"', lucky)
        self.assertIn("ingen tur alls", lucky)

    def test_luck_row_single_coin_reads_as_once(self):
        row = build_page.luck_row("Ida", 0.27)
        self.assertEqual(row.count('class="coin"'), 1)
        self.assertIn("singla krona en gång", row)
        self.assertIn("13 gånger i rad", build_page.luck_row("Jana", 0.0001))

    def test_earths_switches_to_a_fraction_below_one(self):
        self.assertEqual(build_page.earths(build_page.EARTH_ATOMS_LOG10 + 0.85), "7 jordklot")
        self.assertEqual(build_page.earths(build_page.EARTH_ATOMS_LOG10), "ett jordklot")
        self.assertEqual(build_page.earths(build_page.EARTH_ATOMS_LOG10 - 1), "1/10 av jordklotet")
        self.assertEqual(build_page.earths(build_page.EARTH_ATOMS_LOG10 - 3.78), "1/6\u00a0000 av jordklotet")

    def test_one_significant_names_very_large_numbers(self):
        self.assertEqual(build_page.one_significant(5.2e24), "5 kvadriljoner")


class Render(unittest.TestCase):
    def test_replaces_every_token(self):
        self.assertEqual(build_page.render("a [[x]] b [[x]] [[y]]", {"x": 1, "y": "z"}), "a 1 b 1 z")

    def test_missing_token_is_an_error(self):
        with self.assertRaises(KeyError):
            build_page.render("[[nope]]", {})

    def test_leaves_javascript_arrays_alone(self):
        self.assertEqual(build_page.render('[["Strict", 1]]', {}), '[["Strict", 1]]')


class ChartHarness(unittest.TestCase):
    PAGE = ('<link rel="stylesheet" href="x"><style>a{}</style><div class="plot" id="fig1"></div>'
            '<div class="plot" id="fig2"></div><script>draw()</script>')

    def test_shows_only_the_chosen_chart(self):
        import build_charts
        html = build_charts.harness(self.PAGE, "fig2", width=500, row=18)
        self.assertIn('<div class="plot" id="fig2"></div>', html)
        self.assertIn('<div class="plot" id="fig1" hidden></div>', html)
        self.assertIn("width: 500px", html)
        self.assertLess(html.index("window.CHART = {row: 18}"), html.index("draw()"))

    def test_row_height_is_optional_and_unknown_charts_fail(self):
        import build_charts
        self.assertNotIn("window.CHART", build_charts.harness(self.PAGE, "fig1"))
        with self.assertRaises(KeyError):
            build_charts.harness(self.PAGE, "fig9")


if __name__ == "__main__":
    unittest.main()
