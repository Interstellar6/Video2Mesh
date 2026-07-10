#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def pick_image(source: Path, pattern: str) -> Path:
    if source.is_file():
        return source
    candidates = sorted(
        path
        for path in source.rglob(pattern)
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS
    )
    if not candidates:
        raise FileNotFoundError(f"No image matching {pattern!r} under {source}")
    return candidates[len(candidates) // 2]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a real bedroom_4 frame as a PhysX-Anything single-image smoke input."
    )
    parser.add_argument("--source", required=True, type=Path, help="bedroom_4 image folder or a single image")
    parser.add_argument("--output", required=True, type=Path, help="Output run input directory")
    parser.add_argument("--pattern", default="*", help="Image glob used when --source is a directory")
    parser.add_argument("--label", default="bedroom_4_center_frame", help="Stable sample label")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    image = pick_image(source, args.pattern)

    demo_dir = output / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    target = demo_dir / f"{args.label}{image.suffix.lower()}"
    shutil.copy2(image, target)

    manifest = {
        "status": "prepared",
        "purpose": "PhysX-Anything smoke input from a real bedroom_4 frame",
        "source": str(source),
        "selected_image": str(image),
        "demo_image": str(target),
        "label": args.label,
        "important_limit": (
            "PhysX-Anything is a single-object sim-ready asset generator. "
            "This full-room frame is a smoke-test input only unless a reliable object crop or mask is supplied."
        ),
        "expected_next_commands": [
            "python 1_vlm_demo.py --demo_path ./demo --save_part_ply True --remove_bg True --ckpt ./pretrain/vlm",
            "python 2_decoder.py",
            "python 3_split.py",
            "python 4_simready_gen.py --voxel_define 32 --basepath ./test_demo --process 0 --fixed_base 0 --deformable 0",
        ],
    }
    manifest_path = output / "physx_anything_bedroom4_input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
