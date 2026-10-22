---
name: paint-asset
description: "Paint a UV-locked asset with AI: render control images in Blender, repaint them in the art bible's style with Figma Weave (or the HfG AI Hub), project the painted views back onto the UVs, fill gaps, derive Unity PBR maps and build the material — with a quote and the user's approval for every paid run. Use for 'texture/paint this model', hand-painted or stylised looks, or texturing from a concept image."
argument-hint: "<AssetName> [\"style / material notes\"] [--views front,right,back,left,top] [--provider weave|aihub] [--model \"nano banana 2.1\"|\"flux depth pro\"]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Agent, AskUserQuestion, SendMessage, Bash(bash "*/.claude/skills/paint-asset/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---
# Paint Asset

If no asset is given, output usage guidance and exit:
> Usage: `/paint-asset <AssetName> ["style notes"] [--views ...] [--provider weave|aihub]` — the asset needs
> `blender/assets/<Name>/asset.json` and locked unique UVs (`/art-stage uv <Name>`).

The workflow, prompts, file locations and limits are in `.claude/docs/art-pipeline/texturing.md` sections
"Projection painting (/paint-asset)", "Paid generation: the credit protocol" and "Weave models worth knowing" —
read those three sections; this skill sequences them and holds the gates.

## Phase 0: Resolve Config

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys review_mode,automation`

Every paid run asks the user, in every `automation` mode (paid generation is an always-ask category). Other
decisions follow `.claude/docs/automation-modes.md`. `review_mode` → AD-ASSET for this texture stage
(`director-gates.md`, second exception; `solo` → `AD-ASSET skipped — Solo mode (stage texture)`).

## Phase 1: Preconditions

1. `asset.json`, `BRIEF.md` (texturing route, palette and style notes), art bible §4 Color System and §8.3
   (prompt style block) — each present or ABSENT; ABSENT style block → the prompt uses the brief's words and the
   report says so.
2. UVs: `ASSET=<Name> tools/blender_run.sh blender/scripts/uv_tools.py blender/assets/<Name>/<Name>.blend -- check`.
   Any object judged **tiling** (only `MI_` materials) is not a projection target: stop and say so (library
   materials → `/texture-set`). Unique UVs with overlap > 2 % or stretch > 0.25 → stop: `/art-stage uv` first.
3. Provider available: Weave MCP tools (`weave_find_model` responds) or `AIHUB_API_KEY` set. Neither → `NOT ASSESSED
   — no image provider`, stop.
4. Budget: `production/art/weave-budget.json` cap and the ledger total so far — state both.

## Phase 2: Control renders and the spend plan

1. Render clay + depth controls for the views (texturing.md step 1) at 1024 (2048 for hero assets); Read the clay
   sheet to confirm framing.
2. Spawn `texture-artist` with the asset folder, the views, the style notes (inline), the references, and **no
   approval**: it uploads the controls, writes the prompts, and returns the spend plan (hero view first, then the
   other views, optional background removal and upscale), each line quoted.
3. `AskUserQuestion` per run (hero view alone first; then up to 4 views per call), cost and running total in each
   option label. The first Weave quote in the conversation carries the response's `costDisclosure` sentence.

## Phase 3: Paint, look, project

1. Resume the agent with `approved: <runs and credits>`. It runs, downloads into `sources/weave/<Name>/`, and
   returns the paths. **Read the hero result before approving the rest**: silhouette moved, lighting baked in, or
   style off → propose a changed prompt and a re-roll (a new approval), never a silent retry.
2. Projection (`project_paint.py`) → per-view and total coverage; Read `T_<Name>_BC_coverage.png`.
3. Gaps > 3 % → `AskUserQuestion`: paint an extra view (quote) / inpaint the mask (quote) / accept the fill colour
   for the unseen area (free; recorded in BRIEF.md).
4. Maps: `derive_pbr_maps.py --unity` (`--delight` unless the style is painted), `bake_maps.py --maps ao`, then the
   agent writes `blender/assets/<Name>/scripts/materials.sh`; run it on `<Name>.blend`.

## Phase 4: Check and gate

1. `qa_check.py --stage texture` (no FAIL); `render_views.py --mode texture` and `--mode lit` front/q34/back — Read
   them next to the reference.
2. AD-ASSET per the review mode.
3. Report: maps (paths, sizes), coverage, runs and credits (from the ledger), what you saw, seams/limits, then
   `AskUserQuestion`: accept / repaint a view (quote) / adjust maps / stop. Append to `PROGRESS.md`.
   Writes inside `blender/assets/<Name>/` (the PROGRESS.md log, stage scripts, textures, the `.blend`) are the
   bounded art-stage exception for the asset this run named (CLAUDE.md "Art Pipeline"); anything else asks
   "May I write this to [filepath]?" first.

## Recommended Next Steps

- `/produce-asset <Name>` (or `/art-stage rig|unity <Name>`) to continue
- `/texture-set` for the library materials a scene still needs
- `/art-review <Name> texture` for a second independent look
