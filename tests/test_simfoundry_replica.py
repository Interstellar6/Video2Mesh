import json
import re
import struct
from pathlib import Path

from video2mesh.cli import build_parser, main


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def make_minimal_simulator_project(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    mesh_path = project_root / "simulator_assets" / "objects" / "box_001" / "box.obj"
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    mesh_path.write_text(
        "\n".join(
            [
                "v -0.5 -0.5 -0.5",
                "v 0.5 -0.5 -0.5",
                "v 0.5 0.5 -0.5",
                "v -0.5 0.5 -0.5",
                "v -0.5 -0.5 0.5",
                "v 0.5 -0.5 0.5",
                "v 0.5 0.5 0.5",
                "v -0.5 0.5 0.5",
                "f 1 2 3",
                "f 1 3 4",
                "f 5 6 7",
                "f 5 7 8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    bundle_path = project_root / "simulator_assets" / "simulator_asset_bundle.json"
    bundle = {
        "schema_version": 1,
        "scene_id": "simfoundry-test-scene",
        "project_root": str(project_root),
        "coordinate_system": {
            "frame": "video2mesh_scene",
            "scale_to_meters": 1.0,
            "scale_calibrated": True,
            "up_axis": "y",
        },
        "scene_assets": {"scene_3dgs": "scene/reconstruction/3dgs"},
        "objects": [
            {
                "schema_version": 1,
                "object_id": "box_001",
                "asset_role": "object",
                "name": "box",
                "category": "box",
                "mesh": {"path": str(mesh_path), "format": "obj"},
                "collision_proxy": None,
                "pose": {
                    "position": [0.0, 0.5, 0.0],
                    "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
                    "scale": [1.0, 1.0, 1.0],
                    "bbox_size": [1.0, 1.0, 1.0],
                },
                "physics": {
                    "body_type": "dynamic",
                    "collider": "box",
                    "mass_kg": 1.2,
                    "material": {"name": "rigid", "friction": [0.8, 0.02, 0.001], "restitution": 0.1},
                    "source": "manual_physics",
                    "confidence": 0.9,
                },
            },
            {
                "schema_version": 1,
                "object_id": "floor_001",
                "asset_role": "background_structure",
                "name": "floor",
                "category": "floor",
                "mesh": None,
                "collision_proxy": None,
                "pose": {
                    "position": [0.0, -0.05, 0.0],
                    "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
                    "scale": [1.0, 1.0, 1.0],
                    "bbox_size": [4.0, 0.1, 4.0],
                },
                "physics": {
                    "body_type": "static",
                    "collider": "box",
                    "material": {"name": "floor", "friction": [0.9, 0.02, 0.001], "restitution": 0.05},
                    "source": "manual_physics",
                },
            },
        ],
    }
    write_json(bundle_path, bundle)
    write_json(
        project_root / "manifest.json",
        {
            "schema_version": 1,
            "scene_id": "simfoundry-test-scene",
            "simulator_assets_dir": "simulator_assets",
            "objects_dir": "objects",
            "scene": {
                "frames_dir": "scene/frames",
                "camera_info": "scene/cameras/camera_info.json",
                "point_cloud": "scene/reconstruction/point_cloud.ply",
                "scene_3dgs": "scene/reconstruction/3dgs",
            },
            "artifacts": {"simulator_asset_bundle": str(bundle_path)},
            "external_stages": {},
        },
    )
    return project_root, bundle_path


def write_minimal_object_records(project_root: Path) -> None:
    box_mesh = project_root / "simulator_assets" / "objects" / "box_001" / "box.obj"
    write_json(
        project_root / "objects" / "box_001" / "object.json",
        {
            "schema_version": 1,
            "object_id": "box_001",
            "label": "box",
            "category": "box",
            "asset_role": "object",
            "bbox_3d": {"center": [0.0, 0.5, 0.0], "size": [1.0, 1.0, 1.0]},
            "mesh_asset": {
                "asset_path": str(box_mesh),
                "source_mesh": str(box_mesh),
                "format": "obj",
                "coordinate_frame": "object_local",
            },
        },
    )
    write_json(
        project_root / "objects" / "floor_001" / "object.json",
        {
            "schema_version": 1,
            "object_id": "floor_001",
            "label": "floor",
            "category": "floor",
            "asset_role": "background_structure",
            "bbox_3d": {"center": [0.0, -0.05, 0.0], "size": [4.0, 0.1, 4.0]},
        },
    )


def write_tiny_scene_ply(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "ply",
                "format ascii 1.0",
                "element vertex 4",
                "property float x",
                "property float y",
                "property float z",
                "element face 2",
                "property list uchar int vertex_indices",
                "end_header",
                "-1 0 -1",
                "1 0 -1",
                "1 0 1",
                "-1 0 1",
                "3 0 1 2",
                "3 0 2 3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_tiny_binary_scene_ply(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\n".join(
        [
            "ply",
            "format binary_little_endian 1.0",
            "element vertex 4",
            "property float x",
            "property float y",
            "property float z",
            "element face 2",
            "property list uchar int vertex_index",
            "end_header",
            "",
        ]
    ).encode("ascii")
    vertices = [
        (-1.0, 0.0, -1.0),
        (1.0, 0.0, -1.0),
        (1.0, 0.0, 1.0),
        (-1.0, 0.0, 1.0),
    ]
    faces = [(0, 1, 2), (0, 2, 3)]
    with path.open("wb") as f:
        f.write(header)
        for vertex in vertices:
            f.write(struct.pack("<fff", *vertex))
        for face in faces:
            f.write(struct.pack("<Biii", 3, *face))


def test_prepare_simfoundry_collider_scene_from_existing_mesh_updates_manifest_and_bundle(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-collider-scene", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_collider_scene"
    assert args.reconstruct is False
    assert args.update_bundle is True
    assert args.write_collider_only_bundle is True

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    manifest["artifacts"]["scene_collider_mesh_ply"] = str(scene_mesh)
    write_json(project_root / "manifest.json", manifest)

    exit_code = main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--json",
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    )

    assert exit_code == 0
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    sidecar = Path(manifest["artifacts"]["simfoundry_collider_scene_manifest"])
    collider_mesh = Path(manifest["artifacts"]["simfoundry_scene_static_collider_mesh"])
    assert sidecar.exists()
    assert collider_mesh.exists()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["stage"] == "simfoundry_collider_scene"
    assert payload["qa"]["status"] == "pass"
    assert payload["collider"]["body_type"] == "static"
    assert payload["collider_only_bundle_written"] is True
    collider_only_bundle = Path(payload["collider_only_bundle"])
    assert collider_only_bundle.exists()
    assert payload["simfoundry_mapping"]["deferred"]
    assert "object visual meshes" in payload["simfoundry_mapping"]["deferred"]
    assert manifest["external_stages"]["simfoundry_collider_scene"]["summary"]["triangle_count"] == 2
    assert manifest["artifacts"]["simfoundry_collider_only_bundle"] == str(collider_only_bundle)
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["scene_assets"]["scene_static_collider_mesh"] == str(collider_mesh)
    assert bundle["static_colliders"][0]["id"] == "scene_static"
    assert bundle["static_colliders"][0]["path"] == str(collider_mesh)
    collider_only = json.loads(collider_only_bundle.read_text(encoding="utf-8"))
    assert collider_only["objects"] == []
    assert collider_only["scene_assets"]["scene_static_collider_mesh"] == str(collider_mesh)
    assert collider_only["static_colliders"][0]["id"] == "scene_static"


def test_prepare_simfoundry_collider_scene_writes_adapter_ready_bundle_without_objects(tmp_path):
    project_root = tmp_path / "project"
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    write_json(
        project_root / "manifest.json",
        {
            "schema_version": 1,
            "scene_id": "simfoundry-collider-only-test",
            "simulator_assets_dir": "simulator_assets",
            "objects_dir": "objects",
            "artifacts": {"scene_collider_mesh_ply": str(scene_mesh)},
            "external_stages": {},
        },
    )

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
            "--json",
            "--fail-on-fail",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    bundle_path = Path(manifest["artifacts"]["simulator_asset_bundle"])
    assert bundle_path.name == "simulator_asset_bundle.collider_only.json"
    assert manifest["artifacts"]["simfoundry_collider_only_bundle"] == str(bundle_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    collider_mesh = Path(manifest["artifacts"]["simfoundry_scene_static_collider_mesh"])
    assert bundle["scene_id"] == "simfoundry-collider-only-test"
    assert bundle["objects"] == []
    assert bundle["static_colliders"][0]["path"] == str(collider_mesh)
    assert bundle["scene_assets"]["scene_static_collider_mesh"] == str(collider_mesh)

    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--format",
            "mujoco",
            "unity",
            "isaac",
        ]
    ) == 0

    adapters = json.loads(Path(manifest["artifacts"].get("simulator_adapters", project_root / "simulator_assets" / "adapters" / "simulator_adapters.json")).read_text(encoding="utf-8"))
    assert adapters["formats"]["mujoco"]["object_count"] == 0
    assert adapters["formats"]["mujoco"]["static_collider_count"] == 1
    assert adapters["formats"]["unity"]["static_collider_count"] == 1
    assert adapters["formats"]["isaac"]["static_collider_count"] == 1


def test_prepare_simfoundry_collider_scene_converts_binary_ply_without_numpy(tmp_path):
    project_root, _bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_binary_scene.ply"
    write_tiny_binary_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
            "--json",
            "--fail-on-fail",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    payload = json.loads(Path(manifest["artifacts"]["simfoundry_collider_scene_manifest"]).read_text(encoding="utf-8"))
    collider_mesh = Path(manifest["artifacts"]["simfoundry_scene_static_collider_mesh"])
    assert collider_mesh.suffix == ".obj"
    assert collider_mesh.exists()
    assert payload["materialization"]["reader"] == "light_binary_little_endian_ply_to_obj"
    assert payload["qa"]["status"] == "pass"
    assert payload["collider"]["stats"]["vertex_count"] == 4
    assert payload["collider"]["stats"]["triangle_count"] == 2


def test_export_simulator_assets_preserves_prepared_scene_collider(tmp_path):
    project_root, _bundle_path = make_minimal_simulator_project(tmp_path)
    write_minimal_object_records(project_root)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0

    assert main(
        [
            "export-simulator-assets",
            "--project-root",
            str(project_root),
            "--copy-meshes",
            "--collision-proxy",
            "bbox",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    bundle_path = Path(manifest["artifacts"]["simulator_asset_bundle"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    collider_mesh = Path(manifest["artifacts"]["simfoundry_scene_static_collider_mesh"])
    assert bundle["scene_assets"]["scene_static_collider_mesh"] == str(collider_mesh)
    assert bundle["static_colliders"][0]["id"] == "scene_static"
    assert bundle["static_colliders"][0]["path"] == str(collider_mesh)
    assert manifest["external_stages"]["mesh_generation"]["static_collider_count"] == 1
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    assert box["physics"]["mass_kg"] > 0
    assert box["physics"]["material"]["friction"] == [0.8, 0.02, 0.001]
    assert box["physics"]["material"]["restitution"] == 0.1
    assert box["physics"]["source"] == "simfoundry_bbox_physics"
    assert floor["physics"]["body_type"] == "static"
    assert floor["physics"]["mass_kg"] is None


def test_prepare_simfoundry_static_object_scene_wraps_existing_object_records(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-static-object-scene", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_static_object_scene"
    assert args.split_objects is True
    assert args.prepare_collider is True
    assert args.body_type == "static"
    assert args.collision_proxy == "bbox"
    assert args.format == ["mujoco", "unity", "isaac"]

    project_root, _bundle_path = make_minimal_simulator_project(tmp_path)
    write_minimal_object_records(project_root)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-static-object-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--no-split-objects",
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
            "--json",
            "--fail-on-required",
            "--fail-on-empty",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_static_object_scene_report"])
    bundle_path = Path(manifest["artifacts"]["simulator_asset_bundle"])
    adapter_manifest = Path(manifest["artifacts"]["simulator_adapters"])
    assert report_path.exists()
    assert bundle_path.exists()
    assert adapter_manifest.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage"] == "simfoundry_static_object_scene"
    assert report["status"] == "ready"
    assert report["summary"]["object_count"] == 2
    assert report["summary"]["foreground_object_count"] == 1
    assert report["summary"]["background_structure_count"] == 1
    assert report["summary"]["static_collider_count"] == 1
    assert report["summary"]["existing_object_proxy_count"] == 2
    assert report["summary"]["adapter_ready_count"] == 3
    assert manifest["external_stages"]["simfoundry_static_object_scene"]["summary"]["object_count"] == 2

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert len(bundle["objects"]) == 2
    assert len(bundle["static_colliders"]) == 1
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    assert box["physics"]["body_type"] == "static"
    assert box["physics"]["collider"] == "box"
    assert Path(box["collision_proxy"]["path"]).exists()
    assert floor["physics"]["body_type"] == "static"
    assert Path(floor["collision_proxy"]["path"]).exists()

    adapters = json.loads(adapter_manifest.read_text(encoding="utf-8"))
    assert sorted(adapters["formats"]) == ["isaac", "mujoco", "unity"]
    for result in adapters["formats"].values():
        assert Path(result["adapter_file"]).exists()
        assert result["object_count"] == 2
        assert result["static_collider_count"] == 1


def test_export_simulator_assets_supports_collider_only_manifest_without_scene(tmp_path):
    project_root, _bundle_path = make_minimal_simulator_project(tmp_path)
    write_minimal_object_records(project_root)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    manifest_path = project_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("scene", None)
    manifest["artifacts"].pop("simulator_asset_bundle", None)
    manifest["artifacts"]["scene_mesh_ply"] = str(scene_mesh)
    write_json(manifest_path, manifest)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0

    assert main(
        [
            "export-simulator-assets",
            "--project-root",
            str(project_root),
            "--copy-meshes",
            "--collision-proxy",
            "bbox",
        ]
    ) == 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = json.loads(Path(manifest["artifacts"]["simulator_asset_bundle"]).read_text(encoding="utf-8"))
    collider_mesh = Path(manifest["artifacts"]["simfoundry_scene_static_collider_mesh"])
    assert bundle["scene_assets"]["frames_dir"] is None
    assert bundle["scene_assets"]["point_cloud"] == str(scene_mesh)
    assert bundle["scene_assets"]["scene_static_collider_mesh"] == str(collider_mesh)
    assert bundle["static_colliders"][0]["id"] == "scene_static"


def test_simfoundry_scene_static_collider_flows_into_simulator_adapters(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0

    assert main(
        [
            "qa-simulator-assets",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--min-mesh-vertices",
            "1",
            "--json",
            "--fail-on-required",
        ]
    ) == 0

    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
        ]
    ) == 0

    mujoco_xml = project_root / "simulator_assets" / "adapters" / "mujoco" / "scene.xml"
    mujoco_manifest = project_root / "simulator_assets" / "adapters" / "mujoco" / "mujoco_adapter.json"
    unity_adapter = project_root / "simulator_assets" / "adapters" / "unity" / "unity_adapter.json"
    assert mujoco_xml.exists()
    mujoco_xml_text = mujoco_xml.read_text(encoding="utf-8")
    assert 'name="scene_static"' in mujoco_xml_text
    assert '<freejoint name="box_001_freejoint"/>' in mujoco_xml_text
    mujoco_payload = json.loads(mujoco_manifest.read_text(encoding="utf-8"))
    assert mujoco_payload["static_colliders"][0]["collider_id"] == "scene_static"
    assert Path(mujoco_payload["static_colliders"][0]["packaged_mesh_path"]).exists()
    box_mujoco = next(obj for obj in mujoco_payload["objects"] if obj["object_id"] == "box_001")
    assert box_mujoco["joint"] == "freejoint"
    unity_payload = json.loads(unity_adapter.read_text(encoding="utf-8"))
    assert unity_payload["static_colliders"][0]["packaged_mesh_relative"].startswith("../assets/static_scene_static/")


def test_export_simulator_adapter_relative_output_dir_uses_xml_relative_assets(tmp_path, monkeypatch):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["collider"] = "mesh"
    write_json(bundle_path, bundle)
    monkeypatch.chdir(tmp_path)

    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--output-dir",
            "relative_adapters",
            "--format",
            "mujoco",
        ]
    ) == 0

    mujoco_xml = tmp_path / "relative_adapters" / "mujoco" / "scene.xml"
    mujoco_manifest = json.loads((tmp_path / "relative_adapters" / "mujoco" / "mujoco_adapter.json").read_text(encoding="utf-8"))
    assert mujoco_xml.exists()
    assert 'file="../assets/box_001/box.obj"' in mujoco_xml.read_text(encoding="utf-8")
    packaged_mesh = Path(mujoco_manifest["objects"][0]["packaged_mesh"])
    assert packaged_mesh.exists()


def test_prepare_simfoundry_object_colliders_updates_bundle_and_adapters(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-object-colliders", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_object_colliders"
    assert args.provider == "simfoundry_bbox_proxy"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    assert main(
        [
            "prepare-simfoundry-object-colliders",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    sidecar = Path(manifest["artifacts"]["simfoundry_object_colliders_manifest"])
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["summary"]["generated_count"] == 1
    assert payload["summary"]["skipped_count"] == 1
    assert "floor_001" in payload["skipped"]

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    proxy_path = Path(box["collision_proxy"]["path"])
    assert proxy_path.exists()
    assert box["collision_proxy"]["shape"] == "box"
    assert box["physics"]["collision_proxy"]["path"] == str(proxy_path)
    assert box["physics"]["collider"] == "box"
    assert floor["collision_proxy"] is None

    assert main(
        [
            "simulator-physics-quality-report",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--allow-estimated-physics",
            "--json",
            "--fail-on-required",
        ]
    ) == 0
    physics_report = json.loads((project_root / "simulator_assets" / "simulator_physics_quality_report.json").read_text(encoding="utf-8"))
    assert physics_report["summary"]["objects_with_collision_proxy"] == 1

    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "unity",
        ]
    ) == 0
    unity_adapter = json.loads((project_root / "simulator_assets" / "adapters" / "unity" / "unity_adapter.json").read_text(encoding="utf-8"))
    box_adapter = next(obj for obj in unity_adapter["objects"] if obj["object_id"] == "box_001")
    assert Path(box_adapter["packaged_collision_proxy_path"]).exists()
    assert box_adapter["packaged_collision_proxy_relative"].endswith("box_001_bbox_collider.obj")


def test_build_simfoundry_object_colliders_records_external_attempts_and_bbox_fallback(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["build-simfoundry-object-colliders", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_build_simfoundry_object_colliders"
    assert args.methods == "coacd,vhacd,bbox"
    assert args.provider == "simfoundry_collider_builder"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    exit_code = main(
        [
            "build-simfoundry-object-colliders",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--coacd-binary",
            "missing-coacd-for-test",
            "--vhacd-binary",
            "missing-vhacd-for-test",
            "--json",
            "--fail-on-empty",
        ]
    )
    assert exit_code == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    build_manifest_path = Path(manifest["artifacts"]["simfoundry_collider_build_manifest"])
    payload = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    assert payload["stage"] == "simfoundry_collider_build"
    assert payload["summary"]["built_count"] == 1
    assert payload["summary"]["fallback_count"] == 1
    assert payload["summary"]["skipped_count"] == 1
    assert "floor_001" in payload["skipped"]
    assert payload["built"]["box_001"]["selected_method"] == "bbox"
    report_path = Path(payload["built"]["box_001"]["report"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert [attempt["method"] for attempt in report["attempts"]] == ["coacd", "vhacd", "bbox"]
    assert report["attempts"][0]["status"] == "runtime_unavailable"
    assert report["attempts"][1]["status"] == "runtime_unavailable"
    assert report["attempts"][2]["status"] == "success"

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    proxy_path = Path(box["collision_proxy"]["path"])
    assert proxy_path.exists()
    assert box["collision_proxy"]["fallback"] is True
    assert box["collision_proxy"]["builder_method"] == "bbox"
    assert box["physics"]["collision_proxy"]["path"] == str(proxy_path)
    assert box["quality"]["collider_build_report"] == str(report_path)

    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "unity",
        ]
    ) == 0
    unity_adapter = json.loads((project_root / "simulator_assets" / "adapters" / "unity" / "unity_adapter.json").read_text(encoding="utf-8"))
    box_adapter = next(obj for obj in unity_adapter["objects"] if obj["object_id"] == "box_001")
    assert Path(box_adapter["packaged_collision_proxy_path"]).exists()


def test_simfoundry_simulator_smoke_test_passes_structural_preflight(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["simfoundry-simulator-smoke-test", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_simfoundry_simulator_smoke_test"
    assert args.mujoco_runtime == "auto"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert main(["prepare-simfoundry-object-colliders", "--project-root", str(project_root), "--bundle", str(bundle_path)]) == 0
    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
        ]
    ) == 0

    assert main(
        [
            "simfoundry-simulator-smoke-test",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
            "--mujoco-runtime",
            "skip",
            "--min-mesh-vertices",
            "1",
            "--json",
            "--fail-on-required",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "physics" / "sim_preflight_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage"] == "simfoundry_simulator_smoke_test"
    assert report["ok"] is True
    assert report["summary"]["static_collider_count"] == 1
    assert report["summary"]["existing_object_proxy_count"] == 1
    assert report["summary"]["adapter_ready_count"] == 2
    assert report["mujoco_runtime"]["status"] == "skipped"
    assert report["summary"]["required_issue_count"] == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["sim_preflight_report"] == str(report_path)
    assert manifest["external_stages"]["simfoundry_simulator_smoke_test"]["status"] == report["status"]


def test_simfoundry_simulator_smoke_test_requires_scale_when_requested(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["coordinate_system"]["scale_calibrated"] = False
    bundle["coordinate_system"]["calibrated"] = False
    write_json(bundle_path, bundle)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert main(["prepare-simfoundry-object-colliders", "--project-root", str(project_root), "--bundle", str(bundle_path)]) == 0
    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
            "isaac",
        ]
    ) == 0

    assert main(
        [
            "simfoundry-simulator-smoke-test",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
            "isaac",
            "--mujoco-runtime",
            "skip",
            "--min-mesh-vertices",
            "1",
            "--json",
            "--fail-on-required",
        ]
    ) == 0
    baseline_report = json.loads((project_root / "simulator_assets" / "physics" / "sim_preflight_report.json").read_text(encoding="utf-8"))
    assert baseline_report["ok"] is True
    assert baseline_report["summary"]["required_issue_count"] == 0
    assert baseline_report["summary"]["warning_count"] >= 1
    assert any(issue["name"] == "scale_not_calibrated" and issue["severity"] == "warning" for issue in baseline_report["issues"])

    strict_report_rel = Path("simulator_assets/physics/sim_preflight_report.require_scale_calibration.json")
    strict_report_path = project_root / strict_report_rel
    assert main(
        [
            "simfoundry-simulator-smoke-test",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "unity",
            "isaac",
            "--mujoco-runtime",
            "skip",
            "--min-mesh-vertices",
            "1",
            "--require-scale-calibration",
            "--output",
            str(strict_report_rel),
            "--json",
            "--fail-on-required",
        ]
    ) == 1
    strict_report = json.loads(strict_report_path.read_text(encoding="utf-8"))
    assert strict_report["status"] == "fail"
    assert strict_report["summary"]["required_issue_count"] == 2
    required_scale_issues = [issue for issue in strict_report["issues"] if issue["severity"] == "required" and issue["name"] == "scale_not_calibrated"]
    assert {issue["source"] for issue in required_scale_issues} == {"qa-simulator-assets", "simulator-physics-quality-report"}


def test_prepare_scale_calibration_jobs_writes_template_readme_without_calibrating_bundle(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-scale-calibration-jobs", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_scale_calibration_jobs"
    assert args.provider == "manual_measurement"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["coordinate_system"]["scale_calibrated"] = False
    bundle["coordinate_system"]["calibrated"] = False
    write_json(bundle_path, bundle)

    assert main(
        [
            "prepare-scale-calibration-jobs",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--include-background",
            "--sort-by",
            "object_id",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    job_path = Path(manifest["artifacts"]["scale_calibration_job"])
    template_path = Path(manifest["artifacts"]["scale_calibration_template"])
    readme_path = Path(manifest["artifacts"]["scale_calibration_readme"])
    assert job_path.exists()
    assert template_path.exists()
    assert readme_path.exists()

    job = json.loads(job_path.read_text(encoding="utf-8"))
    template = json.loads(template_path.read_text(encoding="utf-8"))
    readme = readme_path.read_text(encoding="utf-8")
    assert job["candidate_count"] == 2
    assert job["include_background"] is True
    assert job["readme"] == str(readme_path)
    assert template["selected_reference"]["reference_length_m"] is None
    assert len(template["candidates"]) == 2
    assert template["measurement_recommendations"][0]["object_id"] in {"box_001", "floor_001"}
    assert "Do not mark `scale_calibrated=true`" in readme

    after_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert after_bundle["coordinate_system"]["scale_calibrated"] is False
    assert after_bundle["coordinate_system"]["calibrated"] is False
    assert manifest["external_stages"]["simulator_scale_calibration"]["status"] == "scale_calibration_job_prepared"


def test_simfoundry_simulator_smoke_test_fails_when_adapter_is_missing(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)

    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
        ]
    ) == 0

    (project_root / "simulator_assets" / "adapters" / "mujoco" / "scene.xml").unlink()
    exit_code = main(
        [
            "simfoundry-simulator-smoke-test",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
            "--mujoco-runtime",
            "skip",
            "--min-mesh-vertices",
            "1",
            "--json",
            "--fail-on-required",
        ]
    )
    assert exit_code == 1
    report = json.loads((project_root / "simulator_assets" / "physics" / "sim_preflight_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    assert any(issue["name"] == "missing_mujoco_adapter" for issue in report["issues"])


def test_settle_simulator_scene_writes_stable_pose_cache_placeholder(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["settle-simulator-scene", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_settle_simulator_scene"
    assert args.mujoco_runtime == "auto"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert main(
        [
            "export-simulator-adapter",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--format",
            "mujoco",
        ]
    ) == 0
    assert main(
        [
            "settle-simulator-scene",
            "--project-root",
            str(project_root),
            "--mujoco-runtime",
            "skip",
            "--steps",
            "3",
            "--json",
            "--fail-on-required",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "physics" / "stable_pose_cache.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage"] == "simfoundry_settle_simulator_scene"
    assert report["status"] == "skipped"
    assert report["runtime"]["status"] == "skipped"
    assert report["steps"] == 3
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["stable_pose_cache"] == str(report_path)


def test_settle_simulator_scene_fails_when_mujoco_xml_missing(tmp_path):
    project_root, _bundle_path = make_minimal_simulator_project(tmp_path)
    exit_code = main(
        [
            "settle-simulator-scene",
            "--project-root",
            str(project_root),
            "--mujoco-runtime",
            "skip",
            "--json",
            "--fail-on-required",
        ]
    )
    assert exit_code == 1
    report = json.loads((project_root / "simulator_assets" / "physics" / "stable_pose_cache.json").read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    assert any(issue["name"] == "missing_mujoco_xml" for issue in report["issues"])


def test_export_scene_relations_infers_support_and_near_predicates(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["export-scene-relations", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_export_scene_relations"
    assert args.max_support_gap == 0.08

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(
        [
            "export-scene-relations",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "semantic" / "scene_relations.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    predicates = {(rel["subject"], rel["predicate"], rel["object"]) for rel in report["relations"]}
    assert ("box_001", "OnTopOf", "floor_001") in predicates
    assert ("box_001", "SupportedBy", "floor_001") in predicates
    assert report["summary"]["support_relation_count"] == 2
    assert report["summary"]["required_issue_count"] == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["scene_relations"] == str(report_path)
    assert manifest["external_stages"]["simfoundry_scene_relations"]["status"] == "relations_inferred"


def test_export_simfoundry_task_specs_from_scene_relations(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["export-simfoundry-task-specs", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_export_simfoundry_task_specs"
    assert args.refresh_relations is False
    assert args.include_near is False

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(
        [
            "export-scene-relations",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--fail-on-empty",
        ]
    ) == 0

    assert main(
        [
            "export-simfoundry-task-specs",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    task_manifest_path = Path(manifest["artifacts"]["simfoundry_task_specs"])
    payload = json.loads(task_manifest_path.read_text(encoding="utf-8"))
    assert payload["stage"] == "simfoundry_task_specs"
    assert payload["status"] == "task_specs_exported"
    assert payload["summary"]["task_count"] == 1
    assert payload["summary"]["task_type_counts"]["place_on"] == 1
    assert payload["tasks"][0]["task_type"] == "place_on"
    assert payload["tasks"][0]["goal_predicates"][0] == {
        "subject": "box_001",
        "predicate": "OnTopOf",
        "object": "floor_001",
        "source": "scene_relation_candidate",
    }
    assert payload["tasks"][0]["review_status"] == "needs_human_or_vlm_review"
    assert payload["task_index"][0]["task_id"] == payload["tasks"][0]["task_id"]
    assert Path(payload["task_index"][0]["path"]).exists()
    task_spec = json.loads(Path(payload["task_index"][0]["path"]).read_text(encoding="utf-8"))
    assert task_spec["instruction"] == "Place box on floor."
    assert task_spec["provenance"]["relations_report"] == manifest["artifacts"]["scene_relations"]
    assert manifest["external_stages"]["simfoundry_task_specs"]["status"] == "task_specs_exported"


def test_export_simfoundry_task_specs_fail_on_empty(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)

    exit_code = main(
        [
            "export-simfoundry-task-specs",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--refresh-relations",
            "--min-confidence",
            "0.99",
            "--json",
            "--fail-on-empty",
        ]
    )

    assert exit_code == 1
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    payload = json.loads(Path(manifest["artifacts"]["simfoundry_task_specs"]).read_text(encoding="utf-8"))
    assert payload["status"] == "empty"
    assert payload["summary"]["task_count"] == 0
    assert payload["summary"]["skipped_relation_count"] >= 1


def test_verify_simfoundry_task_specs_reports_satisfied_goal_and_reset_need(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["verify-simfoundry-task-specs", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_verify_simfoundry_task_specs"
    assert args.max_support_gap == 0.08

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_task_specs_verification"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage"] == "simfoundry_task_specs_verification"
    assert report["status"] == "verified"
    assert report["summary"]["task_count"] == 1
    assert report["summary"]["satisfied_task_count"] == 1
    assert report["summary"]["reset_required_task_count"] == 1
    assert report["tasks"][0]["goal_status"] == "satisfied"
    assert report["tasks"][0]["goal_predicates"][0]["metrics"]["footprint_overlap_over_smaller"] == 1.0
    assert manifest["external_stages"]["simfoundry_task_specs_verification"]["status"] == "verified"


def test_verify_simfoundry_task_specs_reports_not_satisfied_goal(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    write_json(bundle_path, bundle)

    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads(Path(manifest["artifacts"]["simfoundry_task_specs_verification"]).read_text(encoding="utf-8"))
    assert report["status"] == "verified"
    assert report["summary"]["not_satisfied_task_count"] == 1
    assert report["summary"]["reset_required_task_count"] == 0
    assert report["tasks"][0]["goal_status"] == "not_satisfied"
    assert report["tasks"][0]["goal_predicates"][0]["metrics"]["abs_vertical_gap"] > 0.08


def test_prepare_simfoundry_task_resets_moves_satisfied_place_on_goal_to_initial_state(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-task-resets", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_task_resets"
    assert args.write_sidecar_bundles is True
    assert args.reset_margin == 0.25

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0
    original_bundle_text = bundle_path.read_text(encoding="utf-8")

    assert main(["prepare-simfoundry-task-resets", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required", "--fail-on-empty"]) == 0

    assert bundle_path.read_text(encoding="utf-8") == original_bundle_text
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    reset_manifest_path = Path(manifest["artifacts"]["simfoundry_task_resets"])
    reset_manifest = json.loads(reset_manifest_path.read_text(encoding="utf-8"))
    assert reset_manifest["stage"] == "simfoundry_task_resets"
    assert reset_manifest["status"] == "task_resets_exported"
    assert reset_manifest["summary"]["task_count"] == 1
    assert reset_manifest["summary"]["reset_count"] == 1
    assert reset_manifest["summary"]["accepted_reset_count"] == 1
    assert reset_manifest["summary"]["required_issue_count"] == 0

    reset_entry = reset_manifest["reset_index"][0]
    reset_payload = json.loads(Path(reset_entry["path"]).read_text(encoding="utf-8"))
    assert reset_payload["accepted"] is True
    assert reset_payload["candidate_goal_status"] == "not_satisfied"
    assert reset_payload["candidate_goal_predicates"][0]["status"] == "not_satisfied"
    assert reset_payload["manipulated_object"] == "box_001"
    assert reset_payload["target_object"] == "floor_001"
    assert reset_payload["pose_delta"]["candidate_pose"]["position"] != [0.0, 0.55, 0.0]

    sidecar_bundle = json.loads(Path(reset_entry["sidecar_bundle"]).read_text(encoding="utf-8"))
    sidecar_box = next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "box_001")
    assert sidecar_box["pose"]["position"] == reset_payload["pose_delta"]["candidate_pose"]["position"]
    assert sidecar_box["pose"]["position"][0] > 2.0
    assert manifest["external_stages"]["simfoundry_task_resets"]["status"] == "task_resets_exported"


def test_export_simfoundry_task_reset_adapters_writes_per_task_initial_state_adapters(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["export-simfoundry-task-reset-adapters", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_export_simfoundry_task_reset_adapters"
    assert args.format == ["mujoco", "unity", "isaac"]

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0
    assert main(["prepare-simfoundry-task-resets", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required", "--fail-on-empty"]) == 0

    assert main(["export-simfoundry-task-reset-adapters", "--project-root", str(project_root), "--json", "--fail-on-required", "--fail-on-empty"]) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    reset_adapters_path = Path(manifest["artifacts"]["simfoundry_task_reset_adapters"])
    payload = json.loads(reset_adapters_path.read_text(encoding="utf-8"))
    assert payload["stage"] == "simfoundry_task_reset_adapters"
    assert payload["status"] == "task_reset_adapters_exported"
    assert payload["summary"]["adapter_count"] == 1
    record = payload["reset_adapters"][0]
    assert record["task_id"] == "place_on_box_001_floor_001"
    assert record["candidate_goal_status"] == "not_satisfied"
    mujoco_xml = Path(record["formats"]["mujoco"]["adapter_file"])
    unity_adapter = Path(record["formats"]["unity"]["adapter_file"])
    isaac_adapter = Path(record["formats"]["isaac"]["adapter_file"])
    assert mujoco_xml.exists()
    assert unity_adapter.exists()
    assert isaac_adapter.exists()
    xml_text = mujoco_xml.read_text(encoding="utf-8")
    assert 'body name="box_001" pos="2.83 0.55 0"' in xml_text
    unity_payload = json.loads(unity_adapter.read_text(encoding="utf-8"))
    unity_box = next(obj for obj in unity_payload["objects"] if obj["object_id"] == "box_001")
    assert unity_box["position"] == [2.83, 0.55, 0.0]
    assert manifest["external_stages"]["simfoundry_task_reset_adapters"]["status"] == "task_reset_adapters_exported"


def test_prepare_simfoundry_task_resets_empty_when_goal_not_satisfied(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    write_json(bundle_path, bundle)
    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0

    assert main(["prepare-simfoundry-task-resets", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json"]) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    reset_manifest = json.loads(Path(manifest["artifacts"]["simfoundry_task_resets"]).read_text(encoding="utf-8"))
    assert reset_manifest["status"] == "empty"
    assert reset_manifest["summary"]["task_count"] == 1
    assert reset_manifest["summary"]["reset_count"] == 0
    assert reset_manifest["summary"]["skipped_task_count"] == 1
    assert reset_manifest["skipped_tasks"][0]["reason"] == "reset_not_required"


def test_simfoundry_scene_stability_report_passes_supported_dynamic_object(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["simfoundry-scene-stability-report", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_simfoundry_scene_stability_report"
    assert args.require_support is True
    assert args.max_penetration_depth == 0.02

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    write_json(bundle_path, bundle)

    assert main(
        [
            "simfoundry-scene-stability-report",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-required",
            "--fail-on-penetration",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "physics" / "scene_stability_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage"] == "simfoundry_scene_stability"
    assert report["status"] == "stable_preflight"
    assert report["summary"]["supported_dynamic_count"] == 1
    assert report["summary"]["unsupported_dynamic_count"] == 0
    assert report["summary"]["penetration_count"] == 0
    assert report["object_reports"]["box_001"]["support"]["object_id"] == "floor_001"

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["scene_stability_report"] == str(report_path)
    assert manifest["external_stages"]["simfoundry_scene_stability"]["status"] == "stable_preflight"


def test_simfoundry_scene_stability_report_fails_for_unsupported_dynamic_object(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    write_json(bundle_path, bundle)

    exit_code = main(
        [
            "simfoundry-scene-stability-report",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-required",
        ]
    )

    assert exit_code == 1
    report = json.loads((project_root / "simulator_assets" / "physics" / "scene_stability_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    assert report["summary"]["unsupported_dynamic_count"] == 1
    assert any(issue["name"] == "dynamic_object_without_support" and issue["object_id"] == "box_001" for issue in report["issues"])


def test_simfoundry_scene_stability_supports_negative_up_direction(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["simfoundry-scene-stability-report", "--project-root", "proj", "--up-direction", "negative"])
    assert args.up_direction == "negative"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle["coordinate_system"]["up_axis"] = "y"
    bundle["coordinate_system"]["up_direction"] = "negative"
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, 0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, -0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    box["physics"]["body_type"] = "dynamic"
    write_json(bundle_path, bundle)

    assert main(
        [
            "simfoundry-scene-stability-report",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--up-axis",
            "y",
            "--up-direction",
            "negative",
            "--json",
            "--fail-on-required",
            "--fail-on-penetration",
        ]
    ) == 0

    report = json.loads((project_root / "simulator_assets" / "physics" / "scene_stability_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "stable_preflight"
    assert report["coordinate_system"]["up_direction"] == "negative"
    assert report["summary"]["supported_dynamic_count"] == 1
    assert report["object_reports"]["box_001"]["support"]["object_id"] == "floor_001"
    assert report["object_reports"]["box_001"]["support"]["up_direction"] == "negative"


def test_prepare_simfoundry_dynamic_variant_writes_sidecar_without_overwriting_bundle(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-dynamic-variant", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_dynamic_variant"
    assert args.require_support is True
    assert args.allow_penetration is False
    assert args.replace_bundle is False
    assert "box" in args.movable_categories

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    box["physics"]["body_type"] = "static"
    write_json(bundle_path, bundle)

    assert main(
        [
            "prepare-simfoundry-dynamic-variant",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "dynamic_variant_report.json"
    variant_path = project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "simulator_asset_bundle.dynamic_variant.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    variant = json.loads(variant_path.read_text(encoding="utf-8"))
    original = json.loads(bundle_path.read_text(encoding="utf-8"))
    variant_box = next(obj for obj in variant["objects"] if obj["object_id"] == "box_001")
    original_box = next(obj for obj in original["objects"] if obj["object_id"] == "box_001")
    assert report["status"] == "dynamic_variant_ready"
    assert report["summary"]["accepted_dynamic_count"] == 1
    assert report["accepted_dynamic_objects"] == ["box_001"]
    assert variant_box["physics"]["body_type"] == "dynamic"
    assert variant_box["simfoundry_dynamic_variant"]["support"]["object_id"] == "floor_001"
    assert original_box["physics"]["body_type"] == "static"

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert manifest["artifacts"]["simfoundry_dynamic_variant_bundle"] == str(variant_path)
    assert manifest["external_stages"]["simfoundry_dynamic_variant"]["status"] == "dynamic_variant_ready"


def test_prepare_simfoundry_dynamic_variant_accepts_project_relative_bundle(tmp_path, monkeypatch):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["physics"]["body_type"] = "static"
    write_json(bundle_path, bundle)
    monkeypatch.chdir(tmp_path)

    assert (
        main(
            [
                "prepare-simfoundry-dynamic-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                "simulator_assets/simulator_asset_bundle.json",
                "--json",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    report = json.loads((project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "dynamic_variant_report.json").read_text(encoding="utf-8"))
    assert report["bundle"] == str(bundle_path)
    assert report["summary"]["accepted_dynamic_count"] == 1


def test_prepare_simfoundry_tight_collider_variant_writes_mesh_quantile_sidecar(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-tight-collider-variant", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_tight_collider_variant"
    assert args.quantile_min == 0.10
    assert args.quantile_max == 0.90
    assert args.include_background is True
    assert args.replace_bundle is False

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [3.0, 1.0, 3.0]
    box["pose"]["bbox_3d"] = {"center": [0.0, 0.45, 0.0], "size": [3.0, 1.0, 3.0]}
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    write_json(bundle_path, bundle)

    assert main(
        [
            "prepare-simfoundry-tight-collider-variant",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--no-include-background",
            "--json",
            "--fail-on-required",
        ]
    ) == 0

    report_path = project_root / "simulator_assets" / "simfoundry_tight_collider_variant" / "tight_collider_variant_report.json"
    variant_path = project_root / "simulator_assets" / "simfoundry_tight_collider_variant" / "simulator_asset_bundle.tight_collider.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    variant = json.loads(variant_path.read_text(encoding="utf-8"))
    original = json.loads(bundle_path.read_text(encoding="utf-8"))
    variant_box = next(obj for obj in variant["objects"] if obj["object_id"] == "box_001")
    original_box = next(obj for obj in original["objects"] if obj["object_id"] == "box_001")

    assert report["stage"] == "simfoundry_tight_collider_variant"
    assert report["status"] == "tight_collider_ready"
    assert report["summary"]["updated_count"] == 1
    assert report["summary"]["before_penetration_count"] == 1
    assert report["summary"]["after_penetration_count"] == 0
    assert report["updated"]["box_001"]["shrink"]["volume_ratio"] < 0.2
    assert "floor_001" in report["skipped"]
    assert Path(variant_box["collision_proxy"]["path"]).exists()
    assert variant_box["collision_proxy"]["source"] == "mesh_quantile_bbox"
    assert variant_box["physics"]["collider"] == "box"
    assert variant_box["physics"]["collision_proxy"]["source"] == "mesh_quantile_bbox"
    assert variant_box["pose"]["position"] == [0.0, 0.55, 0.0]
    assert variant_box["pose"]["bbox_size"] == [1.04, 1.04, 1.04]
    assert variant_box["bbox_3d"]["size"] == variant_box["pose"]["bbox_size"]
    assert original_box["pose"]["bbox_size"] == [3.0, 1.0, 3.0]

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert manifest["artifacts"]["simfoundry_tight_collider_variant_bundle"] == str(variant_path)
    assert manifest["external_stages"]["simfoundry_tight_collider_variant"]["status"] == "tight_collider_ready"


def test_prepare_simfoundry_tight_collider_variant_preserves_structural_review_proxy(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    plan_path = project_root / "simulator_assets" / "structural_repair_plan.json"
    write_json(
        plan_path,
        {
            "schema_version": 1,
            "stage": "simfoundry_structural_repair_plan",
            "scene_id": "simfoundry-test-scene",
            "status": "structural_repair_plan_ready",
            "bundle": str(bundle_path),
            "summary": {"required_issue_count": 0, "warning_count": 0},
        },
    )
    review_patch_path = project_root / "simulator_assets" / "structural_repair_patch.json"
    write_json(
        review_patch_path,
        {
            "schema_version": 1,
            "structural_repair_patch": {
                "bundle_patch": {"metadata": {"review": "accepted"}},
                "object_patches": [
                    {
                        "object_id": "box_001",
                        "review_status": "accepted",
                        "bbox": {"center": [0.0, 0.5, 0.0], "size": [0.25, 0.5, 0.25]},
                        "physics": {"body_type": "static", "collider": "box"},
                    }
                ],
            },
        },
    )
    import_dir = project_root / "simulator_assets" / "structural_repair_import"
    assert (
        main(
            [
                "import-simfoundry-structural-repair",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--repair-plan",
                str(plan_path),
                "--review-patch",
                str(review_patch_path),
                "--output-dir",
                str(import_dir),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )
    sidecar_bundle = import_dir / "simulator_asset_bundle.structural_repair.json"
    assert (
        main(
            [
                "prepare-simfoundry-tight-collider-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(sidecar_bundle),
                "--no-include-background",
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    tight_report = json.loads(Path(manifest["artifacts"]["simfoundry_tight_collider_variant_report"]).read_text(encoding="utf-8"))
    tight_bundle = json.loads(Path(manifest["artifacts"]["simfoundry_tight_collider_variant_bundle"]).read_text(encoding="utf-8"))
    box = next(obj for obj in tight_bundle["objects"] if obj["object_id"] == "box_001")

    assert tight_report["summary"]["preserved_count"] == 1
    assert tight_report["summary"]["updated_count"] == 0
    assert tight_report["preserved"]["box_001"]["reason"] == "reviewed_structural_repair_collision_proxy"
    assert box["collision_proxy"]["source"] == "simfoundry_structural_repair_review_patch"
    assert box["pose"]["bbox_size"] == [0.25, 0.5, 0.25]


def test_prepare_simfoundry_dynamic_variant_keeps_unsupported_candidate_static(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    box["physics"]["body_type"] = "static"
    write_json(bundle_path, bundle)

    assert main(
        [
            "prepare-simfoundry-dynamic-variant",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
        ]
    ) == 0

    report = json.loads((project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "dynamic_variant_report.json").read_text(encoding="utf-8"))
    variant = json.loads((project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "simulator_asset_bundle.dynamic_variant.json").read_text(encoding="utf-8"))
    variant_box = next(obj for obj in variant["objects"] if obj["object_id"] == "box_001")
    box_report = next(obj for obj in report["objects"] if obj["object_id"] == "box_001")
    assert report["status"] == "dynamic_variant_empty"
    assert report["summary"]["accepted_dynamic_count"] == 0
    assert variant_box["physics"]["body_type"] == "static"
    assert "unsupported" in box_report["reasons"]


def test_prepare_simfoundry_dynamic_variant_accepts_reviewed_support_relation(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    box["physics"]["body_type"] = "static"
    box["support_relation_review"] = {
        "decision": "accepted",
        "support_id": "floor_001",
        "confidence": 0.82,
        "source": "mock_structural_review",
    }
    write_json(bundle_path, bundle)

    assert main(
        [
            "prepare-simfoundry-dynamic-variant",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    report = json.loads((project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "dynamic_variant_report.json").read_text(encoding="utf-8"))
    variant = json.loads((project_root / "simulator_assets" / "simfoundry_dynamic_variant" / "simulator_asset_bundle.dynamic_variant.json").read_text(encoding="utf-8"))
    variant_box = next(obj for obj in variant["objects"] if obj["object_id"] == "box_001")
    box_report = next(obj for obj in report["objects"] if obj["object_id"] == "box_001")

    assert report["status"] == "dynamic_variant_ready"
    assert report["summary"]["accepted_dynamic_count"] == 1
    assert variant_box["physics"]["body_type"] == "dynamic"
    assert variant_box["simfoundry_dynamic_variant"]["support"]["object_id"] == "floor_001"
    assert variant_box["simfoundry_dynamic_variant"]["support"]["source"] == "reviewed_support_relation"
    assert box_report["support"]["confidence"] == 0.82


def test_simfoundry_dynamic_blocker_report_summarizes_repair_queue(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["simfoundry-dynamic-blocker-report", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_simfoundry_dynamic_blocker_report"
    assert args.max_objects == 20
    assert args.max_penetrations == 5

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    box["physics"]["body_type"] = "static"
    lamp = {
        "schema_version": 1,
        "object_id": "lamp_001",
        "asset_role": "object",
        "name": "lamp",
        "category": "lamp",
        "mesh": None,
        "collision_proxy": {"path": "simulator_assets/colliders/objects/lamp_001.obj", "shape": "box"},
        "pose": {
            "position": [0.0, 2.0, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [1.0, 1.0, 1.0],
        },
        "physics": {
            "body_type": "static",
            "collider": "box",
            "mass_kg": 0.6,
            "material": {"name": "rigid", "friction": [0.7, 0.02, 0.001], "restitution": 0.1},
        },
    }
    bundle["objects"].append(lamp)
    write_json(bundle_path, bundle)

    dynamic_output = project_root / "simulator_assets" / "simfoundry_dynamic_from_tight_variant"
    assert main(
        [
            "prepare-simfoundry-dynamic-variant",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--output-dir",
            str(dynamic_output),
            "--json",
        ]
    ) == 0

    report_path = dynamic_output / "dynamic_blocker_report.json"
    md_path = dynamic_output / "dynamic_blocker_report.md"
    assert main(
        [
            "simfoundry-dynamic-blocker-report",
            "--project-root",
            str(project_root),
            "--report",
            str(dynamic_output / "dynamic_variant_report.json"),
            "--output",
            str(report_path),
            "--markdown-output",
            str(md_path),
            "--json",
        ]
    ) == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")
    queue_by_id = {item["object_id"]: item for item in report["repair_queue"]}

    assert report["stage"] == "simfoundry_dynamic_blocker_report"
    assert report["status"] == "dynamic_blockers_found"
    assert report["summary"]["candidate_count"] == 2
    assert report["summary"]["accepted_dynamic_count"] == 0
    assert report["summary"]["blocked_candidate_count"] == 2
    assert report["summary"]["unsupported_candidate_count"] == 2
    assert report["summary"]["penetration_candidate_count"] == 2
    assert report["candidate_reason_counts"]["unsupported"] == 2
    assert report["candidate_reason_counts"]["penetration"] == 2
    assert queue_by_id["box_001"]["priority"] == "p0_support_and_penetration"
    assert queue_by_id["box_001"]["top_penetrations"][0]["object_id"] == "lamp_001"
    assert report["top_penetration_blockers"][0]["affected_candidate_count"] >= 1
    assert "SimFoundry Dynamic Blocker Report" in markdown
    assert "`box_001`" in markdown

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["artifacts"]["simfoundry_dynamic_blocker_report"] == str(report_path)
    assert manifest["artifacts"]["simfoundry_dynamic_blocker_report_md"] == str(md_path)
    assert manifest["external_stages"]["simfoundry_dynamic_blocker_report"]["status"] == "dynamic_blockers_found"


def test_prepare_simfoundry_dynamic_readiness_writes_non_mutating_sidecar(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-dynamic-readiness", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_dynamic_readiness"
    assert args.smoke_test is True
    assert args.fail_on_blocked is False
    assert args.format == ["mujoco", "unity", "isaac"]

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    box["pose"]["bbox_3d"] = {"center": [0.0, 0.55, 0.0], "size": [1.0, 1.0, 1.0]}
    box["physics"]["body_type"] = "static"
    write_json(bundle_path, bundle)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0

    assert main(
        [
            "prepare-simfoundry-dynamic-readiness",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--no-include-background",
            "--mujoco-runtime",
            "skip",
            "--json",
            "--fail-on-required",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_dynamic_readiness_report"])
    dynamic_bundle_path = Path(manifest["artifacts"]["simfoundry_dynamic_readiness_bundle"])
    adapter_manifest_path = Path(manifest["artifacts"]["simfoundry_dynamic_readiness_adapters"])
    smoke_path = Path(manifest["artifacts"]["simfoundry_dynamic_readiness_smoke_report"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dynamic_bundle = json.loads(dynamic_bundle_path.read_text(encoding="utf-8"))
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    adapter_manifest = json.loads(adapter_manifest_path.read_text(encoding="utf-8"))
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))

    assert report["stage"] == "simfoundry_dynamic_readiness"
    assert report["status"] == "dynamic_release_ready"
    assert report["summary"]["accepted_dynamic_count"] == 1
    assert report["summary"]["blocked_candidate_count"] == 0
    assert report["summary"]["adapter_count"] == 3
    assert report["summary"]["smoke_required_issue_count"] == 0
    assert "box_001" in report["accepted_dynamic_objects"]
    dynamic_box = next(obj for obj in dynamic_bundle["objects"] if obj["object_id"] == "box_001")
    original_box = next(obj for obj in original_bundle["objects"] if obj["object_id"] == "box_001")
    assert dynamic_box["physics"]["body_type"] == "dynamic"
    assert original_box["physics"]["body_type"] == "static"
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert adapter_manifest["source_bundle"] == str(dynamic_bundle_path)
    assert sorted(adapter_manifest["formats"]) == ["isaac", "mujoco", "unity"]
    assert smoke["bundle"] == str(dynamic_bundle_path)
    assert smoke["mujoco_runtime"]["status"] == "skipped"
    assert Path(report["dynamic_blocker_report"]).exists()


def test_prepare_simfoundry_provider_jobs_writes_safe_external_model_templates(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-provider-jobs", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_provider_jobs"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.model == "gpt-5-codex"
    assert args.model_reasoning_effort == "high"
    assert args.image_model == "gpt-image-2"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["selected_frames"] = [
        {"frame_id": 1, "image": "frames/000001.png"},
        {"frame_id": 2, "image": "frames/000002.png"},
    ]
    box["object_images"] = [
        {"image": "objects/box_001/crops/000001.png"},
        {"image": "objects/box_001/crops/000002.png"},
    ]
    write_json(bundle_path, bundle)

    exit_code = main(
        [
            "prepare-simfoundry-provider-jobs",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--max-evidence-images",
            "1",
            "--json",
            "--fail-on-empty",
        ]
    )
    assert exit_code == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    jobs_manifest_path = Path(manifest["artifacts"]["simfoundry_provider_jobs"])
    provider_config_path = Path(manifest["artifacts"]["simfoundry_provider_config_template"])
    assert jobs_manifest_path.exists()
    assert provider_config_path.exists()

    payload = json.loads(jobs_manifest_path.read_text(encoding="utf-8"))
    provider_config = json.loads(provider_config_path.read_text(encoding="utf-8"))
    assert payload["stage"] == "simfoundry_provider_jobs"
    assert payload["summary"]["object_job_count"] == 1
    assert payload["summary"]["skipped_count"] == 1
    assert "floor_001" in payload["skipped"]
    assert payload["summary"]["model_provider"] == "custom"
    assert payload["summary"]["reasoning_model"] == "gpt-5-codex"
    assert payload["summary"]["image_model"] == "gpt-image-2"
    assert payload["summary"]["disable_response_storage"] is True
    assert provider_config["provider"]["name"] == "Sub2API"
    assert provider_config["provider"]["base_url"] == "https://plbbl.com"
    assert provider_config["provider"]["wire_api"] == "responses"
    assert provider_config["provider"]["auth_env"] == "OPENAI_API_KEY"
    assert provider_config["provider"]["disable_response_storage"] is True
    assert provider_config["secret_policy"]["store_plaintext_keys"] is False
    assert provider_config["request_defaults"]["store"] is False
    assert provider_config["request_defaults"]["disable_response_storage"] is True

    object_job_path = project_root / "simulator_assets" / "simfoundry_provider_jobs" / "objects" / "box_001" / "provider_job.json"
    object_job = json.loads(object_job_path.read_text(encoding="utf-8"))
    assert object_job["jobs"]["image_editing"]["enabled"] is True
    assert object_job["jobs"]["image_editing"]["model"] == "gpt-image-2"
    assert object_job["jobs"]["object_mesh_generation"]["candidate_models"] == ["hunyuan3d", "trellis", "image-blaster"]
    assert object_job["jobs"]["collider_generation"]["candidate_models"] == ["coacd", "vhacd", "bbox"]
    assert object_job["evidence"]["selected_frames"] == ["frames/000001.png"]
    assert object_job["evidence"]["object_images"] == ["objects/box_001/crops/000001.png"]

    mesh_template = json.loads(Path(payload["mesh_manifest_template"]).read_text(encoding="utf-8"))
    physics_template = json.loads(Path(payload["physics_template"]).read_text(encoding="utf-8"))
    assert mesh_template["objects"][0]["object_id"] == "box_001"
    assert mesh_template["objects"][0]["provider"] == "simfoundry_external_mesh"
    assert physics_template["objects"][0]["object_id"] == "box_001"
    assert Path(payload["postprocess_script"]).exists()
    assert "prepare-simfoundry-object-colliders" in "\n".join(payload["postprocess_commands"])

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            jobs_manifest_path,
            provider_config_path,
            object_job_path,
            Path(payload["mesh_manifest_template"]),
            Path(payload["physics_template"]),
            Path(payload["postprocess_script"]),
        ]
    )
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert "OPENAI_API_KEY" in combined_text


def test_prepare_simfoundry_remote_handoff_writes_safe_server_plan(tmp_path, monkeypatch):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-remote-handoff", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_remote_handoff"
    assert args.remote_host == "connect.westc.seetacloud.com"
    assert args.remote_port == 22356
    assert args.remote_user == "root"
    assert args.remote_root == "/root/simfoundry_video2mesh"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.base_url == "https://plbbl.com"
    assert args.wire_api == "responses"
    assert args.model == "gpt-5-codex"
    assert args.model_reasoning_effort == "high"
    assert args.image_model == "gpt-image-2"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret-that-must-not-be-written")
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    assert main(["prepare-simfoundry-provider-jobs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json"]) == 0
    write_json(
        project_root
        / "simulator_assets"
        / "simfoundry_dynamic_readiness"
        / "dynamic_variant"
        / "dynamic_blocker_report.json",
        {
            "schema_version": 1,
            "stage": "simfoundry_dynamic_blocker_report",
            "status": "dynamic_blockers_found",
            "summary": {"blocked_candidate_count": 1},
        },
    )

    exit_code = main(
        [
            "prepare-simfoundry-remote-handoff",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--json",
            "--fail-on-missing-required",
        ]
    )
    assert exit_code == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    handoff_path = Path(manifest["artifacts"]["simfoundry_remote_handoff"])
    md_path = Path(manifest["artifacts"]["simfoundry_remote_handoff_md"])
    script_path = Path(manifest["artifacts"]["simfoundry_remote_handoff_script"])
    assert handoff_path.exists()
    assert md_path.exists()
    assert script_path.exists()

    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert handoff["stage"] == "simfoundry_remote_handoff"
    assert handoff["status"] == "remote_handoff_prepared"
    assert handoff["remote_target"]["ssh"] == "ssh -p 22356 root@connect.westc.seetacloud.com"
    assert handoff["remote_target"]["project_root"].startswith("/root/simfoundry_video2mesh/")
    assert handoff["provider_contract"]["model_provider"] == "custom"
    assert handoff["provider_contract"]["provider_name"] == "Sub2API"
    assert handoff["provider_contract"]["base_url"] == "https://plbbl.com"
    assert handoff["provider_contract"]["wire_api"] == "responses"
    assert handoff["provider_contract"]["model"] == "gpt-5-codex"
    assert handoff["provider_contract"]["model_reasoning_effort"] == "high"
    assert handoff["provider_contract"]["image_model"] == "gpt-image-2"
    assert handoff["provider_contract"]["disable_response_storage"] is True
    assert handoff["provider_contract"]["request_defaults"]["store"] is False
    assert handoff["provider_contract"]["secret_policy"]["store_plaintext_keys"] is False
    assert handoff["provider_contract"]["secret_policy"]["required_env_vars"] == ["OPENAI_API_KEY"]
    assert handoff["summary"]["remote_host"] == "connect.westc.seetacloud.com"
    assert handoff["summary"]["remote_port"] == 22356
    assert handoff["summary"]["reasoning_model"] == "gpt-5-codex"
    assert handoff["summary"]["image_model"] == "gpt-image-2"
    assert any(item["name"] == "simfoundry_provider_jobs" and item["exists"] for item in handoff["local_artifacts"])
    assert any(item["name"] == "simfoundry_dynamic_blocker_report" and item["exists"] for item in handoff["local_artifacts"])
    assert any("rsync -az" in command for command in handoff["sync_commands"])
    assert any("prepare-simfoundry-provider-jobs" in command for command in handoff["remote_provider_commands"])
    assert any("run-simfoundry-structural-review-worker" in command for command in handoff["remote_provider_commands"])
    assert any("simfoundry-simulator-smoke-test" in command for command in handoff["local_import_commands"])
    assert manifest["external_stages"]["simfoundry_remote_handoff"]["status"] == "remote_handoff_prepared"

    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in [handoff_path, md_path, script_path])
    script_text = script_path.read_text(encoding="utf-8")
    assert "remote-run-dry-run" in script_text
    assert "ssh -p 22356 root@connect.westc.seetacloud.com 'bash -s'" in script_text
    assert "--run-provider" not in script_text
    assert "<set-in-shell>" not in script_text
    assert "sk-test-secret-that-must-not-be-written" not in combined_text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert "OPENAI_API_KEY" in combined_text
    assert "gpt-5-codex" in combined_text
    assert "gpt-image-2" in combined_text
    assert "disable_response_storage" in combined_text
    assert "store" in combined_text


def test_prepare_simfoundry_object_cousins_writes_safe_variant_contracts(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-object-cousins", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_object_cousins"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.model == "gpt-5-codex"
    assert args.model_reasoning_effort == "high"
    assert args.image_model == "gpt-image-2"
    assert args.pose_models == "foundationpose,bbox_alignment"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["selected_frames"] = [{"image": "frames/000001.png"}]
    box["object_images"] = [{"image": "objects/box_001/crops/000001.png"}]
    write_json(bundle_path, bundle)

    assert (
        main(
            [
                "prepare-simfoundry-object-cousins",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--cousin-count",
                "2",
                "--cousin-intents",
                "appearance,geometry",
                "--max-evidence-images",
                "1",
                "--json",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    cousin_manifest_path = Path(manifest["artifacts"]["simfoundry_object_cousins"])
    provider_config_path = Path(manifest["artifacts"]["simfoundry_object_cousins_provider_config"])
    payload = json.loads(cousin_manifest_path.read_text(encoding="utf-8"))
    provider_config = json.loads(provider_config_path.read_text(encoding="utf-8"))

    assert payload["stage"] == "simfoundry_object_cousins"
    assert payload["summary"]["object_count"] == 1
    assert payload["summary"]["cousin_variant_count"] == 2
    assert payload["summary"]["model_provider"] == "custom"
    assert payload["summary"]["provider_name"] == "Sub2API"
    assert payload["summary"]["reasoning_model"] == "gpt-5-codex"
    assert payload["summary"]["image_model"] == "gpt-image-2"
    assert payload["summary"]["pose_models"] == ["foundationpose", "bbox_alignment"]
    assert payload["summary"]["disable_response_storage"] is True
    assert "floor_001" in payload["skipped"]
    assert provider_config["provider"]["auth_env"] == "OPENAI_API_KEY"
    assert provider_config["secret_policy"]["store_plaintext_keys"] is False
    assert provider_config["cousin_defaults"]["cousin_count"] == 2

    object_spec_path = project_root / "simulator_assets" / "simfoundry_object_cousins" / "objects" / "box_001" / "object_cousin_spec.json"
    object_spec = json.loads(object_spec_path.read_text(encoding="utf-8"))
    assert object_spec["stage"] == "simfoundry_object_cousin"
    assert object_spec["evidence"]["selected_frames"] == ["frames/000001.png"]
    assert object_spec["evidence"]["object_images"] == ["objects/box_001/crops/000001.png"]
    assert object_spec["cousin_policy"]["preserve_scale"] is True
    assert len(object_spec["variants"]) == 2
    first_variant = object_spec["variants"][0]
    assert first_variant["model_plan"]["image_editing"]["model"] == "gpt-image-2"
    assert first_variant["model_plan"]["mesh_generation"]["candidate_models"] == ["hunyuan3d", "trellis", "image-blaster"]
    assert first_variant["model_plan"]["pose_scale_refinement"]["candidate_models"] == ["foundationpose", "bbox_alignment"]
    assert first_variant["model_plan"]["collider_generation"]["candidate_models"] == ["coacd", "vhacd", "bbox"]
    assert first_variant["import_contract"]["mesh_manifest_entry"]["provider"] == "simfoundry_object_cousin"
    assert first_variant["import_contract"]["mesh_manifest_entry"]["cousin_of"] == "box_001"

    mesh_template = json.loads(Path(payload["mesh_manifest_template"]).read_text(encoding="utf-8"))
    physics_template = json.loads(Path(payload["physics_template"]).read_text(encoding="utf-8"))
    collider_template = json.loads(Path(payload["collider_manifest_template"]).read_text(encoding="utf-8"))
    assert len(mesh_template["objects"]) == 2
    assert mesh_template["objects"][0]["source_object_id"] == "box_001"
    assert len(physics_template["objects"]) == 2
    assert len(collider_template["objects"]) == 2
    assert Path(payload["postprocess_script"]).exists()
    assert "build-simfoundry-object-colliders" in "\n".join(payload["postprocess_commands"])

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            cousin_manifest_path,
            provider_config_path,
            object_spec_path,
            Path(payload["mesh_manifest_template"]),
            Path(payload["physics_template"]),
            Path(payload["collider_manifest_template"]),
            Path(payload["postprocess_script"]),
        ]
    )
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert "OPENAI_API_KEY" in combined_text


def test_import_simfoundry_object_cousin_writes_sidecar_bundle_and_adapters(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["import-simfoundry-object-cousin", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_import_simfoundry_object_cousin"
    assert args.format == ["mujoco", "unity", "isaac"]
    assert args.replace_object_id is False

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert (
        main(
            [
                "prepare-simfoundry-object-cousins",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--cousin-count",
                "1",
                "--cousin-intents",
                "geometry",
                "--mesh-format",
                "obj",
                "--json",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    object_cousins_path = Path(manifest["artifacts"]["simfoundry_object_cousins"])
    object_cousins = json.loads(object_cousins_path.read_text(encoding="utf-8"))
    variant = object_cousins["objects"][0]["variants"][0]
    variant_id = variant["variant_id"]
    outputs_dir = Path(variant["model_plan"]["mesh_generation"]["expected_mesh"]).parent
    outputs_dir.mkdir(parents=True, exist_ok=True)
    mesh_path = outputs_dir / f"{variant_id}.obj"
    collider_path = outputs_dir / f"{variant_id}_collider.obj"
    mesh_path.write_text(
        "\n".join(
            [
                "v -0.4 -0.4 -0.4",
                "v 0.4 -0.4 -0.4",
                "v 0.4 0.4 -0.4",
                "v -0.4 0.4 -0.4",
                "v -0.4 -0.4 0.4",
                "v 0.4 -0.4 0.4",
                "v 0.4 0.4 0.4",
                "v -0.4 0.4 0.4",
                "f 1 2 3",
                "f 1 3 4",
                "f 5 6 7",
                "f 5 7 8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    collider_path.write_text(mesh_path.read_text(encoding="utf-8"), encoding="utf-8")
    mesh_manifest_path = project_root / "simulator_assets" / "simfoundry_object_cousins" / "mesh_manifest.filled.json"
    physics_path = project_root / "simulator_assets" / "simfoundry_object_cousins" / "physics_properties.filled.json"
    collider_manifest_path = project_root / "simulator_assets" / "simfoundry_object_cousins" / "collider_manifest.filled.json"
    write_json(
        mesh_manifest_path,
        {
            "schema_version": 1,
            "provider": "simfoundry_object_cousin",
            "objects": [
                {
                    "object_id": variant_id,
                    "source_object_id": "box_001",
                    "mesh_path": str(mesh_path),
                    "coordinate_frame": "object_local",
                    "quality": {"status": "controlled_demo_mesh"},
                }
            ],
        },
    )
    write_json(
        physics_path,
        {
            "schema_version": 1,
            "provider": "simfoundry_object_cousin_physics",
            "objects": [
                {
                    "object_id": variant_id,
                    "source_object_id": "box_001",
                    "body_type": "dynamic",
                    "collider": "box",
                    "mass_kg": 0.8,
                    "material": {"name": "demo_plastic", "friction": [0.7, 0.02, 0.001], "restitution": 0.08},
                    "source": "controlled_demo_physics",
                }
            ],
        },
    )
    write_json(
        collider_manifest_path,
        {
            "schema_version": 1,
            "objects": [
                {
                    "object_id": variant_id,
                    "source_object_id": "box_001",
                    "path": str(collider_path),
                    "shape": "box",
                    "provider": "controlled_demo_collider",
                }
            ],
        },
    )
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert (
        main(
            [
                "import-simfoundry-object-cousin",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--object-cousins",
                str(object_cousins_path),
                "--variant-id",
                variant_id,
                "--mesh-manifest",
                str(mesh_manifest_path),
                "--physics",
                str(physics_path),
                "--collider-manifest",
                str(collider_manifest_path),
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_object_cousin_import"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sidecar_bundle = json.loads(Path(report["sidecar_bundle"]).read_text(encoding="utf-8"))
    adapter_manifest = json.loads(Path(report["adapter_manifest"]).read_text(encoding="utf-8"))
    sidecar_box = next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "box_001")

    assert report["stage"] == "simfoundry_object_cousin_import"
    assert report["status"] == "object_cousin_imported"
    assert report["variant_id"] == variant_id
    assert report["summary"]["mesh_imported"] is True
    assert report["summary"]["physics_imported"] is True
    assert report["summary"]["collider_imported"] is True
    assert report["summary"]["main_bundle_overwritten"] is False
    assert sidecar_box["simfoundry_object_cousin"]["variant_id"] == variant_id
    assert sidecar_box["mesh"]["provider"] == "simfoundry_object_cousin"
    assert sidecar_box["physics"]["mass_kg"] == 0.8
    assert sidecar_box["physics"]["material"]["name"] == "demo_plastic"
    assert sidecar_box["collision_proxy"]["provider"] == "controlled_demo_collider"
    assert adapter_manifest["stage"] == "simfoundry_object_cousin_adapter"
    assert set(adapter_manifest["formats"]) == {"mujoco", "unity", "isaac"}
    assert Path(adapter_manifest["formats"]["mujoco"]["adapter_file"]).exists()
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == original_bundle
    assert manifest["external_stages"]["simfoundry_object_cousin_import"]["status"] == "object_cousin_imported"


def test_prepare_simfoundry_scene_cousins_writes_safe_scene_variant_contracts(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-scene-cousins", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_scene_cousins"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.model == "gpt-5-codex"
    assert args.model_reasoning_effort == "high"
    assert args.image_model == "gpt-image-2"
    assert args.scene_cousin_intents == "clean_plate,layout_perturbation,object_swap"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    assert (
        main(
            [
                "prepare-simfoundry-object-cousins",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--cousin-count",
                "1",
                "--json",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "prepare-simfoundry-scene-cousins",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--scene-cousin-count",
                "2",
                "--scene-cousin-intents",
                "clean_plate,object_swap",
                "--json",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    scene_manifest_path = Path(manifest["artifacts"]["simfoundry_scene_cousins"])
    provider_config_path = Path(manifest["artifacts"]["simfoundry_scene_cousins_provider_config"])
    payload = json.loads(scene_manifest_path.read_text(encoding="utf-8"))
    provider_config = json.loads(provider_config_path.read_text(encoding="utf-8"))

    assert payload["stage"] == "simfoundry_scene_cousins"
    assert payload["summary"]["scene_cousin_count"] == 2
    assert payload["summary"]["foreground_object_count"] == 1
    assert payload["summary"]["background_structure_count"] == 1
    assert payload["summary"]["model_provider"] == "custom"
    assert payload["summary"]["provider_name"] == "Sub2API"
    assert payload["summary"]["reasoning_model"] == "gpt-5-codex"
    assert payload["summary"]["image_model"] == "gpt-image-2"
    assert payload["summary"]["uses_object_cousins"] is True
    assert provider_config["provider"]["auth_env"] == "OPENAI_API_KEY"
    assert provider_config["secret_policy"]["store_plaintext_keys"] is False
    assert provider_config["scene_cousin_defaults"]["scene_cousin_count"] == 2
    assert provider_config["scene_cousin_defaults"]["scene_cousin_intents"] == ["clean_plate", "object_swap"]

    first_variant = payload["variants"][0]
    assert first_variant["stage"] == "simfoundry_scene_cousin_variant"
    assert first_variant["model_plan"]["image_editing_clean_plate"]["model"] == "gpt-image-2"
    assert first_variant["model_plan"]["scene_reasoning"]["model"] == "gpt-5-codex"
    assert first_variant["scope"]["selected_foreground_objects"] == ["box_001"]
    assert first_variant["scope"]["background_structures"] == ["floor_001"]
    assert first_variant["import_contract"]["main_bundle_overwritten"] is False
    assert first_variant["expected_artifacts"]["sidecar_bundle"].endswith(".json")

    patch_template = json.loads(Path(payload["scene_bundle_patch_template"]).read_text(encoding="utf-8"))
    relation_template = json.loads(Path(payload["scene_relations_template"]).read_text(encoding="utf-8"))
    assert len(patch_template["variants"]) == 2
    assert len(relation_template["variants"]) == 2
    assert Path(payload["postprocess_script"]).exists()
    assert "simfoundry-scene-stability-report" in "\n".join(payload["postprocess_commands"])

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            scene_manifest_path,
            provider_config_path,
            Path(payload["scene_bundle_patch_template"]),
            Path(payload["scene_relations_template"]),
            Path(payload["postprocess_script"]),
        ]
    )
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert "OPENAI_API_KEY" in combined_text


def test_prepare_simfoundry_task_cousins_writes_safe_task_variant_contracts(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-task-cousins", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_task_cousins"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.model == "gpt-5-codex"
    assert args.model_reasoning_effort == "high"
    assert args.image_model == "gpt-image-2"
    assert args.task_cousin_intents == "object_swap,scene_swap,goal_rephrase"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    floor = next(obj for obj in bundle["objects"] if obj["object_id"] == "floor_001")
    floor["pose"]["position"] = [0.0, -0.05, 0.0]
    floor["pose"]["bbox_size"] = [4.0, 0.1, 4.0]
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.55, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    box["selected_frames"] = [{"image": "frames/000001.png"}]
    box["object_images"] = [{"image": "objects/box_001/crops/000001.png"}]
    write_json(bundle_path, bundle)

    assert main(["export-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--refresh-relations", "--fail-on-empty"]) == 0
    assert main(["verify-simfoundry-task-specs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required"]) == 0
    assert main(["prepare-simfoundry-task-resets", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json", "--fail-on-required", "--fail-on-empty"]) == 0
    assert main(["export-simfoundry-task-reset-adapters", "--project-root", str(project_root), "--json", "--fail-on-required", "--fail-on-empty"]) == 0
    assert main(["prepare-simfoundry-object-cousins", "--project-root", str(project_root), "--bundle", str(bundle_path), "--cousin-count", "1", "--json", "--fail-on-empty"]) == 0
    assert main(["prepare-simfoundry-scene-cousins", "--project-root", str(project_root), "--bundle", str(bundle_path), "--scene-cousin-count", "1", "--json", "--fail-on-empty"]) == 0

    assert (
        main(
            [
                "prepare-simfoundry-task-cousins",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--task-cousin-count",
                "2",
                "--task-cousin-intents",
                "object_swap,goal_rephrase",
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    task_cousins_path = Path(manifest["artifacts"]["simfoundry_task_cousins"])
    provider_config_path = Path(manifest["artifacts"]["simfoundry_task_cousins_provider_config"])
    payload = json.loads(task_cousins_path.read_text(encoding="utf-8"))
    provider_config = json.loads(provider_config_path.read_text(encoding="utf-8"))

    assert payload["stage"] == "simfoundry_task_cousins"
    assert payload["summary"]["task_count"] == 1
    assert payload["summary"]["task_cousin_count"] == 2
    assert payload["summary"]["model_provider"] == "custom"
    assert payload["summary"]["provider_name"] == "Sub2API"
    assert payload["summary"]["reasoning_model"] == "gpt-5-codex"
    assert payload["summary"]["image_model"] == "gpt-image-2"
    assert payload["summary"]["uses_object_cousins"] is True
    assert payload["summary"]["uses_scene_cousins"] is True
    assert payload["summary"]["uses_reset_adapters"] is True
    assert provider_config["provider"]["auth_env"] == "OPENAI_API_KEY"
    assert provider_config["secret_policy"]["store_plaintext_keys"] is False
    assert provider_config["task_cousin_defaults"]["task_cousin_count"] == 2
    assert provider_config["task_cousin_defaults"]["task_cousin_intents"] == ["object_swap", "goal_rephrase"]

    first_variant = payload["variants"][0]
    assert first_variant["stage"] == "simfoundry_task_cousin_variant"
    assert first_variant["source_task_id"] == "place_on_box_001_floor_001"
    assert first_variant["task_context"]["manipulated_object"] == "box_001"
    assert first_variant["task_context"]["target_object"] == "floor_001"
    assert first_variant["task_context"]["reset_candidate_goal_status"] == "not_satisfied"
    assert first_variant["model_plan"]["task_reasoning"]["model"] == "gpt-5-codex"
    assert first_variant["model_plan"]["image_context_editing"]["model"] == "gpt-image-2"
    assert first_variant["source_links"]["task_reset_sidecar_bundle"].endswith(".json")
    assert first_variant["source_links"]["task_reset_adapter"].endswith("simulator_adapters.json")
    assert first_variant["import_contract"]["main_bundle_overwritten"] is False
    assert "success checker" in " ".join(first_variant["acceptance_gates"]).lower()

    task_template = json.loads(Path(payload["task_cousin_specs_template"]).read_text(encoding="utf-8"))
    success_template = json.loads(Path(payload["success_checkers_template"]).read_text(encoding="utf-8"))
    assert len(task_template["variants"]) == 2
    assert len(success_template["variants"]) == 2
    assert Path(payload["postprocess_script"]).exists()
    assert "export-simfoundry-task-reset-adapters" in "\n".join(payload["postprocess_commands"])
    assert manifest["external_stages"]["simfoundry_task_cousins"]["status"] == "task_cousins_prepared"

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            task_cousins_path,
            provider_config_path,
            Path(payload["task_cousin_specs_template"]),
            Path(payload["success_checkers_template"]),
            Path(payload["postprocess_script"]),
        ]
    )
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert "OPENAI_API_KEY" in combined_text


def test_import_simfoundry_scene_cousin_writes_sidecar_bundle_and_adapters(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["import-simfoundry-scene-cousin", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_import_simfoundry_scene_cousin"
    assert args.format == ["mujoco", "unity", "isaac"]
    assert args.body_type == "static"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    assert main(
        [
            "prepare-simfoundry-scene-cousins",
            "--project-root",
            str(project_root),
            "--bundle",
            str(bundle_path),
            "--scene-cousin-count",
            "1",
            "--scene-cousin-intents",
            "layout_perturbation",
            "--json",
            "--fail-on-empty",
        ]
    ) == 0

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    scene_cousins_path = Path(manifest["artifacts"]["simfoundry_scene_cousins"])
    scene_cousins = json.loads(scene_cousins_path.read_text(encoding="utf-8"))
    variant = scene_cousins["variants"][0]
    variant_id = variant["variant_id"]
    patch_path = Path(variant["expected_artifacts"]["bundle_patch"])
    write_json(
        patch_path,
        {
            "schema_version": 1,
            "patch_format": "sidecar_bundle_patch",
            "bundle_patch": {
                "scene_id": "simfoundry-test-scene-cousin",
                "objects": [
                    {
                        "object_id": "box_001",
                        "pose": {"position": [0.75, 0.55, 0.0]},
                        "simfoundry_scene_cousin_source": variant_id,
                    }
                ],
                "metadata": {"scene_cousin_note": "box shifted right for layout perturbation"},
            },
        },
    )
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert (
        main(
            [
                "import-simfoundry-scene-cousin",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--scene-cousins",
                str(scene_cousins_path),
                "--variant-id",
                variant_id,
                "--bundle-patch",
                str(patch_path),
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    import_report_path = Path(manifest["artifacts"]["simfoundry_scene_cousin_import"])
    report = json.loads(import_report_path.read_text(encoding="utf-8"))
    sidecar_bundle_path = Path(report["sidecar_bundle"])
    adapter_manifest_path = Path(report["adapter_manifest"])
    sidecar_bundle = json.loads(sidecar_bundle_path.read_text(encoding="utf-8"))
    adapter_manifest = json.loads(adapter_manifest_path.read_text(encoding="utf-8"))

    assert report["stage"] == "simfoundry_scene_cousin_import"
    assert report["status"] == "scene_cousin_imported"
    assert report["variant_id"] == variant_id
    assert report["import_mode"] == "bundle_patch"
    assert report["summary"]["main_bundle_overwritten"] is False
    assert sidecar_bundle["scene_id"] == "simfoundry-test-scene-cousin"
    assert sidecar_bundle["simfoundry_scene_cousin"]["variant_id"] == variant_id
    assert sidecar_bundle["simfoundry_scene_cousin"]["main_bundle_overwritten"] is False
    assert next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "box_001")["pose"]["position"] == [0.75, 0.55, 0.0]
    assert sidecar_bundle["metadata"]["scene_cousin_note"] == "box shifted right for layout perturbation"
    assert adapter_manifest["stage"] == "simfoundry_scene_cousin_adapter"
    assert set(adapter_manifest["formats"]) == {"mujoco", "unity", "isaac"}
    assert Path(adapter_manifest["formats"]["mujoco"]["adapter_file"]).exists()
    assert Path(adapter_manifest["formats"]["unity"]["adapter_file"]).exists()
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == original_bundle
    assert manifest["external_stages"]["simfoundry_scene_cousin_import"]["status"] == "scene_cousin_imported"


def test_prepare_simfoundry_penetration_repair_variant_writes_sidecar_without_overwriting_source(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-penetration-repair-variant", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_penetration_repair_variant"
    assert args.shrink_ratio == 0.7
    assert args.write_sidecar_bundle is True

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    scene_mesh = project_root / "simulator_assets" / "scene_meshes" / "tiny_scene.ply"
    write_tiny_scene_ply(scene_mesh)
    assert main(
        [
            "prepare-simfoundry-collider-scene",
            "--project-root",
            str(project_root),
            "--scene-mesh",
            str(scene_mesh),
            "--min-vertices",
            "1",
            "--min-triangles",
            "1",
        ]
    ) == 0
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 0.5, 0.0]
    box["pose"]["bbox_size"] = [1.0, 1.0, 1.0]
    wall = {
        "schema_version": 1,
        "object_id": "wall_001",
        "asset_role": "background_structure",
        "name": "wall",
        "category": "wall",
        "mesh": None,
        "collision_proxy": None,
        "pose": {
            "position": [0.0, 0.5, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [0.8, 0.8, 0.8],
        },
        "physics": {
            "body_type": "static",
            "collider": "box",
            "material": {"name": "wall", "friction": [0.9, 0.02, 0.001], "restitution": 0.0},
            "source": "manual_physics",
        },
    }
    bundle["objects"].append(wall)
    write_json(bundle_path, bundle)
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert (
        main(
            [
                "prepare-simfoundry-dynamic-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--include-objects",
                "box_001",
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    dynamic_report = Path(manifest["artifacts"]["simfoundry_dynamic_variant_report"])
    assert (
        main(
            [
                "simfoundry-dynamic-blocker-report",
                "--project-root",
                str(project_root),
                "--report",
                str(dynamic_report),
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    blocker_report = Path(manifest["artifacts"]["simfoundry_dynamic_blocker_report"])

    assert (
        main(
            [
                "prepare-simfoundry-penetration-repair-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--blocker-report",
                str(blocker_report),
                "--shrink-ratio",
                "0.5",
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    repair_report_path = Path(manifest["artifacts"]["simfoundry_penetration_repair_variant_report"])
    repair_bundle_path = Path(manifest["artifacts"]["simfoundry_penetration_repair_variant_bundle"])
    repair_md_path = Path(manifest["artifacts"]["simfoundry_penetration_repair_variant_md"])
    report = json.loads(repair_report_path.read_text(encoding="utf-8"))
    repair_bundle = json.loads(repair_bundle_path.read_text(encoding="utf-8"))
    repaired_box = next(obj for obj in repair_bundle["objects"] if obj["object_id"] == "box_001")

    assert report["stage"] == "simfoundry_penetration_repair_variant"
    assert report["status"] == "repair_variant_ready"
    assert report["summary"]["candidate_count"] >= 1
    assert report["summary"]["repair_count"] >= 1
    assert report["summary"]["before_penetration_count"] == report["summary"]["after_penetration_count"]
    assert report["summary"]["before_total_penetration_volume"] > report["summary"]["after_total_penetration_volume"]
    assert report["summary"]["before_max_penetration_depth"] > report["summary"]["after_max_penetration_depth"]
    assert report["summary"]["improved_penetration_severity"] is True
    assert repaired_box["pose"]["bbox_size"] == [0.5, 0.5, 0.5]
    assert repaired_box["physics"]["body_type"] == "static"
    assert repaired_box["collision_proxy"]["source"] == "simfoundry_penetration_repair_bbox_shrink"
    assert repaired_box["simfoundry_penetration_repair"]["main_bundle_overwritten"] is False
    assert "does not overwrite the main bundle" in repair_md_path.read_text(encoding="utf-8")
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == original_bundle
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert manifest["external_stages"]["simfoundry_penetration_repair_variant"]["status"] == "repair_variant_ready"


def test_prepare_simfoundry_structural_repair_plan_writes_review_sidecar(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["prepare-simfoundry-structural-repair-plan", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_prepare_simfoundry_structural_repair_plan"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.model == "gpt-5-codex"
    assert args.image_model == "gpt-image-2"
    assert args.auth_env == "OPENAI_API_KEY"

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    wall = {
        "schema_version": 1,
        "object_id": "wall_001",
        "asset_role": "background_structure",
        "name": "wall",
        "category": "wall",
        "mesh": None,
        "collision_proxy": None,
        "pose": {
            "position": [0.0, 2.0, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [1.0, 1.0, 1.0],
        },
        "physics": {
            "body_type": "static",
            "collider": "box",
            "material": {"name": "wall", "friction": [0.9, 0.02, 0.001], "restitution": 0.0},
            "source": "manual_physics",
        },
    }
    bundle["objects"].append(wall)
    write_json(bundle_path, bundle)
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert (
        main(
            [
                "prepare-simfoundry-dynamic-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--include-objects",
                "box_001",
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    dynamic_report = Path(manifest["artifacts"]["simfoundry_dynamic_variant_report"])
    assert (
        main(
            [
                "simfoundry-dynamic-blocker-report",
                "--project-root",
                str(project_root),
                "--report",
                str(dynamic_report),
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    blocker_report = Path(manifest["artifacts"]["simfoundry_dynamic_blocker_report"])

    assert (
        main(
            [
                "prepare-simfoundry-structural-repair-plan",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--blocker-report",
                str(blocker_report),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    plan_path = Path(manifest["artifacts"]["simfoundry_structural_repair_plan"])
    md_path = Path(manifest["artifacts"]["simfoundry_structural_repair_plan_md"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    object_plan = next(item for item in plan["object_repair_plans"] if item["object_id"] == "box_001")
    blocker_plan = next(item for item in plan["structural_blocker_plans"] if item["object_id"] == "wall_001")

    assert plan["stage"] == "simfoundry_structural_repair_plan"
    assert plan["status"] == "structural_repair_plan_ready"
    assert plan["provider_contract"]["auth_env"] == "OPENAI_API_KEY"
    assert plan["provider_contract"]["model"] == "gpt-5-codex"
    assert "sk-" not in json.dumps(plan).lower()
    assert object_plan["support_plan"]["status"] == "needs_review"
    assert object_plan["penetration_plan"]["status"] == "needs_review"
    assert "author_support_relation_or_pose_snap" in object_plan["actions"]
    assert "repair_semantic_split_or_collision_proxy" in object_plan["actions"]
    assert blocker_plan["action"] == "structural_semantic_split_or_bbox_refit"
    assert blocker_plan["affected_candidate_count"] >= 1
    assert plan["review_contract"]["main_bundle_overwritten"] is False
    assert "does not overwrite the main bundle" in md_path.read_text(encoding="utf-8")
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == original_bundle
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert manifest["external_stages"]["simfoundry_structural_repair_plan"]["status"] == "structural_repair_plan_ready"


def test_import_simfoundry_structural_repair_writes_sidecar_bundle_and_adapters(tmp_path):
    parser = build_parser()
    args = parser.parse_args(
        [
            "import-simfoundry-structural-repair",
            "--project-root",
            "proj",
            "--review-patch",
            "review.json",
        ]
    )
    assert args.func.__name__ == "cmd_import_simfoundry_structural_repair"
    assert args.provider == "simfoundry_structural_repair_review"
    assert args.format == ["mujoco", "unity", "isaac"]
    assert args.body_type == "static"
    assert args.allow_dynamic is False

    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    wall = {
        "schema_version": 1,
        "object_id": "wall_001",
        "asset_role": "background_structure",
        "name": "wall",
        "category": "wall",
        "mesh": None,
        "collision_proxy": None,
        "pose": {
            "position": [0.0, 2.0, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [1.0, 1.0, 1.0],
        },
        "physics": {
            "body_type": "static",
            "collider": "box",
            "material": {"name": "wall", "friction": [0.9, 0.02, 0.001], "restitution": 0.0},
            "source": "manual_physics",
        },
    }
    bundle["objects"].append(wall)
    write_json(bundle_path, bundle)
    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert (
        main(
            [
                "prepare-simfoundry-dynamic-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--include-objects",
                "box_001",
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    dynamic_report = Path(manifest["artifacts"]["simfoundry_dynamic_variant_report"])
    assert (
        main(
            [
                "simfoundry-dynamic-blocker-report",
                "--project-root",
                str(project_root),
                "--report",
                str(dynamic_report),
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    blocker_report = Path(manifest["artifacts"]["simfoundry_dynamic_blocker_report"])
    assert (
        main(
            [
                "prepare-simfoundry-structural-repair-plan",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--blocker-report",
                str(blocker_report),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    plan_path = Path(manifest["artifacts"]["simfoundry_structural_repair_plan"])
    review_patch_path = project_root / "simulator_assets" / "structural_review_patch.json"
    write_json(
        review_patch_path,
        {
            "schema_version": 1,
            "structural_repair_patch": {
                "bundle_patch": {"metadata": {"structural_repair_note": "wall refit accepted"}},
                "object_patches": [
                    {
                        "object_id": "wall_001",
                        "review_status": "accepted",
                        "bbox": {"center": [1.5, 2.0, 0.0], "size": [0.2, 0.8, 0.8]},
                        "physics": {"body_type": "static", "collider": "box"},
                        "semantic_split_review": {"decision": "refit_wall_bbox"},
                    },
                    {
                        "object_id": "box_001",
                        "review_status": "accepted",
                        "bbox": {"center": [0.0, 0.55, 0.0], "size": [0.8, 0.8, 0.8]},
                        "physics": {"body_type": "dynamic", "collider": "box"},
                        "support_relation_review": {"support_id": "floor_001", "decision": "supported"},
                    },
                ],
            },
        },
    )

    assert (
        main(
            [
                "import-simfoundry-structural-repair",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--repair-plan",
                str(plan_path),
                "--review-patch",
                str(review_patch_path),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_structural_repair_import"])
    sidecar_bundle_path = Path(manifest["artifacts"]["simfoundry_structural_repair_import_bundle"])
    import_md_path = Path(manifest["artifacts"]["simfoundry_structural_repair_import_md"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    sidecar_bundle = json.loads(sidecar_bundle_path.read_text(encoding="utf-8"))
    wall_sidecar = next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "wall_001")
    box_sidecar = next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "box_001")
    adapter_manifest = json.loads(Path(report["adapter_manifest"]).read_text(encoding="utf-8"))

    assert report["stage"] == "simfoundry_structural_repair_import"
    assert report["status"] == "structural_repair_imported"
    assert report["summary"]["applied_object_patch_count"] == 2
    assert report["summary"]["bundle_patch_applied"] is True
    assert report["summary"]["main_bundle_overwritten"] is False
    assert report["summary"]["warning_count"] == 1
    assert any(issue["name"] == "dynamic_release_blocked" for issue in report["issues"])
    assert sidecar_bundle["metadata"]["structural_repair_note"] == "wall refit accepted"
    assert wall_sidecar["pose"]["position"] == [1.5, 2.0, 0.0]
    assert wall_sidecar["pose"]["bbox_size"] == [0.2, 0.8, 0.8]
    assert wall_sidecar["collision_proxy"]["source"] == "simfoundry_structural_repair_review_patch"
    assert Path(wall_sidecar["collision_proxy"]["path"]).exists()
    assert wall_sidecar["semantic_split_review"]["decision"] == "refit_wall_bbox"
    assert box_sidecar["physics"]["body_type"] == "static"
    assert box_sidecar["support_relation_review"]["support_id"] == "floor_001"
    assert adapter_manifest["stage"] == "simfoundry_structural_repair_adapter"
    assert (sidecar_bundle_path.parent / "adapters" / "mujoco" / "scene.xml").exists()
    assert (sidecar_bundle_path.parent / "adapters" / "unity" / "unity_adapter.json").exists()
    assert (sidecar_bundle_path.parent / "adapters" / "isaac" / "isaac_adapter.json").exists()
    assert "does not overwrite the main bundle" in import_md_path.read_text(encoding="utf-8")
    assert json.loads(bundle_path.read_text(encoding="utf-8")) == original_bundle
    assert manifest["artifacts"]["simulator_asset_bundle"] == str(bundle_path)
    assert manifest["external_stages"]["simfoundry_structural_repair_import"]["status"] == "structural_repair_imported"


def test_run_simfoundry_structural_review_worker_dry_run_writes_safe_request(tmp_path, monkeypatch):
    parser = build_parser()
    args = parser.parse_args(["run-simfoundry-structural-review-worker", "--project-root", "proj"])
    assert args.func.__name__ == "cmd_run_simfoundry_structural_review_worker"
    assert args.model_provider == "custom"
    assert args.provider_name == "Sub2API"
    assert args.base_url == "https://plbbl.com"
    assert args.wire_api == "responses"
    assert args.model == "gpt-5-codex"
    assert args.image_model == "gpt-image-2"
    assert args.disable_response_storage is True
    assert args.auth_env == "OPENAI_API_KEY"
    assert args.run_provider is False

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret-that-must-not-be-written")
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    box = next(obj for obj in bundle["objects"] if obj["object_id"] == "box_001")
    box["physics"]["body_type"] = "static"
    box["pose"]["position"] = [0.0, 2.0, 0.0]
    wall = {
        "schema_version": 1,
        "object_id": "wall_001",
        "asset_role": "background_structure",
        "name": "wall",
        "category": "wall",
        "mesh": None,
        "collision_proxy": None,
        "pose": {
            "position": [0.0, 2.0, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [1.0, 1.0, 1.0],
        },
        "physics": {"body_type": "static", "collider": "box"},
    }
    bundle["objects"].append(wall)
    write_json(bundle_path, bundle)

    assert main(["prepare-simfoundry-provider-jobs", "--project-root", str(project_root), "--bundle", str(bundle_path), "--json"]) == 0
    assert (
        main(
            [
                "prepare-simfoundry-dynamic-variant",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--include-objects",
                "box_001",
                "--json",
                "--fail-on-required",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    dynamic_report = Path(manifest["artifacts"]["simfoundry_dynamic_variant_report"])
    assert main(["simfoundry-dynamic-blocker-report", "--project-root", str(project_root), "--report", str(dynamic_report), "--json"]) == 0
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    blocker_report = Path(manifest["artifacts"]["simfoundry_dynamic_blocker_report"])
    assert (
        main(
            [
                "prepare-simfoundry-structural-repair-plan",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--blocker-report",
                str(blocker_report),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "run-simfoundry-structural-review-worker",
                "--project-root",
                str(project_root),
                "--object-id",
                "wall_001",
                "--max-objects",
                "1",
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report_path = Path(manifest["artifacts"]["simfoundry_structural_review_worker"])
    request_path = Path(manifest["artifacts"]["simfoundry_structural_review_request"])
    patch_path = Path(manifest["artifacts"]["simfoundry_structural_review_patch"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    request = json.loads(request_path.read_text(encoding="utf-8"))
    patch = json.loads(patch_path.read_text(encoding="utf-8"))

    assert report["stage"] == "simfoundry_structural_review_worker"
    assert report["status"] == "dry_run_request_prepared"
    assert report["summary"]["provider_called"] is False
    assert report["summary"]["object_patch_count"] == 1
    assert request["endpoint"] == "https://plbbl.com/v1/responses"
    assert request["request_body"]["model"] == "gpt-5-codex"
    assert request["request_body"]["store"] is False
    assert request["request_body"]["reasoning"]["effort"] == "high"
    assert request["provider_contract"]["auth_env"] == "OPENAI_API_KEY"
    assert patch["source"] == "simfoundry_structural_review_worker_dry_run"
    assert patch["structural_repair_patch"]["object_patches"][0]["object_id"] == "wall_001"
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in [report_path, request_path, patch_path])
    assert "sk-test-secret-that-must-not-be-written" not in combined_text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", combined_text) is None
    assert manifest["external_stages"]["simfoundry_structural_review_worker"]["status"] == "dry_run_request_prepared"


def test_run_simfoundry_structural_review_worker_mock_response_imports_patch(tmp_path):
    project_root, bundle_path = make_minimal_simulator_project(tmp_path)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    wall = {
        "schema_version": 1,
        "object_id": "wall_001",
        "asset_role": "background_structure",
        "name": "wall",
        "category": "wall",
        "mesh": None,
        "collision_proxy": None,
        "pose": {
            "position": [0.0, 2.0, 0.0],
            "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
            "scale": [1.0, 1.0, 1.0],
            "bbox_size": [1.0, 1.0, 1.0],
        },
        "physics": {"body_type": "static", "collider": "box"},
    }
    bundle["objects"].append(wall)
    write_json(bundle_path, bundle)
    plan_path = project_root / "simulator_assets" / "structural_repair_plan.json"
    write_json(
        plan_path,
        {
            "schema_version": 1,
            "stage": "simfoundry_structural_repair_plan",
            "scene_id": "simfoundry-test-scene",
            "status": "structural_repair_plan_ready",
            "bundle": str(bundle_path),
            "provider_contract": {
                "model_provider": "custom",
                "provider_name": "Sub2API",
                "base_url": "https://plbbl.com",
                "wire_api": "responses",
                "model": "gpt-5-codex",
                "image_model": "gpt-image-2",
                "model_reasoning_effort": "high",
                "disable_response_storage": True,
                "auth_env": "OPENAI_API_KEY",
            },
            "object_repair_plans": [
                {"object_id": "wall_001", "category": "wall", "asset_role": "background_structure", "actions": ["repair_semantic_split_or_collision_proxy"]}
            ],
            "structural_blocker_plans": [],
            "summary": {"required_issue_count": 0, "warning_count": 0},
        },
    )
    mock_response_path = project_root / "simulator_assets" / "mock_response.json"
    write_json(
        mock_response_path,
        {
            "id": "resp_mock",
            "output_text": json.dumps(
                {
                    "schema_version": 1,
                    "structural_repair_patch": {
                        "bundle_patch": {"metadata": {"mock_review": "accepted"}},
                        "object_patches": [
                            {
                                "object_id": "wall_001",
                                "review_status": "accepted",
                                "bbox": {"center": [1.0, 2.0, 0.0], "size": [0.2, 0.8, 0.8]},
                                "physics": {"body_type": "static", "collider": "box"},
                                "semantic_split_review": {"decision": "mock_refit"},
                            }
                        ],
                    },
                }
            ),
        },
    )

    assert (
        main(
            [
                "run-simfoundry-structural-review-worker",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--repair-plan",
                str(plan_path),
                "--mock-provider-response",
                str(mock_response_path),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads(Path(manifest["artifacts"]["simfoundry_structural_review_worker"]).read_text(encoding="utf-8"))
    patch_path = Path(manifest["artifacts"]["simfoundry_structural_review_patch"])
    assert report["status"] == "mock_review_patch_written"
    assert report["summary"]["mock_provider_response"] is True
    assert report["summary"]["object_patch_count"] == 1

    assert (
        main(
            [
                "import-simfoundry-structural-repair",
                "--project-root",
                str(project_root),
                "--bundle",
                str(bundle_path),
                "--repair-plan",
                str(plan_path),
                "--review-patch",
                str(patch_path),
                "--json",
                "--fail-on-required",
                "--fail-on-empty",
            ]
        )
        == 0
    )
    manifest = json.loads((project_root / "manifest.json").read_text(encoding="utf-8"))
    sidecar_bundle = json.loads(Path(manifest["artifacts"]["simfoundry_structural_repair_import_bundle"]).read_text(encoding="utf-8"))
    wall_sidecar = next(obj for obj in sidecar_bundle["objects"] if obj["object_id"] == "wall_001")
    assert sidecar_bundle["metadata"]["mock_review"] == "accepted"
    assert wall_sidecar["pose"]["position"] == [1.0, 2.0, 0.0]
    assert wall_sidecar["semantic_split_review"]["decision"] == "mock_refit"
