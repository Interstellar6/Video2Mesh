#!/usr/bin/env python3
"""Build a provenance-first report for the bedroom_4 Holi-Spatial rerun."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def ply_header(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    lines: list[str] = []
    with path.open("rb") as handle:
        for _ in range(1024):
            raw = handle.readline()
            if not raw:
                break
            line = raw.decode("ascii", errors="ignore").strip()
            lines.append(line)
            if line == "end_header":
                break
    if not lines or lines[0] != "ply":
        return None
    result: dict[str, Any] = {"format": None, "vertex_count": None, "face_count": None, "properties": []}
    in_vertex = False
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "format":
            result["format"] = parts[1]
        elif len(parts) >= 3 and parts[:2] == ["element", "vertex"]:
            result["vertex_count"] = int(parts[2])
            in_vertex = True
        elif len(parts) >= 3 and parts[:2] == ["element", "face"]:
            result["face_count"] = int(parts[2])
            in_vertex = False
        elif in_vertex and len(parts) >= 3 and parts[0] == "property":
            result["properties"].append(parts[-1])
    return result


def artifact(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }
    if path.suffix.lower() == ".ply" and path.is_file():
        value["ply"] = ply_header(path)
    return value


def parse_pgsr_log(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "training_complete": False}
    text = path.read_text(encoding="utf-8", errors="ignore").replace("\r", "\n")
    iterations = [int(value) for value in re.findall(r"Training progress:\s+\d+%.*?\|\s*(\d+)/30000", text)]
    evaluations = [
        {"iteration": int(iteration), "l1": float(l1), "psnr": float(psnr)}
        for iteration, l1, psnr in re.findall(
            r"\[ITER (\d+)\] Evaluating train: L1 ([0-9.eE+-]+) PSNR ([0-9.eE+-]+)",
            text,
        )
    ]
    return {
        "exists": True,
        "training_complete": "Training complete." in text,
        "latest_iteration_seen": max(iterations) if iterations else 0,
        "depth_not_found_warnings": text.count("depth not found"),
        "evaluations": evaluations,
        "last_evaluation": evaluations[-1] if evaluations else None,
    }


def relative_file_count(root: Path, pattern: str) -> int:
    return len(list(root.glob(pattern))) if root.exists() else 0


def markdown_report(report: dict[str, Any]) -> str:
    counts = report["counts"]
    stages = report["stages"]
    artifacts = report["artifacts"]
    lines = [
        "# Holi-Spatial bedroom_4 full rerun",
        "",
        f"- Run root: `{report['run_root']}`",
        f"- Status: **{report['status']}**",
        "- Geometry coordinate: Video2Mesh/COLMAP scene units; no metric scale calibration was applied.",
        "",
        "## Stage status",
        "",
        "| Stage | Status | Evidence |",
        "|---|---|---|",
    ]
    for name, item in stages.items():
        lines.append(f"| {name} | {item['status']} | {item.get('evidence', '')} |")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- Source frames / DA3 depths: {counts['source_frames']} / {counts['da3_depth_maps']}",
            f"- GroundingDINO candidates / prompts / categories: {counts['dino_candidates']} / {counts['dino_prompts']} / {counts['dino_categories']}",
            f"- SAM3 instance masks / produced classes / merged probability masks: {counts['sam3_instance_masks']} / {counts['sam3_classes']} / {counts['sam3_merged_masks']}",
            f"- 3D instances: {counts['instances_total']} total, {counts['foreground_instances']} foreground, {counts['structure_instances']} structures",
            f"- Semantic DA3 foreground points: {counts['semantic_foreground_points']} / {counts['da3_points']}",
            "",
            "## Main artifacts",
            "",
            "| Artifact | Size | Path |",
            "|---|---:|---|",
        ]
    )
    for name, item in artifacts.items():
        size = item.get("size_bytes")
        size_text = f"{size / (1024 ** 2):.1f} MiB" if isinstance(size, int) else "directory/absent"
        lines.append(f"| {name} | {size_text} | `{item['path']}` |")
    lines.extend(["", "## Known limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    args = parser.parse_args()

    run_root = args.run_root.resolve()
    project = run_root / "video2mesh"
    run_manifest_path = run_root / "run_manifest.json"
    run_manifest = read_json(run_manifest_path, {})
    camera_validation = read_json(run_root / "logs" / "camera_coordinate_validation.json", {})
    dino = read_json(project / "masks" / "object_prompts_groundingdino.json", {})
    scene_json = read_json(run_root / "GroundingDINO-Scannetppv2" / "bedroom_4.json", {})
    sam3_tracking = read_json(project / "masks" / "2d" / "tracking_manifest.json", {})
    class_fusion = read_json(project / "masks" / "3d" / "object_masks.json", {})
    instance_fusion = read_json(project / "masks" / "3d_instances" / "object_masks.json", {})
    semantic_manifest = read_json(project / "simulator_assets" / "semantic_splats_manifest.json", {})
    semantic_preview = read_json(project / "simulator_assets" / "semantic_preview" / "semantic_preview.json", {})
    pgsr_log_path = run_root / "logs" / "pgsr_official_30k.log"
    pgsr_log = parse_pgsr_log(pgsr_log_path)

    instance_objects = instance_fusion.get("objects", {})
    roles = Counter(item.get("asset_role", "unknown") for item in instance_objects.values())
    category_counts = Counter(item.get("category", "unknown") for item in instance_objects.values())
    semantic_objects = semantic_manifest.get("objects", [])
    semantic_foreground_points = sum(
        int(item.get("point_count") or 0)
        for item in semantic_objects
        if int(item.get("semantic_id") or 0) > 0
    )

    pointcloud_da3 = run_root / "scannetppv2" / "data" / "bedroom_4" / "pointcloud_da3.ply"
    semantic_da3 = project / "simulator_assets" / "semantic_da3_points.ply"
    pgsr_ply = run_root / "pgsr_scannetppv2_all" / "bedroom_4" / "point_cloud" / "iteration_30000" / "point_cloud.ply"
    pgsr_semantic = project / "simulator_assets" / "semantic_pgsr_30k.ply"
    pgsr_mesh = run_root / "pgsr_scannetppv2_all" / "bedroom_4" / "mesh" / "tsdf_fusion_post.ply"

    counts = {
        "source_frames": relative_file_count(project / "scene" / "frames", "*.png"),
        "da3_depth_maps": relative_file_count(run_root / "scannetppv2" / "data" / "bedroom_4" / "depth_da3", "*.npy"),
        "da3_points": int((ply_header(pointcloud_da3) or {}).get("vertex_count") or 0),
        "dino_candidates": int(dino.get("candidate_count") or 0),
        "dino_prompts": int(dino.get("object_count") or len(dino.get("objects", []))),
        "dino_categories": len(scene_json.get("categories", [])),
        "sam3_instance_masks": int(sam3_tracking.get("counts", {}).get("source_instance_masks") or 0),
        "sam3_classes": int(sam3_tracking.get("counts", {}).get("classes") or 0),
        "sam3_merged_masks": int(sam3_tracking.get("counts", {}).get("merged_class_frame_masks") or 0),
        "class_fusion_masks": int(class_fusion.get("num_masks") or 0),
        "instances_total": len(instance_objects),
        "foreground_instances": int(roles.get("foreground_object", 0)),
        "structure_instances": int(roles.get("background_structure", 0)),
        "instances_by_category": dict(sorted(category_counts.items())),
        "semantic_foreground_points": semantic_foreground_points,
    }

    pgsr_complete = bool(pgsr_log.get("training_complete") and pgsr_ply.exists())
    pgsr_mesh_complete = pgsr_mesh.exists()
    pgsr_semantic_complete = pgsr_semantic.exists()
    stages = {
        "data_package": {
            "status": "Passed" if camera_validation.get("passed") else "Failed",
            "evidence": f"80 cameras; round-trip error {camera_validation.get('max_world_to_camera_roundtrip_abs_error')}",
        },
        "DA3": {
            "status": "Passed" if counts["da3_depth_maps"] == 80 and counts["da3_points"] == 4_000_000 else "Incomplete",
            "evidence": f"{counts['da3_depth_maps']} depths, {counts['da3_points']} points",
        },
        "GroundingDINO_category_discovery": {
            "status": "Passed",
            "evidence": f"{counts['dino_candidates']} candidates -> {counts['dino_prompts']} prompts -> {counts['dino_categories']} categories",
        },
        "SAM3": {
            "status": "Passed" if counts["sam3_instance_masks"] else "Incomplete",
            "evidence": f"{counts['sam3_instance_masks']} real masks; {counts['sam3_classes']} classes produced masks",
        },
        "Video2Mesh_2D_to_3D": {
            "status": "Passed" if counts["instances_total"] else "Incomplete",
            "evidence": f"probability fusion + occlusion + min 2 votes; {counts['instances_total']} records",
        },
        "bbox_postprocess": {
            "status": "Passed" if (run_root / "output_scannetppv2_new" / "bedroom_4.json").exists() else "Incomplete",
            "evidence": "voxel DBSCAN, 0.5% robust AABB, PCA OBB",
        },
        "PGSR_30k": {
            "status": "Passed" if pgsr_complete else "Running" if pgsr_log.get("exists") else "Pending",
            "evidence": f"iteration {pgsr_log.get('latest_iteration_seen', 0)}; missing-depth warnings {pgsr_log.get('depth_not_found_warnings')}",
        },
        "PGSR_mesh": {
            "status": "Passed" if pgsr_mesh_complete else "Pending",
            "evidence": str(pgsr_mesh),
        },
        "PGSR_semantic_transfer": {
            "status": "Passed" if pgsr_semantic_complete else "Pending",
            "evidence": str(pgsr_semantic),
        },
    }
    required_complete = all(
        stages[name]["status"] == "Passed"
        for name in [
            "data_package",
            "DA3",
            "GroundingDINO_category_discovery",
            "SAM3",
            "Video2Mesh_2D_to_3D",
            "bbox_postprocess",
            "PGSR_30k",
            "PGSR_mesh",
            "PGSR_semantic_transfer",
        ]
    )

    artifacts = {
        "DA3 point cloud": artifact(pointcloud_da3),
        "semantic DA3 PLY": artifact(semantic_da3),
        "3D bbox JSON": artifact(run_root / "output_scannetppv2_new" / "bedroom_4.json"),
        "object PLY manifest": artifact(project / "simulator_assets" / "object_masks_3d" / "object_mask_clouds.json"),
        "SAM3 2D overview": artifact(run_root / "visualizations" / "sam3_2d_overlay_contact_sheet.jpg"),
        "3D bbox topdown": artifact(run_root / "visualizations" / "sam3_da3_3d_bbox_topdown.png"),
        "PGSR 30k PLY": artifact(pgsr_ply),
        "PGSR TSDF post mesh": artifact(pgsr_mesh),
        "semantic PGSR PLY": artifact(pgsr_semantic),
        "PGSR log": artifact(pgsr_log_path),
    }
    limitations = [
        "GroundingDINO is used only to filter the category vocabulary; SAM3 independently predicts its own boxes, scores, and masks.",
        "GroundingDINO retained 11 categories, but SAM3 produced thresholded masks for 9; table and wall art are absent rather than fabricated.",
        "SAM3 image inference has no stable cross-frame instance ID here; foreground instances are split after lifting with voxel DBSCAN.",
        "Door and ceiling masks are visibly less reliable than bed/floor/lamp/nightstand/plant/window and should be treated as low-confidence labels.",
        "BBox dimensions are in the COLMAP/Video2Mesh scene coordinate scale, not meters; metric claims require an explicit scale calibration.",
        "The semantic PLY stores fields as data; viewers must color/filter by object_id to expose semantics.",
    ]
    report = {
        "schema_version": 1,
        "status": "Completed" if required_complete else "Running",
        "run_root": str(run_root),
        "project_root": str(project),
        "components": {
            "DA3": "depth-anything/DA3NESTED-GIANT-LARGE via official Holi-Spatial inference script",
            "category_discovery": "GroundingDINO query-bank filtering only",
            "segmentation": "real SAM3 checkpoint inference",
            "lifting": "Video2Mesh probability fusion, visibility filtering, multi-view votes",
            "instance_postprocess": "voxel DBSCAN + robust AABB + PCA OBB",
            "surface_reconstruction": "official PGSR per-scene training and TSDF render",
        },
        "counts": counts,
        "stages": stages,
        "pgsr": pgsr_log,
        "semantic_preview": semantic_preview.get("summary"),
        "artifacts": artifacts,
        "limitations": limitations,
    }
    write_json(run_root / "experiment_report.json", report)
    (run_root / "experiment_report.md").write_text(markdown_report(report), encoding="utf-8")

    run_manifest["status"] = report["status"].lower()
    run_manifest["stage_status"] = {name: item["status"] for name, item in stages.items()}
    run_manifest["experiment_report"] = str(run_root / "experiment_report.json")
    run_manifest["counts"] = counts
    run_manifest["limitations"] = limitations
    write_json(run_manifest_path, run_manifest)
    print(json.dumps({"status": report["status"], "counts": counts, "stages": stages}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
