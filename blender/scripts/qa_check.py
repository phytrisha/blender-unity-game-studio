# Game-readiness checks per pipeline stage, against the budgets in asset.json.
#   ASSET=<Name> tools/blender_run.sh blender/scripts/qa_check.py <Name>.blend -- [--stage model|uv|texture|rig|anim|all] [--obj A,B]
# Prints PASS / WARN / FAIL lines, a SUMMARY line, writes out/qa_<stage>.json, exits 1 on any FAIL.
# Not detected (look at renders instead): clipping, floating parts, bad silhouettes, ugly deformation.
import bpy, bmesh, json, math, os, re, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g
from mathutils import Matrix

cfg = g.config(); a = g.kv_args()
STAGE = a.get("stage", "all")
STAGES = ["model", "uv", "texture", "rig", "anim"]
run = STAGES[:STAGES.index(STAGE) + 1] if STAGE in STAGES else STAGES
meshes = [bpy.data.objects[n] for n in a["obj"].split(",")] if "obj" in a else g.asset_objects(cfg)
B = cfg["budget"]; results = []

def rep(level, check, msg):
    results.append({"level": level, "check": check, "msg": msg}); g.report(level, f"[{check}] {msg}")

if not meshes:
    rep("FAIL", "scene", f"no meshes in collection '{cfg['collection']}'")

# ---------------------------------------------------------------- model
if "model" in run and meshes:
    total = 0
    for o in meshes:
        t = g.evaluated_tris(o); total += t
        bm = bmesh.new(); bm.from_mesh(o.data)
        ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
        nonman = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        loose_v = sum(1 for v in bm.verts if not v.link_edges)
        loose_e = sum(1 for e in bm.edges if not e.link_faces)
        degen = sum(1 for f in bm.faces if f.calc_area() < 1e-8)
        bm.free()
        flags = []
        if ngons: flags.append(f"{ngons} n-gons")
        if nonman: flags.append(f"{nonman} non-manifold edges")
        rep("WARN" if flags else "PASS", "topology", f"{o.name}: {t} tris" + (" · " + ", ".join(flags) if flags else ""))
        if loose_v or loose_e or degen:
            rep("FAIL", "topology", f"{o.name}: {loose_v} loose verts, {loose_e} loose edges, {degen} zero-area faces")
        sc = o.matrix_world.to_scale()
        if any(s < 0 for s in sc):
            rep("FAIL", "transform", f"{o.name}: negative scale {tuple(round(s, 3) for s in sc)} (flips normals on export)")
        elif any(abs(s - 1) > 1e-4 for s in o.scale):
            rep("WARN", "transform", f"{o.name}: unapplied scale {tuple(round(s, 3) for s in o.scale)}")
        for m in o.modifiers:
            if m.type == 'SUBSURF' and (m.levels > 0 or m.render_levels > 0):
                rep("WARN", "modifiers", f"{o.name}: Subdivision is live - exported tris will include it")
        if re.match(r"^(Cube|Sphere|Cylinder|Plane|Cone|Torus|Icosphere|Suzanne|Mesh)(\.\d+)?$", o.name):
            rep("WARN", "naming", f"{o.name}: default name - name it for the engine (SM_/SK_ prefix, .L/.R sides)")
        if not o.data.materials or any(s is None for s in o.data.materials):
            rep("FAIL", "materials", f"{o.name}: empty material slot")
    lvl = "PASS" if total <= B["tris"] else ("WARN" if total <= B["tris"] * 1.1 else "FAIL")
    rep(lvl, "budget", f"total {total} tris / budget {B['tris']}")
    mats = {m.name for o in meshes for m in o.data.materials if m}
    rep("PASS" if len(mats) <= B["materials"] else "WARN", "budget", f"{len(mats)} materials / budget {B['materials']}: {sorted(mats)}")
    lo, hi = g.bounds(meshes)
    if cfg.get("height_m"):
        h = hi.z - lo.z; dev = abs(h - cfg["height_m"]) / cfg["height_m"]
        rep("PASS" if dev < 0.1 else "WARN", "scale", f"height {h:.3f} m vs brief {cfg['height_m']} m")
    if abs(lo.z) > 0.01 and cfg.get("type") in ("prop", "character", "creature", "vehicle"):
        rep("WARN", "pivot", f"lowest point at z={lo.z:.3f} m - ground contact should be z=0")

