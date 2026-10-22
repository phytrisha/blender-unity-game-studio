# Project painted view images (e.g. Weave outputs made from render_views control images) back onto
# the asset's UV map and blend them into one texture.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/project_paint.py <Name>.blend -- --cams out/ctl_cams.json[,out/ctl2_cams.json] \
#         --images front:sources/weave/Crate/front.png,q34:sources/weave/Crate/q34.png \
#         [--obj Crate,Lid] [--uv UVMap] [--size 2048] [--power 4] \
#         [--base textures/T_Crate_BC.png [--fill-only]] [--fill 808080] --out textures/T_Crate_BC.png
# --fill-only: with --base, only texels that the base's _coverage.png marks red (unseen) are painted;
#              everything already painted is kept. Use it to add a view for the gaps.
# How: per view, Cycles bakes (a) the image seen through that camera (emission via projected UVs)
# and (b) a visibility weight = facing ratio x shadow from a sun along the view x in-frame mask x
# image alpha. Views are blended by weight^power. Texels no view sees keep --base or --fill.
# Writes <out>, <out>_coverage.png (white = painted, red = inside UVs but unseen -> inpaint these),
# and prints coverage %. Images must be the SAME framing as the cams JSON (same size and aspect).
import bpy, json, math, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g
import numpy as np
from mathutils import Matrix
from bpy_extras.object_utils import world_to_camera_view

cfg = g.config(); a = g.kv_args()
for req in ("cams", "images", "out"):
    if req not in a:
        g.report("FAIL", f"missing --{req}"); sys.exit(2)
cams = {}
for cp in a["cams"].split(","):          # several cams files merge (e.g. a later render of extra views)
    cams.update(json.load(open(cp))["views"])
images = dict(kv.split(":", 1) for kv in a["images"].split(","))
SIZE = int(a.get("size", cfg["textures"]["size"]))
POWER = float(a.get("power", 4))
FILL = tuple(int(a.get("fill", "808080")[i:i + 2], 16) / 255 for i in (0, 2, 4))
sc = bpy.context.scene

src = [bpy.data.objects[n] for n in a["obj"].split(",")] if "obj" in a else g.asset_objects(cfg)
arm = g.armature(cfg)
if arm:
    arm.data.pose_position = 'REST'

# ---- temporary evaluated copies (modifiers applied, rest pose), sharing nothing with the originals
dg = bpy.context.evaluated_depsgraph_get()
tmp_coll = bpy.data.collections.new("__paint"); sc.collection.children.link(tmp_coll)
for o in sc.objects:
    o.hide_render = True
temps = []
for o in src:
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    t = bpy.data.objects.new("__p_" + o.name, me); t.matrix_world = o.matrix_world.copy()
    tmp_coll.objects.link(t); temps.append(t)
    uv = a.get("uv") or (o.data.uv_layers.active.name if o.data.uv_layers.active else None)
    if uv is None or uv not in me.uv_layers:
        g.report("FAIL", f"{o.name} has no UV map '{uv}' - unwrap first (uv-unwrapping skill)"); sys.exit(1)
    me.uv_layers.active = me.uv_layers[uv]
    proj = me.uv_layers.new(name="__proj")
    me.uv_layers.active = me.uv_layers[uv]          # bake writes into the asset UV, samples __proj
    me.materials.clear()

def new_image(name, alpha=True):
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=alpha, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    return img

def pixels(img):
    arr = np.empty(SIZE * SIZE * 4, np.float32); img.pixels.foreach_get(arr)
    return arr.reshape(SIZE, SIZE, 4)

def material(kind, view_img=None, target=None):
    m = bpy.data.materials.new(f"__{kind}"); nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "__proj"
    if kind == "color":
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = view_img; tex.extension = 'CLIP'
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(uvn.outputs[0], tex.inputs[0]); nt.links.new(tex.outputs[0], em.inputs[0])
        nt.links.new(em.outputs[0], out.inputs[0])
    elif kind == "weight":
        # in-frame mask x image alpha as diffuse colour; bake DIFFUSE direct*color from a view-aligned sun
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = view_img; tex.extension = 'CLIP'
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(uvn.outputs[0], sep.inputs[0])
        mask = None
        for comp in ("X", "Y"):
            for op, val in (("GREATER_THAN", 0.0), ("LESS_THAN", 1.0)):
                mth = nt.nodes.new("ShaderNodeMath"); mth.operation = op; mth.inputs[1].default_value = val
                nt.links.new(sep.outputs[comp], mth.inputs[0])
                if mask is None:
                    mask = mth
                else:
                    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
                    nt.links.new(mask.outputs[0], mul.inputs[0]); nt.links.new(mth.outputs[0], mul.inputs[1])
                    mask = mul
        nt.links.new(uvn.outputs[0], tex.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
        nt.links.new(mask.outputs[0], mul.inputs[0]); nt.links.new(tex.outputs["Alpha"], mul.inputs[1])
        dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
        nt.links.new(mul.outputs[0], dif.inputs[0]); nt.links.new(dif.outputs[0], out.inputs[0])
    elif kind == "inside":
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (1, 1, 1, 1)
        nt.links.new(em.outputs[0], out.inputs[0])
    tgt = nt.nodes.new("ShaderNodeTexImage"); tgt.image = target
    nt.nodes.active = tgt
    return m

def bake(kind, target, view_img=None):
    m = material(kind, view_img, target)
    for t in temps:
        t.data.materials.clear(); t.data.materials.append(m)
    g.select_only(temps)
    if kind == "weight":
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'COLOR'}, margin=0, use_clear=True)
    else:
        bpy.ops.object.bake(type='EMIT', margin=0, use_clear=True)
    bpy.data.materials.remove(m)
    return pixels(target)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 4
