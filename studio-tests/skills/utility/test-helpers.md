# Skill Test Spec: /test-helpers

## Skill Summary

`/test-helpers [system-name | all | scaffold]` generates test helper files in
Unity's **helper root** — the only place its test runner compiles them:
`Assets/Tests/EditMode/Helpers/` (inside the `EditModeTests` assembly). An
engine other than Unity is not supported by this studio. It writes base
assertion and factory helpers (`scaffold`), and a
`[helper root]/[System]TestFactory.cs` per system built from that system's GDD
(`[system-name]` or `all`). No argument runs `scaffold` when no helpers exist,
else `all`. It reads `engine.name`, `engine.language` and `testing.framework`
from `project.yaml` (falling back to `technical-preferences.md`), samples up to
5 existing test files for house style, and section-greps the GDD (Formulas,
Edge Cases, Detailed Rules/Design) rather than reading it whole.

Helpers must assert through the configured framework's API — never bare
`assert()` — and must not be test fixtures. If the
framework's assertion API cannot be confirmed, the skill says so and generates
no helper. It never overwrites an existing helper: it skips it with a message.
After presenting the file list it asks "May I write these helper files to
`[helper root]`?". No director gates apply. Verdict: COMPLETE when helper files
are created.

---

## Static Assertions (Structural)

Checked against the SKILL.md by `/skill-test spec` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains verdict keyword: COMPLETE
- [ ] Contains "May I write" collaborative protocol language before writing helpers
- [ ] Has a next-step handoff (Next Steps: `/test-setup`, `/dev-story`, `/skill-test`)

---

## Director Gate Checks

None. `/test-helpers` is a scaffolding utility. No director gates apply.

---

## Fixture Defaults

Every case's `project.yaml` sets `modes.rigor: minimal` and
`modes.automation: collaborative`, with no `project.local.yaml`, unless its own
Fixture says otherwise. Rules: `studio-tests/CLAUDE.md` §
Fixture defaults.

---

## Test Cases

### Case 1: Happy Path — Player helper generated for Unity/C#

**Fixture:**
- `project.yaml` has `engine.name: Unity`, `engine.language: C#`,
  `testing.framework: NUnit`; `com.unity.test-framework` is in
  `Packages/manifest.json`, so NUnit's assertion API can be confirmed from the project
- `Assets/Tests/EditMode/PlayerMovementTests.cs` exists
- `design/gdd/player.md` has a Formulas section bounding health to 0–100
- No existing files in `Assets/Tests/EditMode/Helpers/`; the user approves the write

**Input:** `/test-helpers player`

**Expected behavior:**
1. Skill reads engine, language and framework; samples the existing test file
2. Skill greps `design/gdd/player.md` for the Formulas / Edge Cases / Detailed
   Rules headings instead of reading it whole
3. Skill drafts `Assets/Tests/EditMode/Helpers/PlayerTestFactory.cs`: a plain
   `public static class` with `Make*` factories taking default parameters,
   bound constants commented as coming from the GDD, and a header line
   "Based on: design/gdd/player.md"
4. Every assertion goes through NUnit's `Assert` (directly or via `GameAssertions`)
   — no bare `assert()`, no `FAIL_IF` placeholder
5. Skill presents the file list and asks "May I write these helper files to `Assets/Tests/EditMode/Helpers/`?"
6. Files written on approval; verdict COMPLETE, followed by the per-engine usage note

**Assertions:**
- [ ] Generated helper is C# at `Assets/Tests/EditMode/Helpers/PlayerTestFactory.cs`
- [ ] Bound constants trace to the GDD's Formulas section (not invented values)
- [ ] Helper is a plain static class, not a test fixture (no `[TestFixture]`/`[Test]` markers), and uses no singleton
- [ ] No bare `assert()` and no unresolved `FAIL_IF` reaches the file
- [ ] Verdict is COMPLETE

---

### Case 2: Engine Not Configured — Stops with /setup-engine

**Fixture:**
- `project.yaml` has no `engine` block; `technical-preferences.md` shows
  `[TO BE CONFIGURED]` for Engine

**Input:** `/test-helpers player`

**Expected behavior:**
1. Skill checks `project.yaml`, then `technical-preferences.md` — no engine in either
2. Skill outputs: "Engine not configured. Run `/setup-engine` first."
3. Skill stops — no test scan, no draft, no write

**Assertions:**
- [ ] The message states the engine is not configured
- [ ] `/setup-engine` is named as the prerequisite
- [ ] No write tool is called
- [ ] Verdict is not COMPLETE (nothing was created)

---

### Case 3: Helper Already Exists — Skipped, never overwritten

**Fixture:**
- Unity/C#/NUnit configured as in Case 1
- `Assets/Tests/EditMode/Helpers/GameAssertions.cs` already exists with hand-written additions
- `Assets/Tests/EditMode/Helpers/GameFactory.cs` does not exist; the user approves the write

