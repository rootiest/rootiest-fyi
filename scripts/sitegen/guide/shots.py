# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screenshots in guide pages: point them at shots/, or show a placeholder until the image exists."""
import re
from html import escape
from html.parser import HTMLParser

FIGURE = re.compile(r"<figure\b(?P<attrs>[^>]*)>(?P<body>.*?)</figure>", re.S)
IMG = re.compile(r"<img\b[^>]*>", re.S)
SHOT_ID = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


class ShotError(ValueError):
    """A screenshot figure that does not follow the contract."""


class _Attrs(HTMLParser):
    """Collects the attributes of the first start tag fed to it."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is None:
            self.attrs = dict(attrs)

    handle_startendtag = handle_starttag


def _attrs(tag_html):
    """Return the attributes of the start tag TAG_HTML as a dict."""
    p = _Attrs()
    p.feed(tag_html if tag_html.startswith("<") else f"<x {tag_html}>")
    return p.attrs or {}


def _guide_path(src, where):
    """Return SRC as a path from the guide root ("shots/<file>"), whatever its leading ./ or ../ parts."""
    rest = src
    while rest.startswith(("./", "../")):
        rest = rest.split("/", 1)[1]
    if not rest.startswith("shots/") or "/" in rest[len("shots/"):] or rest.startswith(("/", "http")):
        raise ShotError(f"{where}: screenshot src {src!r} must be shots/<file> relative to the page")
    return rest


def render_shots(body, depth, shots_dir, where="page"):
    """
    SYNOPSIS
        render_shots(body, depth, shots_dir, where="page") -> (html, pending)
    DESCRIPTION
        Rewrite every <figure class="shot" data-shot="ID"> in BODY. Its <img src>
        is taken as relative to the page and must name a file in shots/: on the
        landing page "shots/ID.png", on any other page "../shots/ID.png" (the
        landing-page form is accepted everywhere too). The src is rewritten to
        the correct relative path for a page DEPTH folders below the guide root.
        When the file is not in SHOTS_DIR yet, the image is replaced by a
        placeholder showing the alt text and the shot id, so the page never
        shows a broken image. Returns the new HTML and the list of pending
        (id, file) pairs. Raises ShotError for a figure without an id, an img,
        an alt text, or with a src outside shots/.
    EXAMPLE
        html, pending = render_shots(frag.body, 1, Path("site/email/shots"))
    """
    pending = []
    prefix = "../" * depth

    def figure(m):
        fa = _attrs(m.group("attrs"))
        if "shot" not in (fa.get("class") or "").split():
            return m.group(0)
        sid = fa.get("data-shot") or ""
        if not SHOT_ID.match(sid):
            raise ShotError(f"{where}: shot figure needs data-shot=\"<id>\" (lower-case, digits, hyphens), got {sid!r}")
        imgs = IMG.findall(m.group("body"))
        if len(imgs) != 1:
            raise ShotError(f"{where}: shot {sid!r} needs exactly one <img>")
        ia = _attrs(imgs[0])
        alt = (ia.get("alt") or "").strip()
        if not alt:
            raise ShotError(f"{where}: shot {sid!r} needs alt text")
        rel = _guide_path(ia.get("src") or "", f"{where}: shot {sid!r}")
        if (shots_dir / rel[len("shots/"):]).is_file():
            width = f' width="{escape(ia["width"])}"' if ia.get("width") else ""
            height = f' height="{escape(ia["height"])}"' if ia.get("height") else ""
            new = f'<img src="{prefix}{escape(rel)}" alt="{escape(alt)}"{width}{height} loading="lazy" />'
            cls = "shot"
        else:
            pending.append((sid, rel))
            new = (f'<span class="shot-placeholder" role="img" aria-label="{escape(alt)}">'
                   f'<span class="shot-alt">{escape(alt)}</span>'
                   f'<span class="shot-id">Screenshot {escape(sid)} coming soon</span></span>')
            cls = "shot shot-pending"
        body = m.group("body").replace(imgs[0], new, 1)
        return f'<figure class="{cls}" data-shot="{escape(sid)}">{body}</figure>'

    return FIGURE.sub(figure, body), pending
