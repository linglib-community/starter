#!/usr/bin/env bash
# Set up this project: Lean, linglib and Mathlib, then build the worked example.
#
# Safe to run more than once; finished steps are skipped quickly.
# Prints one line per step. Full output of each step goes to .lake/setup-logs/.
# Ends with "SETUP OK" on success, or "SETUP FAILED at <step>" and the log to read.
#
# macOS and Linux. On Windows, see AGENTS.md ("Windows").

set -uo pipefail
cd "$(dirname "$0")/.."

LOGDIR=".lake/setup-logs"
mkdir -p "$LOGDIR"
export PATH="$HOME/.elan/bin:$PATH"
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
FREE_GB=$(df -Pk . | awk 'NR==2 { print int($4 / 1048576) }')
if [ ! -d .lake/packages/mathlib ] && [ "$FREE_GB" -lt 15 ]; then
  fail "Only ${FREE_GB} GB of disk space is free here. Setup needs about 15 GB."
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
step "4/5 Downloading linglib and the prebuilt Mathlib files"
lake exe cache get > "$LOGDIR/4-dependencies.log" 2>&1 \
  || fail "Could not download dependencies. This step needs internet access to github.com and cache.mathlib.org." "$LOGDIR/4-dependencies.log"
done_step

# 5. Build the worked example (compiles the parts of linglib it uses)
step "5/5 Building the worked example"
lake build MyProject.Example > "$LOGDIR/5-build.log" 2>&1 \
  || fail "The worked example did not build." "$LOGDIR/5-build.log"
done_step

printf '\nSETUP OK (total %s min)\n' "$(( ($(date +%s) - START + 59) / 60 ))"
