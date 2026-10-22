# Export a rigged asset (armature + skinned meshes + clips) for Unity, then re-import the file into an empty scene and
# report what arrived. Static meshes don't come here: they go through blender/scripts/stages.py (export.py:
# LODs, UCX hulls, vertex masks, lightmap UVs).
#
#   ASSET=Guard tools/blender_run.sh blender/scripts/export_skinned.py blender/assets/Guard/Guard.blend [-- --textures]
#
# Writes blender/export/Characters/<Name>/:
#   SK_<Name>.fbx    armature + every mesh bound to it, all clips as takes (one NLA strip per action, so each take
#                    carries its action's name and frame range); deform bones only, no leaf bones
#   SK_<Name>.json   manifest: tris, bones, dimensions, clips {name: {frames, loop, root_motion, events}}. Copied next
#                    to the FBX by tools/sync_to_unity.sh; AssetImportRules reads it for loop / root-motion flags
#   Textures/T_*.png the material maps (with --textures), picked up by sync_to_unity.sh
# Armature = asset.json rig.armature (the game skeleton, e.g. GameRig); actions named ctrl_* (control-rig sources)
# and __* are skipped. A game rig made by game_skeleton.py follows the control rig through constraints: they are
# muted for the export. Clip flags come from asset.json "animations" ({name, frames, loop, root_motion}).
# FBX: scale "All" (no x100 root on the armature), -Z forward / Y up, as Unity's Humanoid importer expects.
import bpy, json, os, shutil, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

cfg = g.config(); a = g.kv_args()
NAME = cfg["name"]
OUT = g.path(cfg, "export")
arm = g.armature(cfg)
if arm is None:
    g.report("FAIL", f"no armature (asset.json rig.armature, or an ARMATURE in collection {cfg['collection']})"); sys.exit(1)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and
          (any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers) or o.parent == arm)]
if not meshes:
    g.report("FAIL", f"no meshes bound to {arm.name}"); sys.exit(1)
actions = [x for x in bpy.data.actions if not x.name.startswith(("__", "ctrl_"))]
spec = {x["name"]: x for x in cfg.get("animations", [])}

# clean rest pose, follow constraints off (export samples the game rig's own keys)
arm.data.pose_position = 'POSE'
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
    for c in pb.constraints:
        c.mute = True
ad = arm.animation_data_create(); ad.action = None
for t in list(ad.nla_tracks):
    ad.nla_tracks.remove(t)
for act in actions:                               # one track + strip per clip -> one named take each
    f0 = int(act.frame_start if act.use_frame_range else act.frame_range[0])
    tr = ad.nla_tracks.new(); tr.name = act.name
    st = tr.strips.new(act.name, f0, act); st.name = act.name
    if act.use_frame_range:
        st.action_frame_start, st.action_frame_end = act.frame_start, act.frame_end

g.select_only([arm] + meshes, active=arm)
fbx = os.path.join(OUT, f"SK_{NAME}.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx, use_selection=True, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers=True,
    mesh_smooth_type='FACE', use_triangles=True, use_tspace=True, add_leaf_bones=False,
    use_armature_deform_only=True, primary_bone_axis='Y', secondary_bone_axis='X', armature_nodetype='NULL',
    bake_anim=bool(actions), bake_anim_use_all_actions=False, bake_anim_use_nla_strips=True,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
    path_mode='STRIP', embed_textures=False)
for t in list(ad.nla_tracks):
    ad.nla_tracks.remove(t)

# manifest
lo, hi = g.bounds(meshes)
clips = {}
for act in actions:
    fr = (act.frame_start, act.frame_end) if act.use_frame_range else tuple(act.frame_range)
    s = spec.get(act.name, {})
    clips[act.name] = {"frames": [int(fr[0]), int(fr[1])], "loop": bool(s.get("loop", act.use_cyclic)),
                       "root_motion": bool(s.get("root_motion", False)),
                       "events": {m.name: m.frame for m in act.pose_markers}}
    if act.name not in spec:
        g.report("WARN", f"clip {act.name} is not listed in asset.json animations (loop taken from use_cyclic)")
fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
clip_list = [{"name": k, "first": v["frames"][0], "last": v["frames"][1], "loop": v["loop"], "rootMotion": v["root_motion"],
              "events": [{"name": n, "frame": f} for n, f in sorted(v["events"].items(), key=lambda x: x[1])]}
             for k, v in clips.items()]
manifest = {"name": f"SK_{NAME}", "fps": fps, "clipList": clip_list, "tris": sum(g.evaluated_tris(o) for o in meshes),
            "bones": sum(1 for b in arm.data.bones if b.use_deform), "dimensions": [round(x, 3) for x in (hi - lo)],
            "materials": sorted({m.name for o in meshes for m in o.data.materials if m}), "clips": clips,
            "skeleton": cfg["rig"].get("skeleton")}
with open(os.path.join(OUT, f"SK_{NAME}.json"), "w") as f:
    json.dump(manifest, f, indent=1)

if "textures" in a:
    tdir = os.path.join(OUT, "Textures"); os.makedirs(tdir, exist_ok=True)
    for o in meshes:
        for m in o.data.materials:
            for n in (m.node_tree.nodes if m and m.node_tree else []):
                if n.type == 'TEX_IMAGE' and n.image:
                    src = bpy.path.abspath(n.image.filepath)
                    if os.path.basename(src).startswith("T_") and os.path.exists(src):
                        shutil.copy2(src, os.path.join(tdir, os.path.basename(src)))
                    else:
                        g.report("WARN", f"texture not exported (not T_* or missing): {src}")

# round trip: what does an FBX importer see?
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
shapes = {pb.custom_shape for x in arms for pb in x.pose.bones if pb.custom_shape}
ms = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o not in shapes]
lo2, hi2 = g.bounds(ms)
size = tuple(round(x, 3) for x in (hi2 - lo2))
ok = bool(ms and arms) and all(abs(x - y) < 0.02 for x, y in zip(size, manifest["dimensions"]))
g.report("PASS" if ok else "FAIL",
         f"roundtrip SK_{NAME}.fbx: {len(ms)} meshes, {sum(g.evaluated_tris(o) for o in ms)} tris, "
         f"{sum(len(x.data.bones) for x in arms)} bones, takes {sorted(x.name.split('|')[-1] for x in bpy.data.actions)}, "
         f"size {size} m (built {tuple(manifest['dimensions'])})")
print(f"DONE export_skinned {fbx}")
