#!/usr/bin/env python3
"""Review prepared TRELLIS inputs with a local Qwen2.5-VL instance contract."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def checkerboard(size: tuple[int, int], cell: int = 12) -> Image.Image:
    image = Image.new("RGB", size, (65, 70, 73))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(44, 48, 51))
    return image


def centered_panel(image: Image.Image, panel_size: tuple[int, int], background: tuple[int, int, int]) -> Image.Image:
    panel = Image.new("RGB", panel_size, background)
    preview = ImageOps.contain(image.convert("RGB"), panel_size, Image.Resampling.LANCZOS)
    left = (panel.width - preview.width) // 2
    top = (panel.height - preview.height) // 2
    panel.paste(preview, (left, top))
    return panel


def compose_review_image(rgb_path: Path, rgba_path: Path, support_path: Path, output_path: Path) -> None:
    panel_size = (384, 384)
    rgb = Image.open(rgb_path).convert("RGB")
    rgba = Image.open(rgba_path).convert("RGBA")
    support = Image.open(support_path).convert("L")
    alpha_panel = checkerboard(rgba.size)
    alpha_panel.paste(rgba.convert("RGB"), mask=rgba.getchannel("A"))
    support_overlay = rgb.copy()
    red = Image.new("RGB", rgb.size, (235, 74, 89))
    support_overlay = Image.blend(support_overlay, red, 0.58)
    support_overlay = Image.composite(support_overlay, rgb, support)
    labels = ["Source RGB", "SAM3 candidate RGBA", "Projected 3D support"]
    header_height = 28
    canvas = Image.new("RGB", (panel_size[0] * 3, panel_size[1] + header_height), (25, 29, 32))
    draw = ImageDraw.Draw(canvas)
    panels = [
        centered_panel(rgb, panel_size, (25, 29, 32)),
        centered_panel(alpha_panel, panel_size, (25, 29, 32)),
        centered_panel(support_overlay, panel_size, (25, 29, 32)),
    ]
    for index, (label, panel) in enumerate(zip(labels, panels)):
        offset = index * panel_size[0]
        draw.text((offset + 8, 8), label, fill=(235, 238, 240))
        canvas.paste(panel, (offset, header_height))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def patch_torch_pytree() -> None:
    """Keep the known PyTorch/transformers compatibility fix local to this tool."""
    import torch.utils._pytree as pytree

    original = pytree.register_pytree_node

    def register_compat(node_type: Any, flatten_fn: Any, unflatten_fn: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs.pop("flatten_with_keys_fn", None)
        kwargs.pop("serialized_type_name", None)
        kwargs.pop("to_dumpable_context", None)
        kwargs.pop("from_dumpable_context", None)
        return original(node_type, flatten_fn, unflatten_fn, *args, **kwargs)

    pytree.register_pytree_node = register_compat


def load_qwen(model_path: Path, processor_path: Path, attention_backend: str) -> tuple[Any, Any]:
    patch_torch_pytree()
    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(model_path),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation=attention_backend,
        local_files_only=True,
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(
        str(processor_path),
        min_pixels=65_536,
        max_pixels=524_288,
        local_files_only=True,
    )
    processor.image_processor.min_pixels = 65_536
    processor.image_processor.max_pixels = 524_288
    return model, processor


def extract_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    decoder = json.JSONDecoder()
    starts = [index for index, character in enumerate(text) if character == "{"]
    for start in starts:
        try:
            value, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value, None
    return None, "No JSON object found in the VLM response."


def looks_like_voxel_sequence(text: str) -> bool:
    """Detect the PhysX-Anything fine-tune's coordinate-only output mode."""
    tokens = re.findall(r"\b\d+(?:-\d+)?\b", text)
    if len(tokens) < 24:
        return False
    non_whitespace = re.sub(r"\s+", "", text)
    numeric_content = "".join(tokens).replace("-", "")
    return bool(non_whitespace) and len(numeric_content) / len(non_whitespace) >= 0.72


def normalized_box(value: Any) -> list[int] | None:
    if not isinstance(value, list) or len(value) != 4:
        return None
    try:
        box = [int(round(float(item))) for item in value]
    except (TypeError, ValueError):
        return None
    if any(item < 0 or item > 1000 for item in box) or box[2] <= box[0] or box[3] <= box[1]:
        return None
    return box


