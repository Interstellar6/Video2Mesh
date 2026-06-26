import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from video2mesh.cli import (
    apply_3dgs_sparse_filter,
    build_observation_point_cloud,
    build_parser,
    bbox_proxy_mesh_from_points,
    clean_binary_object_mask,
    clip_mask_by_depth_quantiles,
    depth_to_normal_map,
    filter_points_by_dbscan_largest_cluster,
    filter_points_by_gaussian_attributes,
    filter_points_by_multiview_mask_consistency,
    filter_points_by_pca_quantiles,
    filter_points_by_quantile_bbox,
    filter_points_by_support_quantile_bbox,
    filter_observation_points_by_multiview_depth_consistency,
    filter_mask_by_depth_edges,
    export_viewer_plys,
    filter_colmap_points3d_file,
    make_object_masks_exclusive,
    mesh_support_quality_report,
    parse_ply_vertex_header,
    postprocess_mesh_with_point_support,
    prepare_3dgs_colmap_source,
    quantile_bounds_from_points,
    resolve_export_record_path,
    scaled_intrinsic_for_size,
    select_colmap_sparse_model,
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


def test_select_colmap_sparse_model_prefers_most_registered_images(tmp_path: Path):
    sparse_root = tmp_path / "sparse"
    model0 = sparse_root / "0"
    model1 = sparse_root / "1"
    for model, image_count, point_count in [(model0, 5, 50), (model1, 50, 10)]:
        model.mkdir(parents=True)
        (model / "cameras.txt").write_text("# Camera list\n1 PINHOLE 2 2 1 1 1 1\n", encoding="utf-8")
        image_lines = ["# Image list"]
        for idx in range(image_count):
            image_lines.append(f"{idx + 1} 1 0 0 0 0 0 0 1 {idx:06d}.png")
            image_lines.append("")
        (model / "images.txt").write_text("\n".join(image_lines) + "\n", encoding="utf-8")
        point_lines = ["# Point list"]
        for idx in range(point_count):
            point_lines.append(f"{idx + 1} 0 0 0 255 0 0 0.5 1 0 2 0")
        (model / "points3D.txt").write_text("\n".join(point_lines) + "\n", encoding="utf-8")

    selected, stats = select_colmap_sparse_model(sparse_root, model0)

    assert selected == model1.resolve()
    assert [(Path(item["path"]).name, item["image_count"]) for item in stats] == [("0", 5), ("1", 50)]


def test_export_viewer_plys_keeps_semantic_labels_out_of_supersplat_ply(tmp_path: Path):
    source = tmp_path / "semantic.ply"
    source.write_text(
        "\n".join(
            [
                "ply",
                "format ascii 1.0",
                "element vertex 2",
                "property float x",
                "property float y",
                "property float z",
                "property float f_dc_0",
                "property float f_dc_1",
                "property float f_dc_2",
                "property float opacity",
                "property float scale_0",
                "property float scale_1",
                "property float scale_2",
                "property float rot_0",
                "property float rot_1",
                "property float rot_2",
                "property float rot_3",
                "property int object_id",
                "property float object_probability",
                "end_header",
                "0 0 0 0 0 0 0 -4 -4 -4 1 0 0 0 3 0.9",
                "1 0 0 0 0 0 0 -4 -4 -4 1 0 0 0 4 0.8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = export_viewer_plys(source, tmp_path, "semantic", include_labels=True)

    header = parse_ply_vertex_header(Path(report["supersplat_ply"]))
    property_names = [name for name, _prop_type in header["properties"]]
    assert header["format"] == "binary_little_endian"
    assert "f_rest_44" in property_names
    assert "object_id" not in property_names
    assert "object_probability" not in property_names
    sidecar = Path(report["label_sidecar"])
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["object_id"] == [3, 4]
    assert payload["object_probability"] == [0.8999999761581421, 0.800000011920929]


def test_scaled_intrinsic_for_size_scales_focal_length_and_principal_point():
    intrinsic = {
        "w": 1280,
        "h": 720,
        "fx": 640.0,
        "fy": 680.0,
        "cx": 640.0,
        "cy": 360.0,
    }

    scaled = scaled_intrinsic_for_size(intrinsic, 432, 768)

    assert scaled["w"] == 432
    assert scaled["h"] == 768
    assert scaled["fx"] == 216.0
    assert scaled["fy"] == pytest.approx(725.3333333333333)
    assert scaled["cx"] == 216.0
    assert scaled["cy"] == 384.0


def test_depth_to_normal_map_returns_forward_normals_for_flat_depth():
    np = pytest.importorskip("numpy")
    depth = np.ones((4, 5), dtype=np.float32) * 2.0

    normals = depth_to_normal_map(depth, 100.0, 100.0)

    assert normals.shape == (4, 5, 3)
    assert normals[2, 2, 0] == pytest.approx(0.0)
    assert normals[2, 2, 1] == pytest.approx(0.0)
    assert normals[2, 2, 2] == pytest.approx(1.0)


def test_clean_binary_object_mask_keeps_largest_component():
    np = pytest.importorskip("numpy")
    mask = np.zeros((20, 20), dtype=bool)
    mask[2:5, 2:5] = True
    mask[8:18, 8:18] = True

    cleaned = clean_binary_object_mask(mask, kernel_size=1, keep_largest_component=True, min_component_pixels=1)

    assert int(cleaned.sum()) == 100
    assert cleaned[10, 10]
    assert not cleaned[3, 3]


def test_clip_mask_by_depth_quantiles_removes_far_tail():
    np = pytest.importorskip("numpy")
    depth = np.array([[1.0, 1.1, 1.2, 10.0]], dtype=np.float32)
    mask = np.ones_like(depth, dtype=bool)

    clipped, info = clip_mask_by_depth_quantiles(mask, depth, 0.0, 0.75)

    assert int(clipped.sum()) == 3
    assert not clipped[0, 3]
    assert info["max_depth"] < 10.0


def test_filter_mask_by_depth_edges_removes_large_depth_jump():
    np = pytest.importorskip("numpy")
    depth = np.ones((5, 5), dtype=np.float32)
    depth[:, 4] = 8.0
    mask = np.ones_like(depth, dtype=bool)

    filtered, info = filter_mask_by_depth_edges(mask, depth, edge_quantile=0.8, edge_max=0.5)

    assert int(filtered.sum()) < int(mask.sum())
    assert not filtered[2, 3]
    assert info["threshold"] <= 0.5


def test_quantile_bounds_from_points_ignores_outlier_tail():
    np = pytest.importorskip("numpy")
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [100.0, 100.0, 100.0],
        ],
        dtype=np.float64,
    )

    lower, upper = quantile_bounds_from_points(points, 0.0, 0.75, 0.0)

    assert lower.tolist() == pytest.approx([0.0, 0.0, 0.0])
    assert upper.tolist() == pytest.approx([26.5, 26.5, 26.5])


def test_filter_points_by_quantile_bbox_removes_outlier_points():
    np = pytest.importorskip("numpy")
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [100.0, 100.0, 100.0],
        ],
        dtype=np.float64,
    )
    colors = np.ones_like(points)

    filtered, filtered_colors, report = filter_points_by_quantile_bbox(points, colors, 0.0, 0.75, 0.0)

    assert filtered.shape == (3, 3)
    assert filtered_colors.shape == (3, 3)
    assert report["removed_points"] == 1


