# Lessons learned

Distilled from a large Blender → Unity project built with Claude Code (prop, buildings, a town and a city
with terrain, characters, ~1,000 Unity assets, perf passes in player builds). Genre-specific details were dropped;
what stays applies to any asset/scene project. The skills hold the how-to; this file holds the *why*, so read it
before a big job and add to it when something costs you an hour.

## Process
- **Plan → part → code → run → render → critique → refine.** One-shot whole-object scripts compound spatial errors.
  Research systems for LLM-driven modelling (L3GO, LL3M, SceneCraft) converge on the same loop.
- **Numbers before pictures, pictures before "done".** Query dimensions, tri counts and audits after every step;
  then render fixed views. Several bugs were only visible from the back or from a low angle.
- **Everything re-runnable and idempotent.** Terrain rebuilt from a read-only copy; thinning/scatter seeded by a
  hash per world cell; placement from a plan file. Re-running never stacks edits.
- **Post-process steps get undone by rebuilds.** A re-run of the placement script reset LOD groups that a perf
  pass had tuned. Write "re-run X after Y" next to every post-process step and chain them in one script.
- **Plan in Python, apply in Unity.** A planner with real footprint checks (shapely) writes a text placement file;
  a C# script applies it. Easy to diff, review and regenerate.
- **Parallel builders** work: several sessions, each headless Blender on its own .blend, nobody touching Unity, git
  or someone else's files. Disk-heavy jobs (Cycles bakes, ~0.5 GB temp each) must run one at a time — six in
  parallel filled the disk.
- **Unattended runs**: backup first (verified), restore steps at the top of the log, checkpoints after each major
  step, a decisions table, and a fixed end summary. Mark skipped checks honestly — "perf A/B not done" was the most
  common omission.
- **Track paid-API spend per action** (≈ 8 credits per AI Hub image, more for upscales, Tripo per task).

## Verification
- Blender audits that paid off: floating islands, members with an unsupported end, inverted closed shells (signed
  volume), unapplied transforms, z-fighting (coplanar overlap area), UV seams across smooth edges, UV stretch
  (anisotropy > 2.5), slivers (min angle < 2°), clash pairs via BVH from explicit triangle lists.
- Unity audits that paid off: foundation vs ground, object/object penetration, floating/buried props by down-rays,
  pairwise footprint overlap, a player-sized capsule (r 0.33, h 1.8) at every door and every 1 m along every path,
  interior leak test (rays from inside must not see the void), orphan lights (every light near a lamp mesh).
- **Diff scene dumps** (before/after) to find what a script removed; restore at exact transforms.
- **Test the test.** A normal-softness check was wrong because meshes were in centimetres and `normalized` returned
  zero for tiny edges. Run every new check on a case with a known answer.
- **Integration runs find what unit tests miss**: the interaction ray hit the player's own controller capsule.
- Measure feel numerically too: head wobble px/frame, foot slide cm, hip bounce per clip.

## Modelling
- Parametric generators with all clash rules expressed in their parameters beat hand-placed variants. Fork shared
  kit functions rarely; extend them.
- Visible-face-only templates for repeated pieces save many triangles — then check the corners where a hidden face
  becomes visible.
- Wall openings: stacked openings get re-filled by a per-wall core; build the core per column. Gables lose their apex
  when boards run straight between cuts; cut at regular spacing.
- Joining two shapes (tunnel into dome): subdivide around the opening, cut to the real cross-section, trim end
  vertices to the wall.
- Caps on cylinders (logs, barrels) on their own material with disc UVs; lids sit a few cm in.
- Faceted low-poly round shapes read badly up close: spend triangles on the silhouette.
- Fieldstone/brick walls: model the stones and embed only their back 2–3 cm in a core; tight joints (~2 cm).

## UVs and textures
- UVs in metres per tile everywhere → consistent texel density without per-asset tuning.
- Unroll box UVs around the grain axis with a whole number of repeats; per-face projection makes seams at every bevel.
  Bevelled organic stones: world-space triplanar in the shader (tiling ~1.3/m, sharpness 4, whiteout normal blend).
- `v = x + z` style mappings collapse on one side of a slope: use arc length across the slope.
- Normal maps derived from AI colour images came out 2× too strong (35–50° mean tilt); solve per-texture scales to a
  target tilt and keep them in a table file applied by script. Smoothness too: generated wood read as wet (0.85 →
  0.3); keep a per-material table.
- `uv.pack_islands` only packs selected UVs. Smart project on a noisy decimated mesh shatters into tiny islands
  (10 % atlas use): unwrap a smoothed copy, copy UVs back, pack with everything selected (44 %).
- Bake rays: start ~5 mm out, ~2.5 cm reach; longer rays pick up neighbouring geometry.
- AI upscaling: a fidelity-preserving mode kept colour within 1 %; a "creative" mode drifted and was rejected.
  Keep the pre-upscale bake.

## Normals
- Author normals in Blender (60° hard edges + weighted normals), import them in Unity. Unity's "Calculate" gives flat
  shading on meshes with per-corner vertex colours.
