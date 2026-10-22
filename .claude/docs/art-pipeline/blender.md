# Running Blender

Blender 5.x (tested 5.1.2), path in `.env` (`BLENDER`). Everything goes through one runner.

## The runner

```bash
tools/blender_run.sh <script.py> [file.blend] [-- args...]     # headless, private Blender (safe in parallel)
tools/blender_run.sh --live <step.py>                           # the Blender the user has open (MCP socket)
ASSET=Crate tools/blender_run.sh blender/assets/Crate/build.py blender/assets/Crate/Crate.blend
ASSET=Crate tools/blender_run.sh blender/scripts/qa_check.py blender/assets/Crate/Crate.blend -- --stage model
```
- Headless runs use `--factory-startup` (no user add-ons: reproducible) and print only result lines: `RESULT_JSON`,
  `PASS/WARN/FAIL/INFO/DONE/SUMMARY`, and errors. `VERBOSE=1` prints everything.
- `ASSET=<Name>` selects `blender/assets/<Name>/asset.json` for tool scripts.
- `AUTOEXEC=1` lets scripts embedded in the .blend run (Rigify `rig_ui.py`, Python drivers) — trusted files only.
- Live mode changes the scene the user is looking at: scope edits to named collections, never clear the scene,
  save first. Use it to show work in progress; build and export headless.
- Long runs (bakes, many renders) go in the background while you study the next reference crop.

## Step scripts vs tool scripts

**Step scripts** (`blender/assets/<Name>/build.py`, `blender/scripts/stages.py`, `ingest_mesh.py`): the libs
`blender/lib/{kit,export,audit,review}.py` are prepended, `ASSET` and `ROOT` are set, parameters come in env vars
(`STAGES=build,audit,review,export`, `BUDGET`, `CATEGORY` …), and the script assigns a top-level `result` printed as
one `RESULT_JSON {...}` line. Copy `blender/assets/Crate/build.py` to start an asset: all dimensions as variables at
the top, stages `build / audit / review / export`, `MATERIALS.update({...})` for its library materials.

**Tool scripts** (`blender/scripts/*.py` that `import gamelib`): run as they are, arguments after `--`, PASS/WARN/FAIL
lines and a final `DONE`. They read `asset.json` through `gamelib.config()`.

| Tool script | Does |
|---|---|
| `render_views.py` | ortho turnarounds, control images (`clay color texture lit normal depth mask`), pose tests (`--pose`), animation contact sheets (`--action --frames`), camera JSON for projection |
| `qa_check.py` | stage checks against asset.json (`--stage model|uv|texture|rig|anim|all`) |
| `uv_tools.py` | `unwrap / pack --density / lightmap / check` |
| `project_paint.py` | project painted views onto the UVs (texturing.md) |
| `bake_maps.py` | high→low and self bakes (N, AO, Curv, ID, BC, E) |
| `build_material.py` | URP-ready material from a Unity-named texture set |
| `game_skeleton.py`, `weights.py` | game rig from a control rig; bind / clean / rigid weights |
| `anim_tools.py` | list, loopfix, motion (speed), inplace, events |
| `export_skinned.py` | SK_ export for Unity + manifest + round trip |
| `make_humanoid_bases.py` | rebuilds `blender/bases/humanoid/` from Blender Studio's CC0 bundle (`tools/fetch_humanoid_bases.sh`) |
| `stages.py`, `ingest_mesh.py`, `lod_regen.py`, `uv_audit.py` | step scripts: audit/review/export any asset; ingest external meshes; far-LOD regeneration; UV distortion on FBX |

Writing a new tool script: start with
```python
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g
cfg = g.config(); a = g.kv_args()
...
g.report("PASS", "..."); print("DONE <what>")
```
`gamelib`: `config() path() kv_args() sub_collection() asset_objects() armature() evaluated_tris() bounds()
select_only() save() uv_stats() uv_mode() channelbag() fcurves() load_pixels() save_pixels() report()`.

## The modelling kit (blender/lib/kit.py)

Conventions that make UVs, masks and export work without per-asset fixes: real metres, Z up, front −Y, ground at
z = 0, pivot bottom centre; each part built in a **local frame** (long/grain axis = local X), UV-mapped there in metres
per tile, then moved into place with `bmesh.ops.transform` — objects keep identity transforms. Each asset lives in
collection `SM_<Name>` with one sub-collection per part group. Face layers `edge` (bevel faces) and `var` (per-part
random) feed the vertex-colour masks.

