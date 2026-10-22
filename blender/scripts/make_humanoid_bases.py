# Build rigged humanoid base files from Blender Studio's "Human Base Meshes" bundle (CC0).
# Not part of the asset loop: tools/fetch_humanoid_bases.sh downloads the bundle and runs this.
#   Blender -b --factory-startup --python blender/scripts/make_humanoid_bases.py -- <bundle.blend> <out_dir> [variant ...]
# Per variant it writes <out_dir>/human_<variant>.blend containing:
#   Body (Armature first, Subdivision after), Eye.L / Eye.R (rigid on DEF-spine.006), rig (Rigify,
#   generated from a Basic Human metarig fitted to measured landmarks), metarig (hidden, for re-fitting).
# Landmarks are measured from the mesh (crotch, ankle, neck, fingertips, cross-section centroids), so
# the fit works for realistic and stylised proportions. Hands have no finger bones (Basic Human).
import bpy, bmesh, sys, os, math, addon_utils
import numpy as np
from mathutils import Vector

VARIANTS = {   # name: (collection in the bundle, body object, multires level to bake or None)
    "female_realistic": ("Body Female - Realistic", "GEO-body_female_realistic", 1),
    "male_realistic":   ("Body Male - Realistic",   "GEO-body_male_realistic",   1),
    "female_stylized":  ("Body Female - Stylized",  "GEO-body_female_stylized",  None),
    "male_stylized":    ("Body Male - Stylized",    "GEO-body_male_stylized",    None),
}
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BUNDLE, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
WANT = argv[2:] or list(VARIANTS)
os.makedirs(OUT, exist_ok=True)
addon_utils.enable("rigify", default_set=True)


def load_variant(coll_name, body_name):
    bpy.ops.wm.read_homefile(use_empty=True)
    with bpy.data.libraries.load(BUNDLE, link=False) as (src, dst):
        dst.collections = [coll_name]
    c = dst.collections[0]
    scene_coll = bpy.context.scene.collection
    body = eyes = None
    eyes = []
    for o in list(c.all_objects):
        scene_coll.objects.link(o)
        if o.name.startswith(body_name + ".eye"): eyes.append(o)
        elif o.name == body_name: body = o
        else: bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)
    for lib in list(bpy.data.libraries): bpy.data.libraries.remove(lib)
    return body, sorted(eyes, key=lambda e: e.name)


def bake_multires(o, level):
    for m in list(o.modifiers):
        if m.type == 'MULTIRES':
            if level is None: o.modifiers.remove(m); continue
            m.levels = level
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.object.modifier_apply(modifier=m.name)


