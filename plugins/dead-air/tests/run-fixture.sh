#!/usr/bin/env bash
# Run SPEC §13 tests 1-7a against the bundled fixtures and the design-system snapshot.
# Offline test only: live runs always read the design system artifact, never tests/fixtures/design-system.
#
#   DEAD_AIR_PYTHON=/path/to/python-with-playwright  tests/run-fixture.sh
#
# Needs: a Python with `playwright` (+ `playwright install chromium`), ffmpeg/ffprobe, npm.
# Fonts: $DEAD_AIR_FONTS (an @fontsource dir) or installed once into tests/.fonts/ (gitignored).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${DEAD_AIR_PYTHON:-python3}"

"$PY" -c "import playwright" 2>/dev/null || { echo "ERROR: $PY has no playwright. pip install playwright && python -m playwright install chromium"; exit 2; }
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || { echo "ERROR: ffmpeg/ffprobe not on PATH"; exit 2; }

FONTS="${DEAD_AIR_FONTS:-$HERE/.fonts/node_modules/@fontsource}"
if [ ! -d "$FONTS/work-sans" ]; then
  mkdir -p "$HERE/.fonts"
  [ -f "$HERE/.fonts/package.json" ] || echo '{"name":"dead-air-test-fonts","private":true}' > "$HERE/.fonts/package.json"
  npm i --silent --prefix "$HERE/.fonts" @fontsource/big-shoulders-display @fontsource/work-sans @fontsource/ibm-plex-mono
fi

exec python3 "$HERE/check_fixtures.py" --python "$PY" --fonts "$FONTS" --out "$HERE/out"
