#!/usr/bin/env python3
"""Render compact 2D SAM3 and 3D bbox QA images for a full Holi-Spatial run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


PALETTE = [
    (230, 57, 70),
    (41, 157, 143),
    (244, 162, 97),
    (69, 123, 157),
    (233, 196, 106),
    (155, 93, 229),
    (42, 180, 108),
    (235, 103, 177),
    (93, 173, 226),
    (213, 94, 0),
    (117, 117, 117),
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def object_masks(mask_root: Path) -> dict[str, dict[str, Path]]:
    result: dict[str, dict[str, Path]] = {}
    for directory in sorted(path for path in mask_root.iterdir() if path.is_dir()):
        result[directory.name] = {path.stem: path for path in sorted(directory.glob("*.png"))}
    return result


def evenly_spaced(values: list[Path], count: int) -> list[Path]:
    if len(values) <= count:
        return values
    indices = np.linspace(0, len(values) - 1, count).round().astype(int)
    return [values[int(index)] for index in indices]


def overlay_masks(
    image_path: Path,
    frame_id: str,
    masks: dict[str, dict[str, Path]],
    labels: dict[str, Any],
    selected_ids: list[str] | None = None,
) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    base = np.asarray(image, dtype=np.float32)
    object_ids = selected_ids or sorted(masks)
    active: list[tuple[str, tuple[int, int, int], float]] = []
    for semantic_index, object_id in enumerate(object_ids):
        mask_path = masks.get(object_id, {}).get(frame_id)
        if mask_path is None:
            continue
        mask_image = Image.open(mask_path).convert("L")
        if mask_image.size != image.size:
            mask_image = mask_image.resize(image.size, Image.Resampling.NEAREST)
        probability = np.asarray(mask_image, dtype=np.float32) / 255.0
        selected = probability >= 0.6
        if not np.any(selected):
            continue
        color = PALETTE[semantic_index % len(PALETTE)]
        alpha = np.clip(probability * 0.48, 0.0, 0.48)[..., None]
        color_array = np.asarray(color, dtype=np.float32)[None, None, :]
        base = np.where(selected[..., None], base * (1.0 - alpha) + color_array * alpha, base)
        name = str(labels.get(object_id, {}).get("category") or object_id)
        active.append((name, color, float(probability[selected].max())))

    output = Image.fromarray(np.clip(np.rint(base), 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(output, "RGBA")
    title_font = font(22)
    label_font = font(16)
    draw.rectangle((12, 10, 260, 44), fill=(0, 0, 0, 178))
    draw.text((22, 15), f"frame {frame_id}", fill="white", font=title_font)
    y = 52
    for name, color, score in active:
        width = min(280, 105 + len(name) * 9)
        draw.rectangle((12, y, width, y + 23), fill=(0, 0, 0, 160))
        draw.rectangle((19, y + 5, 31, y + 17), fill=(*color, 255))
        draw.text((38, y + 2), f"{name} {score:.2f}", fill="white", font=label_font)
        y += 25
    return output


def contact_sheet(images: list[Image.Image], output: Path, columns: int, tile_size: tuple[int, int]) -> None:
    rows = int(np.ceil(len(images) / columns))
    sheet = Image.new("RGB", (columns * tile_size[0], rows * tile_size[1]), (20, 20, 20))
    for index, image in enumerate(images):
        tile = image.resize(tile_size, Image.Resampling.LANCZOS)
        sheet.paste(tile, ((index % columns) * tile_size[0], (index // columns) * tile_size[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def make_2d_qa(
    frames_dir: Path,
    mask_root: Path,
    labels: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    masks = object_masks(mask_root)
    frames = sorted(path for path in frames_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
    selected_frames = evenly_spaced(frames, 8)
    overview_images = [overlay_masks(path, path.stem, masks, labels) for path in selected_frames]
    overview_path = output_dir / "sam3_2d_overlay_contact_sheet.jpg"
    contact_sheet(overview_images, overview_path, columns=4, tile_size=(640, 360))

    per_class_images: list[Image.Image] = []
    best_frames: dict[str, Any] = {}
    frame_lookup = {path.stem: path for path in frames}
    for object_id in sorted(masks):
        scored: list[tuple[float, str, Path]] = []
        for frame_id, mask_path in masks[object_id].items():
            array = np.asarray(Image.open(mask_path).convert("L"), dtype=np.float32)
            scored.append((float(array.sum()), frame_id, mask_path))
        if not scored:
            continue
        _mass, frame_id, mask_path = max(scored)
        frame_path = frame_lookup.get(frame_id)
        if frame_path is None:
            continue
        image = overlay_masks(frame_path, frame_id, masks, labels, [object_id])
        per_class_images.append(image)
        best_frames[object_id] = {
            "frame_id": frame_id,
            "mask": str(mask_path),
            "category": labels.get(object_id, {}).get("category"),
        }
    per_class_path = output_dir / "sam3_2d_per_class_best.jpg"
    contact_sheet(per_class_images, per_class_path, columns=3, tile_size=(640, 360))
    return {
        "class_count": len(masks),
        "overview": str(overview_path),
        "per_class": str(per_class_path),
        "overview_frames": [path.stem for path in selected_frames],
        "best_frames": best_frames,
    }


def make_bbox_topdown(object_masks_path: Path, output_dir: Path) -> dict[str, Any] | None:
    if not object_masks_path.exists():
        return None
    objects = read_json(object_masks_path).get("objects", {})
    records = []
    for object_id, item in sorted(objects.items()):
        box = item.get("bbox_3d") or {}
        if not box.get("min") or not box.get("max"):
            continue
        records.append((object_id, item, np.asarray(box["min"], dtype=float), np.asarray(box["max"], dtype=float)))
    if not records:
        return None
    mins = np.min(np.asarray([item[2] for item in records]), axis=0)
    maxs = np.max(np.asarray([item[3] for item in records]), axis=0)
    width, height = 1400, 900
    margin = 80
    canvas = Image.new("RGB", (width, height), (248, 249, 250))
    draw = ImageDraw.Draw(canvas, "RGBA")
    title_font = font(28)
    label_font = font(15)
    draw.text((margin, 22), "SAM3 + DA3 3D instance bboxes (X/Z top view)", fill=(25, 25, 25), font=title_font)
    span_x = max(float(maxs[0] - mins[0]), 1e-6)
    span_z = max(float(maxs[2] - mins[2]), 1e-6)
    scale = min((width - 2 * margin) / span_x, (height - 2 * margin) / span_z)

    def project(x: float, z: float) -> tuple[float, float]:
        return margin + (x - mins[0]) * scale, height - margin - (z - mins[2]) * scale

    legend_y = 70
    categories: dict[str, tuple[int, int, int]] = {}
    for index, (object_id, item, low, high) in enumerate(records):
        category = str(item.get("category") or "unknown")
        color = categories.setdefault(category, PALETTE[len(categories) % len(PALETTE)])
        x0, y1 = project(float(low[0]), float(low[2]))
        x1, y0 = project(float(high[0]), float(high[2]))
        draw.rectangle((x0, y0, x1, y1), fill=(*color, 48), outline=(*color, 255), width=3)
        draw.text((x0 + 3, y0 + 2), object_id.replace("sam3_", ""), fill=(20, 20, 20), font=label_font)
    for category, color in categories.items():
        draw.rectangle((width - 240, legend_y, width - 224, legend_y + 16), fill=(*color, 255))
        draw.text((width - 216, legend_y - 2), category, fill=(25, 25, 25), font=label_font)
        legend_y += 23
    output = output_dir / "sam3_da3_3d_bbox_topdown.png"
    canvas.save(output)
    return {
        "object_count": len(records),
        "path": str(output),
        "scene_bounds": {"min": mins.tolist(), "max": maxs.tolist()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(project_root / "manifest.json")
    frames_dir = project_root / manifest["scene"]["frames_dir"]
    mask_root = project_root / manifest["masks"]["mask_2d_dir"]
    labels = read_json(project_root / "masks" / "object_labels.json")
    class_labels_path = project_root / "masks" / "object_labels_class_fusion.json"
    if class_labels_path.exists():
        labels.update(read_json(class_labels_path))
    two_d = make_2d_qa(frames_dir, mask_root, labels, output_dir)
    bbox_path = project_root / manifest["masks"]["mask_3d_dir"] / "object_masks.json"
    three_d = make_bbox_topdown(bbox_path, output_dir)
    report = {
        "schema_version": 1,
        "project_root": str(project_root),
        "output_dir": str(output_dir),
        "sam3_2d": two_d,
        "bbox_3d": three_d,
    }
    write_json(output_dir / "visualization_report.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
