# Texturing

## The Unity map contract

Unity's `AssetPipeline.EnsureMaterials` creates a URP Lit material for every material slot that has no project
material yet and wires the maps it finds by name: material `MI_Wood` or `M_Crate` → stem `Wood` / `Crate` →

| Map | File | Colour space | URP Lit slot | Notes |
|---|---|---|---|---|
| Base colour | `T_<Stem>_BC.png` | sRGB | `_BaseMap` | no lighting baked in (30–240 sRGB), except stylised painted looks; alpha → cut-out sprites |
| Normal | `T_<Stem>_N.png` | Non-Color | `_BumpMap` | **OpenGL (+Y)**, as Blender bakes it; Unity imports it as a normal map by the `_N` suffix |
| Metallic/Smoothness | `T_<Stem>_MS.png` | Non-Color | `_MetallicGlossMap` | R = metallic (0 or 1 per material, never derived from brightness), **A = smoothness = 1 − roughness** |
| Occlusion | `T_<Stem>_AO.png` | Non-Color | `_OcclusionMap` | |
| Emission | `T_<Stem>_E.png` | sRGB | `_EmissionMap` | black = none |
| Height / masks | `T_<Stem>_H.png`, `_Mask.png` | Non-Color | custom shaders | |

`AssetImportRules.cs` sets the import settings from the same suffixes. Sizes are powers of two ≤ `textures.size`.
Blender side: `blender/scripts/build_material.py` builds the same material from the same files (`--bc --n --ms --ao
--e`), so look-dev renders and Unity agree. Unique maps live in `blender/assets/<Name>/textures/` and ship with the
export; library sets in `textures/<Set>/` are copied to `Assets/Art/Textures/<Family>/` once.

## Choosing a route

| Asset | Route |
|---|---|
| Hard-surface / environment / kit pieces | library `MI_*` materials with tiling sets (`/texture-set`), vertex-colour masks for variation |
| Hero asset with unique look, stylised painted props, creatures, characters | unique UVs → `/paint-asset` (AI repaint of control renders, projected onto UVs) |
| High-poly exists (sculpt, subdivision, booleans) | `bake_maps.py` N/AO/Curv from the high; albedo from `/paint-asset` or library zones |
| AI mesh (Tripo/Hunyuan) | keep its maps for background props; re-texture heroes (`/paint-asset` or library zones) |
| Unique hero from tiling materials | tileable material per zone → masks (edge wear from G/AO, grime in cavities) → bake to the asset's own UVs (reference.md §2, §4) |

## Paid generation: the credit protocol (every provider, every run)

Figma Weave (MCP `weave_*` tools), the HfG AI Hub (`tools/texture/aihub_image.py`) and Tripo (`tools/tripo_make.sh`)
spend real credits. In every automation mode — paid external generation is irreversible, so it is an always-ask
category — each run follows:
1. **Find** (free): `weave_find_model(query)` → id, contract, ~cost; or `weave_list_tools()` /
   `weave_get_tool_inputs(recipeId)` for the user's published Weave flows (prefer those: they encode the user's taste).
2. **Quote** (free): `weave_run_model` / `weave_run_tool` **without** `acknowledgedCost` → `cost_confirmation_required`.
   AI Hub: state model and ~cost from `GET https://ai-hub.hfg-gmuend.de/api/tools/manifest`. Tripo: `DRY=1`.
3. **Ask**: AskUserQuestion, Approve / Cancel, showing purpose, model, cost and the running total
   (`production/art/weave-ledger.jsonl`, `sources/tripo/LOG.tsv`). One question per run, up to 4 per AskUserQuestion.
   The first Weave quote in a conversation adds the response's `costDisclosure` sentence. Never invent inputs.
4. **Run** with `acknowledgedCost` = the quoted number. Re-runs and re-rolls need a new approval.

Agents (`texture-artist`) cannot ask: they stop after step 2 and return a **spend plan** (one line per run: purpose,
model, inputs, quoted cost; total). The orchestrating skill asks and resumes the agent with
"approved: up to N credits for <runs>". `.claude/hooks/weave-guard.py` enforces the project cap in
`production/art/weave-budget.json` and logs every paid run (model, prompt, params, cost, ids) — the ledger is also
the recipe to reproduce a texture.

