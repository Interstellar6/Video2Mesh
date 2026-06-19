# Video2Mesh Unity Import Template

This lightweight Unity project imports a Video2Mesh Unity adapter JSON and builds a scene with object meshes, fallback bbox primitives, colliders, rigidbodies, simple materials, a light, and a camera.

Unity Editor is installed at:

```text
/Users/zhangyuxiang/Unity/Hub/Editor/2023.2.20f1/Unity.app
```

Run from the repository root:

```bash
tools/import_video2mesh_to_unity.sh exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json
```

The importer script is `Assets/Editor/Video2MeshUnityImporter.cs`. It can also be run inside Unity from `Video2Mesh > Import Default Adapter`.

Current default adapter:

```text
../exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json
```

The default adapter JSON and OBJ files are already copied under `Assets/Video2MeshImported/` so the project has the source assets ready. Unity still needs an active Editor license before it can run batchmode import and create `Assets/Scenes/Video2MeshScene.unity`.

Unity-generated folders such as `Library/`, `Temp/`, `Logs/`, `Build/`, `Builds/`, and `UserSettings/` are intentionally ignored.
