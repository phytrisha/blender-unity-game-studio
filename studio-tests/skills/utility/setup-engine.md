# Skill Test Spec: /setup-engine

## Skill Summary

`/setup-engine` pins the project's engine version. This studio supports one
engine, Unity (C#, URP, PhysX), so there is no engine or language choice: it
accepts `unity`, `unity [version]`, `refresh`, `upgrade [old] [new]`, or no
argument for guided version selection. It then:

- writes the Technology Stack and the `ENGINE-REFERENCE-IMPORT` line to
  `CLAUDE.md` after "May I write these engine settings to `CLAUDE.md`?"
- fills `.claude/docs/technical-preferences.md` (the legacy mirror: naming
  conventions, specialist routing table, input/platform, performance budgets)
  after the user approves the presented defaults
- dual-writes the `engine`, `specialists`, `naming` and `commands` blocks to
  `project.yaml` — the primary config store — after "May I write the `engine`,
  `specialists`, `naming`, and `commands` blocks to `project.yaml`?"
- updates or creates `docs/engine-reference/unity/`, never scaffolds a Unity
  project (it tells the user to create it in Unity Hub at the repo root), and
  reads everything back with `project-coherence.sh`

On a re-run it edits existing `project.yaml` blocks in place rather than
duplicating them. No director gates apply. The verdict is COMPLETE when the
engine is configured.

---

## Static Assertions (Structural)

Checked against the SKILL.md by `/skill-test spec` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains verdict keyword: COMPLETE
- [ ] Contains "May I write" language before writing `CLAUDE.md` and before writing the `project.yaml` blocks
- [ ] Has a next-step handoff (Section 12 prints one tier-matched Next-Steps list, e.g. `/brainstorm` at `minimal`)

---

## Director Gate Checks

None. `/setup-engine` is a technical configuration skill. No director gates apply.

---

## Fixture Defaults

Every case's `project.yaml` sets `modes.rigor: minimal` and
`modes.automation: collaborative`, with no `project.local.yaml`, unless its own
Fixture says otherwise. Rules: `studio-tests/CLAUDE.md` §
Fi## Test Cases

### Case 1: Unity + C# — Full engine configuration

**Fixture:**
- `project.yaml` has no `engine` block; `technical-preferences.md` holds only placeholders
- No `design/gdd/game-concept.md` and no `design/game-brief.md`
- `docs/engine-reference/unity/VERSION.md` already pins 6.3 LTS
- The session runs on macOS; the Hub probe finds
  `/Applications/Unity/Hub/Editor/6000.3.26f1/Unity.app/Contents/MacOS/Unity`
- No `Assets/` or `ProjectSettings/` at the repo root; the user approves every
  write and names the build target `StandaloneOSX` when asked

**Input:** `/setup-engine unity 6000.3.26f1`

**Expected behavior:**
1. Full-spec mode: Section 2's guided selection is skipped
2. No engine or language question is asked (Unity is the only engine; the language is C#)
3. Skill shows the Technology Stack and asks "May I write these engine settings to `CLAUDE.md`?"
4. Technical preferences are presented with C# naming (PascalCase classes and
   methods, `_camelCase` private fields) and the routing table:
   `.cs` → unity-specialist, `.shader`/`.shadergraph` → unity-shader-specialist,
   `.unity`/`.prefab` → unity-specialist, `.uxml`/`.uss` → unity-ui-specialist
5. `rendering: URP` and `physics: PhysX` are written directly — no project-shape question
6. `commands.build` target is asked (no hardcoded `StandaloneLinux64`); every
   command that runs the editor starts with the probed editor's quoted full
   path, never bare `Unity`; `naming.constants` carries the `# UNVERIFIED` comment
7. Skill asks "May I write the `engine`, `specialists`, `naming`, and `commands` blocks to `project.yaml`?"
8. Section 6 reads its coverage table: Unity 6 is beyond the Unity row (~2022.3), so
   the knowledge risk is HIGH
9. VERSION.md already pins the 6.3 line → nothing to regenerate; only its
   `Installed at pin time` row is written, from the Section 3 probe
10. No Unity project is scaffolded; the user is told to create it in Unity Hub
    at the repo root; verdict COMPLETE

**Assertions:**
- [ ] `engine.name` is Unity and `engine.language` is C# in `project.yaml`
- [ ] Naming conventions reflect C# conventions
- [ ] Routing table includes `.cs`, `.shader`, `.unity` and `.uxml` entries; `specialists.code` is `unity-specialist`
- [ ] No engine, language or project-shape question is asked
- [ ] No `commands.*` value names bare `Unity`; `engine.path` records the editor executable
- [ ] "May I write" is asked before `CLAUDE.md` and before `project.yaml` are written
- [ ] No Unity project files are written
- [ ] Knowledge Risk is HIGH — the Section 6 table's cutoff is May 2025 and its Unity row ~2022.3, as in the shipped VERSION.md
- [ ] Verdict is COMPLETE

---

### Case 2: No arguments — guided mode goes straight to the version

**Fixture:**
- Placeholders only in `technical-preferences.md`; no `engine` block in `project.yaml`
- The user accepts the version the skill looks up and supplies the build target when asked

**Input:** `/setup-engine`

**Expected behavior:**
1. Guided mode does not offer an engine choice or recommendation between engines
2. The latest Unity 6 LTS is looked up and confirmed with the user before it is pinned
3. The rest of the run matches Case 1 (C# naming, URP/PhysX, build target asked)
4. Verdict COMPLETE

**Assertions:**
- [ ] No engine-selection question or engine comparison is shown
- [ ] The version is confirmed with the user, not picked silently
- [ ] Engine field is set to Unity and Language to C#
- [ ] Verdict is COMPLETE

---

### Case 3: Another engine requested — unsupported, nothing written

**Fixture:**
- Placeholders only; no `engine` block in `project.yaml`

**Input:** `/setup-engine godot 4.7`

**Expected behavior:**
1. The skill says this studio supports Unity only and does not configure Godot
2. It does not silently switch to Unity either: it asks whether to configure Unity instead
3. Nothing is written to `CLAUDE.md`, `project.yaml`, `technical-preferences.md`
   or any VERSION.md before the user answers

**Assertions:**
- [ ] No Godot (or Unreal) values are written anywhere
- [ ] Unity is offered, not assumed
- [ ] No file is written before an answer arrives
- [ ] Verdict is not COMPLETE while the engine is unconfigured

---

### Case 4: Re-run on a Configured Project — blocks edited in place

**Fixture:**
- `project.yaml` already has `engine` (Unity 6000.3.26f1), `specialists`, `naming`, a
  `modes` block, and a `commands` block missing its `smoke` key
- `Assets/`, `Packages/` and `ProjectSettings/` exist at the repo root
- `docs/engine-reference/unity/VERSION.md` pins 6.3 LTS

**Input:** `/setup-engine unity 6000.3.26f1`

**Expected behavior:**
1. Skill reads `project.yaml` before editing it
2. Each existing block is edited in place; `commands.smoke` is added to the
   partial block; no second copy of any block is appended
3. `modes` and every other non-engine block are preserved untouched
4. No file under `Assets/`, `Packages/` or `ProjectSettings/` is written
5. VERSION.md pins the same version → nothing to regenerate: Engine Version,
   Project Pinned and Last Docs Verified are left as they are, and only the
   `Installed at pin time` row is written with the Section 3 probe result
6. Verdict COMPLETE

**Assertions:**
- [ ] No block is duplicated in `project.yaml`, and the missing `commands.smoke` key is added
- [ ] `modes` (and all other non-engine content) is unchanged
- [ ] The Unity project files are not touched
- [ ] For a same-version pin, Engine Version, Project Pinned and Last Docs Verified are untouched and `Installed at pin time` is written
- [ ] Verdict is COMPLETE

---

### Case 5: Director Gate Check — No gate; setup-engine is a utility skill

**Fixture:**
- Fresh project with no engine configured

**Input:** `/setup-engine unity`

**Expected behavior:**
1. Skill completes full engine configuration
2. No director agents are spawned at any point
3. No gate IDs appear in output

**Assertions:**
- [ ] No director gate is invoked
- [ ] No gate skip messages appear
- [ ] Verdict is COMPLETE without any gate check

---

### Case 6: Installed Editor Older Than the Chosen Version — ask, then record

**Fixture:**
- As Case 1; `docs/engine-reference/unity/VERSION.md` pins 6.3 LTS
- The Hub probe finds only `6000.2.6f1`
- The user picks "pin the newer one and upgrade later"

**Input:** `/setup-engine unity 6000.3.26f1`

**Expected behavior:**
1. Section 3 probes the installed editor and finds 6000.2.6f1 — a mismatch
2. Skill states both versions and asks, offering three options: pin the
   installed version, pin the newer one and upgrade later, or pin the newer one
   deliberately
3. The answer is recorded; the skill does not pick for the user
4. VERSION.md already pins the 6.3 line, so nothing is regenerated, but its
   `Installed at pin time` row is written with 6000.2.6f1
5. Verdict COMPLETE

**Assertions:**
- [ ] Both versions are stated and all three options are offered
- [ ] The skill waits for the user's choice rather than picking silently
- [ ] `Installed at pin time` records 6000.2.6f1 — the same-version branch does not skip it
- [ ] Engine Version, Project Pinned and Last Docs Verified are not restamped

---

### Case 7: No Hub editor found — the path is asked for, never bare `Unity`

**Fixture:**
- As Case 1, on Windows; the Hub probe finds no editor under
  `C:/Program Files/Unity/Hub/Editor/`
- `Unity` on `PATH` resolves to Unity's separate CLI, which rejects `-version`
- The user gives `D:/Unity/6000.3.26f1/Editor/Unity.exe` when asked and names the build target `StandaloneWindows64`

**Input:** `/setup-engine unity 6000.3.26f1`

**Expected behavior:**
1. Section 3 reports the installed version as NOT DETERMINED — never "no engine installed" — and asks where the editor is
2. `build`, `test` and `smoke` each start with the quoted full path the user gave, as single-quoted scalars
3. `engine.path` records the executable
4. Verdict COMPLETE

**Assertions:**
- [ ] No `commands.*` value names bare `Unity`
- [ ] Every editor command value is a single-quoted scalar and none holds both quote types
- [ ] `engine.path` records the editor executable
- [ ] Variant — the user does not know where the editor is: the placeholder stays under a `# TODO` comment, and the skill says the commands will not run until the path is set

---

### Case 8: A skipped question is not an answer

**Fixture:**
- Fresh project: no engine configured, no `project.yaml` engine block
- The version confirmation question comes back skipped: the user closes it, or a headless run
  returns every question as skipped
- The sandbox carries the framework's `CLAUDE.md`. The rule this case checks is
  stated there ("A skipped or dismissed question is not an answer") and in
  `.claude/docs/automation-modes.md`, not in `/setup-engine`'s own files; a rule
  `CLAUDE.md` loads counts as the skill's own (`/skill-test` spec mode, Step 3),
  so a sandbox without it is set up wrong, not a skill FAIL

**Input:** `/setup-engine`

**Expected behavior:**
1. The skill does not choose a version itself
2. It asks again in plain text, saying what is waiting on the answer, and waits
3. Nothing is written to `CLAUDE.md`, `project.yaml`, `technical-preferences.md`
   or `VERSION.md` before the user answers
4. In a run where nobody can answer, it stops and reports what is waiting

**Assertions:**
- [ ] No version is picked on the user's behalf
- [ ] The question is asked again in plain text
- [ ] No file is written before an answer arrives

---

 answer arrives

---

## Protocol Compliance

- [ ] Presents draft configuration before asking to write
- [ ] Asks "May I write" before writing `CLAUDE.md` and the `project.yaml` blocks; technical preferences are written only after the user approves the presented defaults
- [ ] Respects engine argument when provided (skips guided selection)
- [ ] Dual-writes `project.yaml` and `technical-preferences.md`, then reads `project.yaml` back to confirm they agree
- [ ] On re-run, edits existing `project.yaml` blocks in place without duplicating them
- [ ] Writes the probed (or user-given) editor path into `commands.*` — never a bare `Unity`, which may resolve to Unity's separate CLI
- [ ] Never defaults the Unity build target — asks for it
- [ ] Writes the Section 3 probe into VERSION.md's `Installed at pin time` row whatever the outcome, after asking "May I record `Installed at pin time: …` in `docs/engine-reference/unity/VERSION.md`?"
- [ ] Verdict is COMPLETE after configuration is written

---

## Coverage Notes

- The `refresh` and `upgrade` subcommands (Sections 10–11) are not tested here.
- Section 6 is a lookup against the skill's own coverage table, asserted in
  Case 1. The Section 7 reference docs for a version with no reference set yet
  depend on WebSearch results; not assertion-tested.
- Linux `commands` (Hub path under `/home/<user>/Unity/Hub/Editor/`) follow
  Case 1; not separately tested.
