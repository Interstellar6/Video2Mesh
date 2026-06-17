# Video2Mesh Unity Import Template

This lightweight Unity project imports a Video2Mesh Unity adapter JSON and builds a scene with object meshes, fallback bbox primitives, colliders, rigidbodies, simple materials, a light, and a camera.

Run from the repository root:

```bash
tools/import_video2mesh_to_unity.sh exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json
```

The importer script is `Assets/Editor/Video2MeshUnityImporter.cs`. Unity-generated folders such as `Library/`, `Temp/`, `Logs/`, `Build/`, `Builds/`, and `UserSettings/` are intentionally ignored.
