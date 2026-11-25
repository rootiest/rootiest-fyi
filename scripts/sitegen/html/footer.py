# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The site footer: links back to the hub, support and the source, and the copyright."""
from html import escape

from .. import config


def footer(links=None):
    """
    SYNOPSIS
        footer(links=None) -> str
    DESCRIPTION
        Return the footer and close the document (</body></html>). LINKS is a
        list of (href, label), config.FOOTER_LINKS by default. Every link is
        plain text: no badges or images from other sites.
    EXAMPLE
        page = head(...) + header(...) + main + footer()
    """
    row = "\n".join(f'        <a href="{escape(h)}">{escape(t)}</a>' for h, t in (links or config.FOOTER_LINKS))
    return f"""  <footer class="site-footer">
    <div class="wrap">
      <nav class="footer-links" aria-label="Footer">
{row}
      </nav>
      <p>© {config.YEAR} {config.ENTITY}. No ads, no trackers.</p>
    </div>
  </footer>
</body>
</html>
"""
