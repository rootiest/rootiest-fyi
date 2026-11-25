# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read the guide's pages: HTML fragments with title, description and order comments."""
import re
from dataclasses import dataclass
from pathlib import Path

HEADER = re.compile(r"^\s*<!--\s*([a-z]+)\s*:\s*(.*?)\s*-->[ \t]*\n?")
SLUG = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
REQUIRED = ("title", "description", "order")


class FragmentError(ValueError):
    """A guide page that cannot be built."""


@dataclass
class Fragment:
    """One guide page."""
    slug: str          # "" for the landing page (index.html)
    title: str
    description: str
    order: int
    body: str          # the HTML after the header comments

    @property
    def depth(self):
        """How many folders below the guide root the built page sits (0 or 1)."""
        return 0 if self.slug == "" else 1

    @property
    def out(self):
        """The built page's path relative to the guide root."""
        return "index.html" if self.slug == "" else f"{self.slug}/index.html"

    @property
    def path(self):
        """The page's URL path relative to the guide root ("" or "slug/")."""
        return "" if self.slug == "" else f"{self.slug}/"


def read_fragment(path):
    """
    SYNOPSIS
        read_fragment(path) -> Fragment
    DESCRIPTION
        Read one fragment. Its leading comments name the page:
            <!-- title: Page title -->
            <!-- description: One sentence. -->
            <!-- order: 10 -->
        index.html is the landing page (slug ""); any other file's slug is its
        name without .html, and must be lower-case letters, digits and hyphens.
        Raises FragmentError on a missing or malformed header.
    EXAMPLE
        read_fragment(Path("content/email/phone.html")).title
    """
    path = Path(path)
    text = path.read_text()
    meta = {}
    while True:
        m = HEADER.match(text)
        if not m:
            break
        if m.group(1) in meta:
            raise FragmentError(f"{path}: duplicate '{m.group(1)}' header")
        meta[m.group(1)] = m.group(2)
        text = text[m.end():]
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        raise FragmentError(f"{path}: missing header comment(s): {', '.join(missing)}")
    if not re.fullmatch(r"-?[0-9]+", meta["order"]):
        raise FragmentError(f"{path}: order must be a whole number, not {meta['order']!r}")
    slug = "" if path.name == "index.html" else path.stem
    if slug and not SLUG.match(slug):
        raise FragmentError(f"{path}: file name must be lower-case letters, digits and hyphens")
    return Fragment(slug, meta["title"], meta["description"], int(meta["order"]), text.strip("\n") + "\n")


def read_guide(folder):
    """
    SYNOPSIS
        read_guide(folder) -> [Fragment]
    DESCRIPTION
        Read every *.html fragment in FOLDER, landing page first, then by
        order and title. Returns [] when FOLDER does not exist (the guide is
        then left out of the build). Raises FragmentError when there are pages
        but no index.html. Pages with the same order sort by title.
    EXAMPLE
        pages = read_guide(Path("content/email"))
    """
    folder = Path(folder)
    if not folder.is_dir():
        return []
    pages = [read_fragment(p) for p in sorted(folder.glob("*.html"))]
    if not pages:
        return []
    if not any(p.slug == "" for p in pages):
        raise FragmentError(f"{folder}: no index.html (the guide's landing page)")
    pages.sort(key=lambda p: (p.slug != "", p.order, p.title.lower()))
    return pages
