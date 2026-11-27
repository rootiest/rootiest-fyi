# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The installable apps: web app manifests for the hub and the guide, and the
go/<label>/ pages the hub's shortcuts open."""
import json
import re
from html import escape

from .. import config
from ..catalog.load import load
from ..guide.fragments import read_guide

MANIFEST = "manifest.webmanifest"
ICON_SVG = re.compile(r"^https://icons\.rootiest\.fyi/color/([a-z0-9-]+)\.svg$")


def _icons(name):
    """The app icons kept by hand in icons/ next to the manifest: <name>-192, -512 and -maskable-512."""
    return [
        {"src": f"icons/{name}-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": f"icons/{name}-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": f"icons/{name}-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ]


def _manifest(name, short_name, desc, icons, shortcuts):
    """Return a manifest as JSON text. Every URL in it is relative to the manifest itself."""
    m = {
        "name": name,
        "short_name": short_name,
        "description": desc,
        "lang": "en-US",
        "dir": "ltr",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": config.APP_BACKGROUND,
        "theme_color": config.APP_BACKGROUND,
        "categories": ["books", "education", "utilities"],
        "icons": icons,
    }
    if shortcuts:
        m["shortcuts"] = shortcuts
    return json.dumps(m, indent=2, ensure_ascii=False) + "\n"


def _shortcut_icon(site):
    """The 96 px raster of a catalog icon on icons.rootiest.fyi, or None for any other icon."""
    m = ICON_SVG.match(site.icon)
    if not m:
        return None
    return [{"src": f"{config.ICONS}/{m.group(1)}/{m.group(1)}-96px.png", "sizes": "96x96", "type": "image/png"}]


def _go_page(site):
    """A page that sends the visitor on to SITE's URL, without JavaScript."""
    url = escape(site.url)
    return f"""<!DOCTYPE html>
{config.LICENSE_COMMENT}
<html lang="en-US">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="0; url={url}" />
  <title>{escape(site.title)}</title>
  <meta name="description" content="On to {escape(site.title)}." />
  <meta name="robots" content="noindex" />
  <meta name="color-scheme" content="light dark" />
  <link rel="canonical" href="{url}" />
  <link rel="stylesheet" href="../../assets/site.css" />
</head>

<body>
  <main id="main" class="wrap">
    <p>On to <a href="{url}">{escape(site.title)}</a>.</p>
  </main>
</body>
</html>
"""


def build(catalog=None, guide_content=None):
    """
    SYNOPSIS
        build(catalog=None, guide_content=None) -> {path: text}
    DESCRIPTION
        Build the hub's manifest.webmanifest (Rootiest Docs, "Docs" on the
        launcher) and, when the guide has pages, email/manifest.webmanifest
        (Rootiest Mail guide, "Mail guide"). Each app's scope is the folder of
        its manifest. The hub's shortcuts are the catalog sites with a
        `shortcut` name, in hub order: the guide opens at email/ (inside the
        hub's scope), any other site through go/<label>/, which redirects to
        it. The guide's shortcuts are its pages with a shortcut comment.
        The icons the manifests list are kept by hand in icons/ and
        email/icons/.
    EXAMPLE
        files = app.build()
    """
    sites = [s for c in load(catalog or config.CATALOG) for s in c.sites]
    out, shortcuts = {}, []
    for s in sites:
        if not s.shortcut:
            continue
        if s.url.rstrip("/") == config.GUIDE_URL:
            url = config.GUIDE_MOUNT.lstrip("/")
        else:
            url = f"{config.GO_DIR}/{s.label}/"
            out[f"{config.GO_DIR}/{s.label}/index.html"] = _go_page(s)
        sc = {"name": s.title, "short_name": s.shortcut, "description": s.description, "url": url}
        icon = _shortcut_icon(s)
        if icon:
            sc["icons"] = icon
        shortcuts.append(sc)
    out[MANIFEST] = _manifest(config.HUB_TITLE, config.HUB_APP_NAME, config.HUB_DESC, _icons("docs"), shortcuts)

    pages = read_guide(guide_content or config.GUIDE_CONTENT)
    if pages:
        index = pages[0]
        out[f"{config.GUIDE_DIR}/{MANIFEST}"] = _manifest(
            config.GUIDE_TITLE, config.GUIDE_APP_NAME, index.description, _icons("mail"),
            [{"name": p.title, "short_name": p.shortcut, "url": p.path or "./"} for p in pages if p.shortcut])
    return out
