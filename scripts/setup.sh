#!/usr/bin/env bash
# Set up this project: Lean, linglib and the Mathlib files it uses, then build the worked example.
#
#   bash scripts/setup.sh           # download only the parts of Mathlib the project uses
#   bash scripts/setup.sh --full    # download all of Mathlib (for work that imports much of linglib)
#
# Safe to run more than once; finished steps are skipped quickly.
# Prints one line per step. Full output of each step goes to .lake/setup-logs/.
# Ends with "SETUP OK" on success, or "SETUP FAILED at <step>" and the log to read.
#
# macOS and Linux. On Windows, see AGENTS.md ("Windows").

set -uo pipefail
cd "$(dirname "$0")/.."

FULL=0
for arg in "$@"; do
  case "$arg" in
    --full) FULL=1 ;;
    *) printf 'Unknown option: %s\nUsage: bash scripts/setup.sh [--full]\n' "$arg"; exit 2 ;;
  esac
done

LOGDIR=".lake/setup-logs"
mkdir -p "$LOGDIR"
export PATH="$HOME/.elan/bin:$PATH"
# Without this, Mathlib downloads all of its prebuilt files (about 7 GB) whenever Lake updates it.
export MATHLIB_NO_CACHE_ON_UPDATE=1
START=$(date +%s)

step() { STEP_NAME="$1"; STEP_START=$(date +%s); printf '%s ... ' "$1"; }
done_step() { printf 'done (%ss)\n' "$(( $(date +%s) - STEP_START ))"; }
fail() {
  printf 'FAILED\n\nSETUP FAILED at "%s"\n' "$STEP_NAME"
  [ -n "${1:-}" ] && printf '%s\n' "$1"
  [ -n "${2:-}" ] && printf 'Log: %s (last lines below)\n\n' "$2" && tail -n 20 "$2"
  exit 1
}

# 1. Prerequisites
step "1/5 Checking prerequisites"
command -v git >/dev/null 2>&1 || fail "git is not installed."
command -v curl >/dev/null 2>&1 || fail "curl is not installed."
if [ "$FULL" -eq 0 ]; then
  command -v python3 >/dev/null 2>&1 || fail "python3 is not installed. It runs the script that downloads only the Mathlib files this project uses."
fi
free_gb() { df -Pk "$1" | awk 'NR==2 { print int($4 / 1048576) }'; }
FREE_GB=$(free_gb .)
HOME_FREE_GB=$(free_gb "$HOME")
if [ "$FULL" -eq 1 ]; then NEED_GB=10; else NEED_GB=3; fi
if [ ! -d .lake/packages/mathlib ] && [ "$FREE_GB" -lt "$NEED_GB" ]; then
  fail "Only ${FREE_GB} GB of disk space is free here. Setup needs about ${NEED_GB} GB in this folder."
fi
if [ ! -d "$HOME/.elan/toolchains" ] && [ "$HOME_FREE_GB" -lt 3 ]; then
  fail "Only ${HOME_FREE_GB} GB is free in your home folder. Lean needs about 3 GB there."
fi
done_step

# 2. elan, Lean's version manager (installs into ~/.elan, no admin rights needed)
step "2/5 Installing Lean's version manager (elan)"
if ! command -v lake >/dev/null 2>&1; then
  curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --default-toolchain none > "$LOGDIR/2-elan.log" 2>&1 \
    || fail "Could not install elan." "$LOGDIR/2-elan.log"
fi
done_step

# 3. The Lean version this project uses (read from lean-toolchain)
step "3/5 Installing Lean $(cut -d: -f2 lean-toolchain)"
lake --version > "$LOGDIR/3-toolchain.log" 2>&1 \
  || fail "Could not install the Lean toolchain." "$LOGDIR/3-toolchain.log"
done_step

# 4. linglib and its dependencies, and the prebuilt Mathlib files
NETWORK="This step needs internet access to github.com and cache.mathlib.org."
if [ "$FULL" -eq 1 ]; then
  step "4/5 Downloading linglib and all of the prebuilt Mathlib files"
else
  step "4/5 Downloading linglib and the prebuilt Mathlib files this project uses"
fi
: > "$LOGDIR/4-dependencies.log"
# Any Lake command fetches the packages named in lake-manifest.json; this one builds nothing.
# A download as large as Mathlib's source sometimes drops, so it is tried twice.
fetch_packages() { lake env lean --version >> "$LOGDIR/4-dependencies.log" 2>&1; }
fetch_packages || { sleep 5; fetch_packages; } \
  || fail "Could not download dependencies. $NETWORK" "$LOGDIR/4-dependencies.log"
if [ "$FULL" -eq 1 ]; then
  lake exe cache get >> "$LOGDIR/4-dependencies.log" 2>&1 \
    || fail "Could not download the prebuilt Mathlib files. $NETWORK" "$LOGDIR/4-dependencies.log"
else
  python3 scripts/get_mathlib.py --verbose >> "$LOGDIR/4-dependencies.log" 2>&1 \
    || fail "Could not download the prebuilt Mathlib files. $NETWORK" "$LOGDIR/4-dependencies.log"
fi
done_step

# 5. Build the worked example (downloads linglib's prebuilt files and unpacks the parts it uses)
step "5/5 Building the worked example"
lake build MyProject.Example > "$LOGDIR/5-build.log" 2>&1 \
  || fail "The worked example did not build." "$LOGDIR/5-build.log"
done_step

printf '\nSETUP OK (total %s min)\n' "$(( ($(date +%s) - START + 59) / 60 ))"
