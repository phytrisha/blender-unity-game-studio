# Orthographic review renders and AI control images of the asset. Never saves the .blend.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/render_views.py <Name>.blend -- --tag look [--views front,right,back,q34] [--mode clay]
#        [--size 1024] [--frames 1,8,16] [--pose pose.json [--rig rig]] [--out out/] [--only Obj1,Obj2]
#        [--action walk [--rig GameRig]]   (plays that action on the rig for --frames)
# Modes: clay (grey + cavity) · color (material viewport colours) · texture (image textures, Workbench)
#        · lit (EEVEE, real materials) · normal (camera-space normals, OpenGL/blue-facing) · depth (near
#        = white) · mask (white silhouette on black)
# Writes out/<tag>_<view>[_f<frame>].png, a stitched out/<tag>_sheet.png (rows = frames, cols =
# views), and out/<tag>_cams.json (camera matrices, used by weave-texturing/project_paint.py).
import bpy, json, math, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g
import numpy as np
from mathutils import Vector, Matrix

cfg = g.config(); a = g.kv_args()
TAG = a.get("tag", "look")
VIEWS = a.get("views", "front,right,back,q34").split(",")
MODE = a.get("mode", "clay")
SIZE = int(a.get("size", 1024))
OUT = a.get("out") or g.path(cfg, "out")
os.makedirs(OUT, exist_ok=True)
FRAMES = [int(f) for f in a["frames"].split(",")] if "frames" in a else [bpy.context.scene.frame_current]
MARGIN = float(a.get("margin", 1.08))

# view name -> direction the camera looks FROM (world, front of asset faces -Y)
DIRS = {"front": (0, -1, 0), "back": (0, 1, 0), "right": (1, 0, 0), "left": (-1, 0, 0),
        "top": (0, 0, 1), "bottom": (0, 0, -1), "q34": (1, -1, 0.55), "q34l": (-1, -1, 0.55),
        "q34back": (1, 1, 0.55)}

sc = bpy.context.scene
objs = g.asset_objects(cfg, ("MESH",))
if "only" in a:
    keep = set(a["only"].split(","))
    objs = [o for o in objs if o.name in keep]
if not objs:
    g.report("FAIL", f"no mesh objects in collection '{cfg['collection']}'"); sys.exit(1)
vis = set(objs)
for o in sc.objects:
    if o.type in ("MESH", "CURVE", "SURFACE", "META", "FONT", "GPENCIL", "EMPTY", "LIGHT") and o not in vis:
        o.hide_render = True

# ---- pose (display only)
arm = bpy.data.objects.get(a["rig"]) if "rig" in a else g.armature(cfg)
if arm and "pose" in a:
    with open(a["pose"]) as f:
        pose = json.load(f)
    for bname, rot in pose.items():
        pb = arm.pose.bones.get(bname)
        if pb is None:
            g.report("WARN", f"pose: no bone {bname}"); continue
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = [math.radians(r) for r in rot]

# ---- render settings per mode
sc.render.resolution_x = sc.render.resolution_y = SIZE
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
world = sc.world or bpy.data.worlds.new("World"); sc.world = world
if MODE in ("clay", "color", "texture"):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
    sh.color_type = {"clay": 'SINGLE', "color": 'MATERIAL', "texture": 'TEXTURE'}[MODE]
    sh.single_color = (0.62, 0.62, 0.62)
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.18, 0.18, 0.2)
    sh.show_object_outline = False
else:
    sc.render.engine = 'BLENDER_EEVEE'
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (0.2, 0.2, 0.22, 1) if MODE == "lit" else (0, 0, 0, 1)
    bg.inputs[1].default_value = 1.0 if MODE == "lit" else 0.0

lo, hi = g.bounds(objs)
center = (lo + hi) / 2
radius = max((hi - lo).length / 2, 1e-3)

