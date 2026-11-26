# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The hub: site/index.html, built from the catalog."""
from html import escape

from .. import config
from ..catalog.load import load
from ..html.card import card
from ..html.footer import footer
from ..html.head import head
from ..html.header import header
from ..html.slug import slug

HUES = ("red", "blue", "green", "mauve", "peach", "sky", "yellow", "lavender")
LEDE = ("Guides, cheatsheets, icons and shared files from Rootiest. "
        "Everything here is public, so open whatever helps.")


def _section(i, cat):
    """Return one category's <section> with its cards."""
    blurb = f'\n      <p class="section-blurb">{escape(cat.blurb)}</p>' if cat.blurb else ""
    cards = "".join(card(s) for s in cat.sites)
    return f"""    <section class="section" id="{slug(cat.name)}">
      <div class="section-head">
        <h2>{escape(cat.name)}</h2>
      </div>{blurb}
      <div class="grid hue-{HUES[i % len(HUES)]}">
{cards}      </div>
    </section>
"""


def build(catalog=None):
    """
    SYNOPSIS
        build(catalog=None) -> {path: html}
    DESCRIPTION
        Build index.html from the catalog at CATALOG (config.CATALOG by
        default): a short intro, a jump list, then one section per category.
    EXAMPLE
        pages = hub.build()
    """
    cats = load(catalog or config.CATALOG)
    jump = " · ".join(f'<a href="#{slug(c.name)}">{escape(c.name)}</a>' for c in cats)
    main = f"""    <section class="hero compact">
      <img src="favicon.svg" alt="" class="hero-logo" width="72" height="72" />
      <h1>{config.HUB_TITLE}</h1>
      <p class="lede">{LEDE}</p>
      <p class="jump" aria-label="Jump to">{jump}</p>
    </section>

""" + "\n".join(_section(i, c) for i, c in enumerate(cats))
    page = (head(config.HUB_TITLE, config.HUB_DESC, config.HUB_URL + "/", "", config.HUB_IMAGE,
                 config.HUB_IMAGE_ALT, config.HUB_TITLE)
            + header(config.HUB_TITLE, "./", "favicon.svg", config.NAV)
            + f'\n  <main id="main" class="wrap">\n{main}  </main>\n\n'
            + footer([lk for lk in config.FOOTER_LINKS if not lk[0].startswith(config.HUB_URL)]))
    return {"index.html": page}
