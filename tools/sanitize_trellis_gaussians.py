#!/usr/bin/env python3
"""Create sanitized TRELLIS Gaussian PLY copies by dropping rare non-finite vertices."""

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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_vertex_mask(vertices: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    mask = np.ones(len(vertices), dtype=bool)
    nonfinite_by_field: dict[str, int] = {}
    for name in vertices.dtype.names or ():
        values = np.asarray(vertices[name])
        if not np.issubdtype(values.dtype, np.floating):
            continue
        finite = np.isfinite(values)
        count = int((~finite).sum())
        if count:
            nonfinite_by_field[name] = count
            mask &= finite
    return mask, nonfinite_by_field


def sanitize_ply(source: Path, destination: Path, max_drop_ratio: float) -> dict[str, Any]:
    if not (0.0 <= max_drop_ratio < 1.0):
        raise ValueError("max_drop_ratio must be in [0, 1)")
    ply = PlyData.read(source)
    vertices = ply["vertex"].data
    finite, nonfinite_by_field = finite_vertex_mask(vertices)
    input_count = int(len(vertices))
    output_count = int(finite.sum())
    dropped_count = input_count - output_count
    dropped_ratio = dropped_count / max(input_count, 1)
    if input_count <= 0:
        raise ValueError(f"PLY has no vertices: {source}")
    if dropped_ratio > max_drop_ratio:
        raise ValueError(
            f"Non-finite drop ratio {dropped_ratio:.6f} exceeds {max_drop_ratio:.6f}: {source}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if dropped_count:
        filtered = vertices[finite].copy()
        elements = [PlyElement.describe(filtered, "vertex")]
        elements.extend(element for element in ply.elements if element.name != "vertex")
        sanitized = PlyData(
            elements,
            text=ply.text,
            byte_order=ply.byte_order,
            comments=ply.comments,
            obj_info=ply.obj_info,
        )
        sanitized.write(destination)
        action = "dropped_nonfinite_vertices"
    else:
        shutil.copy2(source, destination)
        action = "copied_without_changes"
    return {
        "source_ply": str(source),
        "output_ply": str(destination),
        "action": action,
        "input_vertex_count": input_count,
        "output_vertex_count": output_count,
        "dropped_vertex_count": dropped_count,
        "dropped_vertex_ratio": dropped_ratio,
        "max_drop_ratio": max_drop_ratio,
        "nonfinite_by_field": nonfinite_by_field,
        "source_sha256": sha256(source),
        "output_sha256": sha256(destination),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-drop-ratio", type=float, default=0.01)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(args.input_dir.glob("*_trellis_gaussian.ply"))
    if not paths:
        raise FileNotFoundError(f"No TRELLIS Gaussian PLY files in {args.input_dir}")
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for source in paths:
        destination = args.output_dir / source.name
        try:
            report = sanitize_ply(source, destination, args.max_drop_ratio)
            report["status"] = "passed"
            results.append(report)
            print(
                f"sanitized {source.name}: dropped={report['dropped_vertex_count']} "
                f"ratio={report['dropped_vertex_ratio']:.6f}",
                flush=True,
            )
        except Exception as exc:
            failure = {
                "source_ply": str(source),
                "output_ply": str(destination),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
            failures.append(failure)
            print(f"failed sanitize {source.name}: {failure['error']}", flush=True)
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "drop_rare_nonfinite_gaussian_vertices_without_modifying_raw_outputs",
        "input_dir": str(args.input_dir.resolve()),
        "output_dir": str(args.output_dir.resolve()),
        "max_drop_ratio": args.max_drop_ratio,
        "passed_count": len(results),
        "failed_count": len(failures),
        "results": results,
        "failures": failures,
    }
    write_json(args.output_dir / "sanitization_manifest.json", manifest)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
