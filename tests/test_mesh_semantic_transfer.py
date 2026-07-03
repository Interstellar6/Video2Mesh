import json
import struct
from argparse import Namespace
from pathlib import Path

from video2mesh.cli import (
    build_parser,
    cmd_split_mesh_by_semantics,
    cmd_transfer_mesh_semantics,
    read_triangle_mesh_for_semantic_transfer,
)


def write_tiny_indexed_glb(path: Path) -> None:
    vertices = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (2.0, 1.0, 0.0),
    ]
    indices = [0, 1, 2, 3, 4, 5]
    vertex_blob = b"".join(struct.pack("<3f", *vertex) for vertex in vertices)
    index_blob = b"".join(struct.pack("<H", index) for index in indices)
    if len(index_blob) % 4:
        index_blob += b"\x00" * (4 - len(index_blob) % 4)
    bin_blob = vertex_blob + index_blob
    gltf = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "mode": 4,
                    }
                ]
            }
        ],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(vertex_blob), "target": 34962},
            {"buffer": 0, "byteOffset": len(vertex_blob), "byteLength": 12, "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(vertices), "type": "VEC3"},
            {"bufferView": 1, "componentType": 5123, "count": len(indices), "type": "SCALAR"},
        ],
    }
    json_blob = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    if len(json_blob) % 4:
        json_blob += b" " * (4 - len(json_blob) % 4)
    total_length = 12 + 8 + len(json_blob) + 8 + len(bin_blob)
    path.write_bytes(
        b"glTF"
        + struct.pack("<II", 2, total_length)
        + struct.pack("<I4s", len(json_blob), b"JSON")
        + json_blob
        + struct.pack("<I4s", len(bin_blob), b"BIN\x00")
        + bin_blob
    )


def write_semantic_source(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "ply",
                "format ascii 1.0",
                "element vertex 4",
                "property float x",
                "property float y",
                "property float z",
                "property int object_id",
                "property float object_probability",
                "end_header",
                "0.30 0.30 0.00 1 0.95",
                "0.36 0.30 0.00 1 0.85",
                "2.30 0.30 0.00 2 0.90",
                "2.36 0.30 0.00 2 0.80",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_light_glb_reader_preserves_indexed_triangle_order(tmp_path: Path):
    mesh = tmp_path / "two_faces.glb"
    write_tiny_indexed_glb(mesh)

    vertices, triangles, reader = read_triangle_mesh_for_semantic_transfer(mesh)

    assert reader == "light_glb"
    assert vertices.shape == (6, 3)
    assert triangles.tolist() == [[0, 1, 2], [3, 4, 5]]


def test_transfer_mesh_semantics_writes_triangle_index_sidecar_for_glb(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "artifacts": {}, "simulator_assets_dir": "simulator_assets"}),
        encoding="utf-8",
    )
    semantic_ply = tmp_path / "semantic.ply"
    semantic_manifest = tmp_path / "semantic_manifest.json"
    mesh = tmp_path / "two_faces.glb"
    output_dir = tmp_path / "mesh_semantics"
    write_semantic_source(semantic_ply)
    write_tiny_indexed_glb(mesh)
    semantic_manifest.write_text(
        json.dumps(
            {
                "objects": [
                    {"semantic_id": 1, "object_id": "left_object", "name": "left", "category": "toy"},
                    {"semantic_id": 2, "object_id": "right_object", "name": "right", "category": "toy"},
                ]
            }
        ),
        encoding="utf-8",
    )

    rc = cmd_transfer_mesh_semantics(
        Namespace(
            project_root=project_root,
            semantic_splats_ply=semantic_ply,
            semantic_manifest=semantic_manifest,
            mesh=mesh,
            output_dir=output_dir,
            output=None,
            debug_ply=None,
            k=2,
            max_distance=1.0,
            max_distance_ratio=None,
            min_face_probability=0.1,
            min_vote_confidence=0.5,
            distance_power=2.0,
            distance_epsilon=1e-5,
            smooth_iterations=0,
            smooth_keep_probability=0.75,
            smooth_min_neighbors=2,
            min_component_faces=0,
            min_region_faces=0,
            semantic_max_points=0,
            semantic_min_points_per_label=1,
            seed=7,
        )
    )

    assert rc == 0
    payload = json.loads((output_dir / "two_faces_mesh_semantics.json").read_text())
    assert payload["parameters"]["mesh_reader"] == "light_glb"
    assert payload["summary"]["mesh_face_count"] == 2
    assert [item["object_id"] for item in payload["face_semantics"]] == ["left_object", "right_object"]
    assert payload["face_semantics"][0]["face"] == 0
    assert payload["face_semantics"][1]["face"] == 1
    assert (output_dir / "two_faces_semantic_debug.ply").exists()


