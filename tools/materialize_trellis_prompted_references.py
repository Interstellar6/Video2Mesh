#!/usr/bin/env python3
"""Attach prompt-edited RGBA references and geometry contracts to TRELLIS jobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
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


def validate_reference(path: Path, min_alpha_pixels: int, max_alpha_ratio: float) -> dict[str, Any]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    alpha_pixels = int(sum(histogram[1:]))
    total_pixels = int(image.width * image.height)
    alpha_ratio = alpha_pixels / max(total_pixels, 1)
    if alpha_pixels < min_alpha_pixels:
        raise ValueError(f"Reference {path} has only {alpha_pixels} nonzero-alpha pixels")
    if alpha_ratio >= max_alpha_ratio:
        raise ValueError(
            f"Reference {path} alpha ratio {alpha_ratio:.4f} is not an isolated foreground; "
            f"maximum is {max_alpha_ratio:.4f}"
        )
    return {
        "width": image.width,
        "height": image.height,
        "alpha_pixels": alpha_pixels,
        "alpha_ratio": alpha_ratio,
        "alpha_bbox": list(alpha.getbbox() or (0, 0, 0, 0)),
    }


def object_config(config: dict[str, Any], object_id: str) -> dict[str, Any]:
    objects = config.get("objects")
    if not isinstance(objects, dict) or not isinstance(objects.get(object_id), dict):
        raise ValueError(f"Missing prompted-reference config for {object_id}")
    value = dict(objects[object_id])
    prompt = value.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"Missing prompted-reference prompt for {object_id}")
    value["prompt"] = prompt.strip()
    return value


def materialize_reference(
    item: dict[str, Any],
    config: dict[str, Any],
    reference_path: Path,
    output_input_dir: Path,
    provider_metadata_path: Path | None,
    min_alpha_pixels: int,
    max_alpha_ratio: float,
) -> dict[str, Any]:
    object_id = str(item.get("object_id") or "")
    if not object_id:
        raise ValueError("Prepared TRELLIS item has no object_id")
    if not reference_path.is_file():
        raise FileNotFoundError(f"Missing prompted reference for {object_id}: {reference_path}")
    reference_report = validate_reference(reference_path, min_alpha_pixels, max_alpha_ratio)
    prompt_config = object_config(config, object_id)
    geometry_contract = prompt_config.get("geometry_contract", config.get("geometry_contract"))
    if not isinstance(geometry_contract, dict):
        raise ValueError(f"Missing geometry contract for {object_id}")
    output_input_dir.mkdir(parents=True, exist_ok=True)
    destination = output_input_dir / f"{object_id}_prompted_reference_rgba.png"
    shutil.copy2(reference_path, destination)
    provider = str(prompt_config.get("provider") or config.get("provider") or "external_image_editor")
    updated = dict(item)
    updated["prompted_reference"] = {
        "schema_version": 1,
        "kind": "video2mesh.trellis_prompted_reference",
        "rgba_path": str(destination),
        "source_rgba_path": str(item.get("rgba_path") or ""),
        "provider": provider,
        "prompt": prompt_config["prompt"],
        "expected_subject": prompt_config.get("expected_subject"),
        "provider_metadata_path": str(provider_metadata_path) if provider_metadata_path else None,
        "sha256": sha256(destination),
        "image": reference_report,
    }
    updated["geometry_contract"] = dict(geometry_contract)
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--reference-config", type=Path, required=True)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--provider-metadata-dir", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--objects", nargs="*")
    parser.add_argument("--min-alpha-pixels", type=int, default=1024)
    parser.add_argument("--max-alpha-ratio", type=float, default=0.92)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = read_json(args.input_manifest)
    prepared = manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared list in {args.input_manifest}")
    config = read_json(args.reference_config)
    wanted = set(args.objects or [])
    output_root = args.output_root.resolve()
    output_input_dir = output_root / "input"
    results: list[dict[str, Any]] = []
    for raw_item in prepared:
        if not isinstance(raw_item, dict):
            continue
        object_id = str(raw_item.get("object_id") or "")
        if wanted and object_id not in wanted:
            continue
        reference_path = args.reference_dir / f"{object_id}.png"
        metadata_path = None
        if args.provider_metadata_dir:
            candidate = args.provider_metadata_dir / f"{object_id}.json"
            metadata_path = candidate if candidate.is_file() else None
        materialized = materialize_reference(
            raw_item,
            config,
            reference_path,
            output_input_dir,
            metadata_path,
            args.min_alpha_pixels,
            args.max_alpha_ratio,
        )
        results.append(materialized)
        print(f"materialized prompted reference: {object_id}", flush=True)
    if not results:
        raise ValueError("No prompted references were materialized")
    output_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "prompt_edited_reference_to_trellis_rgba_with_geometry_contract",
        "source_input_manifest": str(args.input_manifest.resolve()),
        "reference_config": str(args.reference_config.resolve()),
        "prepared": results,
    }
    output_manifest_path = output_input_dir / "input_selection_manifest.json"
    write_json(output_manifest_path, output_manifest)
    print(f"prepared={len(results)} manifest={output_manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
