---
name: art-review
description: "Independent AD-ASSET review of one asset at one stage by the asset-critic agent: renders and Unity captures against the reference, the brief and the art bible, high-confidence findings only, verdict APPROVE / REVISE / REJECT / NOT ASSESSED. Read-only. Use for a second opinion, before a milestone, or when a stage 'looks off'."
argument-hint: "<AssetName> [model|uv|texture|rig|anim|unity] [\"focus, e.g. the boots\"]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Agent
model: sonnet
---
# Art Review

If no asset is given, output usage guidance and exit:
> Usage: `/art-review <AssetName> [stage] ["focus"]` — the asset needs `blender/assets/<Name>/asset.json`.

This skill runs the AD-ASSET gate on demand, in every review mode (an explicit request is not a workflow gate).

## Phase 1: Gather paths (not opinions)

1. Stage: the argument, else the last stage in `PROGRESS.md` "Current state".
2. Inputs: `asset.json`, `BRIEF.md`, the reference crops (`blender/assets/<Name>/ref/`, `sources/reference/...`),
   the newest sheets for the stage in `renders/<Name>/` (and `renders/unity/` for `unity`). If the newest sheet is
   older than `<Name>.blend`, render fresh ones first (`render_views.py`, the stage's mode) — a review of stale
   images is not a review of the asset.
3. A missing input is passed as missing; the critic answers NOT ASSESSED for it. Do not substitute a description.

## Phase 2: Spawn the critic

Spawn `asset-critic`. The prompt: read `.claude/docs/director-gates/ad-asset.md` first; the stage; the focus if
given; the paths above. **Do not include any builder's report, your own assessment, or PROGRESS.md's narrative** —
the review must not be anchored on them.

## Phase 3: Relay

Print the critic's verdict line and findings unchanged. Then, separately and labelled as yours, say which findings
you agree with after looking at the evidence images yourself, and which you can't confirm. No files are written.

## Recommended Next Steps

- `/art-stage <stage> <Name> "fix: <findings>"` to act on REVISE
- `/produce-asset <Name>` to continue once APPROVE
