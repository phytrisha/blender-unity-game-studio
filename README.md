# Blender + Unity Game Studio

A game studio inside Claude Code for one stack: **Unity 6 (URP, C#)** for the game and **Blender** for 3D art.
It is a fork of [Claude Code Game Studios](https://github.com/donchitos/claude-code-game-studios) (CCGS 1.2.0)
narrowed to Unity, with a **3D art department** that builds assets in Blender by script and ships them into Unity
as prefabs. The department merges the Blender → Unity pipeline from `unity-build-template` (kit, exports, import
rules, prefab builder, scene audits, Tripo) with the game-asset skills from `blender-game-asset-skills`
(Figma Weave projection painting, bakes, Rigify → game skeleton, animation tools, stage QA).

| | |
|---|---|
| **Agents** | 44 — CCGS's directors, leads and specialists (Unity only) + `3d-artist`, `texture-artist`, `rigger`, `animator`, `asset-critic` |
| **Skills** | 80 — CCGS's 74 + `/produce-asset`, `/art-stage`, `/paint-asset`, `/texture-set`, `/generate-model`, `/art-review` |
| **Hooks** | CCGS's 15 + `validate-sources.py` (art inputs append-only), `weave-guard.py` (credit cap + spend ledger) |
| **Verified** | Blender 5.1.2 · Unity 6000.6.0f1 (headless, real import of static, painted, Generic and Humanoid assets) · Figma Weave projection painting — `tools/tests/art_pipeline_smoke.sh` re-checks the Blender side |

## How a game gets made here

```
/start → /brainstorm → /setup-engine (Unity) → /art-bible → /map-systems → /design-system ... → /create-architecture
      → /asset-spec (entity inventory, per-asset specs) ─────────────┐
      → /create-epics → /create-stories → /sprint-plan → /dev-story │ (gameplay code in Assets/Scripts/)
                                                                    ▼
      /produce-asset ASSET-NNN   brief → model → uv → texture ∥ rig → anim → Unity prefab   (gate per stage)
```

CCGS runs design, code, QA and production with its gates and its collaboration protocol (Question → Options →
Decision → Draft → Approval). The art department plugs in where CCGS stopped at specs: `/asset-spec` writes the
spec and the manifest row; `/produce-asset` turns it into a prefab in `Assets/Art/` and marks the row Done.

## The 3D art department

```
art-director (lead: art bible, per-asset brief)
├── 3d-artist        model stage   bpy/bmesh part scripts, blockout → detail, budgets, deformation topology
├── technical-artist uv + Unity    unwrap/density, LODs, UCX, export, sync, import rules, prefab, capture, perf
├── texture-artist   texture       Figma Weave / AI Hub repaint → projection onto UVs, tiling sets, bakes, Unity maps
├── rigger           rig           Rigify → clean game skeleton (Unity Humanoid names), weights, sockets, pose tests
├── animator         anim          clips, loops, root motion, speeds, events, contact sheets, bake
└── asset-critic     AD-ASSET      independent review of every stage, never sees the builder's report
```

Every stage: the agent builds by re-runnable script → this session runs `qa_check.py` and reads the render →
`asset-critic` reviews (AD-ASSET: APPROVE / REVISE / REJECT / NOT ASSESSED) → you decide at the gate.

Rules that carry the most weight (CLAUDE.md "Art Pipeline"):
- **Look before you claim** — numbers and pictures at every stage; a check that could not run says NOT ASSESSED.
- **Paid generation always asks** — Weave, AI Hub and Tripo are quoted first and approved per run in every
  automation mode; `production/art/weave-budget.json` caps the spend; every paid run lands in the ledger.
- **`sources/` is append-only**, and **Unity assets move only through Unity**.
- **Bounded art-stage exception** — art agents rewrite inside the one asset folder a skill named, without a prompt
  per file; the stage still ends at your gate (enforced by `.claude/scripts/write-guard.sh`).

| Command | What it does |
|---|---|
| `/produce-asset ASSET-NNN` | One asset end to end, gate per stage, manifest updated |
| `/art-stage <stage> <Name>` | One stage (model, uv, texture, rig, anim, unity) |
| `/paint-asset <Name>` | Control renders → Weave/AI Hub repaint → projection onto UVs → Unity PBR maps |
| `/texture-set <Material> "<desc>"` | Seamless tiling set for the `MI_` library |
| `/generate-model <Name> "<prompt>"` | Tripo / Hunyuan 3D mesh → ingest (scale, pivot, weld, decimate) |
| `/art-review <Name> [stage]` | Independent AD-ASSET review |
| `/asset-audit` | Naming (art bible or the pipeline contract), sizes, formats, Unity orphan report |

Knowledge: `.claude/docs/art-pipeline/` (pipeline, blender, modeling, uv-unwrapping, texturing, ai-models,
rigging, animation, unity-pipeline, unity-project-structure, qa, reference) — read by section.
Lessons and checklists that grow with the game: `docs/art-pipeline/LESSONS.md`, `CHECKLISTS.md`, `docs/perf.md`.

## Layout

```
.claude/            agents, skills, hooks, rules, docs (CCGS + art department)
Assets/ Packages/   the Unity project IS the repo root (ProjectSettings/ appears on first open)
  Packages/com.phytrisha.studio-pipeline/  Unity package: ProjectPaths, AssetImportRules, AssetPipeline, ProjectSetup, PerfBench
blender/lib/        kit.py, export.py, audit.py, review.py (step libs) + gamelib.py (tool lib)
blender/scripts/    stages, ingest_mesh, lod_regen, uv_audit, render_views, project_paint, bake_maps, build_material,
                    uv_tools, qa_check, game_skeleton, weights, anim_tools, export_skinned
blender/assets/<Name>/  asset.json, BRIEF.md, PROGRESS.md, build.py, <Name>.blend, textures/, ref/, scripts/
blender/bases/humanoid/ four CC0 Rigify base bodies (stylised 25k / realistic 85k tris) — copy to start a character
tools/              blender_run.sh, sync_to_unity.sh, unity_run.sh, tripo_make.sh, sheet.py, new_project.sh,
                    texture/ (aihub_image, derive_pbr_maps, texture_tools), tests/art_pipeline_smoke.sh
unity/              C# eval scripts for the open editor: import_assets, preview_asset, capture, audit_scene, unused_assets
sources/            append-only inputs: reference/, tripo/, weave/
textures/           shared tiling sets (MI_ library)
design/ docs/ production/ studio-tests/   CCGS
```

## Getting started

Requirements: Claude Code, Blender 5.x, Unity Hub + Unity 6 (6000.x) with the Unity CLI (`~/.unity/bin/unity`),
`git` + `git-lfs`, `uv`, Python 3. Optional: the Figma plugin for Claude Code (Weave), the Tripo CLI, an HfG AI Hub
key (`.claude/settings.local.json`, see the `.example`), the Blender MCP add-on for live Blender sessions.

```bash
tools/new_project.sh ~/Dev/my-game "My Game"     # clean copy, own git history, LFS on
cd ~/Dev/my-game
# open the folder in Unity Hub (it is the Unity project), then Tools > Asset Pipeline > Setup Project
claude                                            # then: /start
tools/tests/art_pipeline_smoke.sh                 # Blender side of the pipeline, ~15 s
```
**Two ways to start a game.** `new_project.sh` makes a self-contained copy: the game owns every file and never sees
later studio changes. `link_project.sh` keeps one studio checkout for all your games: the game owns its design,
production, `Assets/` and art sources, and links to the studio for agents, skills, hooks, docs, `tools/`, the Blender
libraries and base bodies, the eval scripts, and the Unity package `com.phytrisha.studio-pipeline` (a relative `file:`
dependency). A studio fix then reaches every linked game at once.

```bash
tools/link_project.sh ~/Dev/my-game "My Game"    # linked game next to the studio, own git + LFS, first commit
cd ~/Dev/my-game && claude                        # once interactively: accept the trust prompt, then /start
<studio>/tools/link_project.sh --relink .         # after studio updates, a moved studio, or broken links
```
Linked games keep the studio path and commit in `.studio`, and add the studio to
`permissions.additionalDirectories` in `.claude/settings.local.json` (per machine, gitignored): without it Claude Code
won't read files through the links. Links are relative, so keep games and the studio side by side on every machine.
A game that needs stability pins the studio to a tag or commit.

Machine paths live in `.env` (from `.env.example`): `BLENDER`, `UNITY_CLI`, `UNITY_PROJECT=$ROOT`.
Unity steps need an open editor (GUI, or headless: `Unity -batchmode -projectPath . -logFile editor.log` without
`-quit`); without one the pipeline copies files and reports "import pending" instead of claiming an import.

## Keeping up with CCGS

This repo keeps CCGS's history (`git remote upstream` → donchitos/claude-code-game-studios). To take upstream
improvements: `git fetch upstream && git merge upstream/main`, then resolve. Expect conflicts where the
Unity-only conversion touched engine branches (setup-engine, test-run/test-scaffold, code-root resolution, the
engine tables in docs and studio-tests) and in the shared files the art department extends (CLAUDE.md, README,
agent-roster, directory-structure, workflow-catalog, art-director, technical-artist, asset-spec, asset-audit,
art-bible, director-gates, write-guard). Upstream's Godot/Unreal additions can be dropped.

## Credits

- [Claude Code Game Studios](https://github.com/donchitos/claude-code-game-studios) by Donchitos — MIT
  (`LICENSE`); the studio framework, agents, skills, hooks and gates.
- `unity-build-template` and `blender-assete-creation-template` — the Blender → Unity pipeline, kit, Unity editor
  code, lessons, checklists and the Rigify humanoid bases.
- Base meshes: Blender Studio, "Human Base Meshes" (CC0); rigs by `blender/scripts/make_humanoid_bases.py`.
- Upstream's release history and upgrade guide (CHANGELOG, UPGRADING) live in the CCGS repository.
