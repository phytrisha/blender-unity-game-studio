# gamelib.py: shared helpers for the tool scripts in blender/scripts/ (render_views, project_paint, qa_check,
# uv_tools, bake_maps, build_material, game_skeleton, weights, anim_tools, export_skinned). Run them through
# tools/blender_run.sh, which sets BLENDER_LIB, ROOT and (with ASSET=<Name>) ASSET_JSON:
#   import sys, os; sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/lib")
#   import gamelib as g
# The step-script libs (kit/export/audit/review) are separate: they are prepended to build.py-style scripts.
import bpy, bmesh, json, os, sys
from mathutils import Vector

# ---------------------------------------------------------------- config (blender/assets/<Name>/asset.json)
DEFAULTS = {
    "name": "Asset",
    "category": "Props",                     # Props | Buildings | Nature | Characters  (= blender/export/<Category>/)
    "type": "prop",
    "engine": "unity",
    "collection": None,                      # default SM_<name>, or SK_<name> for Characters
    "budget": {"tris": 5000, "materials": 2, "bones": 0, "influences": 4, "uv_maps": 2},
    "textures": {"size": 2048, "texel_density": 512},
    "lods": [0.5, 0.25],
    "rig": {"armature": None, "skeleton": "unity-humanoid"},
    "animations": [],
}

def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out

def root():
    """Studio repo root: $ROOT (set by tools/blender_run.sh), else two levels above blender/lib."""
    return os.environ.get("ROOT") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def config():
    """asset.json merged over DEFAULTS. Looks at $ASSET_JSON, then blender/assets/$ASSET/asset.json, then ./asset.json.
    cfg["_root"] = the asset folder (or the studio root when no asset.json exists)."""
    cands = [os.environ.get("ASSET_JSON"),
             os.path.join(root(), "blender", "assets", os.environ["ASSET"], "asset.json") if os.environ.get("ASSET") else None,
             os.path.join(os.getcwd(), "asset.json")]
    p = next((c for c in cands if c and os.path.exists(c)), None)
    if p:
        with open(p) as f:
            cfg = _merge(DEFAULTS, json.load(f))
        cfg["_root"] = os.path.dirname(os.path.abspath(p))
    else:
        cfg = _merge(DEFAULTS, {"name": os.environ.get("ASSET", "Asset")})
        cfg["_root"] = os.path.join(root(), "blender", "assets", cfg["name"]) if os.environ.get("ASSET") else root()
    if not cfg.get("collection"):
        cfg["collection"] = ("SK_" if cfg["category"] == "Characters" else "SM_") + cfg["name"]
    cfg["paths"] = {"textures": os.path.join(cfg["_root"], "textures"),
                    "out": os.path.join(root(), "renders", cfg["name"]),
                    "export": os.path.join(root(), "blender", "export", cfg["category"], cfg["name"]),
                    **cfg.get("paths", {})}
    return cfg

def path(cfg, key, *rest):
    """Absolute path for cfg['paths'][key] (textures | out | export) joined with rest; creates the directory.
    Relative entries in asset.json "paths" are relative to the asset folder."""
    d = cfg["paths"].get(key, key)
    d = d if os.path.isabs(d) else os.path.join(cfg["_root"], d)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *rest)

def args():
    """Script arguments after the '--' separator."""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def kv_args(argv=None):
    """--key value / --flag pairs into a dict (values stay strings)."""
    argv = args() if argv is None else argv
    out, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                out[a[2:]] = argv[i + 1]; i += 2; continue
            out[a[2:]] = True
        i += 1
    return out

# ---------------------------------------------------------------- scene
def asset_collection(cfg):
    c = bpy.data.collections.get(cfg["collection"])
    if c is None:
        c = bpy.data.collections.new(cfg["collection"])
        bpy.context.scene.collection.children.link(c)
    return c

def sub_collection(cfg, name, clear=True):
    """Sub-collection of the asset collection. clear=True deletes its objects (idempotent part scripts)."""
    root = asset_collection(cfg)
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name); root.children.link(c)
    if clear:
        for o in list(c.objects):
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data is not None and data.users == 0 and isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
    return c

def asset_objects(cfg, types=("MESH",)):
    root = bpy.data.collections.get(cfg["collection"])
    objs = root.all_objects if root else bpy.context.scene.objects
    shapes = {pb.custom_shape for o in bpy.data.objects if o.type == 'ARMATURE'
              for pb in o.pose.bones if pb.custom_shape}          # rig widgets are not asset geometry
    return [o for o in objs if o.type in types and o not in shapes and not o.name.startswith(("WGT-", "__"))]

def armature(cfg):
    name = (cfg.get("rig") or {}).get("armature")
    if name and name in bpy.data.objects:
        return bpy.data.objects[name]
    arms = asset_objects(cfg, ("ARMATURE",))
    return arms[0] if arms else None

def evaluated_tris(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    t = sum(len(p.vertices) - 2 for p in me.polygons)
    ev.to_mesh_clear()
    return t

def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    if not pts:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi

def select_only(objs, active=None):
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        if o is not None:
            o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or (objs[0] if objs else None)

def save(path_=None):
    """Save the open file (or save-as path_; an unsaved scene goes to blender/assets/<Name>/<Name>.blend).
    Refuses to write into sources/ or an input/ directory (read-only inputs)."""
    cfg = config()
    p = path_ or bpy.data.filepath or os.path.join(cfg["_root"], cfg["name"] + ".blend")
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    ap = os.path.abspath(p)
    if (os.sep + "input" + os.sep in ap or ap.startswith(os.path.join(root(), "sources") + os.sep)
            or ap.startswith(os.path.join(root(), "blender", "bases") + os.sep)):
        raise RuntimeError(f"refusing to save into a read-only folder (inputs / base templates): {p}")
    bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)

