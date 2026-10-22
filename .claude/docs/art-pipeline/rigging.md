# Rigging for Unity

Unity gets **deform bones, weights, bone names and baked keys** — no constraints, drivers, B-bones or IK. Rig for the
animator in Blender (control rig), ship a clean game skeleton.

```bash
G=blender/scripts; F=blender/assets/Guard/Guard.blend
ASSET=Guard AUTOEXEC=1 tools/blender_run.sh $G/game_skeleton.py $F -- --src rig --names unity [--bake all] --save
ASSET=Guard tools/blender_run.sh $G/weights.py $F -- bind  --arm GameRig --obj SK_Guard_Body [--scale10] --save
ASSET=Guard tools/blender_run.sh $G/weights.py $F -- clean --arm GameRig --max 4 --min 0.01 --save
ASSET=Guard tools/blender_run.sh $G/weights.py $F -- rigid --arm GameRig --obj SK_Guard_Helmet --bone Head --save
ASSET=Guard tools/blender_run.sh $G/qa_check.py $F -- --stage rig
```

## Pick the skeleton

| Asset | Skeleton | Unity import |
|---|---|---|
| Humanoid (shares/retargets clips, mocap, Mixamo) | Rigify Human → `game_skeleton.py --names unity`; fastest start: a CC0 rigged body from `blender/bases/humanoid/` (its README has the verified sequence) | Humanoid avatar (AssetImportRules: `SK_` → Human, CreateFromThisModel) |
| Creature / quadruped | Rigify animal metarig or a hand-built chain; `--names keep` | Generic: set in AssetImportRules or per model |
| Mechanical (door, turret, vehicle, weapon) | one bone per moving part, `weights.py rigid` per part | Generic; or no bones: animate transforms of separate objects |
| Simple wobble (flag, plant, tentacle) | one chain, auto weights | Generic; or shader wind / vertex animation instead |
| AI character (Tripo `--spec mixamo`) | as delivered | Humanoid (ai-models.md) |

Always: one `root` at the origin (root motion hangs off it), rest pose = the modelling pose (A or T), scale 1.
Rigify rigs: `AUTOEXEC=1` for files you or this studio made (rig_ui.py, drivers).

## Rigify → game skeleton (game_skeleton.py)

Rigify's DEF bones are parented to ORG/MCH helpers, so "deform bones only" export breaks the hierarchy (on a basic
human rig, 11 of 35 DEF bones have no deform parent). The script:
- copies every deform bone into `GameRig`, parent = nearest *deform* ancestor (ORG-x resolved to DEF-x), adds `root`,
  removes B-bone segments (Unity doesn't do B-bones: what Blender shows is now what Unity gets);
- `--names unity` renames for Unity's Humanoid auto-mapper (Hips, Spine, Chest, UpperChest, Neck, Head,
  LeftShoulder, LeftUpperArm, LeftLowerArm, LeftHand, LeftUpperLeg, LeftLowerLeg, LeftFoot, LeftToes; twist
  segments as …Twist) and renames the vertex groups to match;
- retargets the Armature modifiers to GameRig and adds Copy Transforms constraints, so animating the Rigify
  controls still drives the mesh;
- `--bake all` bakes every `ctrl_<Clip>` action into `<Clip>` on GameRig (loops get their wrap frame);
- tags the rig so `export_skinned.py` mutes those constraints. Re-running is safe.
Then `"rig": {"armature": "GameRig", "skeleton": "unity-humanoid"}` in asset.json. Check the mapping in Unity's
Avatar configuration (the import report says "valid humanoid" or not). Rigify basic human has no finger or face
bones: hands deform as one unit — use the full Human metarig if fingers matter.

## Weights

- `bind`: bone heat. Unweighted verts → `--scale10` (fails at human scale with small faces), fix non-manifold/loose
  parts, bind pieces separately — or for AI meshes skin a voxel-remeshed proxy and transfer weights.
- `clean` before export: keeps the strongest `--max` influences (Unity: 4 by default, Quality > Skin Weights; 2/1 on
  low-end mobile), drops weights < `--min`, normalises, removes groups without a deform bone.
- `rigid` for hard parts (helmets, weapons, eyes, plates, mechanical pieces): smooth weights make them bend like rubber.
- Accessories that must not stretch across the body: side-restrict their `.L/.R` groups.

## Sockets, blendshapes

- **Sockets** (hand grip, muzzle, VFX points): a non-deform bone (`socket_Hand_R`) parented to the right bone; Unity
  sees it as a child transform under the model when it is exported — set `use_deform` with no weights if it must
  survive the deform-only export, or put the anchor in the export manifest (`anchors`) for static props.
- **Blendshapes** (faces, correctives): model on the final topology, ARKit names for face capture; FBX exports them;
  Unity imports them on the SkinnedMeshRenderer. Corrective shapes need runtime drivers in Unity — avoid unless planned.

## Pose test (look before the gate)

`renders/<Name>/pose_test.json` with extreme but valid rotations on the control rig's FK bones (or GameRig bones when
there's no control rig), e.g. `{"upper_arm_fk.L": [0, 0, 80], "forearm_fk.L": [110, 0, 0], "thigh_fk.L": [-90, 0, 0],
"shin_fk.L": [110, 0, 0], "spine_fk.001": [25, 0, 0], "head": [0, 0, 45]}` (Rigify arms default to IK: set
`upper_arm_parent.L["IK_FK"] = 1.0` for FK). Find each rig's axes once by rotating one bone and rendering.
```bash
ASSET=Guard tools/blender_run.sh blender/scripts/render_views.py $F -- --tag pose --pose renders/Guard/pose_test.json --rig rig --views front,right,q34
```
Look for candy-wrapper twisting at wrists/forearms, collapsing elbows/knees, armpit and groin stretch, accessories
detaching, eyes lagging. Save at rest pose (QA fails a posed rest).
