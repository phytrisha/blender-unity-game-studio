# /test-setup — Phase 6: Post-Setup Summary

> Part of `/test-setup`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## Phase 6: Post-Setup Summary

After writing all files, report:

```
Test infrastructure created for Unity [version].

Files created:
- tests/README.md
- Assets/Tests/EditMode/ and Assets/Tests/PlayMode/ (with their .asmdef files)
- tests/smoke/critical-paths.md
- production/qa/evidence/.gitkeep
- .github/workflows/tests.yml

Next steps:
1. [Install step if any, e.g., "Add com.unity.test-framework to Packages/manifest.json"]
2. Write your first test in Unity's test root:
   Assets/Tests/EditMode/[System]/[System]Tests.cs
3. Run `/qa-plan sprint` before your first sprint to classify stories and set
   test evidence requirements. At `workflow: minimal` — the default — skip
   this: there are no sprints. At `qa.level: minimal`, also the default, tests
   are waived, so `/dev-story` writes none. Raise `qa.level` with `/settings`
   to have it write them
4. `/smoke-check` before every QA hand-off

Gate note: /gate-check Technical Setup → Pre-Production now requires:
- Unity's test root: Assets/Tests/EditMode/ and Assets/Tests/PlayMode/
- .github/workflows/tests.yml
- At least one example test file
Run /test-setup and write one example test before advancing.
(At `workflow: minimal` that gate requires only the engine.)

Verdict: **COMPLETE** — test framework scaffolded and CI/CD wired up.
```

---
