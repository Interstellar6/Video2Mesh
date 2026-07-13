#!/usr/bin/env python3
"""Turn reviewed VLM split contracts into disjoint TRELLIS RGBA inputs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def reviewed_specs(path: Path) -> dict[str, dict[str, Any]]:
    report = read_json(path)
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError(f"Missing results in VLM spec manifest: {path}")
    specs: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        object_id = result.get("object_id")
        spec_path = result.get("spec_path")
        if not isinstance(object_id, str) or not isinstance(spec_path, str):
            continue
        spec = read_json(Path(spec_path))
        if spec.get("object_id") == object_id:
            specs[object_id] = spec
    return specs


def safe_unit_id(value: Any, index: int) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "")).strip("_-")
    return text or f"unit_{index + 1:02d}"


def normalized_to_pixel_box(box: list[Any], width: int, height: int, padding_fraction: float) -> tuple[int, int, int, int]:
    if len(box) != 4:
        raise ValueError(f"Expected four normalized box coordinates, received: {box!r}")
    values = [float(value) for value in box]
    if any(value < 0.0 or value > 1000.0 for value in values):
        raise ValueError(f"Normalized box is outside [0, 1000]: {box!r}")
    x0, y0, x1, y1 = values
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Normalized box is empty: {box!r}")
    pad_x = (x1 - x0) * padding_fraction
    pad_y = (y1 - y0) * padding_fraction
    return (
        max(0, int(np.floor((x0 - pad_x) / 1000.0 * width))),
        max(0, int(np.floor((y0 - pad_y) / 1000.0 * height))),
        min(width, int(np.ceil((x1 + pad_x) / 1000.0 * width))),
        min(height, int(np.ceil((y1 + pad_y) / 1000.0 * height))),
    )


def partition_alpha_by_boxes(alpha: np.ndarray, boxes: list[tuple[int, int, int, int]]) -> list[np.ndarray]:
    """Assign each foreground pixel to one VLM unit so split assets cannot overlap."""
    if alpha.ndim != 2:
        raise ValueError("Expected a single-channel alpha image")
    foreground_y, foreground_x = np.nonzero(alpha)
    assignments = np.zeros(len(foreground_x), dtype=np.int32)
    distances = np.full((len(boxes), len(foreground_x)), np.inf, dtype=np.float32)
    for index, (x0, y0, x1, y1) in enumerate(boxes):
        center_x = (x0 + x1 - 1) / 2.0
        center_y = (y0 + y1 - 1) / 2.0
        half_width = max(1.0, (x1 - x0) / 2.0)
        half_height = max(1.0, (y1 - y0) / 2.0)
        normalized_distance = ((foreground_x - center_x) / half_width) ** 2 + ((foreground_y - center_y) / half_height) ** 2
        inside = (foreground_x >= x0) & (foreground_x < x1) & (foreground_y >= y0) & (foreground_y < y1)
        distances[index, inside] = normalized_distance[inside]
    # A small model-bbox error should not drop alpha pixels; assign any pixel
    # outside every box to its nearest unit instead of copying it to all units.
    fallback_distances = np.empty_like(distances)
    for index, (x0, y0, x1, y1) in enumerate(boxes):
        center_x = (x0 + x1 - 1) / 2.0
        center_y = (y0 + y1 - 1) / 2.0
        half_width = max(1.0, (x1 - x0) / 2.0)
        half_height = max(1.0, (y1 - y0) / 2.0)
        fallback_distances[index] = ((foreground_x - center_x) / half_width) ** 2 + ((foreground_y - center_y) / half_height) ** 2
    inside_any_box = np.isfinite(distances).any(axis=0)
    assignments = np.where(
        inside_any_box,
        np.argmin(distances, axis=0),
        np.argmin(fallback_distances, axis=0),
    )
    masks: list[np.ndarray] = []
    for index in range(len(boxes)):
        mask = np.zeros_like(alpha, dtype=bool)
        selected = assignments == index
        mask[foreground_y[selected], foreground_x[selected]] = True
        masks.append(mask)
    return masks


def crop_bounds(mask: np.ndarray, padding_pixels: int) -> tuple[int, int, int, int]:
    y, x = np.nonzero(mask)
    if not len(x):
        raise ValueError("Split unit has no foreground pixels")
    return (
        max(0, int(x.min()) - padding_pixels),
        max(0, int(y.min()) - padding_pixels),
        min(mask.shape[1], int(x.max()) + 1 + padding_pixels),
        min(mask.shape[0], int(y.max()) + 1 + padding_pixels),
    )


def materialize_split(
    parent: dict[str, Any],
    spec: dict[str, Any],
    output_input_dir: Path,
    output_spec_dir: Path,
    padding_pixels: int,
    min_alpha_pixels: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rgba = Image.open(Path(str(parent["rgba_path"]))).convert("RGBA")
    rgb = Image.open(Path(str(parent["rgb_path"]))).convert("RGB")
    support = Image.open(Path(str(parent["projected_support_path"]))).convert("L")
    if rgb.size != rgba.size or support.size != rgba.size:
        raise ValueError(f"Input panels are not aligned for {parent['object_id']}")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8) > 0
    units = spec.get("asset_units")
    if not isinstance(units, list) or len(units) < 2:
        raise ValueError(f"Split review has fewer than two asset units for {parent['object_id']}")
    boxes = [normalized_to_pixel_box(list(unit["normalized_bbox_xyxy"]), rgba.width, rgba.height, 0.03) for unit in units]
    masks = partition_alpha_by_boxes(alpha, boxes)
    children: list[dict[str, Any]] = []
    child_specs: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for index, (unit, mask, box) in enumerate(zip(units, masks, boxes)):
        alpha_pixels = int(mask.sum())
        if alpha_pixels < min_alpha_pixels:
            raise ValueError(
                f"Split unit {index} for {parent['object_id']} has only {alpha_pixels} alpha pixels; "
                f"minimum is {min_alpha_pixels}."
            )
        suffix = safe_unit_id(unit.get("unit_id"), index)
        child_id = f"{parent['object_id']}_{suffix}"
        if child_id in used_ids:
            child_id = f"{child_id}_{index + 1:02d}"
        used_ids.add(child_id)
        x0, y0, x1, y1 = crop_bounds(mask, padding_pixels)
        crop_box = (x0, y0, x1, y1)
        crop_rgba = rgba.crop(crop_box)
        crop_rgba.putalpha(Image.fromarray((mask[y0:y1, x0:x1].astype(np.uint8) * 255), mode="L"))
        crop_rgb = rgb.crop(crop_box)
        support_array = np.asarray(support, dtype=np.uint8)
        crop_support = (support_array[y0:y1, x0:x1] * mask[y0:y1, x0:x1].astype(np.uint8)).astype(np.uint8)
        rgb_path = output_input_dir / f"{child_id}_rgb.png"
        rgba_path = output_input_dir / f"{child_id}_rgba.png"
        support_path = output_input_dir / f"{child_id}_projected_support.png"
        output_input_dir.mkdir(parents=True, exist_ok=True)
        crop_rgb.save(rgb_path)
        crop_rgba.save(rgba_path)
        Image.fromarray(crop_support, mode="L").save(support_path)
        child_spec = {
            "schema_version": 1,
            "kind": "video2mesh.instance_asset_vlm_spec",
            "object_id": child_id,
            "category": parent["category"],
            "input_contract": spec["input_contract"],
            "decision": "accept_single_instance",
            "reason": f"Materialized one VLM-reviewed unit from {parent['object_id']}: {spec.get('reason', '')}",
            "observed_same_category_instance_count": 1,
            "asset_units": [unit],
            "shared_structure": spec.get("shared_structure", []),
            "excluded_content": spec.get("excluded_content", []),
            "generation_contract": {
                "one_asset_per_unit": True,
                "forbidden_merges": spec["input_contract"].get("forbidden_merges", []),
                "needs_new_instance_masks": False,
            },
            "generation_allowed": True,
            "parent_object_id": parent["object_id"],
            "parent_vlm_spec": str(spec.get("raw_response_path") or ""),
            "split_method": "disjoint_alpha_partition_using_vlm_normalized_boxes",
            "source_normalized_bbox_xyxy": unit["normalized_bbox_xyxy"],
            "source_pixel_bbox_xyxy": list(box),
            "materialized_crop_xyxy": [x0, y0, x1, y1],
        }
        spec_path = output_spec_dir / f"{child_id}_asset_spec.json"
        write_json(spec_path, child_spec)
        child = {
            "object_id": child_id,
            "name": unit.get("unit_id") or child_id,
            "category": parent["category"],
            "parent_object_id": parent["object_id"],
            "source_rgb_path": parent["rgb_path"],
            "source_rgba_path": parent["rgba_path"],
            "source_vlm_spec": str(spec_path),
            "bbox_xyxy_in_parent_crop": [x0, y0, x1, y1],
            "bbox_width": x1 - x0,
            "bbox_height": y1 - y0,
            "rgb_path": str(rgb_path),
            "rgba_path": str(rgba_path),
            "projected_support_path": str(support_path),
            "alpha_pixels": alpha_pixels,
            "low_detail_input": min(x1 - x0, y1 - y0) < 96 or alpha_pixels < 2500,
        }
        children.append(child)
        child_specs.append({
            "object_id": child_id,
            "category": parent["category"],
            "status": "materialized_from_split_required_review",
            "decision": "accept_single_instance",
            "generation_allowed": True,
            "spec_path": str(spec_path),
        })
    return children, child_specs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--vlm-spec-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--objects", nargs="*")
    parser.add_argument("--padding-pixels", type=int, default=10)
    parser.add_argument("--min-alpha-pixels", type=int, default=512)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.padding_pixels < 0:
        raise ValueError("--padding-pixels must be non-negative")
    manifest = read_json(args.input_manifest)
    prepared = manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared inputs in {args.input_manifest}")
    specs = reviewed_specs(args.vlm_spec_manifest)
    wanted = set(args.objects or [])
    output_root = args.output_root.resolve()
    input_dir = output_root / "input"
    spec_dir = output_root / "vlm"
    children: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    child_specs: list[dict[str, Any]] = []
    for parent in prepared:
        if not isinstance(parent, dict):
            continue
        object_id = str(parent.get("object_id") or "")
        if wanted and object_id not in wanted:
            continue
        spec = specs.get(object_id)
        if not spec:
            reports.append({"object_id": object_id, "status": "skipped_missing_vlm_spec"})
            continue
        if spec.get("decision") != "split_required":
            reports.append({"object_id": object_id, "status": "skipped_not_split_required", "decision": spec.get("decision")})
            continue
        if spec.get("validation_errors"):
            reports.append({"object_id": object_id, "status": "skipped_invalid_vlm_spec", "errors": spec["validation_errors"]})
            continue
        materialized, materialized_specs = materialize_split(
            parent,
            spec,
            input_dir,
            spec_dir,
            args.padding_pixels,
            args.min_alpha_pixels,
        )
        children.extend(materialized)
        child_specs.extend(materialized_specs)
        reports.append({"object_id": object_id, "status": "split_materialized", "child_ids": [item["object_id"] for item in materialized]})
        print(f"materialized {object_id}: {len(materialized)} independent inputs", flush=True)
    output_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "VLM_instance_contract_to_disjoint_RGBA_TRELLIS_inputs",
        "source_input_manifest": str(args.input_manifest.resolve()),
        "source_vlm_spec_manifest": str(args.vlm_spec_manifest.resolve()),
        "prepared": children,
        "reports": reports,
    }
    output_manifest_path = input_dir / "input_selection_manifest.json"
    write_json(output_manifest_path, output_manifest)
    child_spec_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "VLM_split_materialization_child_asset_contracts",
        "source_vlm_spec_manifest": str(args.vlm_spec_manifest.resolve()),
        "results": child_specs,
    }
    child_spec_manifest_path = spec_dir / "vlm_asset_specs_manifest.json"
    write_json(child_spec_manifest_path, child_spec_manifest)
    print(f"materialized={len(children)} manifest={output_manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