def test_filter_points_by_pca_quantiles_removes_axis_tail():
    np = pytest.importorskip("numpy")
    points = np.array([[float(i), 0.0, 0.0] for i in range(10)] + [[50.0, 0.0, 0.0]], dtype=np.float64)

    filtered, _colors, report = filter_points_by_pca_quantiles(points, None, 0.0, 0.9, 0.0)

    assert filtered.shape[0] == 10
    assert report["removed_points"] == 1


def test_filter_points_by_dbscan_largest_cluster_keeps_main_cluster():
    np = pytest.importorskip("numpy")
    pytest.importorskip("open3d")
    main = np.array([[0.0, 0.0, 0.0], [0.04, 0.0, 0.0], [0.0, 0.04, 0.0], [0.04, 0.04, 0.0]], dtype=np.float64)
    small = np.array([[1.0, 1.0, 1.0], [1.04, 1.0, 1.0]], dtype=np.float64)
    points = np.concatenate([main, small], axis=0)

    filtered, _colors, report = filter_points_by_dbscan_largest_cluster(points, None, eps=0.08, min_points=2)

    assert filtered.shape[0] == 4
    assert report["removed_points"] == 2


def test_filter_points_by_multiview_mask_consistency_keeps_mask_hits(tmp_path: Path):
    np = pytest.importorskip("numpy")
    Image = pytest.importorskip("PIL.Image")
    mask_dir = tmp_path / "masks" / "obj"
    mask_dir.mkdir(parents=True)
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[4:7, 4:7] = 255
    Image.fromarray(mask, mode="L").save(mask_dir / "000000.png")
    records = {"obj": [SimpleNamespace(frame_id="000000", path=mask_dir / "000000.png")]}
    camera_info = {
        "extrinsic_type": "world_to_camera",
        "extrinsic": {"000000": np.eye(4).tolist()},
        "intrinsic": {"w": 10, "h": 10, "fx": 1.0, "fy": 1.0, "cx": 5.0, "cy": 5.0},
    }
    points = np.array([[0.0, 0.0, 1.0], [4.0, 4.0, 1.0]], dtype=np.float64)
    args = Namespace(
        consistency_min_probability=0.5,
        probability_scale=255.0,
        consistency_max_frames=1,
        extrinsic_type="world_to_camera",
        consistency_min_projected=1,
        consistency_min_hits=1,
        consistency_min_hit_ratio=1.0,
        min_points=1,
        consistency_fallback_keep_original=False,
    )

    filtered, _colors, report = filter_points_by_multiview_mask_consistency(points, None, "obj", records, camera_info, args)

    assert filtered.shape == (1, 3)
    assert filtered[0].tolist() == pytest.approx([0.0, 0.0, 1.0])
    assert report["removed_points"] == 1