# ---------------------------------------------------------------- uv
if "uv" in run:
    for o in meshes:
        n = len(o.data.uv_layers)
        if n == 0:
            rep("FAIL", "uv", f"{o.name}: no UV map"); continue
        if n > B.get("uv_maps", 2):
            rep("WARN", "uv", f"{o.name}: {n} UV maps / budget {B.get('uv_maps', 2)}")
        s = g.uv_stats(o, o.data.uv_layers[0].name, cfg["textures"]["size"], res=256)
        mode = g.uv_mode(o, cfg)
        if mode == "tiling":     # library materials: only stretch matters; density = tile size of the kit mapping
            tile = (cfg["textures"]["size"] / s["density"]) if s["density"] else 0
            rep("WARN" if s["stretch"] > 0.25 else "PASS", "uv",
                f"{o.name}: tiling UVs (MI_ materials) · {1 / tile if tile else 0:.2f} tiles/m (1 UV unit = {tile:.2f} m) · stretch {s['stretch']:.2f}")
            continue
        tgt = cfg["textures"]["texel_density"]
        lvl = "PASS"
        if s["out_of_bounds_tris"] or s["overlap"] > 0.02 or s["stretch"] > 0.25: lvl = "WARN"
        if tgt and abs(s["density"] - tgt) / tgt > 0.35: lvl = "WARN"
        rep(lvl, "uv", f"{o.name}: unique UVs · {s['density']:.0f} px/m (target {tgt}) · overlap {100 * s['overlap']:.1f}% "
                       f"(fine if mirrored on purpose) · out-of-0-1 tris {s['out_of_bounds_tris']} · stretch {s['stretch']:.2f} · used {100 * s['utilisation']:.0f}%")