# ---------------------------------------------------------------- landmarks
def landmarks(P):
    """P: (n,3) world verts of a body standing at x=0, front -Y, feet at z~0, A-pose."""
    H = P[:, 2].max(); h = H / 100.0                       # h = 1% of height
    X, Y, Z = P[:, 0], P[:, 1], P[:, 2]
    def sl(m, z, dz=0.6): return P[m & (np.abs(Z - z) < dz * h)]
    mid = np.abs(X) < 0.15 * h
    crotch = Z[mid & (Z > 0.25 * H) & (Z < 0.65 * H)].min()
    L = (X > 0.15 * h) & (X < 16 * h) & (Z < crotch)       # left leg (+X = character's left)
    # ankle: lowest height where the leg's front-back extent drops well below the foot length
    foot = P[L & (Z < 3 * h)]; foot_len = np.ptp(foot[:, 1])
    ankle_z = None
    for z in np.arange(1.0, 20.0, 0.25) * h:
        s = sl(L, z, 0.3)
        if len(s) and np.ptp(s[:, 1]) < 0.5 * foot_len: ankle_z = z; break
    a = sl(L, ankle_z); ankle = Vector((a[:, 0].mean(), a[:, 1].mean(), ankle_z))
    t = sl(L, crotch - 3 * h); hip_x = t[:, 0].mean()
    hip_z = crotch + 4.5 * h
    tor = sl(np.abs(X) < 6 * h, hip_z)
    hip = Vector((hip_x, tor[:, 1].min() + 0.55 * np.ptp(tor[:, 1]), hip_z))
    knee_z = ankle_z + 0.5 * (hip_z - ankle_z)
    k = sl(L, knee_z); knee = Vector((k[:, 0].mean(), k[:, 1].mean() - 0.6 * h, knee_z))
    toe_y = foot[:, 1].min(); heel_y = foot[:, 1].max()
    tip = foot[foot[:, 1] < toe_y + 2 * h]; toe = Vector((tip[:, 0].mean(), toe_y + 0.5 * h, 1.2 * h))
    ball_y = toe_y + 0.27 * foot_len
    b = foot[np.abs(foot[:, 1] - ball_y) < 1.5 * h]
    ball = Vector((b[:, 0].mean(), ball_y, 1.8 * h))
    heel_w = np.ptp(foot[foot[:, 1] > heel_y - 3 * h][:, 0]) / 2
    heel = (Vector((ankle.x - heel_w, heel_y - 1.5 * h, 0.5 * h)), Vector((ankle.x + heel_w, heel_y - 1.5 * h, 0.5 * h)))
    # neck: narrowest torso-centred slice between 70% and 95% height; neck base where it widens
    zs = np.arange(0.70 * H, 0.95 * H, 0.4 * h)
    def width(z):
        s = sl(np.abs(X) < 12 * h, z, 0.3)
        return np.abs(s[:, 0]).max() if len(s) else 0
    W = np.array([width(z) for z in zs]); i_n = int(np.argmin(W)); neck_z, neck_w = zs[i_n], W[i_n]
    nb = [z for z, w in zip(zs[:i_n], W[:i_n]) if w > 2.2 * neck_w]
    neck_base_z = (nb[-1] if nb else neck_z - 6 * h) - 1.0 * h
    head_z = neck_z + 2.0 * h
    def spine_pt(z):
        s = sl(np.abs(X) < 4 * h, z)
        return Vector((0.0, s[:, 1].min() + 0.6 * np.ptp(s[:, 1]), z))
    # arm: fingertip = outermost vertex above the hips; shoulder joint inside the deltoid
    up = (X > 0) & (Z > crotch)
    F = Vector(P[up][np.argmax(X[up])])
    sh_z = neck_base_z - 2.5 * h
    s = sl((X > 4 * h), sh_z, 1.0); sx = s[:, 0].max()
    sh = sl((X > sx - 6 * h), sh_z, 1.0)
    S = Vector((sx - 4.0 * h, sh[:, 1].mean(), sh_z))
    d = (F - S).normalized(); Lr = (F - S).length
    def cross(tt):
        q = S + d * (Lr * tt)
        rel = P - np.array(q); ax = rel @ np.array(d)
        perp = rel - np.outer(ax, np.array(d))
        m = (np.abs(ax) < 0.6 * h) & (np.linalg.norm(perp, axis=1) < 7 * h) & (X > 3 * h)
        if m.sum() < 4: return Vector(q), 1e9
        c = P[m].mean(axis=0)
        return Vector(c), np.linalg.norm(perp[m], axis=1).mean()
    ts = np.arange(0.62, 0.86, 0.01)
    rad = [cross(tt)[1] for tt in ts]; tw = ts[int(np.argmin(rad))]
    wrist = cross(tw)[0]
    elbow = cross(tw * 0.56)[0] + Vector((0, 0.6 * h, 0))   # slight backward bend for IK
    return dict(H=H, h=h, crotch=crotch, hip=hip, knee=knee, ankle=ankle, ball=ball, toe=toe, heel=heel,
                neck_base_z=neck_base_z, neck_z=neck_z, head_z=head_z, spine_pt=spine_pt,
                shoulder=S, elbow=elbow, wrist=wrist, fingertip=F, tor_front=tor[:, 1].min())


def fit_metarig(body):
    bpy.ops.object.armature_basic_human_metarig_add()
    mr = bpy.context.object; mr.name = "metarig"
    P = np.array([body.matrix_world @ v.co for v in body.data.vertices])
    lm = landmarks(P); h = lm["h"]; H = lm["H"]
    bpy.ops.object.mode_set(mode='EDIT')
    eb = mr.data.edit_bones
    zax = {b.name: b.z_axis.copy() for b in eb}
    def put(n, head, tail):
        for side, sx in (("L", 1), ("R", -1)):
            nn = n.replace(".X", "." + side)
            if nn not in eb: continue
            f = lambda v: Vector((v.x * sx, v.y, v.z))
            b = eb[nn]; b.head = f(head); b.tail = f(tail)
            z = zax[nn]; b.align_roll(Vector((z.x, z.y, z.z)))
            if ".X" not in n: break
    # spine: hips -> neck base in four bones, neck in two, head to the top
    zh, znb = lm["hip"].z, lm["neck_base_z"]
    zs = [zh + (znb - zh) * f for f in (0.0, 0.22, 0.48, 0.74, 1.0)]
    zs += [znb + (lm["head_z"] - znb) * 0.5, lm["head_z"], H]
    pts = [lm["spine_pt"](z) for z in zs[:-1]] + [Vector((0, lm["spine_pt"](lm["head_z"]).y, H))]
    for i in range(7):
        put("spine" + ("" if i == 0 else ".%03d" % i), pts[i], pts[i + 1])
    # legs
    put("thigh.X", lm["hip"], lm["knee"]); put("shin.X", lm["knee"], lm["ankle"])
    put("foot.X", lm["ankle"], lm["ball"]); put("toe.X", lm["ball"], lm["toe"])
    hl, hr = lm["heel"]; put("heel.02.X", hl, hr)
    put("pelvis.X", pts[0], Vector((lm["hip"].x * 1.1, lm["tor_front"] + 3 * h, zh + 6 * h)))
    # arms: clavicle from the sternum notch to the shoulder joint
    S = lm["shoulder"]
    put("shoulder.X", Vector((1.5 * h, pts[4].y - 4 * h, znb - 0.5 * h)), S)
    put("upper_arm.X", S, lm["elbow"]); put("forearm.X", lm["elbow"], lm["wrist"])
    put("hand.X", lm["wrist"], lm["wrist"] + (lm["fingertip"] - lm["wrist"]) * 0.92)
    cz = zh + (znb - zh) * 0.70
    s = P
    fr = s[(np.abs(s[:, 2] - cz) < 0.6 * h) & (np.abs(s[:, 0] - 6 * h) < 1.5 * h)][:, 1].min()
    put("breast.X", Vector((6 * h, fr + 6 * h, cz)), Vector((6 * h, fr + 1.5 * h, cz)))
    bpy.ops.object.mode_set(mode='OBJECT')
    return mr, lm


