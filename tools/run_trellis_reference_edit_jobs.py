#!/usr/bin/env python3
"""Execute planned reference edits through the bundled image CLI and chroma-key helper."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


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


def alpha_report(path: Path) -> dict[str, Any]:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    transparent_pixels = int(histogram[0])
    opaque_pixels = int(histogram[255])
    partial_pixels = int(sum(histogram[1:255]))
    foreground_pixels = opaque_pixels + partial_pixels
    total_pixels = image.width * image.height
    if foreground_pixels < 1024:
        raise ValueError(f"Reference has insufficient foreground pixels: {foreground_pixels}")
    if transparent_pixels < 64:
        raise ValueError("Reference has no meaningful transparent background")
    if foreground_pixels / max(total_pixels, 1) >= 0.92:
        raise ValueError("Reference foreground occupies too much of the canvas")
    return {
        "width": image.width,
        "height": image.height,
        "transparent_pixels": transparent_pixels,
        "partial_alpha_pixels": partial_pixels,
        "opaque_pixels": opaque_pixels,
        "foreground_pixels": foreground_pixels,
        "foreground_ratio": foreground_pixels / max(total_pixels, 1),
        "alpha_bbox": list(alpha.getbbox() or (0, 0, 0, 0)),
    }


def make_contact_sheet(results: list[dict[str, Any]], output_path: Path) -> None:
    completed = [result for result in results if result.get("status") == "completed"]
    tile_width = 300
    tile_height = 380
    columns = 4
    rows = max(1, math.ceil(len(completed) / columns))
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), (30, 35, 37))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, result in enumerate(completed):
        source = Path(str(result["rgba_output"]))
        if not source.is_file():
            continue
        preview = Image.open(source).convert("RGBA")
        preview = ImageOps.contain(preview, (tile_width - 24, tile_height - 70), Image.Resampling.LANCZOS)
        background = Image.new("RGBA", preview.size, (62, 68, 72, 255))
        background.alpha_composite(preview)
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        sheet.paste(background.convert("RGB"), (x + 12, y + 12))
        alpha = result.get("alpha", {})
        detail = f"foreground={float(alpha.get('foreground_ratio') or 0.0):.3f}"
        draw.text((x + 12, y + tile_height - 48), str(result["object_id"]), fill=(238, 240, 241), font=font)
        draw.text((x + 12, y + tile_height - 28), detail, fill=(177, 185, 188), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def run_checked(command: list[str]) -> None:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip(), flush=True)
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip() or "command failed without output"
        raise RuntimeError(f"Command returned {result.returncode}: {message[-2000:]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--image-gen-script", type=Path, required=True)
    parser.add_argument("--remove-chroma-key-script", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--objects", nargs="*")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = read_json(args.jobs)
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError(f"Missing jobs list in {args.jobs}")
    if not args.image_gen_script.is_file():
        raise FileNotFoundError(args.image_gen_script)
    if not args.remove_chroma_key_script.is_file():
        raise FileNotFoundError(args.remove_chroma_key_script)
    wanted = set(args.objects or [])
    output_root = args.output_root.resolve()
    raw_dir = output_root / "reference_raw"
    rgba_dir = output_root / "reference_rgba"
    metadata_dir = output_root / "provider_metadata"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rgba_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for raw_job in jobs:
        if not isinstance(raw_job, dict):
            continue
        object_id = str(raw_job.get("object_id") or "")
        if not object_id or (wanted and object_id not in wanted):
            continue
        source = Path(str(raw_job.get("source_image") or ""))
        raw_output = raw_dir / str(raw_job.get("raw_output_filename") or f"{object_id}.png")
        rgba_output = rgba_dir / str(raw_job.get("rgba_output_filename") or f"{object_id}.png")
        entry: dict[str, Any] = {
            "object_id": object_id,
            "provider": raw_job.get("provider"),
            "quality": raw_job.get("quality"),
            "size": raw_job.get("size"),
            "source_image": str(source),
            "raw_output": str(raw_output),
            "rgba_output": str(rgba_output),
        }
        try:
            if not source.is_file():
                raise FileNotFoundError(source)
            if args.force or not raw_output.is_file():
                command = [
                    args.python,
                    str(args.image_gen_script),
                    "edit",
                    "--image",
                    str(source),
                    "--prompt",
                    str(raw_job.get("prompt") or ""),
                    "--model",
                    str(raw_job.get("provider") or "gpt-image-2"),
                    "--quality",
                    str(raw_job.get("quality") or "medium"),
                    "--size",
                    str(raw_job.get("size") or "1024x1024"),
                    "--output-format",
                    "png",
                    "--no-augment",
                    "--out",
                    str(raw_output),
                ]
                if args.force:
                    command.append("--force")
                run_checked(command)
                provider_status = "completed"
            else:
                provider_status = "reused_existing"
            if args.force or not rgba_output.is_file():
                chroma_command = [
                    args.python,
                    str(args.remove_chroma_key_script),
                    "--input",
                    str(raw_output),
                    "--out",
                    str(rgba_output),
                    "--auto-key",
                    "border",
                    "--soft-matte",
                    "--transparent-threshold",
                    "12",
                    "--opaque-threshold",
                    "220",
                    "--despill",
                ]
                run_checked(chroma_command)
            report = alpha_report(rgba_output)
            entry.update({
                "status": "completed",
                "provider_status": provider_status,
                "source_sha256": sha256(source),
                "raw_sha256": sha256(raw_output),
                "rgba_sha256": sha256(rgba_output),
                "alpha": report,
            })
            print(f"completed reference edit: {object_id} foreground={report['foreground_pixels']}", flush=True)
        except Exception as exc:
            entry.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
            print(f"failed reference edit: {object_id}: {entry['error']}", flush=True)
            if args.stop_on_error:
                results.append(entry)
                write_json(metadata_dir / f"{object_id}.json", entry)
                break
        results.append(entry)
        write_json(metadata_dir / f"{object_id}.json", entry)

    summary = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "bundled_image_cli_edit_then_chroma_key_removal",
        "jobs_manifest": str(args.jobs.resolve()),
        "result_count": len(results),
        "completed_count": sum(result.get("status") == "completed" for result in results),
        "failed_count": sum(result.get("status") != "completed" for result in results),
        "results": results,
    }
    contact_sheet = output_root / "reference_qa" / "reference_contact_sheet.png"
    make_contact_sheet(results, contact_sheet)
    summary["reference_contact_sheet"] = str(contact_sheet)
    write_json(metadata_dir / "reference_edit_summary.json", summary)
    return 1 if summary["failed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