**Input:** `/test-helpers scaffold`

**Expected behavior:**
1. Skill drafts the Unity base helpers only — `GameAssertions.cs` and
   `GameFactory.cs`; no system-specific helpers in `scaffold` mode
2. Skill asks "May I write these helper files to `Assets/Tests/EditMode/Helpers/`?"
3. The missing file, `Assets/Tests/EditMode/Helpers/GameFactory.cs`, is created
4. For the existing file, skill reports: "Skipping `Assets/Tests/EditMode/Helpers/GameAssertions.cs`
   — already exists. Remove the file manually if you want it regenerated."
5. Verdict COMPLETE

**Assertions:**
- [ ] `scaffold` mode generates no `[System]TestFactory` helper
- [ ] The existing `GameAssertions.cs` is left byte-for-byte unchanged
- [ ] The skip message names the existing file and how to regenerate it
- [ ] Only the missing file is written; Verdict is COMPLETE

---

### Case 4: Framework Assertion API Unconfirmed — No helper generated

**Fixture:**
- `project.yaml` has `engine.name: Unity`, `engine.language: C#`;
  `testing.framework` is absent and `technical-preferences.md` shows no Framework
- `com.unity.test-framework` is not in `Packages/manifest.json` and there are no
  existing test files to learn the API from

**Input:** `/test-helpers scaffold`

**Expected behavior:**
1. Skill cannot confirm which assertion call registers a failure with the runner
2. Skill says so, and generates no helper rather than guessing a form such as
   `Assert.AreEqual`, `Assert.That` or a bare `assert()`
3. No "May I write" is asked and nothing is written

**Assertions:**
- [ ] The skill states it cannot confirm the framework's assertion API
- [ ] No helper file is written
- [ ] No guessed assertion form (and no `FAIL_IF` placeholder) is presented as ready to write
- [ ] Verdict is not COMPLETE

---

### Case 5: Director Gate Check — No gate; test-helpers is a scaffolding utility

**Fixture:**
- Engine and framework configured as in Case 1, no existing helpers

**Input:** `/test-helpers player`

**Expected behavior:**
1. Skill generates and writes the helper file
2. No director agents are spawned
3. No gate IDs appear in output

**Assertions:**
- [ ] No director gate is invoked
- [ ] No gate skip messages appear
- [ ] Verdict is COMPLETE without any gate check

---

### Case 6: Unity — Helpers under the engine's test root

**Fixture:**
- `project.yaml` has `engine.name: Unity`, `engine.language: C#`,
  `testing.framework: NUnit`; `com.unity.test-framework` is in
  `Packages/manifest.json`, so NUnit's assertion API can be confirmed from the
  installed package
- `/test-setup` has created `Assets/Tests/EditMode/EditModeTests.asmdef`
- No helpers exist yet; the user approves the write

**Input:** `/test-helpers scaffold`

**Expected behavior:**
1. The helper root is `Assets/Tests/EditMode/Helpers/` — inside the
   `EditModeTests` assembly, where Unity compiles it
2. Skill drafts `GameAssertions.cs` and `GameFactory.cs` for that folder,
   asserting through NUnit's `Assert`
3. Skill asks "May I write these helper files to `Assets/Tests/EditMode/Helpers/`?"
4. Files written on approval; the usage note says to reference the test assembly;
   verdict COMPLETE

**Assertions:**
- [ ] Helpers are written under `Assets/Tests/EditMode/Helpers/`
- [ ] Nothing is written under `tests/helpers/` — outside `Assets/`, Unity never compiles it
- [ ] The "May I write" ask names the Unity helper root
- [ ] Verdict is COMPLETE

---

## Protocol Compliance

- [ ] Reads engine, language and test framework before generating any helper
- [ ] Writes helpers only to Unity's helper root, `Assets/Tests/EditMode/Helpers/`
- [ ] Section-greps the GDD for system helpers (numbered headings such as `## 4. Formulas` included); constants trace to its Formulas section
- [ ] Asserts only through the configured framework — never bare `assert()` — and generates nothing when that API cannot be confirmed
- [ ] Helpers are never test fixtures (no fixture markers, so the runner does not discover them as empty suites)
- [ ] Never overwrites an existing helper; reports the skip instead
- [ ] Asks "May I write" before any file is created
- [ ] Verdict is COMPLETE when helper files are written

---

## Coverage Notes

- `all` mode (one factory per system with test files) follows Case 1 per system;
  not separately tested.
- A Unity project whose PlayMode tests need the helpers too (the skill asks
  before creating a shared `TestHelpers.asmdef`) is not separately tested.
- An `engine.name` other than Unity (unsupported: nothing generated) is not
  separately tested.
- A requested system with no GDD is not tested; the skill does not define that path.
