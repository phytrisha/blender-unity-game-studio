# Animation for Unity

```bash
A=blender/scripts/anim_tools.py; F=blender/assets/Guard/Guard.blend
ASSET=Guard tools/blender_run.sh $A $F -- list
ASSET=Guard tools/blender_run.sh $A $F -- loopfix --action ctrl_Walk --frames 1,32 --save
ASSET=Guard tools/blender_run.sh $A $F -- motion  --action Walk --bone Hips          # travel + speed (m/s)
ASSET=Guard tools/blender_run.sh $A $F -- inplace --action ctrl_Walk --bone torso --save
ASSET=Guard tools/blender_run.sh $A $F -- events  --action Attack --set Windup:4,Hit:11,Recover:18 --save
ASSET=Guard tools/blender_run.sh blender/scripts/render_views.py $F -- --tag walk --action ctrl_Walk --rig rig --views right,front --frames 1,5,9,13,17,21,25,29
```

## Conventions

- Author on the **control rig**, actions `ctrl_<Clip>`; `game_skeleton.py --bake all` writes `<Clip>` on GameRig.
  Simple rigs without a control layer: author `<Clip>` directly. Export skips `ctrl_*` and `__*`.
- Clip names in PascalCase (`Idle`, `Walk`, `Run`, `Attack`): they become Unity clip and animator state names, and
  the importer's fallback loops `Idle*/Walk*/Run*` when no manifest exists.
- One action per clip, fake user on (QA warns otherwise: unused actions vanish on save).
- **Frame rate** 30 fps unless the art bible says otherwise; constant across the project.
- **Loops**: exported range `start..end`; frame `end+1` repeats the start pose (`loopfix`); `use_cyclic` on. Unity's
  Loop Time then blends end → start without a hitch or a doubled frame.
- List every clip in asset.json `animations`: `{name, frames, loop, root_motion}`. `export_skinned.py` writes them to
  `SK_<Name>.json`; `AssetImportRules` sets Loop Time, root-motion locks and AnimationEvents from it.
- **Events**: pose markers (`events`) → AnimationEvents with the marker name as the function name. The gameplay code
  (gameplay-programmer) implements receivers with those names; list them in the export report.

## Clip sets (starting points)

| Asset | Clips |
|---|---|
| Humanoid player | Idle, Walk, Run, Sprint, JumpStart/JumpLoop/Land, CrouchIdle/CrouchWalk, Attack1–3, HitReact, Death, Interact |
| NPC / enemy | Idle, Walk, Run, Attack, HitReact, Death, Alert |
| Creature | Idle, Walk, Run, Bite/Claw, Roar, Hit, Death |
| Prop / mechanical | Open, Close, Idle (loop), Activate, Destroyed |
| First-person weapon | Idle, Fire, Reload, Equip, Unequip, Inspect |

Humanoid clips can also come from Mixamo/Tripo presets and retarget onto the Humanoid avatar in Unity.

## Keying by script (Blender 5.x)

```python
import bpy, math, os, sys
sys.path.insert(0, os.environ["BLENDER_LIB"]); import gamelib as g
rig = bpy.data.objects["rig"]
act = bpy.data.actions.get("ctrl_Idle") or bpy.data.actions.new("ctrl_Idle")
ad = rig.animation_data_create(); ad.action = act                  # slot created on the first key
def key(bone, frame, rot=None, loc=None):
    pb = rig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
    if rot is not None: pb.rotation_euler = [math.radians(r) for r in rot]; pb.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None: pb.location = loc; pb.keyframe_insert("location", frame=frame)
for f, s in ((1, 0), (31, 1), (61, 0)):                             # breathing over 2 s at 30 fps
    key("chest", f, rot=(2 * s, 0, 0)); key("torso", f, loc=(0, 0, -0.005 * s))
act.use_frame_range = True; act.frame_start, act.frame_end = 1, 60; act.use_cyclic = True; act.use_fake_user = True
for fc in g.fcurves(act):                                           # 5.x: no act.fcurves
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
ad.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()                # leave the rig at rest
g.save()
```
Bone axes differ per rig: rotate one bone and render before keying a whole clip. Rigify arms default to IK: for FK
keys set `upper_arm_parent.L["IK_FK"] = 1.0` (key it if it changes in the clip).

## Craft (what reads in game)

- Key poses first (stepped), then breakdowns, then splines; read the contact sheet at each step.
- **Walk** (24–32 frames per two steps): contact → down (lowest hips) → passing → up (highest) → contact other side;
  hips bob twice per cycle and sway to the standing leg, shoulders counter-rotate, arms opposite the legs.
- **Run**: no double support, a flight phase, more lean, 16–20 frames.
- **Attack**: readable anticipation → fast strike (2–4 frames) → hold on the hit frame → follow-through, recovery.
- **Idle**: small (breathing, weight shift); big idles get annoying on loop.
- Arcs on hands and head; overlapping parts (tail, hair, cloth bones) lag 1–3 frames.
- Measure feel numerically too: foot slide (cm), hip bounce per clip, head wobble.

## Root motion vs in place

- **In place**: hips oscillate, no travel; the game moves the character. `motion` must say ~0 m/s; `inplace` removes
  travel on the control rig before baking. asset.json `root_motion: false` → Unity locks root XZ.
- **Root motion**: travel on `root`. `motion --bone root` gives the speed; locomotion blend thresholds = measured
  clip ground speeds (no foot slide). `root_motion: true` → Unity keeps XZ. Feet keep world position while planted
  (side contact sheet across the contact span). In Unity: IK foot pinning with a knee hint for uneven ground.
