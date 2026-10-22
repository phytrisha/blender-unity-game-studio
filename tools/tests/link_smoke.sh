#!/bin/bash
# Smoke test of link mode (tools/link_project.sh): links a throwaway game into a temporary folder next to nothing,
# checks that the links resolve, the game-owned files are real files, the Unity package dependency and the Claude
# Code permission are in place, that a Blender build writes into the game (not the studio), and that --relink is
# idempotent. Needs git, Blender 5.x (the build check; skipped with a SKIP line without it). ~20 s.
#   tools/tests/link_smoke.sh            KEEP=1 keeps the temporary game and prints its path
set -u
STUDIO="$(cd "$(dirname "$0")/../.." && pwd -P)"
TMP="$(mktemp -d)"; G="$TMP/SmokeGame"
fails=0
ok()   { echo "ok   $1"; }
fail() { echo "FAIL $1"; fails=$((fails+1)); }
check() { local label=$1; shift; if "$@" >/dev/null 2>&1; then ok "$label"; else fail "$label"; fi; }

out=$("$STUDIO/tools/link_project.sh" "$G" "Smoke Game" 2>&1) && ok "link_project" || { fail "link_project"; printf '%s\n' "$out" | tail -8; }

for p in .claude/agents .claude/skills .claude/hooks .claude/scripts .claude/rules tools blender/lib blender/scripts \
         blender/bases docs/WORKFLOW-GUIDE.md .claude/docs/art-pipeline unity/import_assets.cs; do
  if [ -L "$G/$p" ] && [ -e "$G/$p" ]; then :; else fail "link resolves: $p"; fi
done
ok "links resolve"
broken=$(find "$G" -path "$G/.git" -prune -o -type l ! -exec test -e {} \; -print | head -5)
[ -z "$broken" ] && ok "no broken links" || fail "broken links: $broken"
abs=$(find "$G" -path "$G/.git" -prune -o -type l -print | while read -r l; do [ "$(readlink "$l" | cut -c1)" = / ] && echo "$l"; done | head -3)
[ -z "$abs" ] && ok "links are relative" || fail "absolute links: $abs"

for p in CLAUDE.md project.yaml .claude/settings.json .claude/docs/technical-preferences.md Packages/manifest.json \
         blender/assets/Crate/build.py .env; do
  [ -f "$G/$p" ] && [ ! -L "$G/$p" ] || fail "game owns: $p"
done
ok "game-owned files are real files"

check "manifest depends on the package (relative file:)" python3 -c "
import json, os, sys
d = json.load(open('$G/Packages/manifest.json'))['dependencies']['com.phytrisha.studio-pipeline']
assert d.startswith('file:../') and os.path.isfile(os.path.join('$G/Packages', d[5:], 'package.json'))"
check "settings.local.json allows the studio" python3 -c "
import json; assert '$STUDIO' in json.load(open('$G/.claude/settings.local.json'))['permissions']['additionalDirectories']"
check ".studio records path and commit" grep -q '^STUDIO_COMMIT=' "$G/.studio"
check "settings.local.json is not committed" test -z "$(git -C "$G" ls-files .claude/settings.local.json)"
check "first commit made" git -C "$G" rev-parse HEAD

BLENDER_BIN=$(sed -n 's/^BLENDER=//p' "$G/.env" | tr -d '"'); BLENDER_BIN=${BLENDER_BIN:-/Applications/Blender.app/Contents/MacOS/Blender}
if [ -x "$BLENDER_BIN" ]; then
  before=$(cd "$STUDIO" && git status --porcelain | md5)
  out=$(cd "$G" && ASSET=Crate STAGES=build,export tools/blender_run.sh blender/assets/Crate/build.py 2>&1)
  if ls "$G"/blender/export/*/Crate/SM_Crate.fbx >/dev/null 2>&1; then ok "build writes into the game"
  else fail "build writes into the game"; printf '%s\n' "$out" | tail -8; fi
  [ "$before" = "$(cd "$STUDIO" && git status --porcelain | md5)" ] && ok "studio untouched by the build" || fail "studio changed by the build"
else
  echo "SKIP build check (no Blender at $BLENDER_BIN)"
fi

(cd "$G" && git add -A && git commit -qm build >/dev/null 2>&1 || true)
"$STUDIO/tools/link_project.sh" --relink "$G" >/dev/null 2>&1 && ok "relink runs" || fail "relink runs"
[ -z "$(git -C "$G" status --porcelain -- . ':!.studio')" ] && ok "relink is idempotent" || { fail "relink is idempotent"; git -C "$G" status --porcelain | head -5; }

if [ -n "${KEEP:-}" ]; then echo "kept: $G"; else rm -rf "$TMP"; fi
[ $fails -eq 0 ] && echo "SUMMARY link smoke: all passed" || echo "SUMMARY link smoke: $fails failed"
exit $((fails > 0))
