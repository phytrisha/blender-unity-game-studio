# Art pipeline reference (Blender → Unity)

How the 3D art department works: the knowledge behind `/produce-asset`, `/art-stage`, `/paint-asset`,
`/texture-set`, `/generate-model` and `/art-review`, and the agents `art-director`, `technical-artist`, `3d-artist`,
`texture-artist`, `rigger`, `animator` and `asset-critic`.

**Read by section, never whole files** (coordination rule 6): find the heading with Grep (`^#`, content mode) and
read that range. Every file is organised so one section answers one question.

| File | Answers |
|---|---|
| `pipeline.md` | stages and gates, the per-asset folder, `asset.json`, budgets, naming, who owns what, parallel work |
| `blender.md` | running Blender (`tools/blender_run.sh`), step vs tool scripts, the kit/export/audit/review libs, review renders and control images, Blender 5.x gotchas |
| `modeling.md` | building game meshes: spec, blockout, part loop, topology for deformation, style recipes, budgets |
| `uv-unwrapping.md` | tiling vs unique UVs, seams, texel density, packing, lightmap UVs, checks |
| `texturing.md` | the Unity map contract, Figma Weave (credit protocol, models, projection painting), AI Hub tiling sets, baking, derived maps, materials |
| `ai-models.md` | Tripo and Hunyuan 3D (via Weave): generation, ingest, when not to use them |
| `rigging.md` | skeletons, Rigify → game skeleton with Unity Humanoid names, weights, sockets, pose tests |
| `animation.md` | clip sets, keying on 5.x slotted actions, loops, root motion, events, contact sheets |
| `unity-pipeline.md` | export → sync → import rules → prefab → animator; running C# in the open editor; placement, scene audits, captures, lighting, performance |
| `unity-project-structure.md` | where everything goes under `Assets/` and how it is named; moving/deleting through Unity only |
| `qa.md` | numeric checks per stage (`qa_check.py`, `audit.py`), the visual review protocol, definitions of done, the gate report |
| `reference.md` | deeper modelling/UV/PBR/prompting reference (numbers, node setups, sources) |

Project docs that grow with the game: `docs/art-pipeline/LESSONS.md` (why the rules exist; add to it when something
costs an hour), `docs/art-pipeline/CHECKLISTS.md`, `docs/perf.md`. Studio-wide art decisions live in the art bible
(`design/art/art-bible.md`, section "Asset Standards" and "3D Production"); per-asset specs in
`design/assets/specs/`; the production list in `design/assets/asset-manifest.md`.
