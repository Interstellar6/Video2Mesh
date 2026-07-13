#!/usr/bin/env python3
"""Prepare correctly aligned 2D-mask inputs for an AnySplat semantic transfer.

AnySplat predicts its own camera frame and processes every input image as a
center-cropped square. Projecting native Video2Mesh masks with COLMAP cameras
onto that Gaussian field is therefore invalid. This helper writes a matched
mask root and a camera_info.json in the AnySplat coordinate convention.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def image_paths(directory: Path) -> list[Path]:
    return sorted(path for path in directory.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)


def thumbnail(path: Path, size: int = 96) -> np.ndarray:
    with Image.open(path) as image:
        image = image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
        return np.asarray(image, dtype=np.float32) / 255.0


def match_input_frames(anysplat_images: list[Path], project_frames: list[Path]) -> list[dict[str, Any]]:
    project_thumbnails = [(path, thumbnail(path)) for path in project_frames]
    matches: list[dict[str, Any]] = []
    for image in anysplat_images:
        candidate = thumbnail(image)
        scores = [(float(np.mean((candidate - reference) ** 2)), path) for path, reference in project_thumbnails]
        scores.sort(key=lambda item: (item[0], item[1].name))
        best_score, best_path = scores[0]
        second_score = scores[1][0] if len(scores) > 1 else None
        matches.append(
            {
                "anysplat_frame_id": image.stem,
                "anysplat_image": str(image),
                "project_frame_id": best_path.stem,
                "project_frame": str(best_path),
                "mse": best_score,
                "second_best_mse": second_score,
            }
        )
    return matches


def anysplat_mask_crop(image: Image.Image, image_size: int) -> Image.Image:
    """Mirror AnySplat src.utils.image.process_image for a segmentation mask."""
    width, height = image.size
    if width > height:
        new_height = image_size
        new_width = int(width * (new_height / height))
    else:
        new_width = image_size
        new_height = int(height * (new_width / width))
    image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
    left = (new_width - image_size) // 2
    top = (new_height - image_size) // 2
    return image.crop((left, top, left + image_size, top + image_size))


def find_mask(mask_dir: Path, frame_id: str) -> Path | None:
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = mask_dir / f"{frame_id}{extension}"
        if candidate.exists():
            return candidate
    return None


def camera_info_from_anysplat(cameras_path: Path, frame_ids: list[str], image_size: int) -> dict[str, Any]:
    """Convert AnySplat camera-to-world predictions into Video2Mesh poses.

    AnySplat exposes ``pred_context_pose[\"extrinsic\"]`` as camera-to-world.
    Video2Mesh projection consumes world-to-camera matrices. Treating the former
    as the latter sends masks through the room and can label a foreground object
    onto an intervening wall, so inversion is required by this adapter contract.
    """
    with np.load(cameras_path, allow_pickle=False) as camera_arrays:
        extrinsics = np.asarray(camera_arrays["extrinsic"], dtype=np.float64).reshape(-1, 4, 4)
        intrinsics = np.asarray(camera_arrays["intrinsic"], dtype=np.float64).reshape(-1, 3, 3)
    if len(frame_ids) != extrinsics.shape[0] or len(frame_ids) != intrinsics.shape[0]:
        raise ValueError(
            f"Frame/camera count mismatch: frames={len(frame_ids)} extrinsics={extrinsics.shape[0]} intrinsics={intrinsics.shape[0]}"
        )
    intrinsic_records: dict[str, dict[str, float | int]] = {}
    frame_camera_ids: dict[str, str] = {}
    extrinsic_records: dict[str, list[list[float]]] = {}
    for index, frame_id in enumerate(frame_ids):
        camera_id = str(index)
        matrix = intrinsics[index]
        intrinsic_records[camera_id] = {
            "model": "PINHOLE",
            "w": int(image_size),
            "h": int(image_size),
            "fx": float(matrix[0, 0] * image_size),
            "fy": float(matrix[1, 1] * image_size),
            "cx": float(matrix[0, 2] * image_size),
            "cy": float(matrix[1, 2] * image_size),
        }
        frame_camera_ids[frame_id] = camera_id
        camera_to_world = extrinsics[index]
        if not np.isfinite(camera_to_world).all():
            raise ValueError(f"AnySplat camera {index} has non-finite extrinsic values")
        try:
            world_to_camera = np.linalg.inv(camera_to_world)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"AnySplat camera {index} has a non-invertible camera-to-world extrinsic") from exc
        extrinsic_records[frame_id] = world_to_camera.tolist()
    return {
        "schema_version": 1,
        "source": "anysplat_predicted_cameras",
        "extrinsic_type": "world_to_camera",
        "source_extrinsic_type": "camera_to_world",
        "extrinsic_conversion": "inverse(predicted_cameras.extrinsic)",
        "intrinsic": intrinsic_records["0"],
        "intrinsics": intrinsic_records,
        "frame_camera_ids": frame_camera_ids,
        "extrinsic": extrinsic_records,
        "notes": "AnySplat predicted camera-to-world poses were inverted to Video2Mesh world-to-camera poses. Masks were resized and center-cropped to the same square input used by AnySplat inference.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--anysplat-run", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path)
    parser.add_argument("--mask-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--image-size", type=int, default=448)
    parser.add_argument("--max-match-mse", type=float, default=0.04)
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    anysplat_run = args.anysplat_run.resolve()
    frames_dir = (args.frames_dir or project_root / "scene" / "frames").resolve()
    mask_root = (args.mask_root or project_root / "masks" / "2d").resolve()
    output_dir = (args.output_dir or anysplat_run / "semantic_projection_inputs").resolve()
    anysplat_images = image_paths(anysplat_run / "images")
    project_frames = image_paths(frames_dir)
    cameras_path = anysplat_run / "predicted_cameras.npz"
    if not anysplat_images or not project_frames:
        raise FileNotFoundError("AnySplat images and project frames must both be non-empty")
    if not cameras_path.exists():
        raise FileNotFoundError(f"Missing AnySplat predicted cameras: {cameras_path}")

    matches = match_input_frames(anysplat_images, project_frames)
    invalid = [item for item in matches if float(item["mse"]) > float(args.max_match_mse)]
    if invalid:
        raise RuntimeError(f"Unable to match {len(invalid)} AnySplat image(s) to project frames below mse={args.max_match_mse}: {invalid[:3]}")

    output_masks = output_dir / "masks_2d"
    copied_masks = 0
    missing_masks: list[dict[str, str]] = []
    for object_dir in sorted(path for path in mask_root.iterdir() if path.is_dir()):
        for match in matches:
            source = find_mask(object_dir, str(match["project_frame_id"]))
            if source is None:
                missing_masks.append({"object_id": object_dir.name, "project_frame_id": str(match["project_frame_id"])})
                continue
            with Image.open(source) as image:
                cropped = anysplat_mask_crop(image.convert("L"), int(args.image_size))
            target = output_masks / object_dir.name / f"{match['anysplat_frame_id']}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            cropped.save(target)
            copied_masks += 1

    frame_ids = [str(item["anysplat_frame_id"]) for item in matches]
    camera_info = camera_info_from_anysplat(cameras_path, frame_ids, int(args.image_size))
    camera_info_path = output_dir / "camera_info_anysplat.json"
    camera_info["frame_map"] = matches
    write_json(camera_info_path, camera_info)
    report_path = output_dir / "semantic_projection_inputs.json"
    report = {
        "project_root": str(project_root),
        "anysplat_run": str(anysplat_run),
        "camera_info": str(camera_info_path),
        "mask_root": str(output_masks),
        "image_size": int(args.image_size),
        "frame_count": len(matches),
        "copied_masks": copied_masks,
        "missing_masks": missing_masks,
        "frame_map": matches,
        "contract": "AnySplat predicted Gaussian coordinates are projected only with AnySplat predicted cameras and AnySplat-cropped 2D masks.",
    }
    write_json(report_path, report)
    print(json.dumps({"camera_info": str(camera_info_path), "mask_root": str(output_masks), "frame_count": len(matches), "copied_masks": copied_masks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
