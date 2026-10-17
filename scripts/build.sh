#!/usr/bin/env bash
# Build the safe way: first download any prebuilt Mathlib files the target needs, then build it.
#
#   bash scripts/build.sh MyProject.Example     # a module, or a path such as MyProject/Example.lean
#   bash scripts/build.sh                       # the whole project
#
# This project downloads only the parts of Mathlib it uses. If a file needs a Mathlib file
# that was never downloaded, Lean compiles it instead, which takes hours. This script stops
# before that can happen, so build through it rather than calling `lake build` directly.
#
# macOS and Linux. On Windows, see AGENTS.md ("Windows").

set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.elan/bin:$PATH"
export MATHLIB_NO_CACHE_ON_UPDATE=1

command -v python3 >/dev/null 2>&1 || { echo "python3 is not installed; scripts/get_mathlib.py needs it."; exit 1; }

python3 scripts/get_mathlib.py "$@"
exec lake build "$@"
