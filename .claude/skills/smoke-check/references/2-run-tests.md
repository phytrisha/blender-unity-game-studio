# /smoke-check — Phase 2: Run Automated Tests

> Part of `/smoke-check`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## Phase 2: Run Automated Tests

**In this file:**

- `commands.test` first
- Unity: Edit Mode, then Play Mode as a second run
- Unknown engine / not configured / not Unity
- Test runner not available here
- Build check (the WAIVED path only)

**Run `commands.test` from `project.yaml` when it is set** — it is the
project's own test command, the one `/setup-engine` wrote and CI runs. Use the
Unity default below only when `commands.test` is absent, and say in the
report which of the two you ran. Wrap it in a timeout (`timeout 900 …`): **a
timeout (exit 124) is a gate FAILURE, never a pass** — the run never completed
and nothing was verified. macOS has no `timeout`: use `gtimeout 900 …` from
Homebrew's `coreutils` (same exit 124), or, with nothing installed,
`perl -e 'alarm shift; exec @ARGV' 900 …`, which exits 142 when time runs out —
a FAILURE the same way. Then read the result. One outcome looks like success
and is not; it is named below.

**Unity:**
Unity **can** run tests headlessly via shell. Do not skip to reading artifacts.

First confirm the Unity Test Framework is installed. A project without it does
not fail cleanly — it **hangs** until something kills it:
```bash
grep -q 'com.unity.test-framework' Packages/manifest.json && echo present || echo ABSENT
```
If ABSENT, report `NOT ASSESSED — Unity Test Framework not installed` and
give the one-line fix (add `com.unity.test-framework` to `Packages/manifest.json`).
**Do not fall through to reading stale artifacts** — an unknown-age XML
reported as a pass is worse than no gate.

If present, the default is (the **editor** executable — `Unity` on `PATH` may be
Unity's separate CLI). Delete the old results file first, whether you run
`commands.test` or this default:
```bash
rm -f test-results/editmode.xml
timeout 900 "<Unity editor>" -batchmode -runTests -projectPath . -testPlatform EditMode -testResults test-results/editmode.xml
```
Exit 0 when every test passes, 2 on a failure. **Exit 1 or 3 is a FAIL**: 1
means the project did not compile (the editor log has the `error CS…` lines),
3 that the run itself failed; 4 (an unknown `-testPlatform`) or any other
non-zero exit is a FAIL too. A compile error writes no results file — which
is why the old one is deleted first: left in place, the last run's pass is read
as this run's. After any exit, no results file is a FAIL. Parse the `<test-run>`
element of the results file for `testcasecount`, `passed` and `failed`. **`testcasecount="0"`
is NOT ASSESSED, never a pass**: tests outside `Assets/` are never compiled, and
Unity then reports `result="Passed"` with exit 0 over zero tests.

**Play Mode is a second run.** `-testPlatform EditMode` — this default, and
`commands.test` as `/setup-engine` writes it — never runs the integration tests
`/test-setup` scaffolds under `Assets/Tests/PlayMode/`. When that folder holds a
test file and the command you ran did not already pass `-testPlatform PlayMode`,
run Play Mode the same way, into its own results file, and read it by the same
rules:
```bash
rm -f test-results/playmode.xml
timeout 900 "<Unity editor>" -batchmode -runTests -projectPath . -testPlatform PlayMode -testResults test-results/playmode.xml
```
Report each platform on its own line — `EditMode: PASS (12/12)`,
`PlayMode: FAIL (1 failure)`. A Play Mode run that could not be made is
reported by name, `PlayMode: NOT RUN — [reason]`: the Edit Mode result does not
cover those tests, so it cannot make the automated-test row a PASS.

**Unknown engine / not configured:**
"Engine not configured in `project.yaml` or
`.claude/docs/technical-preferences.md`. Run `/setup-engine` to configure
Unity, then re-run `/smoke-check`." Verdict: NOT ASSESSED.

**Engine set to anything other than Unity:** report `NOT ASSESSED — engine
'<value>' is not supported by this studio (Unity only)` and run nothing.

**If the test runner is not available in this environment** (no editor
executable resolved in Phase 1 step 3, runner script not found, etc.), report
clearly:

"Automated tests could not be executed — engine executable not found (checked
`commands.test`, `engine.path` and `PATH`; set `engine.path`, or put the
editor's full path in `commands.test`). Status will be recorded as NOT RUN.
Confirm test results from your local IDE
or CI pipeline. Until you do, the verdict is NOT ASSESSED — not FAIL, and not
a pass either: nothing has been observed about this build yet."

Do not treat NOT RUN as an automatic FAIL. Record it, and let the developer's
manual confirmation in Phase 4 resolve it. Until that confirmation arrives the
verdict is **NOT ASSESSED** (see the verdict rules in Phase 5), which ranks
above both pass values and below FAIL. An unrun suite is not a healthy build; it
is an unknown one, and the two need different follow-ups.

Parse runner output and extract:
- Total tests run
- Passing count
- Failing count
- Names of any failing tests (up to 10; if more, note the count)
- Any crash or error output from the runner itself

**Build check — the WAIVED path only** (`qa.level: minimal`, no game tests;
Phase 1 step 1). With no suite to run, run the project's own boot check:
`commands.smoke` when set, else `commands.build` when set, with the executable
Phase 1 step 3 resolved, under the same timeout rules (`timeout 900`, or
`timeout 1800` for `commands.build`; a timeout is a FAIL). Read the result as
`/setup-engine` documents it: Unity `smoke` exits 1 on a compile error; any
other non-zero exit is a FAIL. Record `Build check: PASS — [command] exit 0`,
`FAIL — [reason]`, or `NOT RUN — [commands.smoke and commands.build unset |
executable not found]`. A build check that did not run is named in the report
and leaves the launch in Batch 1 to carry the verdict; it never passes on its
own.

---
