# UVs

## Two kinds of UV0, derived from the materials

| | Tiling (library) | Unique (atlas) |
|---|---|---|
| Materials | only `MI_*` (shared, tiling textures) | `M_<Name>` (the asset's own maps) |
| How | the kit maps each part in its local frame in **metres per tile** (`tile=0.5`) | unwrap + pack into 0–1 |
| Past 0–1 / overlap | intended | not allowed (except deliberate mirroring) |
| Density | = texture px ÷ tile size (consistent everywhere by construction) | vs `textures.texel_density` at `textures.size` |
| Used for | hard-surface, buildings, kits, most props | painted (`/paint-asset`), baked, AI-textured assets, characters |

`qa_check.py` and `uv_tools.py check` decide per object from its material names (`asset.json textures.uv_mode`
overrides). A tiling object is judged on stretch only; a unique one on density, overlap, bounds and stretch.

## Tools

```bash
U=blender/scripts/uv_tools.py; F=blender/assets/Guard/Guard.blend
ASSET=Guard tools/blender_run.sh $U $F -- check
ASSET=Guard tools/blender_run.sh $U $F -- unwrap --method angle --angle 60 --obj SK_Guard_Body --save   # hard-surface
ASSET=Guard tools/blender_run.sh $U $F -- unwrap --method smart --obj SK_Guard_Body --save              # quick, more islands
ASSET=Guard tools/blender_run.sh $U $F -- unwrap --method seams --obj SK_Guard_Body --save              # seams you marked
ASSET=Guard tools/blender_run.sh $U $F -- pack --density 1024 --save      # islands to 1024 px/m, packed unscaled
ASSET=Guard tools/blender_run.sh $U $F -- lightmap --save                 # UV1 "UVLightmap"
$BLENDER -b --factory-startup --python blender/scripts/uv_audit.py -- blender/export/Props/Crate/SM_Crate.fbx
```
`check` prints density, utilisation, overlap, out-of-bounds triangles and **stretch** (area-weighted spread of
per-face density: 0 uniform; > 0.25 shows on a checker — typically a closed tube with no seam).
`pack --density` warns when the islands don't fit one map: lower the density, raise the size, or split a material.
`uv_audit.py` measures anisotropy (> 2.5 = distorted) on exported FBX per material.

## Seams

- **Hard-surface**: on hard edges (> ~60°): hard edge ⇒ seam, always. Unroll box UVs around the grain axis with a
  whole number of repeats; per-face projection makes seams at every bevel.
- **Organic**: where nobody looks — inside of arms/legs, under the chin, behind the hairline, torso sides, soles.
  Limbs as tubes, head front/back. Mark by script (`e.seam = True` chosen by position), then `--method seams`.
- **Cylinders**: one straight seam on the least visible side + caps.
- **Slopes**: `v = x + z` style mappings collapse on one side; use arc length across the slope.
- **Noisy/decimated meshes** (AI generated): smart project shatters into tiny islands (10 % use). Unwrap a smoothed
  copy, copy the UVs back, pack with everything selected (44 %).
- Bevelled organic stones: world-space triplanar in the shader instead (tiling ~1.3/m, sharpness 4, whiteout blend).

## Density, mirroring, atlases

- One density per asset and per scene; faces/hands ×1.5–2, undersides ×0.5 on purpose only.
- **Mirrored UVs** halve the cost of symmetric assets; asymmetric detail (logos, scars) can't sit on mirrored areas.
- An atlas = several objects of one asset in one 0–1 space (`pack` packs the listed objects together); one material.
- **Trim sheets** for kits: faces mapped onto horizontal bands of a tiling texture (U tiles past 0–1, V inside the band).
- Margins ≥ 4 px at the final size (8 px for 4K); projection and bakes extend colour 16 px into the gutters.

## Lightmap UVs

`export.py` writes `UVLightmap` (UV1, non-overlapping, smart project) for every static export and Unity's
`generateSecondaryUV` stays off. If Unity ever generates them on these files: `secondaryUVMinObjectScale = 100` or
they collapse (black lightmaps). Lightmap only walk-in/hero pieces; probe-light the rest (unity-pipeline.md).

## Checker review (before the UV gate)

```bash
uv run tools/texture/texture_tools.py checker renders/Guard/checker.png --size 1024 --cells 16
cp blender/assets/Guard/Guard.blend /tmp/Guard.check.blend    # never on the real file
ASSET=Guard tools/blender_run.sh blender/scripts/build_material.py /tmp/Guard.check.blend -- --mat M_Guard --obj SK_Guard_Body --bc renders/Guard/checker.png --save
ASSET=Guard tools/blender_run.sh blender/scripts/render_views.py /tmp/Guard.check.blend -- --tag checker --mode texture --views front,q34,back
```
Read it: stretched or skewed squares, very different square sizes between neighbours, seams in visible places.
