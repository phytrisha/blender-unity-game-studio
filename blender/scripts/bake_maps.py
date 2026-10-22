# Bake game maps onto a low-poly's UVs with Cycles.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/bake_maps.py <Name>.blend -- --low Crate [--high Crate_high[,Bolt_high]] \
#         --maps normal,ao,curvature,id,basecolor [--size 2048] [--extrusion 0.02] [--samples 64] \
#         [--prefix T_Crate] [--outdir textures]
# --high given  -> selected-to-active (normal/AO detail from the high-poly; cage = extrusion).
# no --high     -> self bake (AO, curvature, ID, basecolor of the current materials).
# Maps: normal (OpenGL tangent space) · ao · curvature (pointiness via a temp copy; 0.5 = flat) ·
#       id (viewport colour of each material, for masks) · basecolor (current material colour) ·
#       roughness · emission. Writes <outdir>/<prefix>_<Map>.png with a 16 px margin.
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

cfg = g.config(); a = g.kv_args()
low = bpy.data.objects[a["low"]]
highs = [bpy.data.objects[n] for n in a["high"].split(",")] if "high" in a else []
SIZE = int(a.get("size", cfg["textures"]["size"]))
OUTDIR = a.get("outdir") or g.path(cfg, "textures")
PREFIX = a.get("prefix", "T_" + low.name)
MAPS = a.get("maps", "normal,ao").split(",")
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(a.get("samples", 64))
bk = sc.render.bake; bk.margin = 16; bk.margin_type = 'EXTEND'
bk.use_selected_to_active = bool(highs)
bk.cage_extrusion = float(a.get("extrusion", 0.02)); bk.max_ray_distance = float(a.get("ray", 0.0))
if not low.data.uv_layers:
    g.report("FAIL", f"{low.name} has no UVs"); sys.exit(1)

saved = [m for m in low.data.materials]
if not saved:
    low.data.materials.append(bpy.data.materials.new("M_" + low.name)); saved = list(low.data.materials)

def target_image(name, noncolor):
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    return img

def with_target(img):
    """Add an active image node to every material on the low-poly (the bake target)."""
    nodes = []
    for m in low.data.materials:
        n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = img; m.node_tree.nodes.active = n
        nodes.append((m, n))
    return nodes

def bake(kind, img, **kw):
    nodes = with_target(img)
    g.select_only(highs + [low], active=low)
    bpy.ops.object.bake(type=kind, **kw)
    for m, n in nodes:
        m.node_tree.nodes.remove(n)
    img.filepath_raw = os.path.join(OUTDIR, img.name + ".png"); img.file_format = 'PNG'; img.save()
    g.report("INFO", f"baked {img.filepath_raw}")

def id_materials():
    """Swap each material for an emission of its viewport colour; returns a restore function."""
    orig = {}
    for i, m in enumerate(low.data.materials):
        e = bpy.data.materials.new("__id_" + m.name); nt = e.node_tree; nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = m.diffuse_color
        o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], o.inputs[0])
        orig[i] = m; low.data.materials[i] = e
    def restore():
        for i, m in orig.items():
            tmp = low.data.materials[i]; low.data.materials[i] = m; bpy.data.materials.remove(tmp)
    return restore

SUFFIX = {"normal": "N", "ao": "AO", "curvature": "Curv", "id": "ID", "basecolor": "BC", "roughness": "R", "emission": "E"}
for mp in MAPS:
    name = f"{PREFIX}_{SUFFIX.get(mp, mp)}"
    if mp == "normal":
        bake('NORMAL', target_image(name, True), normal_space='TANGENT',
             normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z')
    elif mp == "ao":
        bake('AO', target_image(name, True))
    elif mp == "roughness":
        bake('ROUGHNESS', target_image(name, True))
    elif mp == "emission":
        bake('EMIT', target_image(name, False))
    elif mp == "basecolor":
        bake('DIFFUSE', target_image(name, False), pass_filter={'COLOR'})
    elif mp == "id":
        restore = id_materials(); hs = bk.use_selected_to_active; bk.use_selected_to_active = False
        hi_saved = highs[:]; highs.clear()
        bake('EMIT', target_image(name, False))
        highs.extend(hi_saved); bk.use_selected_to_active = hs
        restore()
    elif mp == "curvature":
        # Cycles' Pointiness is per-vertex: good on dense meshes, coarse on low-poly. With a
        # high-poly, bake it from the high (selected-to-active emission).
        srcs = highs or [low]
        tmp = {}
        for s in srcs:
            e = bpy.data.materials.new("__curv"); nt = e.node_tree; nt.nodes.clear()
            geo = nt.nodes.new("ShaderNodeNewGeometry"); ramp = nt.nodes.new("ShaderNodeMapRange")
            ramp.inputs[1].default_value = 0.4; ramp.inputs[2].default_value = 0.6
            em = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
            nt.links.new(geo.outputs["Pointiness"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], em.inputs[0])
            nt.links.new(em.outputs[0], o.inputs[0])
            tmp[s] = [m for m in s.data.materials]
            s.data.materials.clear(); s.data.materials.append(e)
        bake('EMIT', target_image(name, True))
        for s, mats in tmp.items():
            e = s.data.materials[0]; s.data.materials.clear()
            for m in mats: s.data.materials.append(m)
            bpy.data.materials.remove(e)
    else:
        g.report("WARN", f"unknown map {mp}")
print(f"DONE bake {PREFIX}")
