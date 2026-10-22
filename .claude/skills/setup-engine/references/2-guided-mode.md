# /setup-engine — Section 2: Guided Mode

> Part of `/setup-engine`. `SKILL.md` names when to read this file; the settings it
> resolved and the rules under its later headings still apply here.

## 2. Guided Mode (No Arguments)

**In this file:**

- Check for existing game concept
- Confirm Unity and collect the project shape

This studio supports one engine: **Unity 6 (C#, URP)**, with Blender as the DCC.
There is no engine choice to make. Guided mode confirms Unity and collects the
project facts later sections need (target platform, 2D-vs-3D, input).

### Check for existing game concept
Read the design artifact for the resolved tier (see **Tier awareness** above), by
section: find the headings you need with the Grep tool (pattern `^#`, content
mode) and Read those ranges with offset and limit:
- **`standard` / `full`**: read `design/gdd/game-concept.md` if it exists —
  extract genre, scope, platform targets, art style, team size, and the engine
  preference `/brainstorm` recorded.
- **`minimal`**: read `design/game-brief.md` if it exists — extract genre,
  scope, platform, and art direction from its fields. Its absence is **expected**
  at `minimal` (the brief is authored *after* engine setup in the minimal path), so
  do not treat a missing brief as a gap — proceed straight to the questions below.
- If no concept **or** brief exists, inform the user:
  > "No game concept found. Consider running `/brainstorm` first to discover what
  > you want to build. Or tell me about your game and I'll set up Unity for it."

  (At `minimal` this is optional, not a prerequisite — you can set up Unity now
  and write the brief next.)

**If the concept or brief records an engine other than Unity**, say so plainly:
this studio is built for Unity only (its agents, rules, scripts and the Blender →
Unity art pipeline assume it). Ask whether to continue with Unity. If the user
declines, stop and report `NOT CONFIGURED — this studio supports Unity only`;
do not write any engine configuration.

### Confirm Unity and collect the project shape

Ask via `AskUserQuestion`, skipping any answer the concept/brief already gives:

**Question 1 — Target platform** (platform decides the build target in
Section 5.5 and the render-pipeline settings later):
- Prompt: "What platforms are you targeting for this game?"
- Options: `PC (Steam / Epic)` / `Mobile (iOS / Android)` / `Console` / `Web / Browser` / `Multiple platforms`

Then, in conversation:
1. **What kind of game?** (2D, 3D, or both?)
2. **Primary input method?** (keyboard/mouse, gamepad, touch, or mixed?)
3. **Team size and experience?** (solo beginner, solo experienced, small team?)

**Honest Unity notes to share where they matter for this concept:**
- Licensing: free under Unity Personal's revenue/install thresholds; the 2023
  runtime-fee controversy (proposed, then withdrawn) is worth knowing about.
- Web: Unity's web build is functional but heavier than native targets — flag it
  if the concept is web-first.
- This studio's defaults (URP, the Blender asset budgets) target stylised to
  mid-fidelity 3D and 2D; say so if the concept is photorealistic AAA-scale 3D.

Then continue to Section 3 with engine = Unity.

---
