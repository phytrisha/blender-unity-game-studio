# Skill Test Spec: /test-setup

## Skill Summary

`/test-setup [force]` scaffolds the test framework for the configured engine.
It reads `engine.name` from `project.yaml` (falling back to
`technical-preferences.md`) and stops with a `/setup-engine` redirect when
neither names an engine. It checks for existing infrastructure, presents a plan,
and asks "May I create these files? I will not overwrite any test files that
already exist at these paths." before writing.

It creates `tests/README.md`, `tests/smoke/critical-paths.md`,
`production/qa/evidence/`, `.github/workflows/tests.yml`, and the Unity test
root `Assets/Tests/EditMode/` and `Assets/Tests/PlayMode/` with their `.asmdef`
files. An engine other than Unity is not supported by this studio: the skill
stops and writes nothing. When the
infrastructure already exists it exits early unless `force` is passed, and
`force` only creates missing files — it never overwrites. No director gates
apply. The verdict is COMPLETE when the scaffold is in place.

---

## Static Assertions (Structural)

Checked against the SKILL.md by `/skill-test spec` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains verdict keyword: COMPLETE
- [ ] Contains ask-before-write language before creating files ("May I create these files?")
- [ ] Has a next-step handoff (Phase 6 Next steps: `/qa-plan sprint`, `/smoke-check`)

---

## Director Gate Checks

None. `/test-setup` is a scaffolding utility. No director gates apply.

---

## Fixture Defaults

Every case's `project.yaml` sets `modes.rigor: minimal` and
`modes.automation: collaborative`, with no `project.local.yaml`, unless its own
Fixture says otherwise. Rules: `studio-tests/CLAUDE.md` §
Fixture defaults.

---

## Test Cases

### Case 1: Happy Path — Unity project, scaffolds the Unity Test Runner with asmdefs

**Fixture:**
- `project.yaml` has `engine.name: Unity`
- `Packages/manifest.json` lists `com.unity.test-framework`
- No `Assets/Tests/`, no `tests/`, no CI workflow; the user approves the plan

**Input:** `/test-setup`

**Expected behavior:**
1. Phase 1 reports "Engine: Unity. Test directory: not found. CI workflow: not found."; the Test Framework package check passes
2. The plan places unit and integration tests under `Assets/Tests/` — Unity
   compiles only `Assets/` and `Packages/` — not under `tests/unit/`; `tests/`
   keeps only the README and `smoke/`
3. Skill asks "May I create these files? I will not overwrite any test files that
   already exist at these paths."
4. On approval: `Assets/Tests/EditMode/EditModeTests.asmdef` (Editor-only),
   `Assets/Tests/PlayMode/PlayModeTests.asmdef`, `tests/README.md`,
   `tests/smoke/critical-paths.md`, and a file under `production/qa/evidence/`
5. `.github/workflows/tests.yml` runs `game-ci/unity-test-runner@v4` for
   `editmode` and `playmode`, and the `UNITY_LICENSE` secret is noted
6. The README's Running Unity tests note gives two runs with the editor
   executable — Edit Mode into `test-results/editmode.xml`, Play Mode into
   `test-results/playmode.xml`
7. The Phase 6 gate note names Unity's test root (`Assets/Tests/EditMode/` and
   `Assets/Tests/PlayMode/`), not `tests/unit/` and `tests/integration/`; verdict COMPLETE

**Assertions:**
- [ ] Tests are under `Assets/Tests/`, never `tests/` or a top-level `Tests/` (neither is compiled: 0 tests, "Passed")
- [ ] `.asmdef` files are generated
- [ ] EditMode and PlayMode runner config is present, in CI and as two local runs with separate results files
- [ ] `tests/smoke/` and `production/qa/evidence/` exist afterwards (each holds a written file)
- [ ] Approval is asked before any file is created
- [ ] The gate note names the Unity test root
- [ ] Verdict is COMPLETE

---

### Case 2: Another Engine Configured — unsupported, nothing written

**Fixture:**
- `project.yaml` has `engine.name: Godot` (a project configured for another engine)

**Input:** `/test-setup`

**Expected behavior:**
1. Phase 1 reads the engine and stops: "Engine 'Godot' is not supported by this studio (Unity only)."
2. No plan is presented and no file is written

**Assertions:**
- [ ] No Godot (or any non-Unity) test scaffold is generated
- [ ] The engine is not silently treated as Unity
- [ ] No write tool is called
- [ ] Verdict is not COMPLETE

---

### Case 3: Infrastructure Already Exists — Early exit, nothing re-initialized

**Fixture:**
- Unity project; `Assets/Tests/EditMode/`, `Assets/Tests/PlayMode/` (with test files),
  `tests/README.md` and `.github/workflows/tests.yml` all exist
- No `force` argument

**Input:** `/test-setup`

**Expected behavior:**
1. Phase 1 reports "Engine: Unity. Test directory: found. CI workflow: found."
2. Skill says: "Test infrastructure appears to be in place. Re-run with
   `/test-setup force` to regenerate. Proceeding will not overwrite existing test files."
3. No plan approval is requested and no file is written

**Assertions:**
- [ ] Skill does NOT re-initialize when the infrastructure exists
- [ ] The message points to `/test-setup force`
- [ ] No existing file is modified and no new file is written

---

### Case 4: No Engine Configured — Redirects to /setup-engine

**Fixture:**
- `project.yaml` has no `engine.name`; `technical-preferences.md` shows
  `[TO BE CONFIGURED]` for Engine

**Input:** `/test-setup`

**Expected behavior:**
1. Skill checks `project.yaml`, then `technical-preferences.md` — no engine
2. Skill stops: "Engine not configured. Run `/setup-engine` first, then re-run `/test-setup`."
3. No directories or files are created

**Assertions:**
- [ ] Error message explicitly states engine is not configured
- [ ] `/setup-engine` is suggested as the next step
- [ ] No write tool is called
- [ ] Verdict is not COMPLETE (blocked state)

---

### Case 5: Director Gate Check — No gate; test-setup is a scaffolding utility

**Fixture:**
- Engine configured (Unity), `Assets/Tests/` does not exist

**Input:** `/test-setup`

**Expected behavior:**
1. Skill scaffolds and writes all test framework files
2. No director agents are spawned
3. No gate IDs appear in output

**Assertions:**
- [ ] No director gate is invoked
- [ ] No gate skip messages appear
- [ ] Verdict is COMPLETE without any gate check

---

## Protocol Compliance

- [ ] Reads the engine (`project.yaml`, then `technical-preferences.md`) before generating any scaffold
- [ ] Generates engine-appropriate test runner config and CI workflow (not generic)
- [ ] Puts unit and integration tests in Unity's test root, `Assets/Tests/`
- [ ] Creates `production/qa/evidence/` — the path the Phase 6 summary reports
- [ ] Asks approval before creating files
- [ ] Exits early when infrastructure exists; `force` creates only missing files and never overwrites
- [ ] Verdict is COMPLETE when scaffold is in place

---

## Coverage Notes

- The `force` path on a partial scaffold (create only the missing files) is
  covered by protocol compliance, not by its own case.
- A leftover `tests/unit/` from another engine (never compiled by Unity) is not
  tested.
- A Unity project without `com.unity.test-framework` (the skill asks to add the
  version the installed editor bundles, never a copied number) is not tested.