def test_filter_points_by_gaussian_attributes_removes_low_quality_gaussians():
    np = pytest.importorskip("numpy")
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    colors = np.ones((4, 3), dtype=np.float64)
    attrs = {
        "opacities": np.array([0.9, 0.8, 0.01, 0.9], dtype=np.float32),
        "scales": np.array(
            [
                [0.03, 0.03, 0.03],
                [0.04, 0.04, 0.04],
                [0.03, 0.03, 0.03],
                [100.0, 0.001, 0.001],
            ],
            dtype=np.float32,
        ),
    }
    args = Namespace(
        min_points=1,
        min_opacity=0.05,
        max_scale=1.0,
        max_scale_quantile=None,
        max_anisotropy=None,
        max_anisotropy_quantile=None,
        gaussian_attribute_fallback_keep_original=False,
    )

    filtered, filtered_colors, report = filter_points_by_gaussian_attributes(points, colors, attrs, args)

    np.testing.assert_allclose(filtered, np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float64))
    assert filtered_colors.shape == (2, 3)
    assert report["removed_points"] == 2
    assert report["thresholds"]["min_opacity"] == pytest.approx(0.05)
    assert report["thresholds"]["max_scale"] == pytest.approx(1.0)


def test_bbox_proxy_mesh_from_points_returns_box_mesh():
    np = pytest.importorskip("numpy")
    pytest.importorskip("open3d")
    points = np.array(
        [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [2.0, 1.0, 0.0],
            [0.0, 0.0, 0.5],
            [2.0, 0.0, 0.5],
            [0.0, 1.0, 0.5],
            [2.0, 1.0, 0.5],
        ],
        dtype=np.float64,
    )

    mesh, report = bbox_proxy_mesh_from_points(points, 0.0, 1.0, 0.0, 0.05)

    assert len(mesh.vertices) == 8
    assert len(mesh.triangles) == 12
    assert report["method"] == "quantile_aabb_proxy_from_observation_points"
    assert report["extent"] == pytest.approx([2.0, 1.0, 0.5])


