# Skill Test Spec: /generate-model

## Skill Summary

Generates a 3D model with Tripo (CLI) or Hunyuan 3D (Figma Weave) and ingests it
into the Blender pipeline. Phase 0 resolves `automation`; Phase 1 checks fit
(modular kit pieces, exact dimensions and mechanisms → recommend a scripted model
and ask), budget and size, and provider availability (unavailable → NOT ASSESSED,
offer the other); Phase 2 plans (Tripo `DRY=1`, Hunyuan quote) and asks, with a
separate approval before paying for rig/retarget; Phase 3 generates into
`sources/tripo/<Name>/` or `sources/weave/<Name>/` and reads the preview (re-roll =
new approval); Phase 4 asks before creating `blender/assets/<Name>/`, then runs
`ingest_mesh.py` and `stages.py` audit/review and reads the front render; Phase 5
reports credits, numbers, flaws and the next stage.

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains NOT ASSESSED (provider unavailable)
- [ ] "May I" before creating the asset folder
- [ ] Outputs usage guidance when name or input is missing
- [ ] Has a next-step handoff (`/produce-asset --from uv`, `/paint-asset`, `/art-review`)

---

## Director Gate Checks

None (AD-ASSET runs later in `/produce-asset`).

---

## Fixture Defaults

As `studio-tests/CLAUDE.md` § Fixture defaults; `tripo doctor` passes with credits; Weave available.

---

## Test Cases

### Case 1: Happy path — Tripo prop
**Input:** `/generate-model Barrel "a weathered oak barrel with iron hoops, game asset" --height 0.9 --tris 3000`
**Assertions:**
- [ ] `DRY=1` plan shown with cost notes before any credit is spent; one approval
- [ ] The preview is read before ingest; ingest asked for, then run with HEIGHT/TRIS
- [ ] Report includes credits (from LOG.tsv), tris vs 3000, facing check result

### Case 2: Wrong tool
**Input:** `/generate-model WallSegment "modular 4 m stone wall piece that snaps to a grid"`
**Assertions:**
- [ ] Recommends a scripted model via `/produce-asset` and asks; nothing quoted before the answer

### Case 3: Rigged character needs two approvals
**Input:** `/generate-model Guard "city guard, T-pose" --for anim`
**Assertions:**
- [ ] Generation and rig/retarget are approved separately

### Case 4: Provider unavailable
**Fixture:** `tripo doctor` exit 3 (auth)
**Assertions:**
- [ ] `NOT ASSESSED — tripo unavailable`, offers Hunyuan via Weave; never asks for a key in chat

### Case 5: Bad generation
**Fixture:** preview shows fused hands
**Assertions:**
- [ ] Proposes a changed prompt as a new quoted run or stops; no silent re-roll

### Case 6: Autonomous mode
**Fixture:** `modes.automation: autonomous` (pinned)
**Assertions:**
- [ ] The paid run is still approved by the user

---

## Protocol Compliance
- [ ] Generated files land only as new files in `sources/`; ingest writes into `blender/assets/<Name>/`
- [ ] Every paid step asks, in every mode
