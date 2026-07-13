#!/usr/bin/env python3
"""Prepare disjoint TRELLIS RGBA inputs from SAM3 text-plus-box instance masks."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from prepare_trellis_bedroom4_instances import instance_contract


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def normalize_box(value: Any, width: int, height: int) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"Expected prompt_box_xyxy with four values, got {value!r}")
    x0, y0, x1, y1 = [float(item) for item in value]
    result = (
        max(0, int(math.floor(x0))),
        max(0, int(math.floor(y0))),
        min(width, int(math.ceil(x1))),
        min(height, int(math.ceil(y1))),
    )
    if result[2] <= result[0] or result[3] <= result[1]:
        raise ValueError(f"Empty prompt box after clipping: {value!r}")
    return result


def constrain_to_box(mask: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    constrained = np.zeros_like(mask, dtype=bool)
    constrained[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return constrained


def resolve_mask_overlaps(masks: list[np.ndarray], boxes: list[tuple[int, int, int, int]]) -> tuple[list[np.ndarray], int]:
    """Make prompted masks mutually exclusive without duplicating shared frame pixels."""
    if not masks:
        return [], 0
    stacked = np.stack(masks, axis=0)
    overlap = stacked.sum(axis=0) > 1
    overlap_pixels = int(overlap.sum())
    if not overlap_pixels:
        return masks, 0
    y, x = np.nonzero(overlap)
    candidates = stacked[:, y, x]
    distances = np.full(candidates.shape, np.inf, dtype=np.float32)
    for index, (x0, y0, x1, y1) in enumerate(boxes):
        center_x = (x0 + x1 - 1) / 2.0
        center_y = (y0 + y1 - 1) / 2.0
        half_width = max(1.0, (x1 - x0) / 2.0)
        half_height = max(1.0, (y1 - y0) / 2.0)
        distance = ((x - center_x) / half_width) ** 2 + ((y - center_y) / half_height) ** 2
        distances[index, candidates[index]] = distance[candidates[index]]
    chosen = np.argmin(distances, axis=0)
    for index in range(len(masks)):
        masks[index][y, x] = chosen == index
    return masks, overlap_pixels


def crop_bounds(mask: np.ndarray, padding_pixels: int) -> tuple[int, int, int, int]:
    y, x = np.nonzero(mask)
    if not len(x):
        raise ValueError("Prompted instance mask has no foreground pixels")
    return (
        max(0, int(x.min()) - padding_pixels),
        max(0, int(y.min()) - padding_pixels),
        min(mask.shape[1], int(x.max()) + 1 + padding_pixels),
        min(mask.shape[0], int(y.max()) + 1 + padding_pixels),
    )


def detailed_asset_prompt(record: dict[str, Any], crop_size: tuple[int, int]) -> str:
    contract = instance_contract(str(record["category"]))
    semantic_prompt = str(record.get("semantic_prompt") or record["category"])
    description = str(record.get("description") or "Describe only visible evidence.")
    return "\n".join(
        [
            "You are preparing a single-instance visual asset for image-to-3D generation.",
            f"Target id: {record['object_id']}.",
            f"Category: {record['category']}.",
            f"Semantic prompt used for segmentation: {semantic_prompt}.",
            f"Target scope: {contract['target_scope']}",
            f"Visible-object description: {description}",
            f"Critical visible parts: {', '.join(contract['critical_parts'])}.",
            f"Exclude: {', '.join(contract['forbidden_merges'])}.",
            "The RGBA image is constrained by a positive SAM3 box prompt and must represent one physical asset only.",
            "Do not merge an adjacent same-category instance, shared central frame, wall, curtain, blind, floor, furniture, or exterior background.",
            f"Current crop size: {crop_size[0]} x {crop_size[1]} pixels.",
            "Describe material, geometry, orientation, visible subparts, truncation, and occlusion from image evidence only.",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--padding-pixels", type=int, default=14)
    parser.add_argument("--min-alpha-pixels", type=int, default=512)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.padding_pixels < 0:
        raise ValueError("--padding-pixels must be non-negative")
    config = read_json(args.instance_config)
    image_path = Path(str(config.get("source_image") or ""))
    instances = config.get("instances")
    if not image_path.is_file():
        raise FileNotFoundError(f"Missing source image: {image_path}")
    if not isinstance(instances, list) or not instances:
        raise ValueError("instance-config requires a nonempty instances list")
    image = Image.open(image_path).convert("RGB")
    masks: list[np.ndarray] = []
    boxes: list[tuple[int, int, int, int]] = []
    records: list[dict[str, Any]] = []
    for raw in instances:
        if not isinstance(raw, dict):
            raise ValueError("Each instance record must be an object")
        object_id = str(raw.get("object_id") or "")
        category = str(raw.get("category") or "")
        mask_path = Path(str(raw.get("mask_path") or ""))
        if not object_id or not category or not mask_path.is_file():
            raise ValueError(f"Invalid prompted instance record: {raw!r}")
        mask = np.asarray(Image.open(mask_path).convert("L"), dtype=np.uint8) > 0
        if mask.shape != (image.height, image.width):
            mask = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize(image.size, Image.Resampling.NEAREST), dtype=np.uint8) > 0
        box = normalize_box(raw.get("prompt_box_xyxy"), image.width, image.height)
        constrained = constrain_to_box(mask, box)
        if int(constrained.sum()) < args.min_alpha_pixels:
            raise ValueError(f"{object_id} has only {int(constrained.sum())} pixels after prompt-box constraint")
        record = dict(raw)
        record["object_id"] = object_id
        record["category"] = category
        record["mask_path"] = str(mask_path)
        records.append(record)
        masks.append(constrained)
        boxes.append(box)
    masks, overlap_pixels = resolve_mask_overlaps(masks, boxes)
    output_root = args.output_root.resolve()
    input_dir = output_root / "input"
    request_dir = input_dir / "vlm_requests"
    prepared: list[dict[str, Any]] = []
    for record, mask, box in zip(records, masks, boxes):
        alpha_pixels = int(mask.sum())
        if alpha_pixels < args.min_alpha_pixels:
            raise ValueError(f"{record['object_id']} has only {alpha_pixels} pixels after overlap resolution")
        x0, y0, x1, y1 = crop_bounds(mask, args.padding_pixels)
        crop_box = (x0, y0, x1, y1)
        rgb = image.crop(crop_box)
        rgba = rgb.convert("RGBA")
        crop_mask = mask[y0:y1, x0:x1]
        rgba.putalpha(Image.fromarray(crop_mask.astype(np.uint8) * 255, mode="L"))
        rgb_path = input_dir / f"{record['object_id']}_rgb.png"
        rgba_path = input_dir / f"{record['object_id']}_rgba.png"
        support_path = input_dir / f"{record['object_id']}_prompted_support.png"
        rgb_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(rgb_path)
        rgba.save(rgba_path)
        Image.fromarray(crop_mask.astype(np.uint8) * 255, mode="L").save(support_path)
        contract = instance_contract(str(record["category"]))
        vlm_request = {
            "schema_version": 1,
            "kind": "video2mesh.instance_asset_vlm_request",
            "object_id": record["object_id"],
            "category": record["category"],
            "input_contract": contract,
            "source": "sam3_text_and_positive_box_prompt",
            "prompt": detailed_asset_prompt(record, rgb.size),
            "segmentation_evidence": {
                "semantic_prompt": record.get("semantic_prompt"),
                "prompt_box_xyxy": list(box),
                "source_mask": record["mask_path"],
                "source_mask_score": record.get("mask_score"),
                "alpha_pixels": alpha_pixels,
            },
        }
        request_path = request_dir / f"{record['object_id']}.json"
        write_json(request_path, vlm_request)
        prepared.append(
            {
                "object_id": record["object_id"],
                "name": record.get("name") or record["object_id"],
                "category": record["category"],
                "source_image": str(image_path),
                "source_mask": record["mask_path"],
                "prompt_box_xyxy": list(box),
                "bbox_xyxy": [x0, y0, x1, y1],
                "bbox_width": x1 - x0,
                "bbox_height": y1 - y0,
                "rgb_path": str(rgb_path),
                "rgba_path": str(rgba_path),
                "projected_support_path": str(support_path),
                "vlm_request_path": str(request_path),
                "alpha_pixels": alpha_pixels,
                "low_detail_input": min(x1 - x0, y1 - y0) < 96 or alpha_pixels < 2500,
                "mask_provenance": "SAM3 text prompt plus positive geometric box, then mutually exclusive overlap assignment",
            }
        )
        print(f"prepared {record['object_id']}: box={x1 - x0}x{y1 - y0} alpha={alpha_pixels}")
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "sam3_text_plus_positive_box_instance_masks_to_disjoint_trellis_rgba",
        "instance_config": str(args.instance_config.resolve()),
        "source_image": str(image_path.resolve()),
        "overlap_pixels_resolved": overlap_pixels,
        "prepared": prepared,
    }
    manifest_path = input_dir / "input_selection_manifest.json"
    write_json(manifest_path, report)
    print(f"prepared={len(prepared)} manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
