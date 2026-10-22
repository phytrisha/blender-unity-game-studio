// Import settings for everything the Blender/Tripo pipeline drops into Assets/Art, applied automatically on import,
// so no asset needs hand-tuning in the Inspector and re-exports keep the same settings.
//
//   SM_*.fbx   static meshes: file scale, normals + tangents imported (authored in Blender), no generated lightmap UVs
//              (UV1 "UVLightmap" comes from Blender), materials remapped by name onto existing project materials
//   SK_*.fbx   skinned characters: same mesh rules, Humanoid avatar from the model (Unity/Mixamo-style bone names map
//              automatically), clips named after their take. Clip flags come from the export manifest SK_<Name>.json
//              next to the FBX (blender/scripts/export_skinned.py: loop, root motion, events); without one,
//              Idle*/Walk*/Run* loop (Tripo/Mixamo files)
//   T_*        textures: *_N normal map, *_BC / *_E sRGB, everything else linear (ORM, MS, AO, H, Mask)
// Rules for new asset types belong here, not in one-off scripts.
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public class AssetImportRules : AssetPostprocessor
{
    static bool InArt(string path) => path.StartsWith(ProjectPaths.Art + "/");

    void OnPreprocessModel()
    {
        if (!InArt(assetPath)) return;
        var name = Path.GetFileNameWithoutExtension(assetPath);
        if (!name.StartsWith("SM_") && !name.StartsWith("SK_")) return;
        var mi = (ModelImporter)assetImporter;
        mi.globalScale = 1f; mi.useFileScale = true;
        mi.bakeAxisConversion = false;                 // keep the root rotation: prefab code must not reset it either
        mi.importNormals = ModelImporterNormals.Import;
        mi.importTangents = ModelImporterTangents.Import;
        mi.generateSecondaryUV = false;
        mi.meshCompression = ModelImporterMeshCompression.Off;
        mi.isReadable = false;
        mi.importCameras = false; mi.importLights = false;
        mi.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
        mi.materialLocation = ModelImporterMaterialLocation.InPrefab;
        mi.indexFormat = ModelImporterIndexFormat.Auto;
        if (name.StartsWith("SM_"))
        {
            mi.importAnimation = false;
            mi.animationType = ModelImporterAnimationType.None;
        }
        else
        {
            // Humanoid unless the export manifest says otherwise (asset.json rig.skeleton, written by
            // export_skinned.py): "unity-humanoid" -> Human, anything else (creatures, props) -> Generic.
            // No manifest (Tripo / Mixamo files) -> Human, the Mixamo bone names map automatically.
            var man = ReadManifest(assetPath);
            bool human = man == null || string.IsNullOrEmpty(man.skeleton) || man.skeleton == "unity-humanoid";
            mi.animationType = human ? ModelImporterAnimationType.Human : ModelImporterAnimationType.Generic;
            mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            mi.importAnimation = true;
        }
    }

    void OnPostprocessModel(GameObject root)
    {
        if (!InArt(assetPath)) return;
        var mi = (ModelImporter)assetImporter;
        // remap embedded materials onto project materials of the same name (the Blender material name IS the Unity name)
        bool changed = false;
        foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            foreach (var m in r.sharedMaterials)
            {
                if (!m) continue;
                var path = ProjectPaths.Find(m.name + ".mat");
                if (path == null) continue;
                var id = new AssetImporter.SourceAssetIdentifier(typeof(Material), m.name);
                var lib = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (lib && (!mi.GetExternalObjectMap().TryGetValue(id, out var cur) || cur != lib))
                { mi.AddRemap(id, lib); changed = true; }
            }
        if (changed) EditorApplication.delayCall += () => { mi.SaveAndReimport(); };
        // UCX_ hulls are collision only
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
            if (r.name.StartsWith("UCX_")) r.enabled = false;
    }

    [System.Serializable] class ClipEvent { public string name; public int frame; }
    [System.Serializable] class ClipSpec { public string name; public int first; public int last; public bool loop; public bool rootMotion; public ClipEvent[] events; }
    [System.Serializable] class SkinnedManifest { public float fps = 30; public string skeleton; public ClipSpec[] clipList; }

    /// <summary>The export manifest next to an SK_ model (SK_Guard.fbx -> SK_Guard.json), or null.</summary>
    static SkinnedManifest ReadManifest(string modelPath)
    {
        var p = Path.ChangeExtension(modelPath, ".json");
        if (!File.Exists(p)) return null;
        try { return JsonUtility.FromJson<SkinnedManifest>(File.ReadAllText(p)); } catch { return null; }
    }

    void OnPreprocessAnimation()
    {
        if (!InArt(assetPath) || !Path.GetFileName(assetPath).StartsWith("SK_")) return;
        var mi = (ModelImporter)assetImporter;
        var man = ReadManifest(assetPath);
        var clips = mi.defaultClipAnimations;
        foreach (var c in clips)
        {
            var n = c.takeName.Contains("|") ? c.takeName.Split('|').Last() : c.takeName;
            c.name = n;
            var spec = man?.clipList?.FirstOrDefault(x => x.name == n);
            bool loop = spec != null ? spec.loop : n.StartsWith("Idle") || n.StartsWith("Walk") || n.StartsWith("Run");
            bool rootMotion = spec != null ? spec.rootMotion : n.StartsWith("Walk") || n.StartsWith("Run");
            c.loopTime = loop;
            c.lockRootRotation = true; c.lockRootHeightY = true;
            c.lockRootPositionXZ = !rootMotion;
            c.keepOriginalOrientation = true; c.keepOriginalPositionY = true;
            if (spec?.events != null && spec.events.Length > 0 && spec.last > spec.first)
                c.events = spec.events.Select(e => new AnimationEvent
                {
                    functionName = e.name,
                    time = Mathf.Clamp01((e.frame - spec.first) / (float)(spec.last - spec.first)),   // normalised clip time
                }).ToArray();
        }
        mi.clipAnimations = clips;
    }

    void OnPreprocessTexture()
    {
        if (!InArt(assetPath)) return;
        var name = Path.GetFileNameWithoutExtension(assetPath);
        if (!name.StartsWith("T_")) return;
        var ti = (TextureImporter)assetImporter;
        ti.mipmapEnabled = true; ti.anisoLevel = 4; ti.filterMode = FilterMode.Trilinear;
        ti.textureCompression = TextureImporterCompression.CompressedHQ;
        if (name.EndsWith("_N")) { ti.textureType = TextureImporterType.NormalMap; return; }
        ti.textureType = TextureImporterType.Default;
        ti.sRGBTexture = name.EndsWith("_BC") || name.EndsWith("_E");
        if (ti.DoesSourceTextureHaveAlpha() && name.EndsWith("_BC"))
        {   // alpha-cut sprites (leaves, decals): keep coverage in the mips so they don't thin out with distance
            ti.alphaIsTransparency = true; ti.mipMapsPreserveCoverage = true; ti.alphaTestReferenceValue = 0.5f;
        }
    }
}
