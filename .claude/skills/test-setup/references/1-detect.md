# /test-setup — Phase 1: Detect Engine and Existing State

> Part of `/test-setup`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## Phase 1: Detect Engine and Existing State

1. **Read engine config**:
   - Read `engine.name` from `project.yaml`; if that key is absent or empty
     (including when `project.yaml` has no `engine:` block), fall back to the
     `Engine:` value in `.claude/docs/technical-preferences.md`.
   - If neither source yields a configured engine (project.yaml `engine.name`
     absent/empty and technical-preferences.md shows `[TO BE CONFIGURED]` or is
     missing), stop:
     "Engine not configured. Run `/setup-engine` first, then re-run `/test-setup`."
   - If the engine is anything other than Unity, stop: "Engine '[value]' is not
     supported by this studio (Unity only)." Write nothing.

2. **Check for existing test infrastructure**:
   - Glob `tests/` — does the directory exist?
   - Glob `.github/workflows/` — does a CI workflow file exist?
   - Glob `Assets/Tests/EditMode/` and `Assets/Tests/PlayMode/`. These are the
     **test roots** in `.claude/docs/directory-structure.md`; tests anywhere else
     are never compiled on Unity.

3. **Report findings**:
   - "Engine: [engine]. Test directory: [found / not found]. CI workflow: [found / not found]."
   - If everything already exists AND `force` argument was not passed:
     "Test infrastructure appears to be in place. Re-run with `/test-setup force`
     to regenerate. Proceeding will not overwrite existing test files."

If the `force` argument is passed, skip the "already exists" early-exit and
proceed — but still do not overwrite files that already exist at a given path.
Only create files that are missing.

---
