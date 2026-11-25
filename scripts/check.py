#!/usr/bin/env python3
# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the built site in site/.

Usage: python3 scripts/check.py [--online] [--site DIR] [--catalog FILE] [--guide-content DIR] [--shots DIR]

Fails (exit 1) when:
  - site/ is not what scripts/build.py generates (someone edited output by hand,
    or forgot to rebuild after changing sites.yaml, content/ or site.css);
  - an .html file in site/ is not one build.py generates (a stale page);
  - an internal link, image, stylesheet or icon reference points at nothing;
  - a guide page (site/email/) refers to a file outside site/email/, or uses a
    root-relative path that does not exist at both the hub's root and the
    guide's (the guide is served at email.rootiest.fyi/ and rootiest.fyi/email/);
  - a page loads a script, stylesheet, frame or font from another site, or an
    image from anywhere but icons.rootiest.fyi or pages.rootiest.fyi;
  - a page lacks lang, <title>, a meta description or a canonical link;
  - an in-page #fragment has no matching id.

Screenshots the guide refers to that are not in site/email/shots/ yet are
listed as pending; they show a placeholder and never fail the check.

--online also fetches every catalog URL and icon and fails on any that does not
answer 200 (after redirects). CI does not use it; run it before a release.
The other options point the check at a test build (tests/run-tests.sh).
"""
import argparse
import filecmp
import re
import subprocess
import sys
import tempfile
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from sitegen import config  # noqa: E402

IMAGE_HOSTS = ("icons.rootiest.fyi", "pages.rootiest.fyi")


class Page(HTMLParser):
    """Collects references, ids and head metadata from one HTML document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.meta = [], set(), {}
        self.title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.meta["lang"] = a.get("lang")
        if tag == "title":
            self.title = True
        if tag == "meta" and a.get("name") == "description":
            self.meta["description"] = a.get("content")
        if tag == "link" and a.get("rel") == "canonical":
            self.meta["canonical"] = a.get("href")
        if tag == "script":
            self.refs.append((tag, "src", a.get("src") or "(inline)", None))
        for attr in ("href", "src"):
            if a.get(attr) and tag != "script":
                self.refs.append((tag, attr, a[attr], a.get("rel")))
        if a.get("srcset"):
            self.refs.extend((tag, "srcset", s.split()[0], None) for s in str(a["srcset"]).split(","))


def resolve(ref, page, root):
    """Map a local reference on PAGE to the file it needs under ROOT (the web root), or None if external."""
    u = urlsplit(ref)
    if u.scheme or ref.startswith(("//", "mailto:")):
        return None
    path = unquote(u.path)
    if not path:
        return page
    f = (root / path.lstrip("/")).resolve() if path.startswith("/") else (page.parent / path).resolve()
    if path.endswith("/") or f.is_dir():
        f = f / "index.html"
    return f


def check_refs(p, parser, site, pages, problems):
    """Check every reference on page P (parsed as PARSER) and append problems."""
    rel = p.relative_to(site.parent)
    guide_root = site / config.GUIDE_DIR
    in_guide = guide_root in p.parents
    for tag, attr, ref, rel_attr in parser.refs:
        if tag == "script":
            problems.append(f"{rel}: <script> {ref} (the site runs without JavaScript)")
            continue
        u = urlsplit(ref)
        external = u.scheme in ("http", "https") or ref.startswith("//")
        loads = tag in ("iframe", "embed", "object") or (
            tag == "link" and rel_attr in ("stylesheet", "preload", "modulepreload"))
        if external and loads:
            problems.append(f"{rel}: third-party {tag} {ref}")
        if external and tag in ("img", "source") and u.hostname not in IMAGE_HOSTS:
            problems.append(f"{rel}: image from {u.hostname} (only {', '.join(IMAGE_HOSTS)})")
        if tag == "link" and rel_attr == "canonical":
            continue
        rooted = u.path.startswith("/") and not ref.startswith("//")
        roots = [site, guide_root] if in_guide and rooted else [site]
        for root in roots:
            f = resolve(ref, p, root)
            if f is None:
                break
            if in_guide and not rooted and guide_root not in f.parents:
                problems.append(f"{rel}: {attr} {ref} leaves the guide (it would break at {config.GUIDE_URL})")
                break
            if not f.exists():
                where = f" under {root.relative_to(site.parent)}/" if len(roots) > 1 else ""
                problems.append(f"{rel}: broken {attr} {ref}{where}")
                continue
            frag = u.fragment
            if frag and f.suffix == ".html" and f in pages and frag not in pages[f].ids:
                problems.append(f"{rel}: no #{frag} in {f.relative_to(site.parent)}")


