# Skill Test Spec: /art-stage

## Skill Summary

Runs one art stage (`model`, `uv`, `texture`, `rig`, `anim` or `unity`) for one
asset that already has `blender/assets/<Name>/asset.json` and `BRIEF.md`. It is one
turn of `/produce-asset`'s Phase 3 loop and defers to that section for the stage
table, briefing, return contract, texture spend loop and gate rather than
restating them. Phase 0 resolves `review_mode`, `automation` and `engine`; Phase 1
checks preconditions (brief present, stage not skipped, upstream stage passed in
`PROGRESS.md`, downstream stages that must re-run if the stage was already
passed); Phase 2 spawns the stage agent and runs the stage check itself; Phase 3
runs AD-ASSET per the review mode (solo: only for `model` and `unity`), logs the
pass and ends at a user gate.

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains NOT ASSESSED (for a stage check that could not run or a non-Unity engine on the `unity` stage)
- [ ] Outputs usage guidance when the stage or asset is missing, before any spawn
- [ ] References `/produce-asset` Phase 3 for the stage mechanics instead of a second copy
- [ ] Has a next-step handoff (`/produce-asset`, `/art-review`, `/paint-asset`)

---

## Director Gate Checks

- **AD-ASSET**: `full`/`lean` → runs; `solo` → runs for `model` and `unity` only, otherwise `AD-ASSET skipped — Solo mode (stage <name>)`.

---

## Fixture Defaults

As `studio-tests/CLAUDE.md` § Fixture defaults; `engine.name: Unity`; `blender/assets/Guard/` has `asset.json`, `BRIEF.md` and `PROGRESS.md`.

---

## Test Cases

### Case 1: Happy path — texture stage, lean mode
**Fixture:** `modes.review_mode: lean`; PROGRESS.md marks model and uv passed; BRIEF route: library tiling (no paid runs)
**Input:** `/art-stage texture Guard "warmer leather"`
**Assertions:**
- [ ] texture-artist prompt names `blender/assets/Guard/`, carries "warmer leather" verbatim and the return contract
- [ ] The skill runs `qa_check.py --stage texture` itself and reads the lit sheet
- [ ] AD-ASSET runs (lean) with paths only
- [ ] Ends with a gate `AskUserQuestion`; PROGRESS.md and `active.md` get a line

### Case 2: Upstream not passed
**Fixture:** PROGRESS.md shows uv not passed
**Input:** `/art-stage rig Guard`
**Assertions:**
- [ ] The skill says uv has not passed and asks whether to run anyway, before spawning the rigger
- [ ] It does not silently mark uv as passed

### Case 3: Re-running a passed stage
**Fixture:** model, uv, texture passed; user runs `/art-stage model Guard "longer arms"`
**Assertions:**
- [ ] Before running, the skill names uv, texture (and rig/anim if in the brief) as stages that must re-run, and asks

### Case 4: Solo mode, uv stage
**Fixture:** review_mode resolves `solo`
**Input:** `/art-stage uv Guard`
**Assertions:**
- [ ] No asset-critic spawn; the report says `AD-ASSET skipped — Solo mode (stage uv)`
- [ ] The QA check still runs

### Case 5: Unity stage with no engine configured
**Fixture:** no `engine.name`
**Input:** `/art-stage unity Guard`
**Assertions:**
- [ ] Reports `NOT ASSESSED` naming the engine reason and `/setup-engine`; no import is claimed

### Case 6: Missing brief
**Fixture:** `blender/assets/Guard/asset.json` absent
**Input:** `/art-stage model Guard`
**Assertions:**
- [ ] Usage guidance pointing to `/produce-asset`; nothing spawned, nothing written

---

## Protocol Compliance

- [ ] Writes only through the stage agent's bounded exception and the PROGRESS/active.md appends
- [ ] Paid runs in the texture stage ask per run in every automation mode
- [ ] The critic never receives the builder's report

## Coverage Notes
- Stage mechanics are tested in depth by `/produce-asset`'s spec; this spec covers the single-stage entry, preconditions and re-run warnings.
