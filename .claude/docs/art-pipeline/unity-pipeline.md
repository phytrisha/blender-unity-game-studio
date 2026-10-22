# Blender → Unity

```
blender/assets/<Name>/  ──stages.py (export.py)──>  blender/export/<Category>/<Name>/SM_<Name>{,_LOD1,_LOD2}.fbx + .glb + .json + Textures/
                        ──export_skinned.py──────>  blender/export/Characters/<Name>/SK_<Name>.fbx + SK_<Name>.json + Textures/
blender/export/...      ──tools/sync_to_unity.sh──> Assets/Art/{Environment/<Category>,Characters}/<Name>/
                        ──unity/import_assets.cs──> materials (EnsureMaterials/Remap) → AC_<Name> (characters) → PF_<Name>.prefab
scene placement (eval script) ──unity/audit_scene.cs──> FAIL/WARN ──unity/capture.cs──> renders/unity/*.png
```
The Unity project is the studio repo root (`Assets/`, `Packages/`, `ProjectSettings/`). Unity 6 + URP; the editor
version is pinned in `docs/engine-reference/unity/VERSION.md` and probed by `/setup-engine`.

## First-time setup

1. Open the repo folder in Unity Hub (Add → the folder) with the Unity 6 editor; let it import.
2. `Tools > Asset Pipeline > Setup Project` (or `tools/unity_run.sh` with `return ProjectSetup.Run();`): URP asset
   + Forward+ renderer, linear colour, Force Text, visible meta, Run In Background, Frame Timing Stats.
3. `.env` (copied from `.env.example`): `BLENDER`, `UNITY_CLI` (`~/.unity/bin/unity`), `UNITY_PROJECT=$ROOT`.
4. `Packages/manifest.json` carries `com.unity.pipeline` (enables `unity command eval_file`).

## Running Unity code from Claude

- `tools/unity_run.sh unity/<script>.cs [args...]` runs a C# eval script in the **open** editor: detached + `job
  wait` (plain eval has a ~5 s limit). Args land in `unity/args/<script>.txt` (a version-controlled shot list or
  route file can live there; no args = keep the file). The script sees `ROOT` and `ARGS`.
- Eval scripts: top-level statements, fully qualified `UnityEngine.`/`UnityEditor.` names, end with `return "<text>";`.
  They live in `unity/`, never in `Assets/` (they would compile into the game).
- Compile-check first: `COMPILE_ONLY=1 tools/unity_run.sh unity/x.cs`.
- Reusable logic belongs in `Assets/Scripts/Editor/` (`AssetPipeline`, `AssetImportRules`, `ProjectPaths`,
  `ProjectSetup`) so the menu, the CLI and other scripts share it. Eval scripts stay thin.
- Never hard-code folders: `ProjectPaths.Model/Prefab/Mat/Tex/AssetFolder`. Select assets by name or explicit list.
- The editor must be open with Run In Background on, or CLI-driven Play Mode hangs. If it isn't open, say so and
  stop at "copied, import pending" (`NO_IMPORT=1 tools/sync_to_unity.sh ...`) — never report an import that didn't run.

## Export → import contract

| Blender side | Unity side (AssetImportRules / AssetPipeline) |
|---|---|
| static: metres, `FBX_SCALE_NONE`, −Z forward, Y up, triangulated, tangents (`export.py`) | `useFileScale`, scale 1, **root rotation kept** (never reset it in prefab code) |
| skinned: `FBX_SCALE_ALL`, −Z / Y, deform bones only, no leaf bones, one take per clip (`export_skinned.py`) | `SK_` → Humanoid, avatar from the model, clips named after their take |
| custom split normals (60° + weighted) | `importNormals = Import`, `importTangents = Import` |
| UV1 `UVLightmap` (non-overlapping) | `generateSecondaryUV = false` |
| material names = library/unique names (`MI_*`, `M_<Name>`) | remap by name onto `Art/Materials/**`; missing → URP Lit by `EnsureMaterials` with the Blender colour (`.gamma`) and `T_<Stem>_{BC,N,MS,AO,E}` maps |
| `SM_X.fbx` + `UCX_SM_X_NN` hulls, `SM_X_LOD1/2.fbx` | `PF_X`: LODGroup, UCX → convex MeshCollider on LOD0, static flags, probe-lit |
| `SK_X.json`: clips {loop, rootMotion, events}, fps | Loop Time, root XZ lock (unless rootMotion), AnimationEvents (marker name = function) |
| `SK_X` clips | `AC_X.controller` (one state per clip, default Idle*/first loop), assigned on `PF_X`'s Animator |
| vertex colour `Col` (R mask, G edge, B random, A AO), linear | read by custom shaders; plain URP Lit ignores it |
| `SM_X.json` manifest (tris, materials, dims, anchors) | placement scripts read anchors; Blender (x, y, z) → Unity local (−x, z, −y) |

Pitfalls seen before:
- **Axis trap**: single-mesh static FBX carry a (−90°, 0, 0) / ×100 root. Code that resets the root lays LODs on
  their backs. Check by comparing LOD1/2 bounds with LOD0 (± 0.1 m).
- If Unity ever generates lightmap UVs on these files, `secondaryUVMinObjectScale = 100` or they collapse.
  Changing normal import settings regenerates them: rebake afterwards.
- Unity keys mesh sub-assets by name: keep object/mesh names stable across re-exports (`lod_regen.py` does).
- Copy updated files over the old ones (keeps `.meta` GUIDs). Moves/renames/deletes only through Unity.
- A-pose binds need a T-pose avatar reference for retargeting third-party clips; per-character overrides (arm-down
  limit, feet spacing) in a small JSON next to the model.
