#!/usr/bin/env python3
"""Split class-level SAM3/DA3 fusion into stable 3D instances and bboxes."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


STRUCTURE_CATEGORIES = {"ceiling", "floor", "wall"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def resolve_path(raw: str | Path, project_root: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else project_root / path


def read_points(path: Path) -> np.ndarray:
    try:
        import open3d as o3d
    except ImportError as exc:
        raise RuntimeError("open3d is required for 3D instance post-processing") from exc
    cloud = o3d.io.read_point_cloud(str(path))
    points = np.asarray(cloud.points)
    if points.ndim != 2 or points.shape[1] != 3 or not len(points):
        raise ValueError(f"No XYZ points in {path}")
    return points


def bbox(points: np.ndarray) -> dict[str, Any]:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    return {
        "min": mins.tolist(),
        "max": maxs.tolist(),
        "center": ((mins + maxs) * 0.5).tolist(),
        "size": (maxs - mins).tolist(),
    }


def robust_bbox(points: np.ndarray, quantile: float) -> dict[str, Any]:
    if quantile <= 0.0 or len(points) < 32:
        return bbox(points)
    mins = np.quantile(points, quantile, axis=0)
    maxs = np.quantile(points, 1.0 - quantile, axis=0)
    if np.any(maxs <= mins):
        return bbox(points)
    return {
        "min": mins.tolist(),
        "max": maxs.tolist(),
        "center": ((mins + maxs) * 0.5).tolist(),
        "size": (maxs - mins).tolist(),
    }


def robust_pca_obb(points: np.ndarray, quantile: float) -> dict[str, Any] | None:
    if len(points) < 8:
        return None
    centroid = points.mean(axis=0)
    centered = points - centroid
    covariance = np.cov(centered, rowvar=False)
    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    rotation = vectors[:, order]
    if np.linalg.det(rotation) < 0:
        rotation[:, -1] *= -1.0
    local = centered @ rotation
    low = np.quantile(local, quantile, axis=0) if quantile > 0 else local.min(axis=0)
    high = np.quantile(local, 1.0 - quantile, axis=0) if quantile > 0 else local.max(axis=0)
    if np.any(high <= low):
        return None
    local_center = (low + high) * 0.5
    world_center = centroid + local_center @ rotation.T
    corners_local = np.asarray(
        [[x, y, z] for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])],
        dtype=np.float64,
    )
    corners_world = centroid + corners_local @ rotation.T
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation
    transform[:3, 3] = world_center
    return {
        "center": world_center.tolist(),
        "extent": (high - low).tolist(),
        "rotation": rotation.tolist(),
        "transform": transform.tolist(),
        "corners": corners_world.tolist(),
        "method": "pca_quantile",
        "quantile": quantile,
    }


def cluster_voxels(
    points: np.ndarray,
    voxel_size: float,
    eps: float,
    min_voxel_neighbors: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    import open3d as o3d

    coordinates = np.floor(points / voxel_size).astype(np.int64)
    unique_coordinates, inverse, voxel_counts = np.unique(
        coordinates,
        axis=0,
        return_inverse=True,
        return_counts=True,
    )
    voxel_centers = (unique_coordinates.astype(np.float64) + 0.5) * voxel_size
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(voxel_centers)
    voxel_labels = np.asarray(
        cloud.cluster_dbscan(eps=eps, min_points=min_voxel_neighbors, print_progress=False),
        dtype=np.int32,
    )
    point_labels = voxel_labels[inverse]
    report = {
        "input_points": int(len(points)),
        "voxel_count": int(len(unique_coordinates)),
        "voxel_size": voxel_size,
        "dbscan_eps": eps,
        "dbscan_min_voxel_neighbors": min_voxel_neighbors,
        "noise_voxels": int(np.count_nonzero(voxel_labels < 0)),
        "noise_points": int(voxel_counts[voxel_labels < 0].sum()) if np.any(voxel_labels < 0) else 0,
        "raw_cluster_count": int(voxel_labels.max() + 1) if voxel_labels.size else 0,
    }
    return point_labels, report


def load_class_probabilities(mask_3d: dict[str, Any], project_root: Path, indices: np.ndarray) -> dict[str, np.ndarray]:
    probability_path = mask_3d.get("point_probabilities_npz")
    if not probability_path:
        ones = np.ones(len(indices), dtype=np.float32)
        return {
            "probability_mean": ones,
            "probability_max": ones,
            "probability_observations": np.ones(len(indices), dtype=np.uint32),
        }
    with np.load(resolve_path(probability_path, project_root)) as archive:
        archive_indices = np.asarray(archive["point_indices"], dtype=np.int64)
        if not np.array_equal(archive_indices, indices):
            raise ValueError(f"Probability/index mismatch: {probability_path}")
        return {
            "probability_mean": np.asarray(archive["probability_mean"], dtype=np.float32),
            "probability_max": np.asarray(archive["probability_max"], dtype=np.float32),
            "probability_observations": np.asarray(archive["probability_observations"], dtype=np.uint32),
        }


def dino_instance_caps(path: Path | None) -> dict[str, int]:
    if path is None:
        return {}
    value = read_json(path)
    objects = value.get("objects", []) if isinstance(value, dict) else []
    counts = Counter(
        str(item.get("category") or item.get("name") or "").strip().lower()
        for item in objects
        if isinstance(item, dict) and str(item.get("category") or item.get("name") or "").strip()
    )
    return dict(counts)


def aabb_corners(record: dict[str, Any]) -> list[dict[str, float]]:
    low = record["min"]
    high = record["max"]
    return [
        {"x": float(x), "y": float(y), "z": float(z)}
        for x in (low[0], high[0])
        for y in (low[1], high[1])
        for z in (low[2], high[2])
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--class-object-masks", type=Path)
    parser.add_argument("--groundingdino-prompts", type=Path)
    parser.add_argument("--output-mask-dir", default="masks/3d_instances")
    parser.add_argument("--output-objects-dir", default="objects_instances")
    parser.add_argument("--holi-bbox-output", type=Path)
    parser.add_argument("--voxel-size", type=float, default=0.04)
    parser.add_argument("--cluster-eps", type=float, default=0.12)
    parser.add_argument("--min-voxel-neighbors", type=int, default=3)
    parser.add_argument("--min-cluster-points", type=int, default=300)
    parser.add_argument("--min-cluster-fraction", type=float, default=0.003)
    parser.add_argument("--max-instances-per-category", type=int, default=6)
    parser.add_argument("--bbox-quantile", type=float, default=0.005)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    manifest_path = project_root / "manifest.json"
    manifest = read_json(manifest_path)
    class_summary_path = (
        args.class_object_masks.resolve()
        if args.class_object_masks
        else project_root / manifest["masks"]["mask_3d_dir"] / "object_masks.json"
    )
    class_summary = read_json(class_summary_path)
    point_cloud_path = resolve_path(class_summary["point_cloud"], project_root)
    points = read_points(point_cloud_path)
    if int(class_summary.get("num_points", len(points))) != len(points):
        raise ValueError("Class fusion point count does not match source point cloud")

    output_mask_dir = project_root / args.output_mask_dir
    output_objects_dir = project_root / args.output_objects_dir
    for output in (output_mask_dir, output_objects_dir):
        if output.exists():
            if not args.overwrite:
                raise FileExistsError(f"Output exists; pass --overwrite: {output}")
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=True)

    prompts_path = args.groundingdino_prompts
    caps = dino_instance_caps(prompts_path)
    instance_objects: dict[str, Any] = {}
    instance_labels: dict[str, Any] = {}
    class_reports: dict[str, Any] = {}
    holi_records: list[dict[str, Any]] = []
    next_instance_id = 1

    for class_object_id, class_object in sorted(class_summary.get("objects", {}).items()):
        category = str(class_object.get("category") or class_object.get("name") or "unknown").strip().lower()
        class_mask = class_object.get("mask_3d") or {}
        index_path = resolve_path(class_mask["point_indices_npy"], project_root)
        class_indices = np.asarray(np.load(index_path), dtype=np.int64)
        valid = (class_indices >= 0) & (class_indices < len(points))
        class_indices = class_indices[valid]
        probabilities = load_class_probabilities(class_mask, project_root, class_indices)
        class_points = points[class_indices]
        if not len(class_points):
            class_reports[class_object_id] = {"category": category, "status": "skipped_empty"}
            continue

        split_report: dict[str, Any]
        components: list[tuple[np.ndarray, dict[str, Any]]]
        if category in STRUCTURE_CATEGORIES:
            local_positions = np.arange(len(class_indices), dtype=np.int64)
            components = [(local_positions, {"cluster_label": None, "support": float(probabilities["probability_mean"].sum())})]
            split_report = {"method": "preserve_structure_class", "component_count": 1}
        else:
            point_labels, split_report = cluster_voxels(
                class_points,
                args.voxel_size,
                args.cluster_eps,
                args.min_voxel_neighbors,
            )
            minimum = max(args.min_cluster_points, int(math.ceil(len(class_indices) * args.min_cluster_fraction)))
            candidates: list[tuple[np.ndarray, dict[str, Any]]] = []
            for cluster_label in sorted(int(value) for value in np.unique(point_labels) if value >= 0):
                local_positions = np.flatnonzero(point_labels == cluster_label)
                support = float(probabilities["probability_mean"][local_positions].sum())
                candidates.append(
                    (
                        local_positions,
                        {
                            "cluster_label": cluster_label,
                            "point_count": int(len(local_positions)),
                            "support": support,
                            "passes_minimum": len(local_positions) >= minimum,
                        },
                    )
                )
            candidates.sort(key=lambda item: (item[1]["support"], item[1]["point_count"]), reverse=True)
            dino_cap = max(1, caps.get(category, 1))
            cap = min(args.max_instances_per_category, dino_cap)
            cap_override = None
            valid_candidates = [item for item in candidates if item[1]["passes_minimum"]]
            if dino_cap == 1 and len(valid_candidates) > 1:
                leading_support = float(valid_candidates[0][1]["support"])
                second_support = float(valid_candidates[1][1]["support"])
                if leading_support > 0 and second_support / leading_support >= 0.2:
                    cap = min(args.max_instances_per_category, 2)
                    cap_override = {
                        "reason": "second_cluster_has_strong_3d_support",
                        "second_to_first_support_ratio": second_support / leading_support,
                    }
            components = [item for item in candidates if item[1]["passes_minimum"]][:cap]
            if not components and candidates:
                components = candidates[:1]
                components[0][1]["fallback"] = "largest_cluster_below_minimum"
            split_report.update(
                {
                    "method": "voxel_dbscan_then_probability_support_rank",
                    "minimum_cluster_points": minimum,
                    "groundingdino_instance_cap": caps.get(category),
                    "applied_instance_cap": cap,
                    "instance_cap_override": cap_override,
                    "candidate_clusters": [record for _positions, record in candidates],
                    "kept_cluster_count": len(components),
                }
            )

        written_ids: list[str] = []
        for component_number, (local_positions, component_report) in enumerate(components, start=1):
            instance_id = (
                f"sam3_structure_{category.replace(' ', '_')}"
                if category in STRUCTURE_CATEGORIES
                else f"sam3_{category.replace(' ', '_')}_{component_number:02d}"
            )
            selected_indices = class_indices[local_positions]
            selected_points = points[selected_indices]
            selected_probabilities = {
                key: value[local_positions]
                for key, value in probabilities.items()
            }
            raw_box = bbox(selected_points)
            clean_box = robust_bbox(selected_points, args.bbox_quantile)
            obb = robust_pca_obb(selected_points, args.bbox_quantile)

            mask_dir = output_mask_dir / instance_id
            mask_dir.mkdir(parents=True, exist_ok=True)
            indices_output = mask_dir / "point_indices.npy"
            probabilities_output = mask_dir / "point_probabilities.npz"
            np.save(indices_output, selected_indices)
            np.savez_compressed(
                probabilities_output,
                point_indices=selected_indices,
                **selected_probabilities,
            )
            probability_summary = {
                "selected_points": int(len(selected_indices)),
                "mean_probability": float(selected_probabilities["probability_mean"].mean()),
                "max_probability": float(selected_probabilities["probability_max"].max()),
                "min_probability": float(selected_probabilities["probability_mean"].min()),
                "mean_probability_observations": float(selected_probabilities["probability_observations"].mean()),
            }
            write_json(mask_dir / "point_probabilities_summary.json", probability_summary)

            role = "background_structure" if category in STRUCTURE_CATEGORIES else "foreground_object"
            object_record = {
                "schema_version": 1,
                "object_id": instance_id,
                "name": category if role == "background_structure" else f"{category} {component_number}",
                "category": category,
                "asset_role": role,
                "description": f"Real SAM3 {category} mask lifted through corrected DA3 geometry and post-processed in 3D.",
                "point_count": int(len(selected_indices)),
                "bbox_3d": clean_box,
                "bbox_3d_raw": raw_box,
                "obb_3d": obb,
                "bbox_postprocess": {
                    "method": "axis_quantile_and_pca_quantile",
                    "quantile": args.bbox_quantile,
                },
                "mask_3d": {
                    "point_indices_npy": str(indices_output),
                    "point_probabilities_npz": str(probabilities_output),
                    "point_probabilities_summary_json": str(mask_dir / "point_probabilities_summary.json"),
                    "probability_summary": probability_summary,
                    "source_class_object_id": class_object_id,
                    "source_class_object_masks": str(class_summary_path),
                    "fusion_mode": class_mask.get("fusion_mode", "probability"),
                },
                "frame_scores": class_object.get("frame_scores", {}),
                "instance_split": component_report,
            }
            object_dir = output_objects_dir / instance_id
            write_json(object_dir / "object.json", object_record)
            write_json(object_dir / "frame_scores.json", object_record["frame_scores"])
            instance_objects[instance_id] = object_record
            instance_labels[instance_id] = {
                "object_id": instance_id,
                "name": object_record["name"],
                "category": category,
                "description": object_record["description"],
                "confidence": probability_summary["mean_probability"],
                "asset_role": role,
                "source": "sam3_da3_video2mesh_3d_instance_postprocess",
            }
            written_ids.append(instance_id)

            transform = obb["transform"] if obb else np.eye(4, dtype=np.float64).tolist()
            extents = obb["extent"] if obb else clean_box["size"]
            holi_records.append(
                {
                    "ins_id": str(next_instance_id),
                    "source_object_id": instance_id,
                    "label": category,
                    "bounding_box": aabb_corners(clean_box),
                    "obb_transform": transform,
                    "obb_extents": extents,
                    "images": [],
                    "highest_confidence_mask": "",
                    "mask_encodings": [],
                    "description": object_record["description"],
                    "point_count": int(len(selected_indices)),
                    "source": "Video2Mesh probability fusion + voxel DBSCAN + robust bbox postprocess",
                }
            )
            next_instance_id += 1

        class_reports[class_object_id] = {
            "category": category,
            "source_point_count": int(len(class_indices)),
            "instances": written_ids,
            "split": split_report,
        }

    summary = {
        "schema_version": 1,
        "point_cloud": str(point_cloud_path),
        "camera_info": class_summary.get("camera_info"),
        "mask_root": class_summary.get("mask_root"),
        "num_points": int(len(points)),
        "num_masks": class_summary.get("num_masks"),
        "objects": instance_objects,
        "source_class_object_masks": str(class_summary_path),
        "class_reports": class_reports,
        "postprocess": {
            "method": "class_probability_fusion_to_voxel_dbscan_instances",
            "voxel_size": args.voxel_size,
            "cluster_eps": args.cluster_eps,
            "min_voxel_neighbors": args.min_voxel_neighbors,
            "min_cluster_points": args.min_cluster_points,
            "min_cluster_fraction": args.min_cluster_fraction,
            "bbox_quantile": args.bbox_quantile,
            "structure_categories": sorted(STRUCTURE_CATEGORIES),
            "groundingdino_prompts": str(prompts_path.resolve()) if prompts_path else None,
        },
    }
    summary_path = output_mask_dir / "object_masks.json"
    write_json(summary_path, summary)

    labels_path = project_root / "masks" / "object_labels.json"
    class_labels_backup = project_root / "masks" / "object_labels_class_fusion.json"
    if labels_path.exists() and not class_labels_backup.exists():
        shutil.copy2(labels_path, class_labels_backup)
    write_json(labels_path, instance_labels)

    manifest["masks"]["mask_3d_dir"] = args.output_mask_dir
    manifest["objects_dir"] = args.output_objects_dir
    manifest.setdefault("artifacts", {})["class_object_masks_3d"] = str(class_summary_path)
    manifest["artifacts"]["object_masks_3d"] = str(summary_path)
    manifest["artifacts"]["object_labels"] = str(labels_path)
    manifest["artifacts"]["class_object_labels"] = str(class_labels_backup)
    manifest.setdefault("external_stages", {})["instance_3d_postprocess"] = {
        "status": "sam3_classes_split_into_3d_instances",
        "source": str(class_summary_path),
        "instance_count": len(instance_objects),
        "foreground_instance_count": sum(
            1 for value in instance_objects.values() if value["asset_role"] == "foreground_object"
        ),
        "structure_count": sum(
            1 for value in instance_objects.values() if value["asset_role"] == "background_structure"
        ),
        "method": summary["postprocess"],
    }
    write_json(manifest_path, manifest)

    if args.holi_bbox_output:
        write_json(args.holi_bbox_output, holi_records)
    print(
        json.dumps(
            {
                "instances": len(instance_objects),
                "foreground_instances": manifest["external_stages"]["instance_3d_postprocess"]["foreground_instance_count"],
                "structures": manifest["external_stages"]["instance_3d_postprocess"]["structure_count"],
                "object_masks": str(summary_path),
                "holi_bbox_output": str(args.holi_bbox_output) if args.holi_bbox_output else None,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
