# Humanoid base bodies (rigged, CC0)

Four starting bodies for characters: build on the body, or fit outfits, armour and hair to it. Each file holds:
- `Body` — quad mesh with UVs, A-pose, feet at Z = 0, facing −Y. Armature modifier first, then `Subdivision`.
  Automatic (bone heat) weights; every vertex is weighted.
- `Eye.L`, `Eye.R` — separate eyeballs, rigid on `DEF-spine.006`.
- `rig` — Rigify control rig from a **Basic Human** metarig: spine, neck, head, arms and legs with IK/FK, feet,
  toes. **No finger or face bones** (each hand deforms as one unit). 35 deform bones.
- `metarig` (hidden) — re-fit it and re-generate (Rigify panel) for the full Human metarig with fingers and face.

| File | Height | Body tris (no subdivision) | Subdivision (viewport / render) | Game use |
|---|---|---|---|---|
| `human_female_stylized.blend` | 1.62 m | 25,000 | 1 / 2 (→ 100,000) | game mesh: delete the Subdivision modifier |
| `human_male_stylized.blend` | 1.80 m | 25,000 | 1 / 2 (→ 100,000) | game mesh: delete the Subdivision modifier |
| `human_female_realistic.blend` | 1.64 m | 84,680 | 0 / 1 | over most budgets: high-poly to bake from, or decimate |
| `human_male_realistic.blend` | 1.69 m | 84,680 | 0 / 1 | over most budgets: high-poly to bake from, or decimate |

## Use (the path verified into Unity as a valid Humanoid)

These files are templates: copy one, never edit it in place.
```bash
mkdir -p blender/assets/Hero && cp blender/bases/humanoid/human_male_stylized.blend blender/assets/Hero/Hero.blend
# asset.json: "category": "Characters", "rig": {"armature": "GameRig", "skeleton": "unity-humanoid"}, clips under "animations"
H=blender/assets/Hero/Hero.blend; S=blender/scripts; export ASSET=Hero
# (in a prep script) delete Body's Subdivision modifier and give Body a material with its Principled Base Color set
AUTOEXEC=1 tools/blender_run.sh blender/assets/Hero/scripts/anim_<Clip>.py $H    # ctrl_<Clip> actions on `rig`
AUTOEXEC=1 tools/blender_run.sh $S/game_skeleton.py $H -- --src rig --names unity --bake all --save
tools/blender_run.sh $S/weights.py $H -- clean --arm GameRig --max 4 --save         # bone-heat weights exceed 4 influences
tools/blender_run.sh $S/qa_check.py $H -- --stage rig
tools/blender_run.sh $S/export_skinned.py $H && tools/sync_to_unity.sh Characters Hero
```
Details: `.claude/docs/art-pipeline/rigging.md`, `animation.md`. Body proportions towards a reference: change the
mesh with a shape key, not the bones (editing bones breaks the rig).

## Limits

- Weights are automatic: armpits, groin and shoulders aren't hand-painted; extreme poses show it.
- Joint positions come from measured landmarks (crotch, ankle, neck, fingertips, limb cross-sections): close, not
  anatomical. Check with an x-ray view where a joint matters.
- Rigify's arms default to IK; for FK keys set `rig.pose.bones["upper_arm_parent.L"]["IK_FK"] = 1.0`.

## Source and licence

Meshes: **Blender Studio, "Human Base Meshes" bundle v1.4.1**, **CC0 1.0** (public domain, no attribution
required). Rigs, weights and cleanup by `blender/scripts/make_humanoid_bases.py`; these files are CC0 as well.
Bundle: https://www.blender.org/download/demo-files/ (Asset Bundles → Human Base Meshes).
Regenerate or update: `tools/fetch_humanoid_bases.sh [female_realistic male_realistic female_stylized male_stylized]`
(downloads ~50 MB). Other CC0 options: MakeHuman / MPFB2 (fingers and face rigs), Quaternius "Universal Base
Characters".
