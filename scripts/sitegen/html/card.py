# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A card for one site on the hub."""
from html import escape


def card(site):
    """
    SYNOPSIS
        card(site) -> str
    DESCRIPTION
        Return the <article class="card"> for SITE (sitegen.catalog.load.Site):
        its icon, title (the link; the whole card is clickable), status badge,
        description, host name and tags, then any source and extra links. Works
        without JavaScript: the title link stretches over the card and the
        extra links sit above it.
    EXAMPLE
        card(site)
    """
    pill = f' <span class="pill">{escape(site.status)}</span>' if site.status else ""
    meta = "".join(f"<span>{escape(m)}</span>" for m in [site.host] + [f"#{t}" for t in site.tags])
    extra = [(site.repo, "Source")] if site.repo else []
    extra += [(link.url, link.title) for link in site.links]
    links = ""
    if extra:
        links = ('\n            <p class="card-links">'
                 + " ".join(f'<a href="{escape(u)}">{escape(t)}</a>' for u, t in extra) + "</p>")
    return f"""        <article class="card">
          <img class="site-icon" src="{escape(site.icon)}" alt="" width="48" height="48" loading="lazy" />
          <div class="card-body">
            <h3><a class="card-link" href="{escape(site.url)}">{escape(site.title)}</a>{pill}</h3>
            <p>{escape(site.description)}</p>
            <span class="meta">{meta}</span>{links}
          </div>
        </article>
"""
