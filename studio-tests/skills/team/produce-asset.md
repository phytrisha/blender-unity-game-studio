# Skill Test Spec: /produce-asset

## Skill Summary

Orchestrates the 3D art department through one asset, from spec to Unity prefab:
Phase 0 resolves `review_mode`, `automation`, `team.size` and `engine`; Phase 1
loads the asset (an `ASSET-NNN` manifest row + spec block, an existing
`blender/assets/<Name>/` to resume, or a description) and checks tooling; Phase 2
has `art-director` draft the brief (`asset.json`, `BRIEF.md`, `PROGRESS.md`),
returned in its reply and written by the skill after one "May I write" for the
changeset; Phase 3 runs the brief's stages (model → uv → texture ∥ rig → anim)
with the stage agents (`3d-artist`, `technical-artist`, `texture-artist`, `rigger`,
`animator`), this session's own `qa_check.py` run and image read per stage, the
AD-ASSET review by `asset-critic` (paths only, never the builder's report), and a
user gate per stage; Phase 4 exports and imports into Unity; Phase 5 updates the
manifest and reports. Paid generation (Weave, AI Hub, Tripo) is an always-ask
category: every run is approved by the user in every automation mode, through the
texture-artist's spend plan → per-run `AskUserQuestion` → resume loop. AD-ASSET
frequency follows the second exception in `.claude/docs/director-gates.md`:
`full`/`lean` after every stage, `solo` after model and unity only, each skip
announced. A Unity stage that cannot run (engine unset or not Unity, editor
closed) is NOT ASSESSED, never a pass.

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings (Phase 0 through Phase 5)
- [ ] Contains verdict keywords: APPROVE, REVISE, REJECT, NOT ASSESSED (the AD-ASSET vocabulary it branches on)
- [ ] "May I write" language present for the brief changeset and the manifest edit
- [ ] Outputs usage guidance and stops when no argument is given, before any spawn
- [ ] Phase 0 resolves `review_mode`, `automation`, `team.size` and `engine` with the `resolve_config` helper (key `engine`, not `engine.name`)
- [ ] Requires a one-line active-set announcement (agents, skipped stages, parallel texture/rig or not) before the first spawn
- [ ] States that paid generation asks per run in every automation mode, including `autonomous`
- [ ] Names the bounded art-stage exception: the stage agent's prompt names the asset folder, and only `blender/assets/<Name>/`, `renders/<Name>/`, `blender/export/<Category>/<Name>/` are covered
- [ ] Every agent prompt ends with the return contract (files, QA SUMMARY, sheets seen, gaps, questions)
- [ ] The AD-ASSET prompt passes paths only and explicitly excludes the builder's report
- [ ] Has a next-step handoff at the end (`/art-review`, `/produce-asset`, `/asset-spec`, `/asset-audit`, `/dev-story`)

---

## Director Gate Checks

- **AD-ASSET** (run by `asset-critic` for the art-director), per `director-gates.md` second exception:
  - **Full / Lean**: after every stage the brief runs
  - **Solo**: after the model stage and after the Unity import only; every other stage's gate report says `AD-ASSET skipped — Solo mode (stage <name>)`
- No PHASE-GATE or other director gate is spawned.

---

## Fixture Defaults

Every case's `project.yaml` sets `modes.rigor: minimal` and
`modes.automation: collaborative`, with no `project.local.yaml`, unless its own
Fixture says otherwise. Rules: `studio-tests/CLAUDE.md` § Fixture defaults.
Unless a case says otherwise: `engine.name: Unity`; Blender, `uv` and the Unity
CLI are installed; the Unity editor is open on the project; `design/art/art-bible.md`
has §8.1–8.4; `sources/reference/crate.png` exists.

---

## Test Cases

### Case 1: Happy path — static prop, full review mode

**Fixture:**
- `modes.review_mode: full` (pinned: AD-ASSET after every stage)
- `design/assets/asset-manifest.md` row `ASSET-012 | StorageCrate | Props | Needed | design/assets/specs/storage-assets.md`; the spec block has the 3D production table (route: library tiling `MI_WoodPlanks`, no rig, no clips)

**Input:** `/produce-asset ASSET-012`

**Expected behavior:**
1. Phase 0 block resolved; active set announced: art-director, 3d-artist, technical-artist, asset-critic; texture (library route) and rig/anim skipped per brief — or texture run as a library assignment, as the brief says
2. Phase 1 reads the manifest row, spec block, art bible §8 and §3/§4 by section, reports each present/ABSENT, and runs the tooling check
3. Phase 2: art-director returns the drafts in its reply; the skill shows the brief, asks approve/change/stop, then asks once "May I write `blender/assets/StorageCrate/{asset.json,BRIEF.md,PROGRESS.md}`?"; crops references into `blender/assets/StorageCrate/ref/`; asks before setting the manifest row to `In Progress`
4. Each stage: agent spawned with the asset folder named and the return contract; the skill runs `qa_check.py --stage <stage>` itself and Reads the key sheet; spawns asset-critic with paths only; gate report + `AskUserQuestion`
5. Unity: technical-artist exports and syncs; import report "materials mapped", prefab with LODs; final AD-ASSET on the capture
6. Phase 5: asks before marking the row `Done`; final report lists stages run and skipped by name, AD-ASSET verdicts, tris vs budget, credits (0), Unity paths

**Assertions:**
- [ ] Active-set line appears before the first `Agent` call and names the skipped stages
- [ ] The brief files are written only after one approval naming all three paths
- [ ] Every stage agent's prompt names `blender/assets/StorageCrate/` and ends with the return contract
- [ ] The skill runs the stage check itself (not only quoting the agent's numbers) and reads at least one image per stage
- [ ] Each AD-ASSET prompt contains reference, sheet and asset.json paths and no builder report
- [ ] A gate `AskUserQuestion` ends every stage before the next starts
- [ ] Manifest edits are asked for; final report names every skipped stage

### Case 2: Paid texture route — spend plan, approval per run, also in autonomous mode

**Fixture:**
- `modes.automation: autonomous` (pinned: paid runs must still ask)
- Brief texture route: painted (`/paint-asset` workflow), 5 views; `production/art/weave-budget.json` cap 100, ledger total 12
- texture-artist (spawned without an approval) returns a spend plan: hero view Nano Banana 2.1 3.5 credits; 4 more views 3.5 each

**Input:** `/produce-asset StorageCrate --from texture`

**Expected behavior:**
1. The skill shows the spend plan with the running total (12 of 100)
2. `AskUserQuestion` for the hero run alone; then up to 4 views per call, one question per run, cost in the labels
3. After approval, the agent is resumed with `approved: up to <N> credits for <runs>`; no paid run happens before the user answers
4. Merge: `scripts/materials.sh` is run against `StorageCrate.blend`
5. Other (non-paid) decisions in autonomous mode are logged with `log_decision`, not asked

**Assertions:**
- [ ] No `acknowledgedCost` run and no resume-with-approval happens before the user's explicit Approve for that run
- [ ] `autonomous` does not suppress the spend questions
- [ ] Each question shows the run's cost and the running total
- [ ] A cancelled run is not silently replaced by another provider or model
- [ ] The merge step runs `materials.sh` on the main `.blend`, not on the texture copy

### Case 3: Solo review mode — AD-ASSET only after model and unity

**Fixture:**
- No `modes.review_mode` (resolves `solo` from `rigor: minimal`)
- Brief stages: model, uv, texture (library), unity

**Input:** `/produce-asset StorageCrate`

**Expected behavior:**
1. asset-critic spawned after the model stage and after the Unity import
2. The uv and texture gate reports each say `AD-ASSET skipped — Solo mode (stage uv)` / `(stage texture)`

**Assertions:**
- [ ] Exactly two AD-ASSET spawns
- [ ] Each skipped stage's gate report contains the skip line with the stage name
- [ ] The QA check and image read still run at every stage

### Case 4: AD-ASSET REVISE — one fix round, then the user

**Fixture:**
- `modes.review_mode: lean`; model stage AD-ASSET returns `REVISE` with two findings at confidence 85 and one at 60

**Expected behavior:**
1. The skill sends the ≥ 80 % findings back to 3d-artist for one fix round (or puts them to the user), not the 60 % one as a required fix
2. Re-runs the stage check after the fix; the gate report shows the critic's findings and what changed
3. A `REJECT` instead goes straight to the user with the critic's reasoning

**Assertions:**
- [ ] The stage does not pass its gate on REVISE without either a fix round or an explicit user decision
- [ ] The fix brief carries the critic's findings verbatim (evidence and fix)
- [ ] REJECT is never auto-fixed; it reaches the user

### Case 5: Unity stage cannot run — NOT ASSESSED, never a pass

**Fixture (Variant A):** the Unity editor is closed.
**Fixture (Variant B):** `project.yaml` has no `engine.name`.
**Fixture (Variant C):** `engine.name: Godot`.

**Expected behavior:**
- A: technical-artist copies with `NO_IMPORT=1`; the report says `Unity import: NOT ASSESSED — editor not running (files copied, import pending)`; the manifest row is not marked `Done` as if imported
- B: Blender stages run; the Unity stage reports `NOT ASSESSED — engine not configured (run /setup-engine)`
- C: the Unity stage reports `NOT ASSESSED — this studio supports Unity only`

**Assertions:**
- [ ] No variant reports the Unity stage as passed or the asset as imported
- [ ] Each variant names its reason and the next action
- [ ] The final report lists the Unity stage under NOT ASSESSED

### Case 6: No argument / no spec

**Input A:** `/produce-asset` — **Input B:** `/produce-asset "a mossy stone well"` with no matching spec

**Expected behavior:**
- A: usage guidance printed, no agent spawned, no `AskUserQuestion`
- B: offers `/asset-spec` first (recommended) or a quick inline spec written into `BRIEF.md`, and asks which

**Assertions:**
- [ ] A spawns nothing and asks nothing
- [ ] B does not invent a spec silently; the choice is the user's

### Case 7: sources/ stays append-only during the run

**Fixture:** the reference must be cropped for `ref/`.

**Assertions:**
- [ ] Crops are written under `blender/assets/<Name>/ref/`, never into `sources/`
- [ ] No step edits, moves or deletes a file in `sources/`

---

## Protocol Compliance

- [ ] Orchestrates; brief files and manifest edits are written only after "May I write"
- [ ] Stage writes happen only inside the named asset folders under the bounded art-stage exception
- [ ] Paid generation asks per run in every automation mode
- [ ] AD-ASSET frequency matches the review mode and every skip is announced
- [ ] The critic never receives the builder's report
- [ ] A check or stage that could not run is NOT ASSESSED with its reason, never a pass
- [ ] Unlocking an earlier stage names the stages that must re-run and asks first

---

## Coverage Notes

- Texture ∥ rig parallelism at `team.size: small|studio` (separate `.tex.blend` copy) is not given its own case.
- The quality of the art itself is judged by AD-ASSET and the user, not by this spec.
