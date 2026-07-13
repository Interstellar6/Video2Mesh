import importlib.util
from pathlib import Path

import pytest

from video2mesh.cli import (
    audit_gaussian_health,
    export_viewer_plys,
    read_gsplat_ply,
    write_semantic_ply_with_labels,
    write_supersplat_ply,
)


def load_anysplat_projection_module():
    module_path = Path(__file__).resolve().parents[1] / "tools" / "prepare_anysplat_semantic_projection.py"
    spec = importlib.util.spec_from_file_location("prepare_anysplat_semantic_projection", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_anysplat_camera_to_world_is_inverted_for_video2mesh(tmp_path: Path):
    np = pytest.importorskip("numpy")
    module = load_anysplat_projection_module()
    cameras_path = tmp_path / "predicted_cameras.npz"
    camera_to_world = np.array(
        [
            [1.0, 0.0, 0.0, 2.0],
            [0.0, 1.0, 0.0, -3.0],
            [0.0, 0.0, 1.0, 4.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    intrinsic = np.array(
        [
            [0.8, 0.0, 0.5],
            [0.0, 0.9, 0.5],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    np.savez(cameras_path, extrinsic=camera_to_world[None, None], intrinsic=intrinsic[None, None])

    camera_info = module.camera_info_from_anysplat(cameras_path, ["000000"], 448)

    assert camera_info["extrinsic_type"] == "world_to_camera"
    assert camera_info["source_extrinsic_type"] == "camera_to_world"
    assert camera_info["extrinsic_conversion"] == "inverse(predicted_cameras.extrinsic)"
    np.testing.assert_allclose(camera_info["extrinsic"]["000000"], np.linalg.inv(camera_to_world))
    assert camera_info["intrinsics"]["0"]["fx"] == pytest.approx(0.8 * 448)
    assert camera_info["intrinsics"]["0"]["fy"] == pytest.approx(0.9 * 448)


def test_semantic_overlay_uses_viewer_safe_gaussian_arrays(tmp_path: Path):
    np = pytest.importorskip("numpy")
    source = tmp_path / "scene.ply"
    write_supersplat_ply(
        source,
        np.asarray([[0.0, 0.0, 1.0], [0.1, 0.0, 1.0]], dtype=np.float32),
        np.full((2, 3), 0.5, dtype=np.float32),
        np.full(2, 0.9, dtype=np.float32),
        np.asarray([[5.0, 1e-5, 1e-5], [0.03, 0.02, 0.01]], dtype=np.float32),
        np.asarray([[3.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
    )
    semantic = tmp_path / "semantic_core.ply"
    write_semantic_ply_with_labels(source, semantic, [1, 2], [0.9, 0.9])

    report = export_viewer_plys(
        semantic,
        tmp_path,
        "semantic",
        include_labels=True,
        export_point_cloud=False,
        semantic_overlay_max_vertices=2,
    )

    overlay = Path(report["semantic_overlay_supersplat_ply"])
    overlay_data = read_gsplat_ply(overlay)
    assert report["supersplat_ply"] is None
    assert report["semantic_overlay_supersplat_ply_info"]["viewer_safe_geometry"] is True
    assert audit_gaussian_health(overlay_data["scales"], overlay_data["quats"], overlay_data["opacities"])["status"] == "safe"
