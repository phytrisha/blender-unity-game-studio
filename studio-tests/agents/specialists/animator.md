# Agent Test Spec: animator

## Agent Summary
Domain: game animation clips by script — key poses, loops, root motion vs in place, speeds, events, contact sheets, bake to the game skeleton.
Does NOT own: weights/bones/mesh (rigger, 3d-artist), gameplay values the GDD doesn't give (game-designer).
No gate IDs assigned.

---

## Static Assertions (Structural)

- [ ] `description:` is domain-specific (clips / loops / root motion)
- [ ] `tools:` includes Read, Write, Edit, Bash, Glob, Grep
- [ ] Model tier is `inherit`
- [ ] Bounded art-stage exception section present

---

## Test Cases

### Case 1: Locomotion clip
**Input:** anim stage, `Walk` (frames 1–32, loop, in place) from asset.json.
**Assertions:**
- [ ] One idempotent script `scripts/anim_Walk.py` builds `ctrl_Walk`; contact sheets read after each step
- [ ] `loopfix` closes the loop; `motion` reports ~0 m/s (in place); bake writes `Walk`; `qa_check.py --stage anim` no FAIL

### Case 2: Missing gameplay value
**Scenario:** the GDD gives no hit frame for `Attack`.
**Assertions:**
- [ ] Asks through its report (or proposes a value as a proposal); does not set it as fact

### Case 3: Rig problem
**Scenario:** the forearm candy-wraps in every pose.
**Assertions:**
- [ ] Reports to rigger with the sheet; does not change weights

### Case 4: Events
**Scenario:** footsteps needed.
**Assertions:**
- [ ] Adds markers with `events`; lists the event function names gameplay code must implement in its report

### Case 5: Shared file
**Scenario:** rigger is still writing `Guard.blend`.
**Assertions:**
- [ ] Does not write the `.blend` concurrently; says so

---

## Protocol Compliance
- [ ] PascalCase clip names, closed loops, measured speeds; writes only in the bounded folders
