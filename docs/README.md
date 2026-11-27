# rootiest-fyi documentation

The README covers the layout, building, the catalog and writing the guide. This page covers how the
generator fits together.

## How the build works

`scripts/build.py` writes:

| Output | From |
|---|---|
| `site/index.html` | `sites.yaml`, by `sitegen/pages/hub.py` |
| `site/404.html`, `site/email/404.html` | `sitegen/pages/not_found.py` |
| `site/email/index.html`, `site/email/<slug>/index.html` | `content/email/*.html`, by `sitegen/pages/guide.py` |
| `site/email/assets/site.css` | a copy of `site/assets/site.css` |
| `site/manifest.webmanifest`, `site/go/<label>/index.html` | `sites.yaml` and `config.py`, by `sitegen/pages/app.py` |
| `site/email/manifest.webmanifest` | the guide's first page and `shortcut` comments, by `sitegen/pages/app.py` |

The guide, its manifest and its two 404 pages are only built when `content/email/` has pages.

## The catalog format

`sitegen/catalog/parse.py` reads a strict subset of YAML: block mappings and sequences, plain and
double-quoted strings, whole numbers and `[flow, lists]`. It refuses anything else with the line number,
including plain text that YAML would read as something other than a string (`yes`, `1.5`, a date). So
every file it accepts means the same to PyYAML, and the private completeness check (which uses PyYAML)
reads the catalog the same way. `tests/test_sitegen.py` compares the two when PyYAML is installed.

`sitegen/catalog/load.py` then validates the fields: known keys only, https URLs, a known category, a
whole-number `order`, and an icon that is an https URL or a path on `icons.rootiest.fyi` or
`pages.rootiest.fyi`. Labels, URLs and aliases must be unique.

## One guide, two addresses

The guide is served at `https://email.rootiest.fyi/` (Caddy's root is `site/email/`) and at
`https://rootiest.fyi/email/` (the hub's root). So every link and file the guide uses is relative and
stays inside `site/email/`, which has its own favicons and its own copy of the stylesheet. The 404 pages
are the exception: they're served at any path, so they use root-relative `/assets/site.css` and
`/favicon.svg`, which exist at both roots. `scripts/check.py` enforces both rules. The canonical address
of every guide page is on `email.rootiest.fyi`.

## The apps

Each manifest's scope is its own folder, and every URL in it is relative to the manifest, so the hub's
app covers all of `rootiest.fyi` (the guide's copy at `/email/` included) and the guide's app covers
`email.rootiest.fyi`. Guide pages and the 404 pages link the manifest root-relative,
`/manifest.webmanifest`: at `email.rootiest.fyi` that is the guide's own, at `rootiest.fyi/email/` the
hub's. So the guide on the hub's address offers the Docs app, not a second guide app inside its scope.
It is the only root-relative link on guide pages, and `scripts/check.py` makes sure it exists at both.

The site runs no JavaScript, so there is no service worker and no offline copy: Chromium browsers no
longer need one to install an app. Installing uses the browser's own button, not one on the page.

A shortcut must lie inside the app's scope, so the hub's shortcuts to sites on other hosts open
`go/<label>/`, a page whose `<meta http-equiv="refresh">` sends the visitor on. Android launchers show
the first four shortcuts, desktop Chrome up to ten. `scripts/check.py` checks each manifest's icons,
start URL and shortcuts.

## Screenshots

`sitegen/guide/shots.py` rewrites each `<figure class="shot" data-shot="<id>">`. It takes the `<img src>`,
strips any leading `./` and `../`, requires what's left to be `shots/<file>`, and writes the correct
relative path for the page's depth. If the file isn't in `site/email/shots/`, the image becomes a dashed
placeholder showing the alt text and the id. A figure without an id, an image or alt text, or with a
`src` outside `shots/`, stops the build.

## Tests

`./tests/run-tests.sh` runs `tests/test_sitegen.py` (the parser, the loader, the shot rewriting, and a
full build of the fixture guide in `tests/fixtures/` checked by `check.py`), then checks the real `site/`.