# ---------------------------------------------------------------- UVs
def uv_mode(o, cfg):
    """'tiling' or 'unique' for an object's UV0. Tiling = shared library materials (MI_*) mapped in metres per tile
    by the kit: coordinates past 0-1 and overlaps are intended, density is the tile size. Unique = an atlas for the
    asset's own maps (M_*, baked, projected): 0-1, no overlap, density vs textures.texel_density.
    asset.json textures.uv_mode ('tiling' | 'unique') overrides; otherwise derived from the material names."""
    forced = cfg.get("textures", {}).get("uv_mode")
    if forced in ("tiling", "unique"):
        return forced
    mats = [m.name for m in o.data.materials if m]
    return "tiling" if mats and all(n.startswith("MI_") for n in mats) else "unique"

def uv_stats(o, uv_name=None, tex_size=2048, res=512):
    """Texel density (px/m at tex_size), 0-1 utilisation, overlap and out-of-bounds fractions.
    Overlap = share of used UV area covered by more than one face (mirrored/stacked islands count)."""
    import numpy as np
    me = o.data
    uvl = me.uv_layers.get(uv_name) if uv_name else me.uv_layers.active
    if uvl is None:
        return None
    mw = o.matrix_world
    grid = np.zeros((res, res), np.uint16)
    area3d = area_uv = 0.0; oob = 0; ratios = []; weights = []
    for p in me.polygons:
        fa3 = fau = 0.0
        idx = list(p.loop_indices)
        uvs = [uvl.data[i].uv.copy() for i in idx]
        vs = [mw @ me.vertices[me.loops[i].vertex_index].co for i in idx]
        for k in range(1, len(idx) - 1):                 # fan triangulation
            a, b, c = uvs[0], uvs[k], uvs[k + 1]
            A, B, C = vs[0], vs[k], vs[k + 1]
            a3 = ((B - A).cross(C - A)).length / 2
            au = abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
            area3d += a3; area_uv += au; fa3 += a3; fau += au
            if min(a.x, b.x, c.x) < -1e-4 or min(a.y, b.y, c.y) < -1e-4 or max(a.x, b.x, c.x) > 1.0001 or max(a.y, b.y, c.y) > 1.0001:
                oob += 1
            # rasterise into the coverage grid (texel centres inside the triangle)
            xs = np.array([a.x, b.x, c.x]) * res; ys = np.array([a.y, b.y, c.y]) * res
            x0, x1 = max(int(xs.min()), 0), min(int(np.ceil(xs.max())), res)
            y0, y1 = max(int(ys.min()), 0), min(int(np.ceil(ys.max())), res)
            if x1 <= x0 or y1 <= y0 or au <= 0:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            l1 = ((ys[1] - ys[2]) * (X - xs[2]) + (xs[2] - xs[1]) * (Y - ys[2])) / d
            l2 = ((ys[2] - ys[0]) * (X - xs[2]) + (xs[0] - xs[2]) * (Y - ys[2])) / d
            inside = (l1 >= 0) & (l2 >= 0) & (1 - l1 - l2 >= 0)
            grid[y0:y1, x0:x1] += inside.astype(np.uint16)
        if fa3 > 1e-12:
            ratios.append((fau / fa3) ** 0.5); weights.append(fa3)
    used = (grid > 0).sum()
    # stretch: area-weighted spread of per-face density (0 = uniform; > 0.25 shows on a checker)
    r = np.array(ratios); w = np.array(weights)
    mean = (r * w).sum() / max(w.sum(), 1e-12) if len(r) else 0.0
    stretch = float(((((r - mean) ** 2) * w).sum() / max(w.sum(), 1e-12)) ** 0.5 / mean) if mean > 0 else 0.0
    return {"uv": uvl.name, "density": (tex_size * (area_uv / area3d) ** 0.5) if area3d > 0 else 0.0,
            "utilisation": used / res / res, "overlap": float((grid > 1).sum()) / max(used, 1),
            "out_of_bounds_tris": oob, "area_m2": area3d, "stretch": stretch}

# ---------------------------------------------------------------- animation (Blender 4.4+ slotted actions)
def channelbag(action, slot=None, create=False):
    """FCurve container for an action slot. Blender 5.x has no action.fcurves."""
    if not action.layers:
        if not create:
            return None
        layer = action.layers.new("Layer"); layer.strips.new(type='KEYFRAME')
    strip = action.layers[0].strips[0]
    slot = slot or (action.slots[0] if action.slots else None)
    if slot is None:
        return None
    cb = strip.channelbag(slot)
    if cb is None and create:
        cb = strip.channelbag(slot, ensure=True)
    return cb

def fcurves(action):
    """All F-curves of every slot of an action."""
    out = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out

# ---------------------------------------------------------------- images (Blender's Python has numpy, not PIL)
def load_pixels(filepath):
    """(H, W, 4) float32 array, linear for non-colour data as stored."""
    import numpy as np
    img = bpy.data.images.load(filepath, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)

def save_pixels(arr, filepath, colorspace="sRGB"):
    """Write an (H, W, 3|4) float array as PNG (or by extension). colorspace: 'sRGB' or 'Non-Color'."""
    import numpy as np
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones((h, w, 1), arr.dtype)], axis=2)
    img = bpy.data.images.new(os.path.basename(filepath), w, h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = filepath
    img.file_format = {".png": "PNG", ".jpg": "JPEG", ".tga": "TARGA", ".exr": "OPEN_EXR"}.get(
        os.path.splitext(filepath)[1].lower(), "PNG")
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    img.save()
    bpy.data.images.remove(img)

def report(level, msg):
    """Uniform machine-greppable output: PASS / WARN / FAIL / INFO lines."""
    print(f"{level:4s} {msg}")
