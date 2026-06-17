using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class Video2MeshUnityImporter
{
    private const string DefaultAdapterPath =
        "../exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json";

    private const string ImportRoot = "Assets/Video2MeshImported";
    private const string ScenePath = "Assets/Scenes/Video2MeshScene.unity";

    [MenuItem("Video2Mesh/Import Default Adapter")]
    public static void ImportDefaultAdapter()
    {
        ImportFromAdapter(DefaultAdapterPath);
    }

    public static void ImportFromCommandLine()
    {
        ImportFromAdapter(GetArg("-adapter") ?? DefaultAdapterPath);
    }

    private static void ImportFromAdapter(string adapterPath)
    {
        var projectRoot = Directory.GetParent(Application.dataPath)?.FullName
            ?? throw new InvalidOperationException("Could not resolve Unity project root.");
        var absoluteAdapterPath = ResolvePath(projectRoot, adapterPath);
        if (!File.Exists(absoluteAdapterPath))
        {
            throw new FileNotFoundException($"Video2Mesh adapter was not found: {absoluteAdapterPath}");
        }

        var adapterDirectory = Path.GetDirectoryName(absoluteAdapterPath)
            ?? throw new InvalidOperationException($"Adapter path has no directory: {absoluteAdapterPath}");
        var adapter = JsonUtility.FromJson<UnityAdapter>(File.ReadAllText(absoluteAdapterPath));
        if (adapter == null || adapter.objects == null)
        {
            throw new InvalidOperationException($"Adapter JSON could not be parsed: {absoluteAdapterPath}");
        }

        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Scenes"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Video2MeshImported"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Video2MeshImported", "Meshes"));
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Video2MeshImported", "Metadata"));

        File.Copy(
            absoluteAdapterPath,
            Path.Combine(Application.dataPath, "Video2MeshImported", "Metadata", "unity_adapter.json"),
            overwrite: true);

        CopyPackagedMeshes(adapterDirectory, adapter.objects);
        AssetDatabase.Refresh(ImportAssetOptions.ForceUpdate);

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.86f, 0.88f, 0.9f);
        RenderSettings.ambientEquatorColor = new Color(0.55f, 0.57f, 0.6f);
        RenderSettings.ambientGroundColor = new Color(0.34f, 0.35f, 0.38f);

        var root = new GameObject(SanitizeName(adapter.scene_id, "Video2MeshScene"));
        root.transform.position = Vector3.zero;

        var materials = CreateMaterials();
        foreach (var entry in adapter.objects.Where(entry => entry != null))
        {
            CreateObject(root.transform, adapterDirectory, entry, materials);
        }

        AddLighting();
        FrameSceneCamera(adapter.objects);

        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();

        Debug.Log($"Video2Mesh import complete: {adapter.objects.Length} entries from {absoluteAdapterPath}");
    }

    private static void CopyPackagedMeshes(string adapterDirectory, IEnumerable<UnityObjectEntry> entries)
    {
        foreach (var entry in entries)
        {
            if (entry == null || string.IsNullOrWhiteSpace(entry.packaged_mesh_relative))
            {
                continue;
            }

            var source = Path.GetFullPath(Path.Combine(adapterDirectory, entry.packaged_mesh_relative));
            if (!File.Exists(source))
            {
                Debug.LogWarning($"Mesh referenced by adapter does not exist: {source}");
                continue;
            }

            var meshDirectory = Path.Combine(Application.dataPath, "Video2MeshImported", "Meshes", entry.object_id);
            Directory.CreateDirectory(meshDirectory);
            File.Copy(source, Path.Combine(meshDirectory, Path.GetFileName(source)), overwrite: true);
        }
    }

    private static void CreateObject(
        Transform root,
        string adapterDirectory,
        UnityObjectEntry entry,
        IReadOnlyDictionary<string, Material> materials)
    {
        var holder = new GameObject(SanitizeName(entry.object_id, "Video2MeshObject"));
        holder.transform.SetParent(root, false);
        holder.transform.localPosition = ToVector3(entry.position);
        holder.transform.localRotation = ToQuaternion(entry.rotation_xyzw);
        holder.transform.localScale = ToVector3(entry.scale, Vector3.one);

        GameObject visual = null;
        if (!string.IsNullOrWhiteSpace(entry.packaged_mesh_relative))
        {
            var source = Path.GetFullPath(Path.Combine(adapterDirectory, entry.packaged_mesh_relative));
            var assetPath = $"Assets/Video2MeshImported/Meshes/{entry.object_id}/{Path.GetFileName(source)}";
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
            if (prefab != null)
            {
                visual = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
                if (visual != null)
                {
                    visual.name = "mesh";
                    visual.transform.SetParent(holder.transform, false);
                    ApplyMaterial(visual, PickMaterial(entry, materials));
                }
            }
        }

        if (visual == null)
        {
            visual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            visual.name = "bbox";
            visual.transform.SetParent(holder.transform, false);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localRotation = Quaternion.identity;
            visual.transform.localScale = ToVector3(entry.bbox_size, Vector3.one);
            ApplyMaterial(visual, PickMaterial(entry, materials));
        }

        ConfigurePhysics(holder, visual, entry);
    }

    private static void ConfigurePhysics(GameObject holder, GameObject visual, UnityObjectEntry entry)
    {
        var bodyType = entry.physics?.body_type ?? "static";
        var colliderType = entry.physics?.collider ?? "box";

        if (string.Equals(colliderType, "mesh", StringComparison.OrdinalIgnoreCase))
        {
            var meshFilters = visual.GetComponentsInChildren<MeshFilter>();
            foreach (var meshFilter in meshFilters)
            {
                if (meshFilter.sharedMesh == null)
                {
                    continue;
                }

                var collider = meshFilter.gameObject.GetComponent<MeshCollider>()
                    ?? meshFilter.gameObject.AddComponent<MeshCollider>();
                collider.sharedMesh = meshFilter.sharedMesh;
                collider.convex = string.Equals(bodyType, "dynamic", StringComparison.OrdinalIgnoreCase);
            }
        }
        else if (visual.GetComponent<Collider>() == null)
        {
            visual.AddComponent<BoxCollider>();
        }

        if (string.Equals(bodyType, "dynamic", StringComparison.OrdinalIgnoreCase))
        {
            var rigidbody = holder.AddComponent<Rigidbody>();
            rigidbody.mass = Math.Max(0.01f, entry.physics?.mass_kg ?? 1.0f);
        }
        else
        {
            holder.isStatic = true;
            foreach (var child in holder.GetComponentsInChildren<Transform>())
            {
                child.gameObject.isStatic = true;
            }
        }
    }

    private static IReadOnlyDictionary<string, Material> CreateMaterials()
    {
        Directory.CreateDirectory(Path.Combine(Application.dataPath, "Video2MeshImported", "Materials"));
        var materials = new Dictionary<string, Material>
        {
            ["blue"] = CreateMaterial("Video2Mesh_Blue", new Color(0.1f, 0.32f, 0.85f, 1.0f)),
            ["orange"] = CreateMaterial("Video2Mesh_Orange", new Color(0.95f, 0.42f, 0.12f, 1.0f)),
            ["light"] = CreateMaterial("Video2Mesh_Light", new Color(0.86f, 0.84f, 0.76f, 1.0f)),
            ["structure"] = CreateMaterial("Video2Mesh_Structure", new Color(0.45f, 0.48f, 0.5f, 0.42f)),
            ["default"] = CreateMaterial("Video2Mesh_Default", new Color(0.62f, 0.66f, 0.7f, 1.0f))
        };
        AssetDatabase.Refresh();
        return materials;
    }

    private static Material CreateMaterial(string name, Color color)
    {
        var path = $"Assets/Video2MeshImported/Materials/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Standard"));
            AssetDatabase.CreateAsset(material, path);
        }

        material.color = color;
        if (color.a < 1.0f)
        {
            material.SetFloat("_Mode", 3.0f);
            material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            material.SetInt("_ZWrite", 0);
            material.DisableKeyword("_ALPHATEST_ON");
            material.EnableKeyword("_ALPHABLEND_ON");
            material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            material.renderQueue = 3000;
        }
        else
        {
            material.SetFloat("_Mode", 0.0f);
            material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.One);
            material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.Zero);
            material.SetInt("_ZWrite", 1);
            material.DisableKeyword("_ALPHATEST_ON");
            material.DisableKeyword("_ALPHABLEND_ON");
            material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            material.renderQueue = -1;
        }

        EditorUtility.SetDirty(material);
        return material;
    }

    private static Material PickMaterial(UnityObjectEntry entry, IReadOnlyDictionary<string, Material> materials)
    {
        var haystack = $"{entry.object_id} {entry.name} {entry.category}".ToLowerInvariant();
        if (haystack.Contains("blue"))
        {
            return materials["blue"];
        }

        if (haystack.Contains("orange"))
        {
            return materials["orange"];
        }

        if (haystack.Contains("light"))
        {
            return materials["light"];
        }

        if (string.IsNullOrWhiteSpace(entry.packaged_mesh_relative))
        {
            return materials["structure"];
        }

        return materials["default"];
    }

    private static void ApplyMaterial(GameObject target, Material material)
    {
        foreach (var renderer in target.GetComponentsInChildren<Renderer>())
        {
            renderer.sharedMaterial = material;
        }
    }

    private static void AddLighting()
    {
        var sun = new GameObject("Directional Light");
        var light = sun.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.1f;
        sun.transform.rotation = Quaternion.Euler(48.0f, -32.0f, 0.0f);
    }

    private static void FrameSceneCamera(UnityObjectEntry[] entries)
    {
        var cameraObject = new GameObject("Main Camera");
        var camera = cameraObject.AddComponent<Camera>();
        camera.tag = "MainCamera";
        camera.nearClipPlane = 0.01f;
        camera.farClipPlane = 1000.0f;
        camera.clearFlags = CameraClearFlags.Skybox;

        var bounds = CalculateBounds(entries);
        var center = bounds.center;
        var radius = Math.Max(1.0f, bounds.extents.magnitude);
        cameraObject.transform.position = center + new Vector3(radius * 1.7f, radius * 1.1f, -radius * 1.9f);
        cameraObject.transform.LookAt(center);
    }

    private static Bounds CalculateBounds(IEnumerable<UnityObjectEntry> entries)
    {
        var hasBounds = false;
        var bounds = new Bounds(Vector3.zero, Vector3.one);
        foreach (var entry in entries.Where(entry => entry != null))
        {
            var position = ToVector3(entry.position);
            var size = ToVector3(entry.bbox_size, Vector3.one);
            var entryBounds = new Bounds(position, size);
            if (!hasBounds)
            {
                bounds = entryBounds;
                hasBounds = true;
            }
            else
            {
                bounds.Encapsulate(entryBounds);
            }
        }

        return bounds;
    }

    private static Vector3 ToVector3(float[] values)
    {
        return ToVector3(values, Vector3.zero);
    }

    private static Vector3 ToVector3(float[] values, Vector3 fallback)
    {
        if (values == null || values.Length < 3)
        {
            return fallback;
        }

        return new Vector3(values[0], values[1], values[2]);
    }

    private static Quaternion ToQuaternion(float[] xyzw)
    {
        if (xyzw == null || xyzw.Length < 4)
        {
            return Quaternion.identity;
        }

        return new Quaternion(xyzw[0], xyzw[1], xyzw[2], xyzw[3]);
    }

    private static string ResolvePath(string projectRoot, string path)
    {
        return Path.GetFullPath(Path.IsPathRooted(path) ? path : Path.Combine(projectRoot, path));
    }

    private static string GetArg(string name)
    {
        var args = Environment.GetCommandLineArgs();
        for (var i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == name)
            {
                return args[i + 1];
            }
        }

        return null;
    }

    private static string SanitizeName(string value, string fallback)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return fallback;
        }

        var invalid = Path.GetInvalidFileNameChars();
        var cleaned = new string(value.Select(character => invalid.Contains(character) ? '_' : character).ToArray());
        return string.IsNullOrWhiteSpace(cleaned) ? fallback : cleaned;
    }

    [Serializable]
    private sealed class UnityAdapter
    {
        public string scene_id;
        public UnityObjectEntry[] objects;
    }

    [Serializable]
    private sealed class UnityObjectEntry
    {
        public string object_id;
        public string name;
        public string category;
        public string packaged_mesh_relative;
        public float[] position;
        public float[] rotation_xyzw;
        public float[] scale;
        public float[] bbox_size;
        public PhysicsEntry physics;
    }

    [Serializable]
    private sealed class PhysicsEntry
    {
        public string body_type;
        public string collider;
        public float mass_kg;
    }
}