Helpers: `box`, `box_bm`, `cylinder_bm`, `sweep`/`sweep_bm` (beams, pipes, trims along a polyline), `prism`
(extruded outline), `arch_outline`, `make_template` + `instance` (many repeated pieces), `chisel_bm` (rough stone
blocks), `peg_bm` (bolts, rivets), `soft_normals` (60° hard edges + weighted normals), `mat`/`M` (library materials),
`xf` (location/rotation matrix), `clear_coll`, `solo`.

`audit.py`: `validate(root)` (tris, transforms, non-manifold, loose verts, n-gons, zero-area, UV layers, missing
images), `audit_asset(root)` (floating islands, unsupported member ends, inverted shells, lowest point),
`clashes(root)` (triangle overlaps between objects), `check_budget(root, max_tris, max_materials)`.
`review.py`: `review_views(root, tag)` — look-dev renders (AgX, EEVEE, grey ground) front/back/left/right/top/¾/low
into `renders/<Name>/`. `export.py`: see unity-pipeline.md "Export → import contract".

## Looking at it

Two renderers, two jobs:
- `review_views` (step libs, `STAGES=review`): look-dev perspective views with lighting — "does it look right?"
- `render_views.py` (tool): orthographic, auto-framed, comparable round to round — turnarounds against reference
  crops, control images for AI models, pose tests, animation contact sheets, and the cameras for projection.

```bash
R=blender/scripts/render_views.py; F=blender/assets/Crate/Crate.blend
ASSET=Crate tools/blender_run.sh $R $F -- --tag look                                   # clay: front,right,back,q34
ASSET=Crate tools/blender_run.sh $R $F -- --tag lit --mode lit --views front,q34,back
ASSET=Crate tools/blender_run.sh $R $F -- --tag ctl --mode depth --views front,right,back,left,top --size 1024
ASSET=Guard tools/blender_run.sh $R $F -- --tag walk --action ctrl_Walk --rig rig --views right --frames 1,5,9,13,17,21
ASSET=Guard tools/blender_run.sh $R $F -- --tag pose --pose renders/Guard/pose_test.json --rig rig
python3 tools/sheet.py renders/Crate/round3.png renders/Crate/review_*.png               # labelled contact sheet
```
Output: `renders/<Name>/<tag>_<view>.png`, `<tag>_sheet.png` (rows = frames), `<tag>_cams.json`. **Read the sheet
and say what you see** before claiming anything; always include back and sides — holes and clashes hide there.
Data modes (normal, depth, mask) render with the Raw view transform: a camera-facing normal is exactly (128,128,255).

## Blender 5.x gotchas (verified)

| Symptom | Cause | Fix |
|---|---|---|
| `'Action' object has no attribute 'fcurves'` | 5.x layered/slotted actions | `g.fcurves(action)` / `g.channelbag(action, slot)` |
| Action assigned but nothing plays | slot not set | `ad.action = act; ad.action_slot = act.slots[0]` |
| `keyframe_points.insert(..., options={'REPLACE'})` adds nothing | REPLACE only replaces existing keys | omit `options` |
| `'BLENDER_EEVEE_NEXT'` invalid | renamed back | `'BLENDER_EEVEE'` |
| DeprecationWarning `use_nodes` | node trees always exist | drop `use_nodes = True` |
| Control images off (0.5 → 188) | sRGB view transform on data | `view_settings.view_transform = 'Raw'` |
| `bpy.ops` "context is incorrect" | operator needs context | `g.select_only([...])` + `mode_set`, or `bpy.context.temp_override(...)` |
| `ReferenceError: BMesh data removed` | vert refs kept across bmesh ops (`bevel` replaces faces) | diff `set(bm.verts)` before/after; assign UVs after bevelling |
| `IndexError: outdated internal index table` | indexing after adding geometry | `bm.verts.ensure_lookup_table()` |
| "Bone Heat Weighting: failed" | tiny faces at human scale, non-manifold mesh | `weights.py bind --scale10`; weld; or skin a voxel-remeshed proxy and transfer |
| Rigify rig wrong headless | `rig_ui.py` / Python drivers not run | `AUTOEXEC=1` (trusted files) |
| Bake "No active image found" | image node not active in every material | `nt.nodes.active = node` per material |
| Instances inside out | basis matrix with det < 0 | keep it right-handed; `audit_asset` reports inverted shells |
| `uv.pack_islands` ignored islands | only packs selected UVs | select all in UV and mesh |
| Renders washed out | Filmic/AgX on review renders | `Standard` (review), `Raw` (data) |
| Six parallel bakes filled the disk | ~0.5 GB temp per Cycles bake | one bake at a time |
