#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from plyfile import PlyData, PlyElement


def qvec2rotmat(qvec: list[float]) -> np.ndarray:
    q = np.asarray(qvec, dtype=np.float64)
    q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
            [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
            [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
        ],
        dtype=np.float64,
    )


def read_cameras(path: Path) -> dict[int, dict[str, float]]:
    cameras: dict[int, dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cam_id = int(parts[0])
            model = parts[1]
            width, height = int(parts[2]), int(parts[3])
            params = [float(x) for x in parts[4:]]
            if model == "PINHOLE":
                fx, fy, cx, cy = params
            elif model in {"SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"}:
                fx = fy = params[0]
                cx, cy = params[1], params[2]
            else:
                raise ValueError(f"Unsupported camera model: {model}")
            cameras[cam_id] = {
                "width": width,
                "height": height,
                "fx": fx,
                "fy": fy,
                "cx": cx,
                "cy": cy,
            }
    return cameras


def read_points3d(path: Path) -> dict[int, np.ndarray]:
    points: dict[int, np.ndarray] = {}
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            pid = int(parts[0])
            points[pid] = np.array([float(parts[1]), float(parts[2]), float(parts[3])], dtype=np.float64)
    return points


def read_images(path: Path) -> dict[int, dict[str, object]]:
    images: dict[int, dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as f:
        while True:
            raw = f.readline()
            if not raw:
                break
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            qvec = [float(x) for x in parts[1:5]]
            tvec = np.array([float(x) for x in parts[5:8]], dtype=np.float64)
            cam_id = int(parts[8])
            name = parts[9]
            points_line = f.readline().strip()
            obs = []
            if points_line:
                vals = points_line.split()
                for i in range(0, len(vals), 3):
                    obs.append((float(vals[i]), float(vals[i + 1]), int(vals[i + 2])))
            frame = int(Path(name).stem)
            r_w2c = qvec2rotmat(qvec)
            w2c = np.eye(4, dtype=np.float64)
            w2c[:3, :3] = r_w2c
            w2c[:3, 3] = tvec
            c2w = np.linalg.inv(w2c)
            images[frame] = {
                "name": name,
                "camera_id": cam_id,
                "w2c": w2c,
                "c2w": c2w,
                "observations": obs,
            }
    return images


def colmap_to_effective_pixel(
    x: float,
    y: float,
    width: int,
    height: int,
    model_h: int,
    model_w: int,
    trim: int,
) -> tuple[int, int] | None:
    scale = max(model_h / height, model_w / width)
    scaled_w = int(round(width * scale))
    scaled_h = int(round(height * scale))
    crop_col = (scaled_w - model_w) // 2
    crop_row = (scaled_h - model_h) // 2
    xe = x * scale - crop_col - trim
    ye = y * scale - crop_row - trim
    eff_w = model_w - 2 * trim
    eff_h = model_h - 2 * trim
    ix = int(round(xe))
    iy = int(round(ye))
    if ix < 0 or ix >= eff_w or iy < 0 or iy >= eff_h:
        return None
    return ix, iy


def robust_scale_fit(z_pred: np.ndarray, z_gt: np.ndarray) -> dict[str, object]:
    z_pred = np.asarray(z_pred, dtype=np.float64)
    z_gt = np.asarray(z_gt, dtype=np.float64)
    valid = np.isfinite(z_pred) & np.isfinite(z_gt) & (z_pred > 1e-6) & (z_gt > 1e-6)
    z_pred = z_pred[valid]
    z_gt = z_gt[valid]
    n = int(z_pred.size)
    if n < 8:
        return {
            "ok": False,
            "reason": "too_few_depth_anchors",
            "num_anchors": n,
            "scale": 1.0,
        }
    ratios = z_gt / z_pred
    finite = np.isfinite(ratios) & (ratios > 0)
    ratios = ratios[finite]
    z_pred = z_pred[finite]
    z_gt = z_gt[finite]
    if ratios.size < 8:
        return {
            "ok": False,
            "reason": "too_few_positive_ratios",
            "num_anchors": int(ratios.size),
            "scale": 1.0,
        }
    mask = np.ones(ratios.size, dtype=bool)
    history = []
    for _ in range(10):
        scale = float(np.median(ratios[mask]))
        residual = z_gt - scale * z_pred
        abs_res = np.abs(residual)
        mad = np.median(np.abs(abs_res - np.median(abs_res))) * 1.4826
        floor = max(0.005, 0.01 * float(np.median(z_gt)))
        threshold = max(floor, 2.5 * mad)
        new_mask = abs_res <= threshold
        min_keep = min(ratios.size, max(24, int(0.25 * ratios.size)))
        if int(new_mask.sum()) < min_keep:
            order = np.argsort(abs_res)
            new_mask = np.zeros(ratios.size, dtype=bool)
            new_mask[order[:min_keep]] = True
        history.append(
            {
                "kept": int(new_mask.sum()),
                "threshold": float(threshold),
                "median_abs": float(np.median(abs_res)),
                "p90_abs": float(np.percentile(abs_res, 90)),
                "scale": scale,
            }
        )
        if np.array_equal(new_mask, mask):
            break
        mask = new_mask
    scale = float(np.median(ratios[mask]))
    before = z_gt - z_pred
    after = z_gt - scale * z_pred
    return {
        "ok": bool(np.isfinite(scale) and 0.01 < scale < 1000.0),
        "num_anchors": int(ratios.size),
        "kept": int(mask.sum()),
        "scale": scale,
        "before_median_abs": float(np.median(np.abs(before))),
        "before_p90_abs": float(np.percentile(np.abs(before), 90)),
        "after_median_abs": float(np.median(np.abs(after))),
        "after_p90_abs": float(np.percentile(np.abs(after), 90)),
        "ratio_median_all": float(np.median(ratios)),
        "ratio_p10_all": float(np.percentile(ratios, 10)),
        "ratio_p90_all": float(np.percentile(ratios, 90)),
        "z_pred_median": float(np.median(z_pred)),
        "z_gt_median": float(np.median(z_gt)),
        "history_tail": history[-4:],
    }


def robust_affine_fit(z_pred: np.ndarray, z_gt: np.ndarray) -> dict[str, object]:
    z_pred = np.asarray(z_pred, dtype=np.float64)
    z_gt = np.asarray(z_gt, dtype=np.float64)
    valid = np.isfinite(z_pred) & np.isfinite(z_gt) & (z_pred > 1e-6) & (z_gt > 1e-6)
    z_pred = z_pred[valid]
    z_gt = z_gt[valid]
    n = int(z_pred.size)
    if n < 8:
        return {
            "ok": False,
            "reason": "too_few_depth_anchors",
            "num_anchors": n,
            "a": 1.0,
            "b": 0.0,
        }

    def solve(mask: np.ndarray) -> tuple[float, float]:
        x = z_pred[mask]
        y = z_gt[mask]
        a, b = np.linalg.lstsq(np.column_stack([x, np.ones_like(x)]), y, rcond=None)[0]
        return float(a), float(b)

    mask = np.ones(n, dtype=bool)
    history = []
    for _ in range(12):
        a, b = solve(mask)
        pred = a * z_pred + b
        residual = z_gt - pred
        abs_res = np.abs(residual)
        mad = np.median(np.abs(abs_res - np.median(abs_res))) * 1.4826
        floor = max(0.005, 0.01 * float(np.median(z_gt)))
        threshold = max(floor, 2.5 * mad)
        new_mask = abs_res <= threshold
        min_keep = min(n, max(24, int(0.25 * n)))
        if int(new_mask.sum()) < min_keep:
            order = np.argsort(abs_res)
            new_mask = np.zeros(n, dtype=bool)
            new_mask[order[:min_keep]] = True
        history.append(
            {
                "kept": int(new_mask.sum()),
                "threshold": float(threshold),
                "median_abs": float(np.median(abs_res)),
                "p90_abs": float(np.percentile(abs_res, 90)),
                "a": a,
                "b": b,
            }
        )
        if np.array_equal(new_mask, mask):
            break
        mask = new_mask

    a, b = solve(mask)
    fitted = a * z_pred + b
    before = z_gt - z_pred
    after = z_gt - fitted
    return {
        "ok": bool(np.isfinite(a) and np.isfinite(b) and 0.01 < a < 1000.0),
        "num_anchors": n,
        "kept": int(mask.sum()),
        "a": float(a),
        "b": float(b),
        "before_median_abs": float(np.median(np.abs(before))),
        "before_p90_abs": float(np.percentile(np.abs(before), 90)),
        "after_median_abs": float(np.median(np.abs(after))),
        "after_p90_abs": float(np.percentile(np.abs(after), 90)),
        "z_pred_median": float(np.median(z_pred)),
        "z_gt_median": float(np.median(z_gt)),
        "history_tail": history[-4:],
    }


def vertex_xyz(vertex: np.ndarray) -> np.ndarray:
    return np.column_stack([vertex["x"], vertex["y"], vertex["z"]]).astype(np.float64, copy=True)


def set_vertex_xyz(vertex: np.ndarray, xyz: np.ndarray) -> None:
    vertex["x"] = xyz[:, 0].astype(np.float32)
    vertex["y"] = xyz[:, 1].astype(np.float32)
    vertex["z"] = xyz[:, 2].astype(np.float32)


def make_preview(
    output_path: Path,
    per_view_world: list[np.ndarray],
    cameras: list[np.ndarray],
    context_frames: list[int],
    max_points_per_view: int,
) -> None:
    rng = np.random.default_rng(7)
    colors = plt.cm.tab10(np.linspace(0, 1, len(per_view_world)))
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=150)

    for ax, dims, title in [
        (axes[0], (0, 2), "top XZ"),
        (axes[1], (0, 1), "front XY"),
    ]:
        for i, pts in enumerate(per_view_world):
            if pts.shape[0] > max_points_per_view:
                pts = pts[rng.choice(pts.shape[0], max_points_per_view, replace=False)]
            ax.scatter(pts[:, dims[0]], pts[:, dims[1]], s=0.08, alpha=0.25, color=colors[i], label=str(context_frames[i]))
        cam_pts = np.stack(cameras, axis=0)
        ax.scatter(cam_pts[:, dims[0]], cam_pts[:, dims[1]], s=18, c="black", marker="x")
        for frame, c in zip(context_frames, cam_pts):
            ax.text(c[dims[0]], c[dims[1]], str(frame), fontsize=7, color="black")
        ax.set_title(title)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, linewidth=0.3, alpha=0.4)
    axes[0].legend(markerscale=20, fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ply", required=True, type=Path)
    parser.add_argument("--colmap", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--context-frames", default="0,16,32,48,64,79")
    parser.add_argument("--reference-local-view", default=0, type=int)
    parser.add_argument("--model-h", default=256, type=int)
    parser.add_argument("--model-w", default=448, type=int)
    parser.add_argument("--trim", default=8, type=int)
    parser.add_argument("--ratio-min", default=0.25, type=float)
    parser.add_argument("--ratio-max", default=80.0, type=float)
    parser.add_argument("--mode", choices=["scale", "affine"], default="scale")
    parser.add_argument("--preview-points-per-view", default=22000, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(7)
    np.random.seed(7)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / "depth_affine_fusion.log"
    start = time.strftime("%Y-%m-%d %H:%M:%S")
    context_frames = [int(x) for x in args.context_frames.split(",") if x.strip()]
    num_views = len(context_frames)
    eff_w = args.model_w - 2 * args.trim
    eff_h = args.model_h - 2 * args.trim
    vertices_per_view = eff_w * eff_h

    cameras = read_cameras(args.colmap / "cameras.txt")
    images = read_images(args.colmap / "images.txt")
    points3d = read_points3d(args.colmap / "points3D.txt")
    if any(frame not in images for frame in context_frames):
        missing = [frame for frame in context_frames if frame not in images]
        raise KeyError(f"Missing context frames in COLMAP images.txt: {missing}")

    ply = PlyData.read(args.source_ply)
    vertex = ply["vertex"].data.copy()
    if len(vertex) != vertices_per_view * num_views:
        raise ValueError(
            f"Unexpected vertex count {len(vertex)}; expected {vertices_per_view * num_views}"
        )

    xyz_ply = vertex_xyz(vertex)
    ref_frame = context_frames[args.reference_local_view]
    ref_c2w = images[ref_frame]["c2w"]
    ref_r_c2w = ref_c2w[:3, :3]
    ref_r_w2c = ref_r_c2w.T
    xyz_world = (ref_r_c2w @ xyz_ply.T).T
    corrected_world = xyz_world.copy()

    fit_logs: list[dict[str, object]] = []
    per_view_preview: list[np.ndarray] = []
    camera_centers: list[np.ndarray] = []

    for local_view, frame in enumerate(context_frames):
        img = images[frame]
        cam = cameras[int(img["camera_id"])]
        w2c = img["w2c"]
        c2w = img["c2w"]
        camera_centers.append(c2w[:3, 3])
        indices = np.arange(local_view, len(vertex), num_views)
        view_world = xyz_world[indices]

        z_pred_list = []
        z_gt_list = []
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
            pred_point = xyz_world[flat * num_views + local_view]
            gt_point = points3d[pid]
            pred_cam = w2c[:3, :3] @ pred_point + w2c[:3, 3]
            gt_cam = w2c[:3, :3] @ gt_point + w2c[:3, 3]
            if pred_cam[2] > 1e-6 and gt_cam[2] > 1e-6:
                z_pred_list.append(float(pred_cam[2]))
                z_gt_list.append(float(gt_cam[2]))

        if args.mode == "scale":
            fit = robust_scale_fit(np.asarray(z_pred_list), np.asarray(z_gt_list))
        else:
            fit = robust_affine_fit(np.asarray(z_pred_list), np.asarray(z_gt_list))
        if not fit.get("ok", False):
            scale_fit = robust_scale_fit(np.asarray(z_pred_list), np.asarray(z_gt_list))
            fit["fallback_scale_fit"] = scale_fit
            if scale_fit.get("ok", False):
                fit["scale"] = scale_fit["scale"]
                fit["a"] = scale_fit["scale"]
                fit["b"] = 0.0
            else:
                fit["scale"] = 1.0
                fit["a"] = 1.0
                fit["b"] = 0.0
        if args.mode == "scale":
            a = float(fit.get("scale", 1.0))
            b = 0.0
        else:
            a = float(fit["a"])
            b = float(fit["b"])

        cam_points = (w2c[:3, :3] @ view_world.T).T + w2c[:3, 3]
        z = cam_points[:, 2]
        z_new = a * z + b
        ratio = np.ones_like(z)
        valid = np.isfinite(z_new) & np.isfinite(z) & (z > 1e-6) & (z_new > 1e-6)
        ratio[valid] = z_new[valid] / z[valid]
        ratio = np.clip(ratio, args.ratio_min, args.ratio_max)
        cam_points_new = cam_points * ratio[:, None]
        world_new = (c2w[:3, :3] @ (cam_points_new - c2w[:3, 3] * 0).T).T + c2w[:3, 3]
        corrected_world[indices] = world_new
        per_view_preview.append(world_new)

        fit.update(
            {
                "local_view": local_view,
                "frame": frame,
                "ratio_min_actual": float(np.min(ratio)),
                "ratio_median_actual": float(np.median(ratio)),
                "ratio_max_actual": float(np.max(ratio)),
            }
        )
        fit_logs.append(fit)

    corrected_ply = (ref_r_w2c @ corrected_world.T).T
    set_vertex_xyz(vertex, corrected_ply)
    out_ply = args.output_dir / (args.source_ply.stem + "_depth_affine_colmap.ply")
    PlyData([PlyElement.describe(vertex, "vertex")], text=False).write(out_ply)

    preview = args.output_dir / "depth_affine_preview.png"
    make_preview(preview, per_view_preview, camera_centers, context_frames, args.preview_points_per_view)

    summary = {
        "created_at": start,
        "source_ply": str(args.source_ply),
        "colmap": str(args.colmap),
        "output_ply": str(out_ply),
        "preview": str(preview),
        "context_frames": context_frames,
        "reference_frame": ref_frame,
        "model_hw": [args.model_h, args.model_w],
        "trim": args.trim,
        "effective_hw": [eff_h, eff_w],
        "fit_logs": fit_logs,
        "mode": args.mode,
        "ratio_limits": [args.ratio_min, args.ratio_max],
        "bytes": out_ply.stat().st_size,
        "vertices": int(len(vertex)),
    }
    summary_path = args.output_dir / "depth_affine_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
