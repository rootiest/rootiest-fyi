# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The Rootiest Mail guide: site/email/, built from content/email/."""
import re
from html import escape

from .. import config
from ..guide.fragments import read_guide
from ..guide.shots import render_shots
from ..html.footer import footer
from ..html.head import head
from ..html.header import header

H1 = re.compile(r"<h1[\s>]", re.I)


def _href(page, target):
    """Relative link from PAGE to TARGET, both fragments of the guide."""
    up = "../" * page.depth
    return (up + target.path) or "./"


def _nav(pages, current):
    """The list of every guide page, the current one marked."""
    mark = ' aria-current="page"'
    items = "\n".join(
        f'          <li><a href="{_href(current, p)}"{mark if p is current else ""}>{escape(p.title)}</a></li>'
        for p in pages)
    return f"""      <nav class="guide-nav" aria-label="Guide pages">
        <h2>In this guide</h2>
        <ol>
{items}
        </ol>
      </nav>
"""


def _pager(pages, i):
    """Previous and next links at the bottom of page I."""
    cur, parts = pages[i], []
    if i > 0:
        p = pages[i - 1]
        parts.append(f'<a class="prev" href="{_href(cur, p)}"><span>Previous</span>{escape(p.title)}</a>')
    if i + 1 < len(pages):
        p = pages[i + 1]
        parts.append(f'<a class="next" href="{_href(cur, p)}"><span>Next</span>{escape(p.title)}</a>')
    if not parts:
        return ""
    return '\n        <nav class="pager" aria-label="Previous and next page">' + "".join(parts) + "</nav>"


def build(content=None, shots_dir=None):
    """
    SYNOPSIS
        build(content=None, shots_dir=None) -> ({path: html}, pending)
    DESCRIPTION
        Build the guide from the fragments in CONTENT (config.GUIDE_CONTENT by
        default): index.html becomes email/index.html, <slug>.html becomes
        email/<slug>/index.html. Each page gets the guide header, the list of
        every page by order, the fragment (with an <h1> from its title unless
        it has its own), previous/next links and a footer that leads back to
        the hub and to support. Every link and file reference the layout adds
        is relative, so the same files work at email.rootiest.fyi/ and at
        rootiest.fyi/email/. Screenshots are resolved against SHOTS_DIR
        (site/email/shots by default); PENDING lists those not there yet.
        Returns ({}, []) when there is no guide content.
    EXAMPLE
        pages, pending = guide.build()
    """
    pages = read_guide(content or config.GUIDE_CONTENT)
    shots_dir = shots_dir or (config.SITE / config.GUIDE_DIR / "shots")
    out, pending = {}, []
    for i, page in enumerate(pages):
        up = "../" * page.depth
        body, waiting = render_shots(page.body, page.depth, shots_dir, f"{config.GUIDE_DIR}/{page.out}")
        pending += [(page.out, sid, rel) for sid, rel in waiting]
        if not H1.search(body):
            body = f"<h1>{escape(page.title)}</h1>\n{body}"
        title = config.GUIDE_TITLE if page.slug == "" else f"{page.title} - {config.GUIDE_TITLE}"
        url = f"{config.GUIDE_URL}/{page.path}"
        # Root-relative on purpose: at email.rootiest.fyi it is the guide's own
        # manifest, at rootiest.fyi/email/ the hub's, so there the guide offers
        # the Rootiest Docs app (whose scope holds it) instead of a second app.
        html = (head(title, page.description, url, up, config.GUIDE_IMAGE, config.GUIDE_IMAGE_ALT,
                     config.GUIDE_TITLE, manifest="/manifest.webmanifest", app_name=config.GUIDE_APP_NAME)
                + header(config.GUIDE_TITLE, up or "./", up + "favicon.svg",
                         [(config.HUB_URL + "/", "All docs"), (config.SUPPORT_URL + "/", "Support")])
                + '\n  <div class="wrap guide-layout">\n'
                + _nav(pages, page)
                + f'      <main id="main" class="guide">\n{body}{_pager(pages, i)}\n      </main>\n'
                + "  </div>\n\n"
                + footer())
        out[f"{config.GUIDE_DIR}/{page.out}"] = html
    return out, pending
