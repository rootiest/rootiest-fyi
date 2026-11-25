# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The document head: metadata, icons and link-preview tags."""
from html import escape

from .. import config


def head(title, desc, url, prefix, image, image_alt, site_name, robots="index, follow"):
    """
    SYNOPSIS
        head(title, desc, url, prefix, image, image_alt, site_name, robots="index, follow") -> str
    DESCRIPTION
        Return everything from <!DOCTYPE html> through <body>. URL is the page's
        canonical address (also its Open Graph URL). PREFIX is put in front of
        the local stylesheet and icons: "" or "../" for pages that must work
        at more than one address, "/" for error pages served at any path. The
        page loads nothing from other sites: no scripts, fonts or embeds.
    EXAMPLE
        head("Rootiest Docs", "...", "https://rootiest.fyi/", "", config.HUB_IMAGE, "Rootiest logo", "Rootiest Docs")
    """
    t, d, alt = escape(title), escape(desc), escape(image_alt)
    return f"""<!DOCTYPE html>
{config.LICENSE_COMMENT}
<html lang="en-US">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{t}</title>
  <meta name="description" content="{d}" />
  <meta name="robots" content="{robots}" />
  <meta name="author" content="Chris Laprade" />
  <meta name="color-scheme" content="light dark" />
  <link rel="canonical" href="{escape(url)}" />
  <link rel="stylesheet" href="{prefix}assets/site.css" />
  <link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg" />
  <link rel="icon" href="{prefix}favicon.ico" sizes="16x16 32x32 48x48" />
  <link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png" />
  <meta name="theme-color" content="#eff1f5" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#1e1e2e" media="(prefers-color-scheme: dark)" />

  <meta property="og:site_name" content="{escape(site_name)}" />
  <meta property="og:url" content="{escape(url)}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{t}" />
  <meta property="og:description" content="{d}" />
  <meta property="og:image" content="{image}" />
  <meta property="og:image:width" content="512" />
  <meta property="og:image:height" content="512" />
  <meta property="og:image:alt" content="{alt}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{t}" />
  <meta name="twitter:description" content="{d}" />
  <meta name="twitter:image" content="{image}" />
</head>

<body>
  <a class="skip-link" href="#main">Skip to content</a>
"""
