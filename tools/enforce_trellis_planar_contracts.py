#!/usr/bin/env python3
"""Enforce accepted planar thickness on Gaussian centers and covariance in separate PLY copies."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from plyfile import PlyData, PlyElement

from trellis_geometry_contracts import planar_geometry_report


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30.0, 30.0)))


def quaternion_to_matrix(quaternions: np.ndarray) -> np.ndarray:
    q = np.asarray(quaternions, dtype=np.float64)
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    w, x, y, z = q.T
    matrices = np.empty((len(q), 3, 3), dtype=np.float64)
    matrices[:, 0, 0] = 1.0 - 2.0 * (y * y + z * z)
    matrices[:, 0, 1] = 2.0 * (x * y - z * w)
    matrices[:, 0, 2] = 2.0 * (x * z + y * w)
    matrices[:, 1, 0] = 2.0 * (x * y + z * w)
    matrices[:, 1, 1] = 1.0 - 2.0 * (x * x + z * z)
    matrices[:, 1, 2] = 2.0 * (y * z - x * w)
    matrices[:, 2, 0] = 2.0 * (x * z - y * w)
    matrices[:, 2, 1] = 2.0 * (y * z + x * w)
    matrices[:, 2, 2] = 1.0 - 2.0 * (x * x + y * y)
    return matrices


def matrix_to_quaternion(matrices: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrices, dtype=np.float64)
    quaternions = np.empty((len(matrix), 4), dtype=np.float64)
    quaternions[:, 0] = 0.5 * np.sqrt(np.maximum(0.0, 1.0 + matrix[:, 0, 0] + matrix[:, 1, 1] + matrix[:, 2, 2]))
    quaternions[:, 1] = 0.5 * np.copysign(
        np.sqrt(np.maximum(0.0, 1.0 + matrix[:, 0, 0] - matrix[:, 1, 1] - matrix[:, 2, 2])),
        matrix[:, 2, 1] - matrix[:, 1, 2],
    )
    quaternions[:, 2] = 0.5 * np.copysign(
        np.sqrt(np.maximum(0.0, 1.0 - matrix[:, 0, 0] + matrix[:, 1, 1] - matrix[:, 2, 2])),
        matrix[:, 0, 2] - matrix[:, 2, 0],
    )
    quaternions[:, 3] = 0.5 * np.copysign(
        np.sqrt(np.maximum(0.0, 1.0 - matrix[:, 0, 0] - matrix[:, 1, 1] + matrix[:, 2, 2])),
        matrix[:, 1, 0] - matrix[:, 0, 1],
    )
    quaternions /= np.maximum(np.linalg.norm(quaternions, axis=1, keepdims=True), 1e-12)
    return quaternions


def planar_transform(points: np.ndarray, opacity: np.ndarray, contract: dict[str, Any], target_ratio: float) -> tuple[np.ndarray, np.ndarray, float]:
    threshold = float(contract.get("opacity_threshold", 0.5))
    finite = np.isfinite(points).all(axis=1) & np.isfinite(opacity)
    selected = points[finite & (opacity >= threshold)]
    if len(selected) < 8:
        raise ValueError("Insufficient high-opacity points for planar transform")
    center = np.median(selected, axis=0)
    centered = selected - center
    covariance = centered.T @ centered / max(len(centered) - 1, 1)
    _, eigenvectors = np.linalg.eigh(covariance)
    thin_axis = eigenvectors[:, 0]
    before = planar_geometry_report(points, opacity, contract)
    current_ratio = float(before.get("thickness_to_short_side_ratio") or 0.0)
    if current_ratio <= 0.0:
        raise ValueError("Invalid source planar thickness ratio")
    factor = target_ratio / current_ratio
    transform = np.eye(3, dtype=np.float64) + (factor - 1.0) * np.outer(thin_axis, thin_axis)
    transformed_points = center + (points - center) @ transform.T
    return transformed_points, transform, factor


def transform_gaussian_covariances(
    scales: np.ndarray,
    quaternions: np.ndarray,
    transform: np.ndarray,
    chunk_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    output_scales = np.empty_like(scales, dtype=np.float64)
    output_quaternions = np.empty_like(quaternions, dtype=np.float64)
    for start in range(0, len(scales), chunk_size):
        stop = min(start + chunk_size, len(scales))
        scale_chunk = np.asarray(scales[start:stop], dtype=np.float64)
        rotation = quaternion_to_matrix(quaternions[start:stop])
        variances = np.exp(np.clip(2.0 * scale_chunk, -60.0, 60.0))
        covariance = np.einsum("nij,nj,nkj->nik", rotation, variances, rotation)
        transformed = np.einsum("ij,njk,lk->nil", transform, covariance, transform)
        eigenvalues, eigenvectors = np.linalg.eigh(transformed)
        order = np.argsort(eigenvalues, axis=1)[:, ::-1]
        eigenvalues = np.take_along_axis(eigenvalues, order, axis=1)
        eigenvectors = np.take_along_axis(eigenvectors, order[:, None, :], axis=2)
        negative = np.linalg.det(eigenvectors) < 0.0
        eigenvectors[negative, :, -1] *= -1.0
        output_scales[start:stop] = 0.5 * np.log(np.maximum(eigenvalues, 1e-30))
        output_quaternions[start:stop] = matrix_to_quaternion(eigenvectors)
    return output_scales, output_quaternions


def contract_index(path: Path) -> dict[str, dict[str, Any]]:
    manifest = read_json(path)
    prepared = manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared list in {path}")
    return {
        str(item["object_id"]): dict(item["geometry_contract"])
        for item in prepared
        if isinstance(item, dict) and isinstance(item.get("object_id"), str) and isinstance(item.get("geometry_contract"), dict)
    }


def enforce_one(
    source: Path,
    destination: Path,
    contract: dict[str, Any] | None,
    target_fraction: float,
    max_correctable_ratio: float,
    chunk_size: int,
) -> dict[str, Any]:
    object_id = source.stem.removesuffix("_trellis_gaussian")
    if not isinstance(contract, dict) or contract.get("kind") != "planar":
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return {"object_id": object_id, "action": "copied_non_planar", "source_ply": str(source), "output_ply": str(destination)}
    ply = PlyData.read(source)
    vertices = ply["vertex"].data
    points = np.column_stack([vertices["x"], vertices["y"], vertices["z"]]).astype(np.float64)
    opacity = sigmoid(np.asarray(vertices["opacity"], dtype=np.float64))
    before = planar_geometry_report(points, opacity, contract)
    current_ratio = float(before.get("thickness_to_short_side_ratio") or 0.0)
    max_ratio = float(contract.get("max_thickness_to_short_side_ratio", 0.1))
    if before.get("status") == "passed":
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return {
            "object_id": object_id,
            "action": "copied_already_compliant",
            "source_ply": str(source),
            "output_ply": str(destination),
            "before": before,
            "after": before,
        }
    if current_ratio <= 0.0 or current_ratio > max_correctable_ratio:
        raise ValueError(
            f"Planar ratio {current_ratio:.6f} is outside correctable range (0, {max_correctable_ratio:.6f}]"
        )
    target_ratio = max_ratio * target_fraction
    transformed_points, transform, factor = planar_transform(points, opacity, contract, target_ratio)
    scales = np.column_stack([vertices["scale_0"], vertices["scale_1"], vertices["scale_2"]])
    rotations = np.column_stack([vertices["rot_0"], vertices["rot_1"], vertices["rot_2"], vertices["rot_3"]])
    transformed_scales, transformed_rotations = transform_gaussian_covariances(
        scales, rotations, transform, chunk_size
    )
    filtered = vertices.copy()
    for index, name in enumerate(("x", "y", "z")):
        filtered[name] = transformed_points[:, index].astype(filtered[name].dtype)
    for index, name in enumerate(("scale_0", "scale_1", "scale_2")):
        filtered[name] = transformed_scales[:, index].astype(filtered[name].dtype)
    for index, name in enumerate(("rot_0", "rot_1", "rot_2", "rot_3")):
        filtered[name] = transformed_rotations[:, index].astype(filtered[name].dtype)
    elements = [PlyElement.describe(filtered, "vertex")]
    elements.extend(element for element in ply.elements if element.name != "vertex")
    destination.parent.mkdir(parents=True, exist_ok=True)
    PlyData(
        elements,
        text=ply.text,
        byte_order=ply.byte_order,
        comments=ply.comments,
        obj_info=ply.obj_info,
    ).write(destination)
    after = planar_geometry_report(transformed_points, opacity, contract)
    if after.get("status") != "passed":
        raise ValueError(f"Planar transform did not satisfy contract: {after}")
    return {
        "object_id": object_id,
        "action": "compressed_planar_axis_and_covariance",
        "source_ply": str(source),
        "output_ply": str(destination),
        "source_sha256": sha256(source),
        "output_sha256": sha256(destination),
        "axis_scale_factor": factor,
        "target_thickness_to_short_side_ratio": target_ratio,
        "before": before,
        "after": after,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--target-fraction", type=float, default=0.8)
    parser.add_argument("--max-correctable-ratio", type=float, default=0.5)
    parser.add_argument("--chunk-size", type=int, default=100000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (0.0 < args.target_fraction < 1.0):
        raise ValueError("target_fraction must be in (0, 1)")
    contracts = contract_index(args.input_manifest)
    paths = sorted(args.input_dir.glob("*_trellis_gaussian.ply"))
    if not paths:
        raise FileNotFoundError(f"No TRELLIS Gaussian PLY files in {args.input_dir}")
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for source in paths:
        object_id = source.stem.removesuffix("_trellis_gaussian")
        destination = args.output_dir / source.name
        try:
            result = enforce_one(
                source,
                destination,
                contracts.get(object_id),
                args.target_fraction,
                args.max_correctable_ratio,
                args.chunk_size,
            )
            result["status"] = "passed"
            results.append(result)
            print(f"planar contract {object_id}: {result['action']}", flush=True)
        except Exception as exc:
            failure = {"object_id": object_id, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
            failures.append(failure)
            print(f"failed planar contract {object_id}: {failure['error']}", flush=True)
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "pca_planar_center_and_gaussian_covariance_constraint",
        "input_dir": str(args.input_dir.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "input_manifest": str(args.input_manifest.resolve()),
        "target_fraction": args.target_fraction,
        "max_correctable_ratio": args.max_correctable_ratio,
        "passed_count": len(results),
        "failed_count": len(failures),
        "results": results,
        "failures": failures,
    }
    write_json(args.output_dir / "planar_contract_manifest.json", manifest)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