def test_split_mesh_by_semantics_exports_scene_space_object_meshes(tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "objects" / "left_object").mkdir(parents=True)
    (project_root / "objects" / "right_object").mkdir(parents=True)
    (project_root / "objects" / "left_object" / "object.json").write_text(
        json.dumps({"schema_version": 1, "object_id": "left_object", "label": "left", "category": "toy"}),
        encoding="utf-8",
    )
    (project_root / "objects" / "right_object" / "object.json").write_text(
        json.dumps({"schema_version": 1, "object_id": "right_object", "label": "right", "category": "toy"}),
        encoding="utf-8",
    )
    mesh = tmp_path / "two_faces.glb"
    write_tiny_indexed_glb(mesh)
    semantics = tmp_path / "mesh_semantics.json"
    semantics.write_text(
        json.dumps(
            {
                "objects": {
                    "1": {"semantic_id": 1, "object_id": "left_object", "label": "left", "category": "toy", "mean_probability": 0.9},
                    "2": {"semantic_id": 2, "object_id": "right_object", "label": "right", "category": "toy", "mean_probability": 0.8},
                },
                "legend": {
                    "1": {"object_id": "left_object", "name": "left", "category": "toy"},
                    "2": {"object_id": "right_object", "name": "right", "category": "toy"},
                },
                "face_semantics": [
                    {"face": 0, "semantic_id": 1, "object_id": "left_object", "label": "left", "category": "toy", "probability": 0.9},
                    {"face": 1, "semantic_id": 2, "object_id": "right_object", "label": "right", "category": "toy", "probability": 0.8},
                ],
            }
        ),
        encoding="utf-8",
    )
    manifest_path = project_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifacts": {"scene_mesh_ply": str(mesh), "mesh_semantics_local": str(semantics)},
                "simulator_assets_dir": "simulator_assets",
                "objects_dir": "objects",
                "external_stages": {},
            }
        ),
        encoding="utf-8",
    )

    rc = cmd_split_mesh_by_semantics(
        Namespace(
            project_root=project_root,
            mesh=None,
            semantics=None,
            output_dir=None,
            min_faces=1,
            min_probability=0.0,
            include_unknown=False,
            copy_to_assets=True,
            register_as_object_meshes=True,
            mode="copy",
        )
    )

    assert rc == 0
    index = json.loads((project_root / "simulator_assets" / "semantic_object_meshes" / "semantic_object_meshes.json").read_text())
    assert sorted(index["objects"]) == ["left_object", "right_object"]
    assert Path(index["objects"]["left_object"]["source_mesh"]).exists()
    assert Path(index["objects"]["right_object"]["asset_path"]).exists()
    left_obj = json.loads((project_root / "objects" / "left_object" / "object.json").read_text())
    assert left_obj["mesh_asset"]["source"] == "scene_mesh_semantic_split"
    assert left_obj["mesh_asset"]["coordinate_frame"] == "video2mesh_scene"
    assert left_obj["bbox_3d"]["center"] == [0.5, 0.5, 0.0]
    assert left_obj["point_count"] == 3
    manifest = json.loads(manifest_path.read_text())
    assert manifest["artifacts"]["object_meshes"].endswith("semantic_object_meshes.json")


def test_transfer_mesh_semantics_cli_is_registered():
    parser = build_parser()
    args = parser.parse_args(
        [
            "transfer-mesh-semantics",
            "--project-root",
            "proj",
            "--mesh",
            "collider.glb",
        ]
    )

    assert args.func.__name__ == "cmd_transfer_mesh_semantics"
    assert args.k == 8
    assert abs(args.max_distance_ratio - 0.015) < 1e-12

    ray = parser.parse_args(
        [
            "transfer-mesh-semantics-ray",
            "--project-root",
            "proj",
            "--mesh",
            "collider.glb",
            "--camera-info",
            "camera_info.json",
            "--mask-root",
            "masks/2d",
        ]
    )
    assert ray.func.__name__ == "cmd_transfer_mesh_semantics_ray"
    assert ray.min_frame_votes == 1.0
    assert ray.min_vote_confidence == 0.55

    scene_mesh = parser.parse_args(["reconstruct-scene-meshes", "--project-root", "proj"])
    assert scene_mesh.func.__name__ == "cmd_reconstruct_scene_meshes"
    assert scene_mesh.method == "colmap_delaunay"
    assert scene_mesh.copy_input_point_cloud is True

    split = parser.parse_args(["split-mesh-by-semantics", "--project-root", "proj"])
    assert split.func.__name__ == "cmd_split_mesh_by_semantics"
    assert split.register_as_object_meshes is True
    assert split.min_faces == 20
