#!/bin/bash
# Run a Blender script headless (or in the open Blender), the one entry point for every Blender step.
#
#   tools/blender_run.sh <step.py> [file.blend] [-- script args...]     headless: private Blender process
#   tools/blender_run.sh --live <step.py>                               live: the Blender you have open (MCP socket)
#
# Two kinds of script, told apart automatically:
#   step scripts  (blender/assets/<Name>/build.py, blender/scripts/stages.py, ingest_mesh.py ...): the shared libs
#                 blender/lib/{kit,export,audit,review}.py are prepended, ASSET and ROOT are set, parameters come in
#                 env vars, and the script's top-level `result` is printed as one `RESULT_JSON {...}` line.
#   tool scripts  (any script that does `import gamelib`: render_views, project_paint, qa_check, uv_tools,
#                 bake_maps, build_material, game_skeleton, weights, anim_tools, export_skinned): run as they are,
#                 with arguments after `--`; they print PASS/WARN/FAIL/INFO lines and a final DONE line.
# Env: ASSET=<Name> selects blender/assets/<Name>/asset.json for tool scripts (or ASSET_JSON=<path>);
#      VERBOSE=1 prints everything; AUTOEXEC=1 allows scripts embedded in the .blend (Rigify rig_ui / Python
#      drivers; trusted files only); BLENDER_LIBS overrides the prepended libs.
set -euo pipefail
source "$(dirname "$0")/env.sh"
LIVE=0; [ "${1:-}" = "--live" ] && { LIVE=1; shift; }
STEP="$1"; shift
BLEND=""; if [ $# -gt 0 ] && [ "$1" != "--" ]; then BLEND="$1"; shift; fi
[ "${1:-}" = "--" ] && shift
[ -f "$STEP" ] || { echo "FAIL no such script: $STEP"; exit 2; }
[ -z "$BLEND" ] || [ -f "$BLEND" ] || { echo "FAIL no such file: $BLEND"; exit 2; }
export BLENDER_LIB="$ROOT/blender/lib"
if [ -z "${ASSET_JSON:-}" ] && [ -n "${ASSET:-}" ] && [ -f "$ROOT/blender/assets/$ASSET/asset.json" ]; then
  export ASSET_JSON="$ROOT/blender/assets/$ASSET/asset.json"
fi
FILTER='RESULT_JSON|Error|Traceback|line [0-9]+|Exception|^(PASS|WARN|FAIL|INFO|DONE|SUMMARY|ACTION|EVENTS) '

if grep -qE '^\s*import gamelib|^import .*gamelib|gamelib as g' "$STEP"; then
  # tool script: run as is
  RUN="$STEP"
else
  LIBS="${BLENDER_LIBS:-kit export audit review}"
  RUN="$ROOT/blender/.current_$$.py"; trap 'rm -f "$RUN"' EXIT
  {
    echo "import os, sys; ROOT = r'''$ROOT'''; os.environ.setdefault('ROOT', ROOT)"
    echo "result = None"
    for l in $LIBS; do cat "$ROOT/blender/lib/$l.py"; echo; done
    cat "$STEP"; echo
    echo 'import json as _j; print("RESULT_JSON " + _j.dumps(globals().get("result"), default=str))'
  } > "$RUN"
fi

if [ $LIVE = 1 ]; then
  "$BLENDER_MCP_PYTHON" -I "$ROOT/tools/blender_live.py" "$RUN"
else
  ARGS=(-b); [ -n "$BLEND" ] && ARGS+=("$BLEND")
  ARGS+=(--factory-startup); [ "${AUTOEXEC:-0}" = 1 ] && ARGS+=(--enable-autoexec)
  ARGS+=(--python-exit-code 1 --python "$RUN" -- "$@")
  if [ "${VERBOSE:-0}" = 1 ]; then "$BLENDER" "${ARGS[@]}"
  else
    set +o pipefail
    "$BLENDER" "${ARGS[@]}" 2>&1 | grep -E "$FILTER" | grep -v 'Draco mesh compression' | head -150
    exit "${PIPESTATUS[0]}"
  fi
fi
