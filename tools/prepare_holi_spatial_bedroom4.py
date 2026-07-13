#!/usr/bin/env python3
"""Prepare a small Holi-Spatial-style bedroom_4 run package from Video2Mesh outputs."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def resolve_source_path(source_root: Path, manifest: dict[str, Any], key: str, fallback: Path) -> Path:
    raw = manifest.get("artifacts", {}).get(key)
    candidates: list[Path] = []
    if raw:
        path = Path(str(raw))
        candidates.append(path if path.is_absolute() else source_root / path)
        if path.is_absolute() and "video2mesh_runs" in path.parts:
            try:
                index = path.parts.index("video2mesh_runs")
                rel = Path(*path.parts[index + 2 :])
                candidates.append(source_root / rel)
            except Exception:
                pass
    candidates.append(fallback)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def resolve_images_dir(source_root: Path, manifest: dict[str, Any]) -> Path:
    fallback_candidates = [
        source_root / "external" / "graphdeco_3dgs" / "colmap_source" / "images",
        source_root / "scene" / "frames",
        source_root / "external" / "colmap" / "dense" / "images",
    ]
    raw = manifest.get("artifacts", {}).get("colmap_text_images_dir") or manifest.get("artifacts", {}).get("frames")
    if raw:
        path = Path(str(raw))
        candidates = [path if path.is_absolute() else source_root / path]
        if path.is_absolute() and "video2mesh_runs" in path.parts:
            try:
                index = path.parts.index("video2mesh_runs")
                candidates.append(source_root / Path(*path.parts[index + 2 :]))
            except Exception:
                pass
        fallback_candidates = candidates + fallback_candidates
    for candidate in fallback_candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"No source images directory found under {source_root}")


def copy_optional_file(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_tree_files(src: Path, dst: Path, suffixes: set[str] | None = None) -> list[Path]:
    copied: list[Path] = []
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        if suffixes and path.suffix.lower() not in suffixes:
            continue
        rel = path.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out, follow_symlinks=True)
        copied.append(out)
    return copied


def aabb_corners(mins: list[float], maxs: list[float]) -> list[dict[str, float]]:
    corners = []
    for sx in (mins[0], maxs[0]):
        for sy in (mins[1], maxs[1]):
            for sz in (mins[2], maxs[2]):
                corners.append({"x": float(sx), "y": float(sy), "z": float(sz)})
    return corners


def transform_from_center(center: list[float]) -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, float(center[0])],
        [0.0, 1.0, 0.0, float(center[1])],
        [0.0, 0.0, 1.0, float(center[2])],
        [0.0, 0.0, 0.0, 1.0],
    ]


def normalize_score(value: Any, default: float = 0.95) -> float:
    try:
        score = float(value)
    except Exception:
        return default
    if math.isnan(score):
        return default
    if score > 1.0:
        return default
    return max(0.0, min(1.0, score))


def mask_bbox_and_rle(mask_path: Path) -> tuple[list[float] | None, dict[str, Any] | None, int]:
    try:
        image = Image.open(mask_path).convert("L")
    except Exception:
        return None, None, 0
    arr = np.asarray(image) > 0
    ys, xs = np.where(arr)
    if xs.size == 0:
        rle = encode_binary_mask(arr)
        return None, rle, 0
    bbox = [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
    return bbox, encode_binary_mask(arr), int(xs.size)


def encode_binary_mask(mask: np.ndarray) -> dict[str, Any]:
    """COCO uncompressed RLE compatible with pycocotools.decode."""
    flat = np.asarray(mask, dtype=np.uint8, order="F").reshape(-1, order="F")
    if flat.size == 0:
        counts: list[int] = []
    else:
        changes = np.flatnonzero(flat[1:] != flat[:-1]) + 1
        starts = np.concatenate(([0], changes))
        ends = np.concatenate((changes, [flat.size]))
        counts = (ends - starts).astype(np.int64).tolist()
        if int(flat[0]) == 1:
            counts.insert(0, 0)
    return {"size": [int(mask.shape[0]), int(mask.shape[1])], "counts": counts}


def infer_transforms_from_graphdeco(cameras_path: Path, images_dir: Path) -> dict[str, Any]:
    cameras = read_json(cameras_path)
    frames: list[dict[str, Any]] = []
    if not cameras:
        raise ValueError(f"No cameras found: {cameras_path}")
    first = cameras[0]
    width = int(first["width"])
    height = int(first["height"])
    fx = float(first["fx"])
    fy = float(first["fy"])
    cx = width / 2.0
    cy = height / 2.0
    for cam in sorted(cameras, key=lambda item: item["img_name"]):
        img_name = cam["img_name"]
        rotation = np.asarray(cam["rotation"], dtype=np.float64)
        position = np.asarray(cam["position"], dtype=np.float64)
        c2w = np.eye(4, dtype=np.float64)
        c2w[:3, :3] = rotation
        c2w[:3, 3] = position
        with Image.open(images_dir / img_name) as img:
            w, h = img.size
        frames.append(
            {
                "file_path": img_name,
                "transform_matrix": c2w.tolist(),
                "w": int(w),
                "h": int(h),
            }
        )
    return {
        "camera_model": "PINHOLE",
        "fl_x": fx,
        "fl_y": fy,
        "cx": cx,
        "cy": cy,
        "w": width,
        "h": height,
        "frames": frames,
        "test_frames": [],
        "source_note": "Converted from Video2Mesh GraphDECO cameras.json; matrices are kept in the existing scene frame for a Holi-Spatial smoke run.",
    }


def scene_objects_json(scene: str, frames: list[dict[str, Any]], categories: list[str]) -> dict[str, Any]:
    per_image = {Path(frame["file_path"]).name: sorted(categories) for frame in frames}
    return {"scene": scene, "categories": sorted(categories), "per_image": per_image}


def build_mask_index(
    source_root: Path,
    scene: str,
    class_json: dict[str, Any],
    output_root: Path,
    max_masks_per_object: int,
) -> tuple[dict[str, Any], int]:
    labels = read_json(source_root / "masks" / "object_labels.json")
    object_ids = sorted(labels)
    items: list[dict[str, Any]] = []
    for object_id in object_ids:
        label = labels[object_id].get("category") or labels[object_id].get("name") or object_id
        src_dir = source_root / "masks" / "2d" / object_id
        if not src_dir.exists():
            continue
        mask_paths = sorted(src_dir.glob("*.png"))
        if max_masks_per_object > 0:
            mask_paths = mask_paths[:max_masks_per_object]
        for src_mask in mask_paths:
            image_name = f"{src_mask.stem}.png"
            dst_mask = output_root / scene / src_mask.stem / f"{object_id}.png"
            dst_mask.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_mask, dst_mask)
            bbox, rle, area = mask_bbox_and_rle(src_mask)
            score = normalize_score(labels[object_id].get("confidence"), 0.95)
            item = {
                "image": image_name,
                "label": str(label).lower(),
                "object_id": object_id,
                "mask_path": str(dst_mask.resolve()),
                "bbox": bbox,
                "score": score,
                "mask_area": area,
            }
            if rle is not None:
                item["mask_rle"] = rle
            items.append(item)
    index = {
        "scene": scene,
        "image_root": str((output_root.parent / "scannetppv2" / "data" / scene / "dslr" / "resized_undistorted_images").resolve()),
        "mask_root": str((output_root / scene).resolve()),
        "items": items,
        "missing_images": [],
        "source": "Video2Mesh masks/2d converted to Holi-Spatial sam3.py-compatible mask_index.json",
        "class_json_categories": class_json.get("categories", []),
    }
    write_json(output_root / scene / "mask_index.json", index)
    return index, len(items)


def build_bbox_json(source_root: Path, scene: str, out_dir: Path, mask_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    object_masks = read_json(source_root / "masks" / "3d" / "object_masks.json")
    labels = read_json(source_root / "masks" / "object_labels.json")
    object_images = read_json(source_root / "simulator_assets" / "object_images.json")
    objects = object_masks.get("objects", {})
    records: list[dict[str, Any]] = []
    skipped: dict[str, str] = {}
    counter = 1
    for object_id, obj in sorted(objects.items()):
        bbox = obj.get("bbox_3d") or {}
        mins = bbox.get("min")
        maxs = bbox.get("max")
        center = bbox.get("center")
        size = bbox.get("size")
        if not (mins and maxs and center and size):
            skipped[object_id] = "missing_bbox_3d"
            continue
        if min(float(v) for v in size) <= 0:
            skipped[object_id] = "non_positive_extent"
            continue
        label_info = labels.get(object_id, {})
        label = str(label_info.get("category") or obj.get("category") or obj.get("name") or object_id).lower()
        selected = object_images.get(object_id) or {}
        frame_id = str(selected.get("frame_id") or "000000")
        source_mask_path = source_root / "masks" / "2d" / object_id / f"{frame_id}.png"
        package_mask_path = mask_root / scene / frame_id / f"{object_id}.png"
        if not source_mask_path.exists():
            candidates = sorted((source_root / "masks" / "2d" / object_id).glob("*.png"))
            source_mask_path = candidates[0] if candidates else source_mask_path
            frame_id = source_mask_path.stem if source_mask_path.exists() else frame_id
            package_mask_path = mask_root / scene / frame_id / f"{object_id}.png"
        if not package_mask_path.exists():
            candidates = sorted((mask_root / scene).glob(f"*/{object_id}.png"))
            package_mask_path = candidates[0] if candidates else package_mask_path
        rle = None
        images = []
        if source_mask_path.exists():
            _bbox2d, rle, _area = mask_bbox_and_rle(source_mask_path)
        if package_mask_path.exists():
            images = [str(package_mask_path)]
        record = {
            "ins_id": str(counter),
            "source_object_id": object_id,
            "label": label,
            "bounding_box": aabb_corners(mins, maxs),
            "obb_transform": transform_from_center(center),
            "obb_extents": [float(v) for v in size],
            "images": images,
            "highest_confidence_mask": str(package_mask_path) if package_mask_path.exists() else "",
            "mask_encodings": [rle] if rle is not None else [],
            "description": label,
            "source": "Video2Mesh fused 3D object mask bbox converted to Holi-Spatial bbox schema",
            "point_count": obj.get("point_count"),
        }
        records.append(record)
        counter += 1

    if records:
        mins = np.min(
            np.asarray([[p["x"], p["y"], p["z"]] for rec in records for p in rec["bounding_box"]], dtype=np.float64),
            axis=0,
        )
        maxs = np.max(
            np.asarray([[p["x"], p["y"], p["z"]] for rec in records for p in rec["bounding_box"]], dtype=np.float64),
            axis=0,
        )
        span = maxs - mins
        floor_thickness = max(0.02, float(span[1]) * 0.01)
        floor_min = [float(mins[0]), float(mins[1] - floor_thickness), float(mins[2])]
        floor_max = [float(maxs[0]), float(mins[1]), float(maxs[2])]
        floor_center = [float((floor_min[i] + floor_max[i]) * 0.5) for i in range(3)]
        floor_size = [float(floor_max[i] - floor_min[i]) for i in range(3)]
        records.insert(
            0,
            {
                "ins_id": "0",
                "source_object_id": "proxy_floor_from_scene_extent",
                "label": "floor",
                "bounding_box": aabb_corners(floor_min, floor_max),
                "obb_transform": transform_from_center(floor_center),
                "obb_extents": floor_size,
                "images": [],
                "highest_confidence_mask": "",
                "mask_encodings": [],
                "description": "proxy floor generated from Video2Mesh scene extent for Holi-Spatial AABB postprocess",
                "source": "proxy_floor_from_scene_extent",
            },
        )
    write_json(out_dir / f"{scene}.json", records)
    return records, skipped


def create_covisibility(scene_root: Path, frame_count: int, out_root: Path, scene: str) -> Path:
    frames = read_json(scene_root / "dslr" / "nerfstudio" / "transforms_undistorted.json")["frames"]
    positions = np.asarray([frame["transform_matrix"][i][3] for frame in frames for i in range(3)], dtype=np.float64).reshape(-1, 3)
    if len(positions) != frame_count:
        covis = np.ones((frame_count, frame_count), dtype=np.float32)
    else:
        d = np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=-1)
        scale = float(np.median(d[d > 0])) if np.any(d > 0) else 1.0
        covis = np.exp(-d / max(scale, 1e-6)).astype(np.float32)
        covis[covis < 0.05] = 0.05
        np.fill_diagonal(covis, 1.0)
    cov_dir = out_root / scene / "covisibility" / "v0"
    cov_dir.mkdir(parents=True, exist_ok=True)
    cov_path = cov_dir / "covisibility.npy"
    np.save(cov_path, covis)
    return cov_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--scene", default="bedroom_4")
    parser.add_argument("--max-masks-per-object", type=int, default=50)
    args = parser.parse_args()

    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    scene = args.scene
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = read_optional_json(source_root / "manifest.json") or {"artifacts": {}}
    images_src = resolve_images_dir(source_root, manifest)
    cameras_path = resolve_source_path(
        source_root,
        manifest,
        "scene_3dgs_cameras",
        source_root / "scene" / "reconstruction" / "3dgs" / "cameras.json",
    )
    scene_root = output_root / "scannetppv2" / "data" / scene
    images_dst = scene_root / "dslr" / "resized_undistorted_images"
    copied_images = copy_tree_files(images_src, images_dst, {".png", ".jpg", ".jpeg"})
    transforms = infer_transforms_from_graphdeco(cameras_path, images_dst)
    write_json(scene_root / "dslr" / "nerfstudio" / "transforms_undistorted.json", transforms)

    labels = read_json(source_root / "masks" / "object_labels.json")
    categories = sorted({str(v.get("category") or v.get("name") or k).lower() for k, v in labels.items()})
    categories = sorted(set(categories) | {"wall", "floor", "ceiling"})
    class_json = scene_objects_json(scene, transforms["frames"], categories)
    class_dir = output_root / "Qwen3VL-32B-Scannetppv2"
    write_json(class_dir / f"{scene}.json", class_json)

    mask_index, mask_count = build_mask_index(source_root, scene, class_json, output_root / "sam3_masks_scannetppv2_new", args.max_masks_per_object)

    pgsr_dir = output_root / "pgsr_scannetppv2_all" / scene
    ply_dst = pgsr_dir / "point_cloud" / "iteration_30000" / "point_cloud.ply"
    scene_3dgs_ply = resolve_source_path(
        source_root,
        manifest,
        "scene_3dgs_ply",
        source_root / "scene" / "reconstruction" / "3dgs" / "point_cloud" / "iteration_30000" / "point_cloud.ply",
    )
    ply_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scene_3dgs_ply, ply_dst)
    mesh_dst = pgsr_dir / "mesh" / "tsdf_fusion_post.ply"
    scene_mesh_ply = resolve_source_path(
        source_root,
        manifest,
        "scene_mesh_ply",
        source_root / "simulator_assets" / "scene_meshes" / "colmap_delaunay_dense" / "mesh.ply",
    )
    mesh_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(scene_mesh_ply, mesh_dst)
    depth_da3_dir = source_root / "depth_da3"
    copied_depths = 0
    if depth_da3_dir.exists():
        copied_depths = len(copy_tree_files(depth_da3_dir, output_root / "depth_da3" / scene, {".npy"}))
    pointcloud_da3_copied = copy_optional_file(source_root / "pointcloud_da3.ply", output_root / "pointcloud_da3" / f"{scene}.ply")

    mask_root = output_root / "sam3_masks_scannetppv2_new"
    bbox_records, skipped = build_bbox_json(source_root, scene, output_root / "output_scannetppv2_new", mask_root)
    cov_path = create_covisibility(scene_root, len(transforms["frames"]), output_root / "scannetppv2_wai", scene)

    manifest = {
        "schema_version": 1,
        "scene": scene,
        "source_root": str(source_root),
        "output_root": str(output_root),
        "status": "prepared",
        "holi_spatial_layout": {
            "data_root": "scannetppv2/data",
            "scene_dir": f"scannetppv2/data/{scene}",
            "class_json_dir": "Qwen3VL-32B-Scannetppv2",
            "mask_root": "sam3_masks_scannetppv2_new",
            "scenes_dir": "pgsr_scannetppv2_all",
            "bbox_output_dir": "output_scannetppv2_new",
            "wai_root": "scannetppv2_wai",
        },
        "counts": {
            "images": len(copied_images),
            "frames_in_transforms": len(transforms["frames"]),
            "categories": len(categories),
            "mask_index_items": mask_count,
            "bbox_instances_including_proxy_floor": len(bbox_records),
            "bbox_skipped": len(skipped),
        },
        "stage_mapping": {
            "DA3_depth": (
                f"copied {copied_depths} DA3 depth npy file(s)"
                if copied_depths
                else "not rerun; no DA3 depth npy present in source package"
            ),
            "DA3_pointcloud": "copied pointcloud_da3.ply" if pointcloud_da3_copied else "not present",
            "PGSR_3DGS": "reused Video2Mesh GraphDECO 3DGS point_cloud.ply",
            "mesh": "reused Video2Mesh COLMAP Delaunay scene mesh as tsdf_fusion_post.ply",
            "classic_vllm": "adapted from Video2Mesh GroundingDINO object_labels across all frames",
            "SAM3": "adapted from Video2Mesh masks/2d into sam3.py-compatible mask_index.json",
            "3d_bbox": "adapted from Video2Mesh masks/3d/object_masks.json bbox_3d into Holi-Spatial bbox schema",
            "floor": "proxy floor inserted from scene extent so official AABB postprocess can run",
            "covisibility": f"proxy covisibility generated from camera positions at {cov_path.relative_to(output_root)}",
        },
        "skipped_objects": skipped,
        "next_official_commands": [
            "python postprocess_3d_bbox_aabb.py --input_dir output_scannetppv2_new --output_dir output_scannetppv2_new_aabb --floor_label floor --axis_method largest_face --extent_mode keep",
            "python qa_generation/generate_two_view_qa.py --scene-id bedroom_4 --data-root scannetppv2/data --wai-root scannetppv2_wai --bbox-json-folder output_scannetppv2_new_aabb --output output_QA_new_lang --num 2 --covis-threshold 0.05 --marker-types language_description",
        ],
        "notes": [
            "This package is a smoke run for bedroom_4 using existing Video2Mesh artifacts, not a full official Holi-Spatial DA3/SAM3/PGSR rerun.",
            "Use full official scripts only after enough disk is available for DA3/SAM3/checkpoints and dependency installation.",
        ],
        "resolved_inputs": {
            "images_src": str(images_src),
            "cameras_path": str(cameras_path),
            "scene_3dgs_ply": str(scene_3dgs_ply),
            "scene_mesh_ply": str(scene_mesh_ply),
        },
    }
    write_json(output_root / "run_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