# ---------------------------------------------------------------- texture
if "texture" in run:
    seen = set()
    for o in meshes:
        for m in o.data.materials:
            if m is None or m.name in seen: continue
            seen.add(m.name)
            imgs = [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
            if not imgs:
                rep("WARN", "texture", f"{m.name}: no image textures (fine for flat-colour styles)")
            for n in imgs:
                im = n.image; w, h = im.size
                fp = bpy.path.abspath(im.filepath)
                issues = []
                if im.packed_file is None and not os.path.exists(fp): issues.append(f"missing file {fp}")
                if w & (w - 1) or h & (h - 1): issues.append(f"not power of two {w}x{h}")
                if max(w, h) > cfg["textures"]["size"]: issues.append(f"{w}px > budget {cfg['textures']['size']}")
                stem = os.path.splitext(im.name)[0]
                suffix = stem.rsplit("_", 1)[-1] if "_" in stem else ""
                if not stem.startswith("T_") or suffix not in ("BC", "N", "MS", "AO", "E", "H", "ORM", "Mask", "Curv", "ID"):
                    issues.append("not Unity-named T_<Stem>_{BC,N,MS,AO,E,H,Mask} (AssetPipeline won't wire it)")
                data_map = suffix in ("N", "MS", "AO", "H", "ORM", "Mask", "Curv", "ID")
                if data_map and im.colorspace_settings.name != 'Non-Color': issues.append("data map not Non-Color")
                if not data_map and im.colorspace_settings.name == 'Non-Color': issues.append("colour map set to Non-Color")
                rep("WARN" if issues else "PASS", "texture", f"{m.name}/{im.name} {w}x{h}" + (" · " + "; ".join(issues) if issues else ""))

# ---------------------------------------------------------------- rig
if "rig" in run:
    arm = g.armature(cfg)
    if arm is None:
        rep("INFO" if not B.get("bones") else "FAIL", "rig", "no armature")
    else:
        I = Matrix.Identity(4)
        nonrest = [pb.name for pb in arm.pose.bones if any(abs(pb.matrix_basis[i][j] - I[i][j]) > 1e-4 for i in range(4) for j in range(4))]
        rep("FAIL" if nonrest else "PASS", "rig", f"rest pose: {len(nonrest)} posed bones {nonrest[:6]}"
            + (" (an action may be assigned: check at a frame with no keys or clear the pose before saving)" if nonrest else ""))
        deform = [b.name for b in arm.data.bones if b.use_deform]
        rep("PASS" if len(deform) <= B.get("bones", 999) else "WARN", "rig", f"{len(deform)} deform bones / budget {B.get('bones')}")
        roots = [b.name for b in arm.data.bones if b.parent is None and b.use_deform]
        if len(roots) > 1:
            rep("WARN", "rig", f"{len(roots)} root deform bones {roots[:5]} - engines want one root")
        if any(abs(s - 1) > 1e-4 for s in arm.scale):
            rep("WARN", "rig", f"armature object scale {tuple(arm.scale)} - apply before export")
        maxinf = B.get("influences", 4)
        for o in meshes:
            mod = next((m for m in o.modifiers if m.type == 'ARMATURE' and m.object == arm), None)
            if mod is None:
                rep("WARN", "skin", f"{o.name}: not bound to {arm.name} (fine for props that are parented to a bone)"); continue
            names = {vg.index: vg.name for vg in o.vertex_groups}
            stray = [n for n in names.values() if n not in deform]
            unweighted = over = unnorm = 0
            for v in o.data.vertices:
                ws = [ge.weight for ge in v.groups if names.get(ge.group) in deform and ge.weight > 1e-3]
                if not ws: unweighted += 1
                if len(ws) > maxinf: over += 1
                if ws and abs(sum(ws) - 1) > 0.01: unnorm += 1
            lvl = "FAIL" if unweighted else ("WARN" if over or unnorm else "PASS")
            rep(lvl, "skin", f"{o.name}: {unweighted} unweighted verts · {over} verts > {maxinf} influences · "
                             f"{unnorm} not normalised" + (f" · groups without deform bone {stray[:5]}" if stray else ""))

# ---------------------------------------------------------------- anim
if "anim" in run:
    want = {x["name"]: x for x in cfg.get("animations", [])}
    have = {act.name: act for act in bpy.data.actions}
    for n in want:
        if n not in have:
            rep("FAIL", "anim", f"missing action '{n}' from asset.json")
    for n, act in have.items():
        if n.startswith("__"): continue
        fr = act.frame_range; fcs = g.fcurves(act); spec = want.get(n, {})
        lvl = "PASS"; notes = []
        if not act.use_fake_user and act.users == 0:
            lvl = "WARN"; notes.append("no users and no fake user - it will be lost on save")
        if spec.get("loop"):
            # convention: exported range is start..end, and frame end+1 repeats the start pose
            s0, s1 = (spec["frames"][0], spec["frames"][1] + 1) if spec.get("frames") else (fr[0], fr[1])
            worst = 0.0
            for fc in fcs:
                if len(fc.keyframe_points) < 2: continue
                worst = max(worst, abs(fc.evaluate(s0) - fc.evaluate(s1)))
            if worst > 1e-3:
                lvl = "WARN"; notes.append(f"loop not closed (max channel jump {worst:.4f} between frame {s0:.0f} and {s1:.0f})")
            if not act.use_cyclic:
                notes.append("use_cyclic off (engines ignore it, but Blender previews will hitch)")
        if spec.get("frames") and [round(x) for x in fr] != spec["frames"]:
            notes.append(f"range {tuple(round(x) for x in fr)} vs asset.json {spec['frames']}")
        rep(lvl, "anim", f"{n}: frames {fr[0]:.0f}-{fr[1]:.0f}, {len(fcs)} curves" + (" · " + "; ".join(notes) if notes else ""))

fails = sum(r["level"] == "FAIL" for r in results); warns = sum(r["level"] == "WARN" for r in results)
print(f"SUMMARY stage={STAGE} fail={fails} warn={warns} pass={sum(r['level'] == 'PASS' for r in results)}")
with open(g.path(cfg, "out", f"qa_{STAGE}.json"), "w") as f:
    json.dump(results, f, indent=1)
sys.exit(1 if fails else 0)
