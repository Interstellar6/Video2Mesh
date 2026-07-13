#!/usr/bin/env python3
"""Run the locally cached TRELLIS Gaussian decoder over prepared object inputs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GAUSSIAN_MODEL_KEYS = {
    "sparse_structure_decoder",
    "sparse_structure_flow_model",
    "slat_decoder_gs",
    "slat_flow_model",
}


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


def vertex_count(path: Path) -> int | None:
    with path.open("rb") as handle:
        for raw_line in handle:
            line = raw_line.decode("ascii", errors="replace").strip()
            if line.startswith("element vertex "):
                return int(line.split()[-1])
            if line == "end_header":
                break
    return None


def reviewed_specs(path: Path) -> dict[str, dict[str, Any]]:
    report = read_json(path)
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError(f"Missing results in VLM spec manifest: {path}")
    specs: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        object_id = result.get("object_id")
        spec_path = result.get("spec_path")
        if not isinstance(object_id, str) or not isinstance(spec_path, str):
            continue
        spec = read_json(Path(spec_path))
        if spec.get("object_id") == object_id:
            specs[object_id] = spec
    return specs


def gaussian_only_weight_root(weights: Path, output_root: Path) -> Path:
    config = read_json(weights / "pipeline.json")
    args = config.get("args")
    if not isinstance(args, dict) or not isinstance(args.get("models"), dict):
        raise ValueError(f"Invalid TRELLIS pipeline config: {weights / 'pipeline.json'}")
    args = dict(args)
    args["models"] = {key: value for key, value in args["models"].items() if key in GAUSSIAN_MODEL_KEYS}
    config = dict(config)
    config["args"] = args
    root = output_root / "_gaussian_only_weights"
    root.mkdir(parents=True, exist_ok=True)
    ckpts_link = root / "ckpts"
    if not ckpts_link.exists():
        try:
            ckpts_link.symlink_to(weights / "ckpts", target_is_directory=True)
        except FileExistsError:
            pass
    config_path = root / "pipeline.json"
    temporary = root / f".pipeline.{os.getpid()}.json"
    temporary.write_text(json.dumps(config, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(config_path)
    return root


def install_compatibility_shims() -> None:
    sys.modules.setdefault("ipdb", types.SimpleNamespace(set_trace=lambda: None))
    sys.modules.setdefault(
        "rembg",
        types.SimpleNamespace(new_session=lambda *_args, **_kwargs: None, remove=lambda image, **_kwargs: image),
    )
    mesh_module_name = "trellis.representations.mesh"
    if mesh_module_name not in sys.modules:
        mesh_module = types.ModuleType(mesh_module_name)
        mesh_module.MeshExtractResult = type("MeshExtractResult", (), {})
        mesh_module.SparseFeatures2Mesh = type("SparseFeatures2Mesh", (), {})
        sys.modules[mesh_module_name] = mesh_module


def load_pipeline(trellis_root: Path, weights: Path, output_root: Path, dino_source: Path) -> tuple[Any, Any]:
    os.environ.setdefault("ATTN_BACKEND", "xformers")
    os.environ.setdefault("SPCONV_ALGO", "native")
    install_compatibility_shims()
    sys.path.insert(0, str(trellis_root))
    import torch

    original_hub_load = torch.hub.load

    def local_hub_load(repo_or_dir: str, model: str, *args: Any, **kwargs: Any) -> Any:
        if repo_or_dir == "facebookresearch/dinov2":
            local_kwargs = dict(kwargs)
            local_kwargs["source"] = "local"
            return original_hub_load(str(dino_source), model, *args, **local_kwargs)
        return original_hub_load(repo_or_dir, model, *args, **kwargs)

    torch.hub.load = local_hub_load
    from trellis.pipelines import TrellisImageTo3DPipeline

    config_root = gaussian_only_weight_root(weights, output_root)
    pipeline = TrellisImageTo3DPipeline.from_pretrained(str(config_root))
    pipeline.cuda()
    return pipeline, torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--trellis-root", type=Path, required=True)
    parser.add_argument("--dino-source", type=Path, required=True)
    parser.add_argument("--gpu", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--objects", nargs="*")
    parser.add_argument(
        "--vlm-spec-manifest",
        type=Path,
        help="Validated instance-contract review. Entries without generation_allowed=true are blocked.",
    )
    parser.add_argument("--skip-existing", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    os.environ["ATTN_BACKEND"] = "xformers"
    os.environ["SPCONV_ALGO"] = "native"
    manifest = read_json(args.input_manifest)
    prepared = manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared inputs in {args.input_manifest}")
    wanted = set(args.objects or [])
    jobs = [item for item in prepared if isinstance(item, dict) and (not wanted or item.get("object_id") in wanted)]
    output_root = args.output_root.resolve()
    output_dir = output_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = reviewed_specs(args.vlm_spec_manifest.resolve()) if args.vlm_spec_manifest else {}
    results: list[dict[str, Any]] = []
    allowed_jobs: list[dict[str, Any]] = []
    for item in jobs:
        object_id = str(item["object_id"])
        if not args.vlm_spec_manifest:
            allowed_jobs.append(item)
            continue
        spec = specs.get(object_id)
        if spec and spec.get("generation_allowed") is True:
            allowed_jobs.append(item)
            continue
        results.append(
            {
                "object_id": object_id,
                "input": str(item.get("rgba_path") or ""),
                "status": "blocked_by_vlm_instance_contract",
                "vlm_spec_manifest": str(args.vlm_spec_manifest.resolve()),
                "vlm_decision": spec.get("decision") if spec else "missing_review",
                "reason": "TRELLIS accepts only reviewed single-instance inputs when --vlm-spec-manifest is supplied.",
            }
        )
        print(f"blocked {object_id}: VLM review did not allow single-instance generation", flush=True)
    pipeline: Any | None = None
    torch: Any | None = None
    if allowed_jobs:
        pipeline, torch = load_pipeline(args.trellis_root.resolve(), args.weights.resolve(), output_root, args.dino_source.resolve())
        from PIL import Image

    for index, item in enumerate(allowed_jobs):
        object_id = str(item["object_id"])
        input_path = Path(str(item["rgba_path"]))
        ply_path = output_dir / f"{object_id}_trellis_gaussian.ply"
        entry: dict[str, Any] = {
            "object_id": object_id,
            "input": str(input_path),
            "gpu": args.gpu,
            "seed": int(args.seed + index),
            "formats": ["gaussian"],
            "preprocess_image": True,
        }
        if args.vlm_spec_manifest:
            entry["vlm_spec_manifest"] = str(args.vlm_spec_manifest.resolve())
            entry["vlm_decision"] = specs[object_id].get("decision")
        if args.skip_existing and ply_path.is_file() and ply_path.stat().st_size > 0:
            entry.update({
                "status": "skipped_existing",
                "output_ply": str(ply_path),
                "output_bytes": ply_path.stat().st_size,
                "vertex_count": vertex_count(ply_path),
            })
            results.append(entry)
            continue
        started = time.perf_counter()
        try:
            if pipeline is None or torch is None:
                raise RuntimeError("TRELLIS pipeline was not initialized for an allowed job")
            torch.cuda.reset_peak_memory_stats()
            image = Image.open(input_path).convert("RGBA")
            outputs = pipeline.run_old(
                image,
                seed=int(args.seed + index),
                formats=["gaussian"],
                preprocess_image=True,
            )
            torch.cuda.synchronize()
            outputs["gaussian"][0].save_ply(str(ply_path))
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - started
            entry.update({
                "status": "completed",
                "output_ply": str(ply_path),
                "output_bytes": ply_path.stat().st_size,
                "vertex_count": vertex_count(ply_path),
                "elapsed_seconds": elapsed,
                "max_vram_gb": float(torch.cuda.max_memory_allocated() / (1024 ** 3)),
            })
            del outputs
            print(f"completed {object_id}: {entry['vertex_count']} vertices in {elapsed:.3f}s", flush=True)
        except Exception as exc:
            entry.update({
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            })
            print(f"failed {object_id}: {entry['error']}", flush=True)
        finally:
            torch.cuda.empty_cache()
        results.append(entry)
    worker_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "TRELLIS image-to-3D Gaussian-only local cached batch",
        "gpu": args.gpu,
        "weights": str(args.weights.resolve()),
        "trellis_root": str(args.trellis_root.resolve()),
        "dino_source": str(args.dino_source.resolve()),
        "job_count": len(jobs),
        "allowed_job_count": len(allowed_jobs),
        "vlm_spec_manifest": str(args.vlm_spec_manifest.resolve()) if args.vlm_spec_manifest else None,
        "results": results,
    }
    worker_manifest_path = output_dir / f"worker_gpu{args.gpu}_manifest.json"
    write_json(worker_manifest_path, worker_manifest)
    completed = sum(item.get("status") == "completed" for item in results)
    failed = sum(item.get("status") == "failed" for item in results)
    blocked = sum(item.get("status") == "blocked_by_vlm_instance_contract" for item in results)
    print(f"worker gpu={args.gpu}: completed={completed} blocked={blocked} failed={failed} manifest={worker_manifest_path}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
