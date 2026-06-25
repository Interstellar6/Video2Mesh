from argparse import Namespace
from pathlib import Path

from video2mesh.cli import (
    apply_3dgs_sparse_filter,
    filter_colmap_points3d_file,
    make_object_masks_exclusive,
    prepare_3dgs_colmap_source,
    source_labels_from_object_masks,
    write_json,
)


def test_exclusive_object_masks_keep_bed_points_before_large_structures():
    candidates = {
        "gdino_object_door": [1, 2, 3, 4],
        "gdino_object_bed": [3, 4, 5, 6],
        "gdino_object_floor": [4, 6, 7],
    }
    labels = {
        "gdino_object_bed": {"name": "bed", "category": "bed"},
        "gdino_object_door": {"name": "door", "category": "door"},
        "gdino_object_floor": {"name": "floor", "category": "floor"},
    }

    exclusive, report, ordered = make_object_masks_exclusive(
        candidates,
        labels=labels,
        priority_categories=["bed", "door", "floor"],
    )

    assert ordered == ["gdino_object_bed", "gdino_object_door", "gdino_object_floor"]
    assert exclusive["gdino_object_bed"].tolist() == [3, 4, 5, 6]
    assert exclusive["gdino_object_door"].tolist() == [1, 2]
    assert exclusive["gdino_object_floor"].tolist() == [7]
    removed = {item["object_id"]: item["removed_overlap_points"] for item in report}
    assert removed["gdino_object_door"] == 2
    assert removed["gdino_object_floor"] == 2


def test_exclusive_object_masks_default_uses_evidence_not_scene_categories():
    candidates = {
        "thing_a": [1, 2, 3],
        "thing_b": [2, 3, 4],
        "structure": [1, 2, 3, 4],
    }
    labels = {
        "thing_a": {"name": "mug", "category": "mug"},
        "thing_b": {"name": "book", "category": "book"},
        "structure": {"name": "surface", "category": "wall"},
    }

    exclusive, _report, ordered = make_object_masks_exclusive(
        candidates,
        labels=labels,
        priority_categories=[],
        probability_max_by_object={
            "thing_a": [0.9, 0.6, 0.6],
            "thing_b": [0.8, 0.8, 0.8],
            "structure": [0.7, 0.7, 0.7, 0.7],
        },
        observation_count_by_object={
            "thing_a": [3, 2, 2],
            "thing_b": [2, 4, 4],
            "structure": [1, 1, 1, 1],
        },
    )

    assert ordered == ["thing_a", "thing_b", "structure"]
    assert exclusive["thing_a"].tolist() == [1]
    assert exclusive["thing_b"].tolist() == [2, 3, 4]
    assert exclusive["structure"].tolist() == []


