# /setup-engine — Section 4: Update CLAUDE.md Technology Stack

> Part of `/setup-engine`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## 4. Update CLAUDE.md Technology Stack

Unity's language is C# — there is no language question.

Read `CLAUDE.md` and show the user the proposed Technology Stack changes.
Ask: "May I write these engine settings to `CLAUDE.md`?"

Wait for confirmation before making any edits.

Update the Technology Stack section, replacing the `[CHOOSE]` placeholders with the actual values:

**Unity:**
```markdown
- **Engine**: Unity [version]
- **Language**: C#
- **Build System**: Unity Build Pipeline
- **Asset Pipeline**: Blender → Unity art pipeline (`.claude/docs/art-pipeline/`, `tools/`, `Packages/com.phytrisha.studio-pipeline/`) + Addressables
```

### Engine reference import

In the same CLAUDE.md write, check the **Engine Version Reference** import — the
`@docs/engine-reference/...VERSION.md` line under the `ENGINE-REFERENCE-IMPORT`
marker comment. It must be `@docs/engine-reference/unity/VERSION.md`. If CLAUDE.md
has no such line, or it points anywhere else, Edit it to that path (it is the only engine reference
this studio ships). Idempotent — re-running `/setup-engine` rewrites the same line.

---
