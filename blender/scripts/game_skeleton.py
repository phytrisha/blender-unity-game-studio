# Build a clean, engine-ready deform skeleton from a control rig (Rigify or any rig with
# deform + helper bones), rebind the meshes to it, and bake control-rig actions onto it.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/game_skeleton.py <Name>.blend -- --src rig [--name GameRig] [--names unity|keep]
#         [--bake all|ctrl_walk,ctrl_idle] [--save]
# - Keeps only deform bones; every bone gets its nearest *deform* ancestor as parent (Rigify parents
#   DEF-thigh/DEF-upper_arm/DEF-shoulder to ORG bones, which breaks deform-only export). ORG-x is
#   resolved to DEF-x. Bones with no deform ancestor go under a new "root" bone at the origin.
# - No B-bones, no constraints left after baking: the engine sees exactly what Blender shows.
# - Copy Transforms constraints keep the game rig following the control rig, so you keep animating
#   the control rig. Baking writes actions named without the "ctrl_" prefix (ctrl_walk -> walk).
# - Vertex groups on bound meshes are renamed with the bone map and the Armature modifier retargeted.
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

cfg = g.config(); a = g.kv_args()
src = bpy.data.objects[a.get("src") or (cfg["rig"].get("armature") or "rig")]
NAME = a.get("name", "GameRig")
STYLE = a.get("names", "keep")

# Rigify basic-human DEF names -> Unity Humanoid-friendly names. Side suffix handled below. Verify in Unity's
# Avatar configuration; extra bones (twists, breasts) are fine to leave unmapped.
MAPS = {
    "unity": {"spine": "Hips", "spine.001": "Spine", "spine.002": "Chest", "spine.003": "UpperChest",
              "spine.004": "Neck", "spine.005": "NeckUpper", "spine.006": "Head",
              "shoulder": "{S}Shoulder", "upper_arm": "{S}UpperArm", "upper_arm.001": "{S}UpperArmTwist",
              "forearm": "{S}LowerArm", "forearm.001": "{S}LowerArmTwist", "hand": "{S}Hand",
              "thigh": "{S}UpperLeg", "thigh.001": "{S}UpperLegTwist", "shin": "{S}LowerLeg",
              "shin.001": "{S}LowerLegTwist", "foot": "{S}Foot", "toe": "{S}Toes",
              "pelvis": "{S}Pelvis", "breast": "{S}Breast"},
}

def engine_name(n):
    if STYLE not in MAPS:
        return n
    base = n[4:] if n.startswith("DEF-") else n
    side = None
    for suf in (".L", ".R"):
        if base.endswith(suf) or suf + "." in base:
            side = suf[1]; base = base.replace(suf, "", 1); break
    m = MAPS[STYLE].get(base)
    if m is None:
        return n.replace("DEF-", "")
    return m.format(S={"L": "Left", "R": "Right"}.get(side, ""), s=(side or "").lower())

bones = src.data.bones
deform = [b for b in bones if b.use_deform]
if not deform:
    g.report("FAIL", f"{src.name} has no deform bones"); sys.exit(1)

def deform_parent(b):
    p = b.parent
    while p is not None:
        if p.use_deform and p != b:
            return p.name
        if p.name.startswith("ORG-"):
            d = bones.get("DEF-" + p.name[4:])
            if d is not None and d != b and d.use_deform:
                return d.name
        p = p.parent
    return None

rename = {b.name: engine_name(b.name) for b in deform}
if len(set(rename.values())) != len(rename):
    g.report("FAIL", "bone map produced duplicate names; use --names keep"); sys.exit(1)

# ---- build (replace any previous game rig)
old = bpy.data.objects.get(NAME)
rebind = [o for o in bpy.data.objects if o.type == 'MESH' and any(
    m.type == 'ARMATURE' and m.object in (src, old, None) for m in o.modifiers)]
if old:
    for o in rebind:
        if o.parent == old:
            mw = o.matrix_world.copy(); o.parent = src; o.matrix_world = mw
    bpy.data.objects.remove(old, do_unlink=True)
ad = bpy.data.armatures.new(NAME); rig = bpy.data.objects.new(NAME, ad)
for c in src.users_collection:
    c.objects.link(rig)
rig.matrix_world = src.matrix_world.copy()
ad.display_type = 'STICK'; rig.show_in_front = True
rig["game_rig_source"] = src.name          # export_asset mutes the follow constraints when exporting
g.select_only([rig]); bpy.ops.object.mode_set(mode='EDIT')
root = ad.edit_bones.new("root"); root.head = (0, 0, 0); root.tail = (0, 0.25, 0); root.use_deform = False
for b in deform:
    eb = ad.edit_bones.new(rename[b.name])
    eb.head = b.head_local; eb.tail = b.tail_local
    eb.matrix = b.matrix_local.copy()
    eb.use_deform = True; eb.bbone_segments = 1
for b in deform:
    eb = ad.edit_bones[rename[b.name]]; p = deform_parent(b)
    eb.parent = ad.edit_bones[rename[p]] if p else root
    eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for b in deform:
    con = rig.pose.bones[rename[b.name]].constraints.new('COPY_TRANSFORMS')
    con.target = src; con.subtarget = b.name
g.report("INFO", f"{NAME}: {len(deform)} deform bones + root; "
                 f"re-parented {sum(1 for b in deform if b.parent is None or not b.parent.use_deform)} orphans")

# ---- rebind meshes
for o in rebind:
    mod = next((m for m in o.modifiers if m.type == 'ARMATURE' and m.object in (src, None)), None)
    if mod is None: continue
    for vg in o.vertex_groups:
        if vg.name in rename: vg.name = rename[vg.name]
    mod.object = rig
    if o.parent == src:
        mw = o.matrix_world.copy(); o.parent = rig; o.matrix_world = mw
    g.report("INFO", f"rebound {o.name} -> {NAME}")
if cfg["rig"].get("armature") != NAME:
    g.report("INFO", f'set "rig": {{"armature": "{NAME}"}} in asset.json so QA and export use the game rig')

# ---- bake control actions onto the game rig
if "bake" in a:
    want = [x.name for x in bpy.data.actions if x.name.startswith("ctrl_")] if a["bake"] == "all" else a["bake"].split(",")
    src.animation_data_create()
    for an in want:
        act = bpy.data.actions.get(an)
        if act is None:
            g.report("WARN", f"no action {an}"); continue
        src.animation_data.action = act
        if act.slots and src.animation_data.action_slot is None:
            src.animation_data.action_slot = act.slots[0]
        f0, f1 = (int(act.frame_start), int(act.frame_end)) if act.use_frame_range else map(int, act.frame_range)
        if act.use_cyclic or act.get("loop"):
            f1 += 1                                     # include the wrap frame so loops stay closed
        out = an[5:] if an.startswith("ctrl_") else an + "_baked"
        if out in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[out])
        g.select_only([rig]); bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=False, visual_keying=True,
                         clear_constraints=False, use_current_action=False, bake_types={'POSE'})
        bpy.ops.object.mode_set(mode='OBJECT')
        baked = rig.animation_data.action; baked.name = out; baked.use_fake_user = True
        baked.use_frame_range = True; baked.frame_start, baked.frame_end = f0, (f1 - 1 if act.use_cyclic or act.get("loop") else f1)
        baked.use_cyclic = act.use_cyclic
        rig.animation_data.action = None
        g.report("INFO", f"baked {an} -> {out} frames {f0}-{f1}")
    src.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
if "save" in a:
    g.save()
print(f"DONE game skeleton {NAME}")
