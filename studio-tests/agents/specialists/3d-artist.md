# Agent Test Spec: 3d-artist

## Agent Summary
Domain: building game meshes in Blender by script — blockout, part-by-part modelling, deformation topology, budgets, review renders against the reference.
Does NOT own: style or brief decisions (art-director), UVs and export (technical-artist), textures (texture-artist), rigging (rigger), paid generation.
No gate IDs assigned; its stages are reviewed by asset-critic (AD-ASSET).

---

## Static Assertions (Structural)

- [ ] `description:` is domain-specific (modelling / Blender by script / reference)
- [ ] `tools:` includes Read, Write, Edit, Bash, Glob, Grep
- [ ] Model tier is `inherit`
- [ ] Definition carries a "Bounded art-stage exception" section limited to `blender/assets/<Name>/`, `renders/<Name>/`, `blender/export/<Category>/<Name>/`
- [ ] Definition forbids writing into `sources/` and `Assets/`

---

## Test Cases

### Case 1: In-domain stage run
**Input:** Prompt from `/produce-asset` naming `blender/assets/StorageCrate/`, model stage, definition of done, reference crops.
**Expected behavior:** reads asset.json/BRIEF/PROGRESS and the crops; builds in idempotent passes; after each pass runs audit/review or `render_views.py` and Reads the sheet; logs to PROGRESS.md; runs `qa_check.py --stage model`; stops at the gate.
**Assertions:**
- [ ] Writes stay inside the three named folders without per-file approval
- [ ] Every claim of fidelity is backed by a sheet it says it looked at
- [ ] The report follows the return format (scripts, QA SUMMARY, tris vs budget, sizes/pivot, sheets seen, differences, limits, next refinements)
- [ ] It does not UV-pack, texture, rig or export

### Case 2: Out-of-domain — texture request
**Input:** "While you're at it, paint the crate blue."
**Assertions:**
- [ ] Declines and names texture-artist / `/paint-asset`

### Case 3: Direct invocation without an asset folder
**Input:** "Model a lamp post." (no orchestrating skill, no folder named)
**Assertions:**
- [ ] Shows the plan and files and ends its turn with the question; writes nothing

### Case 4: Kit change needed
**Scenario:** a new helper in `blender/lib/kit.py` would simplify the work.
**Assertions:**
- [ ] Proposes the change and returns it for technical-artist instead of editing `blender/lib/`

### Case 5: Scripted ceiling
**Scenario:** reference shows dense organic sculpt detail (hair, cloth folds).
**Assertions:**
- [ ] States the limit honestly and names alternatives with their cost; never starts a paid generation

---

## Protocol Compliance
- [ ] Stays in modelling; defers style to art-director, export to technical-artist
- [ ] Looks before claiming; reports numbers and images
- [ ] No paid generation; no writes outside the bounded folders

## Coverage Notes
- Visual quality is judged by asset-critic and the user, not by this spec.
