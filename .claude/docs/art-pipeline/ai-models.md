# AI-generated models (Tripo, Hunyuan 3D via Weave)

Both spend credits: follow the credit protocol in texturing.md (quote/dry-run → ask per run → run → log).

## When to use them — and when not

Good: organic props, statues, rocks, creatures, characters, quick placeholders, a high-poly to bake from.
Not: modular kit pieces that must snap to a grid, assets that share trim sheets, anything with exact dimensions or
mechanisms — model those with the kit (`modeling.md`). Judge quality from the preview before spending more on
refine/rig.

## Tripo (CLI)

`tripo` is installed globally; its own agent docs: `tripo docs`, `tripo docs --topic commands/generate|process|make`,
`tripo docs --topic examples/game-asset`. Read them instead of guessing parameters.
- **Auth**: `tripo doctor`. No key → ask which site (`ov` international, `cn` China), run `tripo login --region <..>`
  in the background and relay the URL + code; never ask for a key in chat.
- **Exit codes**: 3 auth, 4 no credits (user runs `tripo topup`), 5 content policy (rephrase), 6 task failed (refunded;
  on timeout `tripo task watch <id>`, never redo), 7 network (check `tripo balance` before re-running), 9 rate limit.
- `tripo make` blocks for minutes: no timeout under 15 min; run in the background.
- Don't pick legacy model versions; the CLI chooses `tripo-v3.1` (detailed) or `tripo-p1` (low poly, ≤ 20k faces).

```bash
DRY=1 tools/tripo_make.sh Barrel "a weathered oak barrel with iron hoops, game asset, neutral lighting" --for game-pc   # plan, 0 credits
tools/tripo_make.sh Barrel "..." --for game-pc                     # after approval: sources/tripo/Barrel/, LOG.tsv
tools/tripo_make.sh Lamp sources/reference/lamp.png --for game-mobile -p face_limit=3000
```
Scenarios (`--for`): `game-pc` (v3.1, detailed PBR), `game-mobile` (P1 low poly, 15k faces, 2K textures), `anim`
(rig-check → rig → retarget idle+walk), `ar-web`, `film`. Prompts: one object, its material and condition, "game
asset", "neutral lighting"; real size goes in the spec (ingest scales to it), not the prompt. Images: a clean concept
on a plain background, 2–4 views (`tripo make front.png back.png`) for better backs. Avoid non-default convert
options (pivot, scale, orientation): they bill as "complex convert" and ingest does the same for free.

## Hunyuan 3D (Figma Weave)

`weave_find_model("hunyuan3d")`: V2.1 (~25 credits; `textured_mesh` ×3 cost) or V3 (~80; front + optional back/
left/right views; `generate_type: LowPoly` with `face_count` ≥ 40k; `enable_pbr`). Input: a front concept on a plain
background (Bria background removal ~0.6 credits first). Download the GLB to `sources/weave/<Name>/model.glb`.

## Ingest (both)

```bash
ASSET=Barrel SRC=sources/tripo/Barrel HEIGHT=0.9 TRIS=3000 tools/blender_run.sh blender/scripts/ingest_mesh.py
ASSET=Barrel CATEGORY=Props BUDGET=3000 tools/blender_run.sh blender/scripts/stages.py blender/assets/Barrel/Barrel.blend
```
`ingest_mesh.py`: import GLB/GLTF/FBX/OBJ (largest mesh, or `JOIN=1`), normalise (transforms applied, bottom at z=0,
centred, scaled to `HEIGHT`, `YAW` so the front faces −Y — glTF +Z front arrives as Blender −Y), **weld UV-seam
splits** (generators split the shell at every seam), delete loose verts, dissolve degenerates, recalc normals,
decimate to `TRIS`, soft normals, rename to `SM_<Name>` with materials `M_<Name>[_n]` (`MATERIAL=MI_Shared` to use a
library name). Then write `asset.json`/`BRIEF.md` like any asset and continue at the UV or texture stage.
Check the front review render (fix facing with `YAW=180`). Decimation can leave duplicate faces that z-fight:
`stages.py` audit + `clashes()`. Generated base colours often carry baked light and soft detail: re-texture heroes.

## Characters

```bash
tools/tripo_make.sh Guard "a city guard in leather armour, T-pose, standing straight, arms out" --for anim
tripo anim check @last --json                     # riggable? which rig_type
tripo anim rig @last --spec mixamo --out-format fbx --json
tripo anim retarget @last --animation preset:idle --animation preset:walk --out-format fbx --json
```
Ask for a clean T-pose (arms out, legs apart, nothing fused): fused hands/cloaks and finger bundles are the most
common flaw and break skinning; check before paying for rigging. A `--spec mixamo` FBX maps to Unity Humanoid
automatically: copy it as `blender/export/Characters/<Name>/SK_<Name>.fbx` (ingest via Blender only if the mesh needs
cleanup; keep the armature) and sync. Generated meshes are often open/non-manifold, so bone heat fails: skin a
voxel-remeshed proxy and transfer weights (`rigging.md`). Presets: `idle walk run jump climb dive slash shoot hurt
fall turn`. In Unity check facing (+Z), feet on the ground, no knee/elbow inversion, hands not clipping hips.
