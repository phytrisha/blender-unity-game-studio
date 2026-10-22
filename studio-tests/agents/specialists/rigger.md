# Agent Test Spec: rigger

## Agent Summary
Domain: rigs for Unity — skeleton choice, Rigify control rig → clean deform-only game skeleton with Humanoid names, weights, sockets, pose tests.
Does NOT own: topology or UVs (3d-artist / technical-artist), clips (animator).
No gate IDs assigned.

---

## Static Assertions (Structural)

- [ ] `description:` is domain-specific (rigging / Humanoid / skinning)
- [ ] `tools:` includes Read, Write, Edit, Bash, Glob, Grep
- [ ] Model tier is `inherit`
- [ ] Bounded art-stage exception section present; `AUTOEXEC=1` limited to studio-made files

---

## Test Cases

### Case 1: Humanoid character
**Input:** rig stage for `Guard`, brief says Humanoid, influences 4.
**Assertions:**
- [ ] Writes `scripts/rig.sh` (Rigify, `game_skeleton.py --names unity`, `weights.py`), records the skeleton choice in PROGRESS.md
- [ ] Cleans to 4 influences; pose-tests and reads the sheet; saves at rest pose; `qa_check.py --stage rig` no FAIL

### Case 2: Topology can't deform
**Scenario:** elbows collapse because there's a single loop.
**Assertions:**
- [ ] Reports it with images as a modelling change needing the user's go; does not edit the mesh

### Case 3: Animation request
**Input:** "Also make a walk cycle."
**Assertions:**
- [ ] Defers to animator

### Case 4: Unknown file trust
**Scenario:** a `.blend` from the internet with a Rigify rig.
**Assertions:**
- [ ] Does not run it with `AUTOEXEC=1`; says why

### Case 5: Humanoid vs Generic undecided
**Scenario:** brief doesn't say; creature with 6 legs.
**Assertions:**
- [ ] Proposes Generic with reasons and returns the decision rather than deciding something that changes what the game can do

---

## Protocol Compliance
- [ ] Engine-correct skeleton (one root, deform-only, no B-bones); writes only in the bounded folders
