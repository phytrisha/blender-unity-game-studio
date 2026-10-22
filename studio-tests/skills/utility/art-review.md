# Skill Test Spec: /art-review

## Skill Summary

Runs the AD-ASSET gate on demand for one asset and stage, in every review mode
(an explicit request is not a workflow gate). Phase 1 gathers paths only —
`asset.json`, `BRIEF.md`, reference crops, the newest sheets for the stage —
rendering fresh sheets when the newest is older than the `.blend`, and passing a
missing input as missing; Phase 2 spawns `asset-critic` with the gate file to read
first and those paths, excluding any builder report, the session's own assessment
and PROGRESS.md narrative; Phase 3 relays the verdict and findings unchanged and
then, separately labelled, says which findings the session agrees with after
looking at the evidence. Read-only: no files written (fresh renders go to
`renders/`).

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains verdict keywords APPROVE, REVISE, REJECT, NOT ASSESSED
- [ ] `allowed-tools` has no Write/Edit
- [ ] Outputs usage guidance when no asset is given
- [ ] Has a next-step handoff (`/art-stage`, `/produce-asset`)

---

## Director Gate Checks

- **AD-ASSET** runs in every review mode, including `solo` (explicit request).

---

## Fixture Defaults

As `studio-tests/CLAUDE.md` § Fixture defaults; `blender/assets/Crate/` with brief, `ref/front.png`, and `renders/Crate/look_sheet.png` newer than `Crate.blend`.

---

## Test Cases

### Case 1: Happy path, solo mode
**Input:** `/art-review Crate model`
**Assertions:**
- [ ] asset-critic is spawned although review_mode resolves `solo`
- [ ] The prompt tells it to read `.claude/docs/director-gates/ad-asset.md` first and lists only paths
- [ ] The verdict line and findings are relayed unchanged before the session's own labelled opinion

### Case 2: Stale renders
**Fixture:** `Crate.blend` newer than every sheet
**Assertions:**
- [ ] Fresh sheets are rendered before the critic is spawned

### Case 3: Missing reference
**Fixture:** no `ref/` and no reference in `sources/`
**Assertions:**
- [ ] The missing input is passed as missing; the relayed verdict is `AD-ASSET: NOT ASSESSED` naming it; nothing is substituted

### Case 4: Builder's report available
**Fixture:** PROGRESS.md contains the 3d-artist's self-assessment "matches the reference closely"
**Assertions:**
- [ ] Neither the self-assessment nor any PROGRESS.md narrative appears in the critic's prompt

### Case 5: No asset
**Input:** `/art-review`
**Assertions:**
- [ ] Usage guidance; nothing spawned

---

## Protocol Compliance
- [ ] Read-only; the critic is independent of the builder and of this session's opinion
