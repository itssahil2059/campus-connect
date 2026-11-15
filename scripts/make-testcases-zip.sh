#!/usr/bin/env bash
# Build GitTogether_testcases.zip for the P8 submission (test cases + automation).
#
#   scripts/make-testcases-zip.sh        # writes ./GitTogether_testcases.zip
#
# Contains: backend/tests_ui (Selenium), every app's tests/ folder (pytest),
# backend/conftest.py, backend/pytest.ini, backend/core/testing.py (constants
# the tests import) and docs/test-cases.md. Only files tracked by git are
# included, so caches and local junk stay out. Commit before running.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT="GitTogether_testcases.zip"

FILES=$(git ls-files \
  backend/tests_ui \
  'backend/*/tests/*' \
  backend/conftest.py \
  backend/pytest.ini \
  backend/core/testing.py \
  docs/test-cases.md)

if [ -z "$FILES" ]; then
  echo "No test files found (run from inside the repo)." >&2
  exit 1
fi

rm -f "$OUT"
echo "$FILES" | zip -q "$OUT" -@
echo "Wrote $OUT ($(echo "$FILES" | wc -l | tr -d ' ') files):"
unzip -Z1 "$OUT" | sed 's/^/  /'
