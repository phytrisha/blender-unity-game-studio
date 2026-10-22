#!/usr/bin/env bash
#
# project-coherence.sh — compare what `project.yaml` DECLARES against what the
# project actually IS.
#
# WHY THIS EXISTS
#
# Defects of one shape: `project.yaml` is treated as the source of truth and is
# never reconciled against the artifact it describes.
#
#   1  engine.version says 6000.3; the pinned reference says another series;
#      the installed editor is a third
#   2  commands.test names a runner file that does not exist
#
# Prose warnings in `/setup-engine` are in place and do not hold on their own.
# What was missing was a step that reads back what was written.
#
# A subtler cause is handled elsewhere: `/setup-engine` writes an `Installed at
# pin time` row into VERSION.md, and a VERSION.md with no such row leaves that
# step no slot, so it vanishes without a trace. The row ships in the Unity
# reference file, and check 1 below reads it.
#
# This studio supports Unity only: any other engine.name is reported as not
# checked, by name, rather than compared.
#
# OBSERVATIONS, NEVER VERDICTS
#
# Per CLAUDE.md: a script that scores or judges will eventually contradict a mode
# or override it cannot see. This one prints what it compared and what it found,
# and always exits 0. The reader decides. A check that cannot run says so by
# name — silence is never treated as agreement.

set -u
export LC_ALL=C

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -f "$CLAUDE_PROJECT_DIR/project.yaml" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
fi
cd "$ROOT" || exit 0

DIFFERS=0
CHECKED=0
SKIPPED=0

say()      { printf '%s\n' "$*"; }
match()    { CHECKED=$((CHECKED+1)); say "[MATCH]       $*"; }
differs()  { CHECKED=$((CHECKED+1)); DIFFERS=$((DIFFERS+1)); say "[DIFFERS]     $*"; }
skipped()  { SKIPPED=$((SKIPPED+1)); say "[NOT CHECKED] $*"; }

# Read one `key: value` from a named top-level block of project.yaml.
# Deliberately simple: this file is machine-written and two levels deep.
yaml_block_value() {
  block="$1"; key="$2"
  awk -v b="$block" -v k="$key" '
    $0 ~ "^"b":" { inb=1; next }
    inb && /^[a-zA-Z_]/ { inb=0 }
    inb && $0 ~ "^[[:space:]]+"k":" {
      sub("^[[:space:]]*"k":[[:space:]]*", "")
      gsub(/^"|"$/, "")
      print; exit
    }
  ' project.yaml 2>/dev/null
}

summarise() {
  say ""
  say "checked $CHECKED · differs $DIFFERS · not checked $SKIPPED"
  say ""
  say "Observations only — no verdict. 'not checked' is not agreement:"
  say "each line above names why that comparison could not be made."
  exit 0
}

# major.minor of the first version in $1, with Unity's 6000.N read as 6.N.
vmm() { printf '%s' "$1" | grep -oE '[0-9]+\.[0-9]+' | head -1 | sed -E 's/^6000\./6./'; }

say "=== project coherence ==="

if [ ! -f project.yaml ]; then
  skipped "everything — no project.yaml at the repo root. Run /start."
  summarise
fi

ENGINE="$(yaml_block_value engine name)"
VERSION="$(yaml_block_value engine version)"

if [ -z "$ENGINE" ]; then
  skipped "every engine check — project.yaml has no engine.name. Run /setup-engine."
  summarise
fi

ENGINE_LC="$(printf '%s' "$ENGINE" | tr 'A-Z' 'a-z')"
if [ "$ENGINE_LC" != "unity" ]; then
  skipped "every engine check — engine.name is '$ENGINE'; this studio supports Unity only. Run /setup-engine."
  summarise
fi
VERFILE="docs/engine-reference/$ENGINE_LC/VERSION.md"

# --- 1. VERSION.md carries a recorded installed-version probe -----------------
if [ ! -f "$VERFILE" ]; then
  skipped "pinned-reference checks — $VERFILE does not exist"
