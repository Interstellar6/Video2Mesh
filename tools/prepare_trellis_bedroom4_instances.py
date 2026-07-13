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


# The image-to-3D backend consumes only an RGBA image.  These contracts are
# consumed by the VLM review stage before that image is allowed into TRELLIS.
# They deliberately describe a *single physical asset*, not a semantic class.
CATEGORY_INSTANCE_CONTRACTS: dict[str, dict[str, Any]] = {
    "window": {
        "asset_type": "architectural window unit",
        "target_scope": (
            "Exactly one independently framed window sash, pane, or fixed window unit. "
            "A multi-pane assembly must be split into one asset per independently framed unit."
        ),
        "critical_parts": ["outer frame", "sash", "glass pane", "handle or latch when visible"],
        "forbidden_merges": [
            "adjacent window pane or sash",
            "shared frame outside the selected unit",
            "wall, curtain, blind, exterior view, floor, or furniture",
        ],
        "merge_risk": "Adjacent panes often share a central mullion and can appear as one semantic window mask.",
    },
    "door": {
        "asset_type": "architectural door leaf",
        "target_scope": "Exactly one door leaf with its directly attached handle or hinge hardware when visible.",
        "critical_parts": ["door leaf", "frame boundary", "handle or hinge hardware when visible"],
        "forbidden_merges": ["adjacent door", "wall", "doorway opening outside the leaf", "nearby furniture"],
        "merge_risk": "Adjacent door leaves and wall boundaries can be merged by a category-level mask.",
    },
    "lamp": {
        "asset_type": "light fixture",
        "target_scope": "Exactly one physical light fixture, including its shade, stem, base, and visible cable when attached.",
        "critical_parts": ["shade", "bulb housing", "stem", "base"],
        "forbidden_merges": ["adjacent lamp", "nightstand", "wall", "bed", "background light reflection"],
        "merge_risk": "Small fixtures can be merged with their support surface or another nearby light source.",
    },
    "bed": {
        "asset_type": "bed furniture",
        "target_scope": "Exactly one bed assembly, including its mattress, bed frame, headboard, and pillows only when attached to that bed.",
        "critical_parts": ["mattress", "frame", "headboard", "legs", "pillows when visible"],
        "forbidden_merges": ["nightstand", "lamp", "wall", "floor", "adjacent bed"],
        "merge_risk": "Large furniture masks can absorb nearby support furniture and floor pixels.",
    },
    "nightstand": {
        "asset_type": "nightstand furniture",
        "target_scope": "Exactly one standalone nightstand, including its body, drawer front, top surface, and attached handle when visible.",
        "critical_parts": ["cabinet body", "top", "drawer or door front", "legs", "handle"],
        "forbidden_merges": ["bed", "lamp", "wall", "floor", "adjacent nightstand"],
        "merge_risk": "The object is often partially occluded by the bed and can merge with it in a broad crop.",
    },
    "plant": {
        "asset_type": "potted plant",
        "target_scope": "Exactly one potted plant, including the pot, soil, stems, and leaves belonging to that pot.",
        "critical_parts": ["pot", "stems", "leaves"],
        "forbidden_merges": ["adjacent plant", "planter stand", "wall", "furniture", "background foliage"],
        "merge_risk": "Thin leaves and nearby foliage may be disconnected or merge with the background.",
    },
}

DEFAULT_INSTANCE_CONTRACT: dict[str, Any] = {
    "asset_type": "single physical object",
    "target_scope": "Exactly one physical instance of the requested category.",
    "critical_parts": ["visible body", "directly attached components"],
    "forbidden_merges": ["adjacent same-category instance", "background structure", "nearby furniture"],
    "merge_risk": "A category-level segmentation mask can contain more than one physical instance.",
}


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


def disk_structure(radius: int) -> np.ndarray:
    if radius <= 0:
        return np.ones((1, 1), dtype=bool)
    coordinates = np.arange(-radius, radius + 1, dtype=np.int32)
    yy, xx = np.meshgrid(coordinates, coordinates, indexing="ij")
    return (xx * xx + yy * yy) <= radius * radius


