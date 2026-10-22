# Skill Test Spec: /asset-audit

## Skill Summary

`/asset-audit` audits the Unity asset root, `Assets/` (scripts and `.meta`
files left out), for naming convention compliance, size budgets, format
standards, orphaned assets and missing assets. It reads the art bible or asset
standards from the design docs (Phase 1), resolves the engine and its code root
and scans the asset root with Glob (Phase 2), measures sizes and formats with the
pre-approved read-only commands (`stat`, `file`, `od`, `wc`, `du`), and checks
names against the naming rule the art bible states (§8.2) — with none, files under
`Assets/Art/**` are checked against the art pipeline's naming contract
(`.claude/docs/art-pipeline/pipeline.md` "Naming contract", enforced by
`AssetImportRules.cs`), and the report says which rule was used; other folders
with no bible rule are NOT ASSESSED for naming. Missing assets are found by
searching the **code root** for asset references. Orphaned comes from Unity's
dependency graph: with the editor reachable it runs the pre-approved
`tools/unity_run.sh unity/unused_assets.cs` and lists the unused files as
candidates; with the editor unreachable Orphaned is `NOT ASSESSED — Unity editor
not reachable (unity/unused_assets.cs)`. GDD-level completeness
is `/content-audit`'s job. The report lists violations only, in one table per
category, and names every section it could not assess. A measurement it cannot
take is `NOT ASSESSED`, never an estimate. The skill is read-only: it writes no
files and invokes no director gates.
Verdicts, first match wins: NON-COMPLIANT, WARNINGS, NOT ASSESSED, COMPLIANT —
COMPLIANT only when at least one asset was scanned and every section assessed.

---

## Static Assertions (Structural)

