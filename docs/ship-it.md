# Shipping this project

## push-it
- Run `./tests/run-tests.sh` before pushing. Rebuild with `python3 scripts/build.py` after any change to
  `sites.yaml`, `content/` or `site/assets/site.css`, and commit the result.

## merge-it
- Merge commit. Every PR asks first.

## deploy-it
- CI deploys on merge to `main`: `.github/workflows/pages.yml` publishes `site/` to `pages/rootiest-fyi`.
- Verify: `https://rootiest.fyi/` and `https://email.rootiest.fyi/` load the new version (both edges
  within a few minutes).
