#!/usr/bin/env python3
"""Prepare an isolated bedroom_4 workspace for a real Holi-Spatial rerun."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_symlink(target: Path, link: Path) -> None:
    target = target.resolve()
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() == target:
            return
        link.unlink()
    elif link.exists():
        raise FileExistsError(f"Refusing to replace existing path: {link}")
    link.symlink_to(os.path.relpath(target, link.parent), target_is_directory=target.is_dir())


def corrected_transforms(
    camera_info: dict[str, Any],
    frames_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    intrinsic = camera_info["intrinsic"]
    extrinsics = camera_info["extrinsic"]
    extrinsic_type = camera_info.get("extrinsic_type", "world_to_camera")
    if extrinsic_type != "world_to_camera":
        raise ValueError(f"Expected world_to_camera camera_info, got {extrinsic_type!r}")

    frame_paths = sorted(
        path for path in frames_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not frame_paths:
        raise FileNotFoundError(f"No frames found under {frames_dir}")

    frames: list[dict[str, Any]] = []
    max_roundtrip_error = 0.0
    max_rotation_orthogonality_error = 0.0
    determinants: list[float] = []
    missing: list[str] = []

    for frame_path in frame_paths:
        frame_id = frame_path.stem
        raw = extrinsics.get(frame_id)
        if raw is None and frame_id.isdigit():
            raw = extrinsics.get(str(int(frame_id)))
        if raw is None:
            missing.append(frame_id)
            continue

        w2c = np.asarray(raw, dtype=np.float64)
        if w2c.shape != (4, 4):
            raise ValueError(f"Frame {frame_id} has invalid extrinsic shape {w2c.shape}")
        c2w_colmap = np.linalg.inv(w2c)
        c2w_opengl = c2w_colmap.copy()
        c2w_opengl[:3, 1:3] *= -1.0

        # This mirrors Holi-Spatial load_scannetppv2_poses exactly.
        recovered_c2w_colmap = c2w_opengl.copy()
        recovered_c2w_colmap[:3, 1:3] *= -1.0
        recovered_w2c = np.linalg.inv(recovered_c2w_colmap)
        max_roundtrip_error = max(max_roundtrip_error, float(np.max(np.abs(recovered_w2c - w2c))))

        rotation = w2c[:3, :3]
        max_rotation_orthogonality_error = max(
            max_rotation_orthogonality_error,
            float(np.max(np.abs(rotation @ rotation.T - np.eye(3)))),
        )
        determinants.append(float(np.linalg.det(rotation)))
        frames.append(
            {
                "file_path": frame_path.name,
                "transform_matrix": c2w_opengl.tolist(),
            }
        )

    if missing:
        raise KeyError(f"Missing camera extrinsics for {len(missing)} frame(s): {missing[:10]}")
    if max_roundtrip_error > 1e-7:
        raise ValueError(f"Camera round-trip error is too large: {max_roundtrip_error}")

    transforms = {
        "camera_model": "PINHOLE",
        "fl_x": float(intrinsic["fx"]),
        "fl_y": float(intrinsic["fy"]),
        "cx": float(intrinsic["cx"]),
        "cy": float(intrinsic["cy"]),
        "w": int(intrinsic["w"]),
        "h": int(intrinsic["h"]),
        "frames": frames,
        "test_frames": [],
        "coordinate_convention": {
            "transform_matrix": "camera_to_world_opengl",
            "source": "Video2Mesh camera_info extrinsic world_to_camera COLMAP",
            "conversion": "inverse(world_to_camera), then negate camera Y/Z columns",
            "holi_loader_behavior": "negates camera Y/Z columns again before inversion",
        },
    }
    report = {
        "frame_count": len(frames),
        "max_world_to_camera_roundtrip_abs_error": max_roundtrip_error,
        "max_rotation_orthogonality_abs_error": max_rotation_orthogonality_error,
        "rotation_determinant_min": min(determinants),
        "rotation_determinant_max": max(determinants),
        "passed": max_roundtrip_error <= 1e-7 and max_rotation_orthogonality_error <= 1e-4,
    }
    return transforms, report


def minimal_video2mesh_manifest(project_root: Path, scene: str, source_project: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "scene_id": f"{scene}_holi_spatial_full",
        "project_root": str(project_root),
        "inputs": {"source_project": str(source_project)},
        "scene": {
            "frames_dir": "scene/frames",
            "camera_info": "scene/cameras/camera_info.json",
            "point_cloud": "scene/reconstruction/point_cloud.ply",
            "scene_3dgs": "scene/reconstruction/3dgs",
        },
        "masks": {
            "mask_2d_dir": "masks/2d",
            "mask_3d_dir": "masks/3d",
        },
        "objects_dir": "objects",
        "simulator_assets_dir": "simulator_assets",
        "external_stages": {
            "data_package": {
                "status": "prepared_for_real_holi_spatial_rerun",
                "source_project": str(source_project),
            }
        },
        "artifacts": {
            "frames": str(project_root / "scene" / "frames"),
            "camera_info": str(project_root / "scene" / "cameras" / "camera_info.json"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--scene", default="bedroom_4")
    args = parser.parse_args()

    source_project = args.source_project.resolve()
    run_root = args.run_root.resolve()
    scene = args.scene
    frames_dir = source_project / "scene" / "frames"
    camera_info_path = source_project / "scene" / "cameras" / "camera_info.json"
    if not frames_dir.is_dir():
        raise FileNotFoundError(frames_dir)
    if not camera_info_path.is_file():
        raise FileNotFoundError(camera_info_path)
    if run_root.exists() and any(run_root.iterdir()):
        raise FileExistsError(f"Run root is not empty: {run_root}")

    run_root.mkdir(parents=True, exist_ok=True)
    scene_root = run_root / "scannetppv2" / "data" / scene
    images_link = scene_root / "dslr" / "resized_undistorted_images"
    relative_symlink(frames_dir, images_link)

    camera_info = read_json(camera_info_path)
    transforms, camera_report = corrected_transforms(camera_info, frames_dir)
    transforms_path = scene_root / "dslr" / "nerfstudio" / "transforms_undistorted.json"
    write_json(transforms_path, transforms)
    write_json(run_root / "logs" / "camera_coordinate_validation.json", camera_report)

    v2m_root = run_root / "video2mesh"
    relative_symlink(frames_dir, v2m_root / "scene" / "frames")
    v2m_camera_path = v2m_root / "scene" / "cameras" / "camera_info.json"
    write_json(v2m_camera_path, camera_info)
    for relative in ["scene/reconstruction", "masks/2d", "masks/3d", "objects", "simulator_assets", "logs"]:
        (v2m_root / relative).mkdir(parents=True, exist_ok=True)
    write_json(v2m_root / "manifest.json", minimal_video2mesh_manifest(v2m_root, scene, source_project))

    # PGSR's ScanNet++ depth loader expects this sibling layout. Its current
    # absolute-path parser also treats the first component after /data as the
    # scene name, so keep the explicit compatibility link until upstream fixes
    # Path.parts.index("data").
    relative_symlink(scene_root / "depth_da3", run_root / "DptV3" / "data" / scene / "depth_da3")
    relative_symlink(scene_root / "depth_da3", run_root / "DptV3" / "data" / "zyx" / "depth_da3")

    provenance = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "run_root": str(run_root),
        "scene": scene,
        "source_project": str(source_project),
        "source_frames": str(frames_dir),
        "source_camera_info": str(camera_info_path),
        "source_camera_info_sha256": sha256(camera_info_path),
        "transforms": str(transforms_path),
        "transforms_sha256": sha256(transforms_path),
        "camera_validation": camera_report,
        "stage_status": {
            "data_package": "Passed",
            "DA3": "Pending",
            "GroundingDINO": "Pending",
            "SAM3": "Pending",
            "Video2Mesh_lifting": "Pending",
            "instance_bbox_postprocess": "Pending",
            "PGSR": "Pending",
        },
    }
    write_json(run_root / "run_manifest.json", provenance)
    print(json.dumps(provenance, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
