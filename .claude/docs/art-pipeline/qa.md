# Art QA

Numbers catch what renders can't show; looking catches what numbers can't (clipping, floating parts, proportions,
deformation, style drift). Both are needed at every gate.

## Numeric checks

```bash
ASSET=Crate tools/blender_run.sh blender/scripts/qa_check.py blender/assets/Crate/Crate.blend -- --stage model
ASSET=Crate STAGES=audit tools/blender_run.sh blender/assets/Crate/build.py blender/assets/Crate/Crate.blend   # or stages.py
```
`qa_check.py --stage model|uv|texture|rig|anim|all` (each stage includes the earlier ones) reads the budgets in
`asset.json`, prints `PASS/WARN/FAIL [check] message` and `SUMMARY stage=… fail=… warn=… pass=…`, writes
`renders/<Name>/qa_<stage>.json`, exits 1 on any FAIL.

| Stage | qa_check.py | also |
|---|---|---|
| model | tris per object + total vs budget, n-gons, non-manifold, loose verts/edges, zero-area faces, negative/unapplied scale, live Subdivision, default names, empty slots, material count, height vs `height_m`, ground contact | `audit.py`: floating islands, unsupported member ends, inverted shells, `clashes()` |
| uv | per object tiling (MI_) or unique: tile size / density, overlap, out-of-0–1, **stretch**, utilisation, UV map count | `uv_audit.py` on the FBX (anisotropy > 2.5) |
| texture | files on disk, power of two, ≤ `textures.size`, Unity naming `T_<Stem>_{BC,N,MS,AO,E,H,Mask}`, colour space by suffix | coverage % from `project_paint.py` |
| rig | rest pose, deform bones vs budget, single root, armature scale, unweighted verts, > `influences`, unnormalised weights, stray groups | pose-test sheet |
| anim | clips from asset.json exist, ranges match, loops close (end+1 = start), cyclic flag, fake users | contact sheets; `motion` speed |
| export | — | export round trip (sizes, bones, takes); Unity `import_assets.cs` report |

FAIL blocks the gate. Each WARN gets a sentence in the gate report: fixed, accepted on purpose (mirrored UV overlap,
an n-gon on a flat cap), or a question. A check that could not run (no asset.json, no armature for a rigged brief,
editor closed for the Unity step) is reported as **NOT ASSESSED** with the reason — never as a pass.

## Visual review protocol

1. Render what the stage changed:
   - model: `render_views.py --mode clay` (front, right, back, q34 + the reference's views) and `review_views` look-dev;
   - uv: checker (`texture_tools.py checker` + `build_material.py` on a copy) with `--mode texture`;
   - texture: `--mode texture` and `--mode lit`; the coverage image for painted assets;
   - rig: `--pose renders/<Name>/pose_test.json` front, right, q34;
   - anim: `--action <Clip> --frames ...` contact sheets, side and front;
   - Unity: `unity/capture.cs` shots of the prefab in the sandbox scene.
2. **Read the images** next to the matching reference crop. List concrete differences: proportion, missing
   element, construction, floating/clipping, stretching, seams, colour drift, deformation artefacts.
3. Fix the biggest one, re-render, repeat. Log numbers and what you saw in `PROGRESS.md`.
4. Before the gate: the `asset-critic` agent, briefed with the reference crops, the latest sheets, asset.json and the
   stage — **not** the builder's summary — returns the AD-ASSET verdict (`.claude/docs/director-gates/ad-asset.md`).
   Findings ≥ 80 % confidence are fixed or explained.

## Definition of done per gate

- **Model**: audit 0 floating / 0 inverted / 0 unapplied, clashes reviewed; `qa_check` model clean; renders read from
  all sides; scale and pivot stated; AD-ASSET APPROVE.
- **UV**: no unintended overlap, stretch ≤ 0.25, unique density within 35 % of target, checker read.
- **Texture**: maps present, Unity-named, right colour spaces, base colour without lighting (unless stylised),
  metallic 0/1; coverage ≥ 97 % or gaps explained; lit renders read; spend logged.
- **Rig**: rest pose clean; every vertex weighted; influences ≤ budget; pose test read; avatar valid in Unity.
- **Anim**: every clip in asset.json exists, loops close, speeds measured, events listed, contact sheets read.
- **Export / Unity**: round trip matches the build; `import_assets.cs`: materials mapped, prefab has LODs and
  colliders (LOD1/2 upright, same bounds), avatar valid, animator states; Unity capture read; 0 console errors.

`docs/art-pipeline/CHECKLISTS.md` holds the same as tick lists (asset done, scene change done, before an unattended
run, end-of-session summary).
