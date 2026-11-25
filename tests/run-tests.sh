#!/usr/bin/env bash
# Copyright (C) 2026 Chris Laprade (chris@rootiest.com)
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Runs the generator's tests, then checks the real site/. CI runs this.
set -eu
cd "$(dirname "$0")/.."
python3 tests/test_sitegen.py
python3 scripts/check.py