def online(catalog, problems):
    """Fetch every catalog URL and icon; append a problem for any that does not answer 200."""
    from sitegen.catalog.load import load
    urls = set()
    for cat in load(catalog):
        for s in cat.sites:
            urls.update([s.url, s.icon] + ([s.repo] if s.repo else []) + [lk.url for lk in s.links])
    for url in sorted(urls):
        # Cloudflare refuses Python's default User-Agent (fish.rootiest.fyi answers 403).
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; link-check)"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
        except Exception as e:  # noqa: BLE001 - any failure is the finding
            code = getattr(e, "code", None) or type(e).__name__
        if code != 200:
            problems.append(f"online: {url} answered {code}")
    print(f"{len(urls)} URLs fetched")


def main():
    """Run every check and print problems; exit 1 if there are any."""
    ap = argparse.ArgumentParser(description="Check the built site.")
    ap.add_argument("--online", action="store_true")
    ap.add_argument("--site", default=str(config.SITE))
    ap.add_argument("--catalog", default=None)
    ap.add_argument("--guide-content", default=None)
    ap.add_argument("--shots", default=None)
    a = ap.parse_args()
    site = Path(a.site).resolve()
    problems = []

    opts = []
    for flag, val in (("--catalog", a.catalog), ("--guide-content", a.guide_content), ("--shots", a.shots)):
        if val:
            opts += [flag, val]
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py"), tmp] + opts,
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stderr.strip() or r.stdout.strip())
            print("build failed, nothing else checked")
            sys.exit(1)
        pending = [ln for ln in r.stdout.splitlines() if ln.startswith("pending screenshot:")]
        for f in Path(tmp).rglob("*"):
            if f.is_file():
                live = site / f.relative_to(tmp)
                if not live.exists() or not filecmp.cmp(f, live, shallow=False):
                    problems.append(f"{live.relative_to(site.parent)}: out of date, run scripts/build.py")
        built = {f.relative_to(tmp) for f in Path(tmp).rglob("*.html")}
        for live in site.rglob("*.html"):
            if live.relative_to(site) not in built:
                problems.append(f"{live.relative_to(site.parent)}: not generated by scripts/build.py, delete it")

    pages = {p.resolve(): Page() for p in site.rglob("*.html")}
    for p, parser in pages.items():
        parser.feed(p.read_text())

    for p, parser in pages.items():
        rel = p.relative_to(site.parent)
        m = parser.meta
        if not parser.title or not m.get("canonical"):
            problems.append(f"{rel}: missing <title> or canonical link")
        if not m.get("lang") or not m.get("description"):
            problems.append(f"{rel}: missing lang or meta description")
        check_refs(p, parser, site, pages, problems)

    for css in site.rglob("*.css"):
        for ref in re.findall(r"url\(([^)]+)\)", css.read_text()):
            ref = ref.strip("'\"")
            if ref.startswith(("http", "//")):
                problems.append(f"{css.relative_to(site.parent)}: third-party url({ref})")

    if a.online:
        online(a.catalog or config.CATALOG, problems)

    for line in pending:
        print(line)
    for line in problems:
        print(line)
    print(f"{len(pages)} pages checked, {len(problems)} problem(s), {len(pending)} screenshot(s) pending")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
