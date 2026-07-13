#!/usr/bin/env python3
"""Create lightweight 2D and 3D visualizations for a Holi-Spatial SAM3 run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "bed": (225, 66, 64),
    "ceiling": (89, 190, 210),
    "floor": (231, 180, 52),
    "lamp": (208, 88, 172),
    "nightstand": (73, 117, 205),
    "plant": (67, 157, 88),
    "wall": (145, 151, 160),
    "window": (43, 159, 147),
    "board": (210, 125, 51),
    "wall art": (147, 95, 185),
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def color_for(label: str) -> tuple[int, int, int]:
    return COLORS.get(label, (220, 220, 220))


def resolve_mask_path(run_root: Path, item: dict[str, Any]) -> Path:
    raw = Path(str(item["mask_path"]))
    if raw.exists():
        return raw
    frame = Path(str(item["image"])).stem
    candidate = (
        run_root
        / "sam3_masks_scannetppv2_new"
        / "bedroom_4"
        / frame
        / raw.name
    )
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Mask not found for {item['image']}: {raw}")


def overlay_frame(
    image_path: Path,
    items: list[dict[str, Any]],
    run_root: Path,
    *,
    alpha: float = 0.38,
) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    canvas = np.asarray(image, dtype=np.float32).copy()
    for item in items:
        mask = np.asarray(Image.open(resolve_mask_path(run_root, item)).convert("L")) > 0
        if mask.shape != canvas.shape[:2]:
            resized = Image.fromarray(mask.astype(np.uint8) * 255).resize(
                image.size, Image.Resampling.NEAREST
            )
            mask = np.asarray(resized) > 0
        color = np.asarray(color_for(str(item["label"])), dtype=np.float32)
        canvas[mask] = canvas[mask] * (1.0 - alpha) + color * alpha

    result = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(result)
    font = get_font(16)
    for item in items:
        bbox = item.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x0, y0, x1, y1 = [float(value) for value in bbox]
        x0 = max(0, min(result.width - 1, x0))
        y0 = max(0, min(result.height - 1, y0))
        x1 = max(0, min(result.width - 1, x1))
        y1 = max(0, min(result.height - 1, y1))
        color = color_for(str(item["label"]))
        draw.rectangle((x0, y0, x1, y1), outline=color, width=2)
        text = f"{item['label']} {float(item.get('score', 0.0)):.2f}"
        text_box = draw.textbbox((x0, y0), text, font=font)
        text_w = text_box[2] - text_box[0]
        text_h = text_box[3] - text_box[1]
        text_y = max(0, y0 - text_h - 4)
        draw.rectangle((x0, text_y, x0 + text_w + 6, text_y + text_h + 4), fill=(18, 20, 24))
        draw.text((x0 + 3, text_y + 2), text, fill=color, font=font)
    return result


def make_contact_sheet(
    image_root: Path,
    by_frame: dict[str, list[dict[str, Any]]],
    run_root: Path,
    output_path: Path,
) -> None:
    frames = sorted(by_frame)
    picks = [frames[round(index * (len(frames) - 1) / 7)] for index in range(8)]
    tile_size = (640, 360)
    title_h = 30
    sheet = Image.new("RGB", (tile_size[0] * 2, (tile_size[1] + title_h) * 4), (19, 21, 25))
    font = get_font(18)
    draw = ImageDraw.Draw(sheet)
    for index, frame in enumerate(picks):
        image_path = image_root / frame
        overlay = overlay_frame(image_path, by_frame[frame], run_root)
        overlay.thumbnail(tile_size, Image.Resampling.LANCZOS)
        x = (index % 2) * tile_size[0]
        y = (index // 2) * (tile_size[1] + title_h)
        sheet.paste(overlay, (x, y + title_h))
        draw.text((x + 10, y + 6), f"{frame} | {len(by_frame[frame])} masks", fill="white", font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def make_per_class_sheet(
    image_root: Path,
    items: list[dict[str, Any]],
    run_root: Path,
    output_path: Path,
) -> None:
    best: dict[str, dict[str, Any]] = {}
    for item in items:
        label = str(item["label"])
        if label not in best or float(item.get("score", 0.0)) > float(best[label].get("score", 0.0)):
            best[label] = item
    labels = sorted(best)
    cols = 4
    rows = (len(labels) + cols - 1) // cols
    tile_size = (480, 270)
    title_h = 34
    sheet = Image.new("RGB", (tile_size[0] * cols, (tile_size[1] + title_h) * rows), (19, 21, 25))
    draw = ImageDraw.Draw(sheet)
    font = get_font(18)
    for index, label in enumerate(labels):
        item = best[label]
        image_path = image_root / str(item["image"])
        overlay = overlay_frame(image_path, [item], run_root, alpha=0.48)
        overlay.thumbnail(tile_size, Image.Resampling.LANCZOS)
        x = (index % cols) * tile_size[0]
        y = (index // cols) * (tile_size[1] + title_h)
        sheet.paste(overlay, (x, y + title_h))
        title = f"{label} | score {float(item.get('score', 0.0)):.3f} | {item['image']}"
        draw.text((x + 8, y + 7), title, fill=color_for(label), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def make_stats_chart(
    mask_counts: Counter[str],
    bbox_counts: Counter[str],
    output_path: Path,
) -> None:
    labels = sorted(set(mask_counts) | set(bbox_counts))
    width, height = 1200, 650
    margin_left, margin_right, margin_top, margin_bottom = 150, 50, 70, 90
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    image = Image.new("RGB", (width, height), (20, 22, 27))
    draw = ImageDraw.Draw(image)
    title_font = get_font(28)
    label_font = get_font(17)
    draw.text((margin_left, 20), "SAM3 2D masks vs lifted 3D boxes", fill="white", font=title_font)
    max_value = max([1, *mask_counts.values(), *bbox_counts.values()])
    group_w = plot_w / max(1, len(labels))
    bar_w = max(10, int(group_w * 0.28))
    for index, label in enumerate(labels):
        center_x = margin_left + (index + 0.5) * group_w
        mask_h = int(plot_h * mask_counts[label] / max_value)
        bbox_h = int(plot_h * bbox_counts[label] / max_value)
        color = color_for(label)
        x0 = int(center_x - bar_w - 2)
        x1 = int(center_x - 2)
        x2 = int(center_x + 2)
        x3 = int(center_x + bar_w + 2)
        baseline = margin_top + plot_h
        draw.rectangle((x0, baseline - mask_h, x1, baseline), fill=color)
        draw.rectangle((x2, baseline - bbox_h, x3, baseline), fill=(235, 235, 235))
        draw.text((x0, baseline - mask_h - 24), str(mask_counts[label]), fill=color, font=label_font)
        draw.text((x2, baseline - bbox_h - 24), str(bbox_counts[label]), fill="white", font=label_font)
        draw.text((int(center_x - group_w * 0.43), baseline + 14), label, fill="white", font=label_font)
    draw.line((margin_left, margin_top + plot_h, width - margin_right, margin_top + plot_h), fill=(120, 125, 135), width=2)
    draw.rectangle((margin_left, height - 36, margin_left + 18, height - 18), fill=(225, 66, 64))
    draw.text((margin_left + 26, height - 40), "2D masks (class color)", fill="white", font=label_font)
    draw.rectangle((margin_left + 280, height - 36, margin_left + 298, height - 18), fill=(235, 235, 235))
    draw.text((margin_left + 306, height - 40), "3D boxes", fill="white", font=label_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def obb_corners(item: dict[str, Any]) -> np.ndarray:
    transform = np.asarray(item["obb_transform"], dtype=np.float64)
    extents = np.asarray(item["obb_extents"], dtype=np.float64)
    signs = np.asarray(
        [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ],
        dtype=np.float64,
    )
    local = signs * extents[None, :] * 0.5
    return local @ transform[:3, :3].T + transform[:3, 3]


EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]


def make_bbox_ply(items: list[dict[str, Any]], output_path: Path, samples_per_edge: int = 10) -> dict[str, Any]:
    labels = sorted({str(item["label"]) for item in items})
    class_ids = {label: index for index, label in enumerate(labels)}
    rows: list[tuple[float, float, float, int, int, int, int, int]] = []
    all_corners: list[np.ndarray] = []
    for object_id, item in enumerate(items):
        corners = obb_corners(item)
        all_corners.append(corners)
        label = str(item["label"])
        red, green, blue = color_for(label)
        for start, end in EDGES:
            for alpha in np.linspace(0.0, 1.0, samples_per_edge, endpoint=True):
                point = corners[start] * (1.0 - alpha) + corners[end] * alpha
                rows.append((float(point[0]), float(point[1]), float(point[2]), red, green, blue, class_ids[label], object_id))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="ascii") as handle:
        handle.write("ply\nformat ascii 1.0\n")
        handle.write(f"element vertex {len(rows)}\n")
        handle.write("property float x\nproperty float y\nproperty float z\n")
        handle.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        handle.write("property int class_id\nproperty int object_id\nend_header\n")
        for row in rows:
            handle.write(f"{row[0]:.7f} {row[1]:.7f} {row[2]:.7f} {row[3]} {row[4]} {row[5]} {row[6]} {row[7]}\n")
    stacked = np.concatenate(all_corners, axis=0) if all_corners else np.empty((0, 3))
    return {
        "box_count": len(items),
        "point_count": len(rows),
        "labels": labels,
        "class_ids": class_ids,
        "bounds_min": stacked.min(axis=0).tolist() if len(stacked) else None,
        "bounds_max": stacked.max(axis=0).tolist() if len(stacked) else None,
        "note": "Sampled points along lifted AABB edges; this is a bbox visualization, not a per-point 3D semantic mask.",
    }


def make_topdown(items: list[dict[str, Any]], output_path: Path) -> None:
    corners_by_item = [(item, obb_corners(item)) for item in items]
    all_points = np.concatenate([corners[:, [0, 2]] for _, corners in corners_by_item], axis=0)
    mins = all_points.min(axis=0)
    maxs = all_points.max(axis=0)
    span = np.maximum(maxs - mins, 1e-6)
    width, height = 1200, 900
    margin = 70
    image = Image.new("RGB", (width, height), (20, 22, 27))
    draw = ImageDraw.Draw(image, "RGBA")
    title_font = get_font(28)
    label_font = get_font(16)
    draw.text((margin, 20), f"Lifted AABB top-down view | {len(items)} boxes", fill="white", font=title_font)

    def project(points: np.ndarray) -> list[tuple[float, float]]:
        normalized = (points[:, [0, 2]] - mins[None, :]) / span[None, :]
        x = margin + normalized[:, 0] * (width - margin * 2)
        y = height - margin - normalized[:, 1] * (height - margin * 2)
        return list(zip(x.tolist(), y.tolist()))

    for item, corners in corners_by_item:
        polygon = project(corners[[0, 1, 5, 4]])
        color = color_for(str(item["label"]))
        draw.polygon(polygon, fill=(*color, 18), outline=(*color, 150))
    y = 62
    for label in sorted({str(item["label"]) for item in items}):
        color = color_for(label)
        draw.rectangle((width - 235, y, width - 217, y + 18), fill=(*color, 255))
        draw.text((width - 208, y - 2), label, fill="white", font=label_font)
        y += 24
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_root = args.run_root.resolve()
    image_root = args.image_root.resolve()
    output_dir = (args.output_dir or run_root / "visualizations").resolve()
    mask_index = load_json(run_root / "sam3_masks_scannetppv2_new" / "bedroom_4" / "mask_index.json")
    bbox_items = load_json(run_root / "output_scannetppv2_new_aabb" / "bedroom_4.json")
    items = mask_index["items"]
    by_frame: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_frame.setdefault(str(item["image"]), []).append(item)
    output_dir.mkdir(parents=True, exist_ok=True)
    make_contact_sheet(image_root, by_frame, run_root, output_dir / "sam3_2d_overlay_contact_sheet.png")
    make_per_class_sheet(image_root, items, run_root, output_dir / "sam3_2d_per_class_best.png")
    mask_counts = Counter(str(item["label"]) for item in items)
    bbox_counts = Counter(str(item["label"]) for item in bbox_items)
    make_stats_chart(mask_counts, bbox_counts, output_dir / "sam3_mask_bbox_counts.png")
    bbox_summary = make_bbox_ply(bbox_items, output_dir / "sam3_lifted_bbox_edges.ply")
    make_topdown(bbox_items, output_dir / "sam3_lifted_bbox_topdown.png")
    summary = {
        "source_run": str(run_root),
        "image_root": str(image_root),
        "mask_count": len(items),
        "frame_count": len(by_frame),
        "mask_counts_by_label": dict(sorted(mask_counts.items())),
        "bbox_counts_by_label": dict(sorted(bbox_counts.items())),
        "bbox_ply": bbox_summary,
    }
    with (output_dir / "visualization_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