def validate_spec(spec: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    decision = spec.get("decision")
    allowed_decisions = {"accept_single_instance", "split_required", "reject"}
    if decision not in allowed_decisions:
        errors.append(f"invalid_decision:{decision!r}")
    try:
        count = int(spec.get("observed_same_category_instance_count"))
    except (TypeError, ValueError):
        count = 0
        errors.append("invalid_observed_same_category_instance_count")
    if count < 1:
        errors.append("observed_same_category_instance_count_must_be_positive")
    units = spec.get("asset_units")
    if not isinstance(units, list) or not units:
        errors.append("asset_units_must_be_a_nonempty_list")
        units = []
    cleaned_units: list[dict[str, Any]] = []
    for index, unit in enumerate(units):
        if not isinstance(unit, dict):
            errors.append(f"asset_unit_{index}_must_be_an_object")
            continue
        box = normalized_box(unit.get("normalized_bbox_xyxy"))
        if box is None:
            errors.append(f"asset_unit_{index}_has_invalid_normalized_bbox_xyxy")
            continue
        cleaned_unit = dict(unit)
        cleaned_unit["normalized_bbox_xyxy"] = box
        cleaned_units.append(cleaned_unit)
    if decision == "accept_single_instance" and (count != 1 or len(cleaned_units) != 1):
        errors.append("accept_single_instance_requires_exactly_one_observed_and_described_unit")
    if decision == "split_required" and count != len(cleaned_units):
        errors.append("split_required_requires_one_described_unit_per_observed_instance")
    generation_contract = spec.get("generation_contract")
    if not isinstance(generation_contract, dict):
        errors.append("generation_contract_must_be_an_object")
        generation_contract = {}
    validated = {
        "schema_version": 1,
        "kind": "video2mesh.instance_asset_vlm_spec",
        "object_id": request["object_id"],
        "category": request["category"],
        "input_contract": request["input_contract"],
        "decision": decision,
        "reason": str(spec.get("reason") or ""),
        "observed_same_category_instance_count": count,
        "asset_units": cleaned_units,
        "shared_structure": spec.get("shared_structure") if isinstance(spec.get("shared_structure"), list) else [],
        "excluded_content": spec.get("excluded_content") if isinstance(spec.get("excluded_content"), list) else [],
        "generation_contract": generation_contract,
        "generation_allowed": not errors and decision == "accept_single_instance",
    }
    return validated, errors


def run_review(model: Any, processor: Any, prompt: str, image_path: Path, max_new_tokens: int) -> str:
    from qwen_vl_utils import process_vision_info

    image = Image.open(image_path).convert("RGB")
    messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
    inputs = inputs.to(model.device)
    generated_ids = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
    trimmed = [output_ids[len(input_ids) :] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--processor-path", type=Path, required=True)
    parser.add_argument("--gpu-devices", default="", help="CUDA device list such as 4,5,6,7.")
    parser.add_argument("--attention-backend", default="flash_attention_2")
    parser.add_argument("--objects", nargs="*")
    parser.add_argument("--max-new-tokens", type=int, default=700)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.gpu_devices:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_devices
    manifest = read_json(args.input_manifest)
    prepared = manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared inputs in {args.input_manifest}")
    wanted = set(args.objects or [])
    jobs = [item for item in prepared if isinstance(item, dict) and (not wanted or item.get("object_id") in wanted)]
    if not jobs:
        raise ValueError("No prepared instances match --objects")
    model, processor = load_qwen(args.model_path.resolve(), args.processor_path.resolve(), args.attention_backend)
    output_root = args.output_root.resolve()
    result_dir = output_root / "vlm"
    review_dir = result_dir / "review_images"
    results: list[dict[str, Any]] = []
    for item in jobs:
        object_id = str(item["object_id"])
        request = read_json(Path(str(item["vlm_request_path"])))
        review_image = review_dir / f"{object_id}.png"
        compose_review_image(
            Path(str(item["rgb_path"])),
            Path(str(item["rgba_path"])),
            Path(str(item["projected_support_path"])),
            review_image,
        )
        raw_response = run_review(model, processor, str(request["prompt"]), review_image, args.max_new_tokens)
        raw_path = result_dir / f"{object_id}_raw.txt"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(raw_response + "\n", encoding="utf-8")
        parsed, parse_error = extract_json(raw_response)
        if parsed is None:
            output_mode = "unsupported_voxel_sequence" if looks_like_voxel_sequence(raw_response) else "invalid_non_json_response"
            validated = {
                "schema_version": 1,
                "kind": "video2mesh.instance_asset_vlm_spec",
                "object_id": object_id,
                "category": request["category"],
                "input_contract": request["input_contract"],
                "decision": "reject",
                "generation_allowed": False,
                "review_status": output_mode,
                "model_compatible_with_json_contract": False,
            }
            errors = [
                str(parse_error),
                "The supplied VLM did not emit a structured instance-review response; TRELLIS remains blocked.",
            ]
        else:
            validated, errors = validate_spec(parsed, request)
        validated["raw_response_path"] = str(raw_path)
        validated["review_image_path"] = str(review_image)
        validated["validation_errors"] = errors
        spec_path = result_dir / f"{object_id}_asset_spec.json"
        write_json(spec_path, validated)
        results.append(
            {
                "object_id": object_id,
                "category": request["category"],
                "status": validated.get("review_status") or ("reviewed" if not errors else "reviewed_with_validation_errors"),
                "decision": validated.get("decision"),
                "generation_allowed": validated["generation_allowed"],
                "spec_path": str(spec_path),
                "raw_response_path": str(raw_path),
                "review_image_path": str(review_image),
                "validation_errors": errors,
            }
        )
        print(
            f"reviewed {object_id}: decision={validated.get('decision')} "
            f"generation_allowed={validated['generation_allowed']}",
            flush=True,
        )
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "local_qwen2_5_vl_instance_contract_review_before_trellis",
        "input_manifest": str(args.input_manifest.resolve()),
        "model_path": str(args.model_path.resolve()),
        "processor_path": str(args.processor_path.resolve()),
        "gpu_devices": args.gpu_devices,
        "results": results,
    }
    report_path = result_dir / "vlm_asset_specs_manifest.json"
    write_json(report_path, report)
    allowed = sum(item["generation_allowed"] for item in results)
    print(f"reviewed={len(results)} generation_allowed={allowed} manifest={report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
