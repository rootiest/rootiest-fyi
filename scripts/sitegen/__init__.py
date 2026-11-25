# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Static site generator for rootiest.fyi: the docs hub and the Rootiest Mail guide.

The catalog lives in sites.yaml (read by sitegen.catalog), the guide's pages in
content/email/ (read by sitegen.guide), HTML building blocks in sitegen.html,
and one module per page set in sitegen.pages. scripts/build.py runs it.
"""
