---
name: produce-asset
description: "Produce one 3D asset end to end — spec → brief → model → UV → texture → rig → anim → Unity prefab — with the art department (3d-artist, texture-artist, rigger, animator, technical-artist), an AD-ASSET review and a user gate per stage. Use for 'make/build/model this asset', an ASSET-NNN from the manifest, or any prop, character, creature, weapon or building that should end up in Unity."
argument-hint: "[ASSET-NNN | AssetName | \"description\"] [--from <stage>] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Agent, AskUserQuestion, SendMessage, TaskCreate, TaskGet, TaskList, TaskUpdate, Bash(bash "*/.claude/skills/produce-asset/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---
# Produce Asset

If no argument is provided, output usage guidance and exit without spawning agents:
> Usage: `/produce-asset [ASSET-NNN | AssetName | "description"] [--from <stage>] [--review full|lean|solo]` —
> an entry of `design/assets/asset-manifest.md`, an existing `blender/assets/<Name>/`, or a description.
> `--from uv` resumes at a stage. Do not use `AskUserQuestion` here; output the guidance directly.

One asset moves through gated stages. Each stage: the owning agent builds and returns; this session runs the
stage's numeric check and looks at its key image; `asset-critic` reviews independently (AD-ASSET); the user decides
at the gate. Knowledge lives in `.claude/docs/art-pipeline/` — read it **by section** (Grep `^#`, then the range).

**Decision Points:** every stage ends in an `AskUserQuestion` gate (proceed / iterate / change the brief). In
`collaborative` mode every gate asks; in `guided` mode a stage whose QA has no FAIL and whose AD-ASSET verdict is
APPROVE advances on its own with a one-line note; in `autonomous` mode the run continues and each outcome is
recorded with `log_decision`. **Paid generation (Weave, AI Hub, Tripo) is an always-ask category: every run is
approved by the user in every mode** (`.claude/docs/art-pipeline/texturing.md` "credit protocol"). See
`.claude/docs/automation-modes.md`.

