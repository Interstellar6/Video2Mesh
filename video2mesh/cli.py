#!/usr/bin/env python3
"""Prototype CLI for video scan to object-centric mesh assets.

This module intentionally keeps the heavy research components replaceable:
video-to-3DGS, 2D segmentation/tracking, and mesh generation are external
stages. The built-in stages define the data contract, fuse existing 2D masks
onto a point cloud, select object frames, and export image-blaster assets.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MASK_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MODEL_EXTENSIONS = {".blend", ".fbx", ".glb", ".obj", ".ply", ".stl", ".usdz"}
MODEL_EXTENSION_PRIORITY = {".glb": 0, ".obj": 1, ".ply": 2, ".fbx": 3, ".stl": 4, ".usdz": 5, ".blend": 6}
DEFAULT_SCHEMA_VERSION = 1
MAST3R_KEYFRAMES_DIR = "scene/mast3r_keyframes"
SH_C0 = 0.28209479177387814
SCANNET20_LABEL_IDS = {
    "wall": 1,
    "floor": 2,
    "cabinet": 3,
    "bed": 4,
    "chair": 5,
    "sofa": 6,
    "table": 7,
    "bookshelf": 10,
    "picture": 11,
    "counter": 12,
    "desk": 14,
    "curtain": 16,
    "ceiling": 22,
    "refrigerator": 24,
    "shower curtain": 28,
    "toilet": 33,
    "sink": 34,
    "bathtub": 36,
}
SEMANTIC_PREVIEW_PALETTE = [
    (230, 25, 75),
    (60, 180, 75),
    (0, 130, 200),
    (245, 130, 48),
    (145, 30, 180),
    (70, 240, 240),
    (240, 50, 230),
    (210, 245, 60),
    (250, 190, 190),
    (0, 128, 128),
    (230, 190, 255),
    (170, 110, 40),
    (255, 250, 200),
    (128, 0, 0),
    (170, 255, 195),
    (128, 128, 0),
    (255, 215, 180),
    (0, 0, 128),
]
COLMAP_CAMERA_MODELS = {
    "SIMPLE_PINHOLE",
    "PINHOLE",
    "SIMPLE_RADIAL",
    "RADIAL",
    "OPENCV",
    "OPENCV_FISHEYE",
    "SIMPLE_RADIAL_FISHEYE",
    "RADIAL_FISHEYE",
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, value: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def slugify(value: str, fallback: str = "object") -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip().lower())
    slug = slug.strip("-._")
    return (slug or fallback)[:80]


def frame_stem(frame_id: str | int) -> str:
    text = str(frame_id)
    return f"{int(text):06d}" if text.isdigit() else text


def project_manifest_path(project_root: Path) -> Path:
    return project_root / "manifest.json"


def load_manifest(project_root: Path) -> dict[str, Any]:
    path = project_manifest_path(project_root)
    if not path.exists():
        raise FileNotFoundError(f"Project manifest not found: {path}")
    return read_json(path)


def save_manifest(project_root: Path, manifest: dict[str, Any]) -> None:
    write_json(project_manifest_path(project_root), manifest)


def rel_or_abs(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def resolve_project_cli_path(path: Path, project_root: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    cwd_candidate = path.resolve()
    if path.exists() or path.parent.exists():
        return cwd_candidate
    project_text = str(project_root)
    path_text = str(path)
    if path_text == project_text or path_text.startswith(project_text.rstrip("/") + "/"):
        return cwd_candidate
    return (project_root / path).resolve()


def resolve_project_relative_path(path: Path, project_root: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def copy_or_link(src: Path, dst: Path, mode: str = "copy") -> Path:
    ensure_dir(dst.parent)
    if src.resolve() == dst.resolve():
        return dst
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "symlink":
        dst.symlink_to(src.resolve())
    elif mode == "copy":
        shutil.copy2(src, dst)
    else:
        raise ValueError("--mode must be copy or symlink")
    return dst


def import_numpy():
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("This command requires numpy.") from exc
    return np


def import_cv2():
    try:
        import cv2  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("This command requires opencv-python (cv2).") from exc
    return cv2


def init_project(project_root: Path, scene_id: str, video: Path | None = None) -> dict[str, Any]:
    project_root = project_root.resolve()
    scene_id = slugify(scene_id, fallback="scene")
    for subdir in [
        "scene/frames",
        "scene/cameras",
        "scene/reconstruction",
        "masks/2d",
        "masks/3d",
        "objects",
        "simulator_assets",
        "logs",
    ]:
        ensure_dir(project_root / subdir)

    manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "scene_id": scene_id,
        "project_root": str(project_root),
        "inputs": {},
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
            "video_to_3dgs": {
                "status": "not_configured",
                "notes": "Plug in COLMAP/Gaussian Splatting/MASt3R-SLAM here.",
            },
            "segmentation_2d_tracking": {
                "status": "not_configured",
                "notes": "Plug in SAM/DEVA/XMem/Grounded-SAM style masks here.",
            },
            "mesh_generation": {
                "status": "prepared_for_image_blaster",
                "notes": "Use export-image-blaster and mesh-commands.",
            },
        },
        "artifacts": {},
    }
    if video is not None:
        manifest["inputs"]["video"] = str(video.resolve())
    save_manifest(project_root, manifest)
    return manifest


def cmd_init(args: argparse.Namespace) -> int:
    manifest = init_project(args.project_root, args.scene_id, args.video)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def create_synthetic_image(path: Path, rectangles: list[tuple[int, int, int, int, tuple[int, int, int]]]) -> None:
    np = import_numpy()
    cv2 = import_cv2()
    img = np.full((480, 640, 3), 245, dtype=np.uint8)
    cv2.line(img, (0, 360), (639, 360), (210, 210, 210), 2)
    for x0, y0, x1, y1, color in rectangles:
        cv2.rectangle(img, (x0, y0), (x1, y1), color, thickness=-1)
        cv2.rectangle(img, (x0, y0), (x1, y1), (30, 30, 30), thickness=2)
    ensure_dir(path.parent)
    cv2.imwrite(str(path), img)


def create_synthetic_mask(path: Path, rect: tuple[int, int, int, int]) -> None:
    np = import_numpy()
    cv2 = import_cv2()
    mask = np.zeros((480, 640), dtype=np.uint8)
    x0, y0, x1, y1 = rect
    cv2.rectangle(mask, (x0, y0), (x1, y1), 255, thickness=-1)
    ensure_dir(path.parent)
    cv2.imwrite(str(path), mask)


def write_ascii_ply(path: Path, points: list[tuple[float, float, float, int, int, int]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        for x, y, z, r, g, b in points:
            f.write(f"{x:.6f} {y:.6f} {z:.6f} {r:d} {g:d} {b:d}\n")


def write_point_cloud_ascii_ply(path: Path, points, colors=None) -> None:
    np = import_numpy()
    points_np = np.asarray(points, dtype=np.float64)
    if points_np.ndim != 2 or points_np.shape[1] != 3:
        raise ValueError("points must be an Nx3 array")
    if colors is None:
        colors_np = np.full((points_np.shape[0], 3), 0.6, dtype=np.float64)
    else:
        colors_np = np.asarray(colors, dtype=np.float64)
        if colors_np.shape != points_np.shape:
            raise ValueError("colors must be an Nx3 array matching points")
        if colors_np.size and float(colors_np.max()) > 1.0:
            colors_np = colors_np / 255.0
    rgb = np.clip(np.rint(colors_np * 255.0), 0, 255).astype(np.uint8)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {points_np.shape[0]}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("end_header\n")
        for point, color in zip(points_np, rgb):
            f.write(
                f"{float(point[0]):.8f} {float(point[1]):.8f} {float(point[2]):.8f} "
                f"{int(color[0])} {int(color[1])} {int(color[2])}\n"
            )


def write_point_indices(project_root: Path, manifest: dict[str, Any], object_id: str, indices, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    np = import_numpy()
    mask_3d_dir = ensure_dir(project_root / manifest["masks"]["mask_3d_dir"] / object_id)
    indices_np = np.asarray(indices, dtype=np.int64)
    npy_path = mask_3d_dir / "point_indices.npy"
    json_path = mask_3d_dir / "point_indices.json"
    np.save(npy_path, indices_np)
    write_json(json_path, [int(value) for value in indices_np.tolist()])
    mask_info = {
        "point_indices_npy": str(npy_path),
        "point_indices_json": str(json_path),
        "point_count": int(indices_np.size),
    }
    if metadata:
        mask_info.update(metadata)
    return mask_info


def rgb_to_sh_dc(colors):
    np = import_numpy()
    colors_np = np.clip(np.asarray(colors, dtype=np.float32), 0.0, 1.0)
    return (colors_np - 0.5) / SH_C0


def sh_dc_to_rgb(dc):
    np = import_numpy()
    dc_np = np.asarray(dc, dtype=np.float32)
    return np.clip(dc_np * SH_C0 + 0.5, 0.0, 1.0)


def logit(values, eps: float = 1e-6):
    np = import_numpy()
    clipped = np.clip(np.asarray(values, dtype=np.float32), eps, 1.0 - eps)
    return np.log(clipped / (1.0 - clipped))


def write_supersplat_ply(
    path: Path,
    means,
    colors,
    opacities,
    scales,
    quats,
    labels=None,
) -> None:
    np = import_numpy()
    means_np = np.asarray(means, dtype=np.float32)
    colors_np = np.clip(np.asarray(colors, dtype=np.float32), 0.0, 1.0)
    opacities_np = logit(opacities).reshape(-1)
    scales_np = np.log(np.clip(np.asarray(scales, dtype=np.float32), 1e-8, None))
    quats_np = np.asarray(quats, dtype=np.float32)
    dc_np = rgb_to_sh_dc(colors_np)
    labels_np = None if labels is None else np.asarray(labels, dtype=np.int32).reshape(-1)
    if not (means_np.shape[0] == colors_np.shape[0] == opacities_np.shape[0] == scales_np.shape[0] == quats_np.shape[0]):
        raise ValueError("Supersplat arrays must have the same vertex count")
    if labels_np is not None and labels_np.shape[0] != means_np.shape[0]:
        raise ValueError("labels must match the vertex count")
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {means_np.shape[0]}\n")
        for name in [
            "x",
            "y",
            "z",
            "f_dc_0",
            "f_dc_1",
            "f_dc_2",
            "opacity",
            "scale_0",
            "scale_1",
            "scale_2",
            "rot_0",
            "rot_1",
            "rot_2",
            "rot_3",
        ]:
            f.write(f"property float {name}\n")
        if labels_np is not None:
            f.write("property int object_id\n")
        f.write("end_header\n")
        for idx, (point, dc, opacity, scale, quat) in enumerate(zip(means_np, dc_np, opacities_np, scales_np, quats_np)):
            values = [
                f"{float(point[0]):.8f}",
                f"{float(point[1]):.8f}",
                f"{float(point[2]):.8f}",
                f"{float(dc[0]):.8f}",
                f"{float(dc[1]):.8f}",
                f"{float(dc[2]):.8f}",
                f"{float(opacity):.8f}",
                f"{float(scale[0]):.8f}",
                f"{float(scale[1]):.8f}",
                f"{float(scale[2]):.8f}",
                f"{float(quat[0]):.8f}",
                f"{float(quat[1]):.8f}",
                f"{float(quat[2]):.8f}",
                f"{float(quat[3]):.8f}",
            ]
            if labels_np is not None:
                values.append(str(int(labels_np[idx])))
            f.write(" ".join(values) + "\n")


def qvec_to_rotmat(qvec: list[float]):
    np = import_numpy()
    qw, qx, qy, qz = qvec
    return np.array(
        [
            [1 - 2 * qy * qy - 2 * qz * qz, 2 * qx * qy - 2 * qz * qw, 2 * qx * qz + 2 * qy * qw],
            [2 * qx * qy + 2 * qz * qw, 1 - 2 * qx * qx - 2 * qz * qz, 2 * qy * qz - 2 * qx * qw],
            [2 * qx * qz - 2 * qy * qw, 2 * qy * qz + 2 * qx * qw, 1 - 2 * qx * qx - 2 * qy * qy],
        ],
        dtype=np.float64,
    )


def xyzw_quat_to_rotmat(qvec: list[float]):
    qx, qy, qz, qw = qvec
    return qvec_to_rotmat([qw, qx, qy, qz])


def matrix_inverse(matrix):
    np = import_numpy()
    return np.linalg.inv(np.asarray(matrix, dtype=np.float64))


def rotmat_to_qvec(rotmat) -> list[float]:
    np = import_numpy()
    matrix = np.asarray(rotmat, dtype=np.float64)
    trace = float(np.trace(matrix))
    if trace > 0.0:
        scale = 0.5 / np.sqrt(trace + 1.0)
        qw = 0.25 / scale
        qx = (matrix[2, 1] - matrix[1, 2]) * scale
        qy = (matrix[0, 2] - matrix[2, 0]) * scale
        qz = (matrix[1, 0] - matrix[0, 1]) * scale
    else:
        diag = np.diag(matrix)
        axis = int(np.argmax(diag))
        if axis == 0:
            scale = 2.0 * np.sqrt(max(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2], 1e-12))
            qw = (matrix[2, 1] - matrix[1, 2]) / scale
            qx = 0.25 * scale
            qy = (matrix[0, 1] + matrix[1, 0]) / scale
            qz = (matrix[0, 2] + matrix[2, 0]) / scale
        elif axis == 1:
            scale = 2.0 * np.sqrt(max(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2], 1e-12))
            qw = (matrix[0, 2] - matrix[2, 0]) / scale
            qx = (matrix[0, 1] + matrix[1, 0]) / scale
            qy = 0.25 * scale
            qz = (matrix[1, 2] + matrix[2, 1]) / scale
        else:
            scale = 2.0 * np.sqrt(max(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1], 1e-12))
            qw = (matrix[1, 0] - matrix[0, 1]) / scale
            qx = (matrix[0, 2] + matrix[2, 0]) / scale
            qy = (matrix[1, 2] + matrix[2, 1]) / scale
            qz = 0.25 * scale
    qvec = np.asarray([qw, qx, qy, qz], dtype=np.float64)
    norm = np.linalg.norm(qvec)
    if norm <= 0:
        raise ValueError("Invalid rotation matrix; quaternion norm is zero.")
    qvec = qvec / norm
    if qvec[0] < 0:
        qvec = -qvec
    return [float(value) for value in qvec.tolist()]


def fmt_colmap_float(value: float) -> str:
    return f"{float(value):.12g}"


def read_colmap_text_cameras(path: Path) -> dict[str, dict[str, Any]]:
    cameras: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            camera_id, model, width, height = parts[:4]
            params = [float(value) for value in parts[4:]]
            if model not in COLMAP_CAMERA_MODELS:
                raise ValueError(f"Unsupported COLMAP camera model {model!r} in {path}")
            cameras[camera_id] = colmap_intrinsic(camera_id, model, int(width), int(height), params)
    if not cameras:
        raise ValueError(f"No cameras parsed from {path}")
    return cameras


def colmap_intrinsic(camera_id: str, model: str, width: int, height: int, params: list[float]) -> dict[str, Any]:
    if model == "SIMPLE_PINHOLE":
        f, cx, cy = params[:3]
        fx = fy = f
    elif model == "PINHOLE":
        fx, fy, cx, cy = params[:4]
    elif model in {"SIMPLE_RADIAL", "SIMPLE_RADIAL_FISHEYE"}:
        f, cx, cy = params[:3]
        fx = fy = f
    elif model in {"RADIAL", "RADIAL_FISHEYE"}:
        f, cx, cy = params[:3]
        fx = fy = f
    elif model in {"OPENCV", "OPENCV_FISHEYE"}:
        fx, fy, cx, cy = params[:4]
    else:
        raise ValueError(f"Unsupported COLMAP camera model {model!r}")
    return {
        "camera_id": camera_id,
        "model": model,
        "w": width,
        "h": height,
        "fx": float(fx),
        "fy": float(fy),
        "cx": float(cx),
        "cy": float(cy),
        "params": params,
    }


def image_name_to_frame_id(name: str, regex: str | None = None) -> str:
    stem = Path(name).stem
    if regex:
        match = re.search(regex, stem)
        if match:
            value = match.group(1) if match.groups() else match.group(0)
            return frame_stem(value)
    return frame_stem(stem)


def read_colmap_text_images(path: Path, frame_id_regex: str | None = None) -> dict[str, dict[str, Any]]:
    images: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        pending_image: dict[str, Any] | None = None
        for raw_line in f:
            line = raw_line.strip()
            if line.startswith("#"):
                continue
            parts = line.split()
            is_image_line = len(parts) >= 10 and parts[0].lstrip("-").isdigit()
            if is_image_line:
                if pending_image is not None:
                    frame_id = image_name_to_frame_id(pending_image["name"], frame_id_regex)
                    images[frame_id] = pending_image
                image_id = parts[0]
                qvec = [float(value) for value in parts[1:5]]
                tvec = [float(value) for value in parts[5:8]]
                camera_id = parts[8]
                image_name = " ".join(parts[9:])
                pending_image = {
                    "image_id": image_id,
                    "camera_id": camera_id,
                    "name": image_name,
                    "qvec": qvec,
                    "tvec": tvec,
                }
            elif pending_image is not None:
                frame_id = image_name_to_frame_id(pending_image["name"], frame_id_regex)
                images[frame_id] = pending_image
                pending_image = None
        if pending_image is not None:
            frame_id = image_name_to_frame_id(pending_image["name"], frame_id_regex)
            images[frame_id] = pending_image
    if not images:
        raise ValueError(f"No images parsed from {path}")
    return images


def read_colmap_text_points3d(path: Path) -> list[tuple[float, float, float, int, int, int]]:
    points = []
    if not path.exists():
        return points
    with path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            x, y, z = (float(parts[1]), float(parts[2]), float(parts[3]))
            r, g, b = (int(float(parts[4])), int(float(parts[5])), int(float(parts[6])))
            points.append((x, y, z, r, g, b))
    return points


def colmap_image_to_world_to_camera(image: dict[str, Any]) -> list[list[float]]:
    np = import_numpy()
    rot = qvec_to_rotmat(image["qvec"])
    t = np.asarray(image["tvec"], dtype=np.float64).reshape(3, 1)
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = rot
    matrix[:3, 3:4] = t
    return matrix.tolist()


def mast3r_pose_to_camera_to_world(values: list[float]) -> list[list[float]]:
    np = import_numpy()
    x, y, z, qx, qy, qz, qw = values
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = xyzw_quat_to_rotmat([qx, qy, qz, qw])
    matrix[:3, 3] = [x, y, z]
    return matrix.tolist()


def read_mast3r_slam_traj(path: Path) -> list[dict[str, Any]]:
    poses = []
    with path.open("r", encoding="utf-8") as f:
        for line_idx, raw_line in enumerate(f):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 8:
                raise ValueError(f"Invalid MASt3R-SLAM trajectory line {line_idx + 1}: {line}")
            timestamp = parts[0]
            values = [float(value) for value in parts[1:8]]
            poses.append(
                {
                    "frame_id": f"{len(poses):06d}",
                    "timestamp": timestamp,
                    "camera_to_world": mast3r_pose_to_camera_to_world(values),
                    "raw": values,
                }
            )
    if not poses:
        raise ValueError(f"No poses parsed from {path}")
    return poses


def copy_image_dir(src_dir: Path, dst_dir: Path, mode: str, clear: bool = False) -> int:
    if clear and dst_dir.exists():
        shutil.rmtree(dst_dir)
    ensure_dir(dst_dir)
    copied = 0
    for idx, src in enumerate(sorted(p for p in src_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)):
        dst = dst_dir / f"{idx:06d}{src.suffix.lower()}"
        copy_or_link(src, dst, mode)
        copied += 1
    return copied


def estimate_or_read_intrinsic(args: argparse.Namespace, frames_dir: Path | None = None) -> dict[str, Any]:
    width = args.width
    height = args.height
    if (width is None or height is None) and frames_dir is not None and frames_dir.exists():
        frame = next((p for p in sorted(frames_dir.iterdir()) if p.suffix.lower() in IMAGE_EXTENSIONS), None)
        if frame is not None:
            cv2 = import_cv2()
            img = cv2.imread(str(frame))
            if img is not None:
                height, width = img.shape[:2]

    if width is None or height is None:
        raise ValueError("Unable to infer image size. Pass --width and --height or --frames-dir.")

    fx = args.fx if args.fx is not None else float(max(width, height)) * args.focal_scale
    fy = args.fy if args.fy is not None else fx
    cx = args.cx if args.cx is not None else float(width) / 2.0
    cy = args.cy if args.cy is not None else float(height) / 2.0
    estimated = any(value is None for value in [args.fx, args.fy, args.cx, args.cy])
    return {
        "camera_id": "mast3r_slam_import",
        "model": "PINHOLE",
        "w": int(width),
        "h": int(height),
        "fx": float(fx),
        "fy": float(fy),
        "cx": float(cx),
        "cy": float(cy),
        "estimated": estimated,
        "notes": "Estimated from image size/focal-scale; pass fx/fy/cx/cy for calibrated projection." if estimated else "",
    }


def find_latest_splat_ply(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.rglob("point_cloud.ply"), key=lambda item: (len(str(item)), str(item)))
    if not candidates:
        candidates = sorted(path.rglob("*.ply"), key=lambda item: (len(str(item)), str(item)))
    if not candidates:
        raise FileNotFoundError(f"No PLY file found under {path}")

    def iteration_key(item: Path) -> tuple[int, str]:
        match = re.search(r"iteration[_-]?(\d+)", str(item))
        return (int(match.group(1)) if match else -1, str(item))

    return sorted(candidates, key=iteration_key)[-1]


def cmd_make_sample(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = init_project(project_root, args.scene_id)

    frames_dir = project_root / manifest["scene"]["frames_dir"]
    mask_root = project_root / manifest["masks"]["mask_2d_dir"]
    camera_info_path = project_root / manifest["scene"]["camera_info"]
    point_cloud_path = project_root / manifest["scene"]["point_cloud"]

    objects = {
        "red_cube": {
            "name": "red cube",
            "category": "box",
            "description": "Synthetic red cube for pipeline smoke test.",
            "rect": (155, 160, 285, 315),
            "center_x": -0.6,
            "color": (220, 70, 55),
        },
        "blue_cube": {
            "name": "blue cube",
            "category": "box",
            "description": "Synthetic blue cube for pipeline smoke test.",
            "rect": (355, 155, 495, 315),
            "center_x": 0.6,
            "color": (60, 115, 220),
        },
    }

    for frame_id in [0, 1, 2]:
        jitter = frame_id * 4
        rects = []
        for obj in objects.values():
            x0, y0, x1, y1 = obj["rect"]
            rects.append((x0 + jitter, y0, x1 + jitter, y1, obj["color"]))
        create_synthetic_image(frames_dir / f"{frame_id:06d}.png", rects)
        for object_id, obj in objects.items():
            x0, y0, x1, y1 = obj["rect"]
            create_synthetic_mask(mask_root / object_id / f"{frame_id:06d}.png", (x0 + jitter, y0, x1 + jitter, y1))

    camera_info = {
        "intrinsic": {"w": 640, "h": 480, "fx": 500, "fy": 500, "cx": 320, "cy": 240},
        "extrinsic": {
            "0": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "1": [[1, 0, 0, 0.024], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            "2": [[1, 0, 0, 0.048], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        },
    }
    write_json(camera_info_path, camera_info)

    points: list[tuple[float, float, float, int, int, int]] = []
    for object_id, obj in objects.items():
        rgb = obj["color"]
        for ix in range(18):
            for iy in range(18):
                x = float(obj["center_x"]) + (ix - 8.5) * 0.025
                y = (iy - 8.5) * 0.025
                z = 3.0
                points.append((x, y, z, int(rgb[2]), int(rgb[1]), int(rgb[0])))
    write_ascii_ply(point_cloud_path, points)

    labels = {
        object_id: {
            "name": obj["name"],
            "category": obj["category"],
            "description": obj["description"],
        }
        for object_id, obj in objects.items()
    }
    write_json(project_root / "masks" / "object_labels.json", labels)
    write_json(
        project_root / "masks" / "prompts.json",
        {
            "objects": [
                {
                    "id": object_id,
                    "name": obj["name"],
                    "category": obj["category"],
                    "description": obj["description"],
                    "frame_id": "000000",
                    "bbox": list(obj["rect"]),
                    "bbox_format": "xyxy",
                }
                for object_id, obj in objects.items()
            ]
        },
    )

    manifest["artifacts"].update(
        {
            "sample": True,
            "frames": str(frames_dir),
            "mask_2d_dir": str(mask_root),
            "tracking_prompts": str(project_root / "masks" / "prompts.json"),
            "camera_info": str(camera_info_path),
            "point_cloud": str(point_cloud_path),
        }
    )
    save_manifest(project_root, manifest)
    print(f"Created sample project at {project_root}")
    print("Next: fuse-masks, select-frames, export-image-blaster")
    return 0


def cmd_make_scan_video_sample(args: argparse.Namespace) -> int:
    np = import_numpy()
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = init_project(project_root, args.scene_id)
    video_dir = ensure_dir(project_root / "inputs")
    video_path = args.output_video or (video_dir / "synthetic_scan.mp4")
    if not video_path.is_absolute():
        video_path = project_root / video_path
    frames_dir = ensure_dir(project_root / "source_frames")

    objects = {
        "red_cube": {
            "name": "red cube",
            "category": "box",
            "description": "Synthetic red cube in a scan video smoke test.",
            "rect": (155, 160, 285, 315),
            "center_x": -0.6,
            "color": (220, 70, 55),
        },
        "blue_cube": {
            "name": "blue cube",
            "category": "box",
            "description": "Synthetic blue cube in a scan video smoke test.",
            "rect": (355, 155, 495, 315),
            "center_x": 0.6,
            "color": (60, 115, 220),
        },
    }

    source_frame_paths = []
    for frame_id in range(int(args.frame_count)):
        jitter = int(round(frame_id * args.pixel_step))
        rects = []
        for obj in objects.values():
            x0, y0, x1, y1 = obj["rect"]
            rects.append((x0 + jitter, y0, x1 + jitter, y1, obj["color"]))
        frame_path = frames_dir / f"{frame_id:06d}.png"
        create_synthetic_image(frame_path, rects)
        source_frame_paths.append(frame_path)

    first_image = cv2.imread(str(source_frame_paths[0]))
    if first_image is None:
        raise RuntimeError(f"Failed to read generated frame: {source_frame_paths[0]}")
    height, width = first_image.shape[:2]
    ensure_dir(video_path.parent)
    fourcc = cv2.VideoWriter_fourcc(*args.fourcc)
    writer = cv2.VideoWriter(str(video_path), fourcc, float(args.fps), (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {video_path}")
    try:
        for frame_path in source_frame_paths:
            frame = cv2.imread(str(frame_path))
            if frame is None:
                raise RuntimeError(f"Failed to read generated frame: {frame_path}")
            writer.write(frame)
    finally:
        writer.release()
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise RuntimeError(f"VideoWriter did not create a readable file: {video_path}")

    camera_info_path = project_root / manifest["scene"]["camera_info"]
    extract_every = max(1, int(args.extract_every))
    extracted_count = len([idx for idx in range(int(args.frame_count)) if idx % extract_every == 0])
    extrinsics = {}
    for out_idx in range(extracted_count):
        source_idx = out_idx * extract_every
        extrinsics[str(out_idx)] = [[1, 0, 0, 0.024 * source_idx], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    write_json(
        camera_info_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "source": "synthetic_scan_video_sample",
            "intrinsic": {"w": width, "h": height, "fx": 500, "fy": 500, "cx": width / 2.0, "cy": height / 2.0},
            "extrinsic_type": "world_to_camera",
            "extrinsic": extrinsics,
            "notes": "Camera entries correspond to frames extracted with the generated sample's extract_every value.",
        },
    )

    point_cloud_path = project_root / manifest["scene"]["point_cloud"]
    points: list[tuple[float, float, float, int, int, int]] = []
    for obj in objects.values():
        rgb = obj["color"]
        for ix in range(18):
            for iy in range(18):
                x = float(obj["center_x"]) + (ix - 8.5) * 0.025
                y = (iy - 8.5) * 0.025
                z = 3.0
                points.append((x, y, z, int(rgb[2]), int(rgb[1]), int(rgb[0])))
    write_ascii_ply(point_cloud_path, points)

    labels = {
        object_id: {
            "name": obj["name"],
            "category": obj["category"],
            "description": obj["description"],
        }
        for object_id, obj in objects.items()
    }
    write_json(project_root / "masks" / "object_labels.json", labels)

    manifest["inputs"]["video"] = str(video_path)
    manifest["artifacts"].update(
        {
            "synthetic_scan_video": str(video_path),
            "synthetic_source_frames": str(frames_dir),
            "synthetic_extract_every": extract_every,
            "camera_info": str(camera_info_path),
            "point_cloud": str(point_cloud_path),
            "object_labels": str(project_root / "masks" / "object_labels.json"),
        }
    )
    save_manifest(project_root, manifest)
    print(f"Created synthetic scan video sample at {project_root}")
    print(f"Video: {video_path}")
    print(f"Recommended extract every: {extract_every}")
    return 0


def cmd_make_colmap_sample(args: argparse.Namespace) -> int:
    output_dir = ensure_dir(args.output_dir.resolve())
    images_dir = ensure_dir(output_dir / "images")
    create_synthetic_image(images_dir / "000000.png", [(155, 160, 285, 315, (220, 70, 55))])
    create_synthetic_image(images_dir / "000001.png", [(359, 155, 499, 315, (60, 115, 220))])
    (output_dir / "cameras.txt").write_text(
        "\n".join(
            [
                "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]",
                "1 PINHOLE 640 480 500 500 320 240",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "images.txt").write_text(
        "\n".join(
            [
                "# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME",
                "# POINTS2D[] as (X, Y, POINT3D_ID)",
                "1 1 0 0 0 0 0 0 1 000000.png",
                "",
                "2 1 0 0 0 0.024 0 0 1 000001.png",
                "",
                "",
            ]
        ),
        encoding="utf-8",
    )
    points = []
    for ix in range(8):
        for iy in range(8):
            points.append((1 + len(points), -0.6 + ix * 0.05, -0.2 + iy * 0.05, 3.0, 55, 70, 220, 0.1))
            points.append((1 + len(points), 0.6 + ix * 0.05, -0.2 + iy * 0.05, 3.0, 220, 115, 60, 0.1))
    lines = ["# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]"]
    for point_id, x, y, z, r, g, b, error in points:
        lines.append(f"{point_id} {x:.6f} {y:.6f} {z:.6f} {r} {g} {b} {error:.3f}")
    (output_dir / "points3D.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote COLMAP text sample to {output_dir}")
    return 0


def cmd_extract_frames(args: argparse.Namespace) -> int:
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    video_value = args.video or manifest.get("inputs", {}).get("video")
    if not video_value:
        raise FileNotFoundError("Video not found. Pass --video or set inputs.video in manifest.json.")
    video = Path(video_value)
    if not video.is_absolute():
        video = project_root / video
    if not video or not video.exists():
        raise FileNotFoundError("Video not found. Pass --video or set inputs.video in manifest.json.")

    frames_dir = ensure_dir(args.output_dir.resolve() if args.output_dir else project_root / manifest["scene"]["frames_dir"])
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video}")

    written = 0
    frame_index = 0
    selected_frames = []
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    source_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_index % args.every == 0:
                out_path = frames_dir / f"{written:06d}.png" if args.renumber else frames_dir / f"{frame_index:06d}.png"
                if args.overwrite or not out_path.exists():
                    cv2.imwrite(str(out_path), frame)
                    written += 1
                    selected_frames.append(
                        {
                            "frame_id": out_path.stem,
                            "source_frame_index": frame_index,
                            "source_time_sec": float(frame_index / fps) if fps > 0 else None,
                            "path": str(out_path),
                        }
                    )
                if args.max_frames and written >= args.max_frames:
                    break
            frame_index += 1
    finally:
        cap.release()

    manifest["artifacts"]["frames"] = str(frames_dir)
    extraction_manifest_path = project_root / "scene" / "frames_manifest.json"
    write_json(
        extraction_manifest_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "source_video": str(video.resolve()),
            "frames_dir": str(frames_dir),
            "every": int(args.every),
            "max_frames": int(args.max_frames),
            "renumber": bool(args.renumber),
            "source_fps": fps,
            "source_frame_count": source_frame_count,
            "source_width": width,
            "source_height": height,
            "decoded_frame_count": int(frame_index),
            "written_frame_count": int(written),
            "frames": selected_frames,
        },
    )
    manifest["artifacts"]["frames_manifest"] = str(extraction_manifest_path)
    manifest["inputs"]["video"] = str(video.resolve())
    save_manifest(project_root, manifest)
    print(f"Extracted {written} frame(s) to {frames_dir}")
    print(f"Frame manifest: {extraction_manifest_path}")
    return 0


def cmd_register_reconstruction(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    mode = args.mode

    if args.point_cloud:
        dst = project_root / manifest["scene"]["point_cloud"]
        copy_or_link(args.point_cloud, dst, mode)
        manifest["artifacts"]["point_cloud"] = str(dst)

    if args.camera_info:
        dst = project_root / manifest["scene"]["camera_info"]
        copy_or_link(args.camera_info, dst, mode)
        manifest["artifacts"]["camera_info"] = str(dst)

    if args.scene_3dgs:
        dst = project_root / manifest["scene"]["scene_3dgs"]
        if args.scene_3dgs.is_dir():
            if dst.exists() and mode == "copy":
                shutil.rmtree(dst)
            if mode == "copy":
                shutil.copytree(args.scene_3dgs, dst)
            else:
                copy_or_link(args.scene_3dgs, dst, mode)
        else:
            copy_or_link(args.scene_3dgs, dst, mode)
        manifest["artifacts"]["scene_3dgs"] = str(dst)

    save_manifest(project_root, manifest)
    print(f"Registered reconstruction artifacts in {project_root}")
    return 0


def cmd_import_colmap(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    sparse_dir = args.sparse_dir.resolve()
    cameras_path = sparse_dir / "cameras.txt"
    images_path = sparse_dir / "images.txt"
    points3d_path = sparse_dir / "points3D.txt"
    if not cameras_path.exists() or not images_path.exists():
        raise FileNotFoundError(
            f"Expected COLMAP text model files cameras.txt and images.txt under {sparse_dir}. "
            "If you have .bin files, run COLMAP model_converter to text first."
        )

    cameras = read_colmap_text_cameras(cameras_path)
    images = read_colmap_text_images(images_path, args.frame_id_regex)
    extrinsics = {
        frame_id: colmap_image_to_world_to_camera(image)
        for frame_id, image in sorted(images.items(), key=lambda item: item[0])
    }
    frame_camera_ids = {frame_id: image["camera_id"] for frame_id, image in images.items()}

    first_camera_id = next(iter(cameras))
    camera_info = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "source": "colmap_text",
        "extrinsic_type": "world_to_camera",
        "intrinsic": cameras[first_camera_id],
        "intrinsics": cameras,
        "frame_camera_ids": frame_camera_ids,
        "extrinsic": extrinsics,
        "images": images,
    }
    camera_info_path = project_root / manifest["scene"]["camera_info"]
    write_json(camera_info_path, camera_info)
    manifest["artifacts"]["camera_info"] = str(camera_info_path)
    manifest["artifacts"]["colmap_sparse_text"] = str(sparse_dir)

    if points3d_path.exists():
        points = read_colmap_text_points3d(points3d_path)
        if points:
            point_cloud_path = project_root / manifest["scene"]["point_cloud"]
            write_ascii_ply(point_cloud_path, points)
            manifest["artifacts"]["point_cloud"] = str(point_cloud_path)

    if args.images_dir:
        frames_dir = ensure_dir(project_root / manifest["scene"]["frames_dir"])
        copied = 0
        for image in images.values():
            src = args.images_dir / image["name"]
            if src.exists():
                dst = frames_dir / f"{image_name_to_frame_id(image['name'], args.frame_id_regex)}{src.suffix.lower()}"
                copy_or_link(src, dst, args.mode)
                copied += 1
        manifest["artifacts"]["frames"] = str(frames_dir)
        manifest["artifacts"]["frames_imported"] = copied

    save_manifest(project_root, manifest)
    print(f"Imported COLMAP text model from {sparse_dir}")
    print(f"Frames/cameras: {len(images)} images, {len(cameras)} camera(s)")
    if points3d_path.exists():
        print(f"Point cloud: {manifest['artifacts'].get('point_cloud', 'no points3D parsed')}")
    return 0


def colmap_camera_params(intrinsic: dict[str, Any], model: str) -> list[float]:
    fx = float(intrinsic["fx"])
    fy = float(intrinsic.get("fy", fx))
    cx = float(intrinsic["cx"])
    cy = float(intrinsic["cy"])
    if model == "PINHOLE":
        return [fx, fy, cx, cy]
    if model == "SIMPLE_PINHOLE":
        return [(fx + fy) / 2.0, cx, cy]
    raise ValueError("export-colmap currently supports PINHOLE or SIMPLE_PINHOLE camera models.")


def frame_id_for_path(path: Path) -> str:
    return frame_stem(path.stem)


def frame_id_sort_key(frame_id: str) -> tuple[int, Any]:
    return (0, int(frame_id)) if str(frame_id).isdigit() else (1, str(frame_id))


def camera_intrinsics_for_colmap(camera_info: dict[str, Any], frame_id: str, model: str) -> tuple[str, dict[str, Any]]:
    frame_camera_ids = camera_info.get("frame_camera_ids") or {}
    intrinsics = camera_info.get("intrinsics") or {}
    camera_id = frame_camera_ids.get(frame_id)
    if camera_id is None and frame_id.isdigit():
        camera_id = frame_camera_ids.get(str(int(frame_id)))
    if camera_id is not None and str(camera_id) in intrinsics:
        return str(camera_id), intrinsics[str(camera_id)]
    intrinsic = camera_info["intrinsic"]
    return str(intrinsic.get("camera_id", "1")), intrinsic


def colmap_world_to_camera_from_info(camera_info: dict[str, Any], frame_id: str, fallback_type: str):
    extrinsic = resolve_extrinsic(camera_info["extrinsic"], frame_id)
    if extrinsic is None:
        return None
    extrinsic_type = camera_info.get("extrinsic_type") or fallback_type
    return world_to_camera_matrix(extrinsic, extrinsic_type)


def cmd_export_colmap(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    output_dir = args.output_dir or (project_root / "exports" / "colmap_text")
    output_dir = output_dir.resolve()
    images_dir = ensure_dir(output_dir / "images")
    sparse_dir = ensure_dir(output_dir / "sparse" / "0")

    camera_info = load_camera_info(camera_info_path)
    frames = list_frame_images(frames_dir)
    frame_by_id = {frame_id_for_path(path): path for path in frames}
    frame_ids = sorted(frame_by_id, key=frame_id_sort_key)

    copied_images = []
    for frame_id in frame_ids:
        src = frame_by_id[frame_id]
        dst = images_dir / src.name
        if args.mode == "none":
            pass
        else:
            copy_or_link(src, dst, args.mode)
        copied_images.append(src.name)

    camera_records: dict[str, dict[str, Any]] = {}
    image_lines = [
        "# Image list with two lines of data per image:",
        "# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME",
        "# POINTS2D[] as (X, Y, POINT3D_ID)",
    ]
    camera_key_to_colmap_id: dict[str, str] = {}
    exported_images = 0
    skipped_frames = []
    for image_id, frame_id in enumerate(frame_ids, start=1):
        w2c = colmap_world_to_camera_from_info(camera_info, frame_id, args.extrinsic_type)
        if w2c is None:
            skipped_frames.append({"frame_id": frame_id, "reason": "missing_extrinsic"})
            continue
        camera_key, intrinsic = camera_intrinsics_for_colmap(camera_info, frame_id, args.camera_model)
        if camera_key not in camera_key_to_colmap_id:
            camera_key_to_colmap_id[camera_key] = str(len(camera_key_to_colmap_id) + 1)
        camera_id = camera_key_to_colmap_id[camera_key]
        if camera_id not in camera_records:
            width = int(intrinsic["w"])
            height = int(intrinsic["h"])
            params = colmap_camera_params(intrinsic, args.camera_model)
            camera_records[camera_id] = {
                "model": args.camera_model,
                "width": width,
                "height": height,
                "params": params,
            }
        qvec = rotmat_to_qvec(w2c[:3, :3])
        tvec = [float(value) for value in w2c[:3, 3].tolist()]
        values = [str(image_id), *(fmt_colmap_float(value) for value in qvec), *(fmt_colmap_float(value) for value in tvec), camera_id, frame_by_id[frame_id].name]
        image_lines.append(" ".join(values))
        image_lines.append("")
        exported_images += 1

    camera_lines = [
        "# Camera list with one line of data per camera:",
        "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]",
    ]
    for camera_id, record in sorted(camera_records.items(), key=lambda item: (0, int(item[0])) if item[0].isdigit() else (1, item[0])):
        params = " ".join(fmt_colmap_float(value) for value in record["params"])
        camera_lines.append(f"{camera_id} {record['model']} {record['width']} {record['height']} {params}")

    points, colors = read_point_cloud(point_cloud_path)
    points_lines = [
        "# 3D point list with one line of data per point:",
        "# POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]",
    ]
    if colors is None:
        color_values = [(128, 128, 128) for _ in range(points.shape[0])]
    else:
        np = import_numpy()
        clipped = np.clip(np.rint(colors * 255.0), 0, 255).astype(np.uint8)
        color_values = [(int(rgb[0]), int(rgb[1]), int(rgb[2])) for rgb in clipped]
    for point_id, (point, color) in enumerate(zip(points, color_values), start=1):
        r, g, b = color
        points_lines.append(
            f"{point_id} {fmt_colmap_float(point[0])} {fmt_colmap_float(point[1])} {fmt_colmap_float(point[2])} {r} {g} {b} 0"
        )

    (sparse_dir / "cameras.txt").write_text("\n".join(camera_lines) + "\n", encoding="utf-8")
    (sparse_dir / "images.txt").write_text("\n".join(image_lines) + "\n", encoding="utf-8")
    (sparse_dir / "points3D.txt").write_text("\n".join(points_lines) + "\n", encoding="utf-8")

    export_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "format": "colmap_text",
        "output_dir": str(output_dir),
        "images_dir": str(images_dir),
        "sparse_dir": str(sparse_dir),
        "camera_info": str(camera_info_path),
        "frames_dir": str(frames_dir),
        "point_cloud": str(point_cloud_path),
        "camera_model": args.camera_model,
        "image_count": exported_images,
        "camera_count": len(camera_records),
        "point_count": int(points.shape[0]),
        "skipped_frames": skipped_frames,
        "notes": "Use this as a COLMAP text source for Gaussian Splatting tools; run model_converter if binary COLMAP files are required.",
    }
    write_json(output_dir / "video2mesh_colmap_export.json", export_manifest)
    manifest["artifacts"]["colmap_text_export"] = str(output_dir / "video2mesh_colmap_export.json")
    manifest["artifacts"]["colmap_text_sparse_dir"] = str(sparse_dir)
    manifest["artifacts"]["colmap_text_images_dir"] = str(images_dir)
    save_manifest(project_root, manifest)

    print(f"Exported COLMAP text dataset: {output_dir}")
    print(f"Images: {exported_images}; cameras: {len(camera_records)}; points: {points.shape[0]}")
    if skipped_frames:
        print(f"Skipped {len(skipped_frames)} frame(s) without extrinsics.")
    return 0


def cmd_register_3dgs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    src = args.path.resolve()
    dst = project_root / manifest["scene"]["scene_3dgs"]
    same_location = src == dst.resolve()
    if same_location:
        if not src.exists():
            raise FileNotFoundError(f"3DGS artifact not found: {src}")
    elif args.mode == "copy":
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            ensure_dir(dst)
            copy_or_link(src, dst / src.name, "copy")
    else:
        if src.is_dir():
            if dst.exists() or dst.is_symlink():
                if dst.is_dir() and not dst.is_symlink():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            ensure_dir(dst.parent)
            dst.symlink_to(src)
        else:
            ensure_dir(dst)
            copy_or_link(src, dst / src.name, "symlink")

    splat_ply = find_latest_splat_ply(src)
    local_splat_ply = dst / splat_ply.relative_to(src) if src.is_dir() else dst / src.name
    manifest["artifacts"]["scene_3dgs"] = str(dst)
    manifest["artifacts"]["scene_3dgs_source"] = str(src)
    manifest["artifacts"]["scene_3dgs_ply"] = str(local_splat_ply)
    save_manifest(project_root, manifest)
    print(f"Registered 3DGS artifact: {dst}")
    print(f"Detected splat/point PLY: {local_splat_ply}")
    return 0


def command_from_template(template: str, values: dict[str, str]) -> str:
    try:
        return template.format(**values)
    except KeyError as exc:
        available = ", ".join(sorted(values))
        raise ValueError(f"Unknown run-3dgs template variable {exc}. Available: {available}") from exc


def cmd_run_3dgs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    stage_root = ensure_dir(args.work_dir.resolve() if args.work_dir else project_root / "external" / "3dgs")
    source_path = args.source_path.resolve() if args.source_path else stage_root / "colmap_source"
    output_path = args.output_path.resolve() if args.output_path else project_root / manifest["scene"]["scene_3dgs"]
    log_path = project_root / "logs" / "3dgs_run.log"
    ensure_dir(log_path.parent)

    export_args = argparse.Namespace(
        project_root=project_root,
        output_dir=source_path,
        frames_dir=args.frames_dir,
        camera_info=args.camera_info,
        point_cloud=args.point_cloud,
        camera_model=args.camera_model,
        extrinsic_type=args.extrinsic_type,
        mode=args.image_mode,
    )
    cmd_export_colmap(export_args)
    manifest = load_manifest(project_root)

    command_values = {
        "source_path": str(source_path),
        "output_path": str(output_path),
        "project_root": str(project_root),
        "work_dir": str(stage_root),
        "scene_id": str(manifest.get("scene_id", project_root.name)),
    }
    run_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "stage": "3dgs_training",
        "project_root": str(project_root),
        "source_path": str(source_path),
        "output_path": str(output_path),
        "work_dir": str(stage_root),
        "log_path": str(log_path),
        "command_template": args.command_template,
        "command": None,
        "status": "prepared",
        "notes": "COLMAP-style source prepared. Provide --command-template to launch an external 3DGS trainer.",
    }

    command = command_from_template(args.command_template, command_values) if args.command_template else None
    if command:
        run_manifest["command"] = command
        if args.prepare_only:
            run_manifest["status"] = "prepared_command"
            run_manifest["notes"] = "Command prepared but not executed because --prepare-only was set."
            write_json(stage_root / "3dgs_run_manifest.json", run_manifest)
            manifest["external_stages"]["video_to_3dgs"] = {
                "status": "3dgs_prepared",
                "notes": "COLMAP source and 3DGS command prepared; training not executed.",
                "source_path": str(source_path),
                "output_path": str(output_path),
            }
            manifest["artifacts"]["3dgs_run_manifest"] = str(stage_root / "3dgs_run_manifest.json")
            save_manifest(project_root, manifest)
            print(f"Prepared 3DGS command: {command}")
            print(f"Run manifest: {stage_root / '3dgs_run_manifest.json'}")
            return 0

        start = time.time()
        print("Running external 3DGS command:")
        print(command)
        ensure_dir(output_path)
        with log_path.open("w", encoding="utf-8") as log_file:
            completed = subprocess.run(command, cwd=stage_root, shell=True, stdout=log_file, stderr=subprocess.STDOUT, check=False)
        run_manifest["returncode"] = completed.returncode
        run_manifest["elapsed_seconds"] = round(time.time() - start, 3)
        if completed.returncode != 0:
            run_manifest["status"] = "failed"
            run_manifest["notes"] = f"External 3DGS command failed with exit code {completed.returncode}."
            write_json(stage_root / "3dgs_run_manifest.json", run_manifest)
            manifest["external_stages"]["video_to_3dgs"] = {
                "status": "3dgs_failed",
                "notes": f"External 3DGS command failed. See {log_path}",
                "source_path": str(source_path),
                "output_path": str(output_path),
            }
            manifest["artifacts"]["3dgs_run_manifest"] = str(stage_root / "3dgs_run_manifest.json")
            save_manifest(project_root, manifest)
            print(f"3DGS command failed. See log: {log_path}")
            return completed.returncode

        run_manifest["status"] = "completed"
        run_manifest["notes"] = "External 3DGS command completed and output path was registered."
    elif not args.prepare_only:
        print("No --command-template provided; prepared COLMAP source only.")

    write_json(stage_root / "3dgs_run_manifest.json", run_manifest)
    manifest["artifacts"]["3dgs_run_manifest"] = str(stage_root / "3dgs_run_manifest.json")
    save_manifest(project_root, manifest)

    if command and not args.no_register:
        register_args = argparse.Namespace(project_root=project_root, path=output_path, mode=args.register_mode)
        result = cmd_register_3dgs(register_args)
        manifest = load_manifest(project_root)
        manifest["external_stages"]["video_to_3dgs"] = {
            "status": "3dgs_trained_registered",
            "notes": "External 3DGS command completed and output was registered.",
            "source_path": str(source_path),
            "output_path": str(output_path),
        }
        save_manifest(project_root, manifest)
        return result

    manifest = load_manifest(project_root)
    manifest["external_stages"]["video_to_3dgs"] = {
        "status": "3dgs_source_prepared",
        "notes": "COLMAP-style source prepared for an external 3DGS trainer; no training command executed.",
        "source_path": str(source_path),
        "output_path": str(output_path),
    }
    save_manifest(project_root, manifest)
    print(f"Prepared 3DGS COLMAP source: {source_path}")
    print(f"Run manifest: {stage_root / '3dgs_run_manifest.json'}")
    return 0


def default_3dgs_command_template(provider: str) -> str:
    normalized = slugify(provider)
    if normalized in {"graphdeco", "gaussian-splatting", "graphdeco-gaussian-splatting"}:
        return "python train.py -s {source_path} -m {output_path}"
    if normalized in {"nerfstudio", "splatfacto", "ns-splatfacto"}:
        return "ns-train splatfacto --data {source_path} --output-dir {output_path}"
    if normalized in {"gsplat", "full-gsplat"}:
        return "python train_gsplat_full.py --data {source_path} --output {output_path}"
    return "echo Fill in external 3DGS command for provider={provider} source={source_path} output={output_path}"


def cmd_prepare_high_quality_3dgs_job(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    provider = args.provider
    stage_root = ensure_dir(args.work_dir.resolve() if args.work_dir else project_root / "external" / "high_quality_3dgs")
    source_path = args.source_path.resolve() if args.source_path else stage_root / "colmap_source"
    output_path = args.output_path.resolve() if args.output_path else project_root / "scene" / "reconstruction" / f"3dgs_{slugify(provider)}"
    log_path = project_root / "logs" / f"{slugify(provider)}_3dgs_train.log"
    ensure_dir(log_path.parent)

    export_args = argparse.Namespace(
        project_root=project_root,
        output_dir=source_path,
        frames_dir=args.frames_dir,
        camera_info=args.camera_info,
        point_cloud=args.point_cloud,
        camera_model=args.camera_model,
        extrinsic_type=args.extrinsic_type,
        mode=args.image_mode,
    )
    cmd_export_colmap(export_args)
    manifest = load_manifest(project_root)

    command_template = args.command_template or default_3dgs_command_template(provider)
    values = {
        "provider": provider,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "project_root": str(project_root),
        "work_dir": str(stage_root),
        "scene_id": str(manifest.get("scene_id", project_root.name)),
        "log_path": str(log_path),
    }
    command = command_from_template(command_template, values)
    job = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "stage": "high_quality_3dgs_training",
        "provider": provider,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "source_path": str(source_path),
        "output_path": str(output_path),
        "work_dir": str(stage_root),
        "log_path": str(log_path),
        "camera_model": args.camera_model,
        "command_template": command_template,
        "command": command,
        "expected_registration": {
            "command": f"python -m video2mesh.cli register-3dgs --project-root {project_root} --path {output_path}",
            "notes": "After external training finishes, register the output directory or final point_cloud.ply to replace the minimal baseline.",
        },
        "quality_targets": {
            "notes": "Use a production trainer with densification/pruning/SH/exposure handling. This job only prepares data and commands.",
            "replaces": "video2mesh_minimal_gsplat",
        },
    }
    job_path = stage_root / "high_quality_3dgs_job.json"
    write_json(job_path, job)
    script_path = stage_root / "run_high_quality_3dgs.sh"
    script = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"mkdir -p {output_path!s}",
        f"mkdir -p {log_path.parent!s}",
        f"{command} 2>&1 | tee {log_path}",
        f"python -m video2mesh.cli register-3dgs --project-root {project_root} --path {output_path}",
    ]
    script_path.write_text("\n".join(script) + "\n", encoding="utf-8")
    script_path.chmod(0o755)

    manifest.setdefault("artifacts", {})["high_quality_3dgs_job"] = str(job_path)
    manifest.setdefault("external_stages", {})["video_to_3dgs"] = {
        "status": "high_quality_3dgs_job_prepared",
        "notes": "Prepared COLMAP-style source and external high-quality 3DGS trainer command; training not executed.",
        "provider": provider,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "job": str(job_path),
        "script": str(script_path),
    }
    save_manifest(project_root, manifest)

    print(f"Prepared high-quality 3DGS job: {job_path}")
    print(f"Provider: {provider}")
    print(f"Source: {source_path}")
    print(f"Output: {output_path}")
    print(f"Script: {script_path}")
    return 0


def import_torch_and_gsplat():
    try:
        import torch  # type: ignore
        import gsplat  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("train-gsplat requires torch and gsplat.") from exc
    return torch, gsplat


def write_gsplat_ply(
    path: Path,
    means,
    colors,
    opacities,
    scales,
    quats,
) -> None:
    np = import_numpy()
    means_np = np.asarray(means, dtype=np.float32)
    colors_np = np.clip(np.asarray(colors, dtype=np.float32), 0.0, 1.0)
    opacities_np = np.asarray(opacities, dtype=np.float32).reshape(-1)
    scales_np = np.asarray(scales, dtype=np.float32)
    quats_np = np.asarray(quats, dtype=np.float32)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {means_np.shape[0]}\n")
        for name in ["x", "y", "z", "red", "green", "blue", "opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]:
            if name in {"red", "green", "blue"}:
                f.write(f"property uchar {name}\n")
            else:
                f.write(f"property float {name}\n")
        f.write("end_header\n")
        rgb = np.clip(np.rint(colors_np * 255.0), 0, 255).astype(np.uint8)
        for point, color, opacity, scale, quat in zip(means_np, rgb, opacities_np, scales_np, quats_np):
            values = [
                f"{float(point[0]):.8f}",
                f"{float(point[1]):.8f}",
                f"{float(point[2]):.8f}",
                str(int(color[0])),
                str(int(color[1])),
                str(int(color[2])),
                f"{float(opacity):.8f}",
                f"{float(scale[0]):.8f}",
                f"{float(scale[1]):.8f}",
                f"{float(scale[2]):.8f}",
                f"{float(quat[0]):.8f}",
                f"{float(quat[1]):.8f}",
                f"{float(quat[2]):.8f}",
                f"{float(quat[3]):.8f}",
            ]
            f.write(" ".join(values) + "\n")


def read_gsplat_ply(path: Path) -> dict[str, Any]:
    np = import_numpy()
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        header = []
        vertex_count = None
        properties = []
        for raw_line in f:
            line = raw_line.rstrip("\n")
            header.append(line)
            stripped = line.strip()
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
            elif stripped.startswith("property") and vertex_count is not None:
                properties.append(stripped.split()[-1])
            elif stripped == "end_header":
                break
        if vertex_count is None:
            raise RuntimeError(f"PLY file has no element vertex header: {path}")
        rows = [f.readline().strip().split() for _ in range(vertex_count)]
    name_to_idx = {name: idx for idx, name in enumerate(properties)}
    required_xyz = {"x", "y", "z"}
    if not required_xyz.issubset(name_to_idx):
        missing = ", ".join(sorted(required_xyz - set(name_to_idx)))
        raise ValueError(f"Not a renderable gsplat PLY, missing properties: {missing}")
    has_rgb = {"red", "green", "blue"}.issubset(name_to_idx)
    has_dc = {"f_dc_0", "f_dc_1", "f_dc_2"}.issubset(name_to_idx)
    if not has_rgb and not has_dc:
        raise ValueError("Not a renderable gsplat PLY, missing red/green/blue or f_dc_0/f_dc_1/f_dc_2 color properties")
    points = np.array(
        [[float(row[name_to_idx["x"]]), float(row[name_to_idx["y"]]), float(row[name_to_idx["z"]])] for row in rows],
        dtype=np.float32,
    )
    if has_rgb:
        colors = np.array(
            [
                [
                    float(row[name_to_idx["red"]]) / 255.0,
                    float(row[name_to_idx["green"]]) / 255.0,
                    float(row[name_to_idx["blue"]]) / 255.0,
                ]
                for row in rows
            ],
            dtype=np.float32,
        )
    else:
        colors = sh_dc_to_rgb(
            np.array(
                [
                    [
                        float(row[name_to_idx["f_dc_0"]]),
                        float(row[name_to_idx["f_dc_1"]]),
                        float(row[name_to_idx["f_dc_2"]]),
                    ]
                    for row in rows
                ],
                dtype=np.float32,
            )
        )
    opacities_raw = np.array(
        [float(row[name_to_idx["opacity"]]) if "opacity" in name_to_idx else 0.5 for row in rows],
        dtype=np.float32,
    )
    opacities = 1.0 / (1.0 + np.exp(-opacities_raw)) if has_dc and "opacity" in name_to_idx else opacities_raw
    scales_raw = np.array(
        [
            [
                float(row[name_to_idx["scale_0"]]) if "scale_0" in name_to_idx else 0.02,
                float(row[name_to_idx["scale_1"]]) if "scale_1" in name_to_idx else 0.02,
                float(row[name_to_idx["scale_2"]]) if "scale_2" in name_to_idx else 0.02,
            ]
            for row in rows
        ],
        dtype=np.float32,
    )
    scales = np.exp(scales_raw) if has_dc and {"scale_0", "scale_1", "scale_2"}.issubset(name_to_idx) else scales_raw
    quats = np.array(
        [
            [
                float(row[name_to_idx["rot_0"]]) if "rot_0" in name_to_idx else 1.0,
                float(row[name_to_idx["rot_1"]]) if "rot_1" in name_to_idx else 0.0,
                float(row[name_to_idx["rot_2"]]) if "rot_2" in name_to_idx else 0.0,
                float(row[name_to_idx["rot_3"]]) if "rot_3" in name_to_idx else 0.0,
            ]
            for row in rows
        ],
        dtype=np.float32,
    )
    return {
        "means": points,
        "colors": colors,
        "opacities": opacities,
        "scales": scales,
        "quats": quats,
        "properties": properties,
    }


def read_ascii_ply_property(path: Path, property_name: str) -> list[Any] | None:
    try:
        _header, properties, rows = read_ascii_ply_table(path)
    except Exception:
        return None
    property_to_index = {name: idx for idx, name in enumerate(properties)}
    if property_name not in property_to_index:
        return None
    idx = property_to_index[property_name]
    values = []
    for row in rows:
        raw = row[idx]
        try:
            values.append(int(float(raw)))
        except ValueError:
            values.append(raw)
    return values


def export_viewer_plys(
    source_ply: Path,
    output_dir: Path,
    prefix: str,
    include_labels: bool = False,
) -> dict[str, Any]:
    np = import_numpy()
    data = read_gsplat_ply(source_ply)
    labels = read_ascii_ply_property(source_ply, "object_id") if include_labels else None
    display_colors = data["colors"]
    if labels is not None:
        display_colors = semantic_colors_for_labels(np.asarray(labels, dtype=np.int64)) / 255.0
    plain_path = output_dir / f"{prefix}_point_cloud.ply"
    supersplat_path = output_dir / f"{prefix}_supersplat.ply"
    write_point_cloud_ascii_ply(plain_path, data["means"], display_colors)
    write_supersplat_ply(
        supersplat_path,
        data["means"],
        display_colors,
        data["opacities"],
        data["scales"],
        data["quats"],
        labels=labels,
    )
    return {
        "source_ply": str(source_ply),
        "point_cloud_ply": str(plain_path),
        "supersplat_ply": str(supersplat_path),
        "vertex_count": int(data["means"].shape[0]),
        "includes_object_id": bool(labels is not None),
        "notes": (
            "point_cloud_ply is a plain XYZ/RGB PLY for Preview/CloudCompare. "
            "supersplat_ply uses GraphDECO/SuperSplat Gaussian fields f_dc_*, opacity, scale_*, and rot_*."
        ),
    }


def load_frame_tensor(path: Path, width: int, height: int, device: str):
    np = import_numpy()
    cv2 = import_cv2()
    torch, _gsplat = import_torch_and_gsplat()
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Failed to read frame image: {path}")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    if image.shape[1] != width or image.shape[0] != height:
        image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    image = image.astype(np.float32) / 255.0
    return torch.from_numpy(image).to(device=device, dtype=torch.float32)


def camera_tensors_for_frame(camera_info: dict[str, Any], frame_id: str, extrinsic_type: str, device: str):
    torch, _gsplat = import_torch_and_gsplat()
    intrinsic = intrinsic_for_frame(camera_info, frame_id)
    extrinsic = resolve_extrinsic(camera_info["extrinsic"], frame_id)
    if extrinsic is None:
        raise ValueError(f"Missing camera extrinsic for frame {frame_id}")
    w2c = world_to_camera_matrix(extrinsic, camera_info.get("extrinsic_type") or extrinsic_type)
    viewmat = torch.tensor(w2c, device=device, dtype=torch.float32)
    K = torch.tensor(
        [
            [float(intrinsic["fx"]), 0.0, float(intrinsic["cx"])],
            [0.0, float(intrinsic.get("fy", intrinsic["fx"])), float(intrinsic["cy"])],
            [0.0, 0.0, 1.0],
        ],
        device=device,
        dtype=torch.float32,
    )
    return intrinsic, viewmat, K


def cmd_train_gsplat(args: argparse.Namespace) -> int:
    np = import_numpy()
    torch, gsplat = import_torch_and_gsplat()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    output_dir = args.output_dir or (project_root / manifest["scene"]["scene_3dgs"])
    output_dir = output_dir.resolve()
    iteration_dir = ensure_dir(output_dir / "point_cloud" / f"iteration_{int(args.iterations)}")
    log_path = project_root / "logs" / "gsplat_train_log.json"

    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]
    camera_info = load_camera_info(camera_info_path)
    points, colors = read_point_cloud(point_cloud_path)
    if points.shape[0] == 0:
        raise RuntimeError(f"No points found in point cloud: {point_cloud_path}")
    if args.max_points and points.shape[0] > args.max_points:
        rng = np.random.default_rng(args.seed)
        choice = np.sort(rng.choice(points.shape[0], size=int(args.max_points), replace=False))
        points = points[choice]
        colors = colors[choice] if colors is not None else None

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is False.")

    points_np = np.asarray(points, dtype=np.float32)
    colors_np = np.asarray(colors if colors is not None else np.full((points_np.shape[0], 3), 0.6), dtype=np.float32)
    spacing = float(args.init_scale)
    if args.init_scale <= 0:
        try:
            from scipy.spatial import cKDTree  # type: ignore

            distances, _indices = cKDTree(points_np).query(points_np, k=min(2, points_np.shape[0]))
            if distances.ndim == 2 and distances.shape[1] > 1:
                positive = distances[:, 1][distances[:, 1] > 1e-8]
                spacing = float(np.median(positive)) if positive.size else 0.02
        except Exception:
            spacing = 0.02
    spacing = max(spacing, 1e-4)

    means = torch.nn.Parameter(torch.tensor(points_np, device=device, dtype=torch.float32))
    color_logits = torch.nn.Parameter(torch.logit(torch.tensor(np.clip(colors_np, 1e-4, 1.0 - 1e-4), device=device, dtype=torch.float32)))
    log_scales = torch.nn.Parameter(torch.full((points_np.shape[0], 3), float(np.log(spacing)), device=device, dtype=torch.float32))
    opacity_logits = torch.nn.Parameter(torch.full((points_np.shape[0],), float(args.init_opacity_logit), device=device, dtype=torch.float32))
    quats = torch.zeros((points_np.shape[0], 4), device=device, dtype=torch.float32)
    quats[:, 0] = 1.0

    optimizer = torch.optim.Adam(
        [
            {"params": [means], "lr": args.lr_position},
            {"params": [color_logits], "lr": args.lr_color},
            {"params": [log_scales], "lr": args.lr_scale},
            {"params": [opacity_logits], "lr": args.lr_opacity},
        ]
    )
    frame_records = []
    for frame_path in frames:
        frame_id = frame_id_for_path(frame_path)
        intrinsic, viewmat, K = camera_tensors_for_frame(camera_info, frame_id, args.extrinsic_type, device)
        target_width = int(args.width or intrinsic["w"])
        target_height = int(args.height or intrinsic["h"])
        target = load_frame_tensor(frame_path, target_width, target_height, device)
        frame_records.append(
            {
                "frame_id": frame_id,
                "path": str(frame_path),
                "viewmat": viewmat,
                "K": K,
                "target": target,
                "width": target_width,
                "height": target_height,
            }
        )
    if not frame_records:
        raise RuntimeError("No training frames available.")

    train_log = []
    start = time.time()
    for step in range(1, int(args.iterations) + 1):
        record = frame_records[(step - 1) % len(frame_records)]
        optimizer.zero_grad(set_to_none=True)
        colors_t = torch.sigmoid(color_logits)
        scales_t = torch.exp(log_scales).clamp(args.min_scale, args.max_scale)
        opacities_t = torch.sigmoid(opacity_logits)
        render, alphas, _meta = gsplat.rasterization(
            means,
            quats,
            scales_t,
            opacities_t,
            colors_t,
            record["viewmat"][None],
            record["K"][None],
            width=int(record["width"]),
            height=int(record["height"]),
            packed=False,
            backgrounds=record["target"].reshape(-1, 3).mean(dim=0, keepdim=True),
            render_mode="RGB",
        )
        pred = render[0]
        loss = torch.nn.functional.l1_loss(pred, record["target"])
        if args.alpha_reg > 0:
            loss = loss + float(args.alpha_reg) * alphas.mean()
        loss.backward()
        optimizer.step()
        if step == 1 or step == args.iterations or step % args.log_every == 0:
            train_log.append({"step": step, "frame_id": record["frame_id"], "loss": float(loss.detach().cpu())})
            print(f"step={step} frame={record['frame_id']} loss={float(loss.detach().cpu()):.6f}")

    with torch.no_grad():
        colors_out = torch.sigmoid(color_logits).detach().cpu().numpy()
        scales_out = torch.exp(log_scales).clamp(args.min_scale, args.max_scale).detach().cpu().numpy()
        opacities_out = torch.sigmoid(opacity_logits).detach().cpu().numpy()
        means_out = means.detach().cpu().numpy()
        quats_out = quats.detach().cpu().numpy()

    splat_ply = iteration_dir / "point_cloud.ply"
    write_gsplat_ply(splat_ply, means_out, colors_out, opacities_out, scales_out, quats_out)
    viewer_exports = export_viewer_plys(splat_ply, iteration_dir, "point_cloud")
    trainer_manifest_path = output_dir / "video2mesh_gsplat_train.json"
    trainer_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "trainer": "video2mesh_minimal_gsplat",
        "project_root": str(project_root),
        "frames_dir": str(frames_dir),
        "camera_info": str(camera_info_path),
        "input_point_cloud": str(point_cloud_path),
        "output_dir": str(output_dir),
        "splat_ply": str(splat_ply),
        "point_cloud_ply": viewer_exports["point_cloud_ply"],
        "supersplat_ply": viewer_exports["supersplat_ply"],
        "device": device,
        "point_count": int(means_out.shape[0]),
        "frame_count": len(frame_records),
        "iterations": int(args.iterations),
        "elapsed_seconds": round(time.time() - start, 3),
        "log": train_log,
        "notes": (
            "Minimal gsplat trainer for Video2Mesh integration. It optimizes point-initialized "
            "3D Gaussians without densification/pruning or SH; use it as a real differentiable "
            "3DGS smoke/baseline, not as final-quality reconstruction."
        ),
    }
    write_json(trainer_manifest_path, trainer_manifest)

    register_args = argparse.Namespace(project_root=project_root, path=output_dir, mode=args.register_mode)
    result = cmd_register_3dgs(register_args)
    manifest = load_manifest(project_root)
    manifest["artifacts"]["gsplat_train_manifest"] = str(trainer_manifest_path)
    manifest["artifacts"]["scene_3dgs_point_cloud_ply"] = viewer_exports["point_cloud_ply"]
    manifest["artifacts"]["scene_3dgs_supersplat_ply"] = viewer_exports["supersplat_ply"]
    manifest["external_stages"]["video_to_3dgs"] = {
        "status": "gsplat_trained_registered",
        "notes": "Minimal gsplat trainer completed and output was registered.",
        "output_path": str(output_dir),
        "point_cloud_ply": viewer_exports["point_cloud_ply"],
        "supersplat_ply": viewer_exports["supersplat_ply"],
        "point_count": int(means_out.shape[0]),
        "iterations": int(args.iterations),
        "frame_count": len(frame_records),
    }
    save_manifest(project_root, manifest)
    print(f"Minimal gsplat output: {splat_ply}")
    print(f"Training manifest: {trainer_manifest_path}")
    return result


def save_rgb_image(path: Path, image_array) -> None:
    np = import_numpy()
    cv2 = import_cv2()
    ensure_dir(path.parent)
    rgb = np.clip(np.rint(np.asarray(image_array, dtype=np.float32) * 255.0), 0, 255).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def psnr_from_mse(mse: float) -> float:
    if mse <= 1e-12:
        return 99.0
    import math

    return float(-10.0 * math.log10(float(mse)))


def cmd_render_gsplat_preview(args: argparse.Namespace) -> int:
    np = import_numpy()
    torch, gsplat = import_torch_and_gsplat()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    splat_ply = args.splat_ply or resolve_existing_path(manifest.get("artifacts", {}).get("scene_3dgs_ply"), project_root)
    if splat_ply is None or not splat_ply.exists():
        raise FileNotFoundError("No renderable 3DGS PLY found. Run train-gsplat/register-3dgs or pass --splat-ply.")
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "gsplat_preview"))

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is False.")

    data = read_gsplat_ply(splat_ply)
    means = torch.tensor(data["means"], device=device, dtype=torch.float32)
    colors = torch.tensor(data["colors"], device=device, dtype=torch.float32)
    opacities = torch.tensor(data["opacities"], device=device, dtype=torch.float32)
    scales = torch.tensor(data["scales"], device=device, dtype=torch.float32)
    quats = torch.tensor(data["quats"], device=device, dtype=torch.float32)
    camera_info = load_camera_info(camera_info_path)
    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]

    frame_metrics = []
    with torch.no_grad():
        for frame_path in frames:
            frame_id = frame_id_for_path(frame_path)
            intrinsic, viewmat, K = camera_tensors_for_frame(camera_info, frame_id, args.extrinsic_type, device)
            width = int(args.width or intrinsic["w"])
            height = int(args.height or intrinsic["h"])
            target = load_frame_tensor(frame_path, width, height, device)
            background = target.reshape(-1, 3).mean(dim=0, keepdim=True) if args.background == "target_mean" else None
            if args.background == "white":
                background = torch.ones((1, 3), device=device, dtype=torch.float32)
            elif args.background == "black":
                background = torch.zeros((1, 3), device=device, dtype=torch.float32)
            render, alphas, _meta = gsplat.rasterization(
                means,
                quats,
                scales,
                opacities,
                colors,
                viewmat[None],
                K[None],
                width=width,
                height=height,
                packed=False,
                backgrounds=background,
                render_mode="RGB",
            )
            pred = render[0].clamp(0.0, 1.0)
            error = (pred - target).abs()
            l1 = float(error.mean().detach().cpu())
            mse = float(torch.mean((pred - target) ** 2).detach().cpu())
            alpha_mean = float(alphas.mean().detach().cpu())
            frame_dir = ensure_dir(output_dir / frame_id)
            pred_np = pred.detach().cpu().numpy()
            target_np = target.detach().cpu().numpy()
            error_np = error.detach().cpu().numpy()
            save_rgb_image(frame_dir / "render.png", pred_np)
            save_rgb_image(frame_dir / "target.png", target_np)
            save_rgb_image(frame_dir / "error.png", np.clip(error_np * args.error_gain, 0.0, 1.0))
            frame_metrics.append(
                {
                    "frame_id": frame_id,
                    "source_image": str(frame_path),
                    "render": str(frame_dir / "render.png"),
                    "target": str(frame_dir / "target.png"),
                    "error": str(frame_dir / "error.png"),
                    "width": width,
                    "height": height,
                    "l1": l1,
                    "mse": mse,
                    "psnr": psnr_from_mse(mse),
                    "alpha_mean": alpha_mean,
                }
            )

    mean_l1 = float(np.mean([item["l1"] for item in frame_metrics])) if frame_metrics else None
    mean_psnr = float(np.mean([item["psnr"] for item in frame_metrics])) if frame_metrics else None
    preview_manifest_path = output_dir / "preview_manifest.json"
    preview_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "splat_ply": str(splat_ply),
        "frames_dir": str(frames_dir),
        "camera_info": str(camera_info_path),
        "output_dir": str(output_dir),
        "device": device,
        "background": args.background,
        "gaussian_count": int(means.shape[0]),
        "frame_count": len(frame_metrics),
        "mean_l1": mean_l1,
        "mean_psnr": mean_psnr,
        "frames": frame_metrics,
        "notes": "Preview render/target/error images for checking whether the registered 3DGS explains the input frames.",
    }
    write_json(preview_manifest_path, preview_manifest)
    manifest["artifacts"]["gsplat_preview"] = str(preview_manifest_path)
    save_manifest(project_root, manifest)
    print(f"Rendered {len(frame_metrics)} gsplat preview frame(s) to {output_dir}")
    print(f"mean_l1={mean_l1:.6f} mean_psnr={mean_psnr:.3f}" if mean_l1 is not None and mean_psnr is not None else "No preview frames rendered.")
    print(f"Preview manifest: {preview_manifest_path}")
    return 0


def cmd_import_mast3r_slam(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    traj_path = args.trajectory.resolve()
    if not traj_path.exists():
        raise FileNotFoundError(f"MASt3R-SLAM trajectory not found: {traj_path}")
    poses = read_mast3r_slam_traj(traj_path)

    keyframes_dir = args.frames_dir.resolve() if args.frames_dir else None
    intrinsic_dir = keyframes_dir if (args.use_keyframes_as_scene_frames or args.width is None or args.height is None) else None
    intrinsic = estimate_or_read_intrinsic(args, intrinsic_dir)
    extrinsics = {
        pose["frame_id"]: matrix_inverse(pose["camera_to_world"]).tolist()
        for pose in poses
    }
    camera_info = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "source": "mast3r_slam",
        "extrinsic_type": "world_to_camera",
        "intrinsic": intrinsic,
        "extrinsic": extrinsics,
        "timestamps": {pose["frame_id"]: pose["timestamp"] for pose in poses},
        "camera_to_world": {pose["frame_id"]: pose["camera_to_world"] for pose in poses},
        "notes": "MASt3R-SLAM trajectory is imported from timestamp x y z qx qy qz qw T_WC format.",
    }
    camera_info_path = project_root / manifest["scene"]["camera_info"]
    write_json(camera_info_path, camera_info)
    manifest["artifacts"]["camera_info"] = str(camera_info_path)
    manifest["artifacts"]["mast3r_slam_trajectory"] = str(traj_path)
    manifest["artifacts"]["mast3r_slam_pose_count"] = len(poses)
    manifest["external_stages"]["video_to_3dgs"] = {
        "status": "imported_mast3r_slam",
        "notes": "Imported MASt3R-SLAM trajectory, reconstruction PLY, and keyframes when provided. This is a dense SLAM/point-cloud reconstruction stage; register a trained 3DGS separately if needed.",
    }

    if args.reconstruction_ply:
        point_cloud_path = project_root / manifest["scene"]["point_cloud"]
        copy_or_link(args.reconstruction_ply.resolve(), point_cloud_path, args.mode)
        manifest["artifacts"]["point_cloud"] = str(point_cloud_path)

    if keyframes_dir:
        if args.use_keyframes_as_scene_frames:
            dst_dir = project_root / manifest["scene"]["frames_dir"]
            copied = copy_image_dir(keyframes_dir, dst_dir, args.mode, clear=bool(args.clear_keyframes_output))
            manifest["artifacts"]["frames"] = str(dst_dir)
            manifest["artifacts"]["frames_imported"] = copied
        else:
            dst_dir = project_root / MAST3R_KEYFRAMES_DIR
            copied = copy_image_dir(keyframes_dir, dst_dir, args.mode, clear=bool(args.clear_keyframes_output))
            manifest["artifacts"]["mast3r_keyframes"] = str(dst_dir)
            manifest["artifacts"]["mast3r_keyframes_imported"] = copied

    save_manifest(project_root, manifest)
    print(f"Imported MASt3R-SLAM trajectory: {traj_path}")
    print(f"Poses: {len(poses)}")
    if intrinsic.get("estimated"):
        print("Warning: intrinsics are estimated. Pass --fx --fy --cx --cy for calibrated mask projection.")
    return 0


def find_mast3r_slam_outputs(mast3r_root: Path, save_as: str, dataset_path: Path) -> tuple[Path, Path | None, Path | None]:
    log_dir = mast3r_root / "logs" / save_as if save_as != "default" else mast3r_root / "logs"
    seq_name = dataset_path.stem
    trajectory = log_dir / f"{seq_name}.txt"
    reconstruction = log_dir / f"{seq_name}.ply"
    keyframes = log_dir / "keyframes" / seq_name
    if not trajectory.exists():
        candidates = sorted(log_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True) if log_dir.exists() else []
        if len(candidates) == 1:
            trajectory = candidates[0]
            seq_name = trajectory.stem
            reconstruction = log_dir / f"{seq_name}.ply"
            keyframes = log_dir / "keyframes" / seq_name
        else:
            raise FileNotFoundError(f"MASt3R-SLAM trajectory not found: {trajectory}")
    return trajectory, reconstruction if reconstruction.exists() else None, keyframes if keyframes.exists() else None


def cmd_run_mast3r_slam(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    dataset_value = args.dataset or args.video or manifest.get("inputs", {}).get("video")
    if not dataset_value:
        raise ValueError("Pass --dataset/--video or initialize the project with --video.")
    dataset = Path(dataset_value).resolve()
    if not dataset.exists():
        raise FileNotFoundError(f"MASt3R-SLAM dataset/video not found: {dataset}")

    mast3r_root = args.mast3r_root.resolve()
    main_py = mast3r_root / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"MASt3R-SLAM main.py not found: {main_py}")

    save_as = args.save_as or manifest["scene_id"]
    command = [
        sys.executable,
        "main.py",
        "--dataset",
        str(dataset),
        "--config",
        str(args.config),
        "--save-as",
        save_as,
        "--no-viz",
    ]
    if args.calib:
        command.extend(["--calib", str(args.calib.resolve())])

    log_path = project_root / "logs" / "mast3r_slam_run.log"
    ensure_dir(log_path.parent)
    print("Running MASt3R-SLAM:")
    print(" ".join(command))
    env = os.environ.copy()
    mast3r_python_paths = [
        str(mast3r_root),
        str(mast3r_root / "thirdparty" / "mast3r"),
        str(mast3r_root / "thirdparty" / "mast3r" / "dust3r"),
    ]
    if env.get("PYTHONPATH"):
        mast3r_python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(mast3r_python_paths)
    try:
        import torch  # type: ignore

        torch_lib = Path(torch.__file__).resolve().parent / "lib"
        env["LD_LIBRARY_PATH"] = os.pathsep.join([str(torch_lib), env.get("LD_LIBRARY_PATH", "")]).rstrip(os.pathsep)
    except Exception:
        pass
    with log_path.open("w", encoding="utf-8") as log_file:
        completed = subprocess.run(command, cwd=mast3r_root, env=env, stdout=log_file, stderr=subprocess.STDOUT, check=False)
    if completed.returncode != 0:
        print(f"MASt3R-SLAM failed with exit code {completed.returncode}. See log: {log_path}")
        return completed.returncode

    trajectory, reconstruction, keyframes = find_mast3r_slam_outputs(mast3r_root, save_as, dataset)
    manifest = load_manifest(project_root)
    manifest["artifacts"]["mast3r_slam_log"] = str(log_path)
    save_manifest(project_root, manifest)

    import_args = argparse.Namespace(
        project_root=project_root,
        trajectory=trajectory,
        reconstruction_ply=reconstruction,
        frames_dir=keyframes,
        width=args.width,
        height=args.height,
        fx=args.fx,
        fy=args.fy,
        cx=args.cx,
        cy=args.cy,
        focal_scale=args.focal_scale,
        mode=args.mode,
        use_keyframes_as_scene_frames=args.use_keyframes_as_scene_frames,
        clear_keyframes_output=True,
    )
    result = cmd_import_mast3r_slam(import_args)
    print(f"MASt3R-SLAM log: {log_path}")
    return result


@dataclass
class MaskRecord:
    object_id: str
    frame_id: str
    path: Path


def scan_mask_records(mask_root: Path) -> list[MaskRecord]:
    records: list[MaskRecord] = []
    if not mask_root.exists():
        raise FileNotFoundError(f"2D mask root not found: {mask_root}")

    for child in sorted(mask_root.iterdir()):
        if child.is_dir():
            object_id = slugify(child.name)
            for mask_path in sorted(child.iterdir()):
                if mask_path.suffix.lower() in MASK_EXTENSIONS:
                    records.append(MaskRecord(object_id, frame_stem(mask_path.stem), mask_path))
        elif child.is_file() and child.suffix.lower() in MASK_EXTENSIONS:
            match = re.match(r"^(\d+)[_-](.+)$", child.stem)
            if match:
                frame_id, object_id = match.groups()
                records.append(MaskRecord(slugify(object_id), frame_stem(frame_id), child))

    if not records:
        raise FileNotFoundError(
            f"No masks found in {mask_root}. Use <object_id>/<frame>.png or <frame>_<object_id>.png."
        )
    return records


def read_optional_json(path: Path | None) -> Any:
    if path and path.exists():
        return read_json(path)
    return None


def external_segmentation_prompt_objects(prompts_path: Path | None, frames: list[Path]) -> list[dict[str, Any]]:
    if not prompts_path:
        return []
    data = read_json(prompts_path.resolve())
    raw_objects: list[Any]
    if isinstance(data, dict) and isinstance(data.get("objects"), list):
        raw_objects = data["objects"]
    elif isinstance(data, dict):
        raw_objects = []
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            item = dict(value)
            item.setdefault("id", key)
            raw_objects.append(item)
    elif isinstance(data, list):
        raw_objects = data
    else:
        raise ValueError("Prompt JSON must be a list, an object map, or contain an objects list.")

    objects = []
    fallback_frame = frame_stem(frames[0].stem) if frames else "000000"
    for idx, raw in enumerate(raw_objects):
        if not isinstance(raw, dict):
            continue
        object_id = slugify(raw.get("object_id") or raw.get("id") or raw.get("name") or f"object_{idx:02d}")
        objects.append(
            {
                "object_id": object_id,
                "name": raw.get("name", object_id.replace("_", " ")),
                "category": raw.get("category", "unknown"),
                "description": raw.get("description", ""),
                "frame_id": frame_stem(raw.get("frame_id", raw.get("frame", fallback_frame))),
                "bbox": raw.get("bbox") or raw.get("box"),
                "prompt": raw,
            }
        )
    return objects


def cmd_prepare_video_segmentation_jobs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    frames_dir = frames_dir.resolve()
    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]
    prompts_path = args.prompts or resolve_existing_path(manifest.get("artifacts", {}).get("tracking_prompts"), project_root)
    prompts = external_segmentation_prompt_objects(prompts_path, frames)
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "video_segmentation_jobs"))
    job_root = ensure_dir(output_dir / "jobs")
    mask_output_root = args.mask_output_root or (project_root / manifest["masks"]["mask_2d_dir"])

    frame_records = [
        {
            "frame_id": frame_stem(frame.stem),
            "image": str(frame),
            "index": index,
        }
        for index, frame in enumerate(frames)
    ]
    objects = []
    for prompt in prompts:
        objects.append(
            {
                "object_id": prompt["object_id"],
                "name": prompt.get("name"),
                "category": prompt.get("category"),
                "description": prompt.get("description", ""),
                "prompt_frame": prompt.get("frame_id"),
                "bbox": prompt.get("bbox"),
                "bbox_format": (prompt.get("prompt") or {}).get("bbox_format") or (prompt.get("prompt") or {}).get("format") or "xyxy",
            }
        )

    job = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "provider": args.provider,
        "frames_dir": str(frames_dir),
        "frame_count": len(frame_records),
        "frames": frame_records,
        "prompts": str(prompts_path) if prompts_path else None,
        "objects": objects,
        "expected_output": {
            "mask_root": str(mask_output_root),
            "layout": "masks/<object_id>/<frame_id>.png",
            "manifest": str(output_dir / "external_masks_manifest.json"),
        },
        "notes": (
            "Prepared for external video segmentation/tracking tools such as SAM2, DEVA, XMem, or Grounded-SAM. "
            "Run the external tool, then use import-video-segmentation-masks to normalize outputs into masks/2d."
        ),
    }
    job_path = output_dir / "video_segmentation_job.json"
    write_json(job_path, job)
    per_provider_job_path = job_root / f"{slugify(args.provider, 'external')}.json"
    write_json(per_provider_job_path, job)

    command = None
    if args.command_template:
        values = {
            "job_path": str(job_path),
            "project_root": str(project_root),
            "frames_dir": str(frames_dir),
            "prompts": str(prompts_path) if prompts_path else "",
            "mask_output_root": str(mask_output_root),
            "provider": args.provider,
        }
        command = args.command_template.format(**values)
    script_path = output_dir / "run_video_segmentation.sh"
    script_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if command:
        script_lines.append(command)
    else:
        script_lines.append(f'echo "Fill in external {args.provider} segmentation command for job: {job_path}"')
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    script_path.chmod(0o755)

    manifest.setdefault("artifacts", {})["video_segmentation_job"] = str(job_path)
    manifest.setdefault("external_stages", {})["segmentation_2d_tracking"] = {
        "status": "external_video_segmentation_job_prepared",
        "notes": "Prepared external video segmentation job; run/import external masks before fuse-masks.",
        "provider": args.provider,
        "job": str(job_path),
        "script": str(script_path),
        "object_count": len(objects),
        "frame_count": len(frame_records),
    }
    save_manifest(project_root, manifest)

    print(f"Prepared external video segmentation job: {job_path}")
    print(f"Frames: {len(frame_records)}; objects/prompts: {len(objects)}")
    print(f"Script: {script_path}")
    return 0


def external_manifest_entries(data: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if isinstance(data, dict) and isinstance(data.get("masks"), list):
        for item in data["masks"]:
            if isinstance(item, dict):
                entries.append(dict(item))
    elif isinstance(data, dict) and isinstance(data.get("objects"), list):
        for obj in data["objects"]:
            if not isinstance(obj, dict):
                continue
            object_id = obj.get("object_id") or obj.get("id") or obj.get("name")
            frames = obj.get("frames") or obj.get("masks") or []
            if isinstance(frames, dict):
                frames = [{"frame_id": key, "mask": value} for key, value in frames.items()]
            for frame in frames:
                if isinstance(frame, dict):
                    item = dict(frame)
                    item.setdefault("object_id", object_id)
                    entries.append(item)
    elif isinstance(data, dict):
        for object_id, frames in data.items():
            if object_id in {"schema_version", "project_root", "scene_id", "notes"}:
                continue
            if isinstance(frames, dict):
                for frame_id, mask in frames.items():
                    entries.append({"object_id": object_id, "frame_id": frame_id, "mask": mask})
            elif isinstance(frames, list):
                for frame in frames:
                    if isinstance(frame, dict):
                        item = dict(frame)
                        item.setdefault("object_id", object_id)
                        entries.append(item)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                entries.append(dict(item))
    return entries


def discover_external_mask_records(mask_root: Path) -> list[MaskRecord]:
    return scan_mask_records(mask_root)


def cmd_import_video_segmentation_masks(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    source_root = args.source_root.resolve() if args.source_root else None
    source_manifest_path = args.source_manifest.resolve() if args.source_manifest else None
    output_root = args.output_dir or (project_root / manifest["masks"]["mask_2d_dir"])
    if args.clear_output and output_root.exists():
        shutil.rmtree(output_root)
    output_root = ensure_dir(output_root)

    imported: dict[str, Any] = {}
    missing: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    source_manifest = read_optional_json(source_manifest_path)
    if source_manifest is not None:
        entries = external_manifest_entries(source_manifest)
    elif source_root:
        entries = [
            {"object_id": record.object_id, "frame_id": record.frame_id, "mask": str(record.path)}
            for record in discover_external_mask_records(source_root)
        ]
    else:
        raise ValueError("Pass --source-root or --source-manifest.")

    for index, entry in enumerate(entries):
        object_id = slugify(entry.get("object_id") or entry.get("id") or entry.get("name") or f"object_{index:02d}")
        frame_id = frame_stem(entry.get("frame_id") or entry.get("frame") or entry.get("image_id") or entry.get("index") or "000000")
        mask_value = entry.get("mask") or entry.get("mask_path") or entry.get("path") or entry.get("file")
        if not mask_value:
            missing.append({"entry": entry, "reason": "missing_mask_path"})
            continue
        mask_path = Path(mask_value)
        if not mask_path.is_absolute():
            if source_root and (source_root / mask_path).exists():
                mask_path = source_root / mask_path
            elif source_manifest_path and (source_manifest_path.parent / mask_path).exists():
                mask_path = source_manifest_path.parent / mask_path
            else:
                mask_path = (source_root or project_root) / mask_path
        if not mask_path.exists():
            missing.append({"object_id": object_id, "frame_id": frame_id, "mask": str(mask_path), "reason": "not_found"})
            if not args.skip_missing:
                raise FileNotFoundError(f"External mask not found: {mask_path}")
            continue
        if mask_path.suffix.lower() not in MASK_EXTENSIONS:
            missing.append({"object_id": object_id, "frame_id": frame_id, "mask": str(mask_path), "reason": "unsupported_extension"})
            if not args.skip_missing:
                raise ValueError(f"Unsupported mask extension: {mask_path}")
            continue
        dst = output_root / object_id / f"{frame_id}{mask_path.suffix.lower()}"
        copied = copy_or_link(mask_path, dst, args.mode)
        imported.setdefault(object_id, {"frames": []})
        imported[object_id]["frames"].append(
            {
                "frame_id": frame_id,
                "source_mask": str(mask_path),
                "mask": str(copied),
                "score": entry.get("score") or entry.get("confidence"),
                "bbox": entry.get("bbox"),
            }
        )

    tracking_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "method": "external_video_segmentation_import",
        "provider": args.provider,
        "source_root": str(source_root) if source_root else None,
        "source_manifest": str(source_manifest_path) if source_manifest_path else None,
        "mask_root": str(output_root),
        "objects": {
            object_id: {
                "frames_written": len(record["frames"]),
                "frames": record["frames"],
            }
            for object_id, record in sorted(imported.items())
        },
        "missing": missing,
        "notes": "External video segmentation masks normalized to Video2Mesh masks/2d layout.",
    }
    tracking_manifest_path = output_root / "tracking_manifest.json"
    write_json(tracking_manifest_path, tracking_manifest)
    manifest.setdefault("artifacts", {})["object_masks_2d"] = str(output_root)
    manifest.setdefault("artifacts", {})["mask_tracking_manifest"] = str(tracking_manifest_path)
    manifest.setdefault("external_stages", {})["segmentation_2d_tracking"] = {
        "status": "external_video_segmentation_masks_imported",
        "notes": "Imported external video segmentation masks into standard Video2Mesh masks/2d layout.",
        "provider": args.provider,
        "object_count": len(imported),
        "mask_count": sum(len(record["frames"]) for record in imported.values()),
        "missing_count": len(missing),
    }
    save_manifest(project_root, manifest)

    total = sum(len(record["frames"]) for record in imported.values())
    print(f"Imported {total} external 2D mask(s) for {len(imported)} object(s) into {output_root}")
    if missing:
        print(f"Missing/skipped entries: {len(missing)}")
    print(f"Tracking manifest: {tracking_manifest_path}")
    return 0


def load_object_labels(project_root: Path, labels_path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = labels_path or (project_root / "masks" / "object_labels.json")
    if path.exists():
        data = read_json(path)
        if isinstance(data, dict):
            return {slugify(k): dict(v) for k, v in data.items()}
    return {}


def normalize_object_label_record(raw: Any, object_id: str) -> dict[str, Any]:
    if isinstance(raw, str):
        return {"object_id": object_id, "name": raw, "category": raw, "description": ""}
    if not isinstance(raw, dict):
        raise ValueError(f"Label for {object_id} must be a JSON object or string.")
    label = dict(raw)
    label["object_id"] = slugify(label.get("object_id") or label.get("id") or object_id)
    if "name" not in label and label.get("label"):
        label["name"] = label["label"]
    if "category" not in label:
        label["category"] = label.get("class") or label.get("class_name") or label.get("name") or "unknown"
    if "description" not in label:
        label["description"] = label.get("caption") or label.get("text") or ""
    return label


def load_object_label_updates(path: Path) -> dict[str, dict[str, Any]]:
    data = read_json(path)
    raw_items: list[tuple[str, Any]] = []
    if isinstance(data, dict) and isinstance(data.get("objects"), list):
        for index, raw in enumerate(data["objects"]):
            if not isinstance(raw, dict):
                raise ValueError(f"objects[{index}] in {path} is not a JSON object.")
            object_id = slugify(raw.get("object_id") or raw.get("id") or raw.get("name") or f"object_{index:02d}")
            raw_items.append((object_id, raw))
    elif isinstance(data, dict):
        for key, value in data.items():
            if key in {"schema_version", "project_root", "scene_id", "notes"}:
                continue
            raw_items.append((slugify(key), value))
    elif isinstance(data, list):
        for index, raw in enumerate(data):
            if not isinstance(raw, dict):
                raise ValueError(f"Item #{index} in {path} is not a JSON object.")
            object_id = slugify(raw.get("object_id") or raw.get("id") or raw.get("name") or f"object_{index:02d}")
            raw_items.append((object_id, raw))
    else:
        raise ValueError(f"Label JSON must be a map, list, or object with an objects list: {path}")

    labels: dict[str, dict[str, Any]] = {}
    for object_id, raw in raw_items:
        label = normalize_object_label_record(raw, object_id)
        labels[label["object_id"]] = label
    return labels


def merge_object_label(target: dict[str, Any], label: dict[str, Any], overwrite: bool) -> dict[str, Any]:
    fields = [
        "name",
        "category",
        "description",
        "aliases",
        "open_vocab_labels",
        "confidence",
        "source",
        "vlm",
    ]
    for field in fields:
        if field not in label:
            continue
        current = target.get(field)
        if overwrite or current in (None, "", [], {}, "unknown"):
            target[field] = label[field]
    target.setdefault("label_history", [])
    if isinstance(target["label_history"], list):
        target["label_history"].append(
            {
                "source": label.get("source", "external_label_import"),
                "name": label.get("name"),
                "category": label.get("category"),
                "description": label.get("description"),
                "confidence": label.get("confidence"),
                "timestamp": int(time.time()),
            }
        )
    return target


def object_labeling_image_records(obj: dict[str, Any], object_dir: Path, project_root: Path, max_images: int) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_image(path_value: Any, role: str, extra: dict[str, Any] | None = None) -> None:
        if not path_value:
            return
        raw_path_text = str(path_value)
        resolved_path = resolve_existing_path(raw_path_text, project_root)
        path_text = str(resolved_path) if resolved_path else raw_path_text
        if path_text in seen:
            return
        seen.add(path_text)
        record = {"path": path_text, "role": role}
        if path_text != raw_path_text:
            record["source_path"] = raw_path_text
        if extra:
            for key, value in extra.items():
                if value in (None, "", []):
                    continue
                if key in {"mask", "image", "object_image", "reference_image", "selected_image"}:
                    resolved_extra = resolve_existing_path(str(value), project_root)
                    resolved_text = str(resolved_extra) if resolved_extra else str(value)
                    record[key] = resolved_text
                    if resolved_text != str(value):
                        record[f"source_{key}"] = str(value)
                else:
                    record[key] = value
        images.append(record)

    primary_object_image = obj.get("primary_object_image") if isinstance(obj.get("primary_object_image"), dict) else {}
    add_image(
        primary_object_image.get("reference_image") or primary_object_image.get("object_image"),
        "primary_object_crop",
        {
            "frame_id": primary_object_image.get("frame_id"),
            "mask": primary_object_image.get("mask"),
            "crop_xyxy": primary_object_image.get("crop_xyxy"),
        },
    )
    primary_frame = obj.get("primary_frame") if isinstance(obj.get("primary_frame"), dict) else {}
    add_image(
        primary_frame.get("selected_image") or primary_frame.get("image"),
        "primary_selected_frame",
        {
            "frame_id": primary_frame.get("frame_id"),
            "score": primary_frame.get("score"),
        },
    )
    for item in obj.get("object_images", []) if isinstance(obj.get("object_images"), list) else []:
        if not isinstance(item, dict):
            continue
        add_image(
            item.get("object_image"),
            "object_crop",
            {
                "frame_id": item.get("frame_id"),
                "rank": item.get("rank"),
                "mask": item.get("mask"),
                "crop_xyxy": item.get("crop_xyxy"),
            },
        )
        if max_images > 0 and len(images) >= max_images:
            return images[:max_images]
    for item in obj.get("selected_frames", []) if isinstance(obj.get("selected_frames"), list) else []:
        if not isinstance(item, dict):
            continue
        add_image(
            item.get("selected_image") or item.get("image"),
            "selected_frame",
            {
                "frame_id": item.get("frame_id"),
                "rank": item.get("rank"),
                "score": item.get("score"),
            },
        )
        if max_images > 0 and len(images) >= max_images:
            break
    if max_images <= 0 or len(images) < max_images:
        reference = object_dir / "reference.png"
        if reference.exists():
            add_image(reference, "reference_file")
    for directory_name, role in (("object_images", "object_crop_file"), ("selected_frames", "selected_frame_file")):
        if max_images > 0 and len(images) >= max_images:
            break
        image_dir = object_dir / directory_name
        if not image_dir.exists():
            continue
        for image_path in sorted(p for p in image_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS):
            frame_id = image_path.stem.split("_")[-1]
            extra = {"frame_id": frame_id}
            mask_path = project_root / "masks" / "2d" / slugify(obj.get("object_id") or object_dir.name) / f"{frame_id}.png"
            if mask_path.exists():
                extra["mask"] = str(mask_path)
            add_image(image_path, role, extra)
            if max_images > 0 and len(images) >= max_images:
                break
    return images[:max_images] if max_images > 0 else images


def cmd_prepare_object_labeling_jobs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks/select-frames first.")

    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "object_labeling_jobs"))
    jobs_dir = ensure_dir(output_dir / "jobs")
    labels_template: dict[str, Any] = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "provider": args.provider,
        "instructions": (
            "Fill name/category/description/open_vocab_labels/confidence for each object_id, "
            "then import this file with `python -m video2mesh.cli import-object-labels --labels <file>`."
        ),
        "objects": [],
    }
    jobs: dict[str, Any] = {}
    skipped: dict[str, str] = {}

    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        if is_background_structure_record(obj) and not args.include_background:
            skipped[object_id] = "background_structure"
            continue
        images = object_labeling_image_records(obj, object_json.parent, project_root, args.max_images)
        if not images and not args.allow_missing_images:
            skipped[object_id] = "missing reference images"
            continue
        job = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "name": obj.get("name", object_id),
            "current_category": obj.get("category", "unknown"),
            "current_description": obj.get("description", ""),
            "asset_role": obj.get("asset_role", "object"),
            "object_json": str(object_json),
            "bbox_3d": obj.get("bbox_3d"),
            "point_count": obj.get("point_count", 0),
            "mask_3d_cloud": str(resolve_existing_path((obj.get("mask_3d_cloud") or {}).get("path"), project_root)) if isinstance(obj.get("mask_3d_cloud"), dict) and (obj.get("mask_3d_cloud") or {}).get("path") else None,
            "images": images,
            "recommended_prompt": (
                "Identify the main physical object shown by the masked crop/selected frames. "
                "Return JSON with object_id, name, category, description, aliases, open_vocab_labels, confidence, and source."
            ),
            "expected_output_schema": {
                "object_id": object_id,
                "name": "",
                "category": "",
                "description": "",
                "aliases": [],
                "open_vocab_labels": [],
                "confidence": None,
                "source": args.provider,
                "vlm": {"model": "", "notes": ""},
            },
        }
        job_path = jobs_dir / f"{object_id}.json"
        write_json(job_path, job)
        jobs[object_id] = {**job, "job_path": str(job_path)}
        labels_template["objects"].append(
            {
                "object_id": object_id,
                "name": obj.get("name", object_id),
                "category": obj.get("category", "unknown"),
                "description": obj.get("description", ""),
                "aliases": [],
                "open_vocab_labels": [],
                "confidence": None,
                "source": args.provider,
                "vlm": {"model": "", "notes": ""},
                "job_path": str(job_path),
            }
        )

    manifest_path = output_dir / "object_labeling_jobs.json"
    template_path = output_dir / "labels_template.json"
    write_json(
        manifest_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "scene_id": manifest.get("scene_id"),
            "provider": args.provider,
            "output_dir": str(output_dir),
            "jobs": jobs,
            "labels_template": str(template_path),
            "skipped": skipped,
            "notes": "Prepared external VLM/open-vocabulary object labeling jobs; no model is executed by this command.",
        },
    )
    write_json(template_path, labels_template)
    manifest.setdefault("artifacts", {})["object_labeling_jobs"] = str(manifest_path)
    manifest.setdefault("artifacts", {})["object_labeling_template"] = str(template_path)
    manifest.setdefault("external_stages", {})["semantic_labeling"] = {
        "status": "object_labeling_jobs_prepared",
        "notes": "Prepared per-object reference images and metadata for external VLM/open-vocabulary semantic labeling.",
        "provider": args.provider,
        "job_count": len(jobs),
        "skipped_objects": skipped,
        "labels_template": str(template_path),
    }
    save_manifest(project_root, manifest)

    print(f"Prepared {len(jobs)} object labeling job(s): {manifest_path}")
    print(f"Labels template: {template_path}")
    if skipped:
        print(f"Skipped: {', '.join(sorted(skipped))}")
    return 0


def cmd_import_object_labels(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    updates = load_object_label_updates(args.labels.resolve())
    labels_path = args.output.resolve() if args.output else project_root / "masks" / "object_labels.json"
    existing_labels = load_object_labels(project_root, labels_path if labels_path.exists() else None)
    objects_dir = project_root / manifest["objects_dir"]
    updated_objects: dict[str, Any] = {}
    missing_objects: list[str] = []

    for object_id, label in updates.items():
        previous = existing_labels.get(object_id, {})
        merged_label = merge_object_label(dict(previous), label, args.overwrite)
        existing_labels[object_id] = merged_label
        object_json = objects_dir / object_id / "object.json"
        if object_json.exists():
            obj = read_json(object_json)
            merge_object_label(obj, merged_label, args.overwrite)
            write_json(object_json, obj)
            updated_objects[object_id] = {
                "object_json": str(object_json),
                "name": obj.get("name"),
                "category": obj.get("category"),
                "description": obj.get("description"),
            }
        else:
            missing_objects.append(object_id)

    write_json(labels_path, existing_labels)
    manifest.setdefault("artifacts", {})["object_labels"] = str(labels_path)
    manifest.setdefault("external_stages", {}).setdefault("semantic_labeling", {})
    manifest["external_stages"]["semantic_labeling"] = {
        "status": "labels_imported",
        "notes": "Object names/categories/descriptions imported from external labels or VLM output.",
        "labels": str(args.labels.resolve()),
        "object_labels": str(labels_path),
        "updated_object_count": len(updated_objects),
        "missing_objects": missing_objects,
    }
    save_manifest(project_root, manifest)

    print(f"Imported labels for {len(updates)} object(s). Updated object records: {len(updated_objects)}")
    print(f"Object labels: {labels_path}")
    if missing_objects:
        print(f"Labels without object records: {', '.join(missing_objects)}")
    return 0


def frame_sort_key(path: Path) -> tuple[int, Any]:
    stem = path.stem
    return (0, int(stem)) if stem.isdigit() else (1, stem)


def list_frame_images(frames_dir: Path) -> list[Path]:
    if not frames_dir.exists():
        raise FileNotFoundError(f"Frames directory not found: {frames_dir}")
    frames = sorted((p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS), key=frame_sort_key)
    if not frames:
        raise FileNotFoundError(f"No image frames found in {frames_dir}")
    return frames


def image_shape(path: Path) -> tuple[int, int]:
    cv2 = import_cv2()
    img = cv2.imread(str(path))
    if img is None:
        raise RuntimeError(f"Failed to read image: {path}")
    h, w = img.shape[:2]
    return w, h


def normalize_bbox(value: Any, width: int, height: int, bbox_format: str = "xyxy") -> tuple[int, int, int, int]:
    if isinstance(value, dict):
        if {"x0", "y0", "x1", "y1"}.issubset(value):
            x0, y0, x1, y1 = value["x0"], value["y0"], value["x1"], value["y1"]
        elif {"x", "y", "w", "h"}.issubset(value):
            x0, y0 = value["x"], value["y"]
            x1, y1 = float(x0) + float(value["w"]), float(y0) + float(value["h"])
        else:
            raise ValueError(f"Unsupported bbox object: {value}")
    elif isinstance(value, (list, tuple)) and len(value) == 4:
        x0, y0, x1, y1 = [float(v) for v in value]
        if bbox_format == "xywh":
            x1, y1 = x0 + x1, y0 + y1
    else:
        raise ValueError(f"Expected bbox as [x0,y0,x1,y1], [x,y,w,h], or dict, got: {value}")

    x0 = max(0, min(width - 1, int(round(float(x0)))))
    y0 = max(0, min(height - 1, int(round(float(y0)))))
    x1 = max(0, min(width, int(round(float(x1)))))
    y1 = max(0, min(height, int(round(float(y1)))))
    if x1 <= x0:
        x1 = min(width, x0 + 1)
    if y1 <= y0:
        y1 = min(height, y0 + 1)
    return x0, y0, x1, y1


def expand_bbox(bbox: tuple[int, int, int, int], amount: int, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return max(0, x0 - amount), max(0, y0 - amount), min(width, x1 + amount), min(height, y1 + amount)


def shift_bbox(bbox: tuple[int, int, int, int], dx: int, dy: int, width: int, height: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    nx0 = max(0, min(width - bw, x0 + dx))
    ny0 = max(0, min(height - bh, y0 + dy))
    return nx0, ny0, nx0 + bw, ny0 + bh


def parse_tracking_prompts(path: Path, default_bbox_format: str, width: int, height: int) -> list[dict[str, Any]]:
    data = read_json(path)
    raw_objects: list[Any]
    if isinstance(data, dict) and isinstance(data.get("objects"), list):
        raw_objects = data["objects"]
    elif isinstance(data, dict):
        raw_objects = []
        for key, value in data.items():
            if not isinstance(value, dict):
                continue
            item = dict(value)
            item.setdefault("id", key)
            raw_objects.append(item)
    elif isinstance(data, list):
        raw_objects = data
    else:
        raise ValueError("Prompt JSON must be a list, an object map, or contain an objects list.")

    objects = []
    for idx, raw in enumerate(raw_objects):
        if not isinstance(raw, dict):
            raise ValueError(f"Prompt object #{idx} is not a JSON object.")
        object_id = slugify(raw.get("object_id") or raw.get("id") or raw.get("name") or f"object_{idx:02d}")
        bbox_value = raw.get("bbox") or raw.get("box")
        if bbox_value is None:
            raise ValueError(f"Prompt object {object_id} has no bbox.")
        bbox_format = raw.get("bbox_format") or raw.get("format") or default_bbox_format
        objects.append(
            {
                "object_id": object_id,
                "name": raw.get("name", object_id.replace("_", " ")),
                "category": raw.get("category", "unknown"),
                "description": raw.get("description", ""),
                "frame_id": frame_stem(raw.get("frame_id", raw.get("frame", "000000"))),
                "bbox": normalize_bbox(bbox_value, width, height, bbox_format),
                "prompt": raw,
            }
        )
    if not objects:
        raise ValueError(f"No objects found in prompt JSON: {path}")
    return objects


def match_bbox(prev_img, curr_img, prev_bbox: tuple[int, int, int, int], template_padding: int, search_margin: int):
    cv2 = import_cv2()
    h, w = curr_img.shape[:2]
    prev_h, prev_w = prev_img.shape[:2]
    template_bbox = expand_bbox(prev_bbox, template_padding, prev_w, prev_h)
    tx0, ty0, tx1, ty1 = template_bbox
    template = cv2.cvtColor(prev_img[ty0:ty1, tx0:tx1], cv2.COLOR_BGR2GRAY)
    if template.shape[0] < 2 or template.shape[1] < 2:
        return prev_bbox, 0.0

    search_bbox = expand_bbox(prev_bbox, search_margin + template_padding, w, h)
    sx0, sy0, sx1, sy1 = search_bbox
    search = cv2.cvtColor(curr_img[sy0:sy1, sx0:sx1], cv2.COLOR_BGR2GRAY)
    if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
        return prev_bbox, 0.0

    result = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
    _min_value, max_value, _min_loc, max_loc = cv2.minMaxLoc(result)
    dx = (sx0 + max_loc[0]) - tx0
    dy = (sy0 + max_loc[1]) - ty0
    return shift_bbox(prev_bbox, int(dx), int(dy), w, h), float(max_value)


def mask_from_bbox(image, bbox: tuple[int, int, int, int], use_grabcut: bool, grabcut_iters: int):
    cv2 = import_cv2()
    np = import_numpy()
    h, w = image.shape[:2]
    x0, y0, x1, y1 = normalize_bbox(bbox, w, h)
    rect_mask = np.zeros((h, w), dtype=np.uint8)
    rect_mask[y0:y1, x0:x1] = 255
    if not use_grabcut or (x1 - x0) < 4 or (y1 - y0) < 4:
        return rect_mask

    grab_mask = np.zeros((h, w), dtype=np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    rect = (x0, y0, x1 - x0, y1 - y0)
    try:
        cv2.grabCut(image, grab_mask, rect, bgd_model, fgd_model, grabcut_iters, cv2.GC_INIT_WITH_RECT)
        out = np.where((grab_mask == cv2.GC_FGD) | (grab_mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        if int(out.sum()) > 0:
            return out
    except Exception:
        pass
    return rect_mask


def load_sam_predictor(checkpoint: Path, model_type: str, device: str):
    try:
        from segment_anything import SamPredictor, sam_model_registry  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("SAM backend requires the segment-anything package.") from exc
    if not checkpoint.exists():
        raise FileNotFoundError(f"SAM checkpoint not found: {checkpoint}")
    if model_type not in sam_model_registry:
        raise ValueError(f"Unsupported SAM model type {model_type!r}. Available: {sorted(sam_model_registry.keys())}")
    sam = sam_model_registry[model_type](checkpoint=str(checkpoint))
    if device == "auto":
        try:
            import torch  # type: ignore

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    sam.to(device=device)
    return SamPredictor(sam), device


def mask_from_sam_bbox(predictor, image_bgr, bbox: tuple[int, int, int, int], multimask: bool):
    np = import_numpy()
    cv2 = import_cv2()
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)
    box = np.asarray(bbox, dtype=np.float32)
    masks, scores, _logits = predictor.predict(box=box, multimask_output=multimask)
    if masks is None or len(masks) == 0:
        return None, None
    best = int(np.argmax(scores)) if scores is not None and len(scores) else 0
    mask = masks[best].astype(np.uint8) * 255
    score = float(scores[best]) if scores is not None and len(scores) else None
    return mask, score


def load_sam_automatic_mask_generator(checkpoint: Path, model_type: str, device: str):
    try:
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("SAM automatic prompt generation requires the segment-anything package.") from exc
    if not checkpoint.exists():
        raise FileNotFoundError(f"SAM checkpoint not found: {checkpoint}")
    if model_type not in sam_model_registry:
        raise ValueError(f"Unsupported SAM model type {model_type!r}. Available: {sorted(sam_model_registry.keys())}")
    sam = sam_model_registry[model_type](checkpoint=str(checkpoint))
    if device == "auto":
        try:
            import torch  # type: ignore

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            device = "cpu"
    sam.to(device=device)
    return SamAutomaticMaskGenerator(sam), device


def bbox_area(bbox: tuple[int, int, int, int]) -> int:
    x0, y0, x1, y1 = bbox
    return max(0, x1 - x0) * max(0, y1 - y0)


def bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    inter = bbox_area((ix0, iy0, ix1, iy1))
    if inter <= 0:
        return 0.0
    union = bbox_area(a) + bbox_area(b) - inter
    return float(inter / union) if union > 0 else 0.0


def color_name_from_region(image_bgr, mask) -> tuple[str, str]:
    np = import_numpy()
    cv2 = import_cv2()
    positive = mask.astype(bool)
    if positive.sum() == 0:
        return "object", "object"
    pixels = image_bgr[positive]
    mean_bgr = pixels.reshape(-1, 3).mean(axis=0).astype(np.uint8).reshape(1, 1, 3)
    mean_hsv = cv2.cvtColor(mean_bgr, cv2.COLOR_BGR2HSV)[0, 0]
    hue, sat, val = int(mean_hsv[0]), int(mean_hsv[1]), int(mean_hsv[2])
    if sat < 35:
        label = "dark" if val < 80 else "light" if val > 180 else "neutral"
    elif hue < 10 or hue >= 170:
        label = "red"
    elif hue < 22:
        label = "orange"
    elif hue < 35:
        label = "yellow"
    elif hue < 85:
        label = "green"
    elif hue < 100:
        label = "cyan"
    elif hue < 130:
        label = "blue"
    elif hue < 160:
        label = "purple"
    else:
        label = "pink"
    return label, f"{label} object"


def filter_prompt_candidates(
    candidates: list[dict[str, Any]],
    width: int,
    height: int,
    min_area_ratio: float,
    max_area_ratio: float,
    min_width: int,
    min_height: int,
    max_objects: int,
    nms_iou: float,
    containment_overlap: float,
    containment_area_ratio: float,
) -> list[dict[str, Any]]:
    image_area = max(1, width * height)
    pre_kept: list[dict[str, Any]] = []
    for candidate in sorted(candidates, key=lambda item: float(item.get("score", 0.0)), reverse=True):
        bbox = normalize_bbox(candidate["bbox"], width, height)
        area = int(candidate.get("mask_area") or bbox_area(bbox))
        area_ratio = float(area / image_area)
        if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
            continue
        if (bbox[2] - bbox[0]) < min_width or (bbox[3] - bbox[1]) < min_height:
            continue
        if any(bbox_iou(bbox, tuple(item["bbox"])) > nms_iou for item in pre_kept):
            continue
        candidate["bbox"] = list(bbox)
        candidate["mask_area"] = area
        candidate["area_ratio"] = area_ratio
        pre_kept.append(candidate)
        candidate_budget = max_objects * 3 if max_objects > 0 else 0
        if candidate_budget > 0 and len(pre_kept) >= candidate_budget:
            break

    kept: list[dict[str, Any]] = []
    for idx, candidate in enumerate(pre_kept):
        bbox = tuple(candidate["bbox"])
        area = max(1, bbox_area(bbox))
        suppress_parent = False
        for other_idx, other in enumerate(pre_kept):
            if idx == other_idx:
                continue
            other_bbox = tuple(other["bbox"])
            other_area = max(1, bbox_area(other_bbox))
            if area < other_area * containment_area_ratio:
                continue
            ix0, iy0 = max(bbox[0], other_bbox[0]), max(bbox[1], other_bbox[1])
            ix1, iy1 = min(bbox[2], other_bbox[2]), min(bbox[3], other_bbox[3])
            inter = bbox_area((ix0, iy0, ix1, iy1))
            if inter / min(area, other_area) >= containment_overlap:
                suppress_parent = True
                break
        if suppress_parent:
            continue
        kept.append(candidate)
        if max_objects > 0 and len(kept) >= max_objects:
            break
    return kept


def opencv_prompt_candidates(image_bgr, args: argparse.Namespace) -> list[dict[str, Any]]:
    np = import_numpy()
    cv2 = import_cv2()
    height, width = image_bgr.shape[:2]
    border = np.concatenate(
        [
            image_bgr[: max(1, height // 20), :, :].reshape(-1, 3),
            image_bgr[-max(1, height // 20) :, :, :].reshape(-1, 3),
            image_bgr[:, : max(1, width // 20), :].reshape(-1, 3),
            image_bgr[:, -max(1, width // 20) :, :].reshape(-1, 3),
        ],
        axis=0,
    )
    background = np.median(border.astype(np.float32), axis=0)
    color_distance = np.linalg.norm(image_bgr.astype(np.float32) - background.reshape(1, 1, 3), axis=2)
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    foreground = ((color_distance >= args.color_distance_threshold) | (saturation >= args.min_saturation)) & (value > 20)
    mask = foreground.astype(np.uint8) * 255
    kernel_size = max(1, int(args.morph_kernel))
    if kernel_size > 1:
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    count, labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    candidates: list[dict[str, Any]] = []
    for label_idx in range(1, count):
        x, y, w, h, area = [int(value) for value in stats[label_idx]]
        component_mask = labels == label_idx
        color_slug, color_name = color_name_from_region(image_bgr, component_mask)
        mean_saturation = float(saturation[component_mask].mean()) if int(area) > 0 else 0.0
        score = float(area) * (1.0 + mean_saturation / 255.0)
        candidates.append(
            {
                "bbox": [x, y, x + w, y + h],
                "mask_area": int(area),
                "score": score,
                "source": "opencv_foreground_components",
                "color_slug": color_slug,
                "name_hint": color_name,
                "mean_saturation": mean_saturation,
            }
        )
    return candidates


def sam_prompt_candidates(image_bgr, args: argparse.Namespace) -> tuple[list[dict[str, Any]], str]:
    np = import_numpy()
    cv2 = import_cv2()
    if args.sam_checkpoint is None:
        raise ValueError("--method sam/auto with SAM requires --sam-checkpoint")
    generator, device = load_sam_automatic_mask_generator(args.sam_checkpoint.resolve(), args.sam_model_type, args.sam_device)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    annotations = generator.generate(image_rgb)
    candidates: list[dict[str, Any]] = []
    for annotation in annotations:
        x, y, w, h = [int(round(float(value))) for value in annotation.get("bbox", [0, 0, 0, 0])]
        segmentation = annotation.get("segmentation")
        if segmentation is not None:
            mask = np.asarray(segmentation, dtype=bool)
            color_slug, color_name = color_name_from_region(image_bgr, mask)
        else:
            mask = None
            color_slug, color_name = "object", "object"
        predicted_iou = float(annotation.get("predicted_iou", 0.0) or 0.0)
        stability = float(annotation.get("stability_score", 0.0) or 0.0)
        area = int(annotation.get("area", 0) or (int(mask.sum()) if mask is not None else w * h))
        score = (predicted_iou + stability + 1.0) * max(1, area)
        candidates.append(
            {
                "bbox": [x, y, x + w, y + h],
                "mask_area": area,
                "score": score,
                "source": "sam_automatic_mask_generator",
                "color_slug": color_slug,
                "name_hint": color_name,
                "predicted_iou": predicted_iou,
                "stability_score": stability,
            }
        )
    return candidates, device


def write_prompt_preview(image_bgr, objects: list[dict[str, Any]], output_path: Path) -> None:
    cv2 = import_cv2()
    canvas = image_bgr.copy()
    palette = [
        (40, 90, 240),
        (240, 130, 40),
        (70, 180, 80),
        (180, 80, 200),
        (40, 190, 210),
        (210, 70, 120),
    ]
    for idx, obj in enumerate(objects):
        x0, y0, x1, y1 = [int(value) for value in obj["bbox"]]
        color = palette[idx % len(palette)]
        cv2.rectangle(canvas, (x0, y0), (x1, y1), color, 2)
        label = str(obj.get("id") or f"object_{idx + 1}")[:32]
        cv2.putText(canvas, label, (x0, max(16, y0 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    ensure_dir(output_path.parent)
    cv2.imwrite(str(output_path), canvas)


def cmd_auto_prompts(args: argparse.Namespace) -> int:
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    frames = list_frame_images(frames_dir)
    if args.frame_id:
        frame_path = find_frame_image(frames_dir, frame_stem(args.frame_id))
        if frame_path is None:
            raise FileNotFoundError(f"Frame {args.frame_id!r} not found in {frames_dir}")
    else:
        frame_index = max(0, min(len(frames) - 1, int(args.frame_index)))
        frame_path = frames[frame_index]
    frame_id = frame_stem(frame_path.stem)
    image = cv2.imread(str(frame_path))
    if image is None:
        raise RuntimeError(f"Failed to read frame: {frame_path}")
    height, width = image.shape[:2]

    method = args.method
    sam_device = None
    if method == "auto":
        method = "sam" if args.sam_checkpoint else "opencv"
    if method == "sam":
        try:
            candidates, sam_device = sam_prompt_candidates(image, args)
        except Exception:
            if args.method == "sam":
                raise
            method = "opencv"
            candidates = opencv_prompt_candidates(image, args)
    else:
        candidates = opencv_prompt_candidates(image, args)

    kept = filter_prompt_candidates(
        candidates,
        width,
        height,
        args.min_area_ratio,
        args.max_area_ratio,
        args.min_width,
        args.min_height,
        args.max_objects,
        args.nms_iou,
        args.containment_overlap,
        args.containment_area_ratio,
    )
    output_path = args.output or (project_root / "masks" / "auto_prompts.json")
    output_path = output_path if output_path.is_absolute() else project_root / output_path
    if output_path.exists() and not args.overwrite:
        raise FileExistsError(f"Prompt file already exists: {output_path}. Pass --overwrite to replace it.")

    objects = []
    used_ids: set[str] = set()
    labels = load_object_labels(project_root)
    for idx, candidate in enumerate(kept, start=1):
        color_slug = slugify(candidate.get("color_slug") or "object", fallback="object")
        base_id = slugify(f"{args.object_prefix}_{color_slug}_{idx:02d}", fallback=f"{args.object_prefix}_{idx:02d}")
        object_id = base_id
        suffix = 2
        while object_id in used_ids:
            object_id = f"{base_id}_{suffix}"
            suffix += 1
        used_ids.add(object_id)
        name = candidate.get("name_hint") or object_id.replace("_", " ")
        prompt = {
            "id": object_id,
            "name": name,
            "category": args.category,
            "description": f"Automatically generated {method} bbox prompt from frame {frame_id}.",
            "frame_id": frame_id,
            "bbox": candidate["bbox"],
            "bbox_format": "xyxy",
            "score": candidate.get("score"),
            "mask_area": candidate.get("mask_area"),
            "area_ratio": candidate.get("area_ratio"),
            "source": candidate.get("source"),
        }
        for key in ["predicted_iou", "stability_score", "mean_saturation"]:
            if key in candidate:
                prompt[key] = candidate[key]
        objects.append(prompt)
        labels[object_id] = {
            "name": name,
            "category": args.category,
            "description": prompt["description"],
        }

    preview_path = args.preview_output or output_path.with_name(f"{output_path.stem}_preview.png")
    preview_path = preview_path if preview_path.is_absolute() else project_root / preview_path
    write_prompt_preview(image, objects, preview_path)

    prompt_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "method": method,
        "frames_dir": str(frames_dir),
        "frame_id": frame_id,
        "source_image": str(frame_path),
        "image_size": {"w": width, "h": height},
        "candidate_count": len(candidates),
        "object_count": len(objects),
        "sam": {
            "checkpoint": str(args.sam_checkpoint.resolve()) if args.sam_checkpoint else None,
            "model_type": args.sam_model_type if args.sam_checkpoint else None,
            "device": sam_device,
        }
        if method == "sam"
        else None,
        "filters": {
            "max_objects": args.max_objects,
            "min_area_ratio": args.min_area_ratio,
            "max_area_ratio": args.max_area_ratio,
            "min_width": args.min_width,
            "min_height": args.min_height,
            "nms_iou": args.nms_iou,
            "containment_overlap": args.containment_overlap,
            "containment_area_ratio": args.containment_area_ratio,
        },
        "preview_image": str(preview_path),
        "objects": objects,
        "notes": (
            "Automatically generated bbox prompts for track-masks. These are object proposals, "
            "not reliable semantic labels; inspect or replace them for production-quality scenes."
        ),
    }
    write_json(output_path, prompt_manifest)
    labels_path = project_root / "masks" / "object_labels.json"
    write_json(labels_path, labels)
    manifest["artifacts"]["auto_tracking_prompts"] = str(output_path)
    manifest["artifacts"]["tracking_prompts"] = str(output_path)
    manifest["artifacts"]["auto_tracking_prompts_preview"] = str(preview_path)
    manifest["artifacts"]["object_labels"] = str(labels_path)
    save_manifest(project_root, manifest)

    print(f"Generated {len(objects)} auto prompt(s) from {frame_path}")
    print(f"Candidates: {len(candidates)}; method={method}")
    print(f"Prompts: {output_path}")
    print(f"Preview: {preview_path}")
    return 0


def cmd_track_masks(args: argparse.Namespace) -> int:
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    frames_dir = frames_dir.resolve()
    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]
    width, height = image_shape(frames[0])
    prompts = parse_tracking_prompts(args.prompts.resolve(), args.bbox_format, width, height)

    frame_ids = [frame_stem(path.stem) for path in frames]
    frame_index = {frame_id: idx for idx, frame_id in enumerate(frame_ids)}
    mask_root = args.output_dir or (project_root / manifest["masks"]["mask_2d_dir"])
    if getattr(args, "clear_output", False) and mask_root.exists():
        shutil.rmtree(mask_root)
    mask_root = ensure_dir(mask_root)
    labels = load_object_labels(project_root)
    mask_backend = args.mask_backend
    sam_predictor = None
    sam_device = None
    if mask_backend in {"sam", "auto"}:
        if args.sam_checkpoint:
            try:
                sam_predictor, sam_device = load_sam_predictor(args.sam_checkpoint.resolve(), args.sam_model_type, args.sam_device)
                mask_backend = "sam"
            except Exception:
                if args.mask_backend == "sam":
                    raise
                mask_backend = "opencv"
        elif args.mask_backend == "sam":
            raise ValueError("--mask-backend sam requires --sam-checkpoint")
        else:
            mask_backend = "opencv"

    tracking_summary: dict[str, Any] = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "method": (
            "opencv_template_tracking_sam_bbox"
            if mask_backend == "sam"
            else "opencv_template_tracking_grabcut"
            if args.grabcut
            else "opencv_template_tracking_bbox"
        ),
        "mask_backend": mask_backend,
        "sam": {
            "checkpoint": str(args.sam_checkpoint.resolve()) if args.sam_checkpoint else None,
            "model_type": args.sam_model_type if args.sam_checkpoint else None,
            "device": sam_device,
            "multimask": bool(args.sam_multimask),
        }
        if mask_backend == "sam"
        else None,
        "frames_dir": str(frames_dir),
        "prompts": str(args.prompts.resolve()),
        "objects": {},
    }

    images_cache: dict[int, Any] = {}

    def load_img(index: int):
        if index not in images_cache:
            img = cv2.imread(str(frames[index]))
            if img is None:
                raise RuntimeError(f"Failed to read image: {frames[index]}")
            images_cache[index] = img
        return images_cache[index]

    for prompt in prompts:
        object_id = prompt["object_id"]
        prompt_frame = prompt["frame_id"]
        prompt_idx = frame_index.get(prompt_frame)
        if prompt_idx is None:
            prompt_idx = 0
        bboxes: dict[int, tuple[int, int, int, int]] = {prompt_idx: prompt["bbox"]}
        scores: dict[int, float] = {prompt_idx: 1.0}

        for idx in range(prompt_idx + 1, len(frames)):
            bbox, score = match_bbox(
                load_img(idx - 1),
                load_img(idx),
                bboxes[idx - 1],
                args.template_padding,
                args.search_margin,
            )
            bboxes[idx] = bbox
            scores[idx] = score

        for idx in range(prompt_idx - 1, -1, -1):
            bbox, score = match_bbox(
                load_img(idx + 1),
                load_img(idx),
                bboxes[idx + 1],
                args.template_padding,
                args.search_margin,
            )
            bboxes[idx] = bbox
            scores[idx] = score

        object_mask_dir = ensure_dir(mask_root / object_id)
        frames_written = []
        for idx, frame_path in enumerate(frames):
            frame_id = frame_ids[idx]
            score = scores.get(idx, 0.0)
            if score < args.min_score and not args.keep_low_score:
                continue
            bbox = bboxes[idx]
            sam_score = None
            if mask_backend == "sam" and sam_predictor is not None:
                mask, sam_score = mask_from_sam_bbox(sam_predictor, load_img(idx), bbox, args.sam_multimask)
                if mask is None:
                    mask = mask_from_bbox(load_img(idx), bbox, args.grabcut, args.grabcut_iters)
            else:
                mask = mask_from_bbox(load_img(idx), bbox, args.grabcut, args.grabcut_iters)
            out_path = object_mask_dir / f"{frame_id}.png"
            cv2.imwrite(str(out_path), mask)
            frames_written.append(
                {
                    "frame_id": frame_id,
                    "image": str(frame_path),
                    "mask": str(out_path),
                    "bbox": list(bbox),
                    "track_score": score,
                    "sam_score": sam_score,
                    "mask_area": int((mask >= 128).sum()),
                }
            )

        labels[object_id] = {
            "name": prompt["name"],
            "category": prompt["category"],
            "description": prompt["description"],
        }
        tracking_summary["objects"][object_id] = {
            "prompt_frame": prompt_frame,
            "resolved_prompt_frame": frame_ids[prompt_idx],
            "prompt_bbox": list(prompt["bbox"]),
            "frames_written": len(frames_written),
            "frames": frames_written,
        }

    labels_path = project_root / "masks" / "object_labels.json"
    write_json(labels_path, labels)
    tracking_manifest = mask_root / "tracking_manifest.json"
    write_json(tracking_manifest, tracking_summary)
    manifest["artifacts"]["object_masks_2d"] = str(mask_root)
    manifest["artifacts"]["object_labels"] = str(labels_path)
    manifest["artifacts"]["mask_tracking_manifest"] = str(tracking_manifest)
    manifest["external_stages"]["segmentation_2d_tracking"] = {
        "status": "generated_prompt_tracking",
        "notes": "Generated frame-level object masks from bbox prompts using OpenCV template tracking and OpenCV/SAM bbox mask generation. Replace this adapter with SAM2/DEVA for production-quality video object tracking.",
        "mask_backend": mask_backend,
    }
    save_manifest(project_root, manifest)

    total_masks = sum(obj["frames_written"] for obj in tracking_summary["objects"].values())
    print(f"Wrote {total_masks} 2D mask(s) for {len(prompts)} object(s) to {mask_root}")
    print(f"Wrote labels: {labels_path}")
    return 0


def read_point_cloud(path: Path):
    np = import_numpy()
    try:
        import open3d as o3d  # type: ignore

        pcd = o3d.io.read_point_cloud(str(path))
        if not pcd.is_empty():
            points = np.asarray(pcd.points, dtype=np.float64)
            colors = np.asarray(pcd.colors, dtype=np.float64) if pcd.has_colors() else None
            return points, colors
    except Exception:
        pass

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        header = []
        for line in f:
            header.append(line.strip())
            if line.strip() == "end_header":
                break
        if "format ascii 1.0" not in header:
            raise RuntimeError(f"Point cloud is not readable by Open3D and is not ASCII PLY: {path}")
        vertex_count = 0
        properties: list[str] = []
        for line in header:
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[-1])
            elif line.startswith("property"):
                properties.append(line.split()[-1])
        rows = []
        for _ in range(vertex_count):
            rows.append(f.readline().strip().split())

    name_to_idx = {name: idx for idx, name in enumerate(properties)}
    points = np.array(
        [
            [float(row[name_to_idx["x"]]), float(row[name_to_idx["y"]]), float(row[name_to_idx["z"]])]
            for row in rows
        ],
        dtype=np.float64,
    )
    colors = None
    if {"red", "green", "blue"}.issubset(name_to_idx):
        colors = np.array(
            [
                [
                    float(row[name_to_idx["red"]]) / 255.0,
                    float(row[name_to_idx["green"]]) / 255.0,
                    float(row[name_to_idx["blue"]]) / 255.0,
                ]
                for row in rows
            ],
            dtype=np.float64,
        )
    return points, colors


def cmd_downsample_point_cloud(args: argparse.Namespace) -> int:
    np = import_numpy()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    source = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    source = resolve_project_cli_path(source, project_root)
    if not source.exists():
        raise FileNotFoundError(f"Point cloud not found: {source}")
    output = args.output
    if output is None:
        stem = f"point_cloud_{int(args.max_points)}" if args.method == "random" else f"point_cloud_voxel_{args.voxel_size:g}"
        output = project_root / "scene" / "reconstruction" / f"{stem}.ply"
    else:
        output = resolve_project_relative_path(output, project_root)

    points, colors = read_point_cloud(source)
    source_count = int(points.shape[0])
    if source_count == 0:
        raise RuntimeError(f"No points found in point cloud: {source}")
    method = args.method
    selected_indices = None

    if method == "random":
        target_count = min(int(args.max_points), source_count)
        if target_count <= 0:
            raise ValueError("--max-points must be positive")
        rng = np.random.default_rng(int(args.seed))
        selected_indices = np.sort(rng.choice(source_count, size=target_count, replace=False))
        out_points = points[selected_indices]
        out_colors = colors[selected_indices] if colors is not None else None
    else:
        try:
            import open3d as o3d  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("--method voxel requires open3d.") from exc
        if args.voxel_size <= 0:
            raise ValueError("--voxel-size must be positive")
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        if colors is not None:
            pcd.colors = o3d.utility.Vector3dVector(colors)
        down = pcd.voxel_down_sample(float(args.voxel_size))
        out_points = np.asarray(down.points, dtype=np.float64)
        out_colors = np.asarray(down.colors, dtype=np.float64) if down.has_colors() else None
        if args.max_points and out_points.shape[0] > args.max_points:
            rng = np.random.default_rng(int(args.seed))
            selected_indices = np.sort(rng.choice(out_points.shape[0], size=int(args.max_points), replace=False))
            out_points = out_points[selected_indices]
            out_colors = out_colors[selected_indices] if out_colors is not None else None

    write_point_cloud_ascii_ply(output, out_points, out_colors)
    downsample_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "stage": "point_cloud_downsample",
        "method": method,
        "source_point_cloud": str(source),
        "output_point_cloud": str(output),
        "source_point_count": source_count,
        "output_point_count": int(out_points.shape[0]),
        "max_points": int(args.max_points) if args.max_points else None,
        "voxel_size": float(args.voxel_size) if method == "voxel" else None,
        "seed": int(args.seed),
        "registered_as_point_cloud": bool(args.register_as_point_cloud),
        "notes": "Lightweight point cloud for faster 3DGS smoke training and 2D-to-3D mask fusion; keep the original dense reconstruction for final quality runs.",
    }
    manifest_path = output.with_suffix(".json")
    write_json(manifest_path, downsample_manifest)
    manifest.setdefault("artifacts", {})["downsampled_point_cloud"] = str(output)
    manifest["artifacts"]["downsampled_point_cloud_manifest"] = str(manifest_path)
    if args.register_as_point_cloud:
        dst = project_root / manifest["scene"]["point_cloud"]
        if output != dst.resolve():
            copy_or_link(output, dst, "copy")
        manifest["artifacts"]["point_cloud"] = str(dst)
    save_manifest(project_root, manifest)
    print(f"Downsampled point cloud: {source_count} -> {out_points.shape[0]} point(s)")
    print(f"Output: {output}")
    print(f"Manifest: {manifest_path}")
    if args.register_as_point_cloud:
        print(f"Registered as scene point cloud: {project_root / manifest['scene']['point_cloud']}")
    return 0


def load_camera_info(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if "intrinsic" not in data or "extrinsic" not in data:
        raise ValueError("camera_info.json must contain intrinsic and extrinsic fields.")
    return data


def intrinsic_for_frame(camera_info: dict[str, Any], frame_id: str) -> dict[str, float]:
    frame_camera_ids = camera_info.get("frame_camera_ids") or {}
    intrinsics = camera_info.get("intrinsics") or {}
    camera_id = frame_camera_ids.get(frame_id)
    if camera_id is None and frame_id.isdigit():
        camera_id = frame_camera_ids.get(str(int(frame_id)))
    if camera_id is not None and str(camera_id) in intrinsics:
        return intrinsics[str(camera_id)]
    return camera_info["intrinsic"]


def resolve_extrinsic(extrinsics: dict[str, Any], frame_id: str):
    candidates = [frame_id, str(int(frame_id)) if frame_id.isdigit() else frame_id, frame_stem(frame_id)]
    for key in candidates:
        if key in extrinsics:
            return extrinsics[key]
    return None


def world_to_camera_matrix(matrix: Any, extrinsic_type: str):
    np = import_numpy()
    mat = np.asarray(matrix, dtype=np.float64)
    if mat.shape != (4, 4):
        raise ValueError(f"Expected 4x4 extrinsic matrix, got {mat.shape}")
    if extrinsic_type == "world_to_camera":
        return mat
    if extrinsic_type == "camera_to_world":
        return np.linalg.inv(mat)
    raise ValueError("--extrinsic-type must be world_to_camera or camera_to_world")


def project_points(points, intrinsic: dict[str, float], world_to_camera):
    np = import_numpy()
    ones = np.ones((points.shape[0], 1), dtype=np.float64)
    homo = np.concatenate([points, ones], axis=1)
    cam = (world_to_camera @ homo.T).T[:, :3]
    z = cam[:, 2]
    valid = z > 1e-6
    u = np.full(points.shape[0], -1, dtype=np.int64)
    v = np.full(points.shape[0], -1, dtype=np.int64)
    u_float = intrinsic["fx"] * (cam[:, 0] / np.maximum(z, 1e-6)) + intrinsic["cx"]
    v_float = intrinsic["fy"] * (cam[:, 1] / np.maximum(z, 1e-6)) + intrinsic["cy"]
    width = int(intrinsic["w"])
    height = int(intrinsic["h"])
    inside = valid & (u_float >= 0) & (u_float < width) & (v_float >= 0) & (v_float < height)
    u[inside] = np.floor(u_float[inside]).astype(np.int64)
    v[inside] = np.floor(v_float[inside]).astype(np.int64)
    return inside, u, v, z


def visibility_mask_from_projection(
    inside,
    u,
    v,
    z,
    width: int,
    height: int,
    depth_tolerance: float,
    relative_depth_tolerance: float,
):
    np = import_numpy()
    visible = np.zeros_like(inside, dtype=bool)
    inside_idx = np.flatnonzero(inside)
    if inside_idx.size == 0:
        return visible, np.full((height, width), np.inf, dtype=np.float64)

    pixel = v[inside_idx] * width + u[inside_idx]
    zbuf_flat = np.full(width * height, np.inf, dtype=np.float64)
    np.minimum.at(zbuf_flat, pixel, z[inside_idx])
    nearest = zbuf_flat[pixel]
    tolerance = np.maximum(float(depth_tolerance), nearest * float(relative_depth_tolerance))
    visible[inside_idx] = z[inside_idx] <= nearest + tolerance
    return visible, zbuf_flat.reshape(height, width)


def point_colors_to_u8(colors, count: int):
    np = import_numpy()
    if colors is None:
        return np.full((count, 3), 255, dtype=np.uint8)
    colors_np = np.asarray(colors)
    if colors_np.size == 0:
        return np.full((count, 3), 255, dtype=np.uint8)
    if colors_np.max() <= 1.0:
        colors_np = colors_np * 255.0
    return np.clip(np.rint(colors_np), 0, 255).astype(np.uint8)


def draw_projected_points(image_bgr, u, v, indices, colors_rgb, radius: int, alpha: float):
    cv2 = import_cv2()
    overlay = image_bgr.copy()
    height, width = image_bgr.shape[:2]
    for index in indices:
        x = int(u[index])
        y = int(v[index])
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        rgb = colors_rgb[index]
        color_bgr = (int(rgb[2]), int(rgb[1]), int(rgb[0]))
        cv2.circle(overlay, (x, y), max(1, int(radius)), color_bgr, thickness=-1, lineType=cv2.LINE_AA)
    if alpha >= 1.0:
        return overlay
    return cv2.addWeighted(overlay, float(alpha), image_bgr, 1.0 - float(alpha), 0.0)


def cmd_render_reconstruction_preview(args: argparse.Namespace) -> int:
    np = import_numpy()
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "reconstruction_preview"))

    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]
    camera_info = load_camera_info(camera_info_path)
    points, colors = read_point_cloud(point_cloud_path)
    colors_u8 = point_colors_to_u8(colors, int(points.shape[0]))
    if points.shape[0] == 0:
        raise RuntimeError(f"No points found in point cloud: {point_cloud_path}")

    frame_reports = []
    for frame_path in frames:
        frame_id = frame_id_for_path(frame_path)
        image = cv2.imread(str(frame_path))
        if image is None:
            raise RuntimeError(f"Failed to read frame image: {frame_path}")
        intrinsic = intrinsic_for_frame(camera_info, frame_id)
        extrinsic = resolve_extrinsic(camera_info["extrinsic"], frame_id)
        if extrinsic is None:
            frame_reports.append({"frame_id": frame_id, "image": str(frame_path), "skipped": True, "reason": "missing_extrinsic"})
            continue
        w2c = world_to_camera_matrix(extrinsic, camera_info.get("extrinsic_type") or args.extrinsic_type)
        inside, u, v, z = project_points(points, intrinsic, w2c)
        if args.occlusion_filter:
            visible, _zbuf = visibility_mask_from_projection(
                inside,
                u,
                v,
                z,
                int(intrinsic["w"]),
                int(intrinsic["h"]),
                args.depth_tolerance,
                args.relative_depth_tolerance,
            )
            draw_mask = visible
        else:
            visible = inside
            draw_mask = inside

        draw_indices = np.flatnonzero(draw_mask)
        if args.max_points_per_frame and draw_indices.size > args.max_points_per_frame:
            rng = np.random.default_rng(args.seed)
            draw_indices = np.sort(rng.choice(draw_indices, size=int(args.max_points_per_frame), replace=False))
        overlay = draw_projected_points(image, u, v, draw_indices, colors_u8, args.point_radius, args.alpha)
        frame_dir = ensure_dir(output_dir / frame_id)
        overlay_path = frame_dir / "projection_overlay.png"
        cv2.imwrite(str(overlay_path), overlay)

        projected_pixel_count = int(len(set((int(v[idx]) * int(intrinsic["w"]) + int(u[idx])) for idx in np.flatnonzero(inside))))
        visible_pixel_count = int(len(set((int(v[idx]) * int(intrinsic["w"]) + int(u[idx])) for idx in np.flatnonzero(visible))))
        image_pixels = max(1, int(intrinsic["w"]) * int(intrinsic["h"]))
        z_inside = z[inside]
        frame_reports.append(
            {
                "frame_id": frame_id,
                "image": str(frame_path),
                "overlay": str(overlay_path),
                "skipped": False,
                "point_count": int(points.shape[0]),
                "projected_points": int(inside.sum()),
                "visible_points": int(visible.sum()),
                "drawn_points": int(draw_indices.size),
                "projected_pixel_count": projected_pixel_count,
                "visible_pixel_count": visible_pixel_count,
                "projected_point_ratio": float(inside.sum() / points.shape[0]),
                "visible_point_ratio": float(visible.sum() / points.shape[0]),
                "projected_pixel_ratio": float(projected_pixel_count / image_pixels),
                "visible_pixel_ratio": float(visible_pixel_count / image_pixels),
                "z_min": float(z_inside.min()) if z_inside.size else None,
                "z_max": float(z_inside.max()) if z_inside.size else None,
                "z_mean": float(z_inside.mean()) if z_inside.size else None,
            }
        )

    valid_reports = [item for item in frame_reports if not item.get("skipped")]
    summary = {
        "frame_count": len(frame_reports),
        "valid_frame_count": len(valid_reports),
        "mean_projected_point_ratio": float(np.mean([item["projected_point_ratio"] for item in valid_reports])) if valid_reports else None,
        "mean_visible_point_ratio": float(np.mean([item["visible_point_ratio"] for item in valid_reports])) if valid_reports else None,
        "mean_projected_pixel_ratio": float(np.mean([item["projected_pixel_ratio"] for item in valid_reports])) if valid_reports else None,
        "mean_visible_pixel_ratio": float(np.mean([item["visible_pixel_ratio"] for item in valid_reports])) if valid_reports else None,
    }
    preview_manifest_path = output_dir / "reconstruction_preview.json"
    preview_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "frames_dir": str(frames_dir),
        "camera_info": str(camera_info_path),
        "point_cloud": str(point_cloud_path),
        "output_dir": str(output_dir),
        "occlusion_filter": bool(args.occlusion_filter),
        "summary": summary,
        "frames": frame_reports,
        "notes": "Point cloud projection overlays for checking camera/point-cloud alignment before 2D-to-3D mask fusion.",
    }
    write_json(preview_manifest_path, preview_manifest)
    manifest["artifacts"]["reconstruction_preview"] = str(preview_manifest_path)
    save_manifest(project_root, manifest)
    print(f"Rendered {len(valid_reports)} reconstruction preview frame(s) to {output_dir}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Preview manifest: {preview_manifest_path}")
    return 0


def bbox_for_points(points):
    np = import_numpy()
    if points.size == 0:
        return None
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    center = (mins + maxs) / 2.0
    size = maxs - mins
    return {
        "min": mins.tolist(),
        "max": maxs.tolist(),
        "center": center.tolist(),
        "size": size.tolist(),
    }


def axis_index(axis: str) -> int:
    normalized = str(axis).lower()
    if normalized not in {"x", "y", "z"}:
        raise ValueError("axis must be x, y, or z")
    return {"x": 0, "y": 1, "z": 2}[normalized]


def structure_indices_by_axis(points, axis: int, side: str, thickness: float | None, quantile: float, exclude_indices: set[int] | None = None):
    np = import_numpy()
    values = points[:, axis]
    if side == "min":
        boundary = float(np.quantile(values, float(quantile)))
        limit = boundary + (float(thickness) if thickness is not None else 0.0)
        mask = values <= limit
    elif side == "max":
        boundary = float(np.quantile(values, 1.0 - float(quantile)))
        limit = boundary - (float(thickness) if thickness is not None else 0.0)
        mask = values >= limit
    else:
        raise ValueError("side must be min or max")
    if exclude_indices:
        exclude = np.fromiter(exclude_indices, dtype=np.int64)
        if exclude.size:
            mask[exclude] = False
    return np.flatnonzero(mask), boundary, limit


def background_structure_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    up = axis_index(args.up_axis)
    horizontal = [idx for idx in range(3) if idx != up]
    specs: list[dict[str, Any]] = []
    if args.include_floor:
        specs.append({"object_id": args.floor_id, "name": "floor", "category": "floor", "axis": up, "side": "min"})
    if args.include_ceiling:
        specs.append({"object_id": args.ceiling_id, "name": "ceiling", "category": "ceiling", "axis": up, "side": "max"})
    if args.include_walls:
        axis_names = ["x", "y", "z"]
        for axis in horizontal:
            specs.append(
                {
                    "object_id": f"wall_{axis_names[axis]}_min",
                    "name": f"{axis_names[axis]} min wall",
                    "category": "wall",
                    "axis": axis,
                    "side": "min",
                }
            )
            specs.append(
                {
                    "object_id": f"wall_{axis_names[axis]}_max",
                    "name": f"{axis_names[axis]} max wall",
                    "category": "wall",
                    "axis": axis,
                    "side": "max",
                }
            )
    return specs


def cmd_infer_background_structure_masks(args: argparse.Namespace) -> int:
    np = import_numpy()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    point_cloud_path = resolve_project_cli_path(point_cloud_path, project_root)
    points, _colors = read_point_cloud(point_cloud_path)
    if points.shape[0] == 0:
        raise RuntimeError(f"No points found in point cloud: {point_cloud_path}")
    objects_dir = ensure_dir(project_root / manifest["objects_dir"])
    structure_root = ensure_dir(project_root / manifest["simulator_assets_dir"] / "background_structures")
    occupied: set[int] = set()
    labels = load_object_labels(project_root)
    structures: dict[str, Any] = {}
    skipped: dict[str, str] = {}

    for spec in background_structure_specs(args):
        object_id = slugify(spec["object_id"])
        indices, boundary, limit = structure_indices_by_axis(
            points,
            int(spec["axis"]),
            str(spec["side"]),
            args.thickness,
            args.quantile,
            occupied if args.exclusive else None,
        )
        if indices.size < int(args.min_points):
            skipped[object_id] = f"{indices.size} point(s), below --min-points {args.min_points}"
            continue
        if args.exclusive:
            occupied.update(int(value) for value in indices.tolist())
        bbox = bbox_for_points(points[indices])
        mask_info = write_point_indices(
            project_root,
            manifest,
            object_id,
            indices,
            {
                "source": "background_structure_axis_boundary",
                "axis": int(spec["axis"]),
                "side": spec["side"],
                "boundary": boundary,
                "limit": limit,
                "quantile": float(args.quantile),
                "thickness": args.thickness,
            },
        )
        label = labels.get(object_id, {})
        object_info = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "asset_role": "background_structure",
            "name": label.get("name", spec["name"]),
            "category": label.get("category", spec["category"]),
            "description": label.get("description", f"Inferred {spec['category']} background structure from point-cloud boundary."),
            "point_count": int(indices.size),
            "bbox_3d": bbox,
            "mask_3d": mask_info,
            "frame_scores": {},
            "background_structure": {
                "method": "axis_boundary",
                "axis": int(spec["axis"]),
                "side": spec["side"],
                "boundary": boundary,
                "limit": limit,
                "quantile": float(args.quantile),
                "thickness": args.thickness,
                "exclusive": bool(args.exclusive),
                "source_point_cloud": str(point_cloud_path),
            },
            "notes": "Background structures are semantic scene components; they are not expected to have object crops or per-object generated meshes.",
        }
        object_dir = ensure_dir(objects_dir / object_id)
        write_json(object_dir / "object.json", object_info)
        write_json(object_dir / "frame_scores.json", {})
        structures[object_id] = object_info

    structure_manifest_path = structure_root / "background_structures.json"
    write_json(
        structure_manifest_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "point_cloud": str(point_cloud_path),
            "up_axis": args.up_axis,
            "quantile": float(args.quantile),
            "thickness": args.thickness,
            "exclusive": bool(args.exclusive),
            "structures": structures,
            "skipped": skipped,
            "notes": "Heuristic floor/ceiling/wall masks from point-cloud boundaries. Replace with layout/semantic segmentation for production.",
        },
    )
    manifest.setdefault("artifacts", {})["background_structures"] = str(structure_manifest_path)
    manifest.setdefault("external_stages", {})["background_structure_segmentation"] = {
        "status": "heuristic_background_masks_inferred",
        "notes": "Axis-boundary floor/ceiling/wall masks inferred from the scene point cloud; this is a protocol baseline, not production layout segmentation.",
        "structure_count": len(structures),
        "skipped": skipped,
    }
    save_manifest(project_root, manifest)

    print(f"Inferred {len(structures)} background structure mask(s): {structure_manifest_path}")
    if skipped:
        print(f"Skipped: {', '.join(f'{key} ({value})' for key, value in skipped.items())}")
    return 0


SCENE_STRUCTURE_LABELS = [
    {
        "category": "floor",
        "asset_role": "background_structure",
        "description": "Walkable or support floor plane.",
    },
    {
        "category": "ceiling",
        "asset_role": "background_structure",
        "description": "Ceiling or upper room boundary.",
    },
    {
        "category": "wall",
        "asset_role": "background_structure",
        "description": "Wall or vertical room boundary.",
    },
    {
        "category": "door",
        "asset_role": "background_structure",
        "description": "Door, doorway, or fixed opening.",
    },
    {
        "category": "window",
        "asset_role": "background_structure",
        "description": "Window or fixed transparent opening.",
    },
    {
        "category": "cabinet",
        "asset_role": "background_structure",
        "description": "Built-in cabinet or fixed storage.",
    },
    {
        "category": "counter",
        "asset_role": "background_structure",
        "description": "Countertop or fixed work surface.",
    },
    {
        "category": "shelf",
        "asset_role": "background_structure",
        "description": "Fixed shelf or wall-mounted storage.",
    },
    {
        "category": "fixed_furniture",
        "asset_role": "background_structure",
        "description": "Large fixed or semi-fixed scene furniture.",
    },
    {
        "category": "other_structure",
        "asset_role": "background_structure",
        "description": "Other non-movable scene structure.",
    },
]


def cmd_prepare_scene_structure_jobs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    point_cloud_path = resolve_project_cli_path(point_cloud_path, project_root)
    if not point_cloud_path.exists():
        raise FileNotFoundError(f"Point cloud not found: {point_cloud_path}")
    camera_info_path = resolve_project_path(manifest["scene"]["camera_info"], project_root)
    frames_dir = resolve_project_path(manifest["scene"]["frames_dir"], project_root)
    frames = sorted((p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS), key=frame_sort_key) if frames_dir.exists() else []
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]

    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "scene_structure_jobs"))
    jobs_dir = ensure_dir(output_dir / "jobs")
    expected_mask_manifest = output_dir / "scene_structure_masks_template.json"
    frame_records = [
        {
            "frame_id": frame_stem(frame.stem),
            "image": str(frame),
            "index": index,
        }
        for index, frame in enumerate(frames)
    ]
    artifact_candidates = {
        "semantic_splats_ply": manifest.get("artifacts", {}).get("semantic_splats_ply"),
        "semantic_splats_manifest": manifest.get("artifacts", {}).get("semantic_splats_manifest"),
        "object_mask_clouds": manifest.get("artifacts", {}).get("object_mask_clouds"),
        "svpp_scene": manifest.get("artifacts", {}).get("svpp_scene"),
        "svpp_metadata": manifest.get("artifacts", {}).get("svpp_metadata"),
        "background_structures": manifest.get("artifacts", {}).get("background_structures"),
    }
    resolved_artifacts = {
        key: str(resolve_existing_path(str(value), project_root)) if value and resolve_existing_path(str(value), project_root) else value
        for key, value in artifact_candidates.items()
    }
    job = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "provider": args.provider,
        "point_cloud": str(point_cloud_path),
        "camera_info": str(camera_info_path) if camera_info_path.exists() else None,
        "frames_dir": str(frames_dir) if frames_dir.exists() else None,
        "frame_count": len(frame_records),
        "frames": frame_records,
        "artifacts": resolved_artifacts,
        "recommended_labels": SCENE_STRUCTURE_LABELS,
        "expected_output": {
            "manifest": str(expected_mask_manifest),
            "structures_schema": {
                "object_id": "wall_0",
                "name": "left wall",
                "category": "wall",
                "asset_role": "background_structure",
                "point_indices": [0, 1, 2],
                "point_indices_json": "optional/path/to/indices.json",
                "point_indices_npy": "optional/path/to/indices.npy",
                "confidence": 0.0,
                "source": args.provider,
                "notes": "point_indices must index the job point_cloud vertex order.",
            },
        },
        "notes": (
            "Prepared for external scene structure/layout segmentation such as SpatialLM/PQ3D adapters, "
            "open-vocabulary 3D segmentation, or room-layout parsers. Run the external tool, then import "
            "its point-index masks with import-scene-structure-masks. Frames may be empty for point-cloud-only tools."
        ),
    }
    job_path = output_dir / "scene_structure_job.json"
    write_json(job_path, job)
    per_provider_job_path = jobs_dir / f"{slugify(args.provider, 'external')}.json"
    write_json(per_provider_job_path, job)

    template = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "provider": args.provider,
        "point_cloud": str(point_cloud_path),
        "structures": [
            {
                "object_id": "floor",
                "name": "floor",
                "category": "floor",
                "asset_role": "background_structure",
                "point_indices": [],
                "confidence": None,
                "source": args.provider,
            }
        ],
        "notes": "Fill structures with point-index masks, then run import-scene-structure-masks --source-manifest <this file>.",
    }
    write_json(expected_mask_manifest, template)

    command = None
    if args.command_template:
        values = {
            "job_path": str(job_path),
            "project_root": str(project_root),
            "point_cloud": str(point_cloud_path),
            "camera_info": str(camera_info_path) if camera_info_path.exists() else "",
            "frames_dir": str(frames_dir) if frames_dir.exists() else "",
            "provider": args.provider,
            "output_manifest": str(expected_mask_manifest),
        }
        command = args.command_template.format(**values)
    script_path = output_dir / "run_scene_structure_segmentation.sh"
    script_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if command:
        script_lines.append(command)
    else:
        script_lines.append(f'echo "Fill in external {args.provider} scene-structure command for job: {job_path}"')
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    script_path.chmod(0o755)

    manifest.setdefault("artifacts", {})["scene_structure_job"] = str(job_path)
    manifest.setdefault("artifacts", {})["scene_structure_template"] = str(expected_mask_manifest)
    manifest.setdefault("external_stages", {})["background_structure_segmentation"] = {
        "status": "external_scene_structure_job_prepared",
        "notes": "Prepared external scene structure/layout segmentation job; import point-index masks before semantic export/simulator packaging.",
        "provider": args.provider,
        "job": str(job_path),
        "script": str(script_path),
        "point_cloud": str(point_cloud_path),
        "frame_count": len(frame_records),
    }
    save_manifest(project_root, manifest)

    print(f"Prepared scene structure segmentation job: {job_path}")
    print(f"Template: {expected_mask_manifest}")
    print(f"Script: {script_path}")
    return 0


def scene_structure_entries(data: Any) -> list[dict[str, Any]]:
    raw_entries: list[Any]
    if isinstance(data, dict) and isinstance(data.get("structures"), list):
        raw_entries = data["structures"]
    elif isinstance(data, dict) and isinstance(data.get("objects"), list):
        raw_entries = data["objects"]
    elif isinstance(data, dict):
        raw_entries = []
        for key, value in data.items():
            if key in {"schema_version", "project_root", "scene_id", "provider", "point_cloud", "notes"}:
                continue
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("object_id", key)
                raw_entries.append(item)
    elif isinstance(data, list):
        raw_entries = data
    else:
        raise ValueError("Scene structure manifest must be a list, map, or object with structures/objects.")

    entries: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            raise ValueError(f"Scene structure entry #{index} is not a JSON object.")
        object_id = slugify(raw.get("object_id") or raw.get("id") or raw.get("name") or f"structure_{index:02d}")
        item = dict(raw)
        item["object_id"] = object_id
        entries.append(item)
    return entries


def resolve_scene_structure_sidecar_path(path_value: Any, project_root: Path, source_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([project_root / path, source_root / path])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    if path.is_absolute():
        return path.resolve()
    return (source_root / path).resolve()


def load_scene_structure_indices(entry: dict[str, Any], project_root: Path, source_root: Path) -> list[int]:
    inline = entry.get("point_indices")
    if inline is None:
        inline = entry.get("indices")
    if inline is not None:
        if not isinstance(inline, list):
            raise ValueError(f"point_indices for {entry.get('object_id')} must be a list.")
        return [int(value) for value in inline]
    for key in ("point_indices_json", "indices_json", "point_indices_npy", "indices_npy"):
        path = resolve_scene_structure_sidecar_path(entry.get(key), project_root, source_root)
        if path and path.exists():
            return load_point_index_mask(path)
    raise ValueError(f"Scene structure {entry.get('object_id')} has no point_indices or point_indices_json/npy.")


def write_mask_cloud_for_indices(
    output_dir: Path,
    object_id: str,
    point_cloud_path: Path,
    points,
    colors,
    indices: list[int],
    source_indices: str,
) -> dict[str, Any]:
    np = import_numpy()
    if colors is None:
        colors_u8 = np.full((points.shape[0], 3), 180, dtype=np.uint8)
    else:
        colors_u8 = np.clip(np.rint(colors * 255.0), 0, 255).astype(np.uint8)
    object_points = []
    for index in indices:
        if not (0 <= index < points.shape[0]):
            continue
        point = points[index]
        color = colors_u8[index]
        object_points.append(
            (
                float(point[0]),
                float(point[1]),
                float(point[2]),
                int(color[0]),
                int(color[1]),
                int(color[2]),
            )
        )
    out_ply = output_dir / f"{object_id}.ply"
    write_ascii_ply(out_ply, object_points)
    return {
        "path": str(out_ply),
        "point_count": len(object_points),
        "source_point_cloud": str(point_cloud_path),
        "source_indices": source_indices,
    }


def cmd_import_scene_structure_masks(args: argparse.Namespace) -> int:
    np = import_numpy()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    source_manifest_path = resolve_project_cli_path(args.source_manifest, project_root)
    data = read_json(source_manifest_path)
    entries = scene_structure_entries(data)
    source_root = source_manifest_path.parent
    if args.point_cloud:
        point_cloud_path = resolve_project_cli_path(args.point_cloud, project_root)
    elif isinstance(data, dict) and data.get("point_cloud"):
        point_cloud_path = resolve_scene_structure_sidecar_path(data.get("point_cloud"), project_root, source_root)
    else:
        point_cloud_path = resolve_project_path(manifest["scene"]["point_cloud"], project_root)
    points, colors = read_point_cloud(point_cloud_path)
    if points.shape[0] == 0:
        raise RuntimeError(f"No points found in point cloud: {point_cloud_path}")

    objects_dir = ensure_dir(project_root / manifest["objects_dir"])
    structure_root = ensure_dir(project_root / manifest["simulator_assets_dir"] / "background_structures")
    cloud_dir = ensure_dir(args.cloud_output_dir or (project_root / manifest["simulator_assets_dir"] / "object_masks_3d"))
    labels_path = resolve_project_cli_path(args.object_labels, project_root) if args.object_labels else (project_root / "masks" / "object_labels.json")
    labels = load_object_labels(project_root, labels_path)
    imported: dict[str, Any] = {}
    skipped: dict[str, str] = {}

    for entry in entries:
        object_id = slugify(entry.get("object_id"), fallback="structure")
        indices = [int(index) for index in load_scene_structure_indices(entry, project_root, source_root)]
        invalid_count = sum(1 for index in indices if not (0 <= index < points.shape[0]))
        valid_indices = sorted({index for index in indices if 0 <= index < points.shape[0]})
        duplicate_count = max(0, len(indices) - invalid_count - len(valid_indices))
        if len(valid_indices) < int(args.min_points):
            if args.skip_small:
                skipped[object_id] = f"{len(valid_indices)} valid point(s), below --min-points {args.min_points}"
                continue
            raise ValueError(f"Scene structure {object_id} has only {len(valid_indices)} valid point(s).")

        bbox = entry.get("bbox_3d") if isinstance(entry.get("bbox_3d"), dict) else bbox_for_points(points[np.asarray(valid_indices, dtype=np.int64)])
        mask_info = write_point_indices(
            project_root,
            manifest,
            object_id,
            valid_indices,
            {
                "source": entry.get("source", args.provider),
                "source_manifest": str(source_manifest_path),
                "source_point_cloud": str(point_cloud_path),
                "invalid_index_count": invalid_count,
                "duplicate_index_count": duplicate_count,
            },
        )
        mask_cloud = write_mask_cloud_for_indices(
            cloud_dir,
            object_id,
            point_cloud_path,
            points,
            colors,
            valid_indices,
            mask_info["point_indices_json"],
        )
        label = labels.get(object_id, {})
        category = entry.get("category") or entry.get("class") or entry.get("class_name") or label.get("category") or "other_structure"
        name = entry.get("name") or label.get("name") or object_id.replace("-", " ")
        description = entry.get("description") or label.get("description") or f"Imported {category} scene structure."
        asset_role = "background_structure"
        object_info = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "asset_role": asset_role,
            "name": name,
            "category": category,
            "description": description,
            "point_count": int(len(valid_indices)),
            "bbox_3d": bbox,
            "mask_3d": mask_info,
            "mask_3d_cloud": mask_cloud,
            "frame_scores": {},
            "background_structure": {
                "method": "external_scene_structure_mask",
                "provider": args.provider,
                "source": entry.get("source", args.provider),
                "source_manifest": str(source_manifest_path),
                "source_point_cloud": str(point_cloud_path),
                "confidence": entry.get("confidence"),
                "invalid_index_count": invalid_count,
                "duplicate_index_count": duplicate_count,
                "notes": entry.get("notes"),
            },
            "notes": "Imported scene structure mask. It participates in semantic splats, SVPP metadata, and simulator export; it is skipped by object mesh generation.",
        }
        object_dir = ensure_dir(objects_dir / object_id)
        write_json(object_dir / "object.json", object_info)
        write_json(object_dir / "frame_scores.json", {})
        labels[object_id] = merge_object_label(
            labels.get(object_id, {}),
            {
                "object_id": object_id,
                "name": name,
                "category": category,
                "description": description,
                "confidence": entry.get("confidence"),
                "source": entry.get("source", args.provider),
            },
            True,
        )
        imported[object_id] = object_info

    write_json(labels_path, labels)
    structure_manifest_path = structure_root / "background_structures.json"
    existing_structures: dict[str, Any] = {}
    if structure_manifest_path.exists() and not args.replace_manifest:
        existing = read_json(structure_manifest_path)
        if isinstance(existing, dict) and isinstance(existing.get("structures"), dict):
            existing_structures = dict(existing["structures"])
    existing_structures.update(imported)
    write_json(
        structure_manifest_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "point_cloud": str(point_cloud_path),
            "provider": args.provider,
            "source_manifest": str(source_manifest_path),
            "structures": existing_structures,
            "imported": sorted(imported),
            "skipped": skipped,
            "notes": "Scene structures imported from external point-index masks.",
        },
    )
    object_cloud_manifest_path = cloud_dir / "object_mask_clouds.json"
    if object_cloud_manifest_path.exists():
        cloud_manifest = read_json(object_cloud_manifest_path)
        if not isinstance(cloud_manifest, dict):
            cloud_manifest = {}
    else:
        cloud_manifest = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "point_cloud": str(point_cloud_path),
            "output_dir": str(cloud_dir),
            "objects": {},
        }
    cloud_manifest.setdefault("schema_version", DEFAULT_SCHEMA_VERSION)
    cloud_manifest.setdefault("point_cloud", str(point_cloud_path))
    cloud_manifest.setdefault("output_dir", str(cloud_dir))
    cloud_manifest.setdefault("objects", {})
    for object_id, obj in imported.items():
        cloud_manifest["objects"][object_id] = {
            "object_id": object_id,
            "name": obj.get("name", object_id),
            "category": obj.get("category", "unknown"),
            **(obj.get("mask_3d_cloud") or {}),
        }
    write_json(object_cloud_manifest_path, cloud_manifest)

    manifest.setdefault("artifacts", {})["object_labels"] = str(labels_path)
    manifest.setdefault("artifacts", {})["background_structures"] = str(structure_manifest_path)
    manifest.setdefault("artifacts", {})["object_mask_clouds"] = str(object_cloud_manifest_path)
    manifest.setdefault("external_stages", {})["background_structure_segmentation"] = {
        "status": "external_scene_structure_masks_imported",
        "notes": "Imported external scene structure/layout point-index masks into Video2Mesh object records.",
        "provider": args.provider,
        "source_manifest": str(source_manifest_path),
        "structure_count": len(imported),
        "skipped": skipped,
    }
    save_manifest(project_root, manifest)

    print(f"Imported {len(imported)} scene structure mask(s): {structure_manifest_path}")
    print(f"Object mask clouds: {object_cloud_manifest_path}")
    if skipped:
        print(f"Skipped: {', '.join(f'{key} ({value})' for key, value in skipped.items())}")
    return 0


def read_ascii_ply_table(path: Path) -> tuple[list[str], list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        header = []
        vertex_count = None
        properties = []
        for raw_line in f:
            line = raw_line.rstrip("\n")
            header.append(line)
            stripped = line.strip()
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
            elif stripped.startswith("property") and vertex_count is not None:
                properties.append(stripped.split()[-1])
            elif stripped == "end_header":
                break
        if "format ascii 1.0" not in header:
            raise RuntimeError(f"Only ASCII PLY is supported by this exporter: {path}")
        if vertex_count is None:
            raise RuntimeError(f"PLY file has no element vertex header: {path}")
        rows = [f.readline().strip().split() for _ in range(vertex_count)]
    return header, properties, rows


def write_ascii_ply_table(path: Path, header: list[str], rows: list[list[str]], extra_properties: list[str]) -> None:
    ensure_dir(path.parent)
    out_header = []
    inserted = False
    for line in header:
        if line.strip() == "end_header" and not inserted:
            out_header.extend(extra_properties)
            inserted = True
        out_header.append(line)
    with path.open("w", encoding="utf-8") as f:
        for line in out_header:
            f.write(f"{line}\n")
        for row in rows:
            f.write(" ".join(row) + "\n")


def write_semantic_ply_with_labels(source_ply: Path, output_ply: Path, labels: list[int]) -> tuple[int, str]:
    try:
        header, _properties, rows = read_ascii_ply_table(source_ply)
        if len(rows) != len(labels):
            raise ValueError(f"Label count {len(labels)} does not match PLY vertex count {len(rows)}.")
        out_rows = [row + [str(label)] for row, label in zip(rows, labels)]
        write_ascii_ply_table(output_ply, header, out_rows, ["property int object_id"])
        return len(rows), "ascii_passthrough"
    except Exception:
        pass

    np = import_numpy()
    try:
        import open3d as o3d  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"Only ASCII PLY can be exported without Open3D: {source_ply}") from exc

    pcd = o3d.io.read_point_cloud(str(source_ply))
    if pcd.is_empty():
        raise RuntimeError(f"Open3D could not read any points from: {source_ply}")
    points = np.asarray(pcd.points, dtype=np.float64)
    if points.shape[0] != len(labels):
        raise ValueError(f"Label count {len(labels)} does not match PLY vertex count {points.shape[0]}.")
    colors = np.asarray(pcd.colors, dtype=np.float64) if pcd.has_colors() else np.zeros((points.shape[0], 3), dtype=np.float64)
    colors = np.clip(np.rint(colors * 255.0), 0, 255).astype(np.uint8)

    ensure_dir(output_ply.parent)
    with output_ply.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {points.shape[0]}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("property int object_id\n")
        f.write("end_header\n")
        for point, color, label in zip(points, colors, labels):
            f.write(
                f"{point[0]:.8f} {point[1]:.8f} {point[2]:.8f} "
                f"{int(color[0])} {int(color[1])} {int(color[2])} {int(label)}\n"
            )
    return points.shape[0], "open3d_rewrite"


def load_point_index_mask(path: Path) -> list[int]:
    if path.suffix == ".npy":
        np = import_numpy()
        return [int(value) for value in np.load(path).tolist()]
    data = read_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected list of point indices: {path}")
    return [int(value) for value in data]


def resolve_project_path(value: str | Path, project_root: Path) -> Path:
    path = value if isinstance(value, Path) else Path(str(value))
    return path if path.is_absolute() else project_root / path


def infer_mask_source_ply(project_root: Path, manifest: dict[str, Any], mask_3d_dir: Path, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    object_masks = mask_3d_dir / "object_masks.json"
    if object_masks.exists():
        data = read_json(object_masks)
        point_cloud = data.get("point_cloud") if isinstance(data, dict) else None
        if point_cloud:
            return resolve_project_path(point_cloud, project_root).resolve()
    return resolve_project_path(manifest["scene"]["point_cloud"], project_root).resolve()


def source_labels_from_object_masks(
    mask_3d_dir: Path,
    objects_dir: Path,
    source_point_count: int,
) -> tuple[list[int], list[dict[str, Any]], dict[str, int]]:
    labels = [0 for _ in range(source_point_count)]
    object_table: list[dict[str, Any]] = [{"object_id": "background", "semantic_id": 0, "point_count": 0}]
    object_id_to_semantic = {"background": 0}

    for semantic_id, object_json in enumerate(sorted(objects_dir.glob("*/object.json")), start=1):
        obj = read_json(object_json)
        object_id = obj["object_id"]
        mask_3d = obj.get("mask_3d") if isinstance(obj.get("mask_3d"), dict) else {}
        index_path = resolve_existing_path(mask_3d.get("point_indices_json") or mask_3d.get("point_indices_npy"), objects_dir.parent)
        if not index_path or not index_path.exists():
            index_path = mask_3d_dir / object_id / "point_indices.json"
        if not index_path.exists():
            index_path = mask_3d_dir / object_id / "point_indices.npy"
        if not index_path.exists():
            continue
        indices = load_point_index_mask(index_path)
        assigned = 0
        for index in indices:
            if 0 <= index < len(labels):
                labels[index] = semantic_id
                assigned += 1
        object_id_to_semantic[object_id] = semantic_id
        object_table.append(
            {
                "object_id": object_id,
                "semantic_id": semantic_id,
                "name": obj.get("name", object_id),
                "category": obj.get("category", "unknown"),
                "asset_role": obj.get("asset_role", "object"),
                "source_point_count": assigned,
                "point_count": 0,
                "bbox_3d": obj.get("bbox_3d"),
            }
        )
    return labels, object_table, object_id_to_semantic


def nearest_source_indices(source_points, target_points):
    np = import_numpy()
    try:
        from scipy.spatial import cKDTree  # type: ignore

        distances, indices = cKDTree(source_points).query(target_points, k=1, workers=-1)
        return indices.astype(np.int64), distances.astype(np.float64), "scipy_ckdtree"
    except Exception:
        pass

    try:
        from sklearn.neighbors import NearestNeighbors  # type: ignore

        nn = NearestNeighbors(n_neighbors=1, algorithm="auto")
        nn.fit(source_points)
        distances, indices = nn.kneighbors(target_points, return_distance=True)
        return indices[:, 0].astype(np.int64), distances[:, 0].astype(np.float64), "sklearn_nearest_neighbors"
    except Exception:
        pass

    if source_points.shape[0] * target_points.shape[0] > 5_000_000:
        raise RuntimeError("Nearest transfer requires scipy or scikit-learn for large point clouds.")

    indices = np.empty(target_points.shape[0], dtype=np.int64)
    distances = np.empty(target_points.shape[0], dtype=np.float64)
    for idx, point in enumerate(target_points):
        squared = np.sum((source_points - point) ** 2, axis=1)
        best = int(np.argmin(squared))
        indices[idx] = best
        distances[idx] = float(np.sqrt(squared[best]))
    return indices, distances, "numpy_bruteforce"


def target_labels_from_transfer(
    source_labels: list[int],
    source_points,
    target_points,
    mode: str,
    max_distance: float | None,
) -> tuple[list[int], dict[str, Any]]:
    np = import_numpy()
    if mode == "index":
        if len(source_labels) != target_points.shape[0]:
            raise ValueError(
                f"Index transfer requires mask source count ({len(source_labels)}) "
                f"to match target vertex count ({target_points.shape[0]}). Use --transfer-mode nearest."
            )
        return list(source_labels), {
            "mode": "index",
            "source_point_count": len(source_labels),
            "target_vertex_count": int(target_points.shape[0]),
        }

    indices, distances, engine = nearest_source_indices(source_points, target_points)
    labels_array = np.asarray(source_labels, dtype=np.int64)[indices]
    rejected = 0
    if max_distance is not None:
        far = distances > float(max_distance)
        rejected = int(far.sum())
        labels_array[far] = 0
    nonzero_distances = distances[labels_array > 0] if labels_array.size else distances
    transfer_info = {
        "mode": "nearest",
        "engine": engine,
        "source_point_count": len(source_labels),
        "target_vertex_count": int(target_points.shape[0]),
        "max_transfer_distance": max_distance,
        "rejected_by_distance": rejected,
        "mean_distance": float(distances.mean()) if distances.size else 0.0,
        "max_distance_observed": float(distances.max()) if distances.size else 0.0,
        "mean_labeled_distance": float(nonzero_distances.mean()) if nonzero_distances.size else 0.0,
    }
    return [int(value) for value in labels_array.tolist()], transfer_info


def update_object_table_counts(object_table: list[dict[str, Any]], labels: list[int]) -> None:
    counts: dict[int, int] = {}
    for label in labels:
        counts[int(label)] = counts.get(int(label), 0) + 1
    for item in object_table:
        item["point_count"] = counts.get(int(item["semantic_id"]), 0)


def semantic_preview_color(label: int) -> tuple[int, int, int]:
    if int(label) <= 0:
        return (175, 181, 190)
    return SEMANTIC_PREVIEW_PALETTE[(int(label) - 1) % len(SEMANTIC_PREVIEW_PALETTE)]


def read_semantic_ply(path: Path):
    np = import_numpy()
    header, properties, rows = read_ascii_ply_table(path)
    del header
    property_to_index = {name: idx for idx, name in enumerate(properties)}
    required = {"x", "y", "z", "object_id"}
    missing = sorted(required - set(property_to_index))
    if missing:
        raise RuntimeError(f"Semantic PLY is missing required properties {missing}: {path}")
    points = np.array(
        [
            [
                float(row[property_to_index["x"]]),
                float(row[property_to_index["y"]]),
                float(row[property_to_index["z"]]),
            ]
            for row in rows
        ],
        dtype=np.float64,
    )
    labels = np.array([int(float(row[property_to_index["object_id"]])) for row in rows], dtype=np.int64)
    colors = None
    if {"red", "green", "blue"}.issubset(property_to_index):
        colors = np.array(
            [
                [
                    float(row[property_to_index["red"]]) / 255.0,
                    float(row[property_to_index["green"]]) / 255.0,
                    float(row[property_to_index["blue"]]) / 255.0,
                ]
                for row in rows
            ],
            dtype=np.float64,
        )
    return points, labels, colors


def semantic_label_counts(labels, indices) -> dict[str, int]:
    np = import_numpy()
    if len(indices) == 0:
        return {}
    selected = labels[indices]
    unique, counts = np.unique(selected, return_counts=True)
    return {str(int(label)): int(count) for label, count in zip(unique, counts)}


def semantic_legend_from_manifest(semantic_manifest: dict[str, Any] | None, labels) -> dict[str, dict[str, Any]]:
    np = import_numpy()
    present_ids = {int(value) for value in np.unique(labels).tolist()}
    legend: dict[int, dict[str, Any]] = {
        0: {
            "semantic_id": 0,
            "object_id": "background",
            "name": "background",
            "category": "background",
            "color": list(semantic_preview_color(0)),
            "point_count": int((labels == 0).sum()),
        }
    }
    if isinstance(semantic_manifest, dict):
        for item in semantic_manifest.get("objects", []):
            if not isinstance(item, dict):
                continue
            semantic_id = int(item.get("semantic_id", 0))
            legend[semantic_id] = {
                "semantic_id": semantic_id,
                "object_id": item.get("object_id", f"semantic_{semantic_id}"),
                "name": item.get("name", item.get("object_id", f"semantic_{semantic_id}")),
                "category": item.get("category", "unknown"),
                "color": list(semantic_preview_color(semantic_id)),
                "point_count": int((labels == semantic_id).sum()),
                "source_point_count": item.get("source_point_count"),
                "bbox_3d": item.get("bbox_3d"),
            }
    for semantic_id in present_ids:
        if semantic_id not in legend:
            legend[semantic_id] = {
                "semantic_id": semantic_id,
                "object_id": f"semantic_{semantic_id}",
                "name": f"semantic {semantic_id}",
                "category": "unknown",
                "color": list(semantic_preview_color(semantic_id)),
                "point_count": int((labels == semantic_id).sum()),
            }
    return {str(key): legend[key] for key in sorted(legend)}


def semantic_colors_for_labels(labels):
    np = import_numpy()
    colors = np.zeros((labels.shape[0], 3), dtype=np.uint8)
    for semantic_id in np.unique(labels):
        colors[labels == semantic_id] = semantic_preview_color(int(semantic_id))
    return colors


def write_colored_semantic_ply(path: Path, points, labels, colors_u8) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {points.shape[0]}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("property int object_id\n")
        f.write("end_header\n")
        for point, color, label in zip(points, colors_u8, labels):
            f.write(
                f"{point[0]:.8f} {point[1]:.8f} {point[2]:.8f} "
                f"{int(color[0])} {int(color[1])} {int(color[2])} {int(label)}\n"
            )


def cmd_render_semantic_preview(args: argparse.Namespace) -> int:
    np = import_numpy()
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    artifacts = manifest.get("artifacts", {})
    semantic_splats_ply = args.semantic_splats_ply.resolve() if args.semantic_splats_ply else resolve_existing_path(artifacts.get("semantic_splats_ply"), project_root)
    if semantic_splats_ply is None or not semantic_splats_ply.exists():
        raise FileNotFoundError("Missing semantic splats PLY. Run export-splat-masks first.")
    semantic_manifest_path = args.semantic_manifest.resolve() if args.semantic_manifest else resolve_existing_path(artifacts.get("semantic_splats_manifest"), project_root)
    semantic_manifest = safe_read_json(semantic_manifest_path) if semantic_manifest_path else None
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "semantic_preview"))

    frames = list_frame_images(frames_dir)
    if args.max_frames and args.max_frames > 0:
        frames = frames[: args.max_frames]
    camera_info = load_camera_info(camera_info_path)
    points, labels, _source_colors = read_semantic_ply(semantic_splats_ply)
    if points.shape[0] == 0:
        raise RuntimeError(f"No points found in semantic PLY: {semantic_splats_ply}")
    colors_u8 = semantic_colors_for_labels(labels)
    colored_ply_path = output_dir / "semantic_splats_colored.ply"
    write_colored_semantic_ply(colored_ply_path, points, labels, colors_u8)
    legend = semantic_legend_from_manifest(semantic_manifest, labels)

    frame_reports = []
    for frame_path in frames:
        frame_id = frame_id_for_path(frame_path)
        image = cv2.imread(str(frame_path))
        if image is None:
            raise RuntimeError(f"Failed to read frame image: {frame_path}")
        intrinsic = intrinsic_for_frame(camera_info, frame_id)
        extrinsic = resolve_extrinsic(camera_info["extrinsic"], frame_id)
        if extrinsic is None:
            frame_reports.append({"frame_id": frame_id, "image": str(frame_path), "skipped": True, "reason": "missing_extrinsic"})
            continue
        w2c = world_to_camera_matrix(extrinsic, camera_info.get("extrinsic_type") or args.extrinsic_type)
        inside, u, v, z = project_points(points, intrinsic, w2c)
        if args.occlusion_filter:
            visible, _zbuf = visibility_mask_from_projection(
                inside,
                u,
                v,
                z,
                int(intrinsic["w"]),
                int(intrinsic["h"]),
                args.depth_tolerance,
                args.relative_depth_tolerance,
            )
            draw_mask = visible
        else:
            visible = inside
            draw_mask = inside

        if not args.include_background:
            draw_mask = draw_mask & (labels > 0)
        draw_indices = np.flatnonzero(draw_mask)
        if args.max_points_per_frame and draw_indices.size > args.max_points_per_frame:
            rng = np.random.default_rng(args.seed)
            draw_indices = np.sort(rng.choice(draw_indices, size=int(args.max_points_per_frame), replace=False))

        overlay = draw_projected_points(image, u, v, draw_indices, colors_u8, args.point_radius, args.alpha)
        frame_dir = ensure_dir(output_dir / frame_id)
        overlay_path = frame_dir / "semantic_overlay.png"
        cv2.imwrite(str(overlay_path), overlay)

        projected_foreground = np.flatnonzero(inside & (labels > 0))
        visible_foreground = np.flatnonzero(visible & (labels > 0))
        drawn_foreground = draw_indices[labels[draw_indices] > 0]
        frame_reports.append(
            {
                "frame_id": frame_id,
                "image": str(frame_path),
                "overlay": str(overlay_path),
                "skipped": False,
                "point_count": int(points.shape[0]),
                "foreground_point_count": int((labels > 0).sum()),
                "projected_points": int(inside.sum()),
                "visible_points": int(visible.sum()),
                "projected_foreground_points": int(projected_foreground.size),
                "visible_foreground_points": int(visible_foreground.size),
                "drawn_points": int(draw_indices.size),
                "drawn_foreground_points": int(drawn_foreground.size),
                "projected_label_counts": semantic_label_counts(labels, np.flatnonzero(inside)),
                "visible_label_counts": semantic_label_counts(labels, np.flatnonzero(visible)),
                "drawn_label_counts": semantic_label_counts(labels, draw_indices),
                "projected_foreground_ratio": float(projected_foreground.size / max(1, int((labels > 0).sum()))),
                "visible_foreground_ratio": float(visible_foreground.size / max(1, int((labels > 0).sum()))),
            }
        )

    valid_reports = [item for item in frame_reports if not item.get("skipped")]
    summary = {
        "frame_count": len(frame_reports),
        "valid_frame_count": len(valid_reports),
        "semantic_vertex_count": int(points.shape[0]),
        "foreground_vertex_count": int((labels > 0).sum()),
        "semantic_id_count": len([key for key in legend if int(key) > 0]),
        "mean_projected_foreground_ratio": float(np.mean([item["projected_foreground_ratio"] for item in valid_reports])) if valid_reports else None,
        "mean_visible_foreground_ratio": float(np.mean([item["visible_foreground_ratio"] for item in valid_reports])) if valid_reports else None,
    }
    preview_manifest_path = output_dir / "semantic_preview.json"
    preview_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "semantic_splats_ply": str(semantic_splats_ply),
        "semantic_splats_manifest": str(semantic_manifest_path) if semantic_manifest_path else None,
        "colored_semantic_ply": str(colored_ply_path),
        "frames_dir": str(frames_dir),
        "camera_info": str(camera_info_path),
        "output_dir": str(output_dir),
        "occlusion_filter": bool(args.occlusion_filter),
        "include_background": bool(args.include_background),
        "legend": legend,
        "summary": summary,
        "frames": frame_reports,
        "notes": "Semantic object_id colors projected back to source frames for checking 3D object-mask alignment.",
    }
    write_json(preview_manifest_path, preview_manifest)
    manifest["artifacts"]["semantic_preview"] = str(preview_manifest_path)
    manifest["artifacts"]["semantic_splats_colored_ply"] = str(colored_ply_path)
    save_manifest(project_root, manifest)
    print(f"Rendered {len(valid_reports)} semantic preview frame(s) to {output_dir}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"Colored semantic PLY: {colored_ply_path}")
    print(f"Preview manifest: {preview_manifest_path}")
    return 0


def cmd_export_splat_masks(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    source_ply = args.splat_ply
    if source_ply is None:
        source_value = manifest.get("artifacts", {}).get("scene_3dgs_ply") or manifest["scene"]["point_cloud"]
        source_ply = project_root / source_value if not Path(source_value).is_absolute() else Path(source_value)
    source_ply = source_ply.resolve()
    mask_3d_dir = project_root / manifest["masks"]["mask_3d_dir"]
    objects_dir = project_root / manifest["objects_dir"]
    output_ply = args.output or (project_root / "simulator_assets" / "semantic_splats.ply")
    manifest_path = project_root / "simulator_assets" / "semantic_splats_manifest.json"

    target_points, _colors = read_point_cloud(source_ply)
    mask_source_ply = infer_mask_source_ply(project_root, manifest, mask_3d_dir, args.mask_source_ply)
    source_points, _source_colors = read_point_cloud(mask_source_ply)
    source_labels, object_table, object_id_to_semantic = source_labels_from_object_masks(
        mask_3d_dir,
        objects_dir,
        int(source_points.shape[0]),
    )

    transfer_mode = args.transfer_mode
    if transfer_mode == "auto":
        same_path = source_ply.resolve() == mask_source_ply.resolve()
        transfer_mode = "index" if same_path and len(source_labels) == target_points.shape[0] else "nearest"

    labels, transfer_info = target_labels_from_transfer(
        source_labels,
        source_points,
        target_points,
        transfer_mode,
        args.max_transfer_distance,
    )
    update_object_table_counts(object_table, labels)
    vertex_count, export_mode = write_semantic_ply_with_labels(source_ply, output_ply, labels)
    viewer_exports = None
    try:
        viewer_exports = export_viewer_plys(output_ply, output_ply.parent, "semantic", include_labels=True)
    except Exception as exc:
        viewer_exports = {"error": str(exc)}
    semantic_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "source_ply": str(source_ply),
        "mask_source_ply": str(mask_source_ply),
        "output_ply": str(output_ply),
        "vertex_count": vertex_count,
        "export_mode": export_mode,
        "viewer_exports": viewer_exports,
        "transfer": transfer_info,
        "property": "object_id",
        "object_id_to_semantic": object_id_to_semantic,
        "objects": object_table,
        "notes": (
            "Semantic labels are transferred from fused 3D object masks to the output PLY. "
            "Index mode requires identical vertex order; nearest mode transfers labels by XYZ nearest neighbor."
        ),
    }
    write_json(manifest_path, semantic_manifest)
    manifest["artifacts"]["semantic_splats_ply"] = str(output_ply)
    manifest["artifacts"]["semantic_splats_manifest"] = str(manifest_path)
    if isinstance(viewer_exports, dict) and viewer_exports.get("point_cloud_ply"):
        manifest["artifacts"]["semantic_point_cloud_ply"] = str(viewer_exports["point_cloud_ply"])
    if isinstance(viewer_exports, dict) and viewer_exports.get("supersplat_ply"):
        manifest["artifacts"]["semantic_supersplat_ply"] = str(viewer_exports["supersplat_ply"])
    save_manifest(project_root, manifest)
    print(f"Wrote semantic PLY: {output_ply}")
    if isinstance(viewer_exports, dict) and viewer_exports.get("supersplat_ply"):
        print(f"Wrote semantic SuperSplat PLY: {viewer_exports['supersplat_ply']}")
        print(f"Wrote semantic point-cloud PLY: {viewer_exports['point_cloud_ply']}")
    print(f"Wrote semantic manifest: {manifest_path}")
    return 0


def cmd_export_viewer_plys(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    artifacts = manifest.get("artifacts", {})
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "viewer_plys"))
    kind = args.kind
    results: dict[str, Any] = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "output_dir": str(output_dir),
        "kind": kind,
        "exports": {},
    }

    def export_one(name: str, source_value: str | Path | None, prefix: str, include_labels: bool = False) -> None:
        if not source_value:
            results["exports"][name] = {"ok": False, "error": "missing source artifact"}
            return
        source_path = resolve_existing_path(str(source_value), project_root)
        if source_path is None or not source_path.exists():
            results["exports"][name] = {"ok": False, "error": f"missing source file: {source_value}"}
            return
        try:
            exported = export_viewer_plys(source_path, output_dir, prefix, include_labels=include_labels)
            exported["ok"] = True
            results["exports"][name] = exported
        except Exception as exc:
            results["exports"][name] = {"ok": False, "source_ply": str(source_path), "error": str(exc)}

    if args.splat_ply:
        export_one("custom", args.splat_ply, args.prefix or args.splat_ply.stem, include_labels=args.include_labels)
    else:
        if kind in {"scene", "all"}:
            export_one("scene", artifacts.get("scene_3dgs_ply"), args.prefix or "scene_3dgs", include_labels=False)
        if kind in {"semantic", "all"}:
            export_one("semantic", artifacts.get("semantic_splats_ply"), args.prefix or "semantic_3dgs", include_labels=True)

    manifest_path = output_dir / "viewer_plys_manifest.json"
    write_json(manifest_path, results)
    manifest["artifacts"]["viewer_plys_manifest"] = str(manifest_path)
    scene_export = results["exports"].get("scene")
    if isinstance(scene_export, dict) and scene_export.get("ok"):
        manifest["artifacts"]["scene_3dgs_point_cloud_ply"] = scene_export.get("point_cloud_ply")
        manifest["artifacts"]["scene_3dgs_supersplat_ply"] = scene_export.get("supersplat_ply")
    semantic_export = results["exports"].get("semantic")
    if isinstance(semantic_export, dict) and semantic_export.get("ok"):
        manifest["artifacts"]["semantic_point_cloud_ply"] = semantic_export.get("point_cloud_ply")
        manifest["artifacts"]["semantic_supersplat_ply"] = semantic_export.get("supersplat_ply")
    save_manifest(project_root, manifest)

    ok_count = len([item for item in results["exports"].values() if isinstance(item, dict) and item.get("ok")])
    print(f"Viewer PLY exports: {ok_count}/{len(results['exports'])} succeeded")
    for name, item in results["exports"].items():
        if item.get("ok"):
            print(f"- {name}: point_cloud={item.get('point_cloud_ply')}")
            print(f"  {name}: supersplat={item.get('supersplat_ply')}")
        else:
            print(f"- {name}: failed: {item.get('error')}")
    print(f"Manifest: {manifest_path}")
    return 0 if ok_count == len(results["exports"]) else 1


def cmd_export_object_mask_clouds(args: argparse.Namespace) -> int:
    np = import_numpy()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    point_cloud_path = args.point_cloud or infer_mask_source_ply(
        project_root,
        manifest,
        project_root / manifest["masks"]["mask_3d_dir"],
        None,
    )
    points, colors = read_point_cloud(point_cloud_path)
    if colors is None:
        colors_u8 = np.full((points.shape[0], 3), 180, dtype=np.uint8)
    else:
        colors_u8 = np.clip(np.rint(colors * 255.0), 0, 255).astype(np.uint8)

    mask_3d_dir = project_root / manifest["masks"]["mask_3d_dir"]
    objects_dir = project_root / manifest["objects_dir"]
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "object_masks_3d"))
    exported: dict[str, Any] = {}

    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        index_path = mask_3d_dir / object_id / "point_indices.json"
        if not index_path.exists():
            index_path = mask_3d_dir / object_id / "point_indices.npy"
        if not index_path.exists():
            if args.skip_missing:
                continue
            raise FileNotFoundError(f"Missing 3D mask indices for {object_id}")
        indices = [index for index in load_point_index_mask(index_path) if 0 <= index < points.shape[0]]
        object_points = []
        for index in indices:
            point = points[index]
            color = colors_u8[index]
            object_points.append(
                (
                    float(point[0]),
                    float(point[1]),
                    float(point[2]),
                    int(color[0]),
                    int(color[1]),
                    int(color[2]),
                )
            )
        out_ply = output_dir / f"{object_id}.ply"
        write_ascii_ply(out_ply, object_points)
        mask_cloud = {
            "path": str(out_ply),
            "point_count": len(object_points),
            "source_point_cloud": str(point_cloud_path),
            "source_indices": str(index_path),
        }
        obj["mask_3d_cloud"] = mask_cloud
        write_json(object_json, obj)
        exported[object_id] = {
            "object_id": object_id,
            "name": obj.get("name", object_id),
            "category": obj.get("category", "unknown"),
            **mask_cloud,
        }

    manifest_path = output_dir / "object_mask_clouds.json"
    write_json(
        manifest_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "point_cloud": str(point_cloud_path),
            "output_dir": str(output_dir),
            "objects": exported,
        },
    )
    manifest["artifacts"]["object_mask_clouds"] = str(manifest_path)
    save_manifest(project_root, manifest)
    print(f"Exported {len(exported)} object mask cloud(s) to {output_dir}")
    print(f"Object mask cloud manifest: {manifest_path}")
    return 0


def import_open3d():
    try:
        import open3d as o3d  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("This command requires open3d.") from exc
    return o3d


def mesh_asset_coordinate_frame(mesh_asset: dict[str, Any]) -> str:
    frame = mesh_asset.get("coordinate_frame") or mesh_asset.get("mesh_coordinate_frame")
    if frame:
        return str(frame)
    source = mesh_asset.get("source")
    if source == "object_mask_cloud_reconstruction":
        return "video2mesh_scene"
    return "object_local"


def bbox_for_vertex_list(vertices: list[list[float]]) -> dict[str, Any]:
    mins = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maxs = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    size = [maxs[axis] - mins[axis] for axis in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "center": [(mins[axis] + maxs[axis]) * 0.5 for axis in range(3)],
        "size": size,
    }


def summarize_obj_mesh_light(path: Path) -> dict[str, Any]:
    vertices: list[list[float]] = []
    triangle_count = 0
    face_count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.strip().split()
                if len(parts) >= 4:
                    try:
                        vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    except Exception:
                        pass
            elif line.startswith("f "):
                face_count += 1
                parts = line.strip().split()[1:]
                if len(parts) >= 3:
                    triangle_count += max(1, len(parts) - 2)
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "readable": True,
        "parser": "light_obj",
        "vertex_count": len(vertices),
        "triangle_count": triangle_count,
        "face_count": face_count,
    }
    if vertices:
        bbox = bbox_for_vertex_list(vertices)
        summary["bbox"] = bbox
        summary["bbox_diagonal"] = vector_diagonal(bbox.get("size"))
    return summary


def summarize_ascii_ply_mesh_light(path: Path) -> dict[str, Any]:
    vertex_count = 0
    face_count = 0
    vertices: list[list[float]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
            elif stripped.startswith("element face"):
                face_count = int(stripped.split()[-1])
            elif stripped == "end_header":
                break
        for _ in range(vertex_count):
            line = f.readline()
            if not line:
                break
            parts = line.strip().split()
            if len(parts) >= 3:
                try:
                    vertices.append([float(parts[0]), float(parts[1]), float(parts[2])])
                except Exception:
                    pass
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "readable": True,
        "parser": "light_ascii_ply",
        "vertex_count": vertex_count,
        "triangle_count": face_count,
        "face_count": face_count,
    }
    if vertices:
        bbox = bbox_for_vertex_list(vertices)
        summary["bbox"] = bbox
        summary["bbox_diagonal"] = vector_diagonal(bbox.get("size"))
    return summary


def summarize_triangle_mesh_light(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".obj":
        return summarize_obj_mesh_light(path)
    if suffix == ".ply":
        return summarize_ascii_ply_mesh_light(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "readable": False,
        "parser": "light",
        "error": f"No lightweight parser for {suffix or 'unknown'} mesh files.",
    }


def summarize_triangle_mesh(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"exists": False, "readable": False, "error": "missing path"}
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "readable": False,
    }
    if not path.exists():
        summary["error"] = "file does not exist"
        return summary
    try:
        o3d = import_open3d()
        np = import_numpy()
        mesh = o3d.io.read_triangle_mesh(str(path))
        vertices = np.asarray(mesh.vertices, dtype=np.float64)
        triangles = np.asarray(mesh.triangles)
        summary.update(
            {
                "readable": bool(vertices.size),
                "vertex_count": int(vertices.shape[0]) if vertices.ndim == 2 else 0,
                "triangle_count": int(triangles.shape[0]) if triangles.ndim == 2 else 0,
            }
        )
        if vertices.size:
            bbox = bbox_for_points(vertices)
            summary["bbox"] = bbox
            summary["bbox_diagonal"] = vector_diagonal(bbox.get("size") if isinstance(bbox, dict) else None)
        if triangles.size:
            try:
                summary["surface_area"] = float(mesh.get_surface_area())
            except Exception:
                pass
            for name, fn in (
                ("is_watertight", mesh.is_watertight),
                ("is_edge_manifold", mesh.is_edge_manifold),
                ("is_vertex_manifold", mesh.is_vertex_manifold),
                ("is_orientable", mesh.is_orientable),
            ):
                try:
                    summary[name] = bool(fn())
                except Exception:
                    pass
        return summary
    except Exception as exc:
        try:
            light_summary = summarize_triangle_mesh_light(path)
            light_summary["fallback_reason"] = str(exc)
            return light_summary
        except Exception as fallback_exc:
            summary["error"] = f"{exc}; lightweight fallback failed: {fallback_exc}"
        return summary


def mesh_alignment_summary(mask_bbox: dict[str, Any], mesh_summary: dict[str, Any]) -> dict[str, Any]:
    np = import_numpy()
    mesh_bbox = mesh_summary.get("bbox") if isinstance(mesh_summary.get("bbox"), dict) else {}
    mask_center = mask_bbox.get("center") if isinstance(mask_bbox, dict) else None
    mask_size = mask_bbox.get("size") if isinstance(mask_bbox, dict) else None
    mesh_center = mesh_bbox.get("center") if isinstance(mesh_bbox, dict) else None
    mesh_size = mesh_bbox.get("size") if isinstance(mesh_bbox, dict) else None
    result: dict[str, Any] = {
        "has_mask_bbox": isinstance(mask_center, list) and isinstance(mask_size, list),
        "has_mesh_bbox": isinstance(mesh_center, list) and isinstance(mesh_size, list),
    }
    if not result["has_mask_bbox"] or not result["has_mesh_bbox"]:
        result["status"] = "missing_bbox"
        return result

    mask_center_np = np.asarray(mask_center, dtype=np.float64)
    mesh_center_np = np.asarray(mesh_center, dtype=np.float64)
    mask_size_np = np.asarray(mask_size, dtype=np.float64)
    mesh_size_np = np.asarray(mesh_size, dtype=np.float64)
    center_delta = mesh_center_np - mask_center_np
    denom = np.maximum(mask_size_np, 1e-9)
    size_ratio = mesh_size_np / denom
    mask_diag = float(np.linalg.norm(mask_size_np))
    mesh_diag = float(np.linalg.norm(mesh_size_np))
    center_distance = float(np.linalg.norm(center_delta))
    result.update(
        {
            "status": "ok",
            "center_delta": center_delta.tolist(),
            "center_distance": center_distance,
            "center_distance_over_mask_diagonal": float(center_distance / max(mask_diag, 1e-9)),
            "size_ratio": size_ratio.tolist(),
            "mask_diagonal": mask_diag,
            "mesh_diagonal": mesh_diag,
            "mesh_to_mask_diagonal_ratio": float(mesh_diag / max(mask_diag, 1e-9)),
        }
    )
    return result


def transform_triangle_mesh_file(
    source: Path,
    output: Path,
    translation: list[float],
    scale: float,
    write_ascii: bool = False,
) -> dict[str, Any]:
    np = import_numpy()
    o3d = import_open3d()
    mesh = o3d.io.read_triangle_mesh(str(source))
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    if vertices.size == 0:
        raise RuntimeError(f"Mesh has no vertices: {source}")
    transformed = (vertices + np.asarray(translation, dtype=np.float64).reshape(1, 3)) * float(scale)
    mesh.vertices = o3d.utility.Vector3dVector(transformed)
    ensure_dir(output.parent)
    ok = o3d.io.write_triangle_mesh(str(output), mesh, write_ascii=write_ascii)
    if not ok:
        raise RuntimeError(f"Failed to write transformed mesh: {output}")
    return summarize_triangle_mesh(output)


def bbox_fit_length(size: Any, mode: str) -> float | None:
    if not isinstance(size, (list, tuple)) or len(size) < 3:
        return None
    try:
        values = [abs(float(value)) for value in size[:3]]
    except Exception:
        return None
    if mode == "diagonal":
        return vector_diagonal(values)
    return max(values)


def fit_to_mask_bbox_summary(exported_summary: dict[str, Any], target_bbox: dict[str, Any], target_size_scaled: list[float]) -> dict[str, Any]:
    np = import_numpy()
    exported_bbox = exported_summary.get("bbox") if isinstance(exported_summary.get("bbox"), dict) else {}
    exported_size = exported_bbox.get("size") if isinstance(exported_bbox, dict) else None
    result: dict[str, Any] = {
        "has_exported_bbox": isinstance(exported_size, list),
        "target_bbox": target_bbox,
        "target_bbox_size_scaled": target_size_scaled,
    }
    if not isinstance(exported_size, list):
        result["status"] = "missing_exported_bbox"
        return result
    exported_size_np = np.asarray(exported_size, dtype=np.float64)
    target_size_np = np.asarray(target_size_scaled, dtype=np.float64)
    result.update(
        {
            "status": "ok",
            "exported_bbox": exported_bbox,
            "size_ratio": (exported_size_np / np.maximum(target_size_np, 1e-9)).tolist(),
            "mesh_diagonal": float(np.linalg.norm(exported_size_np)),
            "mask_diagonal": float(np.linalg.norm(target_size_np)),
            "mesh_to_mask_diagonal_ratio": float(np.linalg.norm(exported_size_np) / max(float(np.linalg.norm(target_size_np)), 1e-9)),
            "mesh_longest_axis": float(exported_size_np.max()) if exported_size_np.size else 0.0,
            "mask_longest_axis": float(target_size_np.max()) if target_size_np.size else 0.0,
            "mesh_to_mask_longest_axis_ratio": float(exported_size_np.max() / max(float(target_size_np.max()), 1e-9)) if exported_size_np.size and target_size_np.size else None,
            "center_offset_from_local_origin": exported_bbox.get("center"),
        }
    )
    return result


def fit_object_local_mesh_to_bbox(
    source: Path,
    output: Path,
    source_summary: dict[str, Any],
    target_bbox: dict[str, Any],
    scene_scale: float,
    fit_axis: str,
    write_ascii: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_bbox = source_summary.get("bbox") if isinstance(source_summary.get("bbox"), dict) else {}
    source_center = source_bbox.get("center") if isinstance(source_bbox, dict) else None
    source_size = source_bbox.get("size") if isinstance(source_bbox, dict) else None
    target_size = target_bbox.get("size") if isinstance(target_bbox, dict) else None
    if not isinstance(source_center, list) or not isinstance(source_size, list):
        raise RuntimeError("Source mesh has no readable bbox for bbox-fit.")
    if not isinstance(target_size, list):
        raise RuntimeError("Object record has no bbox_3d.size for bbox-fit.")

    source_length = bbox_fit_length(source_size, fit_axis)
    target_length = bbox_fit_length(target_size, fit_axis)
    if not source_length or source_length <= 1e-12:
        raise RuntimeError("Source mesh bbox is too small for bbox-fit.")
    if not target_length or target_length <= 1e-12:
        raise RuntimeError("Target 3D mask bbox is too small for bbox-fit.")

    fit_scale = float(scene_scale) * float(target_length) / float(source_length)
    exported_summary = transform_triangle_mesh_file(
        source,
        output,
        translation=[-float(value) for value in source_center[:3]],
        scale=fit_scale,
        write_ascii=write_ascii,
    )
    target_size_scaled = scaled_vector(target_size, float(scene_scale), [0.0, 0.0, 0.0])
    fit_summary = fit_to_mask_bbox_summary(exported_summary, target_bbox, target_size_scaled)
    fit_summary.update(
        {
            "applied": True,
            "fit_axis": fit_axis,
            "uniform_scale": fit_scale,
            "scene_scale": float(scene_scale),
            "source_bbox": source_bbox,
            "source_fit_length": float(source_length),
            "target_fit_length": float(target_length),
            "target_fit_length_scaled": float(target_length) * float(scene_scale),
            "notes": "Object-local mesh centered at its own bbox origin and uniformly scaled to the fused 3D mask bbox.",
        }
    )
    return exported_summary, fit_summary


def append_asset_issue(issues: list[dict[str, Any]], severity: str, name: str, detail: str, object_id: str | None = None, value: Any = None, threshold: Any = None) -> None:
    issue = {"severity": severity, "name": name, "detail": detail}
    if object_id:
        issue["object_id"] = object_id
    if value is not None:
        issue["value"] = value
    if threshold is not None:
        issue["threshold"] = threshold
    issues.append(issue)


def simulator_asset_qa_report(
    project_root: Path,
    manifest: dict[str, Any],
    bundle_path: Path,
    min_mesh_vertices: int,
    max_center_ratio: float,
    max_size_ratio_delta: float,
    require_physics: bool,
    require_scale_calibration: bool,
) -> dict[str, Any]:
    bundle = read_json(bundle_path)
    coordinate_system = bundle.get("coordinate_system") if isinstance(bundle.get("coordinate_system"), dict) else {}
    issues: list[dict[str, Any]] = []
    object_reports: list[dict[str, Any]] = []
    scene_scale = float(coordinate_system.get("scale_to_meters") or 1.0)
    up_axis = str(coordinate_system.get("up_axis") or "unknown").lower()
    scale_calibrated = bool(coordinate_system.get("scale_calibrated") or coordinate_system.get("calibrated"))

    if require_scale_calibration and not scale_calibrated:
        append_asset_issue(
            issues,
            "required",
            "scale_not_calibrated",
            "coordinate_system.scale_calibrated is not true; reconstruction units should be calibrated before physics-critical simulation.",
        )
    elif not scale_calibrated:
        append_asset_issue(
            issues,
            "warning",
            "scale_not_calibrated",
            "Scale is still an engineering estimate.",
        )
    if up_axis == "unknown":
        append_asset_issue(issues, "warning", "up_axis_unknown", "coordinate_system.up_axis is unknown.")

    for obj in bundle.get("objects", []):
        if not isinstance(obj, dict):
            continue
        object_id = slugify(obj.get("object_id") or "object")
        is_background_structure = obj.get("asset_role") == "background_structure"
        mesh = obj.get("mesh") if isinstance(obj.get("mesh"), dict) else {}
        pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
        physics = obj.get("physics") if isinstance(obj.get("physics"), dict) else {}
        quality = obj.get("quality") if isinstance(obj.get("quality"), dict) else {}
        mesh_quality = quality.get("mesh") if isinstance(quality.get("mesh"), dict) else {}
        mesh_path = resolve_existing_path(mesh.get("path"), project_root) if mesh else None
        mesh_summary = summarize_triangle_mesh(mesh_path) if mesh_path else {"exists": False, "readable": False, "error": "missing mesh path"}
        object_issues: list[dict[str, Any]] = []

        if (not mesh_path or not mesh_path.exists()) and not is_background_structure:
            append_asset_issue(object_issues, "required", "missing_mesh", "Simulator object has no existing mesh path.", object_id)
        elif not mesh_summary.get("readable"):
            if mesh_path or not is_background_structure:
                append_asset_issue(object_issues, "required", "unreadable_mesh", str(mesh_summary.get("error", "mesh is not readable")), object_id)
        else:
            vertices = int(mesh_summary.get("vertex_count") or 0)
            triangles = int(mesh_summary.get("triangle_count") or 0)
            if vertices < min_mesh_vertices:
                append_asset_issue(object_issues, "warning", "low_mesh_vertex_count", f"{vertices} vertices.", object_id, vertices, min_mesh_vertices)
            if triangles <= 0:
                append_asset_issue(object_issues, "warning", "mesh_has_no_triangles", "Mesh has no triangles.", object_id, triangles, ">0")
            if mesh_summary.get("is_watertight") is False:
                append_asset_issue(object_issues, "warning", "mesh_not_watertight", "Mesh is not watertight.", object_id)
            if mesh_summary.get("is_edge_manifold") is False or mesh_summary.get("is_vertex_manifold") is False:
                append_asset_issue(object_issues, "warning", "mesh_not_manifold", "Mesh is not fully manifold.", object_id)

        fit_alignment = mesh_quality.get("fit_to_mask_bbox") if isinstance(mesh_quality.get("fit_to_mask_bbox"), dict) else {}
        alignment = fit_alignment if fit_alignment.get("status") == "ok" else mesh_quality.get("source_to_mask_alignment") if isinstance(mesh_quality.get("source_to_mask_alignment"), dict) else {}
        if alignment.get("status") == "ok":
            center_ratio = None if fit_alignment.get("status") == "ok" else alignment.get("center_distance_over_mask_diagonal")
            fit_axis = fit_alignment.get("fit_axis") if fit_alignment.get("status") == "ok" else None
            size_ratio_value = alignment.get("mesh_to_mask_longest_axis_ratio") if fit_axis == "longest" else alignment.get("mesh_to_mask_diagonal_ratio")
            size_ratio_label = "longest-axis" if fit_axis == "longest" else "diagonal"
            if center_ratio is not None and float(center_ratio) > max_center_ratio:
                append_asset_issue(
                    object_issues,
                    "warning",
                    "mesh_center_far_from_mask_bbox",
                    "Mesh bbox center is far from the fused 3D mask bbox center.",
                    object_id,
                    float(center_ratio),
                    max_center_ratio,
                )
            if size_ratio_value is not None:
                ratio_delta = abs(float(size_ratio_value) - 1.0)
                if ratio_delta > max_size_ratio_delta:
                    append_asset_issue(
                        object_issues,
                        "warning",
                        "mesh_size_differs_from_mask_bbox",
                        f"Mesh {size_ratio_label} differs substantially from the 3D mask bbox {size_ratio_label}.",
                        object_id,
                        float(size_ratio_value),
                        f"1 +/- {max_size_ratio_delta}",
                    )

        body_type = physics.get("body_type")
        mass = physics.get("mass_kg")
        collider = physics.get("collider")
        if require_physics and ((mass is None and not is_background_structure) or collider in (None, "none") or not body_type):
            append_asset_issue(object_issues, "required", "physics_missing", "Mass/body_type/collider must be set for simulator-ready assets.", object_id)
        else:
            if mass is None and not is_background_structure:
                append_asset_issue(object_issues, "warning", "mass_missing", "mass_kg is still unset.", object_id)
            if collider in (None, "none"):
                append_asset_issue(object_issues, "warning", "collider_missing", "No collider is configured.", object_id)
        if pose.get("bbox_size") in (None, [], [0.0, 0.0, 0.0]):
            append_asset_issue(object_issues, "warning", "bbox_size_missing", "Pose bbox_size is missing or zero.", object_id)

        issues.extend(object_issues)
        object_reports.append(
            {
                "object_id": object_id,
                "name": obj.get("name"),
                "category": obj.get("category"),
                "mesh_path": str(mesh_path) if mesh_path else "",
                "mesh_summary": mesh_summary,
                "pose": pose,
                "physics": physics,
                "quality": quality,
                "issues": object_issues,
                "ok": not any(issue.get("severity") == "required" for issue in object_issues),
            }
        )

    required = [issue for issue in issues if issue.get("severity") == "required"]
    warnings = [issue for issue in issues if issue.get("severity") == "warning"]
    return {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "bundle": str(bundle_path),
        "ok": not required,
        "thresholds": {
            "min_mesh_vertices": min_mesh_vertices,
            "max_center_ratio": max_center_ratio,
            "max_size_ratio_delta": max_size_ratio_delta,
            "require_physics": require_physics,
            "require_scale_calibration": require_scale_calibration,
        },
        "coordinate_system": {
            **coordinate_system,
            "scene_scale_to_meters": scene_scale,
            "scale_calibrated": scale_calibrated,
        },
        "objects": object_reports,
        "summary": {
            "object_count": len(object_reports),
            "required_issue_count": len(required),
            "warning_count": len(warnings),
        },
        "issues": issues,
    }


def cmd_qa_simulator_assets(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    bundle_path = simulator_bundle_path(project_root, manifest, args.bundle)
    if not bundle_path.exists():
        raise FileNotFoundError(f"Missing simulator asset bundle: {bundle_path}. Run export-simulator-assets first.")
    report = simulator_asset_qa_report(
        project_root=project_root,
        manifest=manifest,
        bundle_path=bundle_path,
        min_mesh_vertices=args.min_mesh_vertices,
        max_center_ratio=args.max_center_ratio,
        max_size_ratio_delta=args.max_size_ratio_delta,
        require_physics=args.require_physics,
        require_scale_calibration=args.require_scale_calibration,
    )
    output_path = args.output.resolve() if args.output else project_root / manifest["simulator_assets_dir"] / "simulator_asset_qa.json"
    write_json(output_path, report)
    manifest.setdefault("artifacts", {})["simulator_asset_qa"] = str(output_path)
    save_manifest(project_root, manifest)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if report["ok"] else "ISSUES"
        print(f"Simulator asset QA: {status} ({report['scene_id']})")
        print(
            f"Objects: {report['summary']['object_count']}; "
            f"required={report['summary']['required_issue_count']}; warnings={report['summary']['warning_count']}"
        )
        for issue in report["issues"][: args.max_issues]:
            object_prefix = f"{issue.get('object_id')}: " if issue.get("object_id") else ""
            print(f"- [{issue.get('severity')}] {object_prefix}{issue.get('name')}: {issue.get('detail')}")
        if len(report["issues"]) > args.max_issues:
            print(f"- ... {len(report['issues']) - args.max_issues} more issue(s)")
        print(f"Report: {output_path}")
    return 1 if args.fail_on_required and not report["ok"] else 0


def point_cloud_from_arrays(points, colors):
    np = import_numpy()
    o3d = import_open3d()
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.asarray(points, dtype=np.float64))
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(np.clip(np.asarray(colors, dtype=np.float64), 0.0, 1.0))
    return pcd


def mesh_vertex_triangle_count(mesh) -> tuple[int, int]:
    return len(mesh.vertices), len(mesh.triangles)


def clean_triangle_mesh(mesh):
    mesh.remove_duplicated_vertices()
    mesh.remove_duplicated_triangles()
    mesh.remove_degenerate_triangles()
    mesh.remove_unreferenced_vertices()
    try:
        mesh.remove_non_manifold_edges()
    except Exception:
        pass
    if len(mesh.triangles) > 0:
        mesh.compute_vertex_normals()
    return mesh


def estimate_pcd_spacing(pcd, fallback: float = 0.02) -> float:
    np = import_numpy()
    try:
        distances = np.asarray(pcd.compute_nearest_neighbor_distance(), dtype=np.float64)
        distances = distances[distances > 1e-12]
        if distances.size:
            return float(np.median(distances))
    except Exception:
        pass
    return float(fallback)


def paint_mesh_from_points(mesh, colors) -> None:
    np = import_numpy()
    if colors is None:
        return
    colors_array = np.asarray(colors, dtype=np.float64)
    if colors_array.size == 0:
        return
    mean_color = np.clip(colors_array.reshape(-1, 3).mean(axis=0), 0.0, 1.0)
    try:
        mesh.paint_uniform_color(mean_color.tolist())
    except Exception:
        pass


def bbox_mesh_from_points(points, colors, min_extent: float, padding_ratio: float):
    np = import_numpy()
    o3d = import_open3d()
    points_array = np.asarray(points, dtype=np.float64)
    mins = points_array.min(axis=0)
    maxs = points_array.max(axis=0)
    center = (mins + maxs) / 2.0
    extent = maxs - mins
    extent = np.maximum(extent * (1.0 + float(padding_ratio)), float(min_extent))
    min_corner = center - extent / 2.0
    mesh = o3d.geometry.TriangleMesh.create_box(
        width=float(extent[0]),
        height=float(extent[1]),
        depth=float(extent[2]),
    )
    mesh.translate(min_corner.tolist())
    paint_mesh_from_points(mesh, colors)
    return clean_triangle_mesh(mesh), {
        "method": "bbox",
        "bbox_min": min_corner.tolist(),
        "bbox_max": (min_corner + extent).tolist(),
        "bbox_extent": extent.tolist(),
        "notes": "Axis-aligned box fallback from object 3D mask extent.",
    }


def convex_hull_mesh_from_pcd(pcd):
    try:
        mesh, _ = pcd.compute_convex_hull(joggle_inputs=True)
    except TypeError:
        mesh, _ = pcd.compute_convex_hull()
    return clean_triangle_mesh(mesh), {"method": "convex_hull"}


def alpha_shape_mesh_from_pcd(pcd, alpha: float):
    o3d = import_open3d()
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, float(alpha))
    return clean_triangle_mesh(mesh), {"method": "alpha_shape", "alpha": float(alpha)}


def ball_pivoting_mesh_from_pcd(pcd, spacing: float, multipliers: list[float], normal_radius: float | None):
    o3d = import_open3d()
    radius = float(normal_radius or max(spacing * 3.0, 1e-4))
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30))
    try:
        pcd.orient_normals_consistent_tangent_plane(30)
    except Exception:
        pass
    radii = [max(float(spacing) * float(multiplier), 1e-5) for multiplier in multipliers]
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd,
        o3d.utility.DoubleVector(radii),
    )
    return clean_triangle_mesh(mesh), {"method": "ball_pivoting", "spacing": float(spacing), "radii": radii}


def reconstruct_mesh_from_object_points(points, colors, args: argparse.Namespace) -> tuple[Any, dict[str, Any]]:
    np = import_numpy()
    points_array = np.asarray(points, dtype=np.float64)
    if points_array.ndim != 2 or points_array.shape[1] != 3:
        raise ValueError(f"Expected Nx3 points, got shape {points_array.shape}")
    if points_array.shape[0] < max(1, int(args.min_points)):
        raise ValueError(f"Only {points_array.shape[0]} point(s), below --min-points {args.min_points}")

    colors_array = None if colors is None else np.asarray(colors, dtype=np.float64)
    pcd = point_cloud_from_arrays(points_array, colors_array)
    if args.voxel_size and args.voxel_size > 0:
        pcd = pcd.voxel_down_sample(float(args.voxel_size))
    if args.remove_outliers and len(pcd.points) >= max(8, args.outlier_nb_neighbors):
        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=int(args.outlier_nb_neighbors),
            std_ratio=float(args.outlier_std_ratio),
        )
    if len(pcd.points) < max(1, int(args.min_points)):
        raise ValueError(f"Only {len(pcd.points)} point(s) after filtering, below --min-points {args.min_points}")

    spacing = estimate_pcd_spacing(pcd, fallback=args.min_extent)
    alpha = float(args.alpha) if args.alpha is not None else max(spacing * float(args.alpha_multiplier), 1e-5)
    method_order = [args.method] if args.method != "auto" else ["alpha_shape", "ball_pivoting", "convex_hull", "bbox"]
    attempts = []
    last_error = ""
    for method in method_order:
        try:
            if method == "alpha_shape":
                mesh, detail = alpha_shape_mesh_from_pcd(pcd, alpha)
            elif method == "ball_pivoting":
                mesh, detail = ball_pivoting_mesh_from_pcd(
                    pcd,
                    spacing,
                    [float(value) for value in args.ball_radius_multipliers],
                    args.normal_radius,
                )
            elif method == "convex_hull":
                mesh, detail = convex_hull_mesh_from_pcd(pcd)
            elif method == "bbox":
                mesh, detail = bbox_mesh_from_points(np.asarray(pcd.points), colors_array, args.min_extent, args.bbox_padding_ratio)
            else:
                raise ValueError(f"Unknown mesh method: {method}")
            vertices, triangles = mesh_vertex_triangle_count(mesh)
            detail.update(
                {
                    "input_point_count": int(points_array.shape[0]),
                    "filtered_point_count": int(len(pcd.points)),
                    "vertex_count": int(vertices),
                    "triangle_count": int(triangles),
                    "spacing_estimate": float(spacing),
                }
            )
            if vertices > 0 and triangles > 0:
                if method not in {"bbox"}:
                    paint_mesh_from_points(mesh, colors_array)
                return mesh, {"selected": detail, "attempts": attempts + [detail]}
            raise RuntimeError(f"{method} produced {vertices} vertices and {triangles} triangles")
        except Exception as exc:
            last_error = str(exc)
            attempts.append({"method": method, "error": last_error})
            if args.method != "auto":
                raise

    if args.method == "auto":
        mesh, detail = bbox_mesh_from_points(points_array, colors_array, args.min_extent, args.bbox_padding_ratio)
        vertices, triangles = mesh_vertex_triangle_count(mesh)
        detail.update(
            {
                "input_point_count": int(points_array.shape[0]),
                "filtered_point_count": int(len(pcd.points)),
                "vertex_count": int(vertices),
                "triangle_count": int(triangles),
                "spacing_estimate": float(spacing),
                "fallback_reason": last_error,
            }
        )
        return mesh, {"selected": detail, "attempts": attempts + [detail]}
    raise RuntimeError(last_error or "Object mesh reconstruction failed.")


def resolve_object_mask_cloud_path(obj: dict[str, Any], object_id: str, project_root: Path, manifest: dict[str, Any]) -> Path | None:
    mask_cloud = obj.get("mask_3d_cloud") if isinstance(obj.get("mask_3d_cloud"), dict) else {}
    candidates = [mask_cloud.get("path")]
    mask_cloud_manifest = resolve_existing_path(manifest.get("artifacts", {}).get("object_mask_clouds"), project_root)
    if mask_cloud_manifest and mask_cloud_manifest.exists():
        try:
            data = read_json(mask_cloud_manifest)
            entry = (data.get("objects") or {}).get(object_id) if isinstance(data, dict) else None
            if isinstance(entry, dict):
                candidates.append(entry.get("path"))
        except Exception:
            pass
    candidates.append(str(project_root / manifest["simulator_assets_dir"] / "object_masks_3d" / f"{object_id}.ply"))
    for value in candidates:
        path = resolve_existing_path(value, project_root)
        if path and path.exists():
            return path
    return None


def cmd_reconstruct_object_meshes(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks/export-object-mask-clouds first.")

    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "reconstructed_meshes"))
    sim_objects_dir = ensure_dir(project_root / manifest["simulator_assets_dir"] / "objects")
    reconstructed: dict[str, Any] = {}
    missing: list[str] = []
    failed: dict[str, Any] = {}

    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        mask_cloud_path = resolve_object_mask_cloud_path(obj, object_id, project_root, manifest)
        if mask_cloud_path is None:
            missing.append(object_id)
            if args.skip_missing:
                continue
            raise FileNotFoundError(f"Missing object mask cloud for {object_id}. Run export-object-mask-clouds first.")

        try:
            points, colors = read_point_cloud(mask_cloud_path)
            mesh, reconstruction = reconstruct_mesh_from_object_points(points, colors, args)
        except Exception as exc:
            failed[object_id] = {"mask_cloud": str(mask_cloud_path), "error": str(exc)}
            if args.skip_failed:
                continue
            raise

        object_mesh_dir = ensure_dir(output_dir / object_id)
        mesh_path = object_mesh_dir / f"{object_id}.{args.format}"
        import_open3d().io.write_triangle_mesh(str(mesh_path), mesh, write_ascii=args.ascii)
        asset_path = mesh_path
        if args.copy_to_assets:
            dst = sim_objects_dir / object_id / mesh_path.name
            if mesh_path.resolve() != dst.resolve():
                asset_path = copy_or_link(mesh_path, dst, args.mode)
            else:
                asset_path = dst

        metadata = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "source": "object_mask_cloud_reconstruction",
            "source_mask_cloud": str(mask_cloud_path),
            "source_mesh": str(mesh_path),
            "asset_path": str(asset_path),
            "format": args.format,
            "coordinate_frame": "video2mesh_scene",
            "reconstruction": reconstruction,
            "notes": (
                "Mesh reconstructed from the object's fused 3D mask point cloud. "
                "Auto mode may fall back to an axis-aligned bbox mesh when the mask cloud is sparse, planar, or not watertight."
            ),
        }
        write_json(object_mesh_dir / "reconstruction.json", metadata)
        obj["mesh_asset"] = metadata
        write_json(object_json, obj)
        reconstructed[object_id] = metadata

    mesh_index_path = project_root / manifest["simulator_assets_dir"] / "object_meshes.json"
    write_json(
        mesh_index_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "output_dir": str(output_dir),
            "objects": reconstructed,
            "missing_objects": missing,
            "failed_objects": failed,
        },
    )
    manifest["artifacts"]["object_meshes"] = str(mesh_index_path)
    manifest["external_stages"]["mesh_generation"] = {
        "status": "mask_cloud_meshes_reconstructed" if reconstructed and not missing and not failed else "mask_cloud_meshes_partial" if reconstructed else "mask_cloud_meshes_failed",
        "notes": "Object meshes reconstructed directly from fused 3D mask point clouds.",
        "object_count": len(reconstructed),
        "missing_objects": missing,
        "failed_objects": sorted(failed),
    }
    save_manifest(project_root, manifest)
    print(f"Reconstructed {len(reconstructed)} object mesh(es). Index: {mesh_index_path}")
    if missing:
        print(f"Missing mask clouds: {', '.join(missing)}")
    if failed:
        print(f"Failed meshes: {', '.join(failed)}")
    return 0


def cmd_fuse_masks(args: argparse.Namespace) -> int:
    np = import_numpy()
    cv2 = import_cv2()
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)

    point_cloud_path = args.point_cloud or (project_root / manifest["scene"]["point_cloud"])
    camera_info_path = args.camera_info or (project_root / manifest["scene"]["camera_info"])
    mask_root = args.mask_root or (project_root / manifest["masks"]["mask_2d_dir"])
    mask_3d_dir = ensure_dir(project_root / manifest["masks"]["mask_3d_dir"])
    objects_dir = ensure_dir(project_root / manifest["objects_dir"])

    points, _colors = read_point_cloud(point_cloud_path)
    camera_info = load_camera_info(camera_info_path)
    extrinsics = camera_info["extrinsic"]
    records = scan_mask_records(mask_root)
    labels = load_object_labels(project_root, args.object_labels)

    object_ids = sorted({record.object_id for record in records})
    votes = {object_id: np.zeros(points.shape[0], dtype=np.uint16) for object_id in object_ids}
    frame_stats: dict[str, dict[str, dict[str, Any]]] = {object_id: {} for object_id in object_ids}
    skipped = []

    projection_cache: dict[str, tuple[Any, Any, Any, Any, Any]] = {}
    for record in records:
        if record.frame_id not in projection_cache:
            extrinsic = resolve_extrinsic(extrinsics, record.frame_id)
            if extrinsic is None:
                skipped.append({"mask": str(record.path), "reason": "missing_extrinsic"})
                continue
            w2c = world_to_camera_matrix(extrinsic, args.extrinsic_type)
            intrinsic = intrinsic_for_frame(camera_info, record.frame_id)
            inside, u, v, z = project_points(points, intrinsic, w2c)
            if args.occlusion_filter:
                visible, _zbuf = visibility_mask_from_projection(
                    inside,
                    u,
                    v,
                    z,
                    int(intrinsic["w"]),
                    int(intrinsic["h"]),
                    args.depth_tolerance,
                    args.relative_depth_tolerance,
                )
            else:
                visible = inside
            projection_cache[record.frame_id] = (inside, visible, u, v, z)

        inside, visible, u, v, _z = projection_cache[record.frame_id]
        mask = cv2.imread(str(record.path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            skipped.append({"mask": str(record.path), "reason": "failed_to_read"})
            continue
        positive = np.zeros(points.shape[0], dtype=bool)
        visible_idx = np.flatnonzero(visible)
        hit = mask[v[visible_idx], u[visible_idx]] >= args.mask_threshold
        positive[visible_idx[hit]] = True
        votes[record.object_id][positive] += 1
        frame_stats[record.object_id][record.frame_id] = {
            "mask": str(record.path),
            "mask_area": int((mask >= args.mask_threshold).sum()),
            "projected_points": int(inside.sum()),
            "visible_points": int(visible.sum()),
            "hit_points": int(positive.sum()),
            "occlusion_filter": bool(args.occlusion_filter),
        }

    object_summaries: dict[str, Any] = {}
    for object_id in object_ids:
        indices = np.flatnonzero(votes[object_id] >= args.min_votes).astype(np.int64)
        object_dir = ensure_dir(objects_dir / object_id)
        object_mask_dir = ensure_dir(mask_3d_dir / object_id)
        np.save(object_mask_dir / "point_indices.npy", indices)
        write_json(object_mask_dir / "point_indices.json", indices.tolist())
        bbox = bbox_for_points(points[indices])
        object_info = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "name": labels.get(object_id, {}).get("name", object_id.replace("_", " ")),
            "category": labels.get(object_id, {}).get("category", "unknown"),
            "description": labels.get(object_id, {}).get("description", ""),
            "point_count": int(indices.size),
            "bbox_3d": bbox,
            "mask_3d": {
                "point_indices_npy": str(object_mask_dir / "point_indices.npy"),
                "point_indices_json": str(object_mask_dir / "point_indices.json"),
                "min_votes": args.min_votes,
            },
            "frame_scores": frame_stats[object_id],
        }
        write_json(object_dir / "object.json", object_info)
        write_json(object_dir / "frame_scores.json", frame_stats[object_id])
        object_summaries[object_id] = object_info

    summary = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "point_cloud": str(point_cloud_path),
        "camera_info": str(camera_info_path),
        "mask_root": str(mask_root),
        "num_points": int(points.shape[0]),
        "num_masks": len(records),
        "objects": object_summaries,
        "skipped": skipped,
        "fusion": {
            "occlusion_filter": bool(args.occlusion_filter),
            "depth_tolerance": args.depth_tolerance,
            "relative_depth_tolerance": args.relative_depth_tolerance,
            "notes": "When enabled, per-frame z-buffer visibility keeps only points near the front surface at each projected pixel.",
        },
    }
    write_json(mask_3d_dir / "object_masks.json", summary)
    manifest["artifacts"]["object_masks_3d"] = str(mask_3d_dir / "object_masks.json")
    save_manifest(project_root, manifest)

    print(f"Fused {len(records)} 2D mask(s) onto {points.shape[0]} point(s).")
    print(f"Objects: {', '.join(object_ids)}")
    if skipped:
        print(f"Skipped {len(skipped)} mask(s); see {mask_3d_dir / 'object_masks.json'}")
    return 0


def find_frame_image(frames_dir: Path, frame_id: str) -> Path | None:
    stems = [frame_id, frame_stem(frame_id)]
    for stem in stems:
        for ext in IMAGE_EXTENSIONS:
            path = frames_dir / f"{stem}{ext}"
            if path.exists():
                return path
    return None


def sharpness_score(image_path: Path) -> float:
    cv2 = import_cv2()
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def bbox_from_mask(mask, threshold: int = 128) -> tuple[int, int, int, int] | None:
    np = import_numpy()
    ys, xs = np.where(mask >= threshold)
    if xs.size == 0 or ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def padded_square_bbox(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    padding_ratio: float,
    min_padding: int,
    square: bool,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    box_w = max(1, x1 - x0)
    box_h = max(1, y1 - y0)
    pad = max(int(round(max(box_w, box_h) * padding_ratio)), int(min_padding))
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    if square:
        side = max(box_w, box_h) + 2 * pad
        crop_w = crop_h = side
    else:
        crop_w = box_w + 2 * pad
        crop_h = box_h + 2 * pad
    nx0 = int(round(cx - crop_w / 2.0))
    ny0 = int(round(cy - crop_h / 2.0))
    nx1 = int(round(cx + crop_w / 2.0))
    ny1 = int(round(cy + crop_h / 2.0))

    if nx0 < 0:
        nx1 -= nx0
        nx0 = 0
    if ny0 < 0:
        ny1 -= ny0
        ny0 = 0
    if nx1 > width:
        nx0 -= nx1 - width
        nx1 = width
    if ny1 > height:
        ny0 -= ny1 - height
        ny1 = height
    nx0 = max(0, nx0)
    ny0 = max(0, ny0)
    nx1 = min(width, max(nx0 + 1, nx1))
    ny1 = min(height, max(ny0 + 1, ny1))
    return nx0, ny0, nx1, ny1


def write_object_crop(
    image_path: Path,
    mask_path: Path,
    output_path: Path,
    padding_ratio: float,
    min_padding: int,
    square: bool,
    transparent: bool,
    mask_threshold: int,
    background: tuple[int, int, int],
) -> dict[str, Any]:
    np = import_numpy()
    cv2 = import_cv2()
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Failed to read image: {image_path}")
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"Failed to read mask: {mask_path}")
    bbox = bbox_from_mask(mask, mask_threshold)
    if bbox is None:
        raise RuntimeError(f"Mask has no foreground pixels: {mask_path}")
    height, width = mask.shape[:2]
    crop_box = padded_square_bbox(bbox, width, height, padding_ratio, min_padding, square)
    x0, y0, x1, y1 = crop_box
    image_crop = image[y0:y1, x0:x1]
    mask_crop = mask[y0:y1, x0:x1]
    foreground = mask_crop >= mask_threshold
    ensure_dir(output_path.parent)

    if transparent:
        rgba = cv2.cvtColor(image_crop, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = np.where(foreground, 255, 0).astype(np.uint8)
        cv2.imwrite(str(output_path), rgba)
    else:
        canvas = np.full_like(image_crop, background[::-1], dtype=np.uint8)
        canvas[foreground] = image_crop[foreground]
        cv2.imwrite(str(output_path), canvas)

    return {
        "image": str(image_path),
        "mask": str(mask_path),
        "object_image": str(output_path),
        "bbox_xyxy": list(bbox),
        "crop_xyxy": list(crop_box),
        "transparent": transparent,
        "mask_area": int(foreground.sum()),
        "width": int(x1 - x0),
        "height": int(y1 - y0),
    }


def cmd_select_frames(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    frames_dir = args.frames_dir or (project_root / manifest["scene"]["frames_dir"])
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks first.")

    selected_summary: dict[str, Any] = {}
    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = obj["object_id"]
        frame_scores = obj.get("frame_scores", {})
        ranked = []
        for frame_id, stats in frame_scores.items():
            frame_path = find_frame_image(frames_dir, frame_id)
            if frame_path is None:
                continue
            sharpness = sharpness_score(frame_path) if args.use_sharpness else 0.0
            score = (
                float(stats.get("hit_points", 0)) * args.hit_weight
                + float(stats.get("mask_area", 0)) * args.area_weight
                + sharpness * args.sharpness_weight
            )
            ranked.append(
                {
                    "frame_id": frame_id,
                    "image": str(frame_path),
                    "score": score,
                    "sharpness": sharpness,
                    **stats,
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        selected = ranked[: args.top_k]
        selected_dir = ensure_dir(object_json.parent / "selected_frames")
        copied = []
        for item in selected:
            src = Path(item["image"])
            dst = selected_dir / f"{item['frame_id']}{src.suffix.lower()}"
            shutil.copy2(src, dst)
            copied.append({**item, "selected_image": str(dst)})
        obj["selected_frames"] = copied
        obj["primary_frame"] = copied[0] if copied else None
        write_json(object_json, obj)
        selected_summary[object_id] = copied

    out_path = project_root / "simulator_assets" / "selected_frames.json"
    write_json(out_path, selected_summary)
    manifest["artifacts"]["selected_frames"] = str(out_path)
    save_manifest(project_root, manifest)
    print(f"Selected frames for {len(selected_summary)} object(s). Wrote {out_path}")
    return 0


def cmd_prepare_object_images(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks/select-frames first.")

    prepared_summary: dict[str, Any] = {}
    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = slugify(obj["object_id"])
        selected = obj.get("selected_frames", [])
        if not selected:
            if args.skip_missing:
                continue
            raise RuntimeError(f"Object {object_id} has no selected frames. Run select-frames first.")

        out_dir = ensure_dir(object_json.parent / "object_images")
        prepared = []
        for rank, item in enumerate(selected[: args.top_k], start=1):
            image_path = Path(item.get("selected_image") or item.get("image", ""))
            mask_path = Path(item.get("mask", ""))
            if not image_path.exists() or not mask_path.exists():
                if args.skip_missing:
                    continue
                raise FileNotFoundError(f"Missing image or mask for {object_id} frame {item.get('frame_id')}")
            output_path = out_dir / f"{rank:02d}_{item.get('frame_id', rank)}.png"
            crop_info = write_object_crop(
                image_path=image_path,
                mask_path=mask_path,
                output_path=output_path,
                padding_ratio=args.padding_ratio,
                min_padding=args.min_padding,
                square=args.square,
                transparent=args.transparent,
                mask_threshold=args.mask_threshold,
                background=tuple(args.background),
            )
            prepared.append({**item, **crop_info, "rank": rank})

        if not prepared:
            if args.skip_missing:
                continue
            raise RuntimeError(f"No object images prepared for {object_id}.")

        reference_path = object_json.parent / "reference.png"
        shutil.copy2(prepared[0]["object_image"], reference_path)
        obj["object_images"] = prepared
        obj["primary_object_image"] = {**prepared[0], "reference_image": str(reference_path)}
        write_json(object_json, obj)
        prepared_summary[object_id] = obj["primary_object_image"]

    out_path = project_root / "simulator_assets" / "object_images.json"
    write_json(out_path, prepared_summary)
    manifest["artifacts"]["object_images"] = str(out_path)
    save_manifest(project_root, manifest)
    print(f"Prepared object crop/reference images for {len(prepared_summary)} object(s). Wrote {out_path}")
    return 0


def cmd_export_image_blaster(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    if args.use_object_crop and args.auto_prepare_crops:
        prep_args = argparse.Namespace(
            project_root=project_root,
            top_k=args.crop_top_k,
            padding_ratio=args.crop_padding_ratio,
            min_padding=args.crop_min_padding,
            square=True,
            transparent=args.transparent_crops,
            mask_threshold=args.mask_threshold,
            background=args.crop_background,
            skip_missing=True,
        )
        cmd_prepare_object_images(prep_args)
        manifest = load_manifest(project_root)

    world = slugify(args.world or manifest["scene_id"], fallback="world")
    image_blaster_root = args.image_blaster_root.resolve()
    objects_dir = project_root / manifest["objects_dir"]
    world_root = image_blaster_root / "worlds" / world
    ensure_dir(world_root / "source")
    ensure_dir(world_root / "output")

    exported_objects = []
    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = slugify(obj["object_id"])
        primary = obj.get("primary_frame") or {}
        primary_object_image = obj.get("primary_object_image") or {}
        selected_image = None
        if args.use_object_crop:
            selected_image = primary_object_image.get("reference_image") or primary_object_image.get("object_image")
        selected_image = selected_image or primary.get("selected_image") or primary.get("image")
        if not selected_image:
            if args.skip_missing:
                continue
            raise RuntimeError(f"Object {object_id} has no selected frame. Run select-frames first.")

        out_dir = ensure_dir(world_root / "output" / object_id)
        src = Path(selected_image)
        image_dst = out_dir / f"source{src.suffix.lower()}"
        shutil.copy2(src, image_dst)
        image_rel = rel_or_abs(image_dst, image_blaster_root)
        object_image_rels = [image_rel]
        evidence = [
            {
                "image": image_rel,
                "frame_id": primary_object_image.get("frame_id") or primary.get("frame_id"),
                "notes": "Selected and cropped by Video2Mesh object frame selector." if args.use_object_crop else "Selected by Video2Mesh object frame selector.",
            }
        ]
        if args.use_object_crop:
            for item in obj.get("object_images", []):
                object_image = item.get("object_image")
                if not object_image:
                    continue
                item_src = Path(object_image)
                if not item_src.exists():
                    continue
                item_dst = out_dir / "video2mesh_object_images" / f"{int(item.get('rank', len(object_image_rels))):02d}_{item.get('frame_id', item_src.stem)}{item_src.suffix.lower()}"
                ensure_dir(item_dst.parent)
                shutil.copy2(item_src, item_dst)
                item_rel = rel_or_abs(item_dst, image_blaster_root)
                if item_rel not in object_image_rels:
                    object_image_rels.append(item_rel)
                    evidence.append(
                        {
                            "image": item_rel,
                            "frame_id": item.get("frame_id"),
                            "mask": item.get("mask"),
                            "crop_xyxy": item.get("crop_xyxy"),
                            "notes": "Masked object crop from a Video2Mesh selected frame.",
                        }
                    )
        working_dir = rel_or_abs(out_dir, image_blaster_root)
        blaster_object = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "world": world,
            "object": {
                "id": object_id,
                "name": obj.get("name", object_id),
                "category": obj.get("category", "unknown"),
                "description": obj.get("description") or obj.get("name", object_id),
                "source_images": object_image_rels,
                "evidence": evidence,
                "generate_as_3d_object": True,
                "working_dir": working_dir,
                "video2mesh": {
                    "project_root": str(project_root),
                    "object_json": str(object_json),
                    "point_count": obj.get("point_count", 0),
                    "bbox_3d": obj.get("bbox_3d"),
                    "primary_frame": primary,
                    "primary_object_image": primary_object_image,
                },
            },
            "updated_by": "video2mesh",
        }
        write_json(out_dir / "object.json", blaster_object)
        exported_objects.append(
            {
                "id": object_id,
                "image_blaster_object_json": str(out_dir / "object.json"),
                "source_image": str(image_dst),
                "source_images": object_image_rels,
                "command": image_blaster_command(world, object_id, args.provider, args.reference_only),
            }
        )

    world_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "world": world,
        "video2mesh_project": str(project_root),
        "objects": exported_objects,
    }
    write_json(world_root / "source" / "video2mesh_manifest.json", world_manifest)
    sim_manifest_path = project_root / "simulator_assets" / "asset_manifest.json"
    write_json(sim_manifest_path, world_manifest)
    manifest["artifacts"]["image_blaster_world"] = str(world_root)
    manifest["artifacts"]["simulator_asset_manifest"] = str(sim_manifest_path)
    save_manifest(project_root, manifest)
    print(f"Exported {len(exported_objects)} object(s) to image-blaster world {world_root}")
    print(f"Simulator manifest: {sim_manifest_path}")
    return 0


def image_blaster_command(world: str, object_id: str, provider: str, reference_only: bool = False) -> str:
    parts = [
        "node",
        ".claude/scripts/asset-pipeline/generate-single-asset.mjs",
        "--world",
        shell_quote(world),
        "--object-id",
        shell_quote(object_id),
        "--provider",
        shell_quote(provider),
        "--image-edit-prompt",
        shell_quote("Create a clean single-object reference image on a plain background."),
    ]
    if reference_only:
        parts.append("--reference-only")
    return " ".join(parts)


def shell_quote(value: str) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def cmd_mesh_commands(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    world_root = Path(manifest.get("artifacts", {}).get("image_blaster_world", ""))
    if not world_root:
        raise RuntimeError("No image_blaster_world in manifest. Run export-image-blaster first.")
    image_blaster_root = args.image_blaster_root.resolve()
    world = world_root.name
    commands = []
    for object_json in sorted((world_root / "output").glob("*/object.json")):
        object_id = object_json.parent.name
        commands.append(image_blaster_command(world, object_id, args.provider, args.reference_only))

    script_path = project_root / "simulator_assets" / "mesh_generation_commands.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shell_quote(str(image_blaster_root))}",
        *commands,
        "",
    ]
    script_path.write_text("\n".join(lines), encoding="utf-8")
    script_path.chmod(0o755)
    print(f"Wrote {script_path}")
    for command in commands:
        print(command)

    if args.run:
        env = os.environ.copy()
        for command in commands:
            subprocess.run(command, cwd=image_blaster_root, shell=True, check=True, env=env)
    return 0


def external_mesh_template_values(project_root: Path, object_id: str, object_json: Path, job_path: Path, output_dir: Path, mesh_output: Path, obj: dict[str, Any]) -> dict[str, str]:
    selected_frames = obj.get("selected_frames") if isinstance(obj.get("selected_frames"), list) else []
    image_paths = [
        str(Path(item.get("selected_image") or item.get("image", "")).resolve())
        for item in selected_frames
        if item.get("selected_image") or item.get("image")
    ]
    object_images = obj.get("object_images") if isinstance(obj.get("object_images"), list) else []
    crop_paths = [
        str(Path(item.get("object_image", "")).resolve())
        for item in object_images
        if item.get("object_image")
    ]
    return {
        "project_root": str(project_root),
        "object_id": object_id,
        "object_json": str(object_json),
        "job_path": str(job_path),
        "output_dir": str(output_dir),
        "mesh_output": str(mesh_output),
        "primary_frame": image_paths[0] if image_paths else "",
        "primary_crop": crop_paths[0] if crop_paths else "",
        "image_paths": " ".join(shell_quote(path) for path in image_paths),
        "crop_paths": " ".join(shell_quote(path) for path in crop_paths),
    }


def cmd_prepare_multiview_mesh_jobs(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks/select-frames first.")
    output_root = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "multiview_mesh_jobs"))
    jobs_dir = ensure_dir(output_root / "jobs")
    mesh_root = ensure_dir(args.mesh_output_dir or (output_root / "meshes"))
    commands: list[str] = []
    jobs: dict[str, Any] = {}
    skipped: dict[str, str] = {}

    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        selected_frames = obj.get("selected_frames") if isinstance(obj.get("selected_frames"), list) else []
        object_images = obj.get("object_images") if isinstance(obj.get("object_images"), list) else []
        if not selected_frames and not object_images:
            skipped[object_id] = "missing selected_frames/object_images"
            if not args.skip_missing:
                raise RuntimeError(f"{object_id} has no selected frames or object crops. Run select-frames/prepare-object-images first.")
            continue

        object_job_dir = ensure_dir(mesh_root / object_id)
        mesh_output = object_job_dir / f"{object_id}.{args.mesh_format}"
        job_path = jobs_dir / f"{object_id}.json"
        mask_cloud_path = resolve_object_mask_cloud_path(obj, object_id, project_root, manifest)
        job = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "name": obj.get("name", object_id),
            "category": obj.get("category", "unknown"),
            "description": obj.get("description", ""),
            "object_json": str(object_json),
            "selected_frames": selected_frames[: args.max_frames if args.max_frames > 0 else None],
            "object_images": object_images[: args.max_frames if args.max_frames > 0 else None],
            "mask_3d_cloud": str(mask_cloud_path) if mask_cloud_path else None,
            "bbox_3d": obj.get("bbox_3d"),
            "output_dir": str(object_job_dir),
            "mesh_output": str(mesh_output),
            "recommended_inputs": {
                "single_image": "primary_crop or primary_frame",
                "multi_view": "selected_frames/object_images",
                "geometry_prior": "mask_3d_cloud and bbox_3d",
            },
            "notes": "Prepared job for an external single-image or multi-view object mesh reconstructor; no heavy model is run by this command.",
        }
        write_json(job_path, job)

        command = ""
        if args.command_template:
            values = external_mesh_template_values(project_root, object_id, object_json, job_path, object_job_dir, mesh_output, obj)
            command = command_from_template(args.command_template, values)
            commands.append(command)
        jobs[object_id] = {**job, "job_path": str(job_path), "command": command}

    script_path = output_root / "run_mesh_jobs.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        *commands,
        "",
    ]
    script_path.write_text("\n".join(lines), encoding="utf-8")
    script_path.chmod(0o755)

    manifest_path = output_root / "multiview_mesh_jobs.json"
    job_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "output_root": str(output_root),
        "mesh_root": str(mesh_root),
        "mesh_format": args.mesh_format,
        "jobs": jobs,
        "commands": commands,
        "script": str(script_path),
        "skipped": skipped,
        "template_variables": [
            "project_root",
            "object_id",
            "object_json",
            "job_path",
            "output_dir",
            "mesh_output",
            "primary_frame",
            "primary_crop",
            "image_paths",
            "crop_paths",
        ],
    }
    write_json(manifest_path, job_manifest)
    manifest.setdefault("artifacts", {})["multiview_mesh_jobs"] = str(manifest_path)
    manifest.setdefault("external_stages", {}).setdefault("mesh_generation", {})
    manifest["external_stages"]["mesh_generation"] = {
        "status": "external_mesh_jobs_prepared",
        "notes": "Prepared per-object mesh reconstruction jobs for external single-image or multi-view mesh tools.",
        "job_count": len(jobs),
        "skipped_objects": skipped,
    }
    save_manifest(project_root, manifest)

    print(f"Prepared {len(jobs)} external mesh job(s): {manifest_path}")
    print(f"Command script: {script_path}")
    if skipped:
        print(f"Skipped: {', '.join(sorted(skipped))}")
    if args.run and commands:
        for command in commands:
            print(command)
            subprocess.run(command, cwd=output_root, shell=True, check=True)
    return 0


def indexed_file_index(path: Path) -> int:
    match = re.match(r"^\.?(\d+)-", path.name)
    return int(match.group(1)) if match else -1


def is_model_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in MODEL_EXTENSIONS


def path_matches_object_id(path: Path, object_id: str | None) -> bool:
    if not object_id:
        return True
    object_slug = slugify(object_id)
    if not object_slug:
        return True
    return object_slug == slugify(path.parent.name) or object_slug in slugify(path.stem)


def metadata_path_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key in ("path", "local_path", "asset_path", "file", "filename"):
            if isinstance(value.get(key), str):
                values.append(value[key])
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(metadata_path_values(item))
        return values
    return []


def candidate_roots_for_metadata_path(object_dir: Path, max_depth: int = 8) -> list[Path]:
    roots = [object_dir]
    current = object_dir
    for _ in range(max_depth):
        parent = current.parent
        if parent == current:
            break
        roots.append(parent)
        current = parent
    return roots


def resolve_metadata_model_path(raw_value: str, object_dir: Path) -> Path | None:
    value = str(raw_value).strip()
    if not value or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        return None
    path = Path(value)
    candidates = [path] if path.is_absolute() else [root / path for root in candidate_roots_for_metadata_path(object_dir)]
    for candidate in candidates:
        if candidate.exists() and is_model_file(candidate):
            return candidate.resolve()
    return None


def metadata_model_file_candidates(object_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    for request_path in sorted(object_dir.glob(".*__model-request.json")):
        try:
            data = read_json(request_path)
        except Exception:
            continue
        for key in ("model_files", "output_files", "downloaded_files"):
            for raw_value in metadata_path_values(data.get(key)):
                resolved = resolve_metadata_model_path(raw_value, object_dir)
                if not resolved:
                    continue
                key_path = str(resolved)
                if key_path not in seen:
                    candidates.append(resolved)
                    seen.add(key_path)
    return candidates


def rank_model_candidates(candidates: list[Path]) -> Path | None:
    if not candidates:
        return None

    def sort_key(path: Path) -> tuple[int, int, float, str]:
        priority = MODEL_EXTENSION_PRIORITY.get(path.suffix.lower(), 99)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        return (indexed_file_index(path), -priority, mtime, path.name)

    return max(candidates, key=sort_key)


def find_latest_model_file(object_dir: Path, object_id: str | None = None) -> Path | None:
    if not object_dir.exists():
        return None

    object_dir_matches = bool(object_id) and slugify(object_dir.name) == slugify(object_id)
    groups = [
        [p.resolve() for p in object_dir.iterdir() if is_model_file(p)],
        metadata_model_file_candidates(object_dir),
        [path.resolve() for path in object_dir.rglob("*") if is_model_file(path)],
    ]
    seen: set[str] = set()
    for group in groups:
        candidates: list[Path] = []
        for candidate in group:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
        if object_id and not object_dir_matches:
            candidates = [path for path in candidates if path_matches_object_id(path, object_id)]
        selected = rank_model_candidates(candidates)
        if selected:
            return selected

    return None


def find_model_request_metadata(object_dir: Path, object_id: str, model_path: Path | None) -> dict[str, Any] | None:
    if not object_dir.exists():
        return None
    desired_index = indexed_file_index(model_path) if model_path else -1
    request_files = sorted(object_dir.glob(".*__model-request.json"))
    if not request_files:
        return None

    def request_key(path: Path) -> tuple[int, int, str]:
        index = indexed_file_index(path)
        exact = 1 if index == desired_index else 0
        return (exact, index, path.name)

    for request_path in sorted(request_files, key=request_key, reverse=True):
        try:
            data = read_json(request_path)
        except Exception:
            continue
        if object_id not in request_path.name and desired_index < 0:
            continue
        return {
            "path": str(request_path),
            "kind": data.get("kind"),
            "index": data.get("index", indexed_file_index(request_path)),
            "provider_slug": data.get("provider_slug"),
            "provider": data.get("provider") or data.get("endpoint"),
            "request_id": data.get("request_id"),
            "output_files": data.get("output_files", []),
            "downloaded_files": data.get("downloaded_files", []),
            "status": data.get("status"),
        }
    return None


def mesh_search_dirs_for_object(
    object_id: str,
    project_root: Path,
    manifest: dict[str, Any],
    image_blaster_root: Path,
    world: str | None,
    mesh_root: Path | None,
) -> list[Path]:
    search_dirs: list[Path] = []
    if mesh_root:
        object_mesh_dir = mesh_root / object_id
        search_dirs.append(object_mesh_dir if object_mesh_dir.exists() else mesh_root)

    world_root: Path | None = None
    if world:
        world_root = image_blaster_root / "worlds" / slugify(world, fallback="world")
    else:
        world_value = manifest.get("artifacts", {}).get("image_blaster_world")
        if world_value:
            world_root = Path(world_value)
            if not world_root.is_absolute():
                world_root = project_root / world_root

    if world_root:
        search_dirs.append(world_root / "output" / object_id)

    deduped = []
    seen = set()
    for item in search_dirs:
        key = str(item.resolve()) if item.exists() else str(item)
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def resolve_existing_path(path_value: str | None, project_root: Path) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    candidates = [path]
    if not path.is_absolute():
        candidates.append(project_root / path)
    else:
        parts = path.parts
        project_name = project_root.name
        if project_name in parts:
            idx = len(parts) - 1 - list(reversed(parts)).index(project_name)
            suffix = Path(*parts[idx + 1 :])
            candidates.append(project_root / suffix)
        repo_root = Path(__file__).resolve().parents[1]
        repo_name = repo_root.name
        if repo_name in parts:
            idx = len(parts) - 1 - list(reversed(parts)).index(repo_name)
            suffix = Path(*parts[idx + 1 :])
            candidates.append(repo_root / suffix)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def cmd_import_object_meshes(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks/select-frames first.")

    image_blaster_root = args.image_blaster_root.resolve()
    mesh_root = args.mesh_root.resolve() if args.mesh_root else None
    sim_objects_dir = ensure_dir(project_root / manifest["simulator_assets_dir"] / "objects")
    imported: dict[str, Any] = {}
    missing: list[str] = []

    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        if is_background_structure_record(obj):
            continue
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        selected_mesh: Path | None = None
        selected_dir: Path | None = None
        for candidate_dir in mesh_search_dirs_for_object(
            object_id,
            project_root,
            manifest,
            image_blaster_root,
            args.world,
            mesh_root,
        ):
            model = find_latest_model_file(candidate_dir, object_id)
            if model:
                selected_mesh = model.resolve()
                selected_dir = candidate_dir
                break

        if selected_mesh is None:
            missing.append(object_id)
            if not args.skip_missing:
                raise FileNotFoundError(f"No mesh artifact found for object {object_id}")
            continue

        asset_path = selected_mesh
        if args.copy_to_assets:
            dst = sim_objects_dir / object_id / selected_mesh.name
            if selected_mesh.resolve() != dst.resolve():
                asset_path = copy_or_link(selected_mesh, dst, args.mode)
            else:
                asset_path = dst

        metadata = find_model_request_metadata(selected_dir or selected_mesh.parent, object_id, selected_mesh)
        mesh_asset = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "source": "image_blaster" if selected_dir and "image-blaster" in str(selected_dir) else "external_mesh_root",
            "source_mesh": str(selected_mesh),
            "asset_path": str(asset_path),
            "format": selected_mesh.suffix.lower().lstrip("."),
            "request_metadata": metadata,
            "notes": "Imported generated object mesh for simulator asset export.",
        }
        obj["mesh_asset"] = mesh_asset
        write_json(object_json, obj)
        imported[object_id] = mesh_asset

    mesh_index_path = project_root / manifest["simulator_assets_dir"] / "object_meshes.json"
    write_json(
        mesh_index_path,
        {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "objects": imported,
            "missing_objects": missing,
        },
    )
    manifest["artifacts"]["object_meshes"] = str(mesh_index_path)
    manifest["external_stages"]["mesh_generation"] = {
        "status": "meshes_imported" if imported and not missing else "meshes_imported_with_missing" if imported else "mesh_import_missing",
        "notes": "Object meshes imported from image-blaster/external mesh directory into Video2Mesh object records.",
        "object_count": len(imported),
        "missing_objects": missing,
    }
    save_manifest(project_root, manifest)
    print(f"Imported {len(imported)} mesh asset(s). Index: {mesh_index_path}")
    if missing:
        print(f"Missing meshes: {', '.join(missing)}")
    return 0


def scaled_vector(values: Any, scale: float, fallback: list[float]) -> list[float]:
    if not isinstance(values, (list, tuple)) or len(values) != len(fallback):
        return fallback
    return [float(value) * scale for value in values]


def multiply_vector(values: Any, factor: float, count: int = 3, fallback: float = 0.0) -> list[float]:
    if not isinstance(values, (list, tuple)):
        values = [fallback] * count
    padded = list(values)[:count] + [fallback] * max(0, count - len(values))
    return [float(value) * float(factor) for value in padded[:count]]


def is_background_structure_record(obj: dict[str, Any]) -> bool:
    return obj.get("asset_role") == "background_structure"


def cmd_export_simulator_assets(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks first.")

    sim_dir = ensure_dir(project_root / manifest["simulator_assets_dir"])
    sim_objects_dir = ensure_dir(sim_dir / "objects")
    semantic_manifest_path = resolve_existing_path(manifest.get("artifacts", {}).get("semantic_splats_manifest"), project_root)
    semantic_manifest = read_json(semantic_manifest_path) if semantic_manifest_path and semantic_manifest_path.exists() else {}
    semantic_ids = semantic_manifest.get("object_id_to_semantic", {}) if isinstance(semantic_manifest, dict) else {}
    semantic_splats_ply = args.semantic_splats_ply or resolve_existing_path(manifest.get("artifacts", {}).get("semantic_splats_ply"), project_root)

    object_assets: list[dict[str, Any]] = []
    missing_meshes: list[str] = []
    for index, object_json in enumerate(sorted(objects_dir.glob("*/object.json")), start=1):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        asset_role = obj.get("asset_role", "object")
        is_background_structure = asset_role == "background_structure"
        semantic_id = int(semantic_ids.get(object_id, index))
        bbox = obj.get("bbox_3d") or {}
        mesh_asset = obj.get("mesh_asset") or {}
        source_mesh = resolve_existing_path(mesh_asset.get("asset_path") or mesh_asset.get("source_mesh"), project_root)
        exported_mesh: dict[str, Any] | None = None
        mesh_qa: dict[str, Any] | None = None
        if source_mesh and source_mesh.exists():
            mesh_path = source_mesh
            source_mesh_summary = summarize_triangle_mesh(source_mesh)
            mesh_qa = {
                "source_mesh": source_mesh_summary,
                "source_to_mask_alignment": mesh_alignment_summary(bbox, source_mesh_summary),
                "source_coordinate_frame": mesh_asset_coordinate_frame(mesh_asset),
            }
            mesh_export_normalized = False
            if args.copy_meshes:
                dst = sim_objects_dir / object_id / source_mesh.name
                if mesh_qa["source_coordinate_frame"] == "video2mesh_scene" and bbox.get("center"):
                    local_suffix = source_mesh.suffix.lower() or f".{mesh_asset.get('format', 'obj')}"
                    dst = sim_objects_dir / object_id / f"{source_mesh.stem}_local{local_suffix}"
                    center_unscaled = scaled_vector(bbox.get("center"), 1.0, [0.0, 0.0, 0.0])
                    local_summary = transform_triangle_mesh_file(
                        source_mesh,
                        dst,
                        translation=[-float(value) for value in center_unscaled],
                        scale=args.scene_scale,
                        write_ascii=args.ascii_meshes,
                    )
                    mesh_path = dst
                    mesh_qa["exported_mesh"] = local_summary
                    mesh_qa["localization"] = {
                        "applied": True,
                        "translation": [-float(value) for value in center_unscaled],
                        "scale": args.scene_scale,
                        "reason": "source mesh was in video2mesh_scene coordinates; exported mesh is object-local around bbox center",
                    }
                    mesh_export_normalized = True
                elif args.fit_object_local_meshes_to_bbox and mesh_qa["source_coordinate_frame"] == "object_local" and bbox.get("center") and bbox.get("size"):
                    local_suffix = source_mesh.suffix.lower() or f".{mesh_asset.get('format', 'obj')}"
                    dst = sim_objects_dir / object_id / f"{source_mesh.stem}_bboxfit{local_suffix}"
                    try:
                        fit_summary, fit_detail = fit_object_local_mesh_to_bbox(
                            source_mesh,
                            dst,
                            source_mesh_summary,
                            bbox,
                            args.scene_scale,
                            args.fit_axis,
                            write_ascii=args.ascii_meshes,
                        )
                        mesh_path = dst
                        mesh_qa["exported_mesh"] = fit_summary
                        mesh_qa["fit_to_mask_bbox"] = fit_detail
                        mesh_qa["localization"] = {
                            "applied": True,
                            "translation": [-float(value) for value in fit_detail["source_bbox"].get("center", [0.0, 0.0, 0.0])[:3]],
                            "scale": fit_detail["uniform_scale"],
                            "reason": "object-local mesh was centered and uniformly scaled to the fused 3D mask bbox",
                        }
                        mesh_export_normalized = True
                    except Exception as exc:
                        fallback_dst = sim_objects_dir / object_id / source_mesh.name
                        mesh_qa["fit_to_mask_bbox"] = {
                            "applied": False,
                            "error": str(exc),
                            "reason": "bbox-fit failed; falling back to object-local mesh copy",
                        }
                        if source_mesh.resolve() != fallback_dst.resolve():
                            mesh_path = copy_or_link(source_mesh, fallback_dst, args.mode)
                        else:
                            mesh_path = fallback_dst
                        mesh_qa["exported_mesh"] = summarize_triangle_mesh(mesh_path)
                        mesh_qa["localization"] = {
                            "applied": False,
                            "scale": args.scene_scale,
                            "reason": "source mesh treated as object-local after bbox-fit fallback",
                        }
                elif source_mesh.resolve() != dst.resolve():
                    mesh_path = copy_or_link(source_mesh, dst, args.mode)
                    mesh_qa["exported_mesh"] = summarize_triangle_mesh(mesh_path)
                    mesh_qa["localization"] = {
                        "applied": False,
                        "scale": args.scene_scale,
                        "reason": "source mesh treated as object-local",
                    }
                else:
                    mesh_path = dst
                    mesh_qa["exported_mesh"] = summarize_triangle_mesh(mesh_path)
                    mesh_qa["localization"] = {
                        "applied": False,
                        "scale": args.scene_scale,
                        "reason": "source mesh already at destination and treated as object-local",
                    }
            else:
                mesh_qa["exported_mesh"] = source_mesh_summary
                mesh_qa["localization"] = {
                    "applied": False,
                    "scale": args.scene_scale,
                    "reason": "mesh copying/localization disabled by --no-copy-meshes",
                }
            exported_mesh = {
                "path": str(mesh_path),
                "source_path": str(source_mesh),
                "format": mesh_path.suffix.lower().lstrip("."),
                "source_coordinate_frame": mesh_qa["source_coordinate_frame"],
                "coordinate_frame": "object_local" if mesh_export_normalized else mesh_qa["source_coordinate_frame"],
                "alignment_status": "normalized_to_3d_mask_bbox" if mesh_qa.get("fit_to_mask_bbox", {}).get("applied") else "localized_from_3d_mask_bbox" if mesh_export_normalized else "estimated_from_3d_mask_bbox",
            }
        else:
            if not is_background_structure:
                missing_meshes.append(object_id)

        center = scaled_vector(bbox.get("center"), args.scene_scale, [0.0, 0.0, 0.0])
        size = scaled_vector(bbox.get("size"), args.scene_scale, [0.0, 0.0, 0.0])
        mesh_normalized = bool(exported_mesh and exported_mesh.get("alignment_status") in {"localized_from_3d_mask_bbox", "normalized_to_3d_mask_bbox"})
        mesh_coordinate_frame = exported_mesh.get("coordinate_frame") if isinstance(exported_mesh, dict) else ""
        pose_position = center
        if exported_mesh and mesh_coordinate_frame == "video2mesh_scene" and not mesh_normalized:
            pose_position = [0.0, 0.0, 0.0]
        pose_scale = [1.0, 1.0, 1.0] if mesh_normalized else [args.scene_scale, args.scene_scale, args.scene_scale]
        asset = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "object_id": object_id,
            "asset_role": asset_role,
            "semantic_id": semantic_id,
            "name": obj.get("name", object_id),
            "category": obj.get("category", "unknown"),
            "description": obj.get("description", ""),
            "status": "background_structure" if is_background_structure and not exported_mesh else "ready" if exported_mesh else "missing_mesh",
            "mesh": exported_mesh,
            "pose": {
                "position": pose_position,
                "rotation_xyzw": [0.0, 0.0, 0.0, 1.0],
                "scale": pose_scale,
                "bbox_size": size,
                "bbox_3d": bbox,
            },
            "physics": {
                "body_type": "static" if is_background_structure else args.body_type,
                "collider": "box" if is_background_structure else args.collider if exported_mesh else "none",
                "mass_kg": None,
                "material": None,
                "notes": "Physics values are placeholders; validate mass, friction, and collider before simulation.",
            },
            "masks": {
                "mask_3d": obj.get("mask_3d"),
                "mask_3d_cloud": obj.get("mask_3d_cloud"),
                "point_count": obj.get("point_count", 0),
            },
            "background_structure": obj.get("background_structure") if is_background_structure else None,
            "quality": {
                "mesh": mesh_qa,
            },
            "selected_frames": obj.get("selected_frames", []),
            "primary_frame": obj.get("primary_frame"),
            "source_object_json": str(object_json),
        }
        object_asset_path = sim_objects_dir / object_id / "object_asset.json"
        write_json(object_asset_path, asset)
        asset["object_asset_json"] = str(object_asset_path)
        object_assets.append(asset)

    bundle_path = sim_dir / "simulator_asset_bundle.json"
    bundle = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "scene_id": manifest.get("scene_id"),
        "project_root": str(project_root),
        "coordinate_system": {
            "frame": "video2mesh_scene",
            "scale_to_meters": args.scene_scale,
            "up_axis": "unknown",
            "notes": "Scale/up-axis come from reconstruction; calibrate them before physics-critical simulation.",
        },
        "scene_assets": {
            "frames_dir": str(project_root / manifest["scene"]["frames_dir"]),
            "camera_info": str(project_root / manifest["scene"]["camera_info"]),
            "point_cloud": str(project_root / manifest["scene"]["point_cloud"]),
            "scene_3dgs": str(project_root / manifest["scene"]["scene_3dgs"]),
            "semantic_splats_ply": str(semantic_splats_ply) if semantic_splats_ply else None,
            "semantic_splats_manifest": str(semantic_manifest_path) if semantic_manifest_path else None,
        },
        "objects": object_assets,
        "missing_mesh_objects": missing_meshes,
        "notes": [
            "Object meshes are generated from selected frames and positioned by 3D mask bbox centers.",
            "For simulator use, replace placeholder physics fields with task-specific mass, friction, and collision settings.",
        ],
    }
    write_json(bundle_path, bundle)
    manifest["artifacts"]["simulator_asset_bundle"] = str(bundle_path)
    manifest["external_stages"]["mesh_generation"] = {
        "status": "simulator_assets_exported" if not missing_meshes else "simulator_assets_exported_with_missing_meshes",
        "notes": "Final object-centric simulator asset manifest exported.",
        "object_count": len(object_assets),
        "missing_mesh_objects": missing_meshes,
    }
    save_manifest(project_root, manifest)
    print(f"Wrote simulator asset bundle: {bundle_path}")
    print(f"Objects: {len(object_assets)}; missing meshes: {len(missing_meshes)}")
    return 0


def object_longest_bbox_dimension(obj: dict[str, Any]) -> float | None:
    pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
    bbox_size = pose.get("bbox_size")
    if not isinstance(bbox_size, (list, tuple)) or len(bbox_size) < 3:
        return None
    try:
        return max(abs(float(value)) for value in bbox_size[:3])
    except Exception:
        return None


def resolve_reference_scene_length(bundle: dict[str, Any], object_id: str | None, reference_axis: str) -> float | None:
    if not object_id:
        return None
    axis = str(reference_axis).lower()
    axis_to_index = {"x": 0, "y": 1, "z": 2}
    for obj in bundle.get("objects", []):
        if not isinstance(obj, dict) or slugify(obj.get("object_id", "")) != slugify(object_id):
            continue
        pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
        bbox_size = pose.get("bbox_size")
        if not isinstance(bbox_size, (list, tuple)) or len(bbox_size) < 3:
            return None
        try:
            if axis == "longest":
                return max(abs(float(value)) for value in bbox_size[:3])
            if axis in axis_to_index:
                return abs(float(bbox_size[axis_to_index[axis]]))
        except Exception:
            return None
    return None


def physics_defaults_for_asset(obj: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    asset_role = obj.get("asset_role", "object")
    category = str(obj.get("category") or "").strip().lower()
    pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
    bbox_size = pose.get("bbox_size") if isinstance(pose.get("bbox_size"), list) else [0.0, 0.0, 0.0]
    dimensions = [max(float(value), 0.0) for value in (bbox_size[:3] if len(bbox_size) >= 3 else [0.0, 0.0, 0.0])]
    volume = dimensions[0] * dimensions[1] * dimensions[2]
    is_background_structure = asset_role == "background_structure"

    if is_background_structure:
        body_type = "static"
        collider = "box"
        mass = None
    else:
        body_type = args.body_type
        collider = args.collider
        estimated_mass = volume * float(args.default_density_kg_m3)
        mass = min(max(estimated_mass, args.min_mass_kg), args.max_mass_kg)

    material = args.default_material
    if category in {"floor", "wall", "ceiling"}:
        material = category
    elif category in {"chair", "table", "desk", "cabinet", "bookshelf"}:
        material = "rigid_furniture"

    return {
        "body_type": body_type,
        "collider": collider,
        "mass_kg": mass,
        "material": {
            "name": material,
            "friction": [float(args.friction), float(args.torsional_friction), float(args.rolling_friction)],
            "restitution": float(args.restitution),
        },
        "estimated": True,
        "estimation": {
            "method": "bbox_volume_density" if not is_background_structure else "static_background_structure",
            "bbox_size_m": dimensions,
            "bbox_volume_m3": volume,
            "density_kg_m3": float(args.default_density_kg_m3) if not is_background_structure else None,
            "mass_clamp_kg": [float(args.min_mass_kg), float(args.max_mass_kg)] if not is_background_structure else None,
        },
        "notes": "Estimated simulator physics defaults; replace with measured task-specific values before physics-critical use.",
    }


def cmd_calibrate_simulator_assets(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    bundle_path = simulator_bundle_path(project_root, manifest, args.bundle)
    if not bundle_path.exists():
        raise FileNotFoundError(f"Missing simulator asset bundle: {bundle_path}. Run export-simulator-assets first.")
    bundle = read_json(bundle_path)
    coordinate_system = bundle.get("coordinate_system") if isinstance(bundle.get("coordinate_system"), dict) else {}

    old_scale = float(coordinate_system.get("scale_to_meters") or 1.0)
    scale_to_meters = args.scale_to_meters
    calibration_method = "manual_scale_to_meters" if scale_to_meters is not None else "assumption"
    reference_scene_length = None
    if scale_to_meters is None and args.reference_object and args.reference_length_m:
        reference_scene_length = resolve_reference_scene_length(bundle, args.reference_object, args.reference_axis)
        if not reference_scene_length or reference_scene_length <= 0:
            raise ValueError(f"Could not derive reference scene length for object {args.reference_object!r} on axis {args.reference_axis!r}.")
        scale_to_meters = float(args.reference_length_m) / float(reference_scene_length)
        calibration_method = "reference_object_bbox"
    if scale_to_meters is None:
        scale_to_meters = old_scale

    scale_ratio = float(scale_to_meters) / max(old_scale, 1e-12)
    scale_calibrated = bool(args.scale_calibrated or calibration_method == "reference_object_bbox")
    calibration = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "method": calibration_method,
        "scale_to_meters": float(scale_to_meters),
        "previous_scale_to_meters": old_scale,
        "scale_ratio_applied_to_bundle": scale_ratio,
        "scale_calibrated": scale_calibrated,
        "up_axis": args.up_axis,
        "reference_object": args.reference_object,
        "reference_axis": args.reference_axis if args.reference_object else None,
        "reference_scene_length": reference_scene_length,
        "reference_length_m": args.reference_length_m,
        "timestamp": int(time.time()),
        "notes": args.notes or (
            "Scale derived from a reference object bbox." if calibration_method == "reference_object_bbox" else
            "Manual/assumed simulator calibration; verify with real measurements before physics-critical use."
        ),
    }

    coordinate_system.update(
        {
            "frame": coordinate_system.get("frame", "video2mesh_scene"),
            "scale_to_meters": float(scale_to_meters),
            "scale_calibrated": scale_calibrated,
            "calibrated": scale_calibrated,
            "up_axis": args.up_axis,
            "calibration": calibration,
            "notes": "Scale/up-axis were updated by calibrate-simulator-assets; physics defaults may still be estimates.",
        }
    )
    bundle["coordinate_system"] = coordinate_system

    updated_objects = 0
    for obj in bundle.get("objects", []):
        if not isinstance(obj, dict):
            continue
        pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
        if args.rescale_existing_pose and abs(scale_ratio - 1.0) > 1e-12:
            pose["position"] = multiply_vector(pose.get("position"), scale_ratio, 3, 0.0)
            pose["bbox_size"] = multiply_vector(pose.get("bbox_size"), scale_ratio, 3, 0.0)
            pose["scale"] = multiply_vector(pose.get("scale"), scale_ratio, 3, 1.0)
        pose["units"] = "meters"
        pose["scale_to_meters"] = float(scale_to_meters)
        obj["pose"] = pose

        if args.estimate_physics:
            existing_physics = obj.get("physics") if isinstance(obj.get("physics"), dict) else {}
            defaults = physics_defaults_for_asset(obj, args)
            if args.overwrite_physics:
                obj["physics"] = defaults
            else:
                merged = dict(defaults)
                merged.update({key: value for key, value in existing_physics.items() if value not in (None, "", [], {})})
                if isinstance(existing_physics.get("material"), dict) and isinstance(defaults.get("material"), dict):
                    material = dict(defaults["material"])
                    material.update(existing_physics["material"])
                    merged["material"] = material
                obj["physics"] = merged

        object_asset_path = resolve_existing_path(obj.get("object_asset_json"), project_root)
        if object_asset_path and object_asset_path.exists():
            object_asset = read_json(object_asset_path)
            object_asset["coordinate_system"] = coordinate_system
            object_asset["pose"] = obj.get("pose")
            object_asset["physics"] = obj.get("physics")
            write_json(object_asset_path, object_asset)
        updated_objects += 1

    bundle.setdefault("notes", [])
    if isinstance(bundle["notes"], list):
        bundle["notes"].append("Simulator scale/up-axis/physics defaults updated by calibrate-simulator-assets.")
    bundle["simulator_calibration"] = calibration
    write_json(bundle_path, bundle)

    calibration_path = project_root / manifest["simulator_assets_dir"] / "simulator_calibration.json"
    write_json(
        calibration_path,
        {
            **calibration,
            "project_root": str(project_root),
            "bundle": str(bundle_path),
            "updated_object_count": updated_objects,
            "estimate_physics": bool(args.estimate_physics),
        },
    )
    manifest.setdefault("artifacts", {})["simulator_calibration"] = str(calibration_path)
    manifest.setdefault("external_stages", {})["simulator_calibration"] = {
        "status": "simulator_assets_calibrated" if scale_calibrated else "simulator_assets_assumed",
        "notes": calibration["notes"],
        "scale_to_meters": float(scale_to_meters),
        "up_axis": args.up_axis,
        "estimate_physics": bool(args.estimate_physics),
    }
    save_manifest(project_root, manifest)

    print(f"Calibrated simulator bundle: {bundle_path}")
    print(f"Scale to meters: {scale_to_meters:.8g}; up_axis={args.up_axis}; scale_calibrated={scale_calibrated}")
    print(f"Updated objects: {updated_objects}; calibration: {calibration_path}")
    return 0


def simulator_bundle_path(project_root: Path, manifest: dict[str, Any], explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    bundle = resolve_existing_path(manifest.get("artifacts", {}).get("simulator_asset_bundle"), project_root)
    if bundle and bundle.exists():
        return bundle
    return project_root / manifest["simulator_assets_dir"] / "simulator_asset_bundle.json"


def adapter_rel_path(path_value: str | None, base: Path) -> str | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute():
        try:
            return os.path.relpath(path.resolve(), base.resolve())
        except Exception:
            return str(path)
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path)


def fmt_vec(values: Any, count: int = 3, fallback: float = 0.0) -> str:
    if not isinstance(values, (list, tuple)):
        values = [fallback] * count
    padded = list(values)[:count] + [fallback] * max(0, count - len(values))
    return " ".join(f"{float(value):.6g}" for value in padded[:count])


def adapter_mesh_path(mesh_path: str | None, output_root: Path, object_id: str, args: argparse.Namespace, project_root: Path) -> str | None:
    if not mesh_path:
        return None
    src = resolve_existing_path(mesh_path, project_root) or Path(mesh_path)
    if not src.exists():
        return mesh_path
    if not args.copy_assets:
        return str(src)
    dst = output_root / "assets" / object_id / src.name
    if src.resolve() != dst.resolve():
        copy_or_link(src, dst, args.mode)
    return str(dst)


def write_mujoco_adapter(bundle: dict[str, Any], output_dir: Path, output_root: Path, project_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    xml_path = output_dir / "scene.xml"
    manifest_path = output_dir / "mujoco_adapter.json"
    ensure_dir(output_dir)
    assets = []
    bodies = []
    objects = []
    for obj in bundle.get("objects", []):
        object_id = slugify(obj.get("object_id", "object"))
        mesh = obj.get("mesh") if isinstance(obj.get("mesh"), dict) else None
        pose = obj.get("pose") if isinstance(obj.get("pose"), dict) else {}
        position = pose.get("position", [0.0, 0.0, 0.0])
        bbox_size = pose.get("bbox_size", [0.05, 0.05, 0.05])
        body_type = (obj.get("physics") or {}).get("body_type") or args.body_type
        mesh_path = mesh.get("path") if mesh else None
        packaged_mesh_path = adapter_mesh_path(mesh_path, output_root, object_id, args, project_root)
        mesh_rel = adapter_rel_path(packaged_mesh_path, output_dir) if packaged_mesh_path else None
        mesh_name = f"{object_id}_mesh"
        geom_attrs = ""
        mesh_scale = pose.get("scale") if isinstance(pose.get("scale"), list) else None
        mesh_scale_attr = f' scale="{fmt_vec(mesh_scale, 3, 1.0)}"' if mesh_scale else ""
        if mesh_rel:
            assets.append(f'    <mesh name="{html.escape(mesh_name)}" file="{html.escape(mesh_rel)}"{mesh_scale_attr}/>')
            geom_attrs = f'type="mesh" mesh="{html.escape(mesh_name)}"'
        else:
            half = []
            for value in (bbox_size if isinstance(bbox_size, list) else [0.05, 0.05, 0.05])[:3]:
                half.append(max(float(value) * 0.5, 0.01))
            geom_attrs = f'type="box" size="{fmt_vec(half)}"'
        friction = (((obj.get("physics") or {}).get("material") or {}).get("friction")) if isinstance((obj.get("physics") or {}).get("material"), dict) else None
        friction_attr = f' friction="{fmt_vec(friction, 3, 1.0)}"' if isinstance(friction, list) else ""
        mass_attr = ""
        if body_type == "dynamic":
            mass = (obj.get("physics") or {}).get("mass_kg") or args.default_mass
            mass_attr = f' mass="{float(mass):.6g}"'
        bodies.append(
            f'    <body name="{html.escape(object_id)}" pos="{fmt_vec(position)}">\n'
            f'      <geom name="{html.escape(object_id)}_geom" {geom_attrs}{mass_attr}{friction_attr}/>\n'
            f'    </body>'
        )
        objects.append(
            {
                "object_id": object_id,
                "mesh": mesh_path,
                "packaged_mesh": packaged_mesh_path,
                "mesh_format": (mesh or {}).get("format"),
                "pose": pose,
                "body_type": body_type,
                "notes": "MuJoCo mesh import may require OBJ/STL conversion depending on runtime/version.",
            }
        )

    xml = [
        '<mujoco model="video2mesh_scene">',
        "  <compiler angle=\"radian\" meshdir=\".\"/>",
        "  <option timestep=\"0.002\"/>",
        "  <asset>",
        *assets,
        "  </asset>",
        "  <worldbody>",
        '    <light name="key" pos="0 -3 4" dir="0 1 -1"/>',
        '    <geom name="ground" type="plane" size="5 5 0.1" rgba="0.8 0.8 0.8 1"/>',
        *bodies,
        "  </worldbody>",
        "</mujoco>",
        "",
    ]
    xml_path.write_text("\n".join(xml), encoding="utf-8")
    manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "format": "mujoco",
        "adapter_file": str(xml_path),
        "source_bundle": str(args.bundle) if args.bundle else bundle.get("source_bundle"),
        "objects": objects,
        "notes": [
            "This is a simulator adapter skeleton generated from Video2Mesh object poses and mesh paths.",
            "Verify scale, up-axis, collision geometry, material, and mass before physics-critical simulation.",
        ],
    }
    write_json(manifest_path, manifest)
    return {"adapter_file": str(xml_path), "adapter_manifest": str(manifest_path), "object_count": len(objects)}


def write_json_simulator_adapter(format_name: str, bundle: dict[str, Any], output_dir: Path, output_root: Path, project_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    ensure_dir(output_dir)
    out_path = output_dir / f"{format_name}_adapter.json"
    objects = []
    for obj in bundle.get("objects", []):
        object_id = slugify(obj.get("object_id", "object"))
        mesh = obj.get("mesh") if isinstance(obj.get("mesh"), dict) else None
        mesh_path = mesh.get("path") if mesh else None
        packaged_mesh_path = adapter_mesh_path(mesh_path, output_root, object_id, args, project_root)
        objects.append(
            {
                "object_id": obj.get("object_id"),
                "name": obj.get("name"),
                "category": obj.get("category"),
                "semantic_id": obj.get("semantic_id"),
                "mesh_path": mesh_path,
                "packaged_mesh_path": packaged_mesh_path,
                "packaged_mesh_relative": adapter_rel_path(packaged_mesh_path, output_dir) if packaged_mesh_path else None,
                "mesh_format": mesh.get("format") if mesh else None,
                "position": (obj.get("pose") or {}).get("position"),
                "rotation_xyzw": (obj.get("pose") or {}).get("rotation_xyzw"),
                "scale": (obj.get("pose") or {}).get("scale"),
                "bbox_size": (obj.get("pose") or {}).get("bbox_size"),
                "physics": obj.get("physics"),
                "mask_3d_cloud": (obj.get("masks") or {}).get("mask_3d_cloud"),
                "selected_frames": obj.get("selected_frames", []),
            }
        )
    adapter = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "format": format_name,
        "scene_id": bundle.get("scene_id"),
        "coordinate_system": bundle.get("coordinate_system"),
        "scene_assets": bundle.get("scene_assets"),
        "objects": objects,
        "import_notes": {
            "isaac": "Use mesh_path as the source mesh for USD/Isaac import; verify meters, up-axis, collision approximation, and rigid body properties.",
            "unity": "Use mesh_path as an imported model path or convert to FBX/GLB; create prefabs with position/rotation/scale and semantic metadata.",
        }.get(format_name, "Generic simulator adapter manifest."),
    }
    write_json(out_path, adapter)
    return {"adapter_file": str(out_path), "object_count": len(objects)}


def cmd_export_simulator_adapter(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    bundle_path = simulator_bundle_path(project_root, manifest, args.bundle)
    if not bundle_path.exists():
        raise FileNotFoundError(f"Missing simulator asset bundle: {bundle_path}. Run export-simulator-assets first.")
    bundle = read_json(bundle_path)
    bundle["source_bundle"] = str(bundle_path)
    output_root = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "adapters"))
    formats = args.format
    results: dict[str, Any] = {}
    for format_name in formats:
        format_dir = ensure_dir(output_root / format_name)
        if format_name == "mujoco":
            results[format_name] = write_mujoco_adapter(bundle, format_dir, output_root, project_root, args)
        else:
            results[format_name] = write_json_simulator_adapter(format_name, bundle, format_dir, output_root, project_root, args)

    adapter_manifest_path = output_root / "simulator_adapters.json"
    adapter_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "source_bundle": str(bundle_path),
        "formats": results,
        "notes": "Adapters are import manifests/skeletons. Calibrate scale, up-axis, collisions, and physics parameters in the target simulator.",
    }
    write_json(adapter_manifest_path, adapter_manifest)
    manifest["artifacts"]["simulator_adapters"] = str(adapter_manifest_path)
    save_manifest(project_root, manifest)
    print(f"Simulator adapters: {adapter_manifest_path}")
    for format_name, result in results.items():
        print(f"- {format_name}: {result.get('adapter_file')} ({result.get('object_count')} object(s))")
    return 0


def sceneverse_category_id(category: str, fallback: int) -> int:
    normalized = str(category or "unknown").strip().lower().replace("_", " ")
    return int(SCANNET20_LABEL_IDS.get(normalized, fallback))


def load_category_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"Category map must be a JSON object: {path}")
    return {
        str(key).strip().lower().replace("_", " "): str(value).strip().lower().replace("_", " ")
        for key, value in data.items()
    }


def sceneverse_category(raw_category: Any, category_map: dict[str, str], default_category: str | None) -> str:
    normalized = str(raw_category or "unknown").strip().lower().replace("_", " ")
    mapped = category_map.get(normalized)
    if mapped:
        return mapped
    if normalized in SCANNET20_LABEL_IDS:
        return normalized
    if default_category:
        return str(default_category).strip().lower().replace("_", " ")
    return normalized


def frame_ids_from_project(project_root: Path, manifest: dict[str, Any]) -> list[int | str]:
    frames_dir = project_root / manifest["scene"]["frames_dir"]
    frame_ids: list[int | str] = []
    if frames_dir.exists():
        for frame_path in sorted((p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS), key=frame_sort_key):
            frame_ids.append(int(frame_path.stem) if frame_path.stem.isdigit() else frame_path.stem)
    return frame_ids


def cmd_export_svpp_metadata(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    scene_id = slugify(args.scene_id or manifest.get("scene_id") or project_root.name, fallback="scene")
    output_root = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "svpp" / scene_id))
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks first.")
    category_map = load_category_map(args.category_map)

    point_cloud = resolve_project_path(manifest["scene"]["point_cloud"], project_root)
    camera_info = resolve_project_path(manifest["scene"]["camera_info"], project_root)
    if not point_cloud.exists():
        raise FileNotFoundError(f"Missing point cloud: {point_cloud}")

    mesh_dst = output_root / "mesh.ply"
    camera_dst = output_root / "camera_info.json"
    if point_cloud.resolve() == mesh_dst.resolve():
        pass
    elif args.mode == "symlink":
        copy_or_link(point_cloud, mesh_dst, "symlink")
    else:
        copy_or_link(point_cloud, mesh_dst, "copy")

    if camera_info.exists() and camera_info.resolve() != camera_dst.resolve():
        if args.mode == "symlink":
            copy_or_link(camera_info, camera_dst, "symlink")
        else:
            copy_or_link(camera_info, camera_dst, "copy")

    metadata: dict[str, Any] = {}
    instances = []
    for instance_index, object_json in enumerate(sorted(objects_dir.glob("*/object.json"))):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        raw_category = obj.get("category") or obj.get("name") or object_id
        category = sceneverse_category(raw_category, category_map, args.default_category)
        mask_3d = obj.get("mask_3d") if isinstance(obj.get("mask_3d"), dict) else {}
        index_path = resolve_existing_path(mask_3d.get("point_indices_json") or mask_3d.get("point_indices_npy"), project_root)
        if not index_path or not index_path.exists():
            if args.skip_missing:
                continue
            raise FileNotFoundError(f"Missing 3D point indices for {object_id}")
        point_ids = load_point_index_mask(index_path)
        if len(point_ids) < args.min_points:
            if args.skip_small:
                continue
        pred_class_id = sceneverse_category_id(category, instance_index + 1)
        instance = {
            "object_id": object_id,
            "pred_class_name": str(category).strip().lower().replace("_", " "),
            "pred_class_id": pred_class_id,
            "raw_pred_class_name": str(raw_category).strip().lower().replace("_", " "),
            "point_ids": point_ids,
            "point_count": len(point_ids),
            "bbox_3d": obj.get("bbox_3d"),
            "name": obj.get("name", object_id),
            "description": obj.get("description", ""),
            "selected_frames": obj.get("selected_frames", []),
            "mask_3d": obj.get("mask_3d"),
            "mask_3d_cloud": obj.get("mask_3d_cloud"),
            "mesh_asset": obj.get("mesh_asset"),
            "source_object_json": str(object_json),
        }
        metadata[str(instance_index)] = instance
        instances.append(
            {
                "instance_id": instance_index,
                "object_id": object_id,
                "category": instance["pred_class_name"],
                "pred_class_id": pred_class_id,
                "point_count": len(point_ids),
                "bbox_3d": obj.get("bbox_3d"),
            }
        )

    metadata_path = output_root / "metadata.json"
    write_json(metadata_path, metadata)

    input_video = manifest.get("inputs", {}).get("video")
    data_info = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "scene_id": scene_id,
        "source": "video2mesh",
        "video_url": input_video or "",
        "video_path": input_video or "",
        "data_frames": frame_ids_from_project(project_root, manifest),
        "notes": "SVPP-style export generated from Video2Mesh fused 3D object masks.",
    }
    write_json(output_root / "data_info.json", data_info)

    export_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "scene_id": scene_id,
        "project_root": str(project_root),
        "output_root": str(output_root),
        "files": {
            "mesh": str(mesh_dst),
            "camera_info": str(camera_dst) if camera_dst.exists() else None,
            "metadata": str(metadata_path),
            "data_info": str(output_root / "data_info.json"),
        },
        "instances": instances,
        "compatibility": {
            "spatiallm_generate_layout": "metadata.json contains point_ids and pred_class_name.",
            "pq3d_generate_dataset": "metadata.json contains point_ids, pred_class_name, and pred_class_id.",
            "notes": "mesh.ply is a point-cloud PLY when no triangle mesh reconstruction is registered; SceneVerse++ readers use vertex positions/colors for these adapters.",
        },
    }
    export_manifest_path = output_root / "video2mesh_svpp_export.json"
    write_json(export_manifest_path, export_manifest)
    manifest["artifacts"]["svpp_scene"] = str(output_root)
    manifest["artifacts"]["svpp_metadata"] = str(metadata_path)
    save_manifest(project_root, manifest)

    print(f"Exported SVPP-style scene: {output_root}")
    print(f"Instances: {len(instances)}; metadata: {metadata_path}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    objects_dir = project_root / manifest["objects_dir"]
    if objects_dir.exists():
        print("\nObjects:")
        for object_json in sorted(objects_dir.glob("*/object.json")):
            obj = read_json(object_json)
            mesh_asset = obj.get("mesh_asset") or {}
            mesh_path = mesh_asset.get("asset_path") or mesh_asset.get("source_mesh")
            print(
                f"- {obj.get('object_id')}: points={obj.get('point_count')} "
                f"selected_frames={len(obj.get('selected_frames', []))} "
                f"mesh={'yes' if mesh_path else 'no'}"
            )
    return 0


def validation_item(name: str, ok: bool, detail: str, severity: str = "required") -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "severity": severity,
        "detail": detail,
    }


def path_exists_for_manifest(project_root: Path, value: str | None) -> tuple[bool, str]:
    path = resolve_existing_path(value, project_root)
    return (bool(path and path.exists()), str(path) if path else "")


def safe_read_json(path: Path | None) -> Any | None:
    if path is None or not path.exists():
        return None
    try:
        return read_json(path)
    except Exception:
        return None


def count_files_with_extensions(path: Path, extensions: set[str]) -> int:
    if not path.exists():
        return 0
    return len(
        [
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix.lower() in extensions
            and not any(part.startswith(".") for part in item.relative_to(path).parts)
        ]
    )


def count_ply_vertices(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    try:
        with path.open("rb") as f:
            for raw_line in f:
                line = raw_line.decode("ascii", errors="ignore").strip()
                if line.startswith("element vertex"):
                    return int(line.split()[-1])
                if line == "end_header":
                    break
    except Exception:
        return None
    return None


def read_frames_manifest(project_root: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
    frames_manifest_path = resolve_existing_path(manifest.get("artifacts", {}).get("frames_manifest"), project_root)
    if frames_manifest_path and frames_manifest_path.exists():
        data = safe_read_json(frames_manifest_path)
        return data if isinstance(data, dict) else None
    default_path = project_root / "scene" / "frames_manifest.json"
    data = safe_read_json(default_path)
    return data if isinstance(data, dict) else None


def summarize_point_cloud_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": "", "exists": False, "readable": False, "error": "missing path"}
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "readable": False,
        "vertex_count": count_ply_vertices(path),
    }
    if not path.exists():
        summary["error"] = "file does not exist"
        return summary
    try:
        points, colors = read_point_cloud(path)
        summary["readable"] = True
        summary["vertex_count"] = int(points.shape[0])
        summary["has_color"] = colors is not None
        bbox = bbox_for_points(points)
        summary["bbox"] = bbox
        summary["bbox_diagonal"] = vector_diagonal(bbox.get("size") if isinstance(bbox, dict) else None)
    except Exception as exc:
        summary["error"] = str(exc)
    return summary


def summarize_camera_frame_coverage(camera_info: Any, frames: list[Path]) -> dict[str, Any]:
    if not isinstance(camera_info, dict):
        return {
            "camera_info_exists": False,
            "extrinsic_count": 0,
            "frame_count": len(frames),
            "covered_frame_count": 0,
            "coverage_ratio": 0.0,
            "missing_frame_ids": [frame_id_for_path(frame) for frame in frames[:20]],
        }
    extrinsics = camera_info.get("extrinsic") if isinstance(camera_info.get("extrinsic"), dict) else {}
    covered = []
    missing = []
    for frame_path in frames:
        frame_id = frame_id_for_path(frame_path)
        if resolve_extrinsic(extrinsics, frame_id) is not None:
            covered.append(frame_id)
        else:
            missing.append(frame_id)
    frame_count = len(frames)
    return {
        "camera_info_exists": True,
        "source": camera_info.get("source"),
        "extrinsic_type": camera_info.get("extrinsic_type", "world_to_camera"),
        "intrinsic_estimated": bool((camera_info.get("intrinsic") or {}).get("estimated")),
        "extrinsic_count": len(extrinsics),
        "frame_count": frame_count,
        "covered_frame_count": len(covered),
        "coverage_ratio": float(len(covered) / frame_count) if frame_count else 0.0,
        "missing_frame_ids": missing[:20],
        "covered_frame_ids_sample": covered[:20],
    }


def readiness_item(name: str, ok: bool, severity: str, detail: str, value: Any = None, threshold: Any = None) -> dict[str, Any]:
    item = {
        "name": name,
        "ok": bool(ok),
        "severity": severity,
        "detail": detail,
    }
    if value is not None:
        item["value"] = value
    if threshold is not None:
        item["threshold"] = threshold
    return item


def reconstruction_readiness_report(
    project_root: Path,
    manifest: dict[str, Any],
    min_frames: int = 3,
    min_camera_poses: int = 2,
    min_point_count: int = 100,
    min_camera_coverage: float = 0.8,
    min_visible_point_ratio: float = 0.05,
    require_preview: bool = False,
) -> dict[str, Any]:
    artifacts = manifest.get("artifacts", {})
    frames_dir = project_root / manifest["scene"]["frames_dir"]
    frames = list_frame_images(frames_dir) if frames_dir.exists() else []
    frames_manifest = read_frames_manifest(project_root, manifest)
    camera_path = project_root / manifest["scene"]["camera_info"]
    camera_info = safe_read_json(camera_path)
    camera_coverage = summarize_camera_frame_coverage(camera_info, frames)
    point_cloud_path = project_root / manifest["scene"]["point_cloud"]
    point_cloud = summarize_point_cloud_file(point_cloud_path)
    scene_3dgs_path = resolve_existing_path(artifacts.get("scene_3dgs_ply") or artifacts.get("scene_3dgs"), project_root)
    reconstruction_preview_path = resolve_existing_path(artifacts.get("reconstruction_preview"), project_root)
    reconstruction_preview = safe_read_json(reconstruction_preview_path) if reconstruction_preview_path else None
    preview_summary = reconstruction_preview.get("summary") if isinstance(reconstruction_preview, dict) else None

    frame_count = len(frames)
    extrinsic_count = int(camera_coverage.get("extrinsic_count") or 0)
    covered_frame_count = int(camera_coverage.get("covered_frame_count") or 0)
    coverage_ratio = float(camera_coverage.get("coverage_ratio") or 0.0)
    point_count = int(point_cloud.get("vertex_count") or 0)
    preview_exists = bool(reconstruction_preview_path and reconstruction_preview_path.exists())
    preview_valid_frames = int((preview_summary or {}).get("valid_frame_count") or 0) if isinstance(preview_summary, dict) else 0
    preview_visible_ratio = (preview_summary or {}).get("mean_visible_point_ratio") if isinstance(preview_summary, dict) else None

    checks = [
        readiness_item("frames_present", frame_count > 0, "required", f"{frame_count} frame(s) in {frames_dir}", frame_count, ">0"),
        readiness_item("enough_scan_frames", frame_count >= min_frames, "warning", f"{frame_count} frame(s); short scans may underconstrain geometry.", frame_count, min_frames),
        readiness_item("camera_info_present", isinstance(camera_info, dict), "required", str(camera_path)),
        readiness_item("enough_camera_poses", extrinsic_count >= min_camera_poses, "warning", f"{extrinsic_count} camera pose(s).", extrinsic_count, min_camera_poses),
        readiness_item("frame_camera_coverage", coverage_ratio >= min_camera_coverage, "required", f"{covered_frame_count}/{frame_count} frame(s) have camera poses.", coverage_ratio, min_camera_coverage),
        readiness_item("point_cloud_readable", bool(point_cloud.get("readable")) and point_count > 0, "required", str(point_cloud_path), point_count, ">0"),
        readiness_item("point_cloud_density", point_count >= min_point_count, "warning", f"{point_count} point(s); sparse geometry may hurt 3DGS init and mask fusion.", point_count, min_point_count),
        readiness_item("scene_3dgs_registered", bool(scene_3dgs_path and scene_3dgs_path.exists()), "recommended", str(scene_3dgs_path) if scene_3dgs_path else "missing scene_3dgs artifact"),
        readiness_item("reconstruction_preview_present", preview_exists, "recommended" if not require_preview else "required", "Run render-reconstruction-preview to verify camera/point-cloud alignment."),
    ]
    if preview_exists:
        checks.append(
            readiness_item(
                "reconstruction_preview_valid",
                preview_valid_frames > 0,
                "required" if require_preview else "warning",
                f"{preview_valid_frames} valid projection preview frame(s).",
                preview_valid_frames,
                ">0",
            )
        )
        if preview_visible_ratio is not None:
            checks.append(
                readiness_item(
                    "reconstruction_preview_visibility",
                    float(preview_visible_ratio) >= min_visible_point_ratio,
                    "warning",
                    "Mean visible point ratio in projection preview.",
                    float(preview_visible_ratio),
                    min_visible_point_ratio,
                )
            )

    blocking_failures = [item for item in checks if item["severity"] == "required" and not item["ok"]]
    warnings = [item for item in checks if item["severity"] == "warning" and not item["ok"]]
    recommended_missing = [item for item in checks if item["severity"] == "recommended" and not item["ok"]]
    ready_for_colmap_export = frame_count > 0 and covered_frame_count > 0 and point_count > 0
    ready_for_gsplat_training = ready_for_colmap_export and point_count >= min_point_count
    ready_for_mask_fusion = frame_count > 0 and point_count > 0 and coverage_ratio >= min_camera_coverage
    alignment_verified = preview_exists and preview_valid_frames > 0 and (
        preview_visible_ratio is None or float(preview_visible_ratio) >= min_visible_point_ratio
    )

    return {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "thresholds": {
            "min_frames": min_frames,
            "min_camera_poses": min_camera_poses,
            "min_point_count": min_point_count,
            "min_camera_coverage": min_camera_coverage,
            "min_visible_point_ratio": min_visible_point_ratio,
            "require_preview": require_preview,
        },
        "ok": not blocking_failures and (not require_preview or alignment_verified),
        "ready_for_colmap_export": bool(ready_for_colmap_export),
        "ready_for_gsplat_training": bool(ready_for_gsplat_training),
        "ready_for_mask_fusion": bool(ready_for_mask_fusion),
        "alignment_verified": bool(alignment_verified),
        "frames": {
            "frames_dir": str(frames_dir),
            "frame_count": frame_count,
            "frame_ids_sample": [frame_id_for_path(frame) for frame in frames[:20]],
            "manifest": {
                "exists": frames_manifest is not None,
                "source_video": frames_manifest.get("source_video") if isinstance(frames_manifest, dict) else None,
                "source_frame_count": frames_manifest.get("source_frame_count") if isinstance(frames_manifest, dict) else None,
                "written_frame_count": frames_manifest.get("written_frame_count") if isinstance(frames_manifest, dict) else None,
                "every": frames_manifest.get("every") if isinstance(frames_manifest, dict) else None,
            },
        },
        "camera": {
            "path": str(camera_path),
            **camera_coverage,
        },
        "point_cloud": point_cloud,
        "scene_3dgs": {
            "path": str(scene_3dgs_path) if scene_3dgs_path else "",
            "exists": bool(scene_3dgs_path and scene_3dgs_path.exists()),
            "vertex_count": count_ply_vertices(scene_3dgs_path),
        },
        "reconstruction_preview": {
            "manifest": str(reconstruction_preview_path) if reconstruction_preview_path else "",
            "exists": preview_exists,
            "summary": preview_summary,
        },
        "external_stage": manifest.get("external_stages", {}).get("video_to_3dgs"),
        "checks": checks,
        "blocking_failures": blocking_failures,
        "warnings": warnings,
        "recommended_missing": recommended_missing,
        "recommended_next_steps": [
            "Run render-reconstruction-preview and inspect projection_overlay.png before fusing 2D masks." if not preview_exists else "",
            "Increase scan coverage or improve SLAM/SfM if camera coverage is low." if coverage_ratio < min_camera_coverage else "",
            "Use calibrated intrinsics when camera_info.intrinsic.estimated is true." if camera_coverage.get("intrinsic_estimated") else "",
            "Train/register a real 3DGS before semantic splat transfer." if not (scene_3dgs_path and scene_3dgs_path.exists()) else "",
        ],
    }


def vector_diagonal(values: Any) -> float | None:
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        return None
    try:
        return sum(float(value) ** 2 for value in values) ** 0.5
    except Exception:
        return None


def bundle_objects_by_id(bundle: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(bundle, dict):
        return {}
    result = {}
    for item in bundle.get("objects", []):
        if isinstance(item, dict) and item.get("object_id"):
            result[str(item["object_id"])] = item
    return result


def validate_project(project_root: Path, strict: bool = False) -> dict[str, Any]:
    manifest = load_manifest(project_root)
    artifacts = manifest.get("artifacts", {})
    items: list[dict[str, Any]] = []

    frames_dir = project_root / manifest["scene"]["frames_dir"]
    frame_count = len([p for p in frames_dir.glob("*") if p.suffix.lower() in IMAGE_EXTENSIONS]) if frames_dir.exists() else 0
    items.append(validation_item("frames", frame_count > 0, f"{frame_count} frame image(s) in {frames_dir}"))

    camera_path = project_root / manifest["scene"]["camera_info"]
    camera_ok = False
    camera_detail = str(camera_path)
    if camera_path.exists():
        try:
            camera = read_json(camera_path)
            camera_ok = "intrinsic" in camera and "extrinsic" in camera and bool(camera.get("extrinsic"))
            camera_detail = f"{len(camera.get('extrinsic', {}))} extrinsic(s) in {camera_path}"
        except Exception as exc:
            camera_detail = f"failed to read {camera_path}: {exc}"
    items.append(validation_item("camera_info", camera_ok, camera_detail))

    point_cloud_path = project_root / manifest["scene"]["point_cloud"]
    items.append(validation_item("point_cloud", point_cloud_path.exists(), str(point_cloud_path)))

    scene_3dgs_ok, scene_3dgs_detail = path_exists_for_manifest(project_root, artifacts.get("scene_3dgs_ply") or artifacts.get("scene_3dgs"))
    items.append(validation_item("scene_3dgs", scene_3dgs_ok, scene_3dgs_detail or "missing scene_3dgs/scene_3dgs_ply artifact"))

    objects_dir = project_root / manifest["objects_dir"]
    object_jsons = sorted(objects_dir.glob("*/object.json")) if objects_dir.exists() else []
    items.append(validation_item("objects", bool(object_jsons), f"{len(object_jsons)} object record(s) in {objects_dir}"))

    object_records = []
    for object_json in object_jsons:
        try:
            object_records.append(read_json(object_json))
        except Exception:
            pass
    foreground_object_records = [obj for obj in object_records if obj.get("asset_role", "object") != "background_structure"]
    background_structure_records = [obj for obj in object_records if obj.get("asset_role") == "background_structure"]

    masks3d_ok, masks3d_detail = path_exists_for_manifest(project_root, artifacts.get("object_masks_3d"))
    all_objects_have_3d_mask = bool(object_records) and all((obj.get("mask_3d") or {}).get("point_indices_json") or (obj.get("mask_3d") or {}).get("point_indices_npy") for obj in object_records)
    items.append(validation_item("object_3d_masks", masks3d_ok and all_objects_have_3d_mask, masks3d_detail or "missing object 3D mask artifact"))

    mask_clouds_ok, mask_clouds_detail = path_exists_for_manifest(project_root, artifacts.get("object_mask_clouds"))
    all_objects_have_mask_cloud = bool(object_records) and all((obj.get("mask_3d_cloud") or {}).get("path") for obj in object_records)
    mask_cloud_paths_exist = True
    for obj in object_records:
        cloud_path = resolve_existing_path((obj.get("mask_3d_cloud") or {}).get("path"), project_root)
        if not cloud_path or not cloud_path.exists():
            mask_cloud_paths_exist = False
            break
    items.append(validation_item("object_mask_clouds", mask_clouds_ok and all_objects_have_mask_cloud and mask_cloud_paths_exist, mask_clouds_detail or "missing object mask cloud artifact"))

    semantic_ok, semantic_detail = path_exists_for_manifest(project_root, artifacts.get("semantic_splats_ply"))
    semantic_manifest_ok, semantic_manifest_detail = path_exists_for_manifest(project_root, artifacts.get("semantic_splats_manifest"))
    items.append(validation_item("semantic_splats", semantic_ok and semantic_manifest_ok, f"ply={semantic_detail}; manifest={semantic_manifest_detail}"))
    scene_supersplat_ok, scene_supersplat_detail = path_exists_for_manifest(project_root, artifacts.get("scene_3dgs_supersplat_ply"))
    semantic_supersplat_ok, semantic_supersplat_detail = path_exists_for_manifest(project_root, artifacts.get("semantic_supersplat_ply"))
    items.append(
        validation_item(
            "viewer_plys",
            scene_supersplat_ok and semantic_supersplat_ok,
            f"scene_supersplat={scene_supersplat_detail or 'missing'}; semantic_supersplat={semantic_supersplat_detail or 'missing'}",
            "recommended",
        )
    )
    semantic_preview_ok, semantic_preview_detail = path_exists_for_manifest(project_root, artifacts.get("semantic_preview"))
    items.append(validation_item("semantic_preview", semantic_preview_ok, semantic_preview_detail or "missing semantic mask projection preview", "recommended"))

    labels_ok, labels_detail = path_exists_for_manifest(project_root, artifacts.get("object_labels"))
    object_categories_named = bool(object_records) and all(str(obj.get("category", "unknown")).strip().lower() not in {"", "unknown"} for obj in object_records)
    items.append(validation_item("object_semantic_labels", labels_ok or object_categories_named, labels_detail or "missing object_labels artifact or non-unknown object categories", "recommended"))

    labeling_jobs_ok, labeling_jobs_detail = path_exists_for_manifest(project_root, artifacts.get("object_labeling_jobs"))
    items.append(validation_item("object_labeling_jobs", labeling_jobs_ok, labeling_jobs_detail or "missing external VLM/open-vocabulary labeling jobs", "recommended"))

    selected_ok, selected_detail = path_exists_for_manifest(project_root, artifacts.get("selected_frames"))
    all_objects_have_selected = bool(foreground_object_records) and all(obj.get("selected_frames") for obj in foreground_object_records)
    items.append(validation_item("selected_frames", selected_ok and all_objects_have_selected, selected_detail or "missing selected_frames artifact"))

    object_images_ok, object_images_detail = path_exists_for_manifest(project_root, artifacts.get("object_images"))
    all_objects_have_crops = bool(foreground_object_records) and all(obj.get("primary_object_image") for obj in foreground_object_records)
    items.append(validation_item("object_reference_images", object_images_ok and all_objects_have_crops, object_images_detail or "missing object_images artifact"))

    image_blaster_ok, image_blaster_detail = path_exists_for_manifest(project_root, artifacts.get("image_blaster_world"))
    items.append(validation_item("image_blaster_world", image_blaster_ok, image_blaster_detail or "missing image_blaster_world artifact", "recommended"))

    svpp_scene_ok, svpp_scene_detail = path_exists_for_manifest(project_root, artifacts.get("svpp_scene"))
    svpp_metadata_ok, svpp_metadata_detail = path_exists_for_manifest(project_root, artifacts.get("svpp_metadata"))
    items.append(
        validation_item(
            "svpp_scene",
            svpp_scene_ok and svpp_metadata_ok,
            f"scene={svpp_scene_detail or 'missing'}; metadata={svpp_metadata_detail or 'missing'}",
            "recommended",
        )
    )

    object_meshes_ok, object_meshes_detail = path_exists_for_manifest(project_root, artifacts.get("object_meshes"))
    all_objects_have_mesh = bool(foreground_object_records) and all((obj.get("mesh_asset") or {}).get("asset_path") or (obj.get("mesh_asset") or {}).get("source_mesh") for obj in foreground_object_records)
    mesh_paths_exist = True
    for obj in foreground_object_records:
        mesh_asset = obj.get("mesh_asset") or {}
        mesh_path = resolve_existing_path(mesh_asset.get("asset_path") or mesh_asset.get("source_mesh"), project_root)
        if not mesh_path or not mesh_path.exists():
            mesh_paths_exist = False
            break
    items.append(validation_item("object_meshes", object_meshes_ok and all_objects_have_mesh and mesh_paths_exist, object_meshes_detail or "missing object_meshes artifact"))

    background_ok, background_detail = path_exists_for_manifest(project_root, artifacts.get("background_structures"))
    items.append(validation_item("background_structures", background_ok or bool(background_structure_records), background_detail or f"{len(background_structure_records)} background structure record(s)", "recommended"))

    bundle_ok, bundle_detail = path_exists_for_manifest(project_root, artifacts.get("simulator_asset_bundle"))
    bundle_objects_ok = False
    if bundle_ok:
        try:
            bundle = read_json(Path(bundle_detail))
            bundle_objects_ok = len(bundle.get("objects", [])) >= len(foreground_object_records) and not bundle.get("missing_mesh_objects")
            bundle_detail = f"{bundle_detail}; objects={len(bundle.get('objects', []))}; missing_meshes={bundle.get('missing_mesh_objects')}"
        except Exception as exc:
            bundle_detail = f"{bundle_detail}; failed to read: {exc}"
    items.append(validation_item("simulator_asset_bundle", bundle_ok and bundle_objects_ok, bundle_detail or "missing simulator_asset_bundle artifact"))

    adapters_ok, adapters_detail = path_exists_for_manifest(project_root, artifacts.get("simulator_adapters"))
    items.append(validation_item("simulator_adapters", adapters_ok, adapters_detail or "missing simulator_adapters artifact", "recommended"))

    asset_qa_ok, asset_qa_detail = path_exists_for_manifest(project_root, artifacts.get("simulator_asset_qa"))
    items.append(validation_item("simulator_asset_qa", asset_qa_ok, asset_qa_detail or "missing simulator asset QA report", "recommended"))

    calibration_ok, calibration_detail = path_exists_for_manifest(project_root, artifacts.get("simulator_calibration"))
    items.append(validation_item("simulator_calibration", calibration_ok, calibration_detail or "missing simulator calibration report", "recommended"))

    required_failed = [item for item in items if item["severity"] == "required" and not item["ok"]]
    recommended_failed = [item for item in items if item["severity"] != "required" and not item["ok"]]
    return {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "strict": strict,
        "ok": not required_failed and (not strict or not recommended_failed),
        "items": items,
        "required_failed": [item["name"] for item in required_failed],
        "recommended_failed": [item["name"] for item in recommended_failed],
    }


def evaluate_object_record(
    obj: dict[str, Any],
    project_root: Path,
    min_object_points: int,
    bundle_object: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    object_id = obj.get("object_id") or "unknown"
    asset_role = obj.get("asset_role", "object")
    is_background_structure = asset_role == "background_structure"
    issues: list[dict[str, Any]] = []
    point_count = int(obj.get("point_count") or 0)
    bbox = obj.get("bbox_3d") if isinstance(obj.get("bbox_3d"), dict) else {}
    selected_frames = obj.get("selected_frames") if isinstance(obj.get("selected_frames"), list) else []
    object_images = obj.get("object_images") if isinstance(obj.get("object_images"), list) else []
    frame_scores = obj.get("frame_scores") if isinstance(obj.get("frame_scores"), dict) else {}

    mask_3d = obj.get("mask_3d") if isinstance(obj.get("mask_3d"), dict) else {}
    mask_indices_path = resolve_existing_path(mask_3d.get("point_indices_json") or mask_3d.get("point_indices_npy"), project_root)
    mask_index_count = None
    if mask_indices_path and mask_indices_path.exists():
        try:
            mask_index_count = len(load_point_index_mask(mask_indices_path))
        except Exception:
            mask_index_count = None

    mask_cloud = obj.get("mask_3d_cloud") if isinstance(obj.get("mask_3d_cloud"), dict) else {}
    mask_cloud_path = resolve_existing_path(mask_cloud.get("path"), project_root)
    mesh_asset = obj.get("mesh_asset") if isinstance(obj.get("mesh_asset"), dict) else {}
    mesh_path = resolve_existing_path(mesh_asset.get("asset_path") or mesh_asset.get("source_mesh"), project_root)
    bundle_mesh = bundle_object.get("mesh") if isinstance(bundle_object, dict) and isinstance(bundle_object.get("mesh"), dict) else {}
    bundle_mesh_path = resolve_existing_path(bundle_mesh.get("path"), project_root) if bundle_mesh else None
    mesh_quality = bundle_object.get("quality", {}).get("mesh") if isinstance(bundle_object, dict) and isinstance(bundle_object.get("quality"), dict) else None
    primary_object_image = obj.get("primary_object_image") if isinstance(obj.get("primary_object_image"), dict) else {}
    primary_image_path = resolve_existing_path(primary_object_image.get("reference_image") or primary_object_image.get("object_image"), project_root)

    if point_count < min_object_points:
        issues.append(
            {
                "severity": "warning",
                "object_id": object_id,
                "name": "low_object_point_count",
                "detail": f"{point_count} point(s), threshold={min_object_points}",
            }
        )
    if not selected_frames and not is_background_structure:
        issues.append({"severity": "required", "object_id": object_id, "name": "missing_selected_frames", "detail": "Run select-frames."})
    if (not primary_image_path or not primary_image_path.exists()) and not is_background_structure:
        issues.append({"severity": "required", "object_id": object_id, "name": "missing_object_reference_image", "detail": "Run prepare-object-images."})
    if (not mesh_path or not mesh_path.exists()) and not is_background_structure:
        issues.append({"severity": "required", "object_id": object_id, "name": "missing_object_mesh", "detail": "Import image-blaster/FAL mesh outputs."})
    if not mask_cloud_path or not mask_cloud_path.exists():
        issues.append({"severity": "required", "object_id": object_id, "name": "missing_object_mask_cloud", "detail": "Run export-object-mask-clouds."})

    top_selected_score = None
    if selected_frames:
        try:
            top_selected_score = max(float(item.get("score", 0.0)) for item in selected_frames)
        except Exception:
            top_selected_score = None

    report = {
        "object_id": object_id,
        "asset_role": asset_role,
        "name": obj.get("name", object_id),
        "category": obj.get("category", "unknown"),
        "point_count": point_count,
        "mask_index_count": mask_index_count,
        "bbox_center": bbox.get("center") if isinstance(bbox, dict) else None,
        "bbox_size": bbox.get("size") if isinstance(bbox, dict) else None,
        "bbox_diagonal": vector_diagonal(bbox.get("size")) if isinstance(bbox, dict) else None,
        "frame_score_count": len(frame_scores),
        "selected_frame_count": len(selected_frames),
        "top_selected_score": top_selected_score,
        "object_image_count": len(object_images),
        "primary_object_image_exists": bool(primary_image_path and primary_image_path.exists()),
        "mask_cloud_exists": bool(mask_cloud_path and mask_cloud_path.exists()),
        "mask_cloud_point_count": mask_cloud.get("point_count"),
        "mesh_exists": bool(mesh_path and mesh_path.exists()),
        "mesh_format": mesh_asset.get("format"),
        "mesh_source": mesh_asset.get("source"),
        "simulator_mesh_exists": bool(bundle_mesh_path and bundle_mesh_path.exists()),
        "simulator_mesh_path": str(bundle_mesh_path) if bundle_mesh_path else "",
        "simulator_mesh_coordinate_frame": bundle_mesh.get("coordinate_frame") if isinstance(bundle_mesh, dict) else None,
        "mesh_quality": mesh_quality,
        "issues": issues,
    }
    return report, issues


def cmd_evaluate(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    artifacts = manifest.get("artifacts", {})
    validation = validate_project(project_root, strict=args.strict)
    issues: list[dict[str, Any]] = []

    frames_dir = project_root / manifest["scene"]["frames_dir"]
    camera_path = project_root / manifest["scene"]["camera_info"]
    point_cloud_path = project_root / manifest["scene"]["point_cloud"]
    scene_3dgs_path = resolve_existing_path(artifacts.get("scene_3dgs_ply") or artifacts.get("scene_3dgs"), project_root)
    reconstruction_preview_path = resolve_existing_path(artifacts.get("reconstruction_preview"), project_root)
    reconstruction_preview = safe_read_json(reconstruction_preview_path) if reconstruction_preview_path else None
    gsplat_preview_path = resolve_existing_path(artifacts.get("gsplat_preview"), project_root)
    gsplat_preview = safe_read_json(gsplat_preview_path) if gsplat_preview_path else None
    camera_info = safe_read_json(camera_path)
    frame_count = count_files_with_extensions(frames_dir, IMAGE_EXTENSIONS)
    camera_count = len(camera_info.get("extrinsic", {})) if isinstance(camera_info, dict) else 0

    mask_root = project_root / manifest["masks"]["mask_2d_dir"]
    mask_records_by_object: dict[str, int] = {}
    mask_record_count = 0
    try:
        for record in scan_mask_records(mask_root):
            mask_record_count += 1
            mask_records_by_object[record.object_id] = mask_records_by_object.get(record.object_id, 0) + 1
    except Exception:
        mask_record_count = count_files_with_extensions(mask_root, MASK_EXTENSIONS)

    object_masks_path = resolve_existing_path(artifacts.get("object_masks_3d"), project_root)
    object_masks_summary = safe_read_json(object_masks_path) if object_masks_path else None
    semantic_manifest_path = resolve_existing_path(artifacts.get("semantic_splats_manifest"), project_root)
    semantic_manifest = safe_read_json(semantic_manifest_path) if semantic_manifest_path else None
    semantic_splats_path = resolve_existing_path(artifacts.get("semantic_splats_ply"), project_root)
    scene_supersplat_path = resolve_existing_path(artifacts.get("scene_3dgs_supersplat_ply"), project_root)
    scene_point_cloud_view_path = resolve_existing_path(artifacts.get("scene_3dgs_point_cloud_ply"), project_root)
    semantic_supersplat_path = resolve_existing_path(artifacts.get("semantic_supersplat_ply"), project_root)
    semantic_point_cloud_view_path = resolve_existing_path(artifacts.get("semantic_point_cloud_ply"), project_root)
    semantic_preview_path = resolve_existing_path(artifacts.get("semantic_preview"), project_root)
    semantic_preview = safe_read_json(semantic_preview_path) if semantic_preview_path else None
    mask_cloud_manifest_path = resolve_existing_path(artifacts.get("object_mask_clouds"), project_root)
    mask_cloud_manifest = safe_read_json(mask_cloud_manifest_path) if mask_cloud_manifest_path else None
    mesh_index_path = resolve_existing_path(artifacts.get("object_meshes"), project_root)
    mesh_index = safe_read_json(mesh_index_path) if mesh_index_path else None
    bundle_path = resolve_existing_path(artifacts.get("simulator_asset_bundle"), project_root)
    bundle = safe_read_json(bundle_path) if bundle_path else None
    bundle_by_object = bundle_objects_by_id(bundle)
    labels_path = resolve_existing_path(artifacts.get("object_labels"), project_root)
    labels = safe_read_json(labels_path) if labels_path else None
    multiview_mesh_jobs_path = resolve_existing_path(artifacts.get("multiview_mesh_jobs"), project_root)
    multiview_mesh_jobs = safe_read_json(multiview_mesh_jobs_path) if multiview_mesh_jobs_path else None
    simulator_asset_qa_path = resolve_existing_path(artifacts.get("simulator_asset_qa"), project_root)
    simulator_asset_qa = safe_read_json(simulator_asset_qa_path) if simulator_asset_qa_path else None
    simulator_calibration_path = resolve_existing_path(artifacts.get("simulator_calibration"), project_root)
    simulator_calibration = safe_read_json(simulator_calibration_path) if simulator_calibration_path else None
    svpp_scene_path = resolve_existing_path(artifacts.get("svpp_scene"), project_root)
    svpp_metadata_path = resolve_existing_path(artifacts.get("svpp_metadata"), project_root)
    svpp_metadata = safe_read_json(svpp_metadata_path) if svpp_metadata_path else None

    objects_dir = project_root / manifest["objects_dir"]
    object_reports = []
    object_jsons = sorted(objects_dir.glob("*/object.json")) if objects_dir.exists() else []
    for object_json in object_jsons:
        try:
            obj = read_json(object_json)
        except Exception as exc:
            issues.append({"severity": "required", "name": "unreadable_object_json", "detail": f"{object_json}: {exc}"})
            continue
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        object_report, object_issues = evaluate_object_record(obj, project_root, args.min_object_points, bundle_by_object.get(object_id))
        object_reports.append(object_report)
        issues.extend(object_issues)

    for item in validation["items"]:
        if not item["ok"]:
            issues.append(
                {
                    "severity": item["severity"],
                    "name": f"validation_missing_{item['name']}",
                    "detail": item["detail"],
                }
            )

    ready_mesh_objects = sum(1 for item in object_reports if item["mesh_exists"])
    ready_mask_cloud_objects = sum(1 for item in object_reports if item["mask_cloud_exists"])
    ready_reference_objects = sum(1 for item in object_reports if item["primary_object_image_exists"])
    object_count = len(object_reports)
    required_issue_count = len([item for item in issues if item.get("severity") == "required"])

    report = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "ok": required_issue_count == 0,
        "strict": args.strict,
        "thresholds": {
            "min_object_points": args.min_object_points,
        },
        "scene": {
            "frame_count": frame_count,
            "camera_extrinsic_count": camera_count,
            "point_cloud": {
                "path": str(point_cloud_path),
                "exists": point_cloud_path.exists(),
                "vertex_count": count_ply_vertices(point_cloud_path),
            },
            "scene_3dgs": {
                "path": str(scene_3dgs_path) if scene_3dgs_path else "",
                "exists": bool(scene_3dgs_path and scene_3dgs_path.exists()),
                "vertex_count": count_ply_vertices(scene_3dgs_path),
                "point_cloud_ply": str(scene_point_cloud_view_path) if scene_point_cloud_view_path else "",
                "point_cloud_ply_exists": bool(scene_point_cloud_view_path and scene_point_cloud_view_path.exists()),
                "supersplat_ply": str(scene_supersplat_path) if scene_supersplat_path else "",
                "supersplat_ply_exists": bool(scene_supersplat_path and scene_supersplat_path.exists()),
            },
            "reconstruction_preview": {
                "manifest": str(reconstruction_preview_path) if reconstruction_preview_path else "",
                "exists": bool(reconstruction_preview_path and reconstruction_preview_path.exists()),
                "summary": reconstruction_preview.get("summary") if isinstance(reconstruction_preview, dict) else None,
                "output_dir": reconstruction_preview.get("output_dir") if isinstance(reconstruction_preview, dict) else "",
            },
            "gsplat_preview": {
                "manifest": str(gsplat_preview_path) if gsplat_preview_path else "",
                "exists": bool(gsplat_preview_path and gsplat_preview_path.exists()),
                "frame_count": gsplat_preview.get("frame_count") if isinstance(gsplat_preview, dict) else 0,
                "mean_l1": gsplat_preview.get("mean_l1") if isinstance(gsplat_preview, dict) else None,
                "mean_psnr": gsplat_preview.get("mean_psnr") if isinstance(gsplat_preview, dict) else None,
                "output_dir": gsplat_preview.get("output_dir") if isinstance(gsplat_preview, dict) else "",
            },
        },
        "masks": {
            "masks_2d": {
                "path": str(mask_root),
                "mask_count": mask_record_count,
                "by_object": mask_records_by_object,
            },
            "masks_3d": {
                "path": str(object_masks_path) if object_masks_path else "",
                "exists": bool(object_masks_path and object_masks_path.exists()),
                "num_points": object_masks_summary.get("num_points") if isinstance(object_masks_summary, dict) else None,
                "num_masks": object_masks_summary.get("num_masks") if isinstance(object_masks_summary, dict) else None,
                "skipped_count": len(object_masks_summary.get("skipped", [])) if isinstance(object_masks_summary, dict) else None,
                "fusion": object_masks_summary.get("fusion") if isinstance(object_masks_summary, dict) else None,
            },
            "semantic_splats": {
                "path": str(semantic_splats_path) if semantic_splats_path else "",
                "exists": bool(semantic_splats_path and semantic_splats_path.exists()),
                "vertex_count": count_ply_vertices(semantic_splats_path),
                "point_cloud_ply": str(semantic_point_cloud_view_path) if semantic_point_cloud_view_path else "",
                "point_cloud_ply_exists": bool(semantic_point_cloud_view_path and semantic_point_cloud_view_path.exists()),
                "supersplat_ply": str(semantic_supersplat_path) if semantic_supersplat_path else "",
                "supersplat_ply_exists": bool(semantic_supersplat_path and semantic_supersplat_path.exists()),
                "manifest": str(semantic_manifest_path) if semantic_manifest_path else "",
                "transfer": semantic_manifest.get("transfer") if isinstance(semantic_manifest, dict) else None,
                "preview": {
                    "manifest": str(semantic_preview_path) if semantic_preview_path else "",
                    "exists": bool(semantic_preview_path and semantic_preview_path.exists()),
                    "summary": semantic_preview.get("summary") if isinstance(semantic_preview, dict) else None,
                    "colored_semantic_ply": semantic_preview.get("colored_semantic_ply") if isinstance(semantic_preview, dict) else "",
                    "output_dir": semantic_preview.get("output_dir") if isinstance(semantic_preview, dict) else "",
                },
            },
            "object_mask_clouds": {
                "manifest": str(mask_cloud_manifest_path) if mask_cloud_manifest_path else "",
                "exists": bool(mask_cloud_manifest_path and mask_cloud_manifest_path.exists()),
                "object_count": len(mask_cloud_manifest.get("objects", {})) if isinstance(mask_cloud_manifest, dict) else 0,
            },
        },
        "objects": object_reports,
        "semantic_labeling": {
            "labels": str(labels_path) if labels_path else "",
            "labels_exists": bool(labels_path and labels_path.exists()),
            "label_count": len(labels) if isinstance(labels, dict) else 0,
            "objects_with_non_unknown_category": len(
                [
                    item
                    for item in object_reports
                    if str(item.get("category", "unknown")).strip().lower() not in {"", "unknown"}
                ]
            ),
        },
        "mesh_generation": {
            "mesh_index": str(mesh_index_path) if mesh_index_path else "",
            "mesh_index_exists": bool(mesh_index_path and mesh_index_path.exists()),
            "imported_object_count": len(mesh_index.get("objects", {})) if isinstance(mesh_index, dict) else 0,
            "missing_objects": mesh_index.get("missing_objects", []) if isinstance(mesh_index, dict) else [],
            "multiview_mesh_jobs": str(multiview_mesh_jobs_path) if multiview_mesh_jobs_path else "",
            "multiview_mesh_jobs_exists": bool(multiview_mesh_jobs_path and multiview_mesh_jobs_path.exists()),
            "multiview_mesh_job_count": len(multiview_mesh_jobs.get("jobs", {})) if isinstance(multiview_mesh_jobs, dict) else 0,
        },
        "sceneversepp": {
            "scene": str(svpp_scene_path) if svpp_scene_path else "",
            "scene_exists": bool(svpp_scene_path and svpp_scene_path.exists()),
            "metadata": str(svpp_metadata_path) if svpp_metadata_path else "",
            "metadata_exists": bool(svpp_metadata_path and svpp_metadata_path.exists()),
            "instance_count": len(svpp_metadata) if isinstance(svpp_metadata, dict) else 0,
            "files": {
                "mesh": str(svpp_scene_path / "mesh.ply") if svpp_scene_path else "",
                "camera_info": str(svpp_scene_path / "camera_info.json") if svpp_scene_path else "",
                "data_info": str(svpp_scene_path / "data_info.json") if svpp_scene_path else "",
            },
        },
        "simulator_assets": {
            "bundle": str(bundle_path) if bundle_path else "",
            "bundle_exists": bool(bundle_path and bundle_path.exists()),
            "object_count": len(bundle.get("objects", [])) if isinstance(bundle, dict) else 0,
            "missing_mesh_objects": bundle.get("missing_mesh_objects", []) if isinstance(bundle, dict) else [],
            "coordinate_system": bundle.get("coordinate_system") if isinstance(bundle, dict) else None,
            "calibration_report": str(simulator_calibration_path) if simulator_calibration_path else "",
            "calibration_exists": bool(simulator_calibration_path and simulator_calibration_path.exists()),
            "calibration": simulator_calibration,
            "qa_report": str(simulator_asset_qa_path) if simulator_asset_qa_path else "",
            "qa_exists": bool(simulator_asset_qa_path and simulator_asset_qa_path.exists()),
            "qa_ok": simulator_asset_qa.get("ok") if isinstance(simulator_asset_qa, dict) else None,
            "qa_summary": simulator_asset_qa.get("summary") if isinstance(simulator_asset_qa, dict) else None,
        },
        "summary": {
            "object_count": object_count,
            "objects_with_reference_images": ready_reference_objects,
            "objects_with_3d_mask_clouds": ready_mask_cloud_objects,
            "objects_with_meshes": ready_mesh_objects,
            "required_issue_count": required_issue_count,
            "warning_count": len([item for item in issues if item.get("severity") == "warning"]),
        },
        "external_stages": manifest.get("external_stages", {}),
        "validation": validation,
        "issues": issues,
    }

    output_path = args.output.resolve() if args.output else project_root / manifest["simulator_assets_dir"] / "evaluation_report.json"
    write_json(output_path, report)
    manifest["artifacts"]["evaluation_report"] = str(output_path)
    save_manifest(project_root, manifest)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if report["ok"] else "ISSUES"
        print(f"Video2Mesh evaluation: {status} ({report['scene_id']})")
        print(
            f"Scene: frames={frame_count}, cameras={camera_count}, "
            f"point_cloud_vertices={report['scene']['point_cloud']['vertex_count']}, "
            f"3dgs_vertices={report['scene']['scene_3dgs']['vertex_count']}"
        )
        preview = report["scene"]["gsplat_preview"]
        if preview["exists"]:
            print(
                f"3DGS preview: frames={preview['frame_count']}, "
                f"mean_l1={preview['mean_l1']}, mean_psnr={preview['mean_psnr']}"
            )
        print(
            f"Objects: {object_count}; refs={ready_reference_objects}; "
            f"mask_clouds={ready_mask_cloud_objects}; meshes={ready_mesh_objects}"
        )
        if issues:
            print("Issues:")
            for issue in issues[: args.max_issues]:
                object_prefix = f"{issue.get('object_id')}: " if issue.get("object_id") else ""
                print(f"- [{issue.get('severity')}] {object_prefix}{issue.get('name')}: {issue.get('detail')}")
            if len(issues) > args.max_issues:
                print(f"- ... {len(issues) - args.max_issues} more issue(s)")
        print(f"Report: {output_path}")
    return 1 if args.fail_on_issues and issues else 0


def local_review_path(path_value: str | None, review_dir: Path) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    try:
        return html.escape(str(path.resolve().relative_to(review_dir.resolve())))
    except Exception:
        return html.escape(str(path))


def review_image_tag(path_value: str | None, review_dir: Path, alt: str) -> str:
    if not path_value:
        return '<div class="missing">missing image</div>'
    path = Path(path_value)
    if not path.exists():
        return f'<div class="missing">missing image<br><code>{html.escape(str(path))}</code></div>'
    src = local_review_path(str(path), review_dir)
    return f'<img src="{src}" alt="{html.escape(alt)}" loading="lazy">'


def issue_badges(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return '<span class="badge ok">ready</span>'
    badges = []
    for issue in issues:
        severity = html.escape(str(issue.get("severity", "warning")))
        name = html.escape(str(issue.get("name", "issue")))
        badges.append(f'<span class="badge {severity}">{severity}: {name}</span>')
    return "\n".join(badges)


def first_existing_path(values: list[str | None], project_root: Path) -> Path | None:
    for value in values:
        path = resolve_existing_path(value, project_root)
        if path and path.exists():
            return path
    return None


def preview_frame_items(preview: Any, image_keys: list[str], max_frames: int, project_root: Path) -> list[dict[str, Any]]:
    if not isinstance(preview, dict):
        return []
    items = []
    frames = preview.get("frames") if isinstance(preview.get("frames"), list) else []
    for frame in frames:
        if not isinstance(frame, dict) or frame.get("skipped"):
            continue
        image_path = first_existing_path([frame.get(key) for key in image_keys], project_root)
        if image_path is None:
            continue
        items.append(
            {
                "frame_id": frame.get("frame_id"),
                "image": str(image_path),
                "metrics": {key: value for key, value in frame.items() if isinstance(value, (int, float))},
            }
        )
        if max_frames > 0 and len(items) >= max_frames:
            break
    return items


def review_gallery(title: str, items: list[dict[str, Any]], output_dir: Path) -> str:
    if not items:
        return ""
    cards = []
    for item in items:
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
        metrics_text = " · ".join(f"{html.escape(str(k))}: {float(v):.4g}" for k, v in list(metrics.items())[:4])
        cards.append(
            '<div class="qa-frame">'
            f'{review_image_tag(item.get("image"), output_dir, str(item.get("frame_id", "")))}'
            f'<div>frame {html.escape(str(item.get("frame_id", "")))}</div>'
            f'<div>{metrics_text}</div>'
            "</div>"
        )
    return f'<section class="qa-card"><h2>{html.escape(title)}</h2><div class="qa-gallery">{"".join(cards)}</div></section>'


def cmd_export_review_pack(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    manifest = load_manifest(project_root)
    output_dir = ensure_dir(args.output_dir or (project_root / manifest["simulator_assets_dir"] / "review"))
    objects_dir = project_root / manifest["objects_dir"]
    if not objects_dir.exists():
        raise FileNotFoundError("No objects directory. Run fuse-masks first.")

    validation = validate_project(project_root, strict=False)
    eval_report_path = resolve_existing_path(manifest.get("artifacts", {}).get("evaluation_report"), project_root)
    evaluation = safe_read_json(eval_report_path) if eval_report_path else None
    bundle_path = resolve_existing_path(manifest.get("artifacts", {}).get("simulator_asset_bundle"), project_root)
    bundle = safe_read_json(bundle_path) if bundle_path else None
    bundle_by_object = bundle_objects_by_id(bundle)
    auto_prompt_preview = resolve_existing_path(manifest.get("artifacts", {}).get("auto_tracking_prompts_preview"), project_root)
    reconstruction_preview_path = resolve_existing_path(manifest.get("artifacts", {}).get("reconstruction_preview"), project_root)
    reconstruction_preview = safe_read_json(reconstruction_preview_path) if reconstruction_preview_path else None
    gsplat_preview_path = resolve_existing_path(manifest.get("artifacts", {}).get("gsplat_preview"), project_root)
    gsplat_preview = safe_read_json(gsplat_preview_path) if gsplat_preview_path else None
    semantic_preview_path = resolve_existing_path(manifest.get("artifacts", {}).get("semantic_preview"), project_root)
    semantic_preview = safe_read_json(semantic_preview_path) if semantic_preview_path else None
    scene_review = {
        "auto_prompts_preview": str(auto_prompt_preview) if auto_prompt_preview else None,
        "reconstruction_preview": {
            "manifest": str(reconstruction_preview_path) if reconstruction_preview_path else None,
            "summary": reconstruction_preview.get("summary") if isinstance(reconstruction_preview, dict) else None,
            "frames": preview_frame_items(reconstruction_preview, ["overlay"], args.max_scene_frames, project_root),
        },
        "gsplat_preview": {
            "manifest": str(gsplat_preview_path) if gsplat_preview_path else None,
            "summary": {
                "frame_count": gsplat_preview.get("frame_count"),
                "mean_l1": gsplat_preview.get("mean_l1"),
                "mean_psnr": gsplat_preview.get("mean_psnr"),
            }
            if isinstance(gsplat_preview, dict)
            else None,
            "renders": preview_frame_items(gsplat_preview, ["render"], args.max_scene_frames, project_root),
            "errors": preview_frame_items(gsplat_preview, ["error"], args.max_scene_frames, project_root),
        },
        "semantic_preview": {
            "manifest": str(semantic_preview_path) if semantic_preview_path else None,
            "summary": semantic_preview.get("summary") if isinstance(semantic_preview, dict) else None,
            "colored_semantic_ply": semantic_preview.get("colored_semantic_ply") if isinstance(semantic_preview, dict) else None,
            "frames": preview_frame_items(semantic_preview, ["overlay"], args.max_scene_frames, project_root),
        },
    }

    review_objects = []
    all_issues: list[dict[str, Any]] = []
    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        object_report, object_issues = evaluate_object_record(obj, project_root, args.min_object_points, bundle_by_object.get(object_id))
        all_issues.extend(object_issues)
        primary_object_image = obj.get("primary_object_image") if isinstance(obj.get("primary_object_image"), dict) else {}
        primary_frame = obj.get("primary_frame") if isinstance(obj.get("primary_frame"), dict) else {}
        mesh_asset = obj.get("mesh_asset") if isinstance(obj.get("mesh_asset"), dict) else {}
        review_objects.append(
            {
                **object_report,
                "description": obj.get("description", ""),
                "object_json": str(object_json),
                "primary_object_image": primary_object_image,
                "primary_frame": primary_frame,
                "selected_frames": obj.get("selected_frames", []),
                "mesh_asset": mesh_asset,
            }
        )

    review_manifest = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "project_root": str(project_root),
        "scene_id": manifest.get("scene_id"),
        "validation": validation,
        "evaluation_report": str(eval_report_path) if eval_report_path else None,
        "evaluation_summary": evaluation.get("summary") if isinstance(evaluation, dict) else None,
        "scene_review": scene_review,
        "objects": review_objects,
        "issues": all_issues,
    }
    review_json_path = output_dir / "review_pack.json"
    write_json(review_json_path, review_manifest)

    rows = []
    for item in review_objects:
        primary_image = item.get("primary_object_image") or {}
        primary_frame = item.get("primary_frame") or {}
        image_path = primary_image.get("reference_image") or primary_image.get("object_image") or primary_frame.get("selected_image") or primary_frame.get("image")
        selected_frames = item.get("selected_frames") if isinstance(item.get("selected_frames"), list) else []
        frame_items = []
        for selected in selected_frames[: args.max_frames]:
            thumb_path = selected.get("selected_image") or selected.get("image")
            frame_items.append(
                '<div class="frame">'
                f'{review_image_tag(thumb_path, output_dir, str(selected.get("frame_id", "frame")))}'
                f'<div>frame {html.escape(str(selected.get("frame_id", "")))}</div>'
                f'<div>score {float(selected.get("score", 0.0)):.2f}</div>'
                "</div>"
            )
        mesh_asset = item.get("mesh_asset") if isinstance(item.get("mesh_asset"), dict) else {}
        mesh_path = mesh_asset.get("asset_path") or mesh_asset.get("source_mesh")
        mesh_quality = item.get("mesh_quality") if isinstance(item.get("mesh_quality"), dict) else {}
        localization = mesh_quality.get("localization") if isinstance(mesh_quality.get("localization"), dict) else {}
        simulator_mesh_path = item.get("simulator_mesh_path") or ""
        mesh_frame = item.get("simulator_mesh_coordinate_frame") or mesh_asset.get("coordinate_frame") or ""
        rows.append(
            '<section class="object-card">'
            '<div class="object-main">'
            f'<div class="hero">{review_image_tag(image_path, output_dir, str(item.get("object_id")))}</div>'
            '<div class="meta">'
            f'<h2>{html.escape(str(item.get("object_id")))}</h2>'
            f'<p>{html.escape(str(item.get("name", "")))} · {html.escape(str(item.get("category", "")))}</p>'
            f'<p>points: <strong>{item.get("point_count")}</strong> · mask cloud: <strong>{item.get("mask_cloud_point_count")}</strong> · selected frames: <strong>{item.get("selected_frame_count")}</strong></p>'
            f'<p>mesh: <strong>{"yes" if item.get("mesh_exists") else "no"}</strong> {html.escape(str(mesh_asset.get("format") or ""))}</p>'
            f'<p>sim mesh: <strong>{"yes" if item.get("simulator_mesh_exists") else "no"}</strong> · frame: <strong>{html.escape(str(mesh_frame))}</strong> · localized: <strong>{str(bool(localization.get("applied"))).lower()}</strong></p>'
            f'<p class="path">{html.escape(str(mesh_path or ""))}</p>'
            f'<p class="path">{html.escape(str(simulator_mesh_path))}</p>'
            f'<div class="badges">{issue_badges(item.get("issues", []))}</div>'
            "</div>"
            "</div>"
            f'<div class="frames">{"".join(frame_items)}</div>'
            "</section>"
        )

    scene_sections = []
    if auto_prompt_preview:
        scene_sections.append(
            '<section class="qa-card"><h2>Auto Prompts</h2>'
            f'{review_image_tag(str(auto_prompt_preview), output_dir, "auto prompts preview")}'
            "</section>"
        )
    scene_sections.append(
        review_gallery(
            "Point Cloud Projection",
            scene_review["reconstruction_preview"]["frames"],
            output_dir,
        )
    )
    scene_sections.append(
        review_gallery(
            "Semantic 3D Mask Projection",
            scene_review["semantic_preview"]["frames"],
            output_dir,
        )
    )
    scene_sections.append(
        review_gallery(
            "3DGS Render Preview",
            scene_review["gsplat_preview"]["renders"],
            output_dir,
        )
    )
    scene_sections.append(
        review_gallery(
            "3DGS Error Preview",
            scene_review["gsplat_preview"]["errors"],
            output_dir,
        )
    )
    scene_sections_html = "\n".join(section for section in scene_sections if section)

    css = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; color: #1f2933; background: #f7f8fa; }
h1 { font-size: 28px; margin: 0 0 8px; }
.summary { margin: 0 0 24px; color: #52606d; }
.qa-card { background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; margin: 16px 0; padding: 16px; }
.qa-card h2 { margin: 0 0 12px; font-size: 18px; }
.qa-card > img { max-width: min(100%, 760px); max-height: 360px; object-fit: contain; background: #eef2f7; border: 1px solid #d9e2ec; }
.qa-gallery { display: flex; gap: 12px; flex-wrap: wrap; }
.qa-frame { width: 220px; font-size: 12px; color: #52606d; }
.qa-frame img { width: 220px; height: 150px; object-fit: contain; background: #eef2f7; border: 1px solid #d9e2ec; }
.object-card { background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; margin: 16px 0; padding: 16px; }
.object-main { display: grid; grid-template-columns: 220px 1fr; gap: 16px; align-items: start; }
.hero img { width: 220px; height: 220px; object-fit: contain; background: #eef2f7; border: 1px solid #d9e2ec; }
.meta h2 { margin: 0 0 8px; font-size: 20px; }
.meta p { margin: 6px 0; }
.path { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; color: #697386; word-break: break-all; }
.badge { display: inline-block; border-radius: 999px; padding: 4px 8px; margin: 3px 4px 3px 0; font-size: 12px; background: #e4e7eb; }
.badge.ok { background: #d8f3dc; color: #1b4332; }
.badge.required { background: #ffe3e3; color: #8a1c1c; }
.badge.warning { background: #fff3bf; color: #6b4f00; }
.frames { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
.frame { width: 128px; font-size: 12px; color: #52606d; }
.frame img { width: 128px; height: 96px; object-fit: contain; background: #eef2f7; border: 1px solid #d9e2ec; }
.missing { display: grid; place-items: center; width: 100%; min-height: 80px; background: #fcebea; color: #8a1c1c; font-size: 12px; text-align: center; }
@media (max-width: 760px) { .object-main { grid-template-columns: 1fr; } .hero img { width: 100%; height: 240px; } }
"""
    html_doc = (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>Video2Mesh Review - {html.escape(str(manifest.get('scene_id')))}</title>"
        f"<style>{css}</style></head><body>"
        f"<h1>Video2Mesh Review: {html.escape(str(manifest.get('scene_id')))}</h1>"
        f"<p class=\"summary\">objects={len(review_objects)} · validation={'PASS' if validation.get('ok') else 'ISSUES'} · issues={len(all_issues)}</p>"
        + scene_sections_html
        + "\n".join(rows)
        +
        f"<p class=\"summary\">JSON: {html.escape(str(review_json_path))}</p>"
        "</body></html>"
    )
    index_path = output_dir / "index.html"
    ensure_dir(index_path.parent)
    index_path.write_text(html_doc, encoding="utf-8")

    manifest["artifacts"]["review_pack"] = str(review_json_path)
    manifest["artifacts"]["review_index"] = str(index_path)
    save_manifest(project_root, manifest)
    print(f"Review pack: {review_json_path}")
    print(f"Review HTML: {index_path}")
    print(f"Objects: {len(review_objects)}; issues: {len(all_issues)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    report = validate_project(project_root, args.strict)
    if args.output:
        write_json(args.output.resolve(), report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if report["ok"] else "FAIL"
        print(f"Video2Mesh validation: {status} ({report['scene_id']})")
        for item in report["items"]:
            marker = "OK" if item["ok"] else "MISS"
            print(f"[{marker}] {item['name']}: {item['detail']}")
        if args.output:
            print(f"Report: {args.output.resolve()}")
    return 0 if report["ok"] else 1


def create_placeholder_meshes_for_smoke(project_root: Path, manifest: dict[str, Any], image_blaster_root: Path, world: str) -> dict[str, Any]:
    world_root = image_blaster_root / "worlds" / world
    objects_dir = project_root / manifest["objects_dir"]
    created = []
    for object_json in sorted(objects_dir.glob("*/object.json")):
        obj = read_json(object_json)
        object_id = slugify(obj.get("object_id") or object_json.parent.name)
        out_dir = ensure_dir(world_root / "output" / object_id)
        bbox = obj.get("bbox_3d") or {}
        size = bbox.get("size") if isinstance(bbox, dict) else None
        side = 0.1
        if isinstance(size, list) and size:
            side = max(0.03, min(1.0, float(max(size)) * 0.5))
        mesh_path = out_dir / f"0-{object_id}.obj"
        mesh_path.write_text(
            "\n".join(
                [
                    f"o {object_id}",
                    "v 0 0 0",
                    f"v {side:.6f} 0 0",
                    f"v 0 {side:.6f} 0",
                    "f 1 2 3",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        metadata_path = out_dir / f".0-{object_id}__model-request.json"
        write_json(
            metadata_path,
            {
                "kind": "3d",
                "index": 0,
                "provider_slug": "video2mesh-smoke-placeholder",
                "status": "completed",
                "output_files": [str(mesh_path)],
                "downloaded_files": [{"path": str(mesh_path), "label": "placeholder-obj"}],
                "notes": "Smoke-test placeholder mesh; replace with image-blaster/FAL output for real assets.",
            },
        )
        created.append({"object_id": object_id, "mesh": str(mesh_path), "metadata": str(metadata_path)})
    return {"created": created, "world_root": str(world_root)}


def append_pipeline_step(steps: list[dict[str, Any]], name: str, status: str, detail: str = "") -> None:
    steps.append({"name": name, "status": status, "detail": detail})


def mast3r_keyframes_dir(project_root: Path, manifest: dict[str, Any]) -> Path:
    local_default = project_root / MAST3R_KEYFRAMES_DIR
    if local_default.exists():
        return local_default
    artifact = manifest.get("artifacts", {}).get("mast3r_keyframes")
    if artifact:
        path = Path(str(artifact))
        return path if path.is_absolute() else project_root / path
    return local_default


def cmd_run_pipeline(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    steps: list[dict[str, Any]] = []
    scene_id = slugify(args.scene_id or project_root.name, fallback="scene")
    world = slugify(args.world or scene_id, fallback="world")
    pipeline_report_path = project_root / "logs" / "pipeline_report.json"

    try:
        if args.make_sample:
            cmd_make_sample(argparse.Namespace(project_root=project_root, scene_id=scene_id))
            append_pipeline_step(steps, "make_sample", "completed", str(project_root))
        elif args.make_scan_video_sample:
            cmd_make_scan_video_sample(
                argparse.Namespace(
                    project_root=project_root,
                    scene_id=scene_id,
                    output_video=args.sample_video_output,
                    frame_count=args.sample_video_frame_count,
                    fps=args.sample_video_fps,
                    fourcc=args.sample_video_fourcc,
                    pixel_step=args.sample_video_pixel_step,
                    extract_every=args.every,
                )
            )
            append_pipeline_step(steps, "make_scan_video_sample", "completed", str(project_root))
        elif not project_manifest_path(project_root).exists():
            init_project(project_root, scene_id, args.video)
            append_pipeline_step(steps, "init", "completed", str(project_root))
        else:
            append_pipeline_step(steps, "init", "skipped", "project manifest already exists")

        manifest = load_manifest(project_root)
        working_frames_dir: Path | None = None
        working_point_cloud: Path | None = None

        if args.extract_frames or args.make_scan_video_sample:
            extract_video = args.video
            if extract_video is None and args.dataset is not None and args.dataset.is_file():
                extract_video = args.dataset
            cmd_extract_frames(
                argparse.Namespace(
                    project_root=project_root,
                    video=extract_video,
                    output_dir=None,
                    every=args.every,
                    max_frames=args.max_frames,
                    overwrite=args.overwrite_frames,
                    renumber=args.renumber_frames,
                )
            )
            append_pipeline_step(steps, "extract_frames", "completed")

        if args.run_mast3r_slam:
            cmd_run_mast3r_slam(
                argparse.Namespace(
                    project_root=project_root,
                    mast3r_root=args.mast3r_root,
                    dataset=args.dataset,
                    video=args.video,
                    config=args.mast3r_config,
                    save_as=args.mast3r_save_as or scene_id,
                    calib=args.calib,
                    width=args.width,
                    height=args.height,
                    fx=args.fx,
                    fy=args.fy,
                    cx=args.cx,
                    cy=args.cy,
                    focal_scale=args.focal_scale,
                    mode=args.mode,
                    use_keyframes_as_scene_frames=False,
                )
            )
            append_pipeline_step(steps, "run_mast3r_slam", "completed")
            manifest = load_manifest(project_root)

        if args.use_mast3r_keyframes:
            candidate = mast3r_keyframes_dir(project_root, manifest)
            if not candidate.exists():
                raise FileNotFoundError(f"--use-mast3r-keyframes requested, but keyframes were not found: {candidate}")
            working_frames_dir = candidate
            append_pipeline_step(steps, "use_mast3r_keyframes", "completed", str(candidate))

        if args.downsample_point_cloud:
            downsample_output = args.downsample_output
            if downsample_output is None:
                downsample_output = project_root / "scene" / "reconstruction" / f"point_cloud_{int(args.downsample_max_points)}.ply"
            else:
                downsample_output = resolve_project_relative_path(downsample_output, project_root)
            cmd_downsample_point_cloud(
                argparse.Namespace(
                    project_root=project_root,
                    point_cloud=args.downsample_source_point_cloud,
                    output=downsample_output,
                    method=args.downsample_method,
                    max_points=args.downsample_max_points,
                    voxel_size=args.downsample_voxel_size,
                    seed=args.downsample_seed,
                    register_as_point_cloud=args.downsample_register_as_point_cloud,
                )
            )
            working_point_cloud = resolve_project_cli_path(downsample_output, project_root)
            append_pipeline_step(steps, "downsample_point_cloud", "completed", str(working_point_cloud))
            manifest = load_manifest(project_root)

        g3dgs_output_path = resolve_project_relative_path(args.g3dgs_output_path, project_root) if args.g3dgs_output_path else None
        g3dgs_source_path = resolve_project_relative_path(args.g3dgs_source_path, project_root) if args.g3dgs_source_path else None
        g3dgs_work_dir = resolve_project_relative_path(args.g3dgs_work_dir, project_root) if args.g3dgs_work_dir else None

        if args.render_reconstruction_preview:
            cmd_render_reconstruction_preview(
                argparse.Namespace(
                    project_root=project_root,
                    frames_dir=working_frames_dir,
                    camera_info=None,
                    point_cloud=working_point_cloud,
                    output_dir=None,
                    max_frames=args.reconstruction_preview_max_frames,
                    max_points_per_frame=args.reconstruction_preview_max_points,
                    point_radius=args.reconstruction_preview_point_radius,
                    alpha=args.reconstruction_preview_alpha,
                    seed=args.reconstruction_preview_seed,
                    extrinsic_type=args.extrinsic_type,
                    occlusion_filter=args.occlusion_filter,
                    depth_tolerance=args.depth_tolerance,
                    relative_depth_tolerance=args.relative_depth_tolerance,
                )
            )
            append_pipeline_step(steps, "render_reconstruction_preview", "completed")
        else:
            append_pipeline_step(steps, "render_reconstruction_preview", "skipped", "--render-reconstruction-preview not set")

        if args.train_gsplat:
            cmd_train_gsplat(
                argparse.Namespace(
                    project_root=project_root,
                    frames_dir=working_frames_dir,
                    camera_info=None,
                    point_cloud=working_point_cloud,
                    output_dir=g3dgs_output_path,
                    iterations=args.gsplat_iterations,
                    max_frames=args.gsplat_max_frames,
                    max_points=args.gsplat_max_points,
                    seed=args.gsplat_seed,
                    device=args.gsplat_device,
                    width=args.gsplat_width,
                    height=args.gsplat_height,
                    extrinsic_type=args.extrinsic_type,
                    init_scale=args.gsplat_init_scale,
                    min_scale=args.gsplat_min_scale,
                    max_scale=args.gsplat_max_scale,
                    init_opacity_logit=args.gsplat_init_opacity_logit,
                    lr_position=args.gsplat_lr_position,
                    lr_color=args.gsplat_lr_color,
                    lr_scale=args.gsplat_lr_scale,
                    lr_opacity=args.gsplat_lr_opacity,
                    alpha_reg=args.gsplat_alpha_reg,
                    log_every=args.gsplat_log_every,
                    register_mode=args.mode,
                )
            )
            append_pipeline_step(steps, "train_gsplat", "completed")
        elif args.g3dgs_command_template or args.prepare_3dgs_source:
            cmd_run_3dgs(
                argparse.Namespace(
                    project_root=project_root,
                    source_path=g3dgs_source_path,
                    output_path=g3dgs_output_path,
                    work_dir=g3dgs_work_dir,
                    command_template=args.g3dgs_command_template,
                    prepare_only=args.g3dgs_prepare_only,
                    frames_dir=working_frames_dir,
                    camera_info=None,
                    point_cloud=working_point_cloud,
                    camera_model=args.camera_model,
                    extrinsic_type=args.extrinsic_type,
                    image_mode=args.image_mode,
                    register_mode=args.mode,
                    no_register=args.no_register_3dgs,
                )
            )
            append_pipeline_step(steps, "run_3dgs", "completed" if args.g3dgs_command_template else "prepared")
        else:
            append_pipeline_step(steps, "video_to_3dgs", "skipped", "no --train-gsplat, --g3dgs-command-template, or --prepare-3dgs-source")

        if args.render_gsplat_preview:
            cmd_render_gsplat_preview(
                argparse.Namespace(
                    project_root=project_root,
                    splat_ply=None,
                    frames_dir=working_frames_dir,
                    camera_info=None,
                    output_dir=None,
                    max_frames=args.preview_max_frames,
                    width=args.preview_width,
                    height=args.preview_height,
                    device=args.gsplat_device,
                    extrinsic_type=args.extrinsic_type,
                    background=args.preview_background,
                    error_gain=args.preview_error_gain,
                )
            )
            append_pipeline_step(steps, "render_gsplat_preview", "completed")
        else:
            append_pipeline_step(steps, "render_gsplat_preview", "skipped", "--render-gsplat-preview not set")

        prompts_path = args.prompts
        if args.auto_prompts and not prompts_path:
            cmd_auto_prompts(
                argparse.Namespace(
                    project_root=project_root,
                    frames_dir=working_frames_dir,
                    output=args.auto_prompts_output,
                    preview_output=None,
                    frame_id=args.auto_prompt_frame_id,
                    frame_index=args.auto_prompt_frame_index,
                    method=args.auto_prompt_method,
                    max_objects=args.auto_prompt_max_objects,
                    min_area_ratio=args.auto_prompt_min_area_ratio,
                    max_area_ratio=args.auto_prompt_max_area_ratio,
                    min_width=args.auto_prompt_min_width,
                    min_height=args.auto_prompt_min_height,
                    nms_iou=args.auto_prompt_nms_iou,
                    containment_overlap=args.auto_prompt_containment_overlap,
                    containment_area_ratio=args.auto_prompt_containment_area_ratio,
                    object_prefix=args.auto_prompt_object_prefix,
                    category=args.auto_prompt_category,
                    color_distance_threshold=args.auto_prompt_color_distance_threshold,
                    min_saturation=args.auto_prompt_min_saturation,
                    morph_kernel=args.auto_prompt_morph_kernel,
                    sam_checkpoint=args.sam_checkpoint,
                    sam_model_type=args.sam_model_type,
                    sam_device=args.sam_device,
                    overwrite=True,
                )
            )
            manifest = load_manifest(project_root)
            prompts_path = Path(manifest.get("artifacts", {}).get("tracking_prompts", project_root / "masks" / "auto_prompts.json"))
            append_pipeline_step(steps, "auto_prompts", "completed", str(prompts_path))
        elif args.auto_prompts:
            append_pipeline_step(steps, "auto_prompts", "skipped", "--prompts provided")
        else:
            append_pipeline_step(steps, "auto_prompts", "skipped", "--auto-prompts not set")

        if prompts_path and not args.skip_track_masks:
            cmd_track_masks(
                argparse.Namespace(
                    project_root=project_root,
                    prompts=prompts_path,
                    frames_dir=working_frames_dir,
                    output_dir=None,
                    bbox_format=args.bbox_format,
                    template_padding=args.template_padding,
                    search_margin=args.search_margin,
                    min_score=args.min_score,
                    keep_low_score=args.keep_low_score,
                    grabcut=args.grabcut,
                    grabcut_iters=args.grabcut_iters,
                    mask_backend=args.mask_backend,
                    sam_checkpoint=args.sam_checkpoint,
                    sam_model_type=args.sam_model_type,
                    sam_device=args.sam_device,
                    sam_multimask=args.sam_multimask,
                    max_frames=args.track_max_frames,
                    clear_output=args.clear_mask_output or bool(args.auto_prompts and not args.prompts),
                )
            )
            append_pipeline_step(steps, "track_masks", "completed")
        else:
            append_pipeline_step(steps, "track_masks", "skipped", "no prompts or --skip-track-masks")

        if not args.skip_fuse_masks:
            cmd_fuse_masks(
                argparse.Namespace(
                    project_root=project_root,
                    point_cloud=working_point_cloud,
                    camera_info=None,
                    mask_root=None,
                    object_labels=None,
                    extrinsic_type=args.extrinsic_type,
                    mask_threshold=args.mask_threshold,
                    min_votes=args.min_votes,
                    occlusion_filter=args.occlusion_filter,
                    depth_tolerance=args.depth_tolerance,
                    relative_depth_tolerance=args.relative_depth_tolerance,
                )
            )
            append_pipeline_step(steps, "fuse_masks", "completed")
        else:
            append_pipeline_step(steps, "fuse_masks", "skipped", "--skip-fuse-masks")

        if not args.skip_export_splat_masks:
            cmd_export_splat_masks(
                argparse.Namespace(
                    project_root=project_root,
                    splat_ply=None,
                    mask_source_ply=working_point_cloud,
                    transfer_mode=args.transfer_mode,
                    max_transfer_distance=args.max_transfer_distance,
                    output=None,
                )
            )
            append_pipeline_step(steps, "export_splat_masks", "completed")
        else:
            append_pipeline_step(steps, "export_splat_masks", "skipped", "--skip-export-splat-masks")

        if not args.skip_export_viewer_plys and not args.skip_export_splat_masks:
            cmd_export_viewer_plys(
                argparse.Namespace(
                    project_root=project_root,
                    kind="all",
                    splat_ply=None,
                    output_dir=None,
                    prefix=None,
                    include_labels=False,
                )
            )
            append_pipeline_step(steps, "export_viewer_plys", "completed")
        elif args.skip_export_viewer_plys:
            append_pipeline_step(steps, "export_viewer_plys", "skipped", "--skip-export-viewer-plys")
        else:
            append_pipeline_step(steps, "export_viewer_plys", "skipped", "semantic splat export skipped")

        if args.render_semantic_preview and not args.skip_export_splat_masks:
            cmd_render_semantic_preview(
                argparse.Namespace(
                    project_root=project_root,
                    semantic_splats_ply=None,
                    semantic_manifest=None,
                    frames_dir=working_frames_dir,
                    camera_info=None,
                    output_dir=None,
                    max_frames=args.semantic_preview_max_frames,
                    max_points_per_frame=args.semantic_preview_max_points,
                    point_radius=args.semantic_preview_point_radius,
                    alpha=args.semantic_preview_alpha,
                    seed=args.semantic_preview_seed,
                    extrinsic_type=args.extrinsic_type,
                    occlusion_filter=args.occlusion_filter,
                    depth_tolerance=args.depth_tolerance,
                    relative_depth_tolerance=args.relative_depth_tolerance,
                    include_background=args.semantic_preview_include_background,
                )
            )
            append_pipeline_step(steps, "render_semantic_preview", "completed")
        elif args.render_semantic_preview:
            append_pipeline_step(steps, "render_semantic_preview", "skipped", "semantic splat export skipped")
        else:
            append_pipeline_step(steps, "render_semantic_preview", "skipped", "--render-semantic-preview not set")

        if not args.skip_object_mask_clouds and not args.skip_fuse_masks:
            cmd_export_object_mask_clouds(
                argparse.Namespace(
                    project_root=project_root,
                    point_cloud=working_point_cloud,
                    output_dir=None,
                    skip_missing=False,
                )
            )
            append_pipeline_step(steps, "export_object_mask_clouds", "completed")
        else:
            reason = "--skip-object-mask-clouds" if args.skip_object_mask_clouds else "fuse masks skipped"
            append_pipeline_step(steps, "export_object_mask_clouds", "skipped", reason)

        if not args.skip_select_frames:
            cmd_select_frames(
                argparse.Namespace(
                    project_root=project_root,
                    frames_dir=working_frames_dir,
                    top_k=args.top_k,
                    use_sharpness=True,
                    hit_weight=1.0,
                    area_weight=0.001,
                    sharpness_weight=0.0001,
                )
            )
            append_pipeline_step(steps, "select_frames", "completed")
        else:
            append_pipeline_step(steps, "select_frames", "skipped", "--skip-select-frames")

        if not args.skip_object_images:
            cmd_prepare_object_images(
                argparse.Namespace(
                    project_root=project_root,
                    top_k=args.top_k,
                    padding_ratio=args.crop_padding_ratio,
                    min_padding=args.crop_min_padding,
                    square=True,
                    transparent=args.transparent_crops,
                    mask_threshold=args.mask_threshold,
                    background=args.crop_background,
                    skip_missing=False,
                )
            )
            append_pipeline_step(steps, "prepare_object_images", "completed")
        else:
            append_pipeline_step(steps, "prepare_object_images", "skipped", "--skip-object-images")

        if not args.skip_export_image_blaster:
            cmd_export_image_blaster(
                argparse.Namespace(
                    project_root=project_root,
                    world=world,
                    image_blaster_root=args.image_blaster_root,
                    provider=args.provider,
                    reference_only=args.reference_only,
                    skip_missing=False,
                    use_object_crop=True,
                    auto_prepare_crops=False,
                    crop_top_k=args.top_k,
                    crop_padding_ratio=args.crop_padding_ratio,
                    crop_min_padding=args.crop_min_padding,
                    transparent_crops=args.transparent_crops,
                    mask_threshold=args.mask_threshold,
                    crop_background=args.crop_background,
                )
            )
            append_pipeline_step(steps, "export_image_blaster", "completed")
        else:
            append_pipeline_step(steps, "export_image_blaster", "skipped", "--skip-export-image-blaster")

        if not args.skip_export_image_blaster:
            cmd_mesh_commands(
                argparse.Namespace(
                    project_root=project_root,
                    image_blaster_root=args.image_blaster_root,
                    provider=args.provider,
                    reference_only=args.reference_only,
                    run=args.run_mesh_commands,
                )
            )
            append_pipeline_step(steps, "mesh_commands", "completed" if not args.run_mesh_commands else "ran")
        else:
            append_pipeline_step(steps, "mesh_commands", "skipped", "image-blaster export skipped")

        if args.create_placeholder_meshes:
            manifest = load_manifest(project_root)
            placeholder = create_placeholder_meshes_for_smoke(project_root, manifest, args.image_blaster_root.resolve(), world)
            append_pipeline_step(steps, "create_placeholder_meshes", "completed", f"{len(placeholder['created'])} mesh(es)")

        if args.reconstruct_mask_meshes:
            cmd_reconstruct_object_meshes(
                argparse.Namespace(
                    project_root=project_root,
                    output_dir=None,
                    method=args.mask_mesh_method,
                    format=args.mask_mesh_format,
                    min_points=args.mask_mesh_min_points,
                    min_extent=args.mask_mesh_min_extent,
                    bbox_padding_ratio=args.mask_mesh_bbox_padding_ratio,
                    voxel_size=args.mask_mesh_voxel_size,
                    remove_outliers=args.mask_mesh_remove_outliers,
                    outlier_nb_neighbors=args.mask_mesh_outlier_nb_neighbors,
                    outlier_std_ratio=args.mask_mesh_outlier_std_ratio,
                    alpha=args.mask_mesh_alpha,
                    alpha_multiplier=args.mask_mesh_alpha_multiplier,
                    ball_radius_multipliers=args.mask_mesh_ball_radius_multipliers,
                    normal_radius=args.mask_mesh_normal_radius,
                    ascii=args.mask_mesh_ascii,
                    copy_to_assets=True,
                    mode=args.mode,
                    skip_missing=args.skip_missing_meshes,
                    skip_failed=args.skip_failed_mask_meshes,
                )
            )
            append_pipeline_step(steps, "reconstruct_object_meshes", "completed")
        else:
            append_pipeline_step(steps, "reconstruct_object_meshes", "skipped", "--reconstruct-mask-meshes not set")

        should_import_meshes = args.import_meshes or args.mesh_root is not None or args.create_placeholder_meshes
        if should_import_meshes and not args.skip_import_meshes:
            cmd_import_object_meshes(
                argparse.Namespace(
                    project_root=project_root,
                    image_blaster_root=args.image_blaster_root,
                    world=world,
                    mesh_root=args.mesh_root,
                    mode=args.mode,
                    copy_to_assets=True,
                    skip_missing=args.skip_missing_meshes,
                )
            )
            append_pipeline_step(steps, "import_object_meshes", "completed")
        elif should_import_meshes:
            append_pipeline_step(steps, "import_object_meshes", "skipped", "--skip-import-meshes")
        else:
            append_pipeline_step(steps, "import_object_meshes", "skipped", "mesh import not requested")

        meshes_available = bool(args.reconstruct_mask_meshes or (should_import_meshes and not args.skip_import_meshes))
        if meshes_available:
            if not args.skip_simulator_assets:
                cmd_export_simulator_assets(
                    argparse.Namespace(
                        project_root=project_root,
                        semantic_splats_ply=None,
                        scene_scale=args.scene_scale,
                        body_type=args.body_type,
                        collider=args.collider,
                        copy_meshes=True,
                        ascii_meshes=args.simulator_ascii_meshes,
                        fit_object_local_meshes_to_bbox=args.fit_object_local_meshes_to_bbox,
                        fit_axis=args.fit_axis,
                        mode=args.mode,
                    )
                )
                append_pipeline_step(steps, "export_simulator_assets", "completed")

                if not args.skip_simulator_adapters:
                    cmd_export_simulator_adapter(
                        argparse.Namespace(
                            project_root=project_root,
                            bundle=None,
                            format=args.simulator_format,
                            output_dir=None,
                            body_type=args.body_type,
                            default_mass=args.default_mass,
                            copy_assets=True,
                            mode=args.mode,
                        )
                    )
                    append_pipeline_step(steps, "export_simulator_adapters", "completed", ",".join(args.simulator_format))
                else:
                    append_pipeline_step(steps, "export_simulator_adapters", "skipped", "--skip-simulator-adapters")
            else:
                append_pipeline_step(steps, "export_simulator_assets", "skipped", "--skip-simulator-assets")
                append_pipeline_step(steps, "export_simulator_adapters", "skipped", "simulator assets skipped")
        else:
            append_pipeline_step(steps, "export_simulator_assets", "skipped", "mesh import not requested")
            append_pipeline_step(steps, "export_simulator_adapters", "skipped", "mesh import not requested")

        validate_report = None
        validate_ok = None
        if not args.skip_validate:
            validate_report = validate_project(project_root, strict=False)
            validate_ok = bool(validate_report["ok"])
            write_json(project_root / "simulator_assets" / "validation_report.json", validate_report)
            append_pipeline_step(steps, "validate", "passed" if validate_ok else "failed", ",".join(validate_report["required_failed"]))

        report = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "project_root": str(project_root),
            "scene_id": scene_id,
            "world": world,
            "steps": steps,
            "validate_ok": validate_ok,
        }
        write_json(pipeline_report_path, report)
        print(f"Pipeline report: {pipeline_report_path}")
        if validate_ok is False and not args.allow_incomplete:
            print("Pipeline validation failed; pass --allow-incomplete to return success for partial runs.")
            return 1
        return 0
    except Exception:
        write_json(
            pipeline_report_path,
            {
                "schema_version": DEFAULT_SCHEMA_VERSION,
                "project_root": str(project_root),
                "scene_id": scene_id,
                "world": world,
                "steps": steps,
                "status": "failed",
            },
        )
        raise


def cmd_run_local(args: argparse.Namespace) -> int:
    fuse_args = argparse.Namespace(
        project_root=args.project_root,
        point_cloud=args.point_cloud,
        camera_info=args.camera_info,
        mask_root=args.mask_root,
        object_labels=args.object_labels,
        extrinsic_type=args.extrinsic_type,
        mask_threshold=args.mask_threshold,
        min_votes=args.min_votes,
        occlusion_filter=args.occlusion_filter,
        depth_tolerance=args.depth_tolerance,
        relative_depth_tolerance=args.relative_depth_tolerance,
    )
    cmd_fuse_masks(fuse_args)
    select_args = argparse.Namespace(
        project_root=args.project_root,
        frames_dir=args.frames_dir,
        top_k=args.top_k,
        use_sharpness=True,
        hit_weight=1.0,
        area_weight=0.001,
        sharpness_weight=0.0001,
    )
    cmd_select_frames(select_args)
    export_args = argparse.Namespace(
        project_root=args.project_root,
        world=args.world,
        image_blaster_root=args.image_blaster_root,
        provider=args.provider,
        reference_only=False,
        skip_missing=True,
        use_object_crop=True,
        auto_prepare_crops=True,
        crop_top_k=args.top_k,
        crop_padding_ratio=0.18,
        crop_min_padding=24,
        transparent_crops=True,
        mask_threshold=args.mask_threshold,
        crop_background=[255, 255, 255],
    )
    cmd_export_image_blaster(export_args)
    return 0


def add_common_project_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", type=Path, required=True, help="Video2Mesh project directory.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video2mesh",
        description="Prototype pipeline for video scan to semantic 3D masks and mesh assets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create a Video2Mesh project directory.")
    add_common_project_arg(p)
    p.add_argument("--scene-id", required=True)
    p.add_argument("--video", type=Path)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("make-sample", help="Create a synthetic sample project for smoke tests.")
    add_common_project_arg(p)
    p.add_argument("--scene-id", default="synthetic-room")
    p.set_defaults(func=cmd_make_sample)

    p = sub.add_parser("make-scan-video-sample", help="Create a synthetic scan video plus matching camera/point-cloud artifacts.")
    add_common_project_arg(p)
    p.add_argument("--scene-id", default="synthetic-scan-video")
    p.add_argument("--output-video", type=Path, help="Defaults to inputs/synthetic_scan.mp4.")
    p.add_argument("--frame-count", type=int, default=10)
    p.add_argument("--fps", type=float, default=6.0)
    p.add_argument("--fourcc", default="mp4v")
    p.add_argument("--pixel-step", type=float, default=1.5)
    p.add_argument("--extract-every", type=int, default=3, help="Recommended extraction stride used to create matching camera entries.")
    p.set_defaults(func=cmd_make_scan_video_sample)

    p = sub.add_parser("make-colmap-sample", help="Create a tiny COLMAP text model sample.")
    p.add_argument("--output-dir", type=Path, required=True)
    p.set_defaults(func=cmd_make_colmap_sample)

    p = sub.add_parser("extract-frames", help="Extract frames from a scan video.")
    add_common_project_arg(p)
    p.add_argument("--video", type=Path)
    p.add_argument("--output-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--every", type=int, default=30)
    p.add_argument("--max-frames", type=int, default=0)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--renumber", action=argparse.BooleanOptionalAction, default=True, help="Write contiguous frame ids while preserving source indices in scene/frames_manifest.json.")
    p.set_defaults(func=cmd_extract_frames)

    p = sub.add_parser("register-reconstruction", help="Register point cloud, camera info, or 3DGS artifacts.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--scene-3dgs", type=Path)
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_register_reconstruction)

    p = sub.add_parser("downsample-point-cloud", help="Create a lightweight ASCII PLY point cloud for faster 3DGS/mask-fusion experiments.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path, help="Defaults to scene/reconstruction/point_cloud.ply.")
    p.add_argument("--output", type=Path, help="Defaults to scene/reconstruction/point_cloud_<max_points>.ply or voxel name.")
    p.add_argument("--method", choices=["random", "voxel"], default="random")
    p.add_argument("--max-points", type=int, default=10000)
    p.add_argument("--voxel-size", type=float, default=0.02)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--register-as-point-cloud", action="store_true", help="Replace the project's main scene point cloud with the downsampled output.")
    p.set_defaults(func=cmd_downsample_point_cloud)

    p = sub.add_parser("import-colmap", help="Import a COLMAP text sparse model into Video2Mesh protocol.")
    add_common_project_arg(p)
    p.add_argument("--sparse-dir", type=Path, required=True, help="Directory containing cameras.txt/images.txt/points3D.txt.")
    p.add_argument("--images-dir", type=Path, help="Optional source images directory to copy/symlink into scene/frames.")
    p.add_argument("--frame-id-regex", help="Optional regex to extract frame id from image name.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_import_colmap)

    p = sub.add_parser("export-colmap", help="Export Video2Mesh cameras/frames/point cloud as a COLMAP text dataset.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to <project-root>/exports/colmap_text.")
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-model", choices=["PINHOLE", "SIMPLE_PINHOLE"], default="PINHOLE")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--mode", choices=["copy", "symlink", "none"], default="copy")
    p.set_defaults(func=cmd_export_colmap)

    p = sub.add_parser("register-3dgs", help="Register a 3DGS output directory or PLY artifact.")
    add_common_project_arg(p)
    p.add_argument("--path", type=Path, required=True)
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_register_3dgs)

    p = sub.add_parser("run-3dgs", help="Prepare COLMAP source and optionally run/register an external 3DGS trainer.")
    add_common_project_arg(p)
    p.add_argument("--source-path", type=Path, help="COLMAP-style source dir to create. Defaults to <project>/external/3dgs/colmap_source.")
    p.add_argument("--output-path", type=Path, help="3DGS trainer output dir. Defaults to scene/reconstruction/3dgs.")
    p.add_argument("--work-dir", type=Path, help="Working dir for command execution and run manifest.")
    p.add_argument("--command-template", help="Shell command with {source_path}, {output_path}, {project_root}, {work_dir}, {scene_id}.")
    p.add_argument("--prepare-only", action="store_true", help="Write source/command manifest without executing the command.")
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-model", choices=["PINHOLE", "SIMPLE_PINHOLE"], default="PINHOLE")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--image-mode", choices=["copy", "symlink", "none"], default="copy")
    p.add_argument("--register-mode", choices=["copy", "symlink"], default="copy")
    p.add_argument("--no-register", action="store_true", help="Do not call register-3dgs after a successful command.")
    p.set_defaults(func=cmd_run_3dgs)

    p = sub.add_parser("prepare-high-quality-3dgs-job", help="Prepare a provider-specific high-quality 3DGS training job without running it.")
    add_common_project_arg(p)
    p.add_argument("--provider", default="graphdeco", help="Provider/tool name: graphdeco, nerfstudio, gsplat, etc.")
    p.add_argument("--source-path", type=Path, help="COLMAP-style source dir to create. Defaults to external/high_quality_3dgs/colmap_source.")
    p.add_argument("--output-path", type=Path, help="Expected trainer output dir. Defaults to scene/reconstruction/3dgs_<provider>.")
    p.add_argument("--work-dir", type=Path, help="Defaults to external/high_quality_3dgs.")
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-model", choices=["PINHOLE", "SIMPLE_PINHOLE"], default="PINHOLE")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--image-mode", choices=["copy", "symlink", "none"], default="symlink")
    p.add_argument("--command-template", help="Optional command template with {provider}, {source_path}, {output_path}, {project_root}, {work_dir}, {scene_id}, {log_path}.")
    p.set_defaults(func=cmd_prepare_high_quality_3dgs_job)

    p = sub.add_parser("render-reconstruction-preview", help="Project the point cloud into camera frames and write alignment overlay images/metrics.")
    add_common_project_arg(p)
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--camera-info", type=Path, help="Defaults to scene/cameras/camera_info.json.")
    p.add_argument("--point-cloud", type=Path, help="Defaults to scene/reconstruction/point_cloud.ply.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/reconstruction_preview.")
    p.add_argument("--max-frames", type=int, default=3)
    p.add_argument("--max-points-per-frame", type=int, default=5000)
    p.add_argument("--point-radius", type=int, default=2)
    p.add_argument("--alpha", type=float, default=0.85)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--occlusion-filter", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--depth-tolerance", type=float, default=0.03)
    p.add_argument("--relative-depth-tolerance", type=float, default=0.01)
    p.set_defaults(func=cmd_render_reconstruction_preview)

    p = sub.add_parser("train-gsplat", help="Train a minimal gsplat baseline from project frames/cameras/point cloud.")
    add_common_project_arg(p)
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--output-dir", type=Path, help="Defaults to scene/reconstruction/3dgs.")
    p.add_argument("--iterations", type=int, default=30)
    p.add_argument("--max-frames", type=int, default=3)
    p.add_argument("--max-points", type=int, default=20000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    p.add_argument("--width", type=int, help="Optional render/training width; defaults to camera intrinsic width.")
    p.add_argument("--height", type=int, help="Optional render/training height; defaults to camera intrinsic height.")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--init-scale", type=float, default=0.0, help="Initial Gaussian scale; <=0 estimates from point spacing.")
    p.add_argument("--min-scale", type=float, default=0.001)
    p.add_argument("--max-scale", type=float, default=0.2)
    p.add_argument("--init-opacity-logit", type=float, default=0.0)
    p.add_argument("--lr-position", type=float, default=1e-4)
    p.add_argument("--lr-color", type=float, default=3e-2)
    p.add_argument("--lr-scale", type=float, default=1e-3)
    p.add_argument("--lr-opacity", type=float, default=1e-2)
    p.add_argument("--alpha-reg", type=float, default=0.0)
    p.add_argument("--log-every", type=int, default=10)
    p.add_argument("--register-mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_train_gsplat)

    p = sub.add_parser("render-gsplat-preview", help="Render registered gsplat PLY from project cameras and write preview metrics/images.")
    add_common_project_arg(p)
    p.add_argument("--splat-ply", type=Path, help="Renderable ASCII gsplat PLY. Defaults to manifest artifacts.scene_3dgs_ply.")
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--camera-info", type=Path, help="Defaults to scene/cameras/camera_info.json.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/gsplat_preview.")
    p.add_argument("--max-frames", type=int, default=3)
    p.add_argument("--width", type=int, help="Optional preview width; defaults to camera intrinsic width.")
    p.add_argument("--height", type=int, help="Optional preview height; defaults to camera intrinsic height.")
    p.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--background", choices=["target_mean", "white", "black"], default="target_mean")
    p.add_argument("--error-gain", type=float, default=4.0)
    p.set_defaults(func=cmd_render_gsplat_preview)

    p = sub.add_parser("import-mast3r-slam", help="Import MASt3R-SLAM logs/<seq>.txt and <seq>.ply outputs.")
    add_common_project_arg(p)
    p.add_argument("--trajectory", type=Path, required=True, help="MASt3R-SLAM trajectory txt: timestamp x y z qx qy qz qw.")
    p.add_argument("--reconstruction-ply", type=Path, help="Optional MASt3R-SLAM reconstruction PLY.")
    p.add_argument("--frames-dir", type=Path, help="Optional source frames/keyframes directory.")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fx", type=float)
    p.add_argument("--fy", type=float)
    p.add_argument("--cx", type=float)
    p.add_argument("--cy", type=float)
    p.add_argument("--focal-scale", type=float, default=1.2)
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument(
        "--use-keyframes-as-scene-frames",
        action="store_true",
        help="Copy MASt3R-SLAM keyframes into scene/frames. By default they are stored under scene/mast3r_keyframes.",
    )
    p.add_argument("--clear-keyframes-output", action=argparse.BooleanOptionalAction, default=True)
    p.set_defaults(func=cmd_import_mast3r_slam)

    p = sub.add_parser("run-mast3r-slam", help="Run MASt3R-SLAM, then import its trajectory/PLY/keyframes.")
    add_common_project_arg(p)
    p.add_argument("--mast3r-root", type=Path, default=Path("/root/autodl-tmp/workspace/MASt3R-SLAM"))
    p.add_argument("--dataset", type=Path, help="MASt3R-SLAM input: an .mp4/.mov/.avi video or a directory of .png frames.")
    p.add_argument("--video", type=Path, help="Alias for --dataset when the input is a scan video.")
    p.add_argument("--config", type=Path, default=Path("config/base.yaml"))
    p.add_argument("--save-as", help="MASt3R-SLAM logs/<save-as> directory. Defaults to project scene_id.")
    p.add_argument("--calib", type=Path, help="Optional MASt3R-SLAM intrinsics yaml.")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fx", type=float)
    p.add_argument("--fy", type=float)
    p.add_argument("--cx", type=float)
    p.add_argument("--cy", type=float)
    p.add_argument("--focal-scale", type=float, default=1.2)
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument(
        "--use-keyframes-as-scene-frames",
        action="store_true",
        help="Copy MASt3R-SLAM keyframes into scene/frames. By default they are stored under scene/mast3r_keyframes.",
    )
    p.set_defaults(func=cmd_run_mast3r_slam)

    p = sub.add_parser("track-masks", help="Generate frame-level 2D object masks from bbox prompts.")
    add_common_project_arg(p)
    p.add_argument("--prompts", type=Path, required=True, help="JSON prompts with object ids and bbox prompts.")
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--output-dir", type=Path, help="Defaults to masks/2d.")
    p.add_argument("--clear-output", action="store_true", help="Remove existing mask output dir before writing tracked masks.")
    p.add_argument("--bbox-format", choices=["xyxy", "xywh"], default="xyxy")
    p.add_argument("--template-padding", type=int, default=12)
    p.add_argument("--search-margin", type=int, default=80)
    p.add_argument("--min-score", type=float, default=-1.0, help="Skip propagated masks below this template score unless --keep-low-score is set.")
    p.add_argument("--keep-low-score", action="store_true")
    p.add_argument("--grabcut", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--grabcut-iters", type=int, default=3)
    p.add_argument("--mask-backend", choices=["opencv", "sam", "auto"], default="opencv", help="Mask generator after bbox tracking. SAM uses bbox prompts when --sam-checkpoint is set.")
    p.add_argument("--sam-checkpoint", type=Path, help="Segment Anything checkpoint path for --mask-backend sam/auto.")
    p.add_argument("--sam-model-type", default="vit_h", help="SAM model type, e.g. vit_h/vit_l/vit_b.")
    p.add_argument("--sam-device", default="auto", help="SAM device: auto/cuda/cpu.")
    p.add_argument("--sam-multimask", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--max-frames", type=int, default=0)
    p.set_defaults(func=cmd_track_masks)

    p = sub.add_parser("prepare-video-segmentation-jobs", help="Prepare frame/prompt jobs for external video segmentation tools such as SAM2/DEVA/XMem.")
    add_common_project_arg(p)
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--prompts", type=Path, help="Prompt JSON. Defaults to manifest artifacts.tracking_prompts when available.")
    p.add_argument("--provider", default="external_video_segmentation", help="External provider/tool name, e.g. sam2, deva, xmem, grounded-sam.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/video_segmentation_jobs.")
    p.add_argument("--mask-output-root", type=Path, help="Where the external tool should write masks. Defaults to masks/2d.")
    p.add_argument("--max-frames", type=int, default=0)
    p.add_argument(
        "--command-template",
        help=(
            "Optional shell command with {job_path}, {project_root}, {frames_dir}, {prompts}, "
            "{mask_output_root}, {provider}."
        ),
    )
    p.set_defaults(func=cmd_prepare_video_segmentation_jobs)

    p = sub.add_parser("import-video-segmentation-masks", help="Import external video segmentation masks into the standard masks/2d layout.")
    add_common_project_arg(p)
    p.add_argument("--source-root", type=Path, help="Directory containing <object_id>/<frame>.png masks or <frame>_<object>.png masks.")
    p.add_argument("--source-manifest", type=Path, help="JSON manifest listing external masks.")
    p.add_argument("--provider", default="external_video_segmentation")
    p.add_argument("--output-dir", type=Path, help="Defaults to masks/2d.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument("--clear-output", action="store_true", help="Remove output masks before importing.")
    p.add_argument("--skip-missing", action="store_true")
    p.set_defaults(func=cmd_import_video_segmentation_masks)

    p = sub.add_parser("auto-prompts", help="Generate bbox tracking prompts automatically from a representative frame.")
    add_common_project_arg(p)
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--output", type=Path, help="Defaults to masks/auto_prompts.json.")
    p.add_argument("--preview-output", type=Path, help="Defaults to masks/auto_prompts_preview.png.")
    p.add_argument("--frame-id", help="Frame id to use for prompt discovery.")
    p.add_argument("--frame-index", type=int, default=0, help="Frame index to use when --frame-id is not set.")
    p.add_argument("--method", choices=["auto", "sam", "opencv"], default="auto")
    p.add_argument("--max-objects", type=int, default=12)
    p.add_argument("--min-area-ratio", type=float, default=0.002)
    p.add_argument("--max-area-ratio", type=float, default=0.45)
    p.add_argument("--min-width", type=int, default=12)
    p.add_argument("--min-height", type=int, default=12)
    p.add_argument("--nms-iou", type=float, default=0.65)
    p.add_argument("--containment-overlap", type=float, default=0.9, help="Suppress a larger candidate if it mostly contains a smaller candidate.")
    p.add_argument("--containment-area-ratio", type=float, default=1.8)
    p.add_argument("--object-prefix", default="auto_object")
    p.add_argument("--category", default="unknown")
    p.add_argument("--color-distance-threshold", type=float, default=35.0)
    p.add_argument("--min-saturation", type=int, default=45)
    p.add_argument("--morph-kernel", type=int, default=5)
    p.add_argument("--sam-checkpoint", type=Path)
    p.add_argument("--sam-model-type", default="vit_h")
    p.add_argument("--sam-device", default="auto")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_auto_prompts)

    p = sub.add_parser("prepare-object-labeling-jobs", help="Prepare per-object VLM/open-vocabulary semantic labeling jobs from crops and selected frames.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/object_labeling_jobs.")
    p.add_argument("--provider", default="external_vlm")
    p.add_argument("--max-images", type=int, default=4, help="Maximum evidence images stored per object; 0 keeps all.")
    p.add_argument("--include-background", action="store_true", help="Also prepare jobs for background_structure records.")
    p.add_argument("--allow-missing-images", action="store_true", help="Write jobs even when no crop/selected frame is available.")
    p.set_defaults(func=cmd_prepare_object_labeling_jobs)

    p = sub.add_parser("import-object-labels", help="Import object names/categories/descriptions from JSON labels or VLM output.")
    add_common_project_arg(p)
    p.add_argument("--labels", type=Path, required=True, help="JSON map/list/object-with-objects labels keyed by object_id.")
    p.add_argument("--output", type=Path, help="Defaults to masks/object_labels.json.")
    p.add_argument("--overwrite", action=argparse.BooleanOptionalAction, default=True, help="Overwrite existing unknown/empty fields by default.")
    p.set_defaults(func=cmd_import_object_labels)

    p = sub.add_parser("prepare-scene-structure-jobs", help="Prepare point-cloud/layout jobs for external scene structure segmentation.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path, help="Defaults to scene/reconstruction/point_cloud.ply.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/scene_structure_jobs.")
    p.add_argument("--provider", default="external_scene_structure", help="External provider/tool name, e.g. spatiallm, pq3d, ov3dseg.")
    p.add_argument("--max-frames", type=int, default=0, help="Maximum source frames to list in the job; 0 keeps all.")
    p.add_argument(
        "--command-template",
        help=(
            "Optional shell command with {job_path}, {project_root}, {point_cloud}, "
            "{camera_info}, {frames_dir}, {provider}, {output_manifest}."
        ),
    )
    p.set_defaults(func=cmd_prepare_scene_structure_jobs)

    p = sub.add_parser("import-scene-structure-masks", help="Import external scene structure/layout point-index masks as background_structure records.")
    add_common_project_arg(p)
    p.add_argument("--source-manifest", type=Path, required=True, help="JSON list/map or object with structures/objects entries.")
    p.add_argument("--point-cloud", type=Path, help="Point cloud whose vertex order the imported indices reference. Defaults to manifest or source-manifest point_cloud.")
    p.add_argument("--provider", default="external_scene_structure")
    p.add_argument("--object-labels", type=Path, help="Defaults to masks/object_labels.json.")
    p.add_argument("--cloud-output-dir", type=Path, help="Defaults to simulator_assets/object_masks_3d.")
    p.add_argument("--min-points", type=int, default=1)
    p.add_argument("--skip-small", action="store_true", help="Skip structures below --min-points instead of failing.")
    p.add_argument("--replace-manifest", action="store_true", help="Replace existing background_structures.json instead of merging.")
    p.set_defaults(func=cmd_import_scene_structure_masks)

    p = sub.add_parser("fuse-masks", help="Fuse frame-level 2D masks onto a point cloud.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--mask-root", type=Path)
    p.add_argument("--object-labels", type=Path)
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--mask-threshold", type=int, default=128)
    p.add_argument("--min-votes", type=int, default=1)
    p.add_argument("--occlusion-filter", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--depth-tolerance", type=float, default=0.03)
    p.add_argument("--relative-depth-tolerance", type=float, default=0.01)
    p.set_defaults(func=cmd_fuse_masks)

    p = sub.add_parser("infer-background-structure-masks", help="Infer heuristic floor/ceiling/wall 3D masks from point-cloud boundaries.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path, help="Defaults to scene/reconstruction/point_cloud.ply.")
    p.add_argument("--up-axis", choices=["x", "y", "z"], default="y", help="Axis treated as vertical for floor/ceiling inference.")
    p.add_argument("--quantile", type=float, default=0.03, help="Boundary quantile used for each structure side.")
    p.add_argument("--thickness", type=float, help="Optional absolute boundary thickness. If omitted, the boundary quantile itself is used.")
    p.add_argument("--min-points", type=int, default=50)
    p.add_argument("--exclusive", action=argparse.BooleanOptionalAction, default=True, help="Prevent earlier structures from reusing the same point indices.")
    p.add_argument("--include-floor", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--include-ceiling", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--include-walls", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--floor-id", default="floor")
    p.add_argument("--ceiling-id", default="ceiling")
    p.set_defaults(func=cmd_infer_background_structure_masks)

    p = sub.add_parser("export-splat-masks", help="Write semantic object_id labels into an ASCII PLY splat/point cloud.")
    add_common_project_arg(p)
    p.add_argument("--splat-ply", type=Path, help="Source ASCII PLY. Defaults to registered 3DGS PLY or point_cloud.ply.")
    p.add_argument("--mask-source-ply", type=Path, help="Point cloud used when fuse-masks created point indices. Defaults to masks/3d/object_masks.json point_cloud.")
    p.add_argument("--transfer-mode", choices=["auto", "index", "nearest"], default="auto")
    p.add_argument("--max-transfer-distance", type=float, help="Optional nearest-neighbor distance cutoff; farther target vertices become background.")
    p.add_argument("--output", type=Path, help="Output semantic PLY path.")
    p.set_defaults(func=cmd_export_splat_masks)

    p = sub.add_parser("export-viewer-plys", help="Export plain point-cloud PLY and SuperSplat-compatible Gaussian PLY files.")
    add_common_project_arg(p)
    p.add_argument("--kind", choices=["scene", "semantic", "all"], default="all", help="Which registered splat artifacts to export.")
    p.add_argument("--splat-ply", type=Path, help="Optional custom source PLY. When set, --kind is ignored.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/viewer_plys.")
    p.add_argument("--prefix", help="Output filename prefix. Defaults to scene_3dgs/semantic_3dgs or source stem.")
    p.add_argument("--include-labels", action="store_true", help="Preserve object_id from a custom semantic source PLY when present.")
    p.set_defaults(func=cmd_export_viewer_plys)

    p = sub.add_parser("render-semantic-preview", help="Color semantic splats and project object masks into source frames for QA.")
    add_common_project_arg(p)
    p.add_argument("--semantic-splats-ply", type=Path, help="Defaults to manifest artifacts.semantic_splats_ply.")
    p.add_argument("--semantic-manifest", type=Path, help="Defaults to manifest artifacts.semantic_splats_manifest.")
    p.add_argument("--frames-dir", type=Path, help="Defaults to scene/frames.")
    p.add_argument("--camera-info", type=Path, help="Defaults to scene/cameras/camera_info.json.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/semantic_preview.")
    p.add_argument("--max-frames", type=int, default=3)
    p.add_argument("--max-points-per-frame", type=int, default=5000)
    p.add_argument("--point-radius", type=int, default=2)
    p.add_argument("--alpha", type=float, default=0.9)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--occlusion-filter", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--depth-tolerance", type=float, default=0.03)
    p.add_argument("--relative-depth-tolerance", type=float, default=0.01)
    p.add_argument("--include-background", action=argparse.BooleanOptionalAction, default=False)
    p.set_defaults(func=cmd_render_semantic_preview)

    p = sub.add_parser("export-object-mask-clouds", help="Export each object's 3D mask as its own PLY point cloud.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path, help="Source point cloud for mask indices. Defaults to object_masks.json point_cloud.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/object_masks_3d.")
    p.add_argument("--skip-missing", action="store_true")
    p.set_defaults(func=cmd_export_object_mask_clouds)

    p = sub.add_parser("reconstruct-object-meshes", help="Reconstruct per-object meshes directly from exported 3D mask point clouds.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/reconstructed_meshes.")
    p.add_argument("--method", choices=["auto", "alpha_shape", "ball_pivoting", "convex_hull", "bbox"], default="auto")
    p.add_argument("--format", choices=["obj", "ply", "stl"], default="obj")
    p.add_argument("--min-points", type=int, default=4)
    p.add_argument("--min-extent", type=float, default=0.03, help="Minimum bbox extent for sparse/planar fallback meshes.")
    p.add_argument("--bbox-padding-ratio", type=float, default=0.05)
    p.add_argument("--voxel-size", type=float, default=0.0, help="Optional voxel downsampling size; 0 disables downsampling.")
    p.add_argument("--remove-outliers", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--outlier-nb-neighbors", type=int, default=20)
    p.add_argument("--outlier-std-ratio", type=float, default=2.0)
    p.add_argument("--alpha", type=float, help="Alpha value for alpha-shape reconstruction. Defaults to spacing * --alpha-multiplier.")
    p.add_argument("--alpha-multiplier", type=float, default=4.0)
    p.add_argument("--ball-radius-multipliers", type=float, nargs="+", default=[1.5, 2.5, 4.0])
    p.add_argument("--normal-radius", type=float, help="Normal estimation radius for ball pivoting. Defaults to spacing * 3.")
    p.add_argument("--ascii", action=argparse.BooleanOptionalAction, default=False, help="Ask Open3D to write ASCII mesh files when the format supports it.")
    p.add_argument("--copy-to-assets", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument("--skip-missing", action="store_true")
    p.add_argument("--skip-failed", action="store_true")
    p.set_defaults(func=cmd_reconstruct_object_meshes)

    p = sub.add_parser("select-frames", help="Select best source frames for each fused object.")
    add_common_project_arg(p)
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--use-sharpness", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--hit-weight", type=float, default=1.0)
    p.add_argument("--area-weight", type=float, default=0.001)
    p.add_argument("--sharpness-weight", type=float, default=0.0001)
    p.set_defaults(func=cmd_select_frames)

    p = sub.add_parser("prepare-object-images", help="Create masked object crop/reference images from selected frames.")
    add_common_project_arg(p)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--padding-ratio", type=float, default=0.18)
    p.add_argument("--min-padding", type=int, default=24)
    p.add_argument("--square", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--transparent", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--mask-threshold", type=int, default=128)
    p.add_argument("--background", type=int, nargs=3, default=[255, 255, 255], metavar=("R", "G", "B"))
    p.add_argument("--skip-missing", action="store_true")
    p.set_defaults(func=cmd_prepare_object_images)

    p = sub.add_parser("export-image-blaster", help="Create image-blaster object directories from selected frames.")
    add_common_project_arg(p)
    p.add_argument("--world")
    p.add_argument("--image-blaster-root", type=Path, default=Path("image-blaster"))
    p.add_argument("--provider", choices=["hunyuan", "meshy"], default="hunyuan")
    p.add_argument("--reference-only", action="store_true")
    p.add_argument("--skip-missing", action="store_true")
    p.add_argument("--use-object-crop", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--auto-prepare-crops", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--crop-top-k", type=int, default=3)
    p.add_argument("--crop-padding-ratio", type=float, default=0.18)
    p.add_argument("--crop-min-padding", type=int, default=24)
    p.add_argument("--transparent-crops", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--mask-threshold", type=int, default=128)
    p.add_argument("--crop-background", type=int, nargs=3, default=[255, 255, 255], metavar=("R", "G", "B"))
    p.set_defaults(func=cmd_export_image_blaster)

    p = sub.add_parser("mesh-commands", help="Write image-blaster mesh generation commands.")
    add_common_project_arg(p)
    p.add_argument("--image-blaster-root", type=Path, default=Path("image-blaster"))
    p.add_argument("--provider", choices=["hunyuan", "meshy"], default="hunyuan")
    p.add_argument("--reference-only", action="store_true")
    p.add_argument("--run", action="store_true", help="Actually run image-blaster commands.")
    p.set_defaults(func=cmd_mesh_commands)

    p = sub.add_parser("prepare-multiview-mesh-jobs", help="Prepare per-object external mesh reconstruction jobs from selected frames/crops.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/multiview_mesh_jobs.")
    p.add_argument("--mesh-output-dir", type=Path, help="Defaults to <output-dir>/meshes.")
    p.add_argument("--mesh-format", choices=["obj", "ply", "glb", "stl"], default="obj")
    p.add_argument("--max-frames", type=int, default=0, help="Limit selected frames/object crops stored per job; 0 keeps all.")
    p.add_argument(
        "--command-template",
        help=(
            "Optional shell command with {job_path}, {object_id}, {output_dir}, {mesh_output}, "
            "{primary_frame}, {primary_crop}, {image_paths}, {crop_paths}, {project_root}."
        ),
    )
    p.add_argument("--skip-missing", action="store_true")
    p.add_argument("--run", action="store_true", help="Run prepared external commands. Without this, only JSON/script artifacts are written.")
    p.set_defaults(func=cmd_prepare_multiview_mesh_jobs)

    p = sub.add_parser("import-object-meshes", help="Import generated object meshes from image-blaster/external mesh dirs.")
    add_common_project_arg(p)
    p.add_argument("--image-blaster-root", type=Path, default=Path("image-blaster"))
    p.add_argument("--world", help="image-blaster world slug. Defaults to manifest artifacts.image_blaster_world.")
    p.add_argument("--mesh-root", type=Path, help="Optional external mesh directory; checked before image-blaster.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument("--copy-to-assets", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--skip-missing", action="store_true")
    p.set_defaults(func=cmd_import_object_meshes)

    p = sub.add_parser("export-simulator-assets", help="Export final simulator asset bundle manifest.")
    add_common_project_arg(p)
    p.add_argument("--semantic-splats-ply", type=Path, help="Optional semantic PLY path. Defaults to manifest artifact.")
    p.add_argument("--scene-scale", type=float, default=1.0, help="Scale multiplier from reconstruction units to simulator units.")
    p.add_argument("--body-type", choices=["static", "kinematic", "dynamic"], default="dynamic")
    p.add_argument("--collider", choices=["mesh", "convex_hull", "box", "none"], default="mesh")
    p.add_argument("--copy-meshes", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--ascii-meshes", action=argparse.BooleanOptionalAction, default=False, help="Write localized simulator meshes as ASCII when supported.")
    p.add_argument("--fit-object-local-meshes-to-bbox", action=argparse.BooleanOptionalAction, default=False, help="Center object-local imported meshes and uniformly scale them to the fused 3D mask bbox.")
    p.add_argument("--fit-axis", choices=["diagonal", "longest"], default="diagonal", help="Object-local bbox fitting length metric.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_export_simulator_assets)

    p = sub.add_parser("calibrate-simulator-assets", help="Set simulator scale/up-axis and estimated physics defaults in the asset bundle.")
    add_common_project_arg(p)
    p.add_argument("--bundle", type=Path, help="Optional simulator_asset_bundle.json path. Defaults to manifest artifact.")
    p.add_argument("--scale-to-meters", type=float, help="Manual scale multiplier from current bundle units to meters.")
    p.add_argument("--scale-calibrated", action=argparse.BooleanOptionalAction, default=False, help="Mark the scale as calibrated rather than assumed.")
    p.add_argument("--reference-object", help="Object id whose bbox length is known in meters.")
    p.add_argument("--reference-axis", choices=["x", "y", "z", "longest"], default="longest")
    p.add_argument("--reference-length-m", type=float, help="Known real-world length of the reference object/axis in meters.")
    p.add_argument("--up-axis", choices=["x", "y", "z"], default="y")
    p.add_argument("--rescale-existing-pose", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--estimate-physics", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--overwrite-physics", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--body-type", choices=["static", "kinematic", "dynamic"], default="dynamic")
    p.add_argument("--collider", choices=["mesh", "convex_hull", "box", "none"], default="mesh")
    p.add_argument("--default-density-kg-m3", type=float, default=120.0, help="Density used for bbox-volume mass estimates.")
    p.add_argument("--min-mass-kg", type=float, default=0.05)
    p.add_argument("--max-mass-kg", type=float, default=50.0)
    p.add_argument("--default-material", default="estimated_rigid")
    p.add_argument("--friction", type=float, default=0.8)
    p.add_argument("--torsional-friction", type=float, default=0.02)
    p.add_argument("--rolling-friction", type=float, default=0.001)
    p.add_argument("--restitution", type=float, default=0.1)
    p.add_argument("--notes", help="Optional calibration notes.")
    p.set_defaults(func=cmd_calibrate_simulator_assets)

    p = sub.add_parser("export-simulator-adapter", help="Export MuJoCo/Isaac/Unity adapter manifests from simulator_asset_bundle.json.")
    add_common_project_arg(p)
    p.add_argument("--bundle", type=Path, help="Optional simulator_asset_bundle.json path. Defaults to manifest artifact.")
    p.add_argument("--format", choices=["mujoco", "isaac", "unity"], nargs="+", default=["mujoco"], help="One or more adapter formats to export.")
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/adapters.")
    p.add_argument("--body-type", choices=["static", "kinematic", "dynamic"], default="dynamic", help="Fallback body type for adapter generation.")
    p.add_argument("--default-mass", type=float, default=1.0, help="Fallback MuJoCo geom mass for dynamic bodies.")
    p.add_argument("--copy-assets", action=argparse.BooleanOptionalAction, default=True, help="Copy/symlink meshes into simulator_assets/adapters/assets.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.set_defaults(func=cmd_export_simulator_adapter)

    p = sub.add_parser("qa-simulator-assets", help="Run simulator-readiness QA on exported object meshes, scale, colliders, and physics fields.")
    add_common_project_arg(p)
    p.add_argument("--bundle", type=Path, help="Optional simulator_asset_bundle.json path. Defaults to manifest artifact.")
    p.add_argument("--output", type=Path, help="Defaults to simulator_assets/simulator_asset_qa.json.")
    p.add_argument("--min-mesh-vertices", type=int, default=20)
    p.add_argument("--max-center-ratio", type=float, default=0.5, help="Warn if mesh center is farther than this fraction of mask bbox diagonal.")
    p.add_argument("--max-size-ratio-delta", type=float, default=1.5, help="Warn if mesh/mask bbox diagonal ratio differs from 1 by more than this.")
    p.add_argument("--require-physics", action="store_true", help="Treat missing mass/collider/body_type as required failures.")
    p.add_argument("--require-scale-calibration", action="store_true", help="Treat missing scale calibration as a required failure.")
    p.add_argument("--max-issues", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.add_argument("--fail-on-required", action="store_true")
    p.set_defaults(func=cmd_qa_simulator_assets)

    p = sub.add_parser("export-svpp-metadata", help="Export a SceneVerse++/PQ3D-style scene folder from fused 3D masks.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/svpp/<scene_id>.")
    p.add_argument("--scene-id", help="Scene folder name for the SVPP-style export. Defaults to manifest scene_id.")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy", help="How to place mesh.ply/camera_info.json in the export folder.")
    p.add_argument("--min-points", type=int, default=1, help="Minimum point_ids count to include an instance.")
    p.add_argument("--skip-small", action="store_true", help="Skip instances smaller than --min-points instead of exporting them.")
    p.add_argument("--skip-missing", action="store_true", help="Skip objects without 3D point index masks.")
    p.add_argument("--category-map", type=Path, help="Optional JSON map from Video2Mesh categories to SceneVerse++/ScanNet20 labels.")
    p.add_argument("--default-category", help="Optional fallback category for labels outside SceneVerse++/ScanNet20.")
    p.set_defaults(func=cmd_export_svpp_metadata)

    p = sub.add_parser("run-local", help="Run fuse-masks, select-frames, and export-image-blaster.")
    add_common_project_arg(p)
    p.add_argument("--point-cloud", type=Path)
    p.add_argument("--camera-info", type=Path)
    p.add_argument("--mask-root", type=Path)
    p.add_argument("--frames-dir", type=Path)
    p.add_argument("--object-labels", type=Path)
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--mask-threshold", type=int, default=128)
    p.add_argument("--min-votes", type=int, default=1)
    p.add_argument("--occlusion-filter", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--depth-tolerance", type=float, default=0.03)
    p.add_argument("--relative-depth-tolerance", type=float, default=0.01)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--world")
    p.add_argument("--image-blaster-root", type=Path, default=Path("image-blaster"))
    p.add_argument("--provider", choices=["hunyuan", "meshy"], default="hunyuan")
    p.set_defaults(func=cmd_run_local)

    p = sub.add_parser("run-pipeline", help="Orchestrate the scan-to-semantic-3DGS-to-object-assets workflow.")
    add_common_project_arg(p)
    p.add_argument("--scene-id")
    p.add_argument("--world")
    p.add_argument("--video", type=Path)
    p.add_argument("--dataset", type=Path)
    p.add_argument("--make-sample", action="store_true", help="Create synthetic sample inputs before running the pipeline.")
    p.add_argument("--make-scan-video-sample", action="store_true", help="Create a synthetic scan mp4 plus matching camera/point-cloud artifacts before running.")
    p.add_argument("--sample-video-output", type=Path, help="Defaults to inputs/synthetic_scan.mp4 inside the project.")
    p.add_argument("--sample-video-frame-count", type=int, default=10)
    p.add_argument("--sample-video-fps", type=float, default=6.0)
    p.add_argument("--sample-video-fourcc", default="mp4v")
    p.add_argument("--sample-video-pixel-step", type=float, default=1.5)
    p.add_argument("--extract-frames", action="store_true")
    p.add_argument("--every", type=int, default=30)
    p.add_argument("--max-frames", type=int, default=0)
    p.add_argument("--overwrite-frames", action="store_true")
    p.add_argument("--renumber-frames", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--run-mast3r-slam", action="store_true")
    p.add_argument("--mast3r-root", type=Path, default=Path("/root/autodl-tmp/workspace/MASt3R-SLAM"))
    p.add_argument("--mast3r-config", type=Path, default=Path("config/base.yaml"))
    p.add_argument("--mast3r-save-as")
    p.add_argument("--calib", type=Path)
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fx", type=float)
    p.add_argument("--fy", type=float)
    p.add_argument("--cx", type=float)
    p.add_argument("--cy", type=float)
    p.add_argument("--focal-scale", type=float, default=1.2)
    p.add_argument("--use-mast3r-keyframes", action="store_true", help="Use scene/mast3r_keyframes for 3DGS training, masks, previews, and frame selection after MASt3R-SLAM import.")
    p.add_argument("--downsample-point-cloud", action="store_true", help="Create a lightweight point cloud before 3DGS training and mask fusion.")
    p.add_argument("--downsample-source-point-cloud", type=Path, help="Defaults to scene/reconstruction/point_cloud.ply.")
    p.add_argument("--downsample-output", type=Path, help="Defaults to scene/reconstruction/point_cloud_<max_points>.ply.")
    p.add_argument("--downsample-method", choices=["random", "voxel"], default="random")
    p.add_argument("--downsample-max-points", type=int, default=10000)
    p.add_argument("--downsample-voxel-size", type=float, default=0.02)
    p.add_argument("--downsample-seed", type=int, default=7)
    p.add_argument("--downsample-register-as-point-cloud", action="store_true", help="Replace the project's main scene point cloud with the downsampled output.")
    p.add_argument("--render-reconstruction-preview", action="store_true", help="Project point cloud into frames for camera/reconstruction QA.")
    p.add_argument("--reconstruction-preview-max-frames", type=int, default=3)
    p.add_argument("--reconstruction-preview-max-points", type=int, default=5000)
    p.add_argument("--reconstruction-preview-point-radius", type=int, default=2)
    p.add_argument("--reconstruction-preview-alpha", type=float, default=0.85)
    p.add_argument("--reconstruction-preview-seed", type=int, default=7)
    p.add_argument("--prepare-3dgs-source", action="store_true")
    p.add_argument("--g3dgs-command-template")
    p.add_argument("--g3dgs-source-path", type=Path)
    p.add_argument("--g3dgs-output-path", type=Path)
    p.add_argument("--g3dgs-work-dir", type=Path)
    p.add_argument("--g3dgs-prepare-only", action="store_true")
    p.add_argument("--no-register-3dgs", action="store_true")
    p.add_argument("--train-gsplat", action="store_true", help="Run the built-in minimal gsplat trainer and register its output.")
    p.add_argument("--gsplat-iterations", type=int, default=30)
    p.add_argument("--gsplat-max-frames", type=int, default=3)
    p.add_argument("--gsplat-max-points", type=int, default=20000)
    p.add_argument("--gsplat-seed", type=int, default=7)
    p.add_argument("--gsplat-device", choices=["auto", "cuda", "cpu"], default="auto")
    p.add_argument("--gsplat-width", type=int)
    p.add_argument("--gsplat-height", type=int)
    p.add_argument("--gsplat-init-scale", type=float, default=0.0)
    p.add_argument("--gsplat-min-scale", type=float, default=0.001)
    p.add_argument("--gsplat-max-scale", type=float, default=0.2)
    p.add_argument("--gsplat-init-opacity-logit", type=float, default=0.0)
    p.add_argument("--gsplat-lr-position", type=float, default=1e-4)
    p.add_argument("--gsplat-lr-color", type=float, default=3e-2)
    p.add_argument("--gsplat-lr-scale", type=float, default=1e-3)
    p.add_argument("--gsplat-lr-opacity", type=float, default=1e-2)
    p.add_argument("--gsplat-alpha-reg", type=float, default=0.0)
    p.add_argument("--gsplat-log-every", type=int, default=10)
    p.add_argument("--render-gsplat-preview", action="store_true", help="Render registered/trained 3DGS back to input frames for QA.")
    p.add_argument("--preview-max-frames", type=int, default=3)
    p.add_argument("--preview-width", type=int)
    p.add_argument("--preview-height", type=int)
    p.add_argument("--preview-background", choices=["target_mean", "white", "black"], default="target_mean")
    p.add_argument("--preview-error-gain", type=float, default=4.0)
    p.add_argument("--camera-model", choices=["PINHOLE", "SIMPLE_PINHOLE"], default="PINHOLE")
    p.add_argument("--image-mode", choices=["copy", "symlink", "none"], default="copy")
    p.add_argument("--prompts", type=Path)
    p.add_argument("--auto-prompts", action="store_true", help="Generate bbox prompts automatically before track-masks when --prompts is not provided.")
    p.add_argument("--auto-prompts-output", type=Path, help="Defaults to masks/auto_prompts.json.")
    p.add_argument("--auto-prompt-frame-id")
    p.add_argument("--auto-prompt-frame-index", type=int, default=0)
    p.add_argument("--auto-prompt-method", choices=["auto", "sam", "opencv"], default="auto")
    p.add_argument("--auto-prompt-max-objects", type=int, default=12)
    p.add_argument("--auto-prompt-min-area-ratio", type=float, default=0.002)
    p.add_argument("--auto-prompt-max-area-ratio", type=float, default=0.45)
    p.add_argument("--auto-prompt-min-width", type=int, default=12)
    p.add_argument("--auto-prompt-min-height", type=int, default=12)
    p.add_argument("--auto-prompt-nms-iou", type=float, default=0.65)
    p.add_argument("--auto-prompt-containment-overlap", type=float, default=0.9)
    p.add_argument("--auto-prompt-containment-area-ratio", type=float, default=1.8)
    p.add_argument("--auto-prompt-object-prefix", default="auto_object")
    p.add_argument("--auto-prompt-category", default="unknown")
    p.add_argument("--auto-prompt-color-distance-threshold", type=float, default=35.0)
    p.add_argument("--auto-prompt-min-saturation", type=int, default=45)
    p.add_argument("--auto-prompt-morph-kernel", type=int, default=5)
    p.add_argument("--skip-track-masks", action="store_true")
    p.add_argument("--clear-mask-output", action="store_true", help="Remove existing masks/2d before running track-masks.")
    p.add_argument("--bbox-format", choices=["xyxy", "xywh"], default="xyxy")
    p.add_argument("--template-padding", type=int, default=12)
    p.add_argument("--search-margin", type=int, default=80)
    p.add_argument("--min-score", type=float, default=-1.0)
    p.add_argument("--keep-low-score", action="store_true")
    p.add_argument("--grabcut", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--grabcut-iters", type=int, default=3)
    p.add_argument("--mask-backend", choices=["opencv", "sam", "auto"], default="opencv", help="Mask generator after bbox tracking.")
    p.add_argument("--sam-checkpoint", type=Path)
    p.add_argument("--sam-model-type", default="vit_h")
    p.add_argument("--sam-device", default="auto")
    p.add_argument("--sam-multimask", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--track-max-frames", type=int, default=0)
    p.add_argument("--skip-fuse-masks", action="store_true")
    p.add_argument("--extrinsic-type", choices=["world_to_camera", "camera_to_world"], default="world_to_camera")
    p.add_argument("--mask-threshold", type=int, default=128)
    p.add_argument("--min-votes", type=int, default=1)
    p.add_argument("--occlusion-filter", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--depth-tolerance", type=float, default=0.03)
    p.add_argument("--relative-depth-tolerance", type=float, default=0.01)
    p.add_argument("--skip-export-splat-masks", action="store_true")
    p.add_argument("--skip-export-viewer-plys", action="store_true")
    p.add_argument("--render-semantic-preview", action="store_true", help="Project colored semantic splat/object masks back to frames for QA.")
    p.add_argument("--semantic-preview-max-frames", type=int, default=3)
    p.add_argument("--semantic-preview-max-points", type=int, default=5000)
    p.add_argument("--semantic-preview-point-radius", type=int, default=2)
    p.add_argument("--semantic-preview-alpha", type=float, default=0.9)
    p.add_argument("--semantic-preview-seed", type=int, default=7)
    p.add_argument("--semantic-preview-include-background", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--skip-object-mask-clouds", action="store_true")
    p.add_argument("--transfer-mode", choices=["auto", "index", "nearest"], default="auto")
    p.add_argument("--max-transfer-distance", type=float)
    p.add_argument("--skip-select-frames", action="store_true")
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--skip-object-images", action="store_true")
    p.add_argument("--crop-padding-ratio", type=float, default=0.18)
    p.add_argument("--crop-min-padding", type=int, default=24)
    p.add_argument("--transparent-crops", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--crop-background", type=int, nargs=3, default=[255, 255, 255], metavar=("R", "G", "B"))
    p.add_argument("--skip-export-image-blaster", action="store_true")
    p.add_argument("--image-blaster-root", type=Path, default=Path("image-blaster"))
    p.add_argument("--provider", choices=["hunyuan", "meshy"], default="hunyuan")
    p.add_argument("--reference-only", action="store_true")
    p.add_argument("--run-mesh-commands", action="store_true", help="Actually run image-blaster mesh generation commands.")
    p.add_argument("--create-placeholder-meshes", action="store_true", help="Smoke-test only: create trivial OBJ meshes instead of calling a mesh model.")
    p.add_argument("--reconstruct-mask-meshes", action="store_true", help="Reconstruct object meshes from fused 3D mask point clouds instead of waiting for image-blaster/FAL output.")
    p.add_argument("--mask-mesh-method", choices=["auto", "alpha_shape", "ball_pivoting", "convex_hull", "bbox"], default="auto")
    p.add_argument("--mask-mesh-format", choices=["obj", "ply", "stl"], default="obj")
    p.add_argument("--mask-mesh-min-points", type=int, default=4)
    p.add_argument("--mask-mesh-min-extent", type=float, default=0.03)
    p.add_argument("--mask-mesh-bbox-padding-ratio", type=float, default=0.05)
    p.add_argument("--mask-mesh-voxel-size", type=float, default=0.0)
    p.add_argument("--mask-mesh-remove-outliers", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--mask-mesh-outlier-nb-neighbors", type=int, default=20)
    p.add_argument("--mask-mesh-outlier-std-ratio", type=float, default=2.0)
    p.add_argument("--mask-mesh-alpha", type=float)
    p.add_argument("--mask-mesh-alpha-multiplier", type=float, default=4.0)
    p.add_argument("--mask-mesh-ball-radius-multipliers", type=float, nargs="+", default=[1.5, 2.5, 4.0])
    p.add_argument("--mask-mesh-normal-radius", type=float)
    p.add_argument("--mask-mesh-ascii", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--skip-failed-mask-meshes", action="store_true")
    p.add_argument("--import-meshes", action="store_true")
    p.add_argument("--mesh-root", type=Path)
    p.add_argument("--skip-import-meshes", action="store_true")
    p.add_argument("--skip-missing-meshes", action="store_true")
    p.add_argument("--skip-simulator-assets", action="store_true")
    p.add_argument("--skip-simulator-adapters", action="store_true")
    p.add_argument("--simulator-format", choices=["mujoco", "isaac", "unity"], nargs="+", default=["mujoco"], help="Adapter formats exported after simulator assets.")
    p.add_argument("--default-mass", type=float, default=1.0, help="Fallback MuJoCo geom mass for dynamic adapter bodies.")
    p.add_argument("--scene-scale", type=float, default=1.0)
    p.add_argument("--body-type", choices=["static", "kinematic", "dynamic"], default="dynamic")
    p.add_argument("--collider", choices=["mesh", "convex_hull", "box", "none"], default="mesh")
    p.add_argument("--simulator-ascii-meshes", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--fit-object-local-meshes-to-bbox", action=argparse.BooleanOptionalAction, default=False, help="When exporting simulator assets, bbox-fit imported object-local meshes to fused 3D masks.")
    p.add_argument("--fit-axis", choices=["diagonal", "longest"], default="diagonal")
    p.add_argument("--mode", choices=["copy", "symlink"], default="copy")
    p.add_argument("--skip-validate", action="store_true")
    p.add_argument("--allow-incomplete", action="store_true")
    p.set_defaults(func=cmd_run_pipeline)

    p = sub.add_parser("status", help="Print project manifest and object summary.")
    add_common_project_arg(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("validate", help="Validate whether a project has the artifacts needed for Video2Mesh.")
    add_common_project_arg(p)
    p.add_argument("--strict", action="store_true", help="Treat recommended artifacts as required.")
    p.add_argument("--json", action="store_true", help="Print JSON validation report.")
    p.add_argument("--output", type=Path, help="Optional JSON report path.")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("evaluate", help="Summarize stage readiness and object-level quality signals.")
    add_common_project_arg(p)
    p.add_argument("--strict", action="store_true", help="Treat recommended validation artifacts as required.")
    p.add_argument("--min-object-points", type=int, default=50, help="Warn when a fused object has fewer 3D mask points.")
    p.add_argument("--max-issues", type=int, default=20, help="Maximum issues to print in text mode.")
    p.add_argument("--json", action="store_true", help="Print JSON evaluation report.")
    p.add_argument("--output", type=Path, help="Optional JSON report path. Defaults to simulator_assets/evaluation_report.json.")
    p.add_argument("--fail-on-issues", action="store_true", help="Return a non-zero exit code if any issue is found.")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("export-review-pack", help="Export a lightweight HTML/JSON review pack for object masks, crops, and meshes.")
    add_common_project_arg(p)
    p.add_argument("--output-dir", type=Path, help="Defaults to simulator_assets/review.")
    p.add_argument("--min-object-points", type=int, default=50, help="Warn when a fused object has fewer 3D mask points.")
    p.add_argument("--max-frames", type=int, default=3, help="Maximum selected frame thumbnails per object.")
    p.add_argument("--max-scene-frames", type=int, default=3, help="Maximum scene-level QA frames per preview section.")
    p.set_defaults(func=cmd_export_review_pack)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
