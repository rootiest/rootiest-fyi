#!/usr/bin/env python3
# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for the generator: the catalog subset parser, the loader, and the guide renderer.

Run: python3 tests/test_sitegen.py   (tests/run-tests.sh runs it)
The guide is rendered from the fixture in tests/fixtures/email/, never from content/email/.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

from sitegen.catalog.load import load  # noqa: E402
from sitegen.catalog.parse import CatalogError, parse  # noqa: E402
from sitegen.guide.fragments import FragmentError, read_fragment  # noqa: E402
from sitegen.guide.shots import ShotError, dark_name, render_shots  # noqa: E402

try:
    import yaml
except ImportError:
    yaml = None


class ParseTests(unittest.TestCase):
    def test_subset(self):
        text = ('# c\nsites:\n  - label: a\n    order: 10\n    tags: [x, "y, z"]\n'
                '    links:\n      - title: "A: b"\n        url: https://x.dev/a#b\n')
        self.assertEqual(parse(text), {"sites": [{"label": "a", "order": 10, "tags": ["x", "y, z"],
                                                  "links": [{"title": "A: b", "url": "https://x.dev/a#b"}]}]})

    def test_sequence_at_key_indent(self):
        self.assertEqual(parse("a:\n- x\n- z\nb: 1\n"), {"a": ["x", "z"], "b": 1})

    def test_refuses(self):
        for bad in ("a: yes\n", "a: 1.5\n", "a: x: y\n", "a: x #c\n", "a: 'x'\n", "a: |\n  x\n",
                    "a: 1\na: 2\n", "a:\n\tb: 1\n", "a: &x 1\n", "a: 2026-11-25\n", "a: 0x1F\n",
                    "a: null\n", "a: [x\n", "a: \"x\n", "a:\n", "a: 1 \n", "  a: 1\n", "a:\n    b: 1\n  c: 2\n"):
            with self.subTest(bad=bad), self.assertRaises(CatalogError):
                parse(bad)

    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_same_as_pyyaml(self):
        text = (ROOT / "sites.yaml").read_text()
        self.assertEqual(parse(text), yaml.safe_load(text))


