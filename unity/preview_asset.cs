// Stage prefabs in a review scene for unity/capture.cs: Scenes/Sandbox/Preview.unity is rebuilt from scratch (sun,
// grey ground, MainCamera, the prefabs side by side along +X with 1 m gaps) and saved. Optional pose lines sample an
// animation clip on a placed character at a normalised time, so a capture shows the clip instead of the bind pose.
// Args (unity/args/preview_asset.txt), one per line:
//   Props Crate                 place PF_Crate (category as in tools/sync_to_unity.sh)
//   Characters Hero             place PF_Hero
//   pose Hero Wave 0.5          sample clip "Wave" (from SK_Hero.fbx) on Hero at 50 %
// Returns one line per placed prefab (position, bounds size) and per pose, then "PREVIEW saved <scene>".
// Shot list for capture.cs: the returned "shot" lines frame the whole row (front, three-quarter, side). Unity assets
// face +Z (Blender's -Y front after export), so the front camera stands on the +Z side looking back at them.
var args = ARGS;
var log = new System.Text.StringBuilder();
var scene = UnityEditor.SceneManagement.EditorSceneManager.NewScene(UnityEditor.SceneManagement.NewSceneSetup.EmptyScene, UnityEditor.SceneManagement.NewSceneMode.Single);
var sun = new UnityEngine.GameObject("Sun").AddComponent<UnityEngine.Light>();
sun.type = UnityEngine.LightType.Directional; sun.intensity = 1.2f; sun.shadows = UnityEngine.LightShadows.Soft;
sun.transform.rotation = UnityEngine.Quaternion.Euler(45f, -35f, 0f);
UnityEngine.RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
UnityEngine.RenderSettings.ambientSkyColor = new UnityEngine.Color(0.55f, 0.6f, 0.7f);
UnityEngine.RenderSettings.ambientEquatorColor = new UnityEngine.Color(0.4f, 0.4f, 0.42f);
UnityEngine.RenderSettings.ambientGroundColor = new UnityEngine.Color(0.2f, 0.2f, 0.2f);
var ground = UnityEngine.GameObject.CreatePrimitive(UnityEngine.PrimitiveType.Plane); ground.name = "Ground";
ground.transform.localScale = new UnityEngine.Vector3(4f, 1f, 4f);
var camGo = new UnityEngine.GameObject("Main Camera") { tag = "MainCamera" };
var cam = camGo.AddComponent<UnityEngine.Camera>(); cam.clearFlags = UnityEngine.CameraClearFlags.SolidColor;
cam.backgroundColor = new UnityEngine.Color(0.24f, 0.25f, 0.28f);
camGo.AddComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>();
var root = new UnityEngine.GameObject("Preview");
float x = 0f; var placed = new System.Collections.Generic.Dictionary<string, UnityEngine.GameObject>();
var all = new UnityEngine.Bounds(UnityEngine.Vector3.zero, UnityEngine.Vector3.zero); bool any = false;
foreach (var line in args)
{
    var s = line.Split(' ', System.StringSplitOptions.RemoveEmptyEntries);
    if (s.Length < 2 || s[0] == "pose") continue;
    var cat = ProjectPaths.ParseCategory(s[0]);
    string prefabPath;
    try { prefabPath = ProjectPaths.Prefab("PF_" + s[1]); } catch (System.Exception e) { log.AppendLine($"MISSING PF_{s[1]}: {e.Message}"); continue; }
    var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(prefabPath);
    if (!prefab) { log.AppendLine($"MISSING {prefabPath}"); continue; }
    var go = (UnityEngine.GameObject)UnityEditor.PrefabUtility.InstantiatePrefab(prefab, root.transform);
    var rs = go.GetComponentsInChildren<UnityEngine.Renderer>().Where(r => r.enabled && !r.name.StartsWith("UCX_")).ToArray();
    var b = rs.Length > 0 ? rs[0].bounds : new UnityEngine.Bounds(go.transform.position, UnityEngine.Vector3.one);
    foreach (var r in rs) b.Encapsulate(r.bounds);
    // Characters stand on their pivot (feet at the origin by contract); skinned bounds are conservative, so only
    // static assets are grounded by their renderer bounds.
    float y = cat == ProjectPaths.Category.Character ? 0f : -b.min.y + go.transform.position.y;
    go.transform.position = new UnityEngine.Vector3(x - (b.min.x - go.transform.position.x), y, -b.center.z + go.transform.position.z);
    UnityEngine.Physics.SyncTransforms();
    var b2 = rs.Length > 0 ? rs[0].bounds : b; foreach (var r in rs) b2.Encapsulate(r.bounds);
    x = b2.max.x + 1f; placed[s[1]] = go;
    if (!any) { all = b2; any = true; } else all.Encapsulate(b2);
    log.AppendLine($"placed {go.name} at {go.transform.position} size {b2.size} renderers {rs.Length}");
}
foreach (var line in args)
{
    var s = line.Split(' ', System.StringSplitOptions.RemoveEmptyEntries);
    if (s.Length < 4 || s[0] != "pose") continue;
    if (!placed.TryGetValue(s[1], out var go)) { log.AppendLine($"pose: {s[1]} not placed"); continue; }
    string model = null; try { model = ProjectPaths.Model("SK_" + s[1]); } catch { }
    var clip = model == null ? null : UnityEditor.AssetDatabase.LoadAllAssetsAtPath(model).OfType<UnityEngine.AnimationClip>().FirstOrDefault(c => c.name == s[2]);
    if (!clip) { log.AppendLine($"pose: clip {s[2]} not found in SK_{s[1]}"); continue; }
    float t = float.Parse(s[3], System.Globalization.CultureInfo.InvariantCulture) * clip.length;
    var anim = go.GetComponentInChildren<UnityEngine.Animator>();
    var target = anim ? anim.gameObject : go;
    // SampleAnimation poses Generic and Humanoid clips alike (AnimationMode sampling leaves humanoids in the bind
    // pose). The pose is written into the preview scene, which is a sandbox rebuilt on every run.
    clip.SampleAnimation(target, t);
    log.AppendLine($"pose {s[1]} {clip.name} t={t:F2}s of {clip.length:F2}s (humanMotion {clip.humanMotion}, loop {clip.isLooping}, events {clip.events.Length})");
}
var c = any ? all.center : UnityEngine.Vector3.up; var ext = any ? all.extents.magnitude : 1f;
float d = ext * 2.6f + 1.5f;
var dir3q = new UnityEngine.Vector3(-0.55f, 0.35f, 1f).normalized;
log.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture, "shot preview_front {0:F2} {1:F2} {2:F2} {3:F2} {4:F2} {5:F2} 40", c.x, c.y + ext * 0.15f, c.z + d, c.x, c.y, c.z));
log.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture, "shot preview_q34 {0:F2} {1:F2} {2:F2} {3:F2} {4:F2} {5:F2} 40", c.x + dir3q.x * d, c.y + dir3q.y * d, c.z + dir3q.z * d, c.x, c.y, c.z));
log.AppendLine(string.Format(System.Globalization.CultureInfo.InvariantCulture, "shot preview_side {0:F2} {1:F2} {2:F2} {3:F2} {4:F2} {5:F2} 40", c.x + d, c.y + ext * 0.15f, c.z, c.x, c.y, c.z));
camGo.transform.position = c + dir3q * d; camGo.transform.LookAt(c); cam.fieldOfView = 40f;
ProjectPaths.EnsureFolder(ProjectPaths.Sandbox);
var path = ProjectPaths.Sandbox + "/Preview.unity";
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene, path);
log.AppendLine("PREVIEW saved " + path);
return log.ToString();
