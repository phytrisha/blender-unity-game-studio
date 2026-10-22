# Skill Test Spec: /texture-set

## Skill Summary

Creates a tileable PBR set for the shared material library (`MI_<Material>`):
Phase 0 resolves `automation`; Phase 1 names the files
(`textures/<Family>/T_<Material>_{BC,N,MS,AO,H}.png`), asks what to do if the set
exists, builds the prompt from the template, the description, a scale cue and the
art bible §8.3 style block (ABSENT is said), and picks a provider (none →
NOT ASSESSED); Phase 2 quotes, asks, and generates (Weave output to
`sources/weave/<Material>/`, AI Hub output and prompt to `textures/<Family>/`);
Phase 3 checks tiling (`texture_tools.py seam`), derives the Unity set
(`derive_pbr_maps.py --unity`, `--make-tileable` only on SEAM, `--delight` unless
painted), reads a 2×2 preview and asks before adding the library material;
Phase 4 optionally creates the Unity material; Phase 5 reports.

---

## Static Assertions (Structural)

- [ ] Has required frontmatter fields: `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`
- [ ] Has ≥2 phase headings
- [ ] Contains NOT ASSESSED (no provider)
- [ ] "May I" before adding the library material
- [ ] Outputs usage guidance when no material name is given
- [ ] Has a next-step handoff

---

## Director Gate Checks

None.

---

## Fixture Defaults

As `studio-tests/CLAUDE.md` § Fixture defaults; Weave tools available; art bible §8.3 has a style block.

---

## Test Cases

### Case 1: Happy path
**Input:** `/texture-set WoodPlanks "weathered pine planks, 15 cm wide, vertical"`
**Assertions:**
- [ ] The prompt shown contains the template's tiling/view words, the description, a scale cue and the bible style block
- [ ] One quote and one approval before generation
- [ ] `seam` runs before derivation; `--make-tileable` used only if it reports SEAM
- [ ] Derived files are `T_WoodPlanks_{BC,N,MS,AO,H}.png`; MS carries smoothness in alpha
- [ ] The tiled preview is read and described before the library material is added, which is asked for

### Case 2: Autonomous mode still asks before generating
**Fixture:** `modes.automation: autonomous` (pinned)
**Assertions:**
- [ ] The generation is approved by the user, not logged-and-run

### Case 3: No style block
**Fixture:** art bible without §8.3
**Assertions:**
- [ ] The report says the style block is ABSENT and that the prompt uses the description only

### Case 4: No provider
**Assertions:**
- [ ] `NOT ASSESSED — no image provider`; nothing generated, nothing written

### Case 5: Existing set
**Fixture:** `textures/Surfaces/T_WoodPlanks_BC.png` exists
**Assertions:**
- [ ] Asks regenerate / derive again / stop; a regeneration writes a new raw file and keeps the old one

### Case 6: Unity editor closed
**Assertions:**
- [ ] Phase 4 reports the Unity material as created on the next import of an asset that uses it — not as created now

---

## Protocol Compliance
- [ ] Paid generation asks per run in every mode; Weave downloads only add files to `sources/`
