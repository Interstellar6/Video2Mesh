#!/usr/bin/env python3
"""Bridge GroundingDINO categories and real SAM3 masks into Video2Mesh."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


STRUCTURE_CATEGORIES = {"ceiling", "floor", "wall"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "unknown"


def prompt_objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        objects = value.get("objects") or value.get("prompts") or []
    else:
        objects = value
    return [item for item in objects if isinstance(item, dict)]


def make_scene_json(args: argparse.Namespace) -> None:
    prompts = read_json(args.prompts)
    objects = prompt_objects(prompts)
    category_counts = Counter(
        str(item.get("category") or item.get("name") or "").strip().lower()
        for item in objects
        if str(item.get("category") or item.get("name") or "").strip()
    )
    categories = sorted(category_counts)
    if not categories:
        raise ValueError(f"No GroundingDINO categories found in {args.prompts}")

    frames = sorted(
        path for path in args.frames_dir.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    if not frames:
        raise FileNotFoundError(f"No frames found under {args.frames_dir}")
    scene_json = {
        "scene": args.scene,
        "categories": categories,
        "per_image": {path.name: categories for path in frames},
        "category_discovery": {
            "provider": "GroundingDINO",
            "source": str(args.prompts.resolve()),
            "source_object_count": len(objects),
            "source_candidate_count": prompts.get("candidate_count") if isinstance(prompts, dict) else None,
            "instances_per_category": dict(sorted(category_counts.items())),
            "notes": "Only categories with a retained GroundingDINO object prompt are sent to SAM3.",
        },
    }
    write_json(args.output, scene_json)
    print(json.dumps(scene_json, indent=2, ensure_ascii=False))


def decode_mask(item: dict[str, Any]) -> np.ndarray:
    rle = item.get("mask_rle")
    if rle:
        try:
            from pycocotools import mask as mask_utils
        except ImportError as exc:
            raise RuntimeError("pycocotools is required to decode SAM3 RLE masks") from exc
        encoded = dict(rle)
        counts = encoded.get("counts")
        if isinstance(counts, str):
            encoded["counts"] = counts.encode("ascii")
        mask = mask_utils.decode(encoded)
        if mask.ndim == 3:
            mask = np.any(mask, axis=2)
        return np.asarray(mask, dtype=bool)

    mask_path = Path(str(item.get("mask_path") or ""))
    if mask_path.is_file():
        return np.asarray(Image.open(mask_path).convert("L")) > 0
    raise FileNotFoundError(f"SAM3 item has neither mask_rle nor a readable mask_path: {item}")


def merge_mask_indexes(args: argparse.Namespace) -> None:
    all_items: list[dict[str, Any]] = []
    missing_images: list[str] = []
    source_indexes: list[str] = []
    scene = args.scene
    image_root: str | None = None
    for path in args.inputs:
        index = read_json(path)
        current_scene = str(index.get("scene") or scene)
        if current_scene != scene:
            raise ValueError(f"Scene mismatch in {path}: {current_scene} != {scene}")
        all_items.extend(item for item in index.get("items", []) if isinstance(item, dict))
        missing_images.extend(str(value) for value in index.get("missing_images", []))
        image_root = image_root or index.get("image_root")
        source_indexes.append(str(path.resolve()))

    merged = {
        "scene": scene,
        "image_root": image_root,
        "items": sorted(
            all_items,
            key=lambda item: (
                str(item.get("image", "")),
                str(item.get("label", "")),
                -float(item.get("score") or 0.0),
            ),
        ),
        "missing_images": sorted(set(missing_images)),
        "source_indexes": source_indexes,
        "merge_method": "concatenate_disjoint_frame_shards",
    }
    write_json(args.output, merged)
    print(f"Merged {len(all_items)} SAM3 masks from {len(args.inputs)} shard(s): {args.output}")


def shard_scene_json(args: argparse.Namespace) -> None:
    scene_json = read_json(args.input)
    per_image = scene_json.get("per_image") or {}
    if not per_image:
        raise ValueError(f"No per_image records in {args.input}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame_items = sorted(per_image.items())
    outputs: list[str] = []
    for shard_index in range(args.shards):
        shard = dict(scene_json)
        shard["per_image"] = dict(frame_items[shard_index :: args.shards])
        shard["shard"] = {
            "index": shard_index,
            "count": args.shards,
            "source": str(args.input.resolve()),
            "frame_count": len(shard["per_image"]),
        }
        output = args.output_dir / f"shard_{shard_index:02d}.json"
        write_json(output, shard)
        outputs.append(str(output))
    print(json.dumps({"shards": outputs, "frame_count": len(frame_items)}, indent=2, ensure_ascii=False))


def convert_masks(args: argparse.Namespace) -> None:
    index = read_json(args.mask_index)
    items = [item for item in index.get("items", []) if isinstance(item, dict)]
    if not items:
        raise ValueError(f"No SAM3 mask items in {args.mask_index}")

    project_root = args.project_root.resolve()
    output_root = args.output_root.resolve() if args.output_root else project_root / "masks" / "2d"
    if output_root.exists():
        if not args.overwrite:
            raise FileExistsError(f"Output exists; pass --overwrite: {output_root}")
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        label = str(item.get("label") or "").strip().lower()
        image_name = str(item.get("image") or "").strip()
        if label and image_name:
            grouped[(label, Path(image_name).stem)].append(item)

    per_object: dict[str, dict[str, Any]] = {}
    label_summary: dict[str, dict[str, Any]] = {}
    total_source_instances = 0
    total_merged_masks = 0
    for label in sorted({key[0] for key in grouped}):
        object_id = f"sam3_class_{slugify(label)}"
        frame_groups = sorted((frame_id, values) for (item_label, frame_id), values in grouped.items() if item_label == label)
        scores: list[float] = []
        frame_records: dict[str, Any] = {}
        source_instances = 0
        for frame_id, frame_items in frame_groups:
            weighted: np.ndarray | None = None
            item_scores: list[float] = []
            for item in frame_items:
                mask = decode_mask(item)
                score = max(0.0, min(1.0, float(item.get("score") or 0.0)))
                value = np.uint8(round(score * 255.0))
                candidate = np.where(mask, value, np.uint8(0))
                weighted = candidate if weighted is None else np.maximum(weighted, candidate)
                item_scores.append(score)
            if weighted is None or not np.any(weighted):
                continue
            output_path = output_root / object_id / f"{frame_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(weighted, mode="L").save(output_path)
            frame_records[frame_id] = {
                "mask": str(output_path),
                "source_instance_count": len(frame_items),
                "source_scores": item_scores,
                "max_score": max(item_scores),
                "nonzero_pixels": int(np.count_nonzero(weighted)),
            }
            scores.extend(item_scores)
            source_instances += len(frame_items)
            total_merged_masks += 1

        role = "background_structure" if label in STRUCTURE_CATEGORIES else "foreground_object"
        per_object[object_id] = {
            "object_id": object_id,
            "label": label,
            "frames_written": len(frame_records),
            "source_instance_masks": source_instances,
            "mean_score": float(np.mean(scores)) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "asset_role": role,
            "frames": frame_records,
        }
        label_summary[label] = {
            "object_id": object_id,
            "frames_written": len(frame_records),
            "source_instance_masks": source_instances,
            "mean_score": float(np.mean(scores)) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
        }
        total_source_instances += source_instances

    labels = {
        object_id: {
            "object_id": object_id,
            "name": record["label"],
            "category": record["label"],
            "description": f"Real SAM3 class-level probability masks for {record['label']}.",
            "confidence": record["mean_score"],
            "asset_role": record["asset_role"],
            "source": "sam3_text_prompt_probability_mask_adapter",
        }
        for object_id, record in per_object.items()
    }
    labels_path = project_root / "masks" / "object_labels.json"
    write_json(labels_path, labels)
    tracking_manifest = {
        "schema_version": 1,
        "provider": "SAM3",
        "tracking_mode": "class_probability_merge_without_temporal_instance_ids",
        "mask_root": str(output_root),
        "source_mask_index": str(args.mask_index.resolve()),
        "objects": per_object,
        "counts": {
            "classes": len(per_object),
            "source_instance_masks": total_source_instances,
            "merged_class_frame_masks": total_merged_masks,
        },
        "labels": label_summary,
        "notes": [
            "Same-label SAM3 instances in one frame are merged by pixel-wise maximum.",
            "Each foreground pixel stores round(SAM3 score * 255), preserving score-derived probability.",
            "SAM3 image inference has no stable cross-frame instance id; 3D connectivity splits class masks later.",
        ],
    }
    write_json(output_root / "tracking_manifest.json", tracking_manifest)

    manifest_path = project_root / "manifest.json"
    manifest = read_json(manifest_path)
    manifest.setdefault("masks", {})["mask_2d_dir"] = str(output_root.relative_to(project_root))
    manifest.setdefault("artifacts", {})["object_masks_2d"] = str(output_root)
    manifest["artifacts"]["mask_tracking_manifest"] = str(output_root / "tracking_manifest.json")
    manifest["artifacts"]["object_labels"] = str(labels_path)
    manifest.setdefault("external_stages", {})["segmentation_2d_tracking"] = {
        "status": "generated_real_sam3_class_probability_masks",
        "provider": "SAM3",
        "source_mask_index": str(args.mask_index.resolve()),
        "class_count": len(per_object),
        "source_instance_mask_count": total_source_instances,
        "merged_mask_count": total_merged_masks,
    }
    write_json(manifest_path, manifest)
    print(json.dumps(tracking_manifest["counts"], indent=2, ensure_ascii=False))
    print(f"Video2Mesh probability masks: {output_root}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    sub = subparsers.add_parser("make-scene-json")
    sub.add_argument("--prompts", type=Path, required=True)
    sub.add_argument("--frames-dir", type=Path, required=True)
    sub.add_argument("--output", type=Path, required=True)
    sub.add_argument("--scene", default="bedroom_4")
    sub.set_defaults(func=make_scene_json)

    sub = subparsers.add_parser("merge-indexes")
    sub.add_argument("--inputs", type=Path, nargs="+", required=True)
    sub.add_argument("--output", type=Path, required=True)
    sub.add_argument("--scene", default="bedroom_4")
    sub.set_defaults(func=merge_mask_indexes)

    sub = subparsers.add_parser("shard-scene-json")
    sub.add_argument("--input", type=Path, required=True)
    sub.add_argument("--output-dir", type=Path, required=True)
    sub.add_argument("--shards", type=int, required=True)
    sub.set_defaults(func=shard_scene_json)

    sub = subparsers.add_parser("convert-masks")
    sub.add_argument("--mask-index", type=Path, required=True)
    sub.add_argument("--project-root", type=Path, required=True)
    sub.add_argument("--output-root", type=Path)
    sub.add_argument("--overwrite", action="store_true")
    sub.set_defaults(func=convert_masks)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