def generate(mr):
    before = set(bpy.data.objects)
    bpy.ops.object.select_all(action='DESELECT')
    mr.select_set(True); bpy.context.view_layer.objects.active = mr
    bpy.ops.pose.rigify_generate()
    rig = [o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE'][0]
    rig.name = "rig"; rig.data.name = "rig"
    return rig


def bind(body, eyes, rig):
    # Bone heat fails silently at human scale (tiny faces), so solve at 10x and scale back
    for o in (body, rig): o.scale = (10, 10, 10)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    for o in (body, rig): o.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    body.matrix_parent_inverse.identity()
    am = [m for m in body.modifiers if m.type == 'ARMATURE'][0]
    while body.modifiers[0] != am:
        with bpy.context.temp_override(object=body): bpy.ops.object.modifier_move_up(modifier=am.name)
    for e in eyes:
        e.parent = rig; e.matrix_parent_inverse.identity()      # rig sits at the origin, unscaled
        g = e.vertex_groups.new(name="DEF-spine.006"); g.add(range(len(e.data.vertices)), 1.0, 'REPLACE')
        m = e.modifiers.new("Armature", 'ARMATURE'); m.object = rig
    # unweighted vertices would stay behind when posed
    unw = sum(1 for v in body.data.vertices if not any(g.weight > 1e-4 for g in v.groups))
    return unw


for name in WANT:
    coll_name, body_name, level = VARIANTS[name]
    body, eyes = load_variant(coll_name, body_name)
    bake_multires(body, level)
    for o in [body] + eyes:                      # the bundle's drivers point at removed modifiers
        o.animation_data_clear()
        if o.data.shape_keys: o.data.shape_keys.animation_data_clear()
    dx = -body.location.x
    for o in [body]: o.location.x += dx          # eyes are parented to the body
    bpy.context.view_layer.update()
    for e in eyes:                               # unparent, keep the world placement
        mw = e.matrix_world.copy(); e.parent = None; e.matrix_world = mw
    body.name = body.data.name = "Body"
    for e, side in zip(eyes, ("L", "R")) if eyes[0].name.endswith("L") else zip(eyes, ("R", "L")):
        e.name = e.data.name = "Eye." + side
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = body; body.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for e in eyes:
        bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = e; e.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [body] + eyes: o.data.shade_smooth() if hasattr(o.data, "shade_smooth") else None
    mr, lm = fit_metarig(body)
    rig = generate(mr)
    unw = bind(body, eyes, rig)
    sub = body.modifiers.new("Subdivision", 'SUBSURF'); sub.levels = 0 if level else 1; sub.render_levels = 1 if level else 2
    mr.hide_set(True); mr.hide_render = True
    for c in bpy.data.collections:               # Rigify's bone-shape meshes
        if c.name.startswith("WGTS"): c.hide_viewport = c.hide_render = True
    bpy.ops.object.select_all(action='DESELECT')
    path = os.path.join(OUT, "human_%s.blend" % name)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
    if os.path.exists(path + "1"): os.remove(path + "1")
    f = lambda v: "(%.3f %.3f %.3f)" % tuple(v)
    print("BASE", name, "H=%.3f" % lm["H"], "verts", len(body.data.vertices), "unweighted", unw,
          "hip", f(lm["hip"]), "knee", f(lm["knee"]), "ankle", f(lm["ankle"]), "shoulder", f(lm["shoulder"]),
          "elbow", f(lm["elbow"]), "wrist", f(lm["wrist"]), "neck_base %.3f" % lm["neck_base_z"], "->", path)