sc.render.bake.margin = 0
world = sc.world or bpy.data.worlds.new("W"); sc.world = world
for n in (world.node_tree.nodes if world.node_tree else []):
    if n.type == 'BACKGROUND':
        n.inputs[1].default_value = 0.0
cam_data = bpy.data.cameras.new("__pc"); cam = bpy.data.objects.new("__pc", cam_data); tmp_coll.objects.link(cam)
sun_data = bpy.data.lights.new("__sun", 'SUN'); sun_data.energy = 1.0; sun_data.angle = 0.0
sun = bpy.data.objects.new("__sun", sun_data); tmp_coll.objects.link(sun)
sc.camera = cam

inside = bake("inside", new_image("__inside"))[:, :, 0] > 0.5
acc = np.zeros((SIZE, SIZE, 3), np.float32); wsum = np.zeros((SIZE, SIZE), np.float32)
for view, path_ in images.items():
    if view not in cams:
        g.report("FAIL", f"view '{view}' not in {a['cams']}"); sys.exit(1)
    c = cams[view]
    cam.matrix_world = Matrix(c["matrix_world"]); sun.matrix_world = Matrix(c["matrix_world"])
    cam_data.type = c["type"]; cam_data.ortho_scale = c["ortho_scale"]
    sc.render.resolution_x, sc.render.resolution_y = c["resolution"]
    vimg = bpy.data.images.load(os.path.abspath(path_), check_existing=False)
    if list(vimg.size) != list(c["resolution"]):
        g.report("WARN", f"{view}: image {tuple(vimg.size)} != render {tuple(c['resolution'])}; "
                         "aspect must match or the projection shifts")
    bpy.context.view_layer.update()
    for t in temps:                                  # projected UVs = camera-normalised coords
        me = t.data; proj = me.uv_layers["__proj"].data; mw = t.matrix_world
        for li, loop in enumerate(me.loops):
            p = world_to_camera_view(sc, cam, mw @ me.vertices[loop.vertex_index].co)
            proj[li].uv = (p.x, p.y)
    col = bake("color", new_image("__col"), vimg)[:, :, :3]
    w = bake("weight", new_image("__w"), vimg)[:, :, 0]
    w = np.clip(w / max(w.max(), 1e-6), 0, 1) ** POWER
    acc += col * w[..., None]; wsum += w
    g.report("INFO", f"{view}: sees {100 * ((w > 1e-3) & inside).sum() / max(inside.sum(), 1):.1f}% of UV area")

painted = wsum > 1e-4
lin = np.where(painted[..., None], acc / np.maximum(wsum, 1e-6)[..., None], 0)
srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.maximum(lin, 0), 1 / 2.4) - 0.055)
if "base" in a and os.path.exists(a["base"]):
    base = g.load_pixels(a["base"])[:, :, :3]
    if base.shape[:2] != (SIZE, SIZE):
        g.report("WARN", "--base size differs from --size; ignored"); base = None
else:
    base = None
fill = base if base is not None else np.broadcast_to(np.array(FILL, np.float32), (SIZE, SIZE, 3))
if base is not None and "fill-only" in a:
    cov_path = os.path.splitext(a["base"])[0] + "_coverage.png"
    if not os.path.exists(cov_path):
        g.report("FAIL", f"--fill-only needs {cov_path}"); sys.exit(1)
    prev = g.load_pixels(cov_path)
    before = (prev[..., 0] > 0.5) & (prev[..., 1] > 0.5)        # white = painted earlier
    painted_new = painted & ~before
    painted = painted | before                                  # coverage report counts both
    srgb = np.where(painted_new[..., None], srgb, base)
outimg = np.where(painted[..., None], srgb, fill)

# gutter: grow island colours outward 16 px so mips and bilinear filtering don't bleed the background
known = painted | inside
for _ in range(16):
    if known.all(): break
    pad = np.pad(outimg, ((1, 1), (1, 1), (0, 0)), mode="edge"); kp = np.pad(known, 1)
    s = np.zeros_like(outimg); n = np.zeros(known.shape, np.float32)
    for dy, dx in ((0, 1), (1, 0), (1, 2), (2, 1)):
        k = kp[dy:dy + SIZE, dx:dx + SIZE]
        s += pad[dy:dy + SIZE, dx:dx + SIZE] * k[..., None]; n += k
    grow = ~known & (n > 0)
    outimg[grow] = (s[grow] / n[grow][:, None]); known = known | grow

g.save_pixels(outimg, a["out"], "sRGB")
cov = np.zeros((SIZE, SIZE, 3), np.float32)
cov[inside & painted] = (1, 1, 1); cov[inside & ~painted] = (1, 0, 0)
g.save_pixels(cov, os.path.splitext(a["out"])[0] + "_coverage.png", "sRGB")
pct = 100 * (inside & painted).sum() / max(inside.sum(), 1)
g.report("PASS" if pct > 97 else "WARN", f"coverage {pct:.1f}% of UV area painted "
         f"({'add views or inpaint the red areas of _coverage.png' if pct <= 97 else 'ok'})")
print(f"DONE {a['out']}")
