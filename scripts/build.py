#!/usr/bin/env python3
# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate rootiest.fyi into site/ (or the directory given).

Usage: python3 scripts/build.py [OUTPUT_DIR] [--catalog FILE] [--guide-content DIR] [--shots DIR]

  site/index.html           the hub, from sites.yaml
  site/404.html             the hub's not-found page
  site/email/...            the Rootiest Mail guide, from content/email/*.html
  site/email/404.html       the guide's not-found page
  site/email/assets/site.css  a copy of site/assets/site.css, so the guide is
                            complete on its own at email.rootiest.fyi

Never edit the generated files; edit the sources and rebuild. Screenshots in
site/email/shots/ are kept by hand; the build lists the ones still missing.
Standard library only.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitegen import config  # noqa: E402
from sitegen.catalog.parse import CatalogError  # noqa: E402
from sitegen.guide.fragments import FragmentError  # noqa: E402
from sitegen.guide.shots import ShotError  # noqa: E402
from sitegen.pages import guide, hub, not_found  # noqa: E402


def generate(catalog=None, guide_content=None, shots=None):
    """Return ({relative path: text}, pending shots) for every generated file."""
    files = dict(hub.build(catalog))
    pages, pending = guide.build(guide_content, Path(shots) if shots else None)
    files.update(pages)
    files.update(not_found.build(with_guide=bool(pages)))
    if pages:
        files[f"{config.GUIDE_DIR}/assets/site.css"] = (config.SITE / "assets" / "site.css").read_text()
    return files, pending


def main():
    """Write every generated file and print how many were written, and any pending screenshots."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out", nargs="?", default=str(config.SITE))
    ap.add_argument("--catalog", default=None)
    ap.add_argument("--guide-content", default=None)
    ap.add_argument("--shots", default=None, help="screenshot folder (default site/email/shots)")
    a = ap.parse_args()
    try:
        files, pending = generate(a.catalog, a.guide_content, a.shots)
    except (CatalogError, FragmentError, ShotError) as e:
        print(f"build.py: {e}", file=sys.stderr)
        sys.exit(1)
    out = Path(a.out)
    for rel, text in files.items():
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    print(f"wrote {len(files)} files to {out}")
    for page, sid, rel in pending:
        print(f"pending screenshot: {config.GUIDE_DIR}/{rel} (shot {sid}, on {config.GUIDE_DIR}/{page})")


if __name__ == "__main__":
    main()
