# Animation utilities for game actions (Blender 4.4+/5.x slotted actions).
#   ASSET=<Name> tools/blender_run.sh blender/scripts/anim_tools.py <Name>.blend -- list
#   ASSET=<Name> tools/blender_run.sh blender/scripts/anim_tools.py <Name>.blend -- loopfix --action ctrl_walk [--frames 1,24] [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/anim_tools.py <Name>.blend -- motion  --action walk [--bone Hips] [--rig GameRig]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/anim_tools.py <Name>.blend -- inplace --action walk --bone Hips [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/anim_tools.py <Name>.blend -- events  --action attack --set hit:12,trail_on:8 [--save]
# loopfix: copies every channel's value at the first frame to frame end+1, sets the action's manual
#          range to start..end and use_cyclic. (Convention: exported range excludes the wrap frame.)
# motion : world-space travel of a bone over the action -> speed in m/s at the scene fps. Use it to
#          set the engine's locomotion speed or check that a walk cycle doesn't slide.
# inplace: removes the linear drift of a bone's location channels (keeps bobs and sways): turns a
#          root-motion walk into an in-place one. Run on the control rig before baking.
# events : pose markers on the action (frame-accurate gameplay events: hit frames, footsteps).
#          Unity doesn't import Blender markers; export_skinned.py writes them into SK_<Name>.json and the
#          importer turns them into AnimationEvents (function name = marker name).
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

cfg = g.config(); argv = g.args(); mode = argv[0] if argv else "list"; a = g.kv_args(argv[1:])
sc = bpy.context.scene; fps = sc.render.fps / sc.render.fps_base
act = bpy.data.actions.get(a.get("action", "")) if "action" in a else None
if mode != "list" and act is None:
    g.report("FAIL", f"no action '{a.get('action')}' - have {[x.name for x in bpy.data.actions]}"); sys.exit(1)

def rng(action):
    if "frames" in a:
        f0, f1 = (int(x) for x in a["frames"].split(","))
    elif action.use_frame_range:
        f0, f1 = int(action.frame_start), int(action.frame_end)
    else:
        f0, f1 = (int(x) for x in action.frame_range)
    return f0, f1

def owner(action):
    """An armature that can play this action (one whose bone names its curves use)."""
    want = a.get("rig")
    for o in bpy.data.objects:
        if o.type != 'ARMATURE' or (want and o.name != want): continue
        paths = [fc.data_path for fc in g.fcurves(action)]
        if any(f'pose.bones["{b.name}"]' in p for b in o.data.bones for p in paths[:50]):
            return o
    return None

if mode == "list":
    for x in bpy.data.actions:
        f0, f1 = rng(x)
        print(f"ACTION {x.name:28s} {f0:4d}-{f1:<4d} {(f1 - f0 + 1) / fps:5.2f}s cyclic={x.use_cyclic} "
              f"fake_user={x.use_fake_user} curves={len(g.fcurves(x))} markers={[(m.name, m.frame) for m in x.pose_markers]}")
elif mode == "loopfix":
    f0, f1 = rng(act); n = 0
    for fc in g.fcurves(act):
        if not fc.keyframe_points: continue
        v = fc.evaluate(f0)
        for kp in list(fc.keyframe_points):
            if kp.co.x > f1 + 1e-3:
                fc.keyframe_points.remove(kp)
        fc.keyframe_points.insert(f1 + 1, v); fc.update(); n += 1
    act.use_frame_range = True; act.frame_start, act.frame_end = f0, f1; act.use_cyclic = True
    g.report("PASS", f"{act.name}: {n} channels closed at frame {f1 + 1}; range {f0}-{f1}, cyclic")
elif mode in ("motion", "inplace"):
    rig = owner(act)
    if rig is None:
        g.report("FAIL", "no armature plays this action (--rig)"); sys.exit(1)
    bone = a.get("bone") or next((b.name for b in rig.data.bones if b.parent is None or b.parent.name == "root"), None)
    f0, f1 = rng(act)
    if mode == "motion":
        ad = rig.animation_data_create(); prev = ad.action; ad.action = act
        if act.slots and ad.action_slot is None: ad.action_slot = act.slots[0]
        sc.frame_set(f0); p0 = (rig.matrix_world @ rig.pose.bones[bone].head).copy()
        sc.frame_set(f1 + 1); p1 = (rig.matrix_world @ rig.pose.bones[bone].head).copy()
        ad.action = prev
        d = p1 - p0; secs = (f1 + 1 - f0) / fps
        horiz = (d.x ** 2 + d.y ** 2) ** 0.5
        g.report("INFO", f"{act.name}: {bone} travels {horiz:.3f} m horizontally in {secs:.2f}s -> "
                         f"{horiz / secs:.3f} m/s (dz {d.z:+.3f}); {'root motion' if horiz > 0.05 else 'in place'}")
    else:
        n = 0
        for fc in g.fcurves(act):
            if fc.data_path != f'pose.bones["{bone}"].location': continue
            v0, v1 = fc.evaluate(f0), fc.evaluate(f1 + 1); slope = (v1 - v0) / (f1 + 1 - f0)
            for kp in fc.keyframe_points:
                off = slope * (kp.co.x - f0)
                kp.co.y -= off; kp.handle_left.y -= off; kp.handle_right.y -= off
            fc.update(); n += 1
        g.report("PASS" if n else "WARN", f"{act.name}: removed drift from {n} location channels of {bone}")
elif mode == "events":
    for item in a.get("set", "").split(","):
        if not item: continue
        name, fr = item.split(":")
        m = act.pose_markers.get(name) or act.pose_markers.new(name); m.frame = int(fr)
    print("EVENTS", act.name, sorted(((m.frame, m.name) for m in act.pose_markers)))
else:
    g.report("FAIL", "mode: list | loopfix | motion | inplace | events"); sys.exit(2)
if "save" in a:
    g.save()
print(f"DONE anim {mode}")