Checked against the SKILL.md by `/skill-test spec` — no fixture needed.

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains verdict keywords: COMPLIANT, WARNINGS, NON-COMPLIANT, NOT ASSESSED
- [ ] Does NOT require "May I write" language (read-only: `allowed-tools` has no Write/Edit and the skill states it does not write files)
- [ ] `allowed-tools` pre-approves exactly one non-measuring command, `tools/unity_run.sh unity/unused_assets.cs` (the orphan report; it writes only `unity/reports/unused_assets.tsv`, outside the project's assets)
- [ ] Has a next-step handoff (what to do after audit results)

---

## Director Gate Checks

None. Asset auditing is a read-only analysis skill; no gates are invoked.

---

## Fixture Defaults

Every case's `project.yaml` sets `modes.rigor: minimal` and
`modes.automation: collaborative`, with no `project.local.yaml`, unless its own
Fixture says otherwise. Rules: `studio-tests/CLAUDE.md` §
Fixture defaults.

---

## Test Cases

### Case 1: Happy Path — Every assessable section is clean

**Fixture:**
- `project.yaml`: `engine.name: Unity`, so the asset and code root is `Assets/`
- `design/art/art-bible.md` Asset Standards: textures PNG, power-of-two, ≤2MB, named
  `T_<Name>_<Map>.png`; SFX OGG, 44.1 kHz, ≤500KB, named `SFX_<Context>_<Name>_<NN>.ogg` (no duration budget)
- `Assets/Art/Characters/Grunt/` contains: `T_Grunt_BC.png`, `T_Grunt_N.png` (512×512 PNG, 300KB each)
- `Assets/Audio/SFX/` contains: `SFX_Player_Jump_01.ogg`, `SFX_Item_Pickup_01.ogg` (OGG, 44.1 kHz, 80KB and under 1 s each)
- Each file has its `.meta` next to it
- The Unity editor is open on the project: `tools/unity_run.sh unity/unused_assets.cs` returns
  `roots 2, used 4, unused 0 files, 0.0 MB` (a scene references every asset)

**Input:** `/asset-audit`

**Expected behavior:**
1. Skill reads the asset standards and naming rule from `design/art/art-bible.md` (Phase 1)
2. Skill resolves the engine to Unity and globs `Assets/**/*`, leaving out `.cs`, `.asmdef` and `.meta` (Phase 2)
3. Every name matches the art bible's rule; every file is within budget and in the expected format; no code reference is missing
4. Orphaned runs through `tools/unity_run.sh unity/unused_assets.cs`; the report quotes its `used`/`unused` line and lists no orphan
5. Summary shows 4 assets scanned and 0 in every violation count, with no section not assessed
6. Verdict is COMPLIANT

**Assertions:**
- [ ] Audit covers both art and audio files under `Assets/`, and `.meta` files are not counted
- [ ] Each file is checked against the art bible's naming rule and size budget, and the report says the bible's rule was used
- [ ] Orphaned comes from `unity/unused_assets.cs`, not from a code search, and its result line is quoted
- [ ] Summary reports `Total assets scanned: 4` with zero naming, size, format, orphaned and missing counts
- [ ] Verdict is COMPLIANT
- [ ] No files are written (the eval script's own report under `unity/reports/` is not a project file the skill writes)

**Variant B — editor not reachable:** same fixture, the Unity editor is closed (`unity_run.sh` fails).
- [ ] Orphaned is `NOT ASSESSED — Unity editor not reachable (unity/unused_assets.cs)`, and no orphan list is inferred from a code search
- [ ] Verdict is NOT ASSESSED, naming Orphaned — not COMPLIANT

---

### Case 2: Non-Compliant — Textures exceed size budget

**Fixture:**
- `project.yaml`: `engine.name: Unity`
- `design/art/art-bible.md` asset standards: textures PNG, power-of-two, ≤2MB, named `T_<Name>_<Map>.png`
- `Assets/Art/Environment/` contains 5 correctly named power-of-two PNG textures
- 3 of them are 4096×4096 at 4MB each; 2 are 1024×1024 at 1MB each

**Input:** `/asset-audit`

**Expected behavior:**
1. Skill reads the 2MB texture budget from the art bible
2. Skill measures each file's size with `stat` or `du` — not by estimate
3. The Size Violations table lists the 3 oversized files with Budget, Actual and Overage
4. The 2 within-budget files do not appear in the Size Violations table; `Total assets scanned` counts all 5
5. Recommendations give each oversized file its own fix, naming the target — a resolution (such as 2048×2048) or a compression setting that brings it under 2MB
6. Verdict is NON-COMPLIANT (a known failure outranks the Orphaned NOT ASSESSED)

**Assertions:**
- [ ] All 3 oversized files appear in the Size Violations table with Budget (2MB), Actual (4MB) and Overage
- [ ] Sizes come from a measuring command (`stat`/`du`), not an estimate
- [ ] Verdict is NON-COMPLIANT when any file exceeds its budget
- [ ] Each oversized file has a recommendation that names its target resolution or compression, not only "reduce size"
- [ ] The 2 within-budget files are counted in `Total assets scanned` but are not listed as violations

---

### Case 3: Format Issue — Music in wrong format

**Fixture:**
- `project.yaml`: `engine.name: Unity`
- `design/art/art-bible.md` asset standards: SFX OGG ≤500KB; music OGG or MP3 ≤8MB; audio named `<Type>_<Context>_<Name>_<NN>`
- `Assets/Audio/Music/MUS_Menu_Theme_01.wav` exists (WAV format, 6MB)
- `Assets/Audio/SFX/SFX_Player_Footstep_01.ogg` exists (OGG format, 40KB)

**Input:** `/asset-audit`

**Expected behavior:**
1. Skill applies the Phase 3 audio format standard (OGG for SFX, OGG/MP3 for music)
2. Skill identifies the WAV file's format with `file` or a header read
3. The Format Violations table lists `MUS_Menu_Theme_01.wav` with expected OGG/MP3 and actual WAV
4. `SFX_Player_Footstep_01.ogg` does not appear in any violation table; both files are within their size budgets
5. Recommendations name the target format for the WAV file (re-export as OGG or MP3)
6. Verdict is WARNINGS (a format issue is correctable)

**Assertions:**
- [ ] `MUS_Menu_Theme_01.wav` appears in the Format Violations table with Expected Format OGG/MP3 and Actual Format WAV
- [ ] The recommendation for the WAV file names OGG or MP3 as its target format
- [ ] Verdict is WARNINGS (not NON-COMPLIANT) for a format issue alone
- [ ] `SFX_Player_Footstep_01.ogg` is not listed in any violation table
- [ ] Skill does not modify or convert any asset files

---

### Case 4: Missing Asset — Referenced by code but absent from Assets/

**Fixture:**
- `project.yaml`: `engine.name: Unity`; `design/art/art-bible.md` sets texture budgets and the `T_<Name>_<Map>.png` rule
- `Assets/Art/Characters/` holds 3 other correctly named textures, within budget
- `Assets/Scripts/Editor/BossSetup.cs` loads `"Assets/Art/Characters/Boss/T_Boss_Idle_BC.png"` through `AssetDatabase.LoadAssetAtPath`
- `Assets/Art/Characters/Boss/` is empty — the file does not exist
- `design/gdd/enemies.md` also names `T_Boss_Roar_BC.png`, which no code references

**Input:** `/asset-audit`

**Expected behavior:**
1. Skill searches code for asset references (Phase 3 "Missing assets") and checks each path exists
2. `T_Boss_Idle_BC.png` is not found
3. The Missing Assets table lists Reference Location `Assets/Scripts/Editor/BossSetup.cs` and the Expected Path
4. The GDD-only name `T_Boss_Roar_BC.png` is not reported — the missing-asset check searches code, not GDDs
5. Verdict is NON-COMPLIANT
6. Next steps point to `/content-audit` for the GDD cross-check

**Assertions:**
- [ ] The Missing Assets table lists `Assets/Scripts/Editor/BossSetup.cs` as the reference location and `Assets/Art/Characters/Boss/T_Boss_Idle_BC.png` as the expected path
- [ ] The GDD-only asset name is not reported as missing
- [ ] Verdict is NON-COMPLIANT when a code-referenced asset is missing
- [ ] Next steps name `/content-audit` for GDD-vs-asset completeness
- [ ] Skill does not create or add placeholder assets

---

### Case 5: No Data — No assets and no asset standards

**Fixture:**
- `project.yaml`: `engine.name: Unity`, `modes.review_mode: full`
- `Assets/` holds only `Scripts/*.cs` files and their `.meta` files — no asset to audit
- `design/art/art-bible.md` does not exist; no design doc defines asset standards

**Input:** `/asset-audit`

**Expected behavior:**
1. Skill runs its insufficient-input check before producing a report: records each input as FOUND or ABSENT
2. Every required input is ABSENT, so the skill stops
3. Verdict is `NOT ASSESSED — NO DATA`, naming what was missing and which skill produces it
4. The skill does not report COMPLIANT and does not render zero-count violation tables as a clean pass
5. No director gate is invoked in any review mode; no file is written and no write is offered

**Assertions:**
- [ ] Inputs are listed as FOUND / ABSENT before any report section
- [ ] Verdict is `NOT ASSESSED — NO DATA`, not COMPLIANT
- [ ] The report names the missing inputs (assets under `Assets/`, asset standards) and the skill that produces the standards (`/art-bible`)
- [ ] No director gate is invoked, even with review mode `full`
- [ ] No "May I write" prompt appears and no file is written

---

### Case 6: Zero Assets — Standards exist, nothing to audit

**Fixture:**
- `project.yaml`: `engine.name: Unity`
- `design/art/art-bible.md` asset standards: textures PNG ≤2MB; SFX OGG ≤500KB
- `Assets/` holds only gameplay scripts (`*.cs`, `*.asmdef`, `.meta`) that load no asset yet

**Input:** `/asset-audit`

**Expected behavior:**
1. The art bible is FOUND, so the insufficient-input check does not stop the run
2. Phase 2 globs `Assets/**/*` without scripts and `.meta` files and matches nothing: `Total assets scanned: 0`
3. Naming, Size, Format and Orphaned are `NOT ASSESSED — no assets under Assets/`, and the Summary lists them; the missing-asset search runs and finds no reference
4. Verdict is NOT ASSESSED — zero violations over zero files is not compliance

**Assertions:**
- [ ] `Total assets scanned` is 0 — scripts and `.meta` files are not counted — and the four file checks are NOT ASSESSED with that reason
- [ ] Verdict is NOT ASSESSED, not COMPLIANT
- [ ] No file is written

---

### Case 7: No Bible Standards — Naming falls back to the pipeline contract under Assets/Art

**Fixture:**
- `project.yaml`: `engine.name: Unity`; the Unity editor is not running
- `design/art/art-bible.md` does not exist; no design doc states asset standards
- `Assets/Art/UI/` holds 3 power-of-two PNGs: `T_UI_Hud_Health_Normal.png`, `T_UI_Hud_Ammo_Normal.png` and `Icon_Health.png`
- `Assets/Audio/SFX/jump.ogg` (OGG, 30KB)

**Input:** `/asset-audit`

**Expected behavior:**
1. Assets are FOUND and standards ABSENT, so the skill runs rather than stopping
2. Naming for `Assets/Art/**` uses the art pipeline naming contract (`.claude/docs/art-pipeline/pipeline.md`), and the report says so: `Icon_Health.png` is a Naming violation (a texture without the `T_` prefix is skipped by the import rules); the two `T_UI_*` files pass
3. Naming for `Assets/Audio/` is `NOT ASSESSED — no naming rule for Assets/Audio/` (the contract covers `Assets/Art/` only); `/art-bible` is named
4. Size is `NOT ASSESSED — no size budget set`; Orphaned is NOT ASSESSED (editor not reachable)
5. Verdict is WARNINGS (a naming finding outranks NOT ASSESSED), and the not-assessed sections are still listed

**Assertions:**
- [ ] The Naming table lists `Icon_Health.png` with the contract's expected pattern, and the report names the pipeline naming contract as the rule used
- [ ] No name outside `Assets/Art/` is judged against an invented pattern (in particular not a lowercase-with-underscores rule)
- [ ] No size is judged against an invented budget; Size is NOT ASSESSED with its reason and `/art-bible` is named
- [ ] Verdict is WARNINGS, and the summary lists Size, Orphaned and the `Assets/Audio/` naming as not assessed

---

### Case 8: Scripts and `.meta` files are not assets

**Fixture:**
- `project.yaml`: `engine.name: Unity`
- `design/art/art-bible.md` asset standards: textures ≤4MB, named `T_<Name>_<Map>.png`
- `Assets/` holds `Art/Characters/Grunt/T_Grunt_BC.png` (2.5MB) and its `.meta`,
  `Scripts/Grunt/GruntController.cs`, `Scripts/Grunt/Grunt.asmdef` and their `.meta` files

**Input:** `/asset-audit`

**Expected behavior:**
1. Phase 2 counts only `T_Grunt_BC.png`: `Total assets scanned: 1`
2. Its size is measured against the 4MB budget; it is under
3. No naming, size or format finding is raised for `.cs`, `.asmdef` or `.meta` files
4. The editor is not running, so Orphaned is NOT ASSESSED; Verdict is NOT ASSESSED, naming Orphaned

**Assertions:**
- [ ] `Total assets scanned` is 1
- [ ] No `.cs`, `.asmdef` or `.meta` file appears in any table
- [ ] Verdict is NOT ASSESSED, never COMPLIANT

---

### Case 9: Engine Unresolved or Unsupported — Stop before scanning

**Fixture:**
- `project.yaml` has no `engine.name`; `.claude/docs/technical-preferences.md` reads `[TO BE CONFIGURED]`
- There is no `Assets/` folder at the repo root, so the tree does not decide the code root
- `design/art/art-bible.md` has asset standards; `art/` holds PNG files

**Input:** `/asset-audit`

**Expected behavior:**
1. Phase 2 cannot resolve the engine or its code root per `.claude/docs/code-root-resolution.md`
2. The skill stops with `NOT ASSESSED — engine unresolved`, naming `/setup-engine`
3. No asset root is guessed and no section is reported clean

**Assertions:**
- [ ] Verdict is `NOT ASSESSED — engine unresolved`, not COMPLIANT
- [ ] Output names `/setup-engine`
- [ ] No violation table is filled from an assumed layout
- [ ] Variant — `engine.name: Godot` (a project configured for another engine): the skill stops as NOT ASSESSED, saying the engine is not supported by this studio, and scans nothing

---

## Protocol Compliance

- [ ] Reads the art bible or asset standards design docs before scanning (Phase 1)
- [ ] Naming uses the bible's rule, else the art pipeline naming contract for `Assets/Art/**`, and says which; any other folder without a bible rule is NOT ASSESSED for naming
- [ ] Orphaned comes only from `unity/unused_assets.cs` with the editor reachable; otherwise NOT ASSESSED with the editor reason — never from a code search
- [ ] Resolves the engine and its code root, then scans `Assets/` with Glob, leaving out scripts and `.meta` files; an unresolved or unsupported engine stops the run as NOT ASSESSED
- [ ] Report uses one table per category: Naming (File, Expected Pattern, Issue), Size (File, Budget, Actual, Overage), Format (File, Expected Format, Actual Format), Orphaned (File, Last Modified, Size, Recommendation), Missing (Reference Location, Expected Path)
- [ ] A size or format it cannot measure is `NOT ASSESSED`, never an estimate, and every section not assessed is named with its reason
- [ ] Each recommendation names the change for its violation (target resolution or compression, corrected name, target format)
- [ ] Does not modify any asset files and writes no report file
- [ ] No director gates are invoked
- [ ] Verdict, first match: NON-COMPLIANT, WARNINGS, NOT ASSESSED, COMPLIANT — COMPLIANT only with at least one asset scanned and every section assessed

---

## Coverage Notes

- The skill does not check import metadata (Unity `.meta` files and importer
  settings); a missing import setting is not reported.
- Orphan detection uses Unity's dependency graph (`unity/unused_assets.cs`, Case 1);
  a code search cannot see scene and prefab references, so without the editor it is
  NOT ASSESSED (Case 1 Variant B). The script's roots are the scenes under
  `Scenes/` and project settings: an asset loaded only by Addressables or Resources
  would appear as a candidate, which is why the list is candidates, never deletions.
- `/asset-audit` checks compliance against code references; `/content-audit`
  checks completeness against the GDDs. Case 4 pins that boundary.
- An audio duration budget is not measurable with the skill's tools, so it makes
  that check NOT ASSESSED; Case 1's fixture sets none, and the path is not given
  its own case.
