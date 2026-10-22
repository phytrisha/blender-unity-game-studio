---
name: texture-set
description: "Create a tileable PBR material set for the shared library (MI_<Material>): AI-generate a seamless base colour with Figma Weave or the HfG AI Hub, check tiling, derive Unity maps (BC, N, MS, AO, H), wire the Blender library material and, if Unity is open, the URP material. Use for 'make a wood/stone/metal material', trim sheets, terrain layers, or any tiling surface."
argument-hint: "<MaterialName> \"<material description>\" [--family Surfaces|Foliage|Cloth|Emissive] [--provider weave|aihub] [--metallic 0|1]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, mcp__plugin_figma_figma__weave_find_model, mcp__plugin_figma_figma__weave_upload_asset, mcp__plugin_figma_figma__weave_get_model_run_output, mcp__plugin_figma_figma__weave_list_tools, mcp__plugin_figma_figma__weave_get_tool_inputs, Bash(bash "*/.claude/skills/texture-set/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---
# Texture Set

If no material name is given, output usage guidance and exit:
> Usage: `/texture-set <MaterialName> "<description>" [--family Surfaces] [--provider weave|aihub] [--metallic 0|1]`
> e.g. `/texture-set WoodPlanks "weathered pine planks, 15 cm wide, vertical"`.

Recipe, prompt template and map rules: `.claude/docs/art-pipeline/texturing.md` sections "Tiling material sets
(/texture-set)", "The Unity map contract" and "Paid generation: the credit protocol" — read those sections.

## Phase 0: Resolve Config

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation`

Every generation asks the user in every mode (paid). Other decisions follow `.claude/docs/automation-modes.md`.

## Phase 1: Prepare

1. Name: `MI_<MaterialName>` → files `textures/<Family>/T_<MaterialName>_{BC,N,MS,AO,H}.png`. If the set exists,
   say so and ask: regenerate (new raw, keep the old one) / derive again from the existing raw / stop.
2. Prompt: the template + the description + a scale cue + the art bible §8.3 style block (ABSENT → say so). Show it.
3. Provider: Weave (`weave_find_model`, e.g. flux-3 or Nano Banana 2.1 with a reference set image) or AI Hub
   (`tools/texture/aihub_image.py`, the prompt appended to `textures/<Family>/gen.sh`). Neither available →
   `NOT ASSESSED — no image provider`, stop.

## Phase 2: Generate (one approval per run)

Quote (Weave without `acknowledgedCost`; AI Hub: model and ~cost), `AskUserQuestion` Approve / Cancel, run. Output:
Weave → `sources/weave/<MaterialName>/raw_<n>.png`; AI Hub → `textures/<Family>/<material>_raw.png`. Read it: one
continuous surface, no perspective, no shadows, no objects.

## Phase 3: Derive and check

```bash
uv run tools/texture/texture_tools.py seam <raw.png>                      # TILES or SEAM
uv run tools/texture/derive_pbr_maps.py <raw.png> --out-dir textures/<Family> --name <MaterialName> --unity \
    [--make-tileable only if SEAM] [--delight unless painted style] --normal-strength 4 --roughness-base <..> --metallic-map <0|1>
```
Read a 2×2 tiled preview (`python3 tools/sheet.py renders/textures/<MaterialName>_tile.png <BC> <BC> <BC> <BC> --cols 2`)
for seams and obvious repeats. Ask before writing the material: "May I add `MI_<MaterialName>` to the library
(Blender `MATERIALS` table in the kit or the asset's build.py, and Unity `Assets/Art/Materials/<Family>/` on the
next import)?"

## Phase 4: Unity (optional)

Library maps live in `Assets/Art/Textures/<Family>/`; the material `MI_<MaterialName>` is created by
`AssetPipeline.EnsureMaterials` the first time a model that uses the material is imported (it wires
`T_<MaterialName>_{BC,N,MS,AO,E}` by name). So:
1. Ask "May I copy the maps to `Assets/Art/Textures/<Family>/`?" and copy them (copy, never move; overwriting keeps
   the `.meta` GUIDs).
2. If the Unity editor is reachable, refresh the AssetDatabase so the import rules run
   (`tools/unity_run.sh` with an eval file containing `UnityEditor.AssetDatabase.Refresh(); return "ok";`) and
   report the result; otherwise report `Unity import: NOT ASSESSED — editor not running (maps copied, import pending)`.
3. Report `MI_<MaterialName>: created on the next import of a model that uses it` unless a model already did.

## Phase 5: Report

Files written, the prompt (and where it's logged), credits spent, TILES/SEAM result, the preview you looked at, the
per-material normal/smoothness values chosen (keep them in a table in `textures/<Family>/README.md`).

## Recommended Next Steps

- `/produce-asset` or `/art-stage model <Name>` for assets that use `MI_<MaterialName>`
- `/paint-asset <Name>` for assets that need a unique painted look instead
