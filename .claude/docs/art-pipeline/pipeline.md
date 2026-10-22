# Art pipeline: stages, assets, contracts

## Where an asset comes from and where it ends

```
/art-bible (Asset Standards, 3D Production)  →  /asset-spec  →  design/assets/asset-manifest.md  ASSET-NNN  Needed
        ↓ /produce-asset ASSET-NNN
blender/assets/<Name>/  asset.json · BRIEF.md · PROGRESS.md · build.py (+ parts/) · <Name>.blend · textures/ · ref/
        ↓ stages, each: script → numbers → renders → look → QA → asset-critic → gate (ask)
brief → model → uv → texture ┐
                    └ rig ───┴→ anim → export → Unity (prefab, animator, capture)
        ↓
Assets/Art/{Environment/<Category>,Characters}/<Name>/  SM_/SK_ model, PF_<Name>.prefab, AC_<Name>.controller, T_* maps
manifest row → Done (link to the Unity capture and the export report)
```

Skip stages an asset doesn't need (a static prop has no rig/anim; a flat-colour or tiling-library asset may skip
painting and baking) and write the skipped stages into `BRIEF.md` so a skip is never silent.

## Stage owners and exits

| Stage | Owner agent | Reference | Exit check |
|---|---|---|---|
| Brief | `art-director` | this file | `asset.json` + `BRIEF.md` agreed with the user |
| Model | `3d-artist` | `modeling.md`, `blender.md` | `stages.py` audit clean, `qa_check --stage model`, review renders read, `asset-critic` pass |
| UV | `technical-artist` | `uv-unwrapping.md` | `qa_check --stage uv`, checker render read |
| Texture | `texture-artist` | `texturing.md` | `qa_check --stage texture`, lit + texture renders read, coverage ≥ 97 % for painted assets |
| Rig | `rigger` | `rigging.md` | `qa_check --stage rig`, pose-test sheet read |
| Anim | `animator` | `animation.md` | `qa_check --stage anim`, contact sheets read |
| Export / Unity | `technical-artist` | `unity-pipeline.md` | export round trip, `import_assets.cs` report ("materials mapped", avatar valid), Unity capture read |
| Any stage | `asset-critic` | `qa.md` | AD-ASSET verdict (`.claude/docs/director-gates/ad-asset.md`) |

The `unity-specialist` is consulted for import rules, prefabs, animator and URP questions; `performance-analyst` for
frame-time numbers; `world-builder` / `level-designer` place finished prefabs in scenes.

## The asset folder

```
blender/assets/<Name>/            <Name> = PascalCase, the base name everywhere (SM_<Name>, PF_<Name>, T_<Name>_BC ...)
  asset.json                      the numbers scripts read (below)
  BRIEF.md                        what and why: spec excerpt, piece list, construction, skipped stages, definition of done
  PROGRESS.md                     durable log: current state, open gaps, numbers per pass, decisions (latest wins)
  build.py                        the build entry point (step script; parts/*.py for complex assets, run in order by it)
  <Name>.blend                    the working file (Git LFS). Back up before risky steps: <Name>.<date>.blend in the folder
  textures/                       the asset's own maps T_<Name>_{BC,N,MS,AO,E,H,Mask}.png (unique/baked/projected)
  ref/                            reference crops per view/region (derived from sources/, safe to rewrite)
  scripts/                        stage scripts that must be re-runnable: materials.sh, rig.sh, anim_<Clip>.py
sources/                          append-only inputs (hook-enforced): reference/, tripo/<Name>/, weave/<Name>/
blender/bases/humanoid/           CC0 rigged base bodies (Rigify): copy one into an asset folder, never edit in place
textures/<Set>/                   shared tiling sets for the MI_ material library (gen.sh = the prompts)
renders/<Name>/                   review renders, control images, sheets (git-ignored)
blender/export/<Category>/<Name>/ generated exports + manifest (git-ignored; Unity keeps the copies)
```

## asset.json

```json
{ "name": "Crate", "category": "Props", "type": "prop", "height_m": 0.6,
  "budget":   {"tris": 2000, "materials": 2, "bones": 0, "influences": 4, "uv_maps": 2},
  "textures": {"size": 1024, "texel_density": 512, "uv_mode": "unique"},
  "lods": [0.5, 0.25],
  "rig":      {"armature": null, "skeleton": "unity-humanoid"},
  "animations": [{"name": "Open", "frames": [1, 30], "loop": false, "root_motion": false}],
  "spec": "ASSET-012", "spec_file": "design/assets/specs/storage-assets.md" }
```
- `category`: `Props | Buildings | Nature | Characters` (= `blender/export/<Category>/` = `ProjectPaths.Category`).
- `collection`: default `SM_<name>` (`SK_<name>` for Characters); every shipping object lives under it.
- `textures.uv_mode`: optional; by default derived per object from its materials (only `MI_*` = tiling, else unique).
- Values come from the spec and the art bible's Asset Standards; when the bible is silent use the table below and
  say so in `BRIEF.md` ("budget from pipeline defaults, no bible value").
- Scripts select it with `ASSET=<Name>` (tools/blender_run.sh sets `ASSET_JSON`).

## Default budgets (when the art bible sets none)