else
  PINNED="$(grep -E '^\| \*\*Engine Version\*\* \|' "$VERFILE" \
            | sed -E 's/^\| \*\*Engine Version\*\* \| *//; s/ *\|$//')"
  INSTALLED_ROW="$(grep -E '^\| \*\*Installed at pin time\*\* \|' "$VERFILE" \
            | sed -E 's/^\| \*\*Installed at pin time\*\* \| *//; s/ *\|$//')"

  if [ -z "$INSTALLED_ROW" ]; then
    differs "$VERFILE has no 'Installed at pin time' row. /setup-engine is required to write one; its absence means the probe result was never recorded, not that the versions agree."
  elif printf '%s' "$INSTALLED_ROW" | grep -qE 'NOT DETERMINED'; then
    skipped "pinned-vs-installed — $VERFILE records '$INSTALLED_ROW'. A probe that did not run has not established a match."
  else
    match "VERSION.md records the installed version at pin time: $INSTALLED_ROW"
  fi

  # --- 2. project.yaml version vs the pinned reference ------------------------
  # Compared on major.minor, as check 3 does: engine.version is usually the full
  # release (6000.3.23f1) and the pin the series (Unity 6.3 LTS). Unity numbers
  # the same editor two ways -- 6000.3 is marketed as 6.3.
  WANT2="$(vmm "$VERSION")"; GOT2="$(vmm "$PINNED")"
  if [ -z "$PINNED" ]; then
    skipped "project.yaml version vs pinned reference — no Engine Version row in $VERFILE"
  elif [ -z "$VERSION" ]; then
    skipped "project.yaml version vs pinned reference — project.yaml has no engine.version"
  elif printf '%s' "$PINNED" | grep -qF "$VERSION" || { [ -n "$WANT2" ] && [ "$WANT2" = "$GOT2" ]; }; then
    match "engine.version ($VERSION) agrees with $VERFILE ($PINNED)"
  else
    differs "engine.version is '$VERSION' but $VERFILE pins '$PINNED'. Agents consult the reference file, so they will answer for a version the project does not declare."
  fi
fi

# --- 3. Declared version vs the binary actually installed ---------------------
PROBE=""
# The editor named in commands.test (/setup-engine writes its full, quoted
# path), else the Hub folder for engine.version, picked by OS -- Unity's
# Hub installs to a different path on each. Never bare `Unity`: on PATH
# that is often Unity's separate CLI, which rejects -version with exit 2.
UEXE="$(yaml_block_value commands test | grep -oE '"[^"]*/Unity(\.exe)?"' | head -1 | tr -d '"')"
if [ -z "$UEXE" ] && [ -n "$VERSION" ]; then
  case "$(uname -s)" in
    Darwin) UEXE="/Applications/Unity/Hub/Editor/$VERSION/Unity.app/Contents/MacOS/Unity" ;;
    Linux)  UEXE="$HOME/Unity/Hub/Editor/$VERSION/Editor/Unity" ;;
    *)      UEXE="C:/Program Files/Unity/Hub/Editor/$VERSION/Editor/Unity.exe" ;;
  esac
fi
[ -n "$UEXE" ] && [ -x "$UEXE" ] && PROBE="$("$UEXE" -version 2>/dev/null | head -1)"

if [ -z "$PROBE" ]; then
  skipped "declared version vs installed binary — no Unity editor at the path in commands.test or in the Hub folder for engine.version. A probe that could not run has not established absence."
elif [ -z "$VERSION" ]; then
  skipped "declared version vs installed binary — project.yaml has no engine.version"
else
  # Compare on major.minor: a patch difference is normal and not worth a flag.
  WANT="$(vmm "$VERSION")"
  GOT="$(vmm "$PROBE")"
  if [ -n "$WANT" ] && [ "$WANT" = "$GOT" ]; then
    match "engine.version $VERSION matches the installed binary ($PROBE)"
  else
    differs "engine.version is '$VERSION' but the installed binary reports '$PROBE'. Build, test and smoke commands all target the declared version."
  fi
fi

# --- 4/5. Declared rendering + physics vs the project's own files -------------
skipped "project-file checks — no comparison of engine.rendering or engine.physics against the Unity project's files is implemented"

# --- 6. Declared commands reference files that exist -------------------------
BUILD_CMD="$(yaml_block_value commands build)"
TEST_CMD="$(yaml_block_value commands test)"

if [ -z "$BUILD_CMD" ] && [ -z "$TEST_CMD" ]; then
  skipped "command checks — project.yaml declares no commands.build or commands.test"
else
  # A wrapper script named in commands.test (run-tests.sh, a .py or .cs runner)
  # must exist; the Unity editor path itself is probed by check 3.
  RUNNER="$(printf '%s' "$TEST_CMD" | grep -oE '[A-Za-z0-9_/.-]+\.(cs|py|sh)' | head -1)"
  if [ -n "$RUNNER" ]; then
    if [ -f "$RUNNER" ]; then
      match "commands.test runner exists ($RUNNER)"
    else
      differs "commands.test is '$TEST_CMD' but '$RUNNER' does not exist, so this command cannot run as written."
    fi
  fi
fi

summarise
