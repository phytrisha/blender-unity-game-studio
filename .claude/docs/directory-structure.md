# Directory Structure

The Unity project lives at the repository root: `Assets/`, `Packages/` and
`ProjectSettings/` sit next to the studio's own folders. Unity reads only
`Assets/`, `Packages/` and `ProjectSettings/`; it ignores the rest.

```text
/
├── CLAUDE.md                    # Master configuration
├── project.yaml                 # Machine-readable project config — engine, modes, stage (source of truth)
├── .claude/                     # Agent definitions, skills, hooks, rules, docs
├── Assets/                      # Unity content AND the code root (game code under Assets/Scripts/<System>/)
├── Packages/                    # Unity package manifest
├── ProjectSettings/             # Unity project settings
├── design/                      # Game design documents (gdd, narrative, levels, balance)
├── docs/                        # Technical documentation (architecture, api, postmortems)
│   └── engine-reference/        # Curated engine API snapshots (version-pinned)
├── tests/                       # Test README and smoke-test seed (test CODE lives in Assets/Tests/)
├── tools/                       # Pipeline entry points: blender_run.sh, sync_to_unity.sh, unity_run.sh,
│                                #   tripo_make.sh, sheet.py, texture/ (AI textures, PBR derivation), tests/
├── blender/                     # 3D art source: lib/ (kit, export, audit, review, gamelib), scripts/ (tools),
│   ├── bases/humanoid/          #   CC0 Rigify base bodies (templates: copy, never edit)
│   └── assets/<Name>/           #   one folder per asset: asset.json, BRIEF.md, PROGRESS.md, build.py, <Name>.blend,
│                                #   textures/, ref/, scripts/   (export/ = generated, gitignored)
├── sources/                     # Append-only art inputs: reference/, tripo/<Name>/, weave/<Name>/ (hook-enforced)
├── textures/                    # Shared tiling texture sets for the MI_ material library (gen.sh = prompts)
├── unity/                       # C# eval scripts run in the open editor (never inside Assets/), args/, reports/
├── renders/                     # Review renders, control images, Unity captures (gitignored)
├── prototypes/                  # Throwaway prototypes (outside the code root)
├── production/                  # Production management (sprints, milestones, releases)
│   ├── session-state/           # Ephemeral session state (active.md — gitignored)
│   └── session-logs/            # Session audit trail (gitignored)
└── studio-tests/                # QA for the skills/agents themselves — /skill-test, /skill-improve
```

Unity's generated folders (`Library/`, `Temp/`, `Logs/`, `UserSettings/`,
`obj/`, `Build/`, `Builds/`) also appear at the root and are gitignored.

Inside `Assets/`, first-party content follows `.claude/docs/art-pipeline/unity-project-structure.md`
(`Art/`, `Shaders/`, `Scripts/`, `Scenes/`, `Settings/`, `Tests/`), with paths resolved through
`Assets/Scripts/Editor/ProjectPaths.cs`. Art pipeline layout and contracts: `.claude/docs/art-pipeline/pipeline.md`.

## The code root is `Assets/`

**Unity will not build a project whose code sits in `src/`.** This is not a
style preference — it is a hard constraint of the engine's own toolchain:

| `engine.name` | Code root | Why it cannot be `src/` |
|---|---|---|
| **Unity** | `Assets/` | Unity compiles **only** `Assets/` and `Packages/`. Code outside them is invisible to the compiler. |

**Resolve the code root from `engine.name` before writing any source file.** A
path shown as `src/…` alone is a generic example: read it as *"the code root"*,
`Assets/` (game code under `Assets/Scripts/<System>/`). This studio supports
Unity only; any other `engine.name` leaves the code root unresolved.

**Tests follow the same rule** — the same compiler decides what it sees:

| `engine.name` | Test root | Anywhere else |
|---|---|---|
| **Unity** | `Assets/Tests/EditMode/`, `Assets/Tests/PlayMode/` | not compiled: "0 tests, Passed" |

Read `tests/unit/[system]/` (or `integration/`) anywhere as the test root plus `[System]/`.