def override_material(kind):
    m = bpy.data.materials.new(f"__{kind}")
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs[0])
    if kind == "mask":
        em.inputs[0].default_value = (1, 1, 1, 1)
    elif kind == "normal":
        geo = nt.nodes.new("ShaderNodeNewGeometry"); vt = nt.nodes.new("ShaderNodeVectorTransform")
        vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
        mad = nt.nodes.new("ShaderNodeVectorMath"); mad.operation = 'MULTIPLY_ADD'
        mad.inputs[1].default_value = (0.5, 0.5, -0.5); mad.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs["Normal"], vt.inputs[0]); nt.links.new(vt.outputs[0], mad.inputs[0])
        nt.links.new(mad.outputs[0], em.inputs[0])
    elif kind == "depth":
        cd = nt.nodes.new("ShaderNodeCameraData"); mr = nt.nodes.new("ShaderNodeMapRange")
        m["near_far"] = True
        nt.links.new(cd.outputs["View Z Depth"], mr.inputs[0]); nt.links.new(mr.outputs[0], em.inputs[0])
    return m

if MODE in ("normal", "depth", "mask"):
    sc.view_settings.view_transform = 'Raw'      # data images: no sRGB encoding (0.5 stays 128)
    mat = override_material(MODE)
    bpy.context.view_layer.material_override = mat

if "action" in a:
    act = bpy.data.actions.get(a["action"]); rig_ = arm
    if act is None or rig_ is None:
        g.report("FAIL", f"--action needs an existing action and rig (have {[x.name for x in bpy.data.actions]})"); sys.exit(1)
    ad = rig_.animation_data_create(); ad.action = act
    if act.slots and ad.action_slot is None: ad.action_slot = act.slots[0]

cam_data = bpy.data.cameras.new("__cam"); cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("__cam", cam_data); sc.collection.objects.link(cam); sc.camera = cam
cams, tiles = {}, []
for f in FRAMES:
    sc.frame_set(f)
    row = []
    for v in VIEWS:
        d = Vector(DIRS[v]).normalized()
        dist = radius * 4
        cam.location = center + d * dist
        up = Vector((0, 1, 0)) if abs(d.z) > 0.99 else Vector((0, 0, 1))
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y' if abs(d.z) > 0.99 else 'Y').to_euler()
        # fit: project bounds corners into camera plane
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        corners = [inv @ (o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box]
        w = max(c.x for c in corners) - min(c.x for c in corners)
        h = max(c.y for c in corners) - min(c.y for c in corners)
        cx = (max(c.x for c in corners) + min(c.x for c in corners)) / 2
        cy = (max(c.y for c in corners) + min(c.y for c in corners)) / 2
        cam.location = cam.matrix_world @ Vector((cx, cy, 0))
        cam_data.ortho_scale = max(w, h) * MARGIN
        cam_data.clip_start = 0.001; cam_data.clip_end = dist * 4
        if MODE == "depth":
            zs = [-c.z for c in corners]
            mr = next(n for n in mat.node_tree.nodes if n.type == 'MAP_RANGE')
            mr.inputs[1].default_value = min(zs); mr.inputs[2].default_value = max(zs)
            mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
        bpy.context.view_layer.update()
        name = f"{TAG}_{v}" + (f"_f{f}" if len(FRAMES) > 1 else "")
        sc.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)
        cams[v] = {"matrix_world": [list(r) for r in cam.matrix_world], "ortho_scale": cam_data.ortho_scale,
                   "type": "ORTHO", "resolution": [SIZE, SIZE], "image": sc.render.filepath, "frame": f}
        row.append(g.load_pixels(sc.render.filepath)[:, :, :3])
    tiles.append(np.concatenate(row, axis=1))

sheet = np.concatenate(tiles[::-1], axis=0)   # first frame on top (pixel rows run bottom-up)
g.save_pixels(sheet, os.path.join(OUT, f"{TAG}_sheet.png"))
with open(os.path.join(OUT, f"{TAG}_cams.json"), "w") as fh:
    json.dump({"mode": MODE, "views": cams}, fh, indent=1)
g.report("INFO", f"bounds {tuple(round(x, 3) for x in lo)} .. {tuple(round(x, 3) for x in hi)} m")
print(f"DONE {os.path.join(OUT, TAG + '_sheet.png')}")
