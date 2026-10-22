# Smoke-test fixtures (tools/tests/art_pipeline_smoke.sh): builds two assets under blender/assets/ of the tree the
# runner was started from (the smoke test runs in a temporary copy, never in the studio itself):
#   SmokeCrate     (Props)      bevelled 0.8 m crate, unique M_ material, smart-UV'd: projection, bakes, materials, export
#   SmokeTentacle  (Characters) 1.2 m tentacle bound to a 3-bone "rig", looping action "Wiggle": rig/anim/skinned export
#   tools/blender_run.sh tools/tests/make_fixture.py
import bpy, bmesh, json, math, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "blender", "lib"))
import gamelib as g

ASSETS = os.path.join(g.root(), "blender", "assets")

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def asset_json(name, data):
    d = os.path.join(ASSETS, name); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "asset.json"), "w") as f:
        json.dump(dict(name=name, **data), f, indent=1)
    os.environ["ASSET_JSON"] = os.path.join(d, "asset.json")
    return os.path.join(d, name + ".blend")

# ---------------------------------------------------------------- SmokeCrate
reset()
blend = asset_json("SmokeCrate", {"category": "Props", "type": "prop", "height_m": 0.8,
                                  "budget": {"tris": 600, "materials": 1}, "textures": {"size": 512, "texel_density": 256}})
cfg = g.config()
coll = g.sub_collection(cfg, "Body")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.8)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.4))
bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.04, segments=2, affect='EDGES')
me = bpy.data.meshes.new("SM_SmokeCrate_Body"); bm.to_mesh(me); bm.free()
crate = bpy.data.objects.new("SM_SmokeCrate_Body", me); coll.objects.link(crate)
mat = bpy.data.materials.new("M_SmokeCrate"); mat.diffuse_color = (0.55, 0.38, 0.2, 1); me.materials.append(mat)
g.select_only([crate])
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
g.save(blend)

# ---------------------------------------------------------------- SmokeTentacle
reset()
blend = asset_json("SmokeTentacle", {"category": "Characters", "type": "creature", "height_m": 1.2,
                                     "budget": {"tris": 1000, "materials": 1, "bones": 10, "influences": 4},
                                     "textures": {"size": 512, "texel_density": 256},
                                     "rig": {"armature": "rig", "skeleton": "custom"},
                                     "animations": [{"name": "Wiggle", "frames": [1, 24], "loop": True}]})
cfg = g.config()
coll = g.sub_collection(cfg, "Body")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.12, radius2=0.04, depth=1.2)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.6))
bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5],
                          cuts=11, use_grid_fill=True)
me = bpy.data.meshes.new("SK_SmokeTentacle_Body"); bm.to_mesh(me); bm.free()
ten = bpy.data.objects.new("SK_SmokeTentacle_Body", me); coll.objects.link(ten)
m2 = bpy.data.materials.new("M_SmokeTentacle"); m2.diffuse_color = (0.3, 0.6, 0.4, 1); me.materials.append(m2)
ad = bpy.data.armatures.new("rig"); arm = bpy.data.objects.new("rig", ad); coll.objects.link(arm)
g.select_only([arm]); bpy.ops.object.mode_set(mode='EDIT')
prev = None
for i in range(3):
    b = ad.edit_bones.new(f"tentacle_{i:02d}")
    b.head = (0, 0, i * 0.4); b.tail = (0, 0, (i + 1) * 0.4)
    if prev: b.parent = prev; b.use_connect = True
    prev = b
bpy.ops.object.mode_set(mode='OBJECT')
ten.parent = arm
mod = ten.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
for i in range(3):
    ten.vertex_groups.new(name=f"tentacle_{i:02d}")
for v in me.vertices:
    for i in range(3):
        w = max(0.0, 1 - abs(v.co.z - (i * 0.4 + 0.2)) / 0.4)
        if w > 0: ten.vertex_groups[i].add([v.index], w, 'REPLACE')
act = bpy.data.actions.new("Wiggle")
arm.animation_data_create(); arm.animation_data.action = act
for f, ang in ((1, 0), (7, 20), (13, 0), (19, -20), (25, 3)):          # frame 25 deliberately off: loopfix closes it
    for i in range(3):
        pb = arm.pose.bones[f"tentacle_{i:02d}"]
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (math.radians(ang), 0, 0)
        pb.keyframe_insert("rotation_euler", frame=f)
for pb in arm.pose.bones:
    pb.rotation_euler = (0, 0, 0)
act.use_frame_range = True; act.frame_start, act.frame_end = 1, 24; act.use_cyclic = True
arm.animation_data.action = None; act.use_fake_user = True
g.save(blend)
print("DONE fixtures SmokeCrate SmokeTentacle")