def test_filter_colmap_points3d_uses_track_length_and_error(tmp_path: Path):
    src = tmp_path / "points3D.txt"
    dst = tmp_path / "filtered.txt"
    src.write_text(
        "\n".join(
            [
                "# header",
                "1 0 0 0 255 0 0 0.5 1 0 2 0 3 0 4 0",
                "2 0 0 0 255 0 0 1.5 1 0 2 0 3 0 4 0",
                "3 0 0 0 255 0 0 0.5 1 0 2 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = filter_colmap_points3d_file(src, dst, max_error=1.0, min_track_length=4)

    lines = [line for line in dst.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
    assert [line.split()[0] for line in lines] == ["1"]
    assert report["total"] == 3
    assert report["kept"] == 1
    assert report["with_track"] == 3


def test_apply_3dgs_sparse_filter_skips_ply_export_without_tracks(tmp_path: Path):
    sparse = tmp_path / "sparse" / "0"
    sparse.mkdir(parents=True)
    points = sparse / "points3D.txt"
    points.write_text("# header\n1 0 0 0 128 128 128 0\n2 1 1 1 128 128 128 0\n", encoding="utf-8")

    report = apply_3dgs_sparse_filter(
        tmp_path,
        Namespace(filter_sparse_points=True, sparse_max_reprojection_error=1.0, sparse_min_track_length=4),
    )

    assert report["enabled"] is False
    assert report["reason"].startswith("points3D.txt has no TRACK[]")
    assert points.read_text(encoding="utf-8").count("\n") == 3


def test_source_labels_keep_first_priority_assignment(tmp_path: Path):
    mask_root = tmp_path / "masks" / "3d"
    objects_dir = tmp_path / "objects"
    for object_id, category, indices in [
        ("gdino_object_door", "door", [0, 1, 2]),
        ("gdino_object_bed", "bed", [1, 2, 3]),
        ("gdino_object_floor", "floor", [2, 3, 4]),
    ]:
        mask_dir = mask_root / object_id
        obj_dir = objects_dir / object_id
        mask_dir.mkdir(parents=True)
        obj_dir.mkdir(parents=True)
        write_json(mask_dir / "point_indices.json", indices)
        write_json(
            obj_dir / "object.json",
            {
                "object_id": object_id,
                "name": category,
                "category": category,
                "mask_3d": {"point_indices_json": str(mask_dir / "point_indices.json")},
            },
        )

    labels, _probabilities, table, object_id_to_semantic = source_labels_from_object_masks(mask_root, objects_dir, 5)

    assert [item["object_id"] for item in table[1:]] == ["gdino_object_bed", "gdino_object_door", "gdino_object_floor"]
    assert labels[1] == object_id_to_semantic["gdino_object_bed"]
    assert labels[2] == object_id_to_semantic["gdino_object_bed"]
    assert labels[3] == object_id_to_semantic["gdino_object_bed"]
    assert labels[0] == object_id_to_semantic["gdino_object_door"]
    assert labels[4] == object_id_to_semantic["gdino_object_floor"]


def test_prepare_3dgs_source_reuses_real_colmap_sparse_then_filters(tmp_path: Path):
    project = tmp_path / "project"
    sparse = project / "external" / "colmap" / "sparse_text" / "0"
    frames = project / "scene" / "frames"
    sparse.mkdir(parents=True)
    frames.mkdir(parents=True)
    (frames / "000000.png").write_bytes(b"fake")
    (sparse / "cameras.txt").write_text(
        "# Camera list\n1 PINHOLE 2 2 1 1 1 1\n",
        encoding="utf-8",
    )
    (sparse / "images.txt").write_text(
        "# Image list\n1 1 0 0 0 0 0 0 1 000000.png\n\n",
        encoding="utf-8",
    )
    (sparse / "points3D.txt").write_text(
        "\n".join(
            [
                "# header",
                "1 0 0 0 255 0 0 0.5 1 0 2 0 3 0 4 0",
                "2 0 0 0 255 0 0 1.5 1 0 2 0 3 0 4 0",
                "3 0 0 0 255 0 0 0.5 1 0 2 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = {
        "scene": {"frames_dir": "scene/frames", "point_cloud": "scene/reconstruction/point_cloud.ply"},
        "artifacts": {"colmap_sparse_text": str(sparse)},
    }

    source_path = project / "external" / "3dgs" / "colmap_source"
    manifest, source_report = prepare_3dgs_colmap_source(
        project,
        manifest,
        Namespace(
            use_existing_colmap_sparse=True,
            camera_info=None,
            point_cloud=None,
            frames_dir=None,
            camera_model="PINHOLE",
            extrinsic_type="world_to_camera",
            image_mode="copy",
        ),
        source_path,
    )
    report = apply_3dgs_sparse_filter(
        source_path,
        Namespace(filter_sparse_points=True, sparse_max_reprojection_error=1.0, sparse_min_track_length=4),
    )

    assert source_report["mode"] == "existing_colmap_sparse_text"
    assert report["enabled"] is True
    assert report["total"] == 3
    assert report["kept"] == 1
    points_lines = [
        line
        for line in (source_path / "sparse" / "0" / "points3D.txt").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert [line.split()[0] for line in points_lines] == ["1"]
