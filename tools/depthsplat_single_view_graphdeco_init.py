#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement

from depthsplat_colmap_depth_affine_fusion import (
    colmap_to_effective_pixel,
    read_cameras,
    read_images,
    read_points3d,
    robust_scale_fit,
)

C0 = 0.28209479177387814


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ply", required=True, type=Path)
    parser.add_argument("--colmap", required=True, type=Path)
    parser.add_argument("--output-ply", required=True, type=Path)
    parser.add_argument("--context-frames", default="0,16,32,48,64,79")
    parser.add_argument("--local-view", default=2, type=int)
    parser.add_argument("--export-reference-local-view", default=0, type=int)
    parser.add_argument("--model-h", default=256, type=int)
    parser.add_argument("--model-w", default=448, type=int)
    parser.add_argument("--trim", default=8, type=int)
    parser.add_argument("--scale", default=None, type=float)
    return parser.parse_args()


def sh_to_rgb_u8(f_dc: np.ndarray) -> np.ndarray:
    rgb = np.clip(f_dc * C0 + 0.5, 0.0, 1.0)
    return np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)


def main() -> None:
    args = parse_args()
    context_frames = [int(x) for x in args.context_frames.split(",") if x.strip()]
    num_views = len(context_frames)
    frame = context_frames[args.local_view]
    ref_frame = context_frames[args.export_reference_local_view]
    eff_w = args.model_w - 2 * args.trim
    eff_h = args.model_h - 2 * args.trim
    vertices_per_view = eff_w * eff_h

    cameras = read_cameras(args.colmap / "cameras.txt")
    images = read_images(args.colmap / "images.txt")
    points3d = read_points3d(args.colmap / "points3D.txt")
    ply = PlyData.read(args.source_ply)
    vertex = ply["vertex"].data
    if len(vertex) != vertices_per_view * num_views:
        raise ValueError(f"Unexpected vertex count: {len(vertex)}")

    all_xyz = np.column_stack([vertex["x"], vertex["y"], vertex["z"]]).astype(np.float64)
    ref_rot = images[ref_frame]["c2w"][:3, :3]
    all_world = (ref_rot @ all_xyz.T).T
    local_indices = np.arange(args.local_view, len(vertex), num_views)
    world = all_world[local_indices]

    img = images[frame]
    cam = cameras[int(img["camera_id"])]
    w2c = img["w2c"]
    c2w = img["c2w"]

    z_pred = []
    z_gt = []
    used_pixels = set()
    for x, y, pid in img["observations"]:
        if pid < 0 or pid not in points3d:
            continue
        pix = colmap_to_effective_pixel(
            x,
            y,
            int(cam["width"]),
            int(cam["height"]),
            args.model_h,
            args.model_w,
            args.trim,
        )
        if pix is None:
            continue
        ix, iy = pix
        flat = iy * eff_w + ix
        if flat in used_pixels:
            continue
        used_pixels.add(flat)
        pred_point = all_world[flat * num_views + args.local_view]
        gt_point = points3d[pid]
        pred_cam = w2c[:3, :3] @ pred_point + w2c[:3, 3]
        gt_cam = w2c[:3, :3] @ gt_point + w2c[:3, 3]
        if pred_cam[2] > 1e-6 and gt_cam[2] > 1e-6:
            z_pred.append(float(pred_cam[2]))
            z_gt.append(float(gt_cam[2]))

    fit = robust_scale_fit(np.asarray(z_pred), np.asarray(z_gt))
    scale = float(args.scale if args.scale is not None else fit["scale"])

    cam_points = (w2c[:3, :3] @ world.T).T + w2c[:3, 3]
    cam_points_scaled = cam_points * scale
    world_scaled = (c2w[:3, :3] @ cam_points_scaled.T).T + c2w[:3, 3]

    f_dc = np.column_stack([vertex["f_dc_0"], vertex["f_dc_1"], vertex["f_dc_2"]]).astype(np.float64)
    rgb = sh_to_rgb_u8(f_dc[local_indices])
    normals = np.zeros_like(world_scaled, dtype=np.float32)
    out_dtype = [
        ("x", "f4"),
        ("y", "f4"),
        ("z", "f4"),
        ("nx", "f4"),
        ("ny", "f4"),
        ("nz", "f4"),
        ("red", "u1"),
        ("green", "u1"),
        ("blue", "u1"),
    ]
    out = np.empty(world_scaled.shape[0], dtype=out_dtype)
    out["x"] = world_scaled[:, 0].astype(np.float32)
    out["y"] = world_scaled[:, 1].astype(np.float32)
    out["z"] = world_scaled[:, 2].astype(np.float32)
    out["nx"] = normals[:, 0]
    out["ny"] = normals[:, 1]
    out["nz"] = normals[:, 2]
    out["red"] = rgb[:, 0]
    out["green"] = rgb[:, 1]
    out["blue"] = rgb[:, 2]

    args.output_ply.parent.mkdir(parents=True, exist_ok=True)
    PlyData([PlyElement.describe(out, "vertex")], text=False).write(args.output_ply)
    summary = {
        "source_ply": str(args.source_ply),
        "output_ply": str(args.output_ply),
        "local_view": args.local_view,
        "frame": frame,
        "export_reference_frame": ref_frame,
        "vertices": int(world_scaled.shape[0]),
        "scale": scale,
        "fit": fit,
        "xyz_min": world_scaled.min(axis=0).tolist(),
        "xyz_max": world_scaled.max(axis=0).tolist(),
    }
    summary_path = args.output_ply.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
