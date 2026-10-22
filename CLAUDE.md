# Blender + Unity Game Studio -- Game Studio Agent Architecture

Indie game development managed through 44 coordinated Claude Code subagents,
built on Claude Code Game Studios (CCGS) and narrowed to one stack: **Unity 6
(URP, C#)** for the game and **Blender** for 3D art, with a 3D art department
that builds assets by script and ships them into Unity.
Each agent owns a specific domain, enforcing separation of concerns and quality.

## Technology Stack

- **Engine**: [CHOOSE: Unity 6 version — /setup-engine probes the installed editor]
- **Language**: C#
- **Rendering / Physics**: URP / PhysX
- **3D content**: Blender 5.x by script (`tools/blender_run.sh`), Figma Weave and the HfG AI Hub for textures,
  Tripo and Hunyuan 3D for generated meshes
- **Version Control**: Git with trunk-based development, Git LFS for binaries (`.gitattributes`)
- **Build System**: [SPECIFY after /setup-engine]
- **Asset Pipeline**: [SPECIFY after /setup-engine]

> The Unity project is the repository root (`Assets/`, `Packages/`, `ProjectSettings/`).
> Engine specialists: `unity-specialist` + shader, UI, DOTS and Addressables sub-specialists.

## Project Structure

@.claude/docs/directory-structure.md

## Engine Version Reference

<!-- ENGINE-REFERENCE-IMPORT: /setup-engine checks the line below and keeps it at
     @docs/engine-reference/unity/VERSION.md, the only engine reference this
     studio ships. Skills that need the pinned version read it on demand too. -->
@docs/engine-reference/unity/VERSION.md


## Technical Preferences

`project.yaml` at the repo root is the primary config store — engine, specialists,
naming, platform, performance, modes. Skills resolve it via `resolve_config`
(see `.claude/docs/config-resolution.md`).

`.claude/docs/technical-preferences.md` is the **legacy fallback**, read on demand
when a key is absent from `project.yaml`. It is not imported here: before
`/setup-engine` runs it is almost entirely `[TO BE CONFIGURED]` placeholders, and
after it runs `project.yaml` holds the real values.

## Coordination Rules

@.claude/docs/coordination-rules.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
  (exempt: `active.md` appends, agent memory, a subagent's new file at the path
  its orchestrating skill named, and the art-stage exception below; see
  `.claude/rules/agent-memory.md`)
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction
- A skipped or dismissed question is not an answer: act on nothing, re-ask in
  plain text and wait
- Started outside this file's folder? Warn first: hooks, deny rules and the
  ask-first mode load only when Claude Code starts here

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow.

## Art Pipeline (Blender → Unity)

The 3D art department — `art-director` (lead), `3d-artist`, `texture-artist`,
`rigger`, `animator`, `technical-artist`, `asset-critic` — builds assets through
`/produce-asset` (spec → brief → model → UV → texture → rig → anim → Unity prefab),
`/art-stage`, `/paint-asset`, `/texture-set`, `/generate-model` and `/art-review`.
Its reference is `.claude/docs/art-pipeline/` (read by section; start with
`README.md` and `pipeline.md`). Four rules carry the most weight:

- **Look before you claim.** Every stage renders and reads its images; numbers
  (`qa_check.py`, `audit.py`) and pictures both, and `asset-critic` reviews each
  stage without seeing the builder's report (gate AD-ASSET).
- **Paid generation always asks.** Figma Weave, the AI Hub and Tripo spend credits:
  quote first, the user approves every run in every automation mode; spend is
  logged (`production/art/weave-ledger.jsonl`, `sources/tripo/LOG.tsv`).
- **`sources/` is append-only** (references and paid generations; hook-enforced).
  **Unity assets move only through Unity** (`AssetDatabase`), never `mv`/`rm`.
- **Bounded art-stage exception.** When `/produce-asset` or `/art-stage` names an
  asset folder in an art agent's prompt, that agent rewrites files inside
  `blender/assets/<Name>/`, `renders/<Name>/` and `blender/export/<Category>/<Name>/`
  without a per-file approval: the user approved the stage, and every stage ends
  at the user's gate. Nothing outside those folders is covered.

## Coding Standards

@.claude/docs/coding-standards.md

## Context Management

Read `.claude/docs/context-management.md` on demand — it is a reference, not
session context. Two of its conventions are load-bearing and cited by name
elsewhere in the repo, so they are restated here rather than lost:

- **`production/session-state/active.md` is the session checkpoint.** The file is
  the memory, not the conversation. Read it first after any compaction, crash, or
  `/clear`. Per-asset state lives in `blender/assets/<Name>/PROGRESS.md`.
- **Helpers in `.claude/scripts/` emit observations, never verdicts.** A script
  that scores or judges will eventually contradict a mode or override it cannot
  see. (Cited by `artifact-check.sh` and `adr-dep-graph.sh`.)