| Class | LOD0 tris | Materials | Texel density | LODs |
|---|---|---|---|---|
| Small prop (< 0.5 m) | 300–1.5k | 1 | 512 px/m | LOD1 50 %, cull |
| Medium prop (crate, chair) | 1k–5k | 1–2 | 512 px/m | 50 % / 25 % |
| Large prop / vehicle | 5k–25k | ≤ 4 | 512 px/m | 50 % / 15 % |
| Building (exterior) | 25k–100k | ≤ 6 | 256–512 px/m | 25–30 % / 2–4 % (≤ 3.5k) |
| Landmark / walk-in | ≤ 250k | ≤ 8 | 512 px/m | 25 % / 2 % (≤ 12k) |
| Character | 15k–50k | 1–3 | 1024 px/m | 50 % / 20 % |
| Creature | 8k–30k | 1–2 | 1024 px/m | 50 % / 20 % |
| Tree / plant | 2k–15k | 2 (bark, leaves) | — | 50 % + cross-fade |

Mobile/VR: divide by 4–10. Far LODs ≤ 2–3k tris, 1 material, used beyond ~120 m. Bones: humanoid 30–70 (+ ~30
fingers), creature 20–60. Influences: 4 (Unity's default skin weights). Third-person mid-range props 512 px/m,
first-person/hero 1024 px/m, large environment 256 px/m; keep one density per scene.

## Naming contract (Blender name = Unity name)

| Prefix | What | Example |
|---|---|---|
| `SM_` | static mesh FBX / collection; LODs `_LOD1`, `_LOD2` | `SM_Crate.fbx` |
| `SK_` | skinned mesh FBX / collection | `SK_Guard.fbx` |
| `PF_` | prefab (made in Unity) | `PF_Crate.prefab` |
| `MI_` | shared library material (tiling textures, `textures/<Set>/`) | `MI_WoodPlanks` |
| `M_` | material unique to one asset (its own UV atlas) | `M_Crate` |
| `T_` | texture `T_<Stem>_<Map>`, Map ∈ `BC N MS AO E H Mask` (`ORM` for non-Unity copies) | `T_Crate_BC.png` |
| `AC_` / `AM_` | animator controller / avatar mask | `AC_Guard.controller` |
| `UCX_` | convex collision hull in an FBX | `UCX_SM_Crate_00` |

`<Stem>` = the material name without `MI_`/`M_` (`M_Crate` → `T_Crate_*`): that is how Unity's `EnsureMaterials`
finds the maps. Object names inside the .blend: `<Name>_<Part>` (`Crate_Lid`), sides `.L/.R`. Renaming a material
means re-exporting. If the art bible states a different naming rule, the bible wins and `AssetImportRules.cs`,
`ProjectPaths.cs` and this table change in the same commit.

## Rules (each one cost time once; see docs/art-pipeline/LESSONS.md)

1. **The reference is the spec, and looking is the work.** Never call a stage done without having rendered it and
   read the image. Report what was verified (numbers, images seen) and what was not.
2. **Measure, don't assume.** Every step returns numbers (`RESULT_JSON`, PASS/WARN/FAIL lines); check them.
3. **Re-runnable everything.** Every change is a script (`build.py`, `parts/`, `scripts/`); re-running never
   stacks edits. Post-process steps get undone by rebuilds: write "re-run X after Y" and chain them.
4. **sources/ is append-only** (hook-enforced): references and paid generations are evidence.
5. **Lock upstream before downstream.** Topology freezes at the UV gate; UVs freeze before painting and skinning.
   Unlocking a stage means re-running everything after it: say so before doing it.
6. **Budgets are real**: `qa_check.py` reads them from `asset.json`. Over budget = fix or ask.
7. **Paid generation asks every time** (Weave, Tripo, AI Hub) in every automation mode; quote first.
8. **Stop at gates.** At each gate: QA, renders, the AD-ASSET verdict, the gate report, the question.
9. **Keep PROGRESS.md current** after every pass; it survives compaction. Session-level state still goes to
   `production/session-state/active.md`.
10. **Be honest about limits.** Scripted geometry has a ceiling (organic sculpt detail, hair, cloth): say so and
    propose the tool (hand sculpt, Tripo/Hunyuan + retopology, a marketplace asset), with its cost.
11. **Unity assets move only through Unity** (`AssetDatabase`), never `mv`/`rm`/Finder inside `Assets/`.

## Parallel work

Two writers never share one `.blend`. After the UV gate:
- `rigger` works in `<Name>.blend`;
- `texture-artist` copies it to `<Name>.tex.blend`, produces only files (`textures/T_*.png`, `scripts/materials.sh`
  = `build_material.py` calls), and the merge is running `scripts/materials.sh` on `<Name>.blend`.
- Several assets build in parallel (own folders, own `.blend` files, headless Blender). Nobody touches Unity, git or
  someone else's files in parallel; Unity import runs once, at the end, from one session.
- Disk-heavy jobs (Cycles bakes ~0.5 GB temp each) run one at a time.

## Gate report (every stage, same shape)

```
Asset: Crate (ASSET-012) · Stage: texture · AD-ASSET: APPROVE (asset-critic)
QA: fail=0 warn=1 pass=14 (warn: overlap 6 % — mirrored sides, intended)
Numbers: 1,184 / 1,500 tris · 512 px/m · T_Crate_{BC,N,MS,AO} 1024² · coverage 99.2 % · Weave 21.5 credits
Looked at: renders/Crate/lit_sheet.png, tex_sheet.png vs blender/assets/Crate/ref/front.png, side.png
Seen: lid planks match; stencil softer than reference; colour seam at the back-left corner
Skipped: rig, anim (static prop, BRIEF.md)
Next: uv lock holds · proceed to export? / iterate / change the brief
```
