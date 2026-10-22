---
name: art-stage
description: "Run one art stage (model, uv, texture, rig, anim or unity) for one asset that already has a brief in blender/assets/<Name>/ — the stage's agent builds, this session checks and looks, asset-critic reviews, the user decides at the gate. Use to iterate a single stage, redo a stage after feedback, or step through an asset manually."
argument-hint: "<model|uv|texture|rig|anim|unity> <AssetName> [\"extra instructions\"] [--review full|lean|solo]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Agent, AskUserQuestion, SendMessage, Bash(bash "*/.claude/skills/art-stage/../../hooks/yaml-helper.sh" resolve_config *)
model: sonnet
---
# Art Stage

If the stage or the asset is missing, output usage guidance and exit:
> Usage: `/art-stage <model|uv|texture|rig|anim|unity> <AssetName> ["extra instructions"]` — the asset needs
> `blender/assets/<Name>/asset.json` and `BRIEF.md` (run `/produce-asset` first to create them).

This is one turn of `/produce-asset`'s stage loop, for when you want a single stage. The stage table, the briefing
rules, the return contract, the texture spend loop and the gate are those of
`.claude/skills/produce-asset/SKILL.md` Phase 3 (read that section) — this skill does not restate them.

## Phase 0: Resolve Config

!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys review_mode,automation,engine`

`review_mode` → whether AD-ASSET runs for this stage (`.claude/docs/director-gates.md`, second exception: `solo`
runs it only for `model` and `unity`; otherwise say `AD-ASSET skipped — Solo mode (stage <name>)`).
`automation` → the gate (`.claude/docs/automation-modes.md`); paid generation always asks. `engine` → the `unity`
stage needs Unity (else `NOT ASSESSED`, named).

## Phase 1: Preconditions

1. Read `blender/assets/<Name>/asset.json`, `BRIEF.md` (the stage's definition of done; is the stage skipped?) and
   `PROGRESS.md` "Current state" / "Open gaps".
2. Upstream lock: the stage before it must be marked passed in `PROGRESS.md` (model before uv, uv before texture and
   rig, rig before anim, all before unity). If not, say which and ask whether to run anyway (results may be redone).
3. If the stage was already passed and this run changes it, name the downstream stages that must re-run.

## Phase 2: Run the stage

Spawn the stage's agent exactly as `/produce-asset` Phase 3 specifies (the prompt names the asset folder; the extra
instructions from the argument go in verbatim). Texture stage: the spend loop. Then this session runs the stage's
check (`qa_check.py --stage <stage>`, or the export round trip and `import_assets.cs` report for `unity`) and Reads
the key image. A check that could not run is reported as `NOT ASSESSED — <why>`.

## Phase 3: Review and gate

1. AD-ASSET per the review mode (`asset-critic`, paths only, never the builder's report).
2. Append the pass to `PROGRESS.md`; one line to `production/session-state/active.md`.
   Writes inside `blender/assets/<Name>/` (the PROGRESS.md log, stage scripts, textures, the `.blend`) are the
   bounded art-stage exception for the asset this run named (CLAUDE.md "Art Pipeline"); anything else asks
   "May I write this to [filepath]?" first.
3. Gate report (`.claude/docs/art-pipeline/pipeline.md` "Gate report") and `AskUserQuestion`: accept the stage /
   iterate (what to change) / back to `/produce-asset` for the next stage / stop.

## Recommended Next Steps

- `/produce-asset <Name>` to continue the remaining stages in order
- `/art-review <Name> <stage>` for another independent look
- `/paint-asset <Name>` when the texture stage is a painted look
