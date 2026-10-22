# Agent Test Spec: technical-artist

## Agent Summary
Domain: Shaders, VFX, rendering optimization, art pipeline tools, and visual performance; the Blender → Unity pipeline (UV stage, LODs, collision, export, import rules, prefabs) and its code (`blender/lib/`, `blender/scripts/`, `tools/`, `unity/`, `Assets/Scripts/Editor/`).
Does NOT own: art style decisions or color palette (art-director), gameplay code (gameplay-programmer).
No gate IDs assigned.

---

## Static Assertions (Structural)

- [ ] `description:` field is present and domain-specific (references shaders / VFX / rendering)
- [ ] `tools:` list includes Read, Write, Edit, Bash, Glob, Grep
- [ ] Model tier is `inherit` — frontmatter `model:` reads exactly `inherit` (tiers: `.claude/docs/model-tiers.md`)
- [ ] Agent definition does not claim authority over art style direction or gameplay logic
- [ ] Definition carries the bounded art-stage exception, and writes into `Assets/` only via `tools/sync_to_unity.sh` at the approved export stage

---

## Test Cases

### Case 1: In-domain request — appropriate output
**Input:** "Create a dissolve effect shader for enemy death sequences."
**Expected behavior:**
- Proposes the approach (shader structure, exposed parameters) before implementing, and asks "May I write this to [filepath]?" before writing
- Produces a URP Shader Graph node spec (or HLSL shader code) for the project's Unity version
- Exposes the dissolve driver as a documented shader parameter (e.g., a `_DissolveAmount` property, 0.0–1.0, thresholding a noise texture) and documents each parameter's visual effect
- States the effect's performance budget (e.g., texture samples, shader instruction count)
- Leaves the look of the effect (edge color, glow) to art-director rather than deciding it
- Output is engine-version-aware (checks version reference if post-cutoff APIs are needed)

### Case 2: Out-of-domain request — redirects correctly
**Input:** "Define the art bible color palette: primary, secondary, and accent colors for the UI."
**Expected behavior:**
- Does NOT produce color palette decisions or art direction documents
- Explicitly states that art style decisions belong to `art-director`
- Redirects the request to `art-director`
- Any follow-up it offers is implementation on its side — e.g., a color-grading or palette LUT shader once art-director has decided the palette — with no palette values chosen by it

### Case 3: Performance warning — GPU particle count
**Input:** "The VFX system is triggering a GPU particle count warning at 50,000 particles in the explosion pool."
**Expected behavior:**
- Produces an optimization spec addressing the specific warning
- Proposes concrete strategies: particle budget caps per emitter, LOD-based particle reduction, GPU instancing, or switching to mesh-based VFX for distant effects
- Sets an explicit particle-count budget for the explosion effect and states the visual-quality cost of each strategy (e.g., as documented quality tiers)
- Flags any visible change to the explosion's look for art-director rather than deciding it
- Does NOT change gameplay behavior of the explosion (delegates any gameplay impact to gameplay-programmer)

### Case 4: Engine version compatibility
**Input:** "Use the new texture sampler API for the water shader."
**Expected behavior:**
- Checks the engine version reference (`docs/engine-reference/unity/VERSION.md`) before suggesting any API
- Flags if the requested API is post-cutoff (anything Unity 6 changed after the 2022 LTS the model knows)
- Provides the correct syntax for the project's pinned engine version
- If uncertain about post-cutoff behavior, explicitly states the uncertainty and directs to verified docs

### Case 5: Context pass — uses performance budget
**Input:** Performance budget provided in context: 2ms GPU budget for the forest, max 200 draw calls per frame. Request: "Optimize the forest rendering system."
**Expected behavior:**
- Treats the 2ms GPU budget and 200 draw call limit from the provided context as the budgets it enforces — no other numbers substituted
- Proposes rendering optimizations (LOD, occlusion, batching, atlasing), each tied to the budget it targets (e.g., "batching reduces draw calls from 340 to ~180, within the 200 limit")
- Calls out any optimization that helps one budget at the other's expense (e.g., merged meshes cut draw calls but can defeat occlusion and raise GPU time past 2ms) instead of presenting it as a free win
- Proposes the approach before implementing and asks before writing files

---

### Case 6: Unity stage with the editor closed
**Input:** export stage for `StorageCrate` named by `/produce-asset`; the Unity editor is not running.
**Expected behavior:**
- Exports (`stages.py`), runs `NO_IMPORT=1 tools/sync_to_unity.sh Props StorageCrate`, and reports "Unity import: NOT ASSESSED — editor not running (files copied, import pending)"
**Assertions:**
- [ ] Never reports materials mapped, prefab built or avatar valid without an `import_assets.cs` report
- [ ] Quotes import results verbatim when the editor is open (materials mapped / UNMAPPED, avatar, LOD counts)

### Case 7: UV stage — tiling vs unique
**Input:** UV stage for an asset with `MI_` library materials on the walls and an `M_Shed_Sign` unique decal.
**Assertions:**
- [ ] Judges the walls on stretch only (tiling) and the sign on density/overlap/bounds (unique), per `uv-unwrapping.md`
- [ ] Renders and reads a checker on a copy before the gate; writes the steps to `scripts/uv.sh`

### Case 8: Shared pipeline change
**Input:** "Change AssetImportRules so SK_ files import as Generic."
**Assertions:**
- [ ] Proposes the change and asks before editing `Assets/Scripts/Editor/` (the exception does not cover shared pipeline code)

## Protocol Compliance

- [ ] Stays within declared domain (shaders, VFX, rendering optimization, art pipeline)
- [ ] Redirects art style decisions to art-director
- [ ] Returns structured findings (shader code, optimization specs with metrics, node graphs)
- [ ] Does not modify gameplay code files without explicit delegation
- [ ] Checks engine version reference before suggesting post-cutoff APIs
- [ ] Ties each proposed optimization to the per-category budget it serves (draw calls, particle count, shader instructions, texture memory, overdraw)

---

## Coverage Notes
- Dissolve shader (Case 1) should include a visual test reference in `production/qa/evidence/`
- Engine version check (Case 4) confirms the agent treats VERSION.md as authoritative
- Performance budget case (Case 5) verifies the agent reads and applies provided context numbers