def projected_support_seed(
    points: np.ndarray,
    candidate: Candidate,
    world_to_camera: np.ndarray,
    intrinsic: dict[str, float],
    foreground: np.ndarray,
    dilation_radius: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Project the selected 3D instance back into the selected image crop."""
    height, width = foreground.shape
    x0, y0, x1, y1 = candidate.bbox_xyxy
    u, v, in_front = project_points(points, world_to_camera, intrinsic)
    ui = np.rint(u).astype(np.int32)
    vi = np.rint(v).astype(np.int32)
    in_image = in_front & (ui >= 0) & (ui < width) & (vi >= 0) & (vi < height)
    in_crop = in_image & (ui >= x0) & (ui < x1) & (vi >= y0) & (vi < y1)
    inside_mask = np.zeros(len(points), dtype=bool)
    source_indices = np.flatnonzero(in_crop)
    if len(source_indices):
        inside_mask[source_indices] = foreground[vi[source_indices], ui[source_indices]]
    seed = np.zeros((y1 - y0, x1 - x0), dtype=bool)
    seed_indices = np.flatnonzero(inside_mask)
    if len(seed_indices):
        seed[vi[seed_indices] - y0, ui[seed_indices] - x0] = True
    envelope = ndimage.binary_dilation(seed, structure=disk_structure(dilation_radius)) if seed.any() else seed
    return seed, envelope, {
        "projected_points_in_image": int(in_image.sum()),
        "projected_points_in_crop": int(in_crop.sum()),
        "projected_points_inside_category_mask": int(inside_mask.sum()),
        "seed_pixels": int(seed.sum()),
        "seed_envelope_pixels": int(envelope.sum()),
        "seed_dilation_radius_px": int(dilation_radius),
    }


def mask_for_candidate(
    candidate: Candidate,
    points: np.ndarray,
    world_to_camera: np.ndarray,
    intrinsic: dict[str, float],
    probability_threshold: float,
    min_component_support: float,
    support_seed_radius: int,
) -> tuple[Image.Image, Image.Image, Image.Image, dict[str, Any]]:
    image = Image.open(candidate.image_path).convert("RGB")
    mask = np.asarray(Image.open(candidate.mask_path).convert("L"), dtype=np.uint8)
    if mask.shape != (image.height, image.width):
        mask = np.asarray(Image.fromarray(mask).resize(image.size, Image.Resampling.NEAREST), dtype=np.uint8)
    foreground = mask >= int(round(probability_threshold * 255.0))
    x0, y0, x1, y1 = candidate.bbox_xyxy
    crop_mask = foreground[y0:y1, x0:x1]
    seed, seed_envelope, seed_report = projected_support_seed(
        points,
        candidate,
        world_to_camera,
        intrinsic,
        foreground,
        support_seed_radius,
    )
    labels, label_count = ndimage.label(crop_mask)
    retained_labels: list[int] = []
    retained_by = "size_fallback"
    component_seed_pixels: dict[str, int] = {}
    if label_count:
        component_sizes = np.bincount(labels.ravel())
        nonzero_sizes = component_sizes[1:]
        if seed.any():
            seed_labels = labels[seed]
            seed_counts = np.bincount(seed_labels, minlength=len(component_sizes))
            component_seed_pixels = {
                str(index): int(count)
                for index, count in enumerate(seed_counts)
                if index and count
            }
            # A category mask may have several disconnected objects.  Retain
            # only components touched by the actual 3D instance projection.
            retained_labels = [
                int(index)
                for index, count in enumerate(seed_counts)
                if index and count and component_sizes[index] >= 8
            ]
            if retained_labels:
                retained_by = "projected_instance_seed"
        if not retained_labels and len(nonzero_sizes):
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
    seed_image = Image.fromarray((seed.astype(np.uint8) * 255), mode="L")
    return cropped_image, rgba, seed_image, {
        "foreground_pixels_before_component_filter": int(crop_mask.sum()),
        "foreground_pixels_after_component_filter": int(cleaned.sum()),
        "component_count": int(label_count),
        "retained_component_labels": retained_labels,
        "retained_by": retained_by,
        "component_seed_pixels": component_seed_pixels,
        "projected_instance_seed": seed_report,
    }


def instance_contract(category: str) -> dict[str, Any]:
    contract = CATEGORY_INSTANCE_CONTRACTS.get(category, DEFAULT_INSTANCE_CONTRACT)
    return {
        "asset_type": str(contract["asset_type"]),
        "target_scope": str(contract["target_scope"]),
        "critical_parts": list(contract["critical_parts"]),
        "forbidden_merges": list(contract["forbidden_merges"]),
        "merge_risk": str(contract["merge_risk"]),
    }


def build_vlm_request(
    object_id: str,
    name: Any,
    category: str,
    bbox_width: int,
    bbox_height: int,
    component_report: dict[str, Any],
) -> dict[str, Any]:
    """Create the grounded review contract used before image-to-3D generation."""
    contract = instance_contract(category)
    seed_report = component_report.get("projected_instance_seed", {})
    prompt = "\n".join(
        [
            "You are the instance-grounding reviewer for a video-to-3D asset pipeline.",
            "The supplied composite has three aligned panels: source RGB crop, candidate RGBA foreground, and sparse projected 3D support.",
            "The RGBA crop comes from a category-level SAM3 mask and may accidentally include neighboring physical instances.",
            f"Requested semantic category: {category}.",
            f"Requested asset id: {object_id}.",
            f"Required asset type: {contract['asset_type']}.",
            f"Target scope: {contract['target_scope']}",
            f"Visible parts to inspect: {', '.join(contract['critical_parts'])}.",
            f"Forbidden merges: {', '.join(contract['forbidden_merges'])}.",
            f"Known merge risk: {contract['merge_risk']}",
            "Use only visible evidence. Do not invent hidden geometry, unseen handles, or extra objects.",
            "Count separately framed or separately supported same-category entities. Shared contact, a central mullion, or touching masks does not make them one object.",
            "If the crop contains more than one candidate asset, return split_required even when the category mask is connected.",
            "The projected-support panel is evidence of the current 3D instance, not proof that its semantic mask is pure.",
            "Return JSON only. Use normalized bbox coordinates in [0, 1000] relative to the RGB crop.",
            "Required schema:",
            '{"decision":"accept_single_instance|split_required|reject","reason":"short evidence-based reason","observed_same_category_instance_count":1,"asset_units":[{"unit_id":"short_stable_id","normalized_bbox_xyxy":[0,0,1000,1000],"visible_parts":["..."],"appearance":"visible material/color/texture","geometry":"visible shape, depth cues, and orientation","occlusion":"what is occluded or truncated","confidence":0.0}],"shared_structure":["..."],"excluded_content":["..."],"generation_contract":{"one_asset_per_unit":true,"forbidden_merges":["..."],"needs_new_instance_masks":false}}',
        ]
    )
    return {
        "schema_version": 1,
        "kind": "video2mesh.instance_asset_vlm_request",
        "object_id": object_id,
        "name": name,
        "category": category,
        "crop_size": {"width": int(bbox_width), "height": int(bbox_height)},
        "input_contract": contract,
        "projection_evidence": seed_report,
        "prompt": prompt,
        "expected_response_schema": {
            "decision": ["accept_single_instance", "split_required", "reject"],
            "observed_same_category_instance_count": "positive integer",
            "asset_units": "one record per physically separate asset unit",
            "normalized_bbox_xyxy": "[x0, y0, x1, y1], each coordinate in [0, 1000]",
        },
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
    parser.add_argument(
        "--support-seed-radius",
        type=int,
        default=4,
        help="Dilation radius used only to audit projected 3D support in the selected crop.",
    )
    parser.add_argument("--objects", nargs="*", help="Optional instance ids to prepare, such as sam3_window_01.")
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
    vlm_request_dir = input_dir / "vlm_requests"
    vlm_request_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = {path.stem: path for path in args.frames_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg"}}
    wanted = set(args.objects or [])
    results: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    for ordinal, (object_id, record) in enumerate(sorted(objects.items())):
        if wanted and object_id not in wanted:
            continue
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
        selected_extrinsic = np.asarray(extrinsics[selected.frame_id], dtype=np.float32)
        selected_intrinsic = intrinsic_for_frame(camera_info, selected.frame_id)
        rgb, rgba, projected_support, component_report = mask_for_candidate(
            selected,
            points,
            selected_extrinsic,
            selected_intrinsic,
            args.min_mask_probability,
            args.min_component_support,
            args.support_seed_radius,
        )
        rgb_path = input_dir / f"{object_id}_rgb.png"
        rgba_path = input_dir / f"{object_id}_rgba.png"
        projected_support_path = input_dir / f"{object_id}_projected_support.png"
        rgb.save(rgb_path)
        rgba.save(rgba_path)
        projected_support.save(projected_support_path)
        alpha_pixels = int(np.asarray(rgba.getchannel("A"), dtype=np.uint8).astype(bool).sum())
        vlm_request = build_vlm_request(
            object_id,
            record.get("name"),
            category,
            selected.bbox_width,
            selected.bbox_height,
            component_report,
        )
        vlm_request_path = vlm_request_dir / f"{object_id}.json"
        write_json(vlm_request_path, vlm_request)
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
            "projected_support_path": str(projected_support_path),
            "vlm_request_path": str(vlm_request_path),
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
        "schema_version": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "instance_3d_projection_seeded_sam3_mask_preparation_with_pre_generation_vlm_contracts",
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
            "support_seed_radius": args.support_seed_radius,
            "objects": sorted(wanted),
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