class LoadTests(unittest.TestCase):
    def _load(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(text)
        try:
            return load(f.name)
        finally:
            Path(f.name).unlink()

    SITE = ("  - label: a\n    url: https://a.rootiest.fyi\n    title: A\n    description: The A site.\n"
            "    icon: icons.rootiest.fyi/color/logo.svg\n    category: C\n    order: 10\n")

    def test_real_catalog(self):
        cats = load(ROOT / "sites.yaml")
        self.assertTrue(cats)
        for c in cats:
            for s in c.sites:
                self.assertTrue(s.icon.startswith("https://"), s.label)

    def test_icon_path_gets_https(self):
        cats = self._load("categories:\n  - name: C\nsites:\n" + self.SITE)
        self.assertEqual(cats[0].sites[0].icon, "https://icons.rootiest.fyi/color/logo.svg")

    def test_errors(self):
        cases = {
            "unknown key": self.SITE + "    colour: red\n",
            "unknown category": self.SITE.replace("category: C", "category: D"),
            "duplicate label": self.SITE + self.SITE.replace("a.rootiest", "b.rootiest"),
            "bad icon": self.SITE.replace("icons.rootiest.fyi/color", "example.com"),
            "missing field": self.SITE.replace("    title: A\n", ""),
            "http url": self.SITE.replace("https://a", "http://a"),
        }
        for name, sites in cases.items():
            with self.subTest(name), self.assertRaises(CatalogError):
                self._load("categories:\n  - name: C\nsites:\n" + sites)


class GuideTests(unittest.TestCase):
    def test_fragment_header(self):
        f = read_fragment(FIX / "email" / "webmail.html")
        self.assertEqual((f.slug, f.title, f.order, f.out), ("webmail", "Webmail", 10, "webmail/index.html"))
        self.assertFalse(f.body.startswith("<!--"))

    def test_fragment_missing_header(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.html"
            p.write_text("<!-- title: X -->\n<p>x</p>\n")
            with self.assertRaises(FragmentError):
                read_fragment(p)

    def test_shot_forms(self):
        shots = FIX / "shots"
        for src in ("shots/webmail-login.png", "../shots/webmail-login.png", "./shots/webmail-login.png"):
            fig = f'<figure class="shot" data-shot="webmail-login"><img src="{src}" alt="A"></figure>'
            html, pending = render_shots(fig, 1, shots)
            self.assertIn('src="../shots/webmail-login.png"', html)
            self.assertEqual(pending, [])
            html, _ = render_shots(fig, 0, shots)
            self.assertIn('src="shots/webmail-login.png"', html)

    def test_shot_dark_version(self):
        shots = FIX / "shots"
        fig = '<figure class="shot" data-shot="webmail-login"><img src="../shots/webmail-login.png" alt="A"></figure>'
        dark = shots / "webmail-login-dark.png"
        try:
            dark.write_bytes((shots / "webmail-login.png").read_bytes())
            html, pending = render_shots(fig, 1, shots)
        finally:
            dark.unlink()
        self.assertEqual(pending, [])
        self.assertIn('<picture><source srcset="../shots/webmail-login-dark.png" media="(prefers-color-scheme: dark)" />', html)
        self.assertIn('src="../shots/webmail-login.png"', html)
        plain, _ = render_shots(fig, 1, shots)
        self.assertNotIn("<picture>", plain)

    def test_dark_name(self):
        self.assertEqual(dark_name("shots/a-b.png"), "shots/a-b-dark.png")

    def test_shot_placeholder(self):
        fig = '<figure class="shot" data-shot="nope"><img src="../shots/nope.png" alt="Alt text"><figcaption>C</figcaption></figure>'
        html, pending = render_shots(fig, 1, FIX / "shots")
        self.assertEqual(pending, [("nope", "shots/nope.png")])
        self.assertNotIn("<img", html)
        self.assertIn("shot-pending", html)
        self.assertIn("Alt text", html)
        self.assertIn("nope", html)
        self.assertIn("<figcaption>C</figcaption>", html)

    def test_shot_errors(self):
        for fig in ('<figure class="shot"><img src="shots/a.png" alt="A"></figure>',
                    '<figure class="shot" data-shot="a"><img src="shots/a.png"></figure>',
                    '<figure class="shot" data-shot="a"><img src="/shots/a.png" alt="A"></figure>',
                    '<figure class="shot" data-shot="a"><img src="img/a.png" alt="A"></figure>'):
            with self.subTest(fig=fig), self.assertRaises(ShotError):
                render_shots(fig, 0, FIX / "shots")

    def test_other_figures_untouched(self):
        fig = '<figure class="diagram"><img src="x.svg" alt=""></figure>'
        self.assertEqual(render_shots(fig, 0, FIX / "shots"), (fig, []))


class BuildTests(unittest.TestCase):
    """Build the whole site with the fixture guide and run check.py on it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.site = Path(cls.tmp) / "site"
        shutil.copytree(ROOT / "site", cls.site, ignore=shutil.ignore_patterns("*.html"))
        shutil.copytree(FIX / "shots", cls.site / "email" / "shots", dirs_exist_ok=True)
        cls.args = ["--guide-content", str(FIX / "email"), "--shots", str(FIX / "shots")]
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), str(cls.site)] + cls.args,
                       check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def read(self, rel):
        return (self.site / rel).read_text()

    def test_outputs(self):
        for rel in ("index.html", "404.html", "email/index.html", "email/webmail/index.html",
                    "email/phone/index.html", "email/404.html", "email/assets/site.css"):
            self.assertTrue((self.site / rel).is_file(), rel)
        self.assertEqual(self.read("email/assets/site.css"), (ROOT / "site/assets/site.css").read_text())

    def test_check_passes_with_pending_shots(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check.py"), "--site", str(self.site)] + self.args,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("2 screenshot(s) pending", r.stdout)

    def test_guide_pages_are_relative(self):
        for rel in ("email/index.html", "email/webmail/index.html", "email/phone/index.html"):
            html = self.read(rel)
            self.assertEqual(re.findall(r'(?:href|src)="/(?!/)[^"]*"', html), [], rel)
            self.assertIn('href="https://rootiest.fyi/"', html)
            self.assertIn('href="https://support.rootiest.dev/"', html)

    def test_nav_order_and_current(self):
        html = self.read("email/phone/index.html")
        nav = re.search(r'<nav class="guide-nav".*?</nav>', html, re.S).group(0)
        self.assertEqual(re.findall(r'href="([^"]+)"', nav), ["../", "../webmail/", "../phone/"])
        self.assertIn('href="../phone/" aria-current="page"', nav)

    def test_own_h1_kept_once(self):
        self.assertEqual(self.read("email/phone/index.html").count("<h1"), 1)
        self.assertIn("<h1>Webmail</h1>", self.read("email/webmail/index.html"))

    def test_check_catches_breakage(self):
        page = self.site / "email" / "webmail" / "index.html"
        good = page.read_text()
        try:
            page.write_text(good.replace('href="../phone/#imap"', 'href="../../index.html"'))
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check.py"), "--site", str(self.site)]
                               + self.args, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("leaves the guide", r.stdout)
            self.assertIn("out of date", r.stdout)
        finally:
            page.write_text(good)


if __name__ == "__main__":
    unittest.main(verbosity=1)
