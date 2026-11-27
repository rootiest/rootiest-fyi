# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The 404 pages for the hub and the guide."""
from .. import config
from ..html.footer import footer
from ..html.head import head
from ..html.header import header


def _page(title, home, lede, image, image_alt, app_name):
    """Return a 404 page. It is served at any path, so local files are root-relative."""
    main = f"""    <section class="hero compact">
      <img src="/favicon.svg" alt="" class="hero-logo" width="72" height="72" />
      <h1>Page not found</h1>
      <p class="lede">{lede}</p>
      <div class="actions">
        <a href="{home}" class="btn primary">{title}</a>
        <a href="{config.HUB_URL}/" class="btn">All Rootiest docs</a>
        <a href="{config.SUPPORT_URL}/" class="btn">Support</a>
      </div>
    </section>
"""
    return (head(f"Page not found - {title}", "This page does not exist.", home + "404.html", "/", image,
                 image_alt, title, robots="noindex", manifest="/manifest.webmanifest", app_name=app_name)
            + header(title, home, "/favicon.svg", config.NAV)
            + f'\n  <main id="main" class="wrap">\n{main}  </main>\n\n' + footer())


def build(with_guide=True):
    """
    SYNOPSIS
        build(with_guide=True) -> {path: html}
    DESCRIPTION
        Build 404.html for the hub and, WITH_GUIDE, email/404.html for the
        guide's own address. Caddy serves them for unknown paths. Their local
        files (stylesheet, logo) are root-relative, and exist at both the hub's
        root and the guide's, so either page works on either address. So is
        the manifest: each address answers with its own app's.
    EXAMPLE
        pages = not_found.build()
    """
    out = {"404.html": _page(config.HUB_TITLE, config.HUB_URL + "/",
                             "That page doesn't exist, or it moved. The docs index lists everything on rootiest.fyi.",
                             config.HUB_IMAGE, config.HUB_IMAGE_ALT, config.HUB_APP_NAME)}
    if with_guide:
        out[f"{config.GUIDE_DIR}/404.html"] = _page(
            config.GUIDE_TITLE, config.GUIDE_URL + "/",
            "That page isn't part of the guide, or it moved. Start again from the guide's first page.",
            config.GUIDE_IMAGE, config.GUIDE_IMAGE_ALT, config.GUIDE_APP_NAME)
    return out
