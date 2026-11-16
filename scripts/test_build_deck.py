import tempfile
import unittest
from pathlib import Path

import build_deck

DECK = {"title": "Kubb & co", "order": ["b", "a"],
        "faces": {"x": {"family": "X", "href": "https://fonts.googleapis.com/css2?family=X&display=swap"}}}


def slide(name, body=""):
    return f'<section id="{name}">{body}<aside>notes {name}</aside></section>\n'


class ReadSlides(unittest.TestCase):
    def test_follows_the_deck_order(self):
        with tempfile.TemporaryDirectory() as d:
            for name in "ab":
                Path(d, f"{name}.html").write_text(slide(name))
            self.assertEqual(build_deck.read_slides(DECK, Path(d)), [slide("b"), slide("a")])

    def test_slide_without_its_id_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.html").write_text(slide("a"))
            Path(d, "b.html").write_text(slide("other"))
            with self.assertRaises(ValueError):
                build_deck.read_slides(DECK, Path(d))

    def test_missing_slide_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.html").write_text(slide("a"))
            with self.assertRaises(FileNotFoundError):
                build_deck.read_slides(DECK, Path(d))


class ChartsUsed(unittest.TestCase):
    def test_each_chart_once_and_sorted(self):
        slides = [slide("a", '<img src="charts/fig3.png">'), slide("b", '<img src="charts/fig1.png"><img src="charts/fig3.png">')]
        self.assertEqual(build_deck.charts_used(slides), ["fig1", "fig3"])

    def test_no_charts(self):
        self.assertEqual(build_deck.charts_used([slide("a")]), [])


class Page(unittest.TestCase):
    def test_keeps_slides_in_order_with_notes(self):
        out = build_deck.page(DECK, [slide("b"), slide("a")])
        self.assertLess(out.index('id="b"'), out.index('id="a"'))
        self.assertIn("<aside>notes a</aside>", out)

    def test_escapes_title_and_loads_fonts(self):
        out = build_deck.page(DECK, [slide("a")])
        self.assertIn("<title>Kubb &amp; co</title>", out)
        self.assertIn('href="https://fonts.googleapis.com/css2?family=X&amp;display=swap"', out)

    def test_no_artifact_asset_links_left(self):
        out = build_deck.page(DECK, [slide("a", '<img src="charts/fig1.png">')])
        self.assertNotIn("/_blob/", out)


if __name__ == "__main__":
    unittest.main()
