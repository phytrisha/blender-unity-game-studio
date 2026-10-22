#!/bin/bash
# Smoke test of the Blender side of the art pipeline: copies tools/ and blender/ into a temporary tree, builds two
# fixture assets there (tools/tests/make_fixture.py) and runs every Blender tool script and the static/skinned exports
# once through tools/blender_run.sh, checking each for its expected output line. Needs Blender 5.x and uv. ~1 min.
# Never touches the studio's own blender/assets or blender/export. Unity is not involved (see unity/ for that loop).
#   tools/tests/art_pipeline_smoke.sh            KEEP=1 keeps the temporary tree and prints its path
set -u
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
T="$(mktemp -d)/studio"; mkdir -p "$T"
rsync -a --exclude 'blender/export' --exclude 'blender/assets/*/' "$SRC/tools" "$SRC/blender" "$SRC/.env.example" "$T/"
mkdir -p "$T/blender/assets"
cd "$T"
BR=tools/blender_run.sh; S=blender/scripts
fails=0
run() {  # run <label> <regex that must appear> <cmd...>
  local label=$1 want=$2; shift 2
  local out; out=$("$@" 2>&1)
  if printf '%s\n' "$out" | grep -qE "$want"; then echo "ok   $label"
  else echo "FAIL $label"; printf '%s\n' "$out" | tail -8; fails=$((fails+1)); fi
}
C=blender/assets/SmokeCrate/SmokeCrate.blend
K=blender/assets/SmokeTentacle/SmokeTentacle.blend
run fixtures        "DONE fixtures"               $BR tools/tests/make_fixture.py
export ASSET=SmokeCrate
run render-control  "DONE .*ctl_sheet"            $BR $S/render_views.py $C -- --tag ctl --mode clay --views front,right,back,left,top --size 256
run render-normal   "DONE"                        $BR $S/render_views.py $C -- --tag nrm --mode normal --views front --size 128
python3 - <<'EOF'
# synthetic "paintings": one flat colour per view, same size as the control renders (stand-ins for Weave output)
import os, struct, zlib
def png(path, rgb, n=256):
    raw = b"".join(b"\x00" + bytes(rgb) * n for _ in range(n))
    def ch(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b""))
os.makedirs("sources/weave/SmokeCrate", exist_ok=True)
for v, c in {"front": (220, 40, 40), "right": (40, 200, 40), "back": (40, 40, 220), "left": (220, 220, 40), "top": (240, 240, 240)}.items():
    png(f"sources/weave/SmokeCrate/{v}.png", c)
EOF
TX=blender/assets/SmokeCrate/textures
run project-paint   "coverage 8[0-9]\.[0-9]%"     $BR $S/project_paint.py $C -- --obj SM_SmokeCrate_Body --cams renders/SmokeCrate/ctl_cams.json --images front:sources/weave/SmokeCrate/front.png,right:sources/weave/SmokeCrate/right.png,back:sources/weave/SmokeCrate/back.png,left:sources/weave/SmokeCrate/left.png,top:sources/weave/SmokeCrate/top.png --size 256 --out $TX/T_SmokeCrate_BC.png
run coverage-mask   "mask covers 1[0-9]\."        uv run -q tools/texture/texture_tools.py coverage-mask $TX/T_SmokeCrate_BC_coverage.png renders/SmokeCrate/inpaint_mask.png
run render-gapview  "DONE .*ctl2_sheet"           $BR $S/render_views.py $C -- --tag ctl2 --mode clay --views bottom --size 256
cp sources/weave/SmokeCrate/top.png sources/weave/SmokeCrate/bottom.png
run fill-only       "coverage 100\.0%"            $BR $S/project_paint.py $C -- --obj SM_SmokeCrate_Body --cams renders/SmokeCrate/ctl_cams.json,renders/SmokeCrate/ctl2_cams.json --images bottom:sources/weave/SmokeCrate/bottom.png --size 256 --base $TX/T_SmokeCrate_BC.png --fill-only --out $TX/T_SmokeCrate_BC.png
run bake-ao         "DONE bake"                   $BR $S/bake_maps.py $C -- --low SM_SmokeCrate_Body --maps ao,id --size 256 --samples 4 --prefix T_SmokeCrate --outdir $TX
run derive-unity    "T_SmokeCrate_N"              uv run -q tools/texture/derive_pbr_maps.py $TX/T_SmokeCrate_BC.png --out-dir renders/SmokeCrate/derived --name SmokeCrate --unity --metallic-map 0
cp renders/SmokeCrate/derived/T_SmokeCrate_N.png renders/SmokeCrate/derived/T_SmokeCrate_MS.png $TX/
run material        "DONE material M_SmokeCrate"  $BR $S/build_material.py $C -- --mat M_SmokeCrate --obj SM_SmokeCrate_Body --bc $TX/T_SmokeCrate_BC.png --n $TX/T_SmokeCrate_N.png --ms $TX/T_SmokeCrate_MS.png --ao $TX/T_SmokeCrate_AO.png --save
run render-lit      "DONE .*lit_sheet"            $BR $S/render_views.py $C -- --tag lit --mode lit --views q34 --size 256
run qa-crate        "SUMMARY stage=texture fail=0"    $BR $S/qa_check.py $C -- --stage texture
run export-static   "T_SmokeCrate_MS.png"         env CATEGORY=Props BUDGET=600 STAGES=audit,export $BR $S/stages.py $C
export ASSET=SmokeTentacle
run uv-unwrap       "stretch 0\.0"                $BR $S/uv_tools.py $K -- unwrap --method smart --save
run weights-clean   "DONE weights clean"          $BR $S/weights.py $K -- clean --arm rig --save
run qa-loop-open    "loop not closed"             $BR $S/qa_check.py $K -- --stage anim
run anim-loopfix    "PASS Wiggle: .* closed"      $BR $S/anim_tools.py $K -- loopfix --action Wiggle --frames 1,24 --save
run anim-events     "EVENTS Wiggle"               $BR $S/anim_tools.py $K -- events --action Wiggle --set Swish:7 --save
run qa-tentacle     "SUMMARY stage=all fail=0"    $BR $S/qa_check.py $K -- --stage all
run render-anim     "DONE .*anim_sheet"           $BR $S/render_views.py $K -- --tag anim --action Wiggle --rig rig --views right --frames 1,7,13,19 --size 128
run export-skinned  "PASS roundtrip SK_SmokeTentacle.fbx: 1 meshes.*3 bones.*Wiggle" $BR $S/export_skinned.py $K
run manifest        "\"loop\": true"              cat blender/export/Characters/SmokeTentacle/SK_SmokeTentacle.json
echo "tree: $T"
[ "${KEEP:-0}" = 1 ] || rm -r "$T"
[ $fails -eq 0 ] && echo "ALL PASSED" || { echo "$fails FAILED"; exit 1; }
