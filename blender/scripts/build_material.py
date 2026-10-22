# Build (or rebuild) a URP-ready Principled material from a Unity-named texture set and assign it.
# Idempotent: re-running replaces the node tree. Texture work ships as files + a scripts call of this, so it can be
# re-applied to the rigged file and never has to share a .blend with the rigger.
#   tools/blender_run.sh blender/scripts/build_material.py blender/assets/Crate/Crate.blend -- --mat M_Crate \
#         --obj SM_Crate_Body[,SM_Crate_Lid] --bc T_Crate_BC.png [--n T_Crate_N.png] [--ms T_Crate_MS.png]
#         [--ao T_Crate_AO.png] [--e T_Crate_E.png] [--alpha clip|blend] [--save]
# Unity contract (Packages/com.phytrisha.studio-pipeline/Editor/AssetPipeline.EnsureMaterials): the Unity material gets the same name and
# finds T_<Stem>_{BC,N,MS,AO,E}.png by the stem of the material name (M_Crate -> Crate, MI_Wood -> Wood).
# _MS = URP Lit Metallic map: R metallic, A smoothness. Normal maps are OpenGL (+Y) for Blender and Unity alike.
import bpy, os, sys
sys.path.insert(0, os.environ.get("BLENDER_LIB") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import gamelib as g

a = g.kv_args()
if "mat" not in a:
    g.report("FAIL", "missing --mat"); sys.exit(2)
m = bpy.data.materials.get(a["mat"]) or bpy.data.materials.new(a["mat"])
nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (600, 0)
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (250, 0)
nt.links.new(bsdf.outputs[0], out.inputs[0])

def tex(path_, colorspace, y):
    if not os.path.exists(path_):
        g.report("FAIL", f"missing texture {path_}"); sys.exit(1)
    n = nt.nodes.new("ShaderNodeTexImage"); n.location = (-500, y)
    n.image = bpy.data.images.load(os.path.abspath(path_), check_existing=True)
    n.image.colorspace_settings.name = colorspace
    return n

bc = a.get("bc") or a.get("basecolor")
if bc:
    t = tex(bc, "sRGB", 300); nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if a.get("alpha") in ("clip", "blend"):
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = 'DITHERED' if a["alpha"] == "clip" else 'BLENDED'
if "ms" in a:   # R = metallic, A = smoothness
    t = tex(a["ms"], "Non-Color", 0); sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (-200, 0)
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; inv.location = (-50, -60)
    nt.links.new(t.outputs["Color"], sep.inputs[0]); nt.links.new(sep.outputs[0], bsdf.inputs["Metallic"])
    nt.links.new(t.outputs["Alpha"], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
n = a.get("n") or a.get("normal")
if n:
    t = tex(n, "Non-Color", -300); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-200, -300)
    nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
if "ao" in a:   # Blender's Principled has no AO input: kept on the node tree for reference/baking, Unity uses it
    t = tex(a["ao"], "Non-Color", -450); t.label = "AO (Unity _OcclusionMap)"
e = a.get("e") or a.get("emission")
if e:
    t = tex(e, "sRGB", -600)
    nt.links.new(t.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = 1.0
for name in a.get("obj", "").split(","):
    if not name: continue
    o = bpy.data.objects.get(name)
    if o is None:
        g.report("WARN", f"no object {name}"); continue
    o.data.materials.clear(); o.data.materials.append(m)
if "save" in a:
    g.save()
print(f"DONE material {m.name}")