def test_postprocess_mesh_with_point_support_crops_outlying_vertices():
    np = pytest.importorskip("numpy")
    o3d = pytest.importorskip("open3d")
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [10.0, 10.0, 10.0],
        ],
        dtype=np.float64,
    )
    triangles = np.array([[0, 1, 2], [1, 2, 3]], dtype=np.int32)
    mesh = o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(vertices),
        o3d.utility.Vector3iVector(triangles),
    )
    support = vertices[:3]
    args = Namespace(
        min_points=1,
        mesh_crop_to_support_bbox=True,
        mesh_crop_quantile_min=0.0,
        mesh_crop_quantile_max=1.0,
        mesh_crop_padding_ratio=0.0,
        mesh_keep_largest_component=True,
        simplify_triangles=0,
        smooth_iterations=0,
    )

    processed, report = postprocess_mesh_with_point_support(mesh, support, args)

    assert len(processed.vertices) == 3
    assert len(processed.triangles) == 1
    assert report["support_bbox_crop"]["removed_vertices"] == 1


def test_filter_observation_points_by_multiview_depth_consistency_uses_mask_and_depth(tmp_path: Path):
    np = pytest.importorskip("numpy")
    Image = pytest.importorskip("PIL.Image")
    mask_path = tmp_path / "mask.png"
    Image.fromarray(np.full((5, 5), 255, dtype=np.uint8), mode="L").save(mask_path)
    depth_path = tmp_path / "depth.npy"
    np.save(depth_path, np.ones((5, 5), dtype=np.float32) * 2.0)
    frames = [
        {
            "frame_id": "a",
            "mask": str(mask_path),
            "depth_npy": str(depth_path),
            "width": 5,
            "height": 5,
            "intrinsic": {"fx": 1.0, "fy": 1.0, "cx": 2.0, "cy": 2.0},
            "world_to_camera": np.eye(4).tolist(),
        },
        {
            "frame_id": "b",
            "mask": str(mask_path),
            "depth_npy": str(depth_path),
            "width": 5,
            "height": 5,
            "intrinsic": {"fx": 1.0, "fy": 1.0, "cx": 2.0, "cy": 2.0},
            "world_to_camera": np.eye(4).tolist(),
        },
    ]
    points = np.array([[0.0, 0.0, 2.0], [0.0, 0.0, 4.0]], dtype=np.float64)
    colors = np.ones((2, 3), dtype=np.float64)
    source_frames = np.array([0, 0], dtype=np.int32)
    args = Namespace(
        min_points=1,
        surface_consistency_min_probability=0.5,
        surface_consistency_depth_tolerance=0.05,
        surface_consistency_min_hits=1,
        surface_consistency_min_projected=1,
        surface_consistency_min_hit_ratio=0.0,
        surface_consistency_max_frames=0,
        surface_consistency_fallback_keep_original=False,
    )

    filtered, filtered_colors, report = filter_observation_points_by_multiview_depth_consistency(points, colors, source_frames, frames, args)

    np.testing.assert_allclose(filtered, np.array([[0.0, 0.0, 2.0]], dtype=np.float64))
    assert filtered_colors.shape == (1, 3)
    assert report["removed_points"] == 1


def test_filter_points_by_support_quantile_bbox_removes_spatial_tail():
    np = pytest.importorskip("numpy")
    points = np.array([[0.0, 0.0, 0.0], [0.1, 0.0, 0.0], [0.2, 0.0, 0.0], [10.0, 0.0, 0.0]], dtype=np.float64)
    colors = np.ones((4, 3), dtype=np.float64)
    args = Namespace(
        min_points=1,
        surface_crop_to_quantile_bbox=True,
        surface_bbox_quantile_min=0.0,
        surface_bbox_quantile_max=0.75,
        surface_bbox_padding_ratio=0.0,
        surface_crop_fallback_keep_original=False,
    )

    filtered, filtered_colors, report = filter_points_by_support_quantile_bbox(points, colors, args)

    assert filtered.shape == (3, 3)
    assert filtered_colors.shape == (3, 3)
    assert report["removed_points"] == 1


