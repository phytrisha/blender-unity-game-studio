# Assets layout

First-party content lives in five folders, grouped by what an asset is, not by when it was made. Third-party content goes in
`ThirdParty/<Vendor>/` (or `Packages/`), never into these folders.

| Folder | Contents |
|---|---|
| `Art/Environment/{Buildings,Props,Nature}/<Name>/` | `SM_<Name>.fbx` + LODs + `PF_<Name>.prefab` (synced from Blender) |
| `Art/Environment/Terrain/` | terrain data, `Layers/`, `Textures/`, `Source/` (read-only originals) |
| `Art/Characters/<Name>/` | `SK_` model, `PF_` prefab, `AC_` animator, `M_` material, `Textures/` |
| `Art/Materials/{Surfaces,Foliage,Cloth,Emissive}/` | shared material library (`MI_*`; same names as in Blender) |
| `Art/Textures/{Surfaces,Foliage,Utility}/`, `Art/VFX/` | texture sets, effects |
| `Shaders/` | custom shaders and their includes |
| `Scripts/{Runtime,Rendering,Editor}/` | game code, URP renderer features, the game's own editor tools |
| `Tests/{EditMode,PlayMode}/` | NUnit tests (`/test-setup`) |
| `Scenes/` | scenes; `Sandbox/` for experiments |
| `Settings/{Rendering,PostProcessing,Lighting,Input,Data}/` | pipeline assets, volume profiles, lighting settings, input actions, data assets |

Rules: scripts find assets through `ProjectPaths`, never hard-coded folders; move/rename/delete only inside Unity; no
screenshots or scratch files in Assets. The pipeline's editor code (`ProjectPaths`, `AssetImportRules`, `AssetPipeline`,
`ProjectSetup`, `PerfBench`) is the package `com.phytrisha.studio-pipeline`, not part of `Assets/`.
Full rules: `.claude/docs/art-pipeline/unity-project-structure.md`.
