# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The site header: brand and a row of links."""
from html import escape


def header(brand, home, logo, links):
    """
    SYNOPSIS
        header(brand, home, logo, links) -> str
    DESCRIPTION
        Return the site header. BRAND is the name beside LOGO (an image path),
        both linking to HOME; LINKS is a list of (href, label) on the right.
    EXAMPLE
        header("Rootiest Docs", "./", "favicon.svg", config.NAV)
    """
    nav = "\n".join(f'        <a href="{escape(h)}">{escape(t)}</a>' for h, t in links)
    return f"""  <header class="site-header">
    <div class="wrap">
      <a href="{escape(home)}" class="brand"><img src="{escape(logo)}" alt="" width="28" height="28" />{escape(brand)}</a>
      <nav class="nav" aria-label="Main">
{nav}
      </nav>
    </div>
  </header>
"""
