#!/usr/bin/env python3
"""Decode one PhysX-Anything prompted VLM output with the mesh+gaussian path."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("SPCONV_ALGO", "native")

import numpy as np
import torch
import trimesh
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_gaussian_raster_settings() -> None:
    import diff_gaussian_rasterization as dgr

    original_settings = dgr.GaussianRasterizationSettings

    def settings_compat(*args: Any, **kwargs: Any) -> Any:
        kwargs.pop("kernel_size", None)
        kwargs.pop("subpixel_offset", None)
        return original_settings(*args, **kwargs)

    dgr.GaussianRasterizationSettings = settings_compat


def mesh_stats(path: Path) -> dict[str, Any]:
    scene_or_mesh = trimesh.load(path, force="scene")
    geometries = list(scene_or_mesh.geometry.values()) if isinstance(scene_or_mesh, trimesh.Scene) else [scene_or_mesh]
    vertices = int(sum(len(getattr(geom, "vertices", [])) for geom in geometries))
    faces = int(sum(len(getattr(geom, "faces", [])) for geom in geometries))
    visual_types = sorted({type(getattr(geom, "visual", None)).__name__ for geom in geometries})
    return {
        "file_size": int(path.stat().st_size),
        "geometry_count": len(geometries),
        "vertices": vertices,
        "faces": faces,
        "visual_types": visual_types,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--qwen-dir", type=Path, required=True)
    parser.add_argument("--decoder", type=Path, default=Path("./pretrain/decoder_abs_debug"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--texture-size", type=int, default=1024)
    parser.add_argument("--simplify", type=float, default=0.5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    allind_path = args.qwen_dir / "allind.npy"
    if not allind_path.is_file():
        raise FileNotFoundError(f"Missing {allind_path}")
    output = args.output or (args.qwen_dir / "sample.glb")
    report_path = args.report or (args.qwen_dir / "decode_report.json")
    patch_gaussian_raster_settings()
    from trellis.pipelines import TrellisImageTo3DPipeline
    from trellis.utils import postprocessing_utils

    image = Image.open(args.image).convert("RGB")
    coords = np.load(allind_path)
    coords = coords + 32 - 16
    resolution = 64
    if (coords < 0).any() or (coords >= resolution).any():
        raise ValueError(f"Shifted coords out of [0, {resolution})")
    sparse = torch.zeros(1, resolution, resolution, resolution, dtype=torch.long)
    sparse[:, coords[:, 0], coords[:, 1], coords[:, 2]] = 1
    sparse = sparse.cuda().float().unsqueeze(0)
    print(f"[decode-one] image={args.image} size={image.size}")
    print(f"[decode-one] allind={coords.shape} shifted_min={coords.min(axis=0).tolist()} shifted_max={coords.max(axis=0).tolist()}")
    pipeline = TrellisImageTo3DPipeline.from_pretrained(str(args.decoder))
    pipeline.cuda()
    outputs = pipeline.run_control(sparse, image, seed=args.seed, formats=["mesh", "gaussian"])
    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        outputs["mesh"][0],
        simplify=args.simplify,
        texture_size=args.texture_size,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    glb.export(output)
    del outputs, sparse, pipeline
    gc.collect()
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "physx_anything_mesh_gaussian_decode_one_compat",
        "image": str(args.image),
        "qwen_dir": str(args.qwen_dir),
        "decoder": str(args.decoder),
        "output": str(output),
        "mesh_stats": mesh_stats(output),
    }
    write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