## Phase 0: Resolve Config

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys review_mode,automation,team.size,engine`

Resolved above — use as-is; `--review` overrides `review_mode`. No block → defaults in
`.claude/docs/config-resolution.md`.

- **`review_mode`** → AD-ASSET frequency (`.claude/docs/director-gates.md`, second exception): `full`/`lean` after
  every stage; `solo` after the model stage and after the Unity import only. Every stage that skips it says
  `AD-ASSET skipped — Solo mode (stage <name>)` in its gate report.
- **`team.size`** → parallelism: `individual` (default) runs stages one after another; `small`/`studio` run the
  texture and rig stages in parallel after the UV gate (separate files — `pipeline.md` "Parallel work").
- **`engine`** (`engine.name` in project.yaml) → the Unity stage needs `Unity`. `unset` → Blender stages run, the Unity stage reports
  `NOT ASSESSED — engine not configured (run /setup-engine)`; any other value → `NOT ASSESSED — this studio supports
  Unity only`. Never treat it as a pass.

**Announce the active set before Phase 2** in one line: which agents this run will spawn, which stages the brief
skips, and whether texture/rig run in parallel.

## Phase 1: Load the asset

1. Resolve the argument:
   - `ASSET-NNN` → its row in `design/assets/asset-manifest.md` and its block in the spec file the row names.
   - `AssetName` with `blender/assets/<Name>/asset.json` → resume: read `PROGRESS.md` "Current state"; `--from`
     or the first stage not marked passed there.
   - A description with no spec → offer `/asset-spec` first (recommended: the spec carries the art-bible anchors and
     the 3D production block) or a quick inline spec that this run writes into `BRIEF.md`; ask which.
2. Read by section: art bible §8 Asset Standards (8.1–8.4), §3 Shape Language, §4 Color System, and the GDD
   sections the spec cites (gameplay sizes, timings). Report each as present or ABSENT; an absent bible section means
   pipeline defaults, and the brief must say which values are defaults.
3. **Tooling check** (observations; each missing tool makes the stages that need it NOT ASSESSED, named in the
   report): Blender (`source tools/env.sh; "$BLENDER" --version`), `uv --version`, the Unity CLI and an open editor
   (`"$UNITY_CLI" --version`; the editor check happens at the Unity stage), Weave MCP tools (texture route), `tripo`
   (Tripo route). References in `sources/reference/` or the spec.

## Phase 2: Brief (art-director)

Spawn `art-director` with: the spec block (inline), the art bible §8 lines you read (inline), the reference paths,
and `.claude/docs/art-pipeline/pipeline.md` sections "The asset folder", "asset.json", "Default budgets", "Naming
contract". Return contract: the drafts of `asset.json`, `BRIEF.md` (piece list with construction, crops to make,
stages skipped and why, definition of done per stage, spend estimate) and `PROGRESS.md` **in its reply** (it does not
write them), plus ≤5 bullets of decisions and any CONCERNS.

Present the brief summary and the numbers. `AskUserQuestion`: approve / change / stop. On approval ask
"May I write `blender/assets/<Name>/{asset.json,BRIEF.md,PROGRESS.md}`?" (one changeset) and write them. Crop the
reference into `blender/assets/<Name>/ref/` (`sips`), never touching `sources/`. Set the manifest row to
`In Progress` (ask before editing `design/assets/asset-manifest.md`).

## Phase 3: Stages

Run the brief's stages in order: **model → uv → texture ∥ rig → anim → unity**. Skip the ones the brief skips and
name each skip in the stage report. Per stage:

| Stage | Agent | Reference sections to name in the prompt | This session's check |
|---|---|---|---|
| model | `3d-artist` | modeling.md, blender.md | `qa_check.py --stage model` + `stages.py` audit; Read the clay sheet |
| uv | `technical-artist` | uv-unwrapping.md | `qa_check.py --stage uv`; Read the checker sheet |
| texture | `texture-artist` (spend loop below) | texturing.md | `qa_check.py --stage texture`; Read the lit sheet and the coverage image |
| rig | `rigger` | rigging.md | `qa_check.py --stage rig`; Read the pose sheet |
| anim | `animator` | animation.md | `qa_check.py --stage anim`; Read one contact sheet per clip |
| unity | `technical-artist` | unity-pipeline.md | the export round trip line and `import_assets.cs` report; Read the Unity capture |

**Brief each agent — do not dump context.** Pass: the asset folder path, the stage, the definition of done for the
stage from `BRIEF.md` (inline), the open gaps from `PROGRESS.md` (inline), the reference crop paths, the reference
doc sections by heading, any user instruction from the last gate, and for the texture stage the approval text if
one was given. **The prompt names the asset folder**, which is what activates the agent's bounded art-stage
exception (writes inside `blender/assets/<Name>/`, `renders/<Name>/`, `blender/export/<Category>/<Name>/`).

**Return contract** (end every agent prompt with it): "Return only: (1) files written or changed, (2) the QA SUMMARY
line and the key numbers, (3) the sheets you looked at and what you saw, (4) open gaps and honest limits, (5) any
questions or BLOCKED items, one line each. Do not restate the documents you read."

**Texture spend loop.** The texture-artist returns a spend plan (runs, models, quoted costs, total) unless the
prompt carried an approval. Show it with the running total from `production/art/weave-ledger.jsonl`; ask per run
(`AskUserQuestion`, up to 4 runs per call, Approve / Cancel each, cost in the label); resume the agent (SendMessage)
with `approved: up to <N> credits for <runs>`. Repeat until done. Merge: run
`blender/assets/<Name>/scripts/materials.sh` against `<Name>.blend` (it calls `build_material.py`).

**Then, in this session:**
1. Run the stage's check (`ASSET=<Name> tools/blender_run.sh blender/scripts/qa_check.py blender/assets/<Name>/<Name>.blend -- --stage <stage>`)
   and Read the stage's key image yourself. A check that cannot run → `NOT ASSESSED — <why>` for this stage.
2. **AD-ASSET** (when the review mode runs it here): spawn `asset-critic`; the prompt says to read
   `.claude/docs/director-gates/ad-asset.md` first and passes **only** paths — asset.json, BRIEF.md, reference crops,
   the stage's sheets — never the builder's report. REVISE → one fix round with the builder on the critic's findings
   ≥ 80 % confidence (or put them to the user); REJECT → straight to the user with the critic's reasoning.
3. Append the pass to `PROGRESS.md` (bounded: the agent did, or you append) and a line to
   `production/session-state/active.md`.
   Writes inside `blender/assets/<Name>/` (the PROGRESS.md log, stage scripts, textures, the `.blend`) are the
   bounded art-stage exception for the asset this run named (CLAUDE.md "Art Pipeline"); anything else asks
   "May I write this to [filepath]?" first.
4. **Gate**: the gate report (`pipeline.md` "Gate report") then `AskUserQuestion`: proceed to <next stage> /
   iterate this stage (what to change) / change the brief / stop here.

**Unlocking an earlier stage** (e.g. a model change after UVs): say which later stages must re-run, ask, then
re-run them in order. Never patch downstream around an upstream change.

## Phase 4: Unity

The `technical-artist` exports (`stages.py` for SM_, `export_skinned.py` for SK_), runs
`tools/sync_to_unity.sh <Category> <Name>` and captures the prefab (`unity/capture.cs`, a sandbox shot list in
`unity/args/capture.txt`). Editor closed or CLI unavailable → `NO_IMPORT=1` copy only and the stage reports
`Unity import: NOT ASSESSED — editor not running (files copied, import pending)`. Gate failures: UNMAPPED materials,
an INVALID avatar for a Humanoid brief, missing clips, LOD1/2 bounds off by > 0.1 m, pink shaders. Final AD-ASSET on
the Unity capture against the Blender look-dev render.

## Phase 5: Close

1. Ask "May I update `design/assets/asset-manifest.md`?" → status `Done` (or `In Progress` with the open gaps if the
   user stopped early), linking `blender/assets/<Name>/PROGRESS.md` and the capture.
2. When the asset closes a story, copy the Unity capture to `production/qa/evidence/` (the evidence rule in
   `.claude/docs/coding-standards.md`).
3. Final report: stages run / skipped / NOT ASSESSED (each named), AD-ASSET verdicts per stage, tris vs budget, maps,
   bones and clips, credits spent this run (Weave ledger, Tripo LOG.tsv, AI Hub gen.sh), Unity paths (prefab,
   controller), open gaps, honest limits.

## Recommended Next Steps

- `/art-review <Name>` for a fresh independent look at any stage
- `/produce-asset ASSET-NNN` for the next manifest entry, or `/asset-spec` to spec more
- `/asset-audit` once several assets are in `Assets/Art/`
- Gameplay hooks: hand the clip events and sockets to `gameplay-programmer` via `/dev-story`
