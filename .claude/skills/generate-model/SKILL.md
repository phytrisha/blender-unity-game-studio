---
name: generate-model
description: "Generate a 3D model with Tripo (CLI) or Hunyuan 3D (Figma Weave) from a prompt or concept image, ingest it into Blender (scale, pivot, facing, weld, decimate to budget, rename) and hand it to the art pipeline — with a dry run / quote and the user's approval before any credits are spent. Use for AI-generated props, statues, rocks, creatures, characters (incl. Tripo auto-rig), placeholders, or a high-poly to bake from."
argument-hint: "<AssetName> \"<prompt>\" | <image path> [--provider tripo|hunyuan] [--for game-pc|game-mobile|anim] [--height <m>] [--tris <n>]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Bash(bash "*/.claude/skills/generate-model/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---
# Generate Model

If no asset name and input are given, output usage guidance and exit:
> Usage: `/generate-model <AssetName> "<prompt>" | <image> [--provider tripo|hunyuan] [--height 0.9] [--tris 3000]`.

Everything provider-specific is in `.claude/docs/art-pipeline/ai-models.md` (read the sections "When to use them",
the provider's section, "Ingest", and "Characters" for rigged requests).

## Phase 0: Resolve Config

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation`

Paid generation asks the user in every mode.

## Phase 1: Fit check

1. Is a generated mesh the right tool for this asset (ai-models.md "When to use them")? Modular kit pieces, exact
   dimensions and mechanisms → say so and recommend `/produce-asset` with a scripted model instead; ask.
2. Budget and size from the spec / art bible §8.1 (or ask): `HEIGHT` (m) and `TRIS`.
3. Provider: `tripo doctor` (auth, balance) or Weave (`weave_find_model("hunyuan3d")`). Unavailable →
   `NOT ASSESSED — <provider> unavailable`, offer the other.

## Phase 2: Plan, quote, approve

- Tripo: `DRY=1 tools/tripo_make.sh <Name> "<prompt|image>" --for <scenario>` → model, steps, cost notes.
- Hunyuan: upload the concept (background removed if needed — that is a separate small quote), quote
  `weave_run_model` without `acknowledgedCost`.
`AskUserQuestion` Approve / Cancel with the cost; rigged characters: ask separately before paying for rig/retarget.

## Phase 3: Generate and judge

Run; outputs land in `sources/tripo/<Name>/` or `sources/weave/<Name>/` (append-only). Read the preview: fused parts,
broken silhouette, wrong facing, unusable texture → propose a re-roll with a changed prompt (a new approval) or stop.

## Phase 4: Ingest

Ask "May I create `blender/assets/<Name>/` (asset.json, BRIEF.md, PROGRESS.md, <Name>.blend)?", then:
```bash
ASSET=<Name> SRC=<sources path> HEIGHT=<m> TRIS=<n> tools/blender_run.sh blender/scripts/ingest_mesh.py
ASSET=<Name> CATEGORY=<Category> BUDGET=<n> STAGES=audit,review tools/blender_run.sh blender/scripts/stages.py blender/assets/<Name>/<Name>.blend
```
Read the review renders (front first: facing; fix with `YAW=180`). Write `BRIEF.md` with the source route, what the
generated maps are good for, and which stages remain (usually uv → texture → unity; rig/anim for characters).

## Phase 5: Report

Credits spent (LOG.tsv / ledger), the files, audit numbers, tris vs budget, what you saw, known flaws (non-manifold,
fused parts, baked light in the albedo), and the recommended next stage.

## Recommended Next Steps

- `/produce-asset <Name> --from uv` to continue in the pipeline
- `/paint-asset <Name>` to re-texture a hero asset in the art bible's style
- `/art-review <Name> model` for an independent look at the generated geometry
