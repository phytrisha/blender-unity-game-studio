# Modelling game meshes

## Spec first

`/produce-asset` writes the spec into `BRIEF.md` and `asset.json`; the top of `build.py` repeats the numbers as
variables. Ask the user only when something important is ambiguous; otherwise use the art bible and pipeline.md.

| Field | Example |
|---|---|
| Use & camera distance | prop, third person, seen from 2–30 m |
| Real dimensions (m) | 0.6 × 0.6 × 0.6; door 0.9 × 2.1; seat height 0.45; humanoid 1.6–1.9 |
| Budget | LOD0 2k tris, ≤ 2 materials; LOD1 50 %, LOD2 25 % |
| Parts list | panels, battens, brackets, bolts — sizes and positions, how each is built |
| Materials | `MI_WoodPlanks`, `MI_SteelPainted` (library) or `M_<Name>` (unique atlas, painted/baked) |
| Texel density | from the bible (default 512 px/m third person) |
| Pivot / facing | bottom centre at the origin, front −Y (Unity: +Z forward after export) |
| Deliverables | `SM_<Name>.fbx` + LODs + UCX, `.glb`, manifest, review renders, Unity prefab |

## Order of work

1. **Read the reference.** Crop it into views and regions (`ref/`). Write down silhouette, construction, details and
   sizes in metres in `BRIEF.md`'s piece list.
2. **Blockout** (≈ 10 % of the time): one named object per part, real dimensions as variables. Render the clay
   turnaround next to the reference; fix proportions now — everything after inherits them.
3. **Refine one part group per run** (`build.py` stages or `parts/pNN_<group>.py`). Biggest gap first: silhouette →
   proportions → secondary forms → detail. Rewrite a part rather than patch a dead end.
4. **After every major step**: `STAGES=audit` and `STAGES=review` (and `render_views.py` against the crops); fix what
   the audit reports; before/after sheets with `tools/sheet.py`.
5. **Game pass**: budget, merge what can be merged, pivots, names, transforms applied (kit objects already are),
   triangulate concave/non-planar quads, `soft_normals`.
6. **Gate**: `stages.py` audit clean, `qa_check --stage model`, renders read, `asset-critic` → AD-ASSET.

## Game-mesh rules

- **Silhouette first.** Triangles go where they change the outline (rims, profiles, joints); detail that doesn't
  change the silhouette belongs in the normal map or the texture. Faceted low-poly round shapes read badly up close.
- **Real scale; pivot where the game uses it**: base centre (props), between the feet (characters), hinge axis
  (doors, lids), grip (weapons), grid corner (modular pieces).
- **Construction matters as much as silhouette**: "boxes stuck together" is the most common failure. Model shaped,
  integrated forms with detail as relief (`ridge`, `dome`, inset panel lines), not dozens of separate tiny objects.
- **Never coplanar**: a surface on or behind another (glass in a wall, plates on a hull) is offset 2–4 cm;
  `clashes()` finds overlaps.
- **Supports end under what they carry**: check end planes, not just heights (`member_keys` in `audit_asset`).
- **No hidden waste**: delete faces nobody sees unless the object can be picked up or flipped; visible-face-only
  templates for repeated pieces — then check corners where a hidden face becomes visible.
- **Parametric generators** with every clash rule expressed in their parameters beat hand-placed variants; audit each variant.
- **Modular kits**: grid (1/2/4 m), pivots on grid corners, matching open edges, one texel density, shared trim sheet.
- **Separate objects only when the game needs them**: moving parts, swappable parts, materials that can't share.
- **Smoothing**: 60° hard edges + weighted normals (`soft_normals`); author normals in Blender and import them in
  Unity (Unity's "Calculate" shades meshes with per-corner vertex colours flat). Hard edges coincide with UV seams.

## Topology for deformation (anything rigged)

Quads in deforming areas; 3 edge loops around elbows, knees and knuckles, 5+ around shoulders and hips; loops follow
muscle flow around mouth and eyes when there are blendshapes; even density along limbs; no long thin triangles
across joints. Model in A- or T-pose as the rig expects, symmetric about X = 0 (build half, mirror). Knees bound
slightly bent forward (~1 % of height) — a hyperextended bind makes Humanoid retargets cave in.

## Style recipes

| Style | Construction | Settings |
|---|---|---|
| Low-poly / flat | few segments, faceted | flat shading, vertex colours or a palette texture |
| Stylised hand-painted | chunky, exaggerated forms, bevels in geometry | smooth + weighted normals; detail painted in the albedo (`/paint-asset`) |
| Realistic PBR | high-poly (subdivision, sculpt, booleans) baked to a low-poly | low-poly matches the silhouette; N/AO from `bake_maps.py`; library tiling materials or a painted atlas |
| Hard-surface | boxes + bevels + booleans → cleanup | bevel modifier on high, weighted normals on low |

Keep both meshes for baking: `<Name>_high` (any topology, never exported, outside the `SM_` collection) and the game
mesh in `SM_<Name>`.

## bmesh building blocks (beyond the kit)

```python
bmesh.ops.bevel(bm, geom=edges, offset=0.02, segments=2, affect='EDGES', profile=0.5)
bmesh.ops.inset_region(bm, faces=faces, thickness=0.02, depth=-0.01)          # panel lines, recesses
bmesh.ops.extrude_face_region(bm, geom=faces)                                  # then translate the new verts
bmesh.ops.spin(bm, geom=profile, axis=(0, 0, 1), cent=(0, 0, 0), steps=16, angle=math.tau)   # lathe
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True)
bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(5), verts=bm.verts, edges=bm.edges)
mod = o.modifiers.new("cut", 'BOOLEAN'); mod.object = cutter; mod.solver = 'EXACT'
```
Joining two shapes (tunnel into a dome): subdivide around the opening, cut to the real cross-section, trim end
vertices to the wall. Caps on cylinders (logs, barrels) on their own material with disc UVs; lids sit a few cm in.
Fieldstone/brick walls: model the stones, embed their back 2–3 cm in a core, joints ~2 cm.

## Characters: start from a base body

Humanoids start from a rigged CC0 body in `blender/bases/humanoid/` (copy it to `blender/assets/<Name>/<Name>.blend`,
never edit the base): stylised bodies are 25k tris without their Subdivision modifier (delete it for the game mesh),
realistic ones 85k (bake from them or decimate). Build clothing, armour and hair on top, conforming to the body;
change proportions with a shape key, never by editing bones.

## When scripted geometry isn't the right tool

Organic sculpt detail, hair, cloth folds, complex creatures: say so. Options, with their cost: an AI mesh as the
high-poly or blockout (`ai-models.md`), hand sculpting by the user (prepare the `.blend` and the spec), or a
marketplace asset (under `Assets/ThirdParty/<Vendor>/`, never edited). Record the decision in PROGRESS.md.
