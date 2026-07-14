#!/usr/bin/env python3
"""Validate TRELLIS Gaussian PLY files and create lightweight QA previews."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from plyfile import PlyData

from trellis_geometry_contracts import evaluate_geometry_contract


REQUIRED_FIELDS = {
    "x",
    "y",
    "z",
    "f_dc_0",
    "f_dc_1",
    "f_dc_2",
    "opacity",
    "scale_0",
    "scale_1",
    "scale_2",
    "rot_0",
    "rot_1",
    "rot_2",
    "rot_3",
}
SH_C0 = 0.28209479177387814


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def normalized_pixels(values: np.ndarray, width: int, margin: int) -> np.ndarray:
    lower, upper = np.percentile(values, (0.5, 99.5))
    if not np.isfinite(lower) or not np.isfinite(upper) or upper - lower < 1e-9:
        lower, upper = float(values.min()), float(values.max())
    span = max(upper - lower, 1e-9)
    pixels = margin + (values - lower) / span * max(1, width - 2 * margin - 1)
    return np.clip(np.rint(pixels).astype(np.int32), 0, width - 1)


def render_projection(
    left: np.ndarray,
    right: np.ndarray,
    colors: np.ndarray,
    alpha: np.ndarray,
    title: str,
    size: tuple[int, int] = (560, 500),
) -> Image.Image:
    width, height = size
    margin = 20
    x = normalized_pixels(left, width, margin)
    y = normalized_pixels(right, height - 42, margin) + 22
    y = (height - 1) - y
    canvas = np.zeros((height, width, 3), dtype=np.float32)
    weights = np.zeros((height, width), dtype=np.float32)
    weighted_colors = colors * alpha[:, None]
    np.add.at(canvas, (y, x), weighted_colors)
    np.add.at(weights, (y, x), alpha)
    visible = weights > 0
    canvas[visible] /= weights[visible, None]
    background = np.array([30, 35, 37], dtype=np.float32) / 255.0
    mix = np.clip(weights[..., None] * 0.60, 0.0, 0.96)
    image_array = np.where(visible[..., None], canvas * mix + background * (1.0 - mix), background)
    image = Image.fromarray(np.clip(image_array * 255.0, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(image)
    draw.text((12, 8), title, fill=(230, 235, 237), font=ImageFont.load_default())
    return image


def preview(vertices: np.ndarray, output_path: Path, max_points: int) -> None:
    points = np.column_stack([vertices["x"], vertices["y"], vertices["z"]]).astype(np.float32)
    features = np.column_stack([vertices["f_dc_0"], vertices["f_dc_1"], vertices["f_dc_2"]]).astype(np.float32)
    opacity = sigmoid(np.asarray(vertices["opacity"], dtype=np.float32))
    finite = np.isfinite(points).all(axis=1) & np.isfinite(features).all(axis=1) & np.isfinite(opacity)
    indices = np.flatnonzero(finite)
    if len(indices) > max_points:
        generator = np.random.default_rng(20260713)
        indices = generator.choice(indices, size=max_points, replace=False)
    selected_points = points[indices]
    selected_colors = np.clip(0.5 + SH_C0 * features[indices], 0.0, 1.0)
    selected_alpha = np.clip(0.10 + 0.90 * opacity[indices], 0.05, 1.0)
    panels = [
        render_projection(selected_points[:, 0], selected_points[:, 1], selected_colors, selected_alpha, "X / Y"),
        render_projection(selected_points[:, 0], selected_points[:, 2], selected_colors, selected_alpha, "X / Z"),
        render_projection(selected_points[:, 1], selected_points[:, 2], selected_colors, selected_alpha, "Y / Z"),
    ]
    sheet = Image.new("RGB", (len(panels) * panels[0].width, panels[0].height), (30, 35, 37))
    for index, panel in enumerate(panels):
        sheet.paste(panel, (index * panel.width, 0))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def qa_one(
    path: Path,
    output_dir: Path,
    max_points: int,
    geometry_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ply = PlyData.read(path)
    if not ply.elements:
        raise ValueError("PLY has no elements")
    vertices = ply["vertex"].data
    names = set(vertices.dtype.names or [])
    missing_fields = sorted(REQUIRED_FIELDS - names)
    all_finite = True
    finite_counts: dict[str, int] = {}
    for name in sorted(REQUIRED_FIELDS & names):
        values = np.asarray(vertices[name])
        finite = np.isfinite(values)
        finite_counts[name] = int(finite.sum())
        all_finite = all_finite and bool(finite.all())
    point_array = np.column_stack([vertices["x"], vertices["y"], vertices["z"]]).astype(np.float64) if not missing_fields else np.empty((0, 3))
    rotations = np.column_stack([vertices["rot_0"], vertices["rot_1"], vertices["rot_2"], vertices["rot_3"]]).astype(np.float64) if not missing_fields else np.empty((0, 4))
    norms = np.linalg.norm(rotations, axis=1) if len(rotations) else np.empty(0)
    opacity = sigmoid(np.asarray(vertices["opacity"], dtype=np.float64)) if not missing_fields else np.empty(0)
    file_passed = bool(not missing_fields and all_finite and len(vertices))
    geometry = evaluate_geometry_contract(point_array, opacity, geometry_contract) if file_passed else {
        "kind": geometry_contract.get("kind") if isinstance(geometry_contract, dict) else None,
        "status": "not_tested",
        "reason": "file_contract_failed",
    }
    geometry_passed = geometry["status"] in {"passed", "not_applicable"}
    preview_path = output_dir / f"{path.stem}_orthographic_preview.png"
    if not missing_fields and len(vertices):
        preview(vertices, preview_path, max_points)
    result = {
        "source_ply": str(path),
        "bytes": path.stat().st_size,
        "vertex_count": int(len(vertices)),
        "properties": list(vertices.dtype.names or []),
        "missing_required_fields": missing_fields,
        "all_required_attributes_finite": all_finite,
        "finite_counts": finite_counts,
        "position_bbox": {
            "min": point_array.min(axis=0).tolist() if len(point_array) else None,
            "max": point_array.max(axis=0).tolist() if len(point_array) else None,
        },
        "quaternion_norm": {
            "min": float(norms.min()) if len(norms) else None,
            "median": float(np.median(norms)) if len(norms) else None,
            "max": float(norms.max()) if len(norms) else None,
        },
        "file_status": "passed" if file_passed else "failed",
        "geometry_contract": geometry_contract,
        "geometry": geometry,
        "preview": str(preview_path) if preview_path.exists() else None,
        "status": "passed" if file_passed and geometry_passed else "failed",
    }
    write_json(output_dir / f"{path.stem}_qa.json", result)
    return result


def make_contact_sheet(results: list[dict[str, Any]], output_path: Path) -> None:
    tile_width = 480
    tile_height = 184
    columns = 2
    rows = max(1, math.ceil(len(results) / columns))
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), (30, 35, 37))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, result in enumerate(results):
        preview_value = result.get("preview")
        if not isinstance(preview_value, str) or not Path(preview_value).is_file():
            continue
        preview = Image.open(preview_value).convert("RGB")
        preview.thumbnail((tile_width - 24, tile_height - 44), Image.Resampling.LANCZOS)
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        sheet.paste(preview, (x + 12, y + 12))
        label = Path(str(result["source_ply"])).stem.replace("_trellis_gaussian", "")
        detail = f"{result['status']}  {result['vertex_count']} gaussians"
        draw.text((x + 12, y + tile_height - 28), label, fill=(235, 238, 240), font=font)
        draw.text((x + 228, y + tile_height - 28), detail, fill=(174, 182, 185), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-preview-points", type=int, default=140000)
    parser.add_argument("--input-manifest", type=Path, help="Optional TRELLIS input manifest containing per-object geometry_contract values.")
    parser.add_argument("--require-geometry-contract", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(args.input_dir.glob("*_trellis_gaussian.ply"))
    if not paths:
        raise FileNotFoundError(f"No TRELLIS Gaussian PLY files in {args.input_dir}")
    contracts: dict[str, dict[str, Any]] = {}
    if args.input_manifest:
        manifest = json.loads(args.input_manifest.read_text(encoding="utf-8"))
        prepared = manifest.get("prepared") if isinstance(manifest, dict) else None
        if not isinstance(prepared, list):
            raise ValueError(f"Missing prepared list in {args.input_manifest}")
        for item in prepared:
            if not isinstance(item, dict):
                continue
            object_id = item.get("object_id")
            contract = item.get("geometry_contract")
            if isinstance(object_id, str) and isinstance(contract, dict):
                contracts[object_id] = contract
    results: list[dict[str, Any]] = []
    for path in paths:
        object_id = path.stem.removesuffix("_trellis_gaussian")
        geometry_contract = contracts.get(object_id)
        if args.require_geometry_contract and geometry_contract is None:
            geometry_contract = {"kind": "missing_required_contract"}
        result = qa_one(path, args.output_dir, args.max_preview_points, geometry_contract)
        results.append(result)
        print(f"{path.name}: {result['status']} vertices={result['vertex_count']}")
    summary = {
        "schema_version": 1,
        "input_dir": str(args.input_dir.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "file_count": len(results),
        "passed_count": sum(result["status"] == "passed" for result in results),
        "failed_count": sum(result["status"] != "passed" for result in results),
        "results": results,
    }
    contact_sheet = args.output_dir / "gaussian_preview_contact_sheet.png"
    make_contact_sheet(results, contact_sheet)
    summary["preview_contact_sheet"] = str(contact_sheet)
    write_json(args.output_dir / "qa_summary.json", summary)
    return 1 if summary["failed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
