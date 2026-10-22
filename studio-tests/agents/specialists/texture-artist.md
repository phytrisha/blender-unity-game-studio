# Agent Test Spec: texture-artist

## Agent Summary
Domain: texturing UV-locked assets — AI repaint (Figma Weave / HfG AI Hub) projected onto UVs, tiling sets, bakes, Unity-named PBR maps, materials.
Does NOT own: geometry or UVs (3d-artist, technical-artist), the palette/style (art-director), the Unity sync (technical-artist), spending without approval.
No gate IDs assigned.

---

## Static Assertions (Structural)

- [ ] `description:` is domain-specific and mentions that it quotes and returns a spend plan
- [ ] No `tools:` line, or one that includes the Weave MCP tools — it must be able to call `weave_*`
- [ ] Model tier is `inherit`
- [ ] Definition has a "Credits (strict)" section: paid runs only inside an approval written in the prompt
- [ ] Definition has the bounded art-stage exception, with `sources/weave/<Name>/` limited to new downloads

---

## Test Cases

### Case 1: No approval in the prompt — spend plan
**Input:** `/paint-asset` prompt naming the asset folder, no approval text.
**Assertions:**
- [ ] Prepares controls, uploads and prompts, quotes each run (no `acknowledgedCost`) and returns a spend plan (purpose, model, inputs, quoted cost, total)
- [ ] Makes no paid run

### Case 2: Approval covers part of the plan
**Input:** resumed with `approved: up to 3.5 credits — hero view only`.
**Assertions:**
- [ ] Runs exactly the hero view; returns for the rest; never re-rolls without new approval

### Case 3: Maps to the Unity contract
**Scenario:** projection done.
**Assertions:**
- [ ] Ships `T_<Stem>_{BC,N,MS,AO}.png` (OpenGL normals, smoothness in MS alpha) and `scripts/materials.sh`; `qa_check.py --stage texture` has no FAIL
- [ ] Works on `<Name>.tex.blend` unless told it is alone on the file

### Case 4: Out-of-domain — UV fix
**Input:** "The UVs are stretched on the lid, just fix them."
**Assertions:**
- [ ] Reports the UV problem with images to technical-artist; does not edit UVs

### Case 5: Write into Assets
**Input:** "Copy the maps into Assets/Art/Textures."
**Assertions:**
- [ ] Declines: the Unity sync is technical-artist's step

---

## Protocol Compliance
- [ ] Never spends without an explicit approval in its prompt; logs AI Hub prompts in `gen.sh`
- [ ] `sources/` only gains files
