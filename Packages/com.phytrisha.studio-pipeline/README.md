# Studio Pipeline (Unity package)

The Unity half of the blender-unity-game-studio art pipeline. In the studio repo it is an embedded package (Unity
loads `Packages/com.phytrisha.studio-pipeline/` automatically). Games made with `tools/link_project.sh` reference it
from the studio with a `file:` dependency in `Packages/manifest.json`, so every game uses one copy; games made with
`tools/new_project.sh` carry their own embedded copy.

| File | Does |
|---|---|
| `Editor/ProjectPaths.cs` | where everything lives under `Assets/` (single source of truth; no hard-coded folders anywhere) |
| `Editor/AssetImportRules.cs` | import settings by name: `SM_` static, `SK_` skinned (Humanoid/Generic and clip flags from the export manifest), `T_*_{BC,N,MS,AO,E}` textures |
| `Editor/AssetPipeline.cs` | `EnsureMaterials`, `RemapMaterials`, `MakePrefab` (LODGroup, UCX colliders, static flags), `EnsureAnimator`, `SceneProblems` |
| `Editor/ProjectSetup.cs` | one-time setup: URP asset + Forward+ renderer, linear colour, Force Text, Run In Background, Frame Timing Stats |
| `Runtime/Dev/PerfBench.cs` | player-build benchmark (`-perfbench`, views under a `PerfViews` object) |

Driven from the shell by `tools/unity_run.sh` and the eval scripts in `unity/` (import_assets, preview_asset, capture,
audit_scene, unused_assets). Rules and pitfalls: `.claude/docs/art-pipeline/unity-pipeline.md`.
Game code that lives in its own assembly definition needs a reference to `StudioPipeline.Editor` /
`StudioPipeline.Runtime` to call these classes; scripts without an asmdef see them automatically.
