# Skill Test Spec: /paint-asset

## Skill Summary

AI-paints a UV-locked asset: Phase 0 resolves `review_mode` and `automation`;
Phase 1 checks preconditions (brief, art bible §4/§8.3 present or ABSENT, unique
UVs via `uv_tools.py check` — objects whose materials are all `MI_*` are tiling
and refused, unique UVs with overlap > 2 % or stretch > 0.25 stop the run — a
provider available, the Weave budget cap and ledger total stated); Phase 2
renders clay + depth control images and has `texture-artist` (spawned without an
approval) upload, write prompts and return a quoted spend plan; Phase 3 asks per
run (hero view first, then up to 4 views per call), resumes the agent with the
approval, reads the hero result before approving the rest, projects with
`project_paint.py`, reads the coverage image and asks how to fill gaps > 3 %,
derives maps and runs `materials.sh`; Phase 4 runs `qa_check.py --stage texture`,
reads the texture/lit renders, runs AD-ASSET per review mode and ends at a gate.
Every paid run asks in every automation mode. Downloads land in
`sources/weave/<Name>/` (append-only); derived files go to the asset folder.

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains NOT ASSESSED (no image provider)
- [ ] Outputs usage guidance when no asset is given
- [ ] States that every paid run asks the user in every automation mode
- [ ] Points to `texturing.md` sections by name instead of restating the workflow
- [ ] Has a next-step handoff (`/produce-asset`/`/art-stage`, `/texture-set`, `/art-review`)

---

## Director Gate Checks

- **AD-ASSET** for the texture stage: `full`/`lean` → runs; `solo` → `AD-ASSET skipped — Solo mode (stage texture)`.

---

## Fixture Defaults

As `studio-tests/CLAUDE.md` § Fixture defaults. Unless a case says otherwise:
`blender/assets/Crate/` with brief and `M_Crate` unique UVs (overlap 0 %, stretch
0.03); Weave MCP tools available; `production/art/weave-budget.json` cap 100,
ledger total 0; art bible §4 and §8.3 present.

---

## Test Cases

### Case 1: Happy path — hero view first
**Input:** `/paint-asset Crate "weathered blue paint, rusty corners"`
**Expected behavior:**
1. Preconditions reported (bible sections present, UV check passed, provider, budget 0 / 100)
2. Control renders; texture-artist returns the spend plan (hero 3.5, four views 3.5 each)
3. `AskUserQuestion` for the hero run only; first quote carries the cost disclosure sentence
4. Hero result read before the remaining runs are offered; then one call with 4 view questions
5. Projection coverage reported; maps derived; `materials.sh` written and run; QA texture clean; renders read; gate
**Assertions:**
- [ ] The hero run is approved and inspected before any other view is approved
- [ ] Each question shows its cost and the running total
- [ ] The agent receives `approved: ...` only for runs the user approved
- [ ] Coverage %, credits spent and the renders looked at appear in the report

### Case 2: Autonomous mode still asks for every paid run
**Fixture:** `modes.automation: autonomous` (pinned)
**Assertions:**
- [ ] Every paid run has an `AskUserQuestion` approval; none is logged-and-run via `log_decision`

### Case 3: Tiling object refused
**Fixture:** `SM_Shed_Walls` uses only `MI_Brick` (tiling UVs)
**Input:** `/paint-asset Shed`
**Assertions:**
- [ ] The run stops before any render or quote, naming the tiling object and pointing to `/texture-set`

### Case 4: Unusable unique UVs
**Fixture:** `M_Crate` UVs stretch 1.4
**Assertions:**
- [ ] Stops and recommends `/art-stage uv Crate`; nothing is quoted

### Case 5: No provider
**Fixture:** Weave tools unavailable and no `AIHUB_API_KEY`
**Assertions:**
- [ ] Verdict `NOT ASSESSED — no image provider`; nothing rendered for nothing

### Case 6: Hero result rejected
**Fixture:** the hero repaint moved the silhouette
**Assertions:**
- [ ] The skill says what is wrong and proposes a changed prompt as a new quoted run; no silent retry, no approval reused

### Case 7: Coverage gaps
**Fixture:** projection coverage 88 % (bottom unseen)
**Assertions:**
- [ ] `AskUserQuestion` offers an extra view (quoted), inpainting (quoted) or the fill colour (free, recorded in BRIEF.md)
- [ ] Downloads stay in `sources/weave/Crate/`; the gap-filled texture is a new file in the asset folder, never an edit in `sources/`

---

## Protocol Compliance

- [ ] Paid runs: quote → per-run approval → run, in every automation mode
- [ ] `sources/` only gains new files
- [ ] A check that could not run is NOT ASSESSED, never a pass

## Coverage Notes
- AI Hub as provider follows the same gates; not given its own case.
