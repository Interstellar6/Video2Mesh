#!/usr/bin/env python3
"""Prepare instance-level TRELLIS inputs from a Video2Mesh bedroom_4 run."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage


STRUCTURE_CATEGORIES = {"ceiling", "floor", "wall"}


@dataclass
class Candidate:
    frame_id: str
    image_path: str
    mask_path: str
    bbox_xyxy: list[int]
    bbox_width: int
    bbox_height: int
    bbox_area: int
    visible_points: int
    mask_support_points: int
    support_ratio: float
    score: float


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def read_ascii_ply_xyz(path: Path) -> np.ndarray:
    header_lines = 0
    vertex_count: int | None = None
    ascii_format = False
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            header_lines += 1
            stripped = line.strip()
            if stripped == "format ascii 1.0":
                ascii_format = True
            if stripped.startswith("element vertex "):
                vertex_count = int(stripped.split()[-1])
            if stripped == "end_header":
                break
        else:
            raise ValueError(f"PLY header has no end_header: {path}")
    if not ascii_format:
        raise ValueError(f"Only ASCII PLY is supported: {path}")
    if vertex_count is None or vertex_count <= 0:
        raise ValueError(f"PLY has no vertices: {path}")
    points = np.loadtxt(path, dtype=np.float32, skiprows=header_lines, usecols=(0, 1, 2))
    points = np.atleast_2d(points)
    if len(points) != vertex_count:
        raise ValueError(f"PLY vertex count mismatch for {path}: header={vertex_count}, parsed={len(points)}")
    return points


def sampled_points(points: np.ndarray, max_points: int, seed: int) -> np.ndarray:
    if max_points <= 0 or len(points) <= max_points:
        return points
    generator = np.random.default_rng(seed)
    indices = generator.choice(len(points), size=max_points, replace=False)
    return points[indices]


def intrinsic_for_frame(camera_info: dict[str, Any], frame_id: str) -> dict[str, float]:
    intrinsics = camera_info.get("intrinsics")
    camera_ids = camera_info.get("frame_camera_ids")
    if isinstance(intrinsics, dict) and isinstance(camera_ids, dict):
        camera_id = str(camera_ids.get(frame_id, ""))
        record = intrinsics.get(camera_id)
        if isinstance(record, dict):
            return {key: float(record[key]) for key in ("fx", "fy", "cx", "cy", "w", "h")}
    record = camera_info.get("intrinsic")
    if not isinstance(record, dict):
        raise KeyError(f"No intrinsic available for frame {frame_id}")
    return {key: float(record[key]) for key in ("fx", "fy", "cx", "cy", "w", "h")}


def project_points(points: np.ndarray, world_to_camera: np.ndarray, intrinsic: dict[str, float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    camera_points = points @ world_to_camera[:3, :3].T + world_to_camera[:3, 3]
    depth = camera_points[:, 2]
    valid = depth > 1e-5
    safe_depth = np.where(valid, depth, 1.0)
    u = intrinsic["fx"] * camera_points[:, 0] / safe_depth + intrinsic["cx"]
    v = intrinsic["fy"] * camera_points[:, 1] / safe_depth + intrinsic["cy"]
    return u, v, valid


def candidate_for_frame(
    points: np.ndarray,
    frame_id: str,
    image_path: Path,
    mask_path: Path,
    world_to_camera: np.ndarray,
    intrinsic: dict[str, float],
    probability_threshold: float,
    min_support_points: int,
) -> Candidate | None:
    mask = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8)
    width, height = image_path and Image.open(image_path).size
    if mask.shape != (height, width):
        mask = np.asarray(Image.fromarray(mask).resize((width, height), Image.Resampling.NEAREST), dtype=np.uint8)
    foreground = mask >= int(round(probability_threshold * 255.0))
    if not foreground.any():
        return None
    u, v, in_front = project_points(points, world_to_camera, intrinsic)
    ui = np.rint(u).astype(np.int32)
    vi = np.rint(v).astype(np.int32)
    in_image = in_front & (ui >= 0) & (ui < width) & (vi >= 0) & (vi < height)
    if int(in_image.sum()) < min_support_points:
        return None
    indices = np.flatnonzero(in_image)
    support = foreground[vi[indices], ui[indices]]
    support_indices = indices[support]
    if len(support_indices) < min_support_points:
        return None
    support_u = u[support_indices]
    support_v = v[support_indices]
    x0, x1 = np.percentile(support_u, (1.0, 99.0))
    y0, y1 = np.percentile(support_v, (1.0, 99.0))
    raw_width = max(1.0, float(x1 - x0))
    raw_height = max(1.0, float(y1 - y0))
    padding = max(12.0, 0.18 * max(raw_width, raw_height))
    box = [
        max(0, int(math.floor(x0 - padding))),
        max(0, int(math.floor(y0 - padding))),
        min(width, int(math.ceil(x1 + padding))),
        min(height, int(math.ceil(y1 + padding))),
    ]
    box_width = max(1, box[2] - box[0])
    box_height = max(1, box[3] - box[1])
    area = box_width * box_height
    support_ratio = float(len(support_indices) / len(indices))
    score = float(area * (1.0 + math.log1p(len(support_indices))) * max(0.05, support_ratio))
    return Candidate(
        frame_id=frame_id,
        image_path=str(image_path),
        mask_path=str(mask_path),
        bbox_xyxy=box,
        bbox_width=box_width,
        bbox_height=box_height,
        bbox_area=area,
        visible_points=int(len(indices)),
        mask_support_points=int(len(support_indices)),
        support_ratio=support_ratio,
        score=score,
    )


def mask_for_candidate(candidate: Candidate, probability_threshold: float, min_component_support: float) -> tuple[Image.Image, Image.Image, dict[str, Any]]:
    image = Image.open(candidate.image_path).convert("RGB")
    mask = np.asarray(Image.open(candidate.mask_path).convert("L"), dtype=np.uint8)
    if mask.shape != (image.height, image.width):
        mask = np.asarray(Image.fromarray(mask).resize(image.size, Image.Resampling.NEAREST), dtype=np.uint8)
    foreground = mask >= int(round(probability_threshold * 255.0))
    x0, y0, x1, y1 = candidate.bbox_xyxy
    crop_mask = foreground[y0:y1, x0:x1]
    labels, label_count = ndimage.label(crop_mask)
    retained_labels: list[int] = []
    if label_count:
        component_sizes = np.bincount(labels.ravel())
        nonzero_sizes = component_sizes[1:]
        if len(nonzero_sizes):
            threshold = max(8, int(nonzero_sizes.max() * min_component_support))
            retained_labels = [int(index) for index, size in enumerate(component_sizes) if index and size >= threshold]
    if retained_labels:
        cleaned = np.isin(labels, retained_labels)
    else:
        cleaned = crop_mask
    if int(cleaned.sum()) < 16:
        cleaned = crop_mask
    cropped_image = image.crop((x0, y0, x1, y1))
    rgba = cropped_image.convert("RGBA")
    rgba.putalpha(Image.fromarray((cleaned.astype(np.uint8) * 255), mode="L"))
    return cropped_image, rgba, {
        "foreground_pixels_before_component_filter": int(crop_mask.sum()),
        "foreground_pixels_after_component_filter": int(cleaned.sum()),
        "component_count": int(label_count),
        "retained_component_labels": retained_labels,
    }


def make_contact_sheet(items: list[dict[str, Any]], output_path: Path) -> None:
    tile_width = 320
    tile_height = 290
    columns = 3
    rows = max(1, math.ceil(len(items) / columns))
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), (27, 31, 34))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, item in enumerate(items):
        column = index % columns
        row = index // columns
        origin_x = column * tile_width
        origin_y = row * tile_height
        preview = Image.open(item["rgba_path"]).convert("RGBA")
        preview = ImageOps.contain(preview, (tile_width - 24, tile_height - 72), Image.Resampling.LANCZOS)
        checker = Image.new("RGBA", preview.size, (67, 73, 77, 255))
        checker.alpha_composite(preview)
        sheet.paste(checker.convert("RGB"), (origin_x + 12, origin_y + 12))
        label = item["object_id"].replace("sam3_", "")
        detail = f"{item['frame_id']}  {item['bbox_width']}x{item['bbox_height']}  alpha={item['alpha_pixels']}"
        draw.text((origin_x + 12, origin_y + tile_height - 45), label, fill=(238, 239, 240), font=font)
        draw.text((origin_x + 12, origin_y + tile_height - 26), detail, fill=(178, 185, 188), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--object-manifest", type=Path, required=True)
    parser.add_argument("--camera-info", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path, required=True)
    parser.add_argument("--masks-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--max-points-per-object", type=int, default=80000)
    parser.add_argument("--min-mask-probability", type=float, default=0.6)
    parser.add_argument("--min-support-points", type=int, default=80)
    parser.add_argument("--min-component-support", type=float, default=0.01)
    parser.add_argument("--include-structure", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    object_manifest = read_json(args.object_manifest)
    camera_info = read_json(args.camera_info)
    objects = object_manifest.get("objects")
    extrinsics = camera_info.get("extrinsic")
    if not isinstance(objects, dict) or not isinstance(extrinsics, dict):
        raise ValueError("Object manifest or camera info has an unexpected schema")
    output_root = args.output_root.resolve()
    input_dir = output_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = {path.stem: path for path in args.frames_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg"}}
    results: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    for ordinal, (object_id, record) in enumerate(sorted(objects.items())):
        if not isinstance(record, dict):
            skipped[object_id] = "invalid_object_record"
            continue
        category = str(record.get("category") or "")
        if category in STRUCTURE_CATEGORIES and not args.include_structure:
            skipped[object_id] = "background_structure_kept_as_scan_geometry"
            continue
        point_cloud = Path(str(record.get("path") or ""))
        mask_dir = args.masks_dir / f"sam3_class_{category}"
        if not point_cloud.is_file():
            skipped[object_id] = f"missing_point_cloud:{point_cloud}"
            continue
        if not mask_dir.is_dir():
            skipped[object_id] = f"missing_category_masks:{mask_dir}"
            continue
        points = sampled_points(read_ascii_ply_xyz(point_cloud), args.max_points_per_object, seed=20260713 + ordinal)
        candidates: list[Candidate] = []
        for mask_path in sorted(mask_dir.glob("*.png")):
            frame_id = mask_path.stem
            image_path = frame_paths.get(frame_id)
            extrinsic = extrinsics.get(frame_id)
            if image_path is None or not isinstance(extrinsic, list):
                continue
            candidate = candidate_for_frame(
                points,
                frame_id,
                image_path,
                mask_path,
                np.asarray(extrinsic, dtype=np.float32),
                intrinsic_for_frame(camera_info, frame_id),
                args.min_mask_probability,
                args.min_support_points,
            )
            if candidate is not None:
                candidates.append(candidate)
        if not candidates:
            skipped[object_id] = "no_frame_with_instance_projected_inside_sam3_mask"
            continue
        candidates.sort(key=lambda item: item.score, reverse=True)
        selected = candidates[0]
        rgb, rgba, component_report = mask_for_candidate(selected, args.min_mask_probability, args.min_component_support)
        rgb_path = input_dir / f"{object_id}_rgb.png"
        rgba_path = input_dir / f"{object_id}_rgba.png"
        rgb.save(rgb_path)
        rgba.save(rgba_path)
        alpha_pixels = int(np.asarray(rgba.getchannel("A"), dtype=np.uint8).astype(bool).sum())
        result = {
            "object_id": object_id,
            "name": record.get("name"),
            "category": category,
            "source_point_cloud": str(point_cloud),
            "sampled_point_count": int(len(points)),
            "frame_id": selected.frame_id,
            "source_image": selected.image_path,
            "source_mask": selected.mask_path,
            "bbox_xyxy": selected.bbox_xyxy,
            "bbox_width": selected.bbox_width,
            "bbox_height": selected.bbox_height,
            "bbox_area": selected.bbox_area,
            "visible_points": selected.visible_points,
            "mask_support_points": selected.mask_support_points,
            "support_ratio": selected.support_ratio,
            "selection_score": selected.score,
            "rgb_path": str(rgb_path),
            "rgba_path": str(rgba_path),
            "alpha_pixels": alpha_pixels,
            "low_detail_input": min(selected.bbox_width, selected.bbox_height) < 96 or alpha_pixels < 2500,
            "component_filter": component_report,
            "top_candidates": [asdict(item) for item in candidates[:5]],
        }
        results.append(result)
        print(f"prepared {object_id}: frame={selected.frame_id} box={selected.bbox_width}x{selected.bbox_height} alpha={alpha_pixels}")
    contact_sheet = output_root / "qa" / "input_contact_sheet.png"
    make_contact_sheet(results, contact_sheet)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "instance_3d_point_projection_intersected_with_real_sam3_class_masks",
        "object_manifest": str(args.object_manifest.resolve()),
        "camera_info": str(args.camera_info.resolve()),
        "frames_dir": str(args.frames_dir.resolve()),
        "masks_dir": str(args.masks_dir.resolve()),
        "output_root": str(output_root),
        "input_contact_sheet": str(contact_sheet),
        "parameters": {
            "max_points_per_object": args.max_points_per_object,
            "min_mask_probability": args.min_mask_probability,
            "min_support_points": args.min_support_points,
            "min_component_support": args.min_component_support,
            "include_structure": args.include_structure,
        },
        "prepared_count": len(results),
        "skipped_count": len(skipped),
        "prepared": results,
        "skipped": skipped,
    }
    report_path = input_dir / "input_selection_manifest.json"
    write_json(report_path, report)
    print(f"prepared {len(results)} instance inputs; skipped {len(skipped)}; manifest={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