**Files**: upload a local image with `weave_upload_asset()` → `curl -s -F "file=@<path>" -H "X-Weave-Upload-Token:
<token>" "<submitUrl>"` → pass the whole asset object (token lasts ~10 min). Poll with `weave_get_model_run_output`
/ `weave_get_tool_run_output`. Download with the response's curl into `sources/weave/<Name>/<view>_<n>.png`
(append-only). Square in, square out: `aspect_ratio "1:1"`; resize to the control render's size if needed
(`sips -z 1024 1024 in.png --out renders/<Name>/painted_front.png`) — never edit the file in `sources/`.

## Weave models worth knowing (check `weave_find_model` for current ids and costs)

| Job | Model | ~Credits |
|---|---|---|
| Repaint a control render in a style, consistent across views (up to 14 reference images) | Nano Banana 2.1 (edit) | 3.5 |
| Same, higher fidelity, 2K/4K | Nano Banana Pro (edit) | 11 |
| Strict geometry lock from a depth / edge image | Flux Depth Pro / Flux Canny Pro | 6 |
| Text-to-image (tiles, concepts) | flux-3 | 4 |
| Inpaint holes / seams (white mask = change) | Flux Fill Pro, Flux 2 Inpaint [Klein 9B] | 4–10 |
| Upscale (fidelity mode; reject "creative" drift) | Magnific Upscale `optimized_for: videogame_assets`, Recraft Crisp | 18 / 5 |
| Background removal (alpha) | Bria Remove Background, Pixelcut | 0.6–1 |
| Image to 3D | Hunyuan 3D V2.1 / V3 (ai-models.md) | 25 / 80 |

AI Hub models (`tools/texture/aihub_image.py --model`): `gpt-image-2.5-flare-2026-09-08` (~8, default),
`gpt-image-2.5-sunburst-2026-09-08` (~8, most detail), `flux-3-image` (~75), `gemini-nano-banana-2.1` (~53),
`gemini-3-pro-image` (~209, hero only). Key `AIHUB_API_KEY` in `.claude/settings.local.json` (`env`); never print it.
Run hub generations one at a time (HTTP 429 at ~8 parallel).

## Projection painting (/paint-asset)

1. **Control renders** of the UV-locked asset, square, same cameras for every mode:
   ```bash
   R=blender/scripts/render_views.py; F=blender/assets/Crate/Crate.blend
   ASSET=Crate tools/blender_run.sh $R $F -- --tag ctl  --mode clay  --views front,right,back,left,top --size 1024
   ASSET=Crate tools/blender_run.sh $R $F -- --tag ctld --mode depth --views front,right,back,left,top --size 1024
   ```
   Keep `renders/Crate/ctl_cams.json`; projection uses exactly these cameras.
2. **Hero view first**: control render (+ reference / art-bible style refs) → Nano Banana 2.1:
   > Repaint image 1, a grey 3D render of a {asset}, as a finished game texture in the style of image 2:
   > {materials, colours, wear}. Keep the exact silhouette, framing, camera and every edge and panel position of
   > image 1. Flat, even, shadowless lighting: albedo colour only, no highlights, no cast shadows, no ambient
   > occlusion. Pure black background.
   Flux Depth Pro alternative: the depth render as `control_image`, the same text as prompt.
3. **Other views with the painted hero as a reference**: images = [control of this view, painted hero, reference],
   prompt adds *"the same object, same materials, colours and markings as image 2, seen from the {side}"*. Read each
   result; re-roll (new approval) when the silhouette moved or details contradict the hero view.
4. Optional background removal for clean alpha (the projector uses alpha as a weight).
5. **Project**:
   ```bash
   ASSET=Crate tools/blender_run.sh blender/scripts/project_paint.py $F -- --obj SM_Crate_Body \
       --cams renders/Crate/ctl_cams.json --size 2048 --power 4 \
       --images front:renders/Crate/painted_front.png,right:...,back:...,left:...,top:... \
       --out blender/assets/Crate/textures/T_Crate_BC.png
   ```
   Per texel, the views that see it most head-on win (facing^power × sun-shadow visibility × in-frame × alpha).
   Prints per-view and total coverage; writes `T_Crate_BC_coverage.png` (white painted, **red = inside the UVs
   but unseen**).
