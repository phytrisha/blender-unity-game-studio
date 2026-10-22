#!/bin/bash
# Download Blender Studio's "Human Base Meshes" bundle (CC0) and rebuild the rigged base bodies in
# blender/bases/humanoid/ with blender/scripts/make_humanoid_bases.py. Only needed to regenerate or update them.
#   tools/fetch_humanoid_bases.sh [variant ...]   (female_realistic male_realistic female_stylized male_stylized)
#   HBM_VERSION=1.4.1 tools/fetch_humanoid_bases.sh
set -euo pipefail
source "$(dirname "$0")/env.sh"
VER=${HBM_VERSION:-1.4.1}
URL=https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v$VER.zip
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
echo "downloading $URL"
curl -fsSL -o "$TMP/hbm.zip" "$URL"
unzip -q "$TMP/hbm.zip" -d "$TMP/x"
SRC=$(find "$TMP/x" -name 'human_base_meshes_bundle.blend' | head -1)
"$BLENDER" -b --factory-startup --python-exit-code 1 --python "$ROOT/blender/scripts/make_humanoid_bases.py" \
  -- "$SRC" "$ROOT/blender/bases/humanoid" "$@" 2>&1 | grep -E "^(BASE|Error|Traceback|  File)|Heat" || true
ls -la "$ROOT"/blender/bases/humanoid/*.blend
