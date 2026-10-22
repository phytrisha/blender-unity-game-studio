# Unwrap, normalise texel density, pack, and check UVs for game assets.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/uv_tools.py <Name>.blend -- check  [--obj A,B] [--uv UVMap]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/uv_tools.py <Name>.blend -- unwrap --method angle|smart [--angle 60] [--obj A,B] [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/uv_tools.py <Name>.blend -- pack   [--density 512] [--margin 0.004] [--obj A,B] [--save]
#   ASSET=<Name> tools/blender_run.sh blender/scripts/uv_tools.py <Name>.blend -- lightmap [--obj A,B] [--save]      (adds non-overlapping UV2 "UVLightmap"; export.py makes one for static meshes anyway)
# unwrap angle: marks seams on edges sharper than --angle (and existing sharp/seam edges), then
#   angle-based unwrap. Good default for hard-surface. Organic: mark seams by hand-picked edge loops
#   (see .claude/docs/art-pipeline/uv-unwrapping.md) then `unwrap --method seams`. smart: Smart UV Project (fast, more islands).
# pack: all listed objects share ONE 0-1 space (atlas). With --density, islands are scaled to that
#   px/m at textures.size first and packed without rescaling; if they don't fit it says so.
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

cfg = g.config(); argv = g.args(); mode = argv[0] if argv else "check"; a = g.kv_args(argv[1:])
objs = [bpy.data.objects[n] for n in a["obj"].split(",")] if "obj" in a else g.asset_objects(cfg)
TEX = int(a.get("size", cfg["textures"]["size"]))

def edit(objs_):
    g.select_only(objs_); bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE'); bpy.ops.mesh.select_all(action='SELECT')

def obj_mode():
    bpy.ops.object.mode_set(mode='OBJECT')

def report_all():
    worst = "PASS"
    for o in objs:
        s = g.uv_stats(o, a.get("uv"), TEX)
        if s is None:
            g.report("FAIL", f"{o.name}: no UV map"); worst = "FAIL"; continue
        if g.uv_mode(o, cfg) == "tiling" and s["uv"] != "UVLightmap":
            tile = cfg["textures"]["size"] / s["density"] if s["density"] else 0
            lvl = "WARN" if s["stretch"] > 0.25 else "PASS"
            g.report(lvl, f"{o.name} [{s['uv']}] tiling (MI_ materials): 1 UV unit = {tile:.2f} m · stretch {s['stretch']:.2f}")
            if lvl != "PASS" and worst == "PASS": worst = lvl
            continue
        target = cfg["textures"]["texel_density"]
        lvl = "PASS"
        if s["overlap"] > 0.02: lvl = "WARN"
        if s["out_of_bounds_tris"]: lvl = "WARN"
        if s["stretch"] > 0.25: lvl = "WARN"
        if target and s["uv"] != "UVLightmap" and abs(s["density"] - target) / target > 0.35: lvl = "WARN"
        g.report(lvl, f"{o.name} [{s['uv']}] density {s['density']:.0f} px/m (target {target}) · "
                      f"used {100 * s['utilisation']:.0f}% · overlap {100 * s['overlap']:.1f}% · "
                      f"out-of-0-1 tris {s['out_of_bounds_tris']} · stretch {s['stretch']:.2f}"
                      + (" (closed tube/shell without a seam? mark one, or --method smart)" if s["stretch"] > 0.25 else ""))
        if lvl != "PASS" and worst == "PASS": worst = lvl
    return worst

if mode == "check":
    report_all()
elif mode == "unwrap":
    method = a.get("method", "angle")
    for o in objs:
        if not o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    edit(objs)
    if method == "smart":
        bpy.ops.uv.smart_project(angle_limit=math.radians(float(a.get("angle", 66))), island_margin=0.01)
    else:
        if method == "angle":
            obj_mode()
            lim = math.radians(float(a.get("angle", 60)))
            for o in objs:
                bm = bmesh.new(); bm.from_mesh(o.data)
                for e in bm.edges:
                    if e.is_boundary or not e.smooth or (len(e.link_faces) == 2 and e.calc_face_angle(0) > lim):
                        e.seam = True
                bm.to_mesh(o.data); bm.free()
            edit(objs)
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.01)
    obj_mode()
    report_all()
elif mode == "pack":
    margin = float(a.get("margin", 4 / TEX))
    edit(objs)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    dens = a.get("density")
    obj_mode()
    if dens:
        # scale every UV about the origin so the measured density hits the target, then pack unscaled
        cur = [g.uv_stats(o, None, TEX, res=64) for o in objs]
        area3d = sum(s["area_m2"] for s in cur)
        avg = sum(s["density"] * s["area_m2"] for s in cur) / max(area3d, 1e-9)
        f = float(dens) / max(avg, 1e-9)
        for o in objs:
            for d in o.data.uv_layers.active.data:
                d.uv = d.uv * f
        edit(objs); bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=True, margin=margin, scale=False, shape_method='CONCAVE')
        obj_mode()
        oob = sum(g.uv_stats(o, None, TEX, res=64)["out_of_bounds_tris"] for o in objs)
        if oob:
            g.report("WARN", f"islands at {dens} px/m don't fit one {TEX} map ({oob} tris outside 0-1): "
                             "lower the density, raise textures.size, or split into a second material")
    else:
        edit(objs); bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(rotate=True, margin=margin, shape_method='CONCAVE')
        obj_mode()
    report_all()
elif mode == "lightmap":
    for o in objs:
        uvl = o.data.uv_layers.get("UVLightmap") or o.data.uv_layers.new(name="UVLightmap")
        o.data.uv_layers.active = uvl
    edit(objs)
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.02)
    obj_mode()
    for o in objs:
        o.data.uv_layers.active = o.data.uv_layers[0]
        o.data.uv_layers[0].active_render = True
    a["uv"] = "UVLightmap"; report_all()
else:
    g.report("FAIL", "mode: check | unwrap | pack | lightmap"); sys.exit(2)
if "save" in a and mode != "check":
    g.save()
print(f"DONE uv {mode}")
