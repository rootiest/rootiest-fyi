# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read and validate sites.yaml into categories and sites."""
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from .parse import CatalogError, parse

ICON_HOSTS = ("icons.rootiest.fyi", "pages.rootiest.fyi")
LABEL = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
HOST = re.compile(r"^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$")
SITE_KEYS = {"label", "url", "title", "description", "icon", "category", "order"}
SITE_OPTIONAL = {"tags", "repo", "status", "links", "aliases"}


@dataclass
class Link:
    """An extra link shown on a site's card."""
    title: str
    url: str


@dataclass
class Site:
    """One entry of the catalog."""
    label: str
    url: str
    title: str
    description: str
    icon: str
    category: str
    order: int
    tags: list = field(default_factory=list)
    repo: str = ""
    status: str = ""
    links: list = field(default_factory=list)
    aliases: list = field(default_factory=list)

    @property
    def host(self):
        """The host name of the site's URL."""
        return urlsplit(self.url).hostname


@dataclass
class Category:
    """A heading on the hub, with its sites in order."""
    name: str
    blurb: str
    sites: list = field(default_factory=list)


def _https(value, where):
    """Return VALUE if it is an https URL with a host, else raise."""
    u = urlsplit(str(value))
    if u.scheme != "https" or not u.hostname:
        raise CatalogError(0, f"{where}: {value!r} is not an https:// URL")
    return str(value)


def _icon(value, where):
    """Return the full URL for an icon given as a URL or as a path on icons./pages.rootiest.fyi."""
    value = str(value)
    if value.startswith("https://"):
        return _https(value, where)
    if value.startswith(tuple(h + "/" for h in ICON_HOSTS)):
        return "https://" + value
    raise CatalogError(0, f"{where}: icon {value!r} must be an https URL or a path on {' or '.join(ICON_HOSTS)}")


def _text(d, key, where, required=True):
    """Return d[key] as a non-empty string (or "" when optional and absent)."""
    if key not in d:
        if required:
            raise CatalogError(0, f"{where}: missing {key!r}")
        return ""
    v = d[key]
    if not isinstance(v, str) or not v.strip():
        raise CatalogError(0, f"{where}: {key!r} must be non-empty text")
    return v


def _site(d, i, categories):
    """Validate one site mapping and return a Site."""
    where = f"sites[{i}]"
    if not isinstance(d, dict):
        raise CatalogError(0, f"{where}: each site must be a mapping")
    if "label" in d:
        where = f"site {d['label']!r}"
    unknown = set(d) - SITE_KEYS - SITE_OPTIONAL
    if unknown:
        raise CatalogError(0, f"{where}: unknown key(s) {', '.join(sorted(unknown))}")
    label = _text(d, "label", where)
    if not LABEL.match(label):
        raise CatalogError(0, f"{where}: label must be lower-case letters, digits and hyphens")
    category = _text(d, "category", where)
    if category not in categories:
        raise CatalogError(0, f"{where}: category {category!r} is not under categories")
    if not isinstance(d.get("order"), int):
        raise CatalogError(0, f"{where}: 'order' must be a whole number")
    tags = d.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise CatalogError(0, f"{where}: 'tags' must be a list of text")
    aliases = d.get("aliases", [])
    if not isinstance(aliases, list) or not all(isinstance(a, str) and HOST.match(a) for a in aliases):
        raise CatalogError(0, f"{where}: 'aliases' must be a list of host names")
    links = []
    for j, ld in enumerate(d.get("links", []) or []):
        lw = f"{where} links[{j}]"
        if not isinstance(ld, dict) or set(ld) != {"title", "url"}:
            raise CatalogError(0, f"{lw}: each link needs exactly 'title' and 'url'")
        links.append(Link(_text(ld, "title", lw), _https(ld["url"], lw)))
    repo = _text(d, "repo", where, required=False)
    return Site(
        label=label,
        url=_https(_text(d, "url", where), where),
        title=_text(d, "title", where),
        description=_text(d, "description", where),
        icon=_icon(_text(d, "icon", where), where),
        category=category,
        order=d["order"],
        tags=tags,
        repo=_https(repo, where) if repo else "",
        status=_text(d, "status", where, required=False),
        links=links,
        aliases=aliases,
    )


def load(path):
    """
    SYNOPSIS
        load(path) -> [Category]
    DESCRIPTION
        Read the catalog at PATH and return its categories in file order, each
        holding its sites sorted by order, then title. Raises CatalogError with
        a readable message for anything malformed: unknown keys, a missing
        field, a duplicate label, URL or alias, an unknown category, or an icon
        that is neither an https URL nor a path on icons./pages.rootiest.fyi.
    EXAMPLE
        for cat in load("sites.yaml"): print(cat.name, len(cat.sites))
    """
    try:
        data = parse(Path(path).read_text())
    except CatalogError as e:
        raise CatalogError(e.line, f"{path}: {e}") from None
    if not isinstance(data, dict) or set(data) != {"categories", "sites"}:
        raise CatalogError(0, f"{path}: the top level must have exactly 'categories' and 'sites'")
    cats = {}
    for i, c in enumerate(data["categories"] or []):
        if not isinstance(c, dict) or not set(c) <= {"name", "blurb"}:
            raise CatalogError(0, f"categories[{i}]: needs 'name' and optionally 'blurb'")
        name = _text(c, "name", f"categories[{i}]")
        if name in cats:
            raise CatalogError(0, f"categories[{i}]: duplicate category {name!r}")
        cats[name] = Category(name, _text(c, "blurb", f"category {name!r}", required=False))
    seen, sites = {}, [_site(d, i, cats) for i, d in enumerate(data["sites"] or [])]
    hosts = {s.host for s in sites}
    for s in sites:
        for key in [("label", s.label), ("url", s.url.rstrip("/"))] + [("alias", a) for a in s.aliases]:
            if key in seen:
                raise CatalogError(0, f"site {s.label!r}: {key[0]} {key[1]!r} is already used by {seen[key]!r}")
            seen[key] = s.label
        clash = [a for a in s.aliases if a in hosts]
        if clash:
            raise CatalogError(0, f"site {s.label!r}: alias {clash[0]!r} is another site's host")
        cats[s.category].sites.append(s)
    for c in cats.values():
        c.sites.sort(key=lambda s: (s.order, s.title.lower()))
    empty = [c.name for c in cats.values() if not c.sites]
    if empty:
        raise CatalogError(0, f"categories with no sites: {', '.join(empty)}")
    return list(cats.values())
