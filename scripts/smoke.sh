#!/usr/bin/env bash
# Replay-demo smoke, and `--url` for the live check after deploy.
#
# The demo builds its own database in a fresh mkdtemp() directory. This script
# builds another one, points WB_DATABASE at it, and asserts the file is unchanged
# afterwards: the demo ignores that path rather than deleting anything there.
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

if [[ "${1:-}" == "--url" ]]; then
  if [[ $# -ne 2 || -z "${2:-}" ]]; then
    echo "usage: scripts/smoke.sh --url BASE_URL" >&2
    exit 2
  fi
  base=${2%/}
  health=$(curl -fsS --max-time 30 "$base/healthz")
  grep -q '^version: 0\.1\.0$' <<<"$health"
  grep -q '^replay: ok$' <<<"$health"
  grep -q '^stop_reason: end_turn$' <<<"$health"
  map=$(curl -fsS --max-time 30 "$base/")
  grep -q $'^1\.2\t' <<<"$map"
  grep -q $'^1\.3\t' <<<"$map"
  grep -q $'^5\.3\t' <<<"$map"
  grep -q $'^5\.6\t' <<<"$map"
  grep -q 'workbench/coordinator/coordinator.py:' <<<"$map"
  grep -q 'workbench/readout/template.py:' <<<"$map"
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "usage: scripts/smoke.sh [--url BASE_URL]" >&2
  exit 2
fi

if ! command -v wb >/dev/null 2>&1; then
  echo "wb is not on PATH" >&2
  exit 1
fi

py=$(dirname "$(command -v wb)")/python
home=$("$py" -c 'import tempfile; print(tempfile.mkdtemp(prefix="wb-smoke-"))')
trap 'rm -rf "$home"' EXIT

export WB_SOURCES_ROOT="$root/sources"
export WB_SMOKE_HOME="$home"
"$py" - <<'PY'
import os
from pathlib import Path

from workbench.core.config import Config
from workbench.core.store import Store

home = Path(os.environ["WB_SMOKE_HOME"])
config = Config(
    database_path=home / "configured.sqlite3",
    sources_root=Path(os.environ["WB_SOURCES_ROOT"]),
)
with Store.open(config) as store:
    store.build()
PY
export WB_DATABASE="$home/configured.sqlite3"

checksums() {
  find "$home" -maxdepth 1 -name 'configured.sqlite3*' -print | sort | while read -r file; do
    cksum "$file"
  done
}

before=$(checksums)
out="$home/demo.out"
wb demo --principal lead-parrott --role lead | tee "$out"

require() {
  local pattern=$1
  if ! grep -q -e "$pattern" "$out"; then
    echo "smoke: expected pattern not in the demo output" >&2
    exit 1
  fi
}

require '^demo: replay$'
require '^documents: 8$'
require 'coverage: 5 question(s), 4 answered, 1 failed'
require 'GAP  q'
require 'claims: 7 verified, 1 not verified'
require 'conflicts: 1'
require 'exception handling: level unknown'
require 'invoice matching: level 2'
require 'recorded_verified: false'
require '^coverage_gaps_present:'
require '^state: final$'
require '^accept_gaps: true$'
require 'HLP-4901'

after=$(checksums)
if [[ "$before" != "$after" ]]; then
  echo "smoke: the configured database was modified" >&2
  exit 1
fi

out2="$home/demo2.out"
wb demo --principal lead-parrott --role lead >"$out2"
if ! cmp -s "$out" "$out2"; then
  echo "smoke: back-to-back demo output differed" >&2
  exit 1
fi