def test_mesh_support_quality_report_rejects_oversized_mesh():
    np = pytest.importorskip("numpy")
    o3d = pytest.importorskip("open3d")
    mesh = o3d.geometry.TriangleMesh.create_box(width=5.0, height=1.0, depth=1.0)
    support = np.array([[0.0, 0.0, 0.0], [1.0, 0.2, 0.2], [0.5, 0.1, 0.1]], dtype=np.float64)
    args = Namespace(
        quality_guard=True,
        quality_bbox_quantile_min=0.0,
        quality_bbox_quantile_max=1.0,
        quality_bbox_padding_ratio=0.0,
        quality_max_diagonal_ratio=1.5,
        quality_max_longest_axis_ratio=1.5,
        quality_max_center_distance_ratio=1.0,
    )

    report = mesh_support_quality_report(mesh, support, args)

    assert report["passed"] is False
    assert "mesh_longest_axis_exceeds_support" in report["issues"]


def test_resolve_export_record_path_remaps_stale_export_root(tmp_path: Path):
    project_root = tmp_path / "run_a"
    target = project_root / "simulator_assets" / "foo.txt"
    target.parent.mkdir(parents=True)
    target.write_text("ok")
    stale = Path("/root/autodl-tmp/workspace/Video2Mesh/exports/run_a/simulator_assets/foo.txt")

    assert resolve_export_record_path(stale, project_root) == target


def test_observation_depth_to_point_cloud_uses_mask_and_camera(tmp_path: Path):
    np = pytest.importorskip("numpy")
    Image = pytest.importorskip("PIL.Image")
    depth = np.ones((2, 2), dtype=np.float32) * 2.0
    depth_path = tmp_path / "depth.npy"
    np.save(depth_path, depth)
    mask_path = tmp_path / "mask.png"
    rgb_path = tmp_path / "rgb.png"
    Image.fromarray(np.array([[255, 0], [0, 0]], dtype=np.uint8), mode="L").save(mask_path)
    Image.fromarray(np.full((2, 2, 3), 128, dtype=np.uint8), mode="RGB").save(rgb_path)
    frame = {
        "depth_npy": str(depth_path),
        "mask": str(mask_path),
        "rgb": str(rgb_path),
        "width": 2,
        "height": 2,
        "intrinsic": {"fx": 2.0, "fy": 2.0, "cx": 0.0, "cy": 0.0},
        "world_to_camera": np.eye(4).tolist(),
    }

    points, colors = build_observation_point_cloud([frame], min_depth=0.1, max_depth=5.0, stride=1)

    assert points.shape == (1, 3)
    assert colors.shape == (1, 3)
    assert points[0].tolist() == pytest.approx([0.0, 0.0, 2.0])


def test_3dgs_mesh_cli_commands_are_registered():
    parser = build_parser()

    obs = parser.parse_args(["export-3dgs-mesh-observations", "--project-root", "proj"])
    recon = parser.parse_args(["reconstruct-3dgs-object-meshes", "--project-root", "proj"])
    semantic_recon = parser.parse_args(["reconstruct-semantic-3dgs-object-meshes", "--project-root", "proj"])
    neus = parser.parse_args(["prepare-neus-surface-jobs", "--project-root", "proj"])

    assert obs.func.__name__ == "cmd_export_3dgs_mesh_observations"
    assert recon.func.__name__ == "cmd_reconstruct_3dgs_object_meshes"
    assert recon.proxy_mesh == "none"
    assert recon.surface_consistency_filter is True
    assert recon.surface_consistency_min_projected == 2
    assert recon.surface_consistency_min_hit_ratio == pytest.approx(0.35)
    assert recon.surface_crop_to_quantile_bbox is True
    assert recon.quality_guard is True
    assert semantic_recon.func.__name__ == "cmd_reconstruct_semantic_3dgs_object_meshes"
    assert semantic_recon.gaussian_attribute_filter is True
    assert semantic_recon.max_scale_quantile == pytest.approx(0.90)
    assert semantic_recon.mesh_crop_to_support_bbox is True
    assert neus.func.__name__ == "cmd_prepare_neus_surface_jobs"