- Unity takes a material's colour from the Principled BSDF **Base Color**, not Blender's viewport colour
  (`diffuse_color`): set colours with the kit's `mat()` or `build_material.py`, or the Unity material comes out white.
- Preview and capture: assets face **+Z** in Unity (Blender −Y front); a front camera stands on the +Z side.
  `unity/preview_asset.cs` stages prefabs in `Scenes/Sandbox/Preview.unity` and poses clips with `SampleAnimation`.
- 4K character maps cost ~64 MB VRAM for three maps vs 16 MB at 2K: decide per camera distance.

## Sync and import

```bash
tools/sync_to_unity.sh Props Crate                 # copy FBX (+ LODs, Textures/, SK_ manifests) and run import_assets.cs
tools/sync_to_unity.sh Characters Guard
tools/sync_to_unity.sh Buildings Shed lightmapped  # 3rd word = import arg: LOD0 gets baked lightmaps
NO_IMPORT=1 tools/sync_to_unity.sh Props Crate     # editor closed: copy only, import later
```
`import_assets.cs` reports per asset: NEW materials created (check them, then move values into the library), rig
type and avatar validity (characters), the animator (clips, default state), prefab path and LOD count, LOD0 tris, and
"materials mapped" or UNMAPPED names. Any UNMAPPED, INVALID avatar or missing clip is a gate failure.

## Prefabs and placement

- LOD thresholds per category in `AssetPipeline.LodThresholds` (buildings .3/.12/.025, props .25/.08/.02, nature
  .14/.04/.012 with cross-fade). Renderers under 1.5 m cast no shadows.
- Probe-lit by default (LOD changes need no rebake); `lightmapped` for walk-in or hero pieces (LOD0 only). Never
  lightmap thousands of small overlapping parts.
- **Placeholder pattern**: the root holds logic, colliders and anchors; only a child `Visual` is swapped when art
  arrives — gameplay can start before the art is done.
- **Plan in Python, apply in Unity**: a planner with footprint checks writes a placement file (name, position,
  rotation, scale); an eval script applies it. Easy to diff and regenerate.
- Ground objects at the lowest footprint point, tilt runs (fences) along slopes, keep small furniture off paths and
  doorways. Fixed objects never move when resolving overlaps; every move is logged.
- After placing/moving static geometry: `audit_scene.cs` → walk test → probes → **rebake lighting AND occlusion
  culling** (stale occlusion data culled visible terrain as a white void).
- Interiors: enough UCX hulls that doors and aisles stay open; ramps for stairs; ray-test from inside for leaks.

## Terrain

Keep a read-only copy of the TerrainData in `Art/Environment/Terrain/Source/`; every terrain script rebuilds from it
and writes only changed cells. Pads: level at the footprint average, 1.2 m margin, 2.2 m front apron, 5.5 m
smoothstep falloff; cut deeper than ~1 m → retaining wall or move the building. Paths only lower the terrain;
re-ground objects afterwards. URP Terrain Lit draws 4 layers per pass: ≤ 8 layers per tile. Create TerrainData before
splatmaps; import textures before TerrainLayers; append layers. Multiple tiles: never `Terrain.activeTerrain`.
Terrain detail meshes: identity root transform (`VEGETATION=1` export), exactly one material.

## Review loop in Unity

1. `unity/audit_scene.cs` (args: root names, `walk x z x z ...` routes) → 0 FAIL (missing refs, pink shaders,
   floating/buried, overlaps, blocked walk routes with a player capsule r 0.33 h 1.8).
2. `unity/capture.cs` with a fixed shot list per area (`unity/args/capture.txt`), then `tools/sheet.py` before/after
   sheets; same shots every round. Captures go to `renders/unity/`; copy the ones that close a story to
   `production/qa/evidence/` (CCGS evidence rule).
3. Play Mode with 0 console errors (particles only animate in Play Mode).
4. `unity/unused_assets.cs` before deleting anything: the "used" count must not drop.

## Performance (player build)

Measure in a build with `Assets/Scripts/Runtime/Dev/PerfBench.cs` (`-perfbench`, views = children of `PerfViews`),
Frame Timing Stats on; modes interleave per view, medians, compare within one run (laptop throttling ±20 %). The
editor was ~2× faster than the build and missed pixel cost. Find costs by switching parts off (`noshadow`, `nossao`,
`noterrain`, `nodetails`, `hide:<group>`). Wins seen: grass/detail instance count, shadow distance 70 m with 2–3
cascades, no shadows on small renderers, LOD2 shadow proxies, STP at render scale 0.75, LOD bias 1–1.5, baked
occlusion culling, far LODs to fixed budgets (`lod_regen.py`), SSAO off where AO is baked. Didn't help: depth priming,
1024 shadow maps, GPU occlusion culling, Unity Mesh LOD on already-LODed FBX. Record results in `docs/perf.md`;
back up values before a pass; shared URP asset changes go in the session log. Lightmaps ≤ 2048 per atlas (a 4096 EXR
was 152 MB, over GitHub's file limit).

## Lighting and post defaults that worked (URP)

Forward+, mixed sun with Shadowmask, baked point lights, light probes around (not inside) objects, box-projected
reflection probes; HDR grading + Neutral or ACES; SSAO from DepthNormals (intensity ~1, radius ~0.2, downsampled).
More light beats more grading. Fog that looks right in the editor is often too heavy in play (0.011 → 0.006); check
from an elevated camera. Atmosphere in URP 17: a RenderGraph renderer feature with Unity's own fog off.