6. **Gaps**, in order: render + paint a view that sees them (`--tag ctl2 --views bottom`), then
   `--cams ctl_cams.json,ctl2_cams.json --base T_Crate_BC.png --fill-only` paints only the gaps; or inpaint in UV
   space (`uv run tools/texture/texture_tools.py coverage-mask T_Crate_BC_coverage.png renders/Crate/mask.png`,
   then Flux Fill with "continue the surrounding {material}" — fine for uniform materials, it can't know geometry);
   or accept the `--fill` colour for undersides nobody sees, and say so.
7. **Clean up and derive**: `derive_pbr_maps.py --unity --delight` (skip delight for painted styles), upscale with
   approval if soft, `bake_maps.py --maps ao` for occlusion, then `scripts/materials.sh` with `build_material.py`.
8. **Look**: `render_views.py --mode texture` and `--mode lit`, front/q34/back: seams where views meet, smears on
   surfaces seen edge-on, drift from the reference.

Honest limits: views disagree a little even with references (soft blends at borders); deep concavities are seen by
no view; the bottom is usually a fill; detail finer than a control pixel doesn't exist (2048 controls for heroes).

## Tiling material sets (/texture-set)

One prompt per material, not per asset. Template (tiling and view words first, a material, never a scene):
```
Seamless tileable <material> texture, <specifics + scale cue: "about 7 stones across the image">,
top-down orthographic view, perfectly flat surface filling the whole frame, flat even diffuse lighting,
no shadows, no highlights, no reflections, no perspective, no vignette, uniform albedo, PBR base color map
```
Append the art bible's prompt style block. Avoid big unique features, extreme colours, lighting moods. When the
structure is modelled (planks, tiles, rivets) ask for "one continuous surface, no seams" — never a tiled texture on
modelled tiles. Generate into `sources/weave/<Set>/` (Weave) or `textures/<Set>/<material>_raw.png` via `gen.sh`
(AI Hub; every prompt is a line in `gen.sh`, so a set can be regenerated). Then:
```bash
uv run tools/texture/texture_tools.py seam textures/Surfaces/oak_raw.png            # TILES or SEAM
uv run tools/texture/derive_pbr_maps.py textures/Surfaces/oak_raw.png --out-dir textures/Surfaces --name Oak \
    --unity [--make-tileable only if SEAM] --delight --normal-strength 4 --roughness-base 0.65 --roughness-range 0.2 [--metallic-map 1.0]
```
→ `T_Oak_{BC,N,MS,AO,H}.png` for `MI_Oak`. Derived normals come out ~2× too strong: start at Normal Map strength ~0.5
in Blender, set per-material normal scales in Unity and keep them in a table file. Smoothness too: generated wood
read wet (0.85 → 0.3) — keep a per-material table. Sprites (leaves, decals, grass cards): generate on solid magenta,
`texture_tools.py key raw.png T_<Name>_BC.png`. Use `--ref` (AI Hub) or a reference image (Weave) with an existing
project texture to keep a set consistent. UVs in metres per tile make every library material land at the same density.

## Baking

```bash
B=blender/scripts/bake_maps.py; F=blender/assets/Crate/Crate.blend
ASSET=Crate tools/blender_run.sh $B $F -- --low SM_Crate_Body --high Crate_high --maps normal,ao,curvature,id \
    --size 2048 --samples 64 --extrusion 0.02 --prefix T_Crate --outdir blender/assets/Crate/textures
```
Writes `T_Crate_{N,AO,Curv,ID}.png` (and `BC`, `R`, `E` on request). Rays start ~5 mm out, ~2.5 cm reach
(`--extrusion`, `--ray`): longer rays pick up neighbouring geometry; too short leaves black spots. Hard edges ⇒ UV
seams or the bake shows lines. Exploded bakes for close parts, on a copy (`<Name>.bake.blend`). Curvature is per
vertex (Pointiness): bake it from the dense high. AO with the real neighbours present. One Cycles bake at a time.
Read every baked map: banding, black blotches (cage), smears (wrong surface), seams.

## Vertex-colour masks (stylised variation without textures)

`export.apply_masks` writes vertex colour `Col` (linear): R custom mask (`mask_fn`, default up-facing for dust/moss/
snow), G bevel edge, B per-part random, A baked AO (dense parts only; list flat/shingle materials in `ao_skip` or they
bake near-black). Plain URP Lit ignores it; custom shaders (technical-artist) read it.

## Emissive under AgX

Near-black base colour, saturated emission, strength ~1 in Blender; higher washes to white.
