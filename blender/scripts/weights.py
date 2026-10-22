# Skin weights for game meshes.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/weights.py <Name>.blend -- bind  --arm GameRig --obj Body[,Hair] [--scale10] [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/weights.py <Name>.blend -- clean --arm GameRig [--obj Body] [--max 4] [--min 0.01] [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/weights.py <Name>.blend -- rigid --arm GameRig --obj Helmet --bone Head [--save]
# bind : automatic (bone heat) weights. --scale10 scales mesh+rig x10 around the origin first: bone
#        heat fails on human-scale meshes with tiny faces ("Bone Heat Weighting: failed").
# clean: drop weights < --min, keep the --max strongest deform influences per vertex, normalise,
#        delete groups with no matching deform bone. Unity skins with up to 4 bones per vertex by default
#        (Quality > Skin Weights) - clean before export, then look at a pose test.
# rigid: whole object follows one bone at 100% (helmets, weapons, eyes, armour plates).
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g
from mathutils import Matrix

cfg = g.config(); argv = g.args(); mode = argv[0] if argv else ""; a = g.kv_args(argv[1:])
arm = bpy.data.objects.get(a.get("arm", "")) or g.armature(cfg)
if arm is None:
    g.report("FAIL", "no armature (--arm)"); sys.exit(1)
objs = [bpy.data.objects[n] for n in a["obj"].split(",")] if "obj" in a else [
    o for o in g.asset_objects(cfg) if any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers)]
deform = {b.name for b in arm.data.bones if b.use_deform}

def ensure_modifier(o):
    mod = next((m for m in o.modifiers if m.type == 'ARMATURE'), None) or o.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm
    while o.modifiers[0] != mod:                       # armature first, before any other deformer
        bpy.context.view_layer.objects.active = o
        with bpy.context.temp_override(object=o):
            bpy.ops.object.modifier_move_up(modifier=mod.name)
    if o.parent != arm:
        mw = o.matrix_world.copy(); o.parent = arm; o.matrix_world = mw

if mode == "bind":
    if "scale10" in a:
        S = Matrix.Scale(10, 4)
        for o in objs + [arm]:
            o.matrix_world = S @ o.matrix_world
    for o in objs:
        for vg in list(o.vertex_groups):
            if vg.name in deform: o.vertex_groups.remove(vg)
    g.select_only(objs + [arm], active=arm)
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    if "scale10" in a:
        S = Matrix.Scale(0.1, 4)
        for o in [arm]:
            o.matrix_world = S @ o.matrix_world      # children follow the parent
        for o in objs:
            if o.parent != arm: o.matrix_world = S @ o.matrix_world
    for o in objs:
        ensure_modifier(o)
        empty = sum(1 for v in o.data.vertices if not any(ge.weight > 1e-3 for ge in v.groups))
        g.report("WARN" if empty else "PASS", f"{o.name}: bound, {empty} unweighted verts"
                 + (" - try --scale10, fix non-manifold/loose parts, or bind pieces separately" if empty else ""))
elif mode == "clean":
    mx, mn = int(a.get("max", cfg["budget"].get("influences", 4))), float(a.get("min", 0.01))
    for o in objs:
        names = {vg.index: vg.name for vg in o.vertex_groups}
        for vg in list(o.vertex_groups):
            if vg.name not in deform and not vg.name.startswith(("mask_", "MASK")):
                o.vertex_groups.remove(vg)
        names = {vg.index: vg.name for vg in o.vertex_groups}
        changed = 0
        for v in o.data.vertices:
            ws = sorted(((ge.weight, ge.group) for ge in v.groups if names.get(ge.group) in deform), reverse=True)
            keep = [(w, gi) for w, gi in ws[:mx] if w >= mn] or ws[:1]
            total = sum(w for w, _ in keep) or 1.0
            drop = {gi for _, gi in ws} - {gi for _, gi in keep}
            for gi in drop:
                o.vertex_groups[gi].remove([v.index])
            for w, gi in keep:
                if abs(w / total - w) > 1e-5:
                    o.vertex_groups[gi].add([v.index], w / total, 'REPLACE')
            changed += bool(drop) or abs(total - 1) > 1e-4
        g.report("INFO", f"{o.name}: {changed} verts changed (max {mx} influences, min {mn}, normalised)")
        ensure_modifier(o)
elif mode == "rigid":
    bone = a["bone"]
    if bone not in deform:
        g.report("FAIL", f"{bone} is not a deform bone of {arm.name}"); sys.exit(1)
    for o in objs:
        for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
        o.vertex_groups.new(name=bone).add([v.index for v in o.data.vertices], 1.0, 'REPLACE')
        ensure_modifier(o); g.report("PASS", f"{o.name}: rigid to {bone}")
else:
    g.report("FAIL", "mode: bind | clean | rigid"); sys.exit(2)
if "save" in a:
    g.save()
print(f"DONE weights {mode}")