- Batch-fixing old FBX files: import → soften → re-export with identical settings, one process per file, then verify
  bounds, polycount, UV sets, colours and materials are unchanged. Keep the .blend as the source of truth: Blender's
  FBX importer crashes on some files.

## Export / import
- The axis trap happened twice: single-mesh FBX carry a rotation + ×100 scale on the root; code that resets the
  root's rotation lays far LODs on their backs. Keep the root rotation; compare LOD bounds.
- Collision: walk-in interiors need many convex hulls (hundreds) so doors and aisles stay open; one hull around a
  porch blocks walking under it. Stairs as ramps.
- Water: a hidden floor collider ~1.1 m below the surface lets the player wade; add a far floor so distant water
  doesn't render lighter.
- Vendor packages: unpack by GUID when their manifest would downgrade a dependency; never edit vendor assets.

## Characters (AI-generated)
- Generated meshes are split at every UV seam: weld before anything else. They are often open/non-manifold, so bone
  heat fails: skin a voxel-remeshed proxy and transfer weights.
- Fused hands/cloaks and finger bundles are common; ask for a clean T-pose and check before paying for rigging.
- Decimation can leave duplicate faces that z-fight: validate.
- Knees: bind slightly bent forward (≈ 1 % of height); a hyperextended bind makes Humanoid retargets cave in.
- A-pose binds need a T-pose avatar reference for retargeting third-party clips. Per-character overrides (arm-down
  limit, feet spacing) in a small JSON next to the model.
- Facing: Unity honours the FBX axis header; check +Z forward in the first import.
- Locomotion: blend thresholds = measured clip ground speeds (no foot slide); IK foot pinning with a knee hint.
- 4K character maps cost ~64 MB VRAM for three maps vs 16 MB at 2K: decide per camera distance.

## Terrain and placement
See the asset-pipeline skill for the numbers. The big ones: rebuild from a read-only copy; paths only lower terrain;
deep cuts → retaining walls or move the building; blend tile seams over a 40 m band with Hermite curves (≤ 2.5 cm
mismatch); re-ground objects after edits; grass fades out near colliders (1.2–2 m) and is thinned by a noise field.

## Lighting and post
- Light instead of filter: raising emissive/lights and halving a grading volume looked better than more grading.
- Local volumes for interior mood (box, 2.5 m blend): exposure −0.35, contrast +8, saturation −8, vignette 0.26,
  grain 0.1, bloom 0.55 above HDR threshold 1.0 were good starting values.
- Fake light shafts: additive ribbon cards with soft edges, falloff, edge-on fade, soft scene intersection, cut by a
  raycast; ~0.5 ms.
- Fog values that look fine in the editor are often too heavy in play (density 0.011 → 0.006). Measure fog from an
  elevated camera too: steep height falloff makes it vanish from above. Put the values in the rebuild script.
- Atmosphere in URP 17: a RenderGraph renderer feature (`AddBlitPass`) for height fog / in-scatter / god rays, with
  Unity's own fog off.

## Performance (player build, GPU-bound scenes)
- The editor was ~2× faster than the build and missed pixel cost. Measure in the build, interleave A/B modes per
  view, take medians; compare only within one run (laptop throttling ±20 %).
- Biggest wins seen: grass/detail instance count (22.7 → 10.9 ms), shadows (distance/cascades/proxies, −1.5 to −22 ms
  depending on scene), terrain layers ≤ 8 per tile, far LODs at fixed budgets, baked occlusion culling (−1 ms avg,
  −4 ms indoors), SSAO off where AO is baked (−3 to −5 ms), LOD bias 2 → 1–1.5.
- Overall: 66 → 43 ms GPU and 1.6 → 1.0 GB build after a structured pass; after that, settings hit a floor and only
  content (HLOD, collider simplification, culling distances) helps.

## Git and structure
- Set up from day one: Force Text, visible meta, `.gitattributes` with unityyamlmerge, binary rules for FBX/PNG/EXR,
  `.asset` without text/eol (TerrainData/LightingData are binary), Git LFS for large binaries. GitHub rejects files
  > 100 MB (a 4K lightmap EXR was 152 MB): cap lightmaps at 2048.
- Group by what assets are, not by when they were made — a reorganisation later took ~1,300 `MoveAsset` calls and
  ~100 script path fixes. `ProjectPaths` from the start avoids that.
- Unused-asset report before deleting; "used" count must not change.
- Commit after each feature; scene + lighting data + occlusion data in the same commit.

## Runtime patterns that stayed useful
- Systems talk through events; data in ScriptableObjects; pure logic in plain C# with EditMode tests.
- One input-lock service for UI panels (movement, look, cursor) and one shared Escape handler.
- Cinemachine brain camera at the scene root, never a child of the moving player (jitter).
- Some input wrappers only update on change: re-read actions every frame after a pause.
- Debug teleports on number keys (ground by ray, off while UI is open, `active` flag for release builds).
- Placeholder sounds and effects generated in code keep systems testable before art exists.
