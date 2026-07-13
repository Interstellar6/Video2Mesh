#!/usr/bin/env python3
"""Run PhysX-Anything VLM with known-object prompt guidance.

This is an experiment runner intended to be copied into an official
PhysX-Anything checkout. It keeps the upstream script intact while replacing
the generic VLM questions with a Video2Mesh object contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


DEFAULT_OVERALL_PROMPT = Path("dataset/overall_prompt.txt")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_torch_pytree() -> None:
    import torch.utils._pytree as pytree

    original = pytree.register_pytree_node

    def register_compat(node_type: Any, flatten_fn: Any, unflatten_fn: Any, *args: Any, **kwargs: Any) -> Any:
        kwargs.pop("flatten_with_keys_fn", None)
        kwargs.pop("serialized_type_name", None)
        kwargs.pop("to_dumpable_context", None)
        kwargs.pop("from_dumpable_context", None)
        return original(node_type, flatten_fn, unflatten_fn, *args, **kwargs)

    pytree.register_pytree_node = register_compat


def voxel_decode(indices: np.ndarray, size: int = 32) -> np.ndarray:
    indices = np.asarray(indices, dtype=np.int64).ravel()
    if indices.size == 0:
        return np.zeros((0, 3), dtype=np.int64)
    indices = indices.clip(0, size**3 - 1)
    x = (indices >> 10) & 31
    y = (indices >> 5) & 31
    z = indices & 31
    return np.stack([x, y, z], axis=1)


def dash_str_to_ints(text: str) -> np.ndarray:
    values: set[int] = set()
    for token in re.findall(r"\d+\s*-\s*\d+|\d+", text):
        if "-" in token:
            left, right = [int(item.strip()) for item in token.split("-", 1)]
            if left > right:
                left, right = right, left
            values.update(range(left, right + 1))
        else:
            values.add(int(token))
    return np.array(sorted(values), dtype=np.int64)


def add_turn(messages: list[dict[str, Any]], assistant_text: str, user_text: str) -> list[dict[str, Any]]:
    updated = list(messages)
    updated.append({"role": "assistant", "content": [{"type": "text", "text": assistant_text}]})
    updated.append({"role": "user", "content": [{"type": "text", "text": user_text}]})
    return updated


def generate_text(
    model: Any,
    processor: Any,
    messages: list[dict[str, Any]],
    max_new_tokens: int,
) -> str:
    from qwen_vl_utils import process_vision_info

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)
    generated_ids = model.generate(
        **inputs,
        do_sample=False,
        temperature=0,
        max_new_tokens=max_new_tokens,
    )
    trimmed = [out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def compact_list(values: Any) -> str:
    if isinstance(values, list):
        return ", ".join(str(item) for item in values)
    if values is None:
        return ""
    return str(values)


def build_overall_prompt(base_prompt: str, object_id: str, override: dict[str, Any]) -> str:
    target_name = str(override.get("target_name") or object_id)
    target_class = str(override.get("target_class") or override.get("category") or target_name)
    expected_parts = compact_list(override.get("expected_parts"))
    negative_categories = compact_list(override.get("negative_categories"))
    merge_policy = str(
        override.get("part_merge_policy")
        or "Use the fewest physically meaningful parts. Merge uncertain thin or isolated fragments into the nearest large fixed part."
    )
    static_policy = str(
        override.get("static_joint_policy")
        or "If the target is static furniture or a rigid object, put all parts into one fixed group with Type: E."
    )
    extra_notes = str(override.get("notes") or "")
    max_parts = override.get("max_parts")
    max_parts_line = f"Prefer no more than {int(max_parts)} parts." if isinstance(max_parts, int) else ""
    exact_parts = bool(override.get("exact_expected_parts", False))
    part_instruction = (
        f"Use exactly these expected parts when visible: {expected_parts}."
        if exact_parts and expected_parts
        else f"Prefer these expected parts when visible: {expected_parts}."
    )
    return "\n".join(
        [
            base_prompt.strip(),
            "",
            "Video2Mesh known-object override:",
            f"- object_id: {object_id}",
            f"- target name: {target_name}",
            f"- target class/category: {target_class}",
            "- Analyze only the target object inside the crop/mask. Ignore background, walls, floor, nearby furniture, occluders, and shadows.",
            f"- The Name and Category fields must describe the target as {target_name} / {target_class}; do not guess a different category.",
            f"- {part_instruction}" if expected_parts else "- Use a small set of physically meaningful parts.",
            f"- {max_parts_line}" if max_parts_line else "",
            f"- Forbidden or negative categories: {negative_categories}." if negative_categories else "",
            f"- Part merge policy: {merge_policy}",
            f"- Joint policy: {static_policy}",
            "- Avoid invented drawers, hinges, legs, handles, or movable joints unless they are clearly visible.",
            "- Keep the official output schema exactly. Do not add markdown, JSON, or commentary.",
            extra_notes,
        ]
    ).strip()


def build_coord_prompt(part_id: int, basic_info: str, override: dict[str, Any]) -> str:
    expected_parts = compact_list(override.get("expected_parts"))
    target_class = str(override.get("target_class") or override.get("category") or "")
    merge_policy = str(
        override.get("part_merge_policy")
        or "merge uncertain isolated fragments into the nearest large structural part"
    )
    return "\n".join(
        [
            f"Based on the structured description of l_{part_id}, generate its 3D voxel grid.",
            "Output only voxel numbers from 0 to 32767, using maximal consecutive runs such as 199-216. Do not output prose.",
            f"Target category: {target_class}.",
            f"Expected whole-object parts: {expected_parts}." if expected_parts else "",
            f"Part merge policy from the previous answer: {merge_policy}.",
            "Make this part spatially contiguous in the 32^3 voxel grid whenever possible.",
            "Avoid thin isolated shards, tiny floating islands, and disconnected noise.",
            "For static furniture and rigid objects, prefer coarse complete volumes over many small fragments.",
            "If a visible feature is uncertain, merge it into the nearest large fixed structural part rather than creating a separate island.",
        ]
    ).strip()


def build_seeded_basic_info(object_id: str, override: dict[str, Any]) -> str:
    seeded = override.get("seeded_basic_info")
    if isinstance(seeded, str) and seeded.strip():
        return seeded.strip() + "\n"
    target_name = str(override.get("target_name") or object_id)
    target_class = str(override.get("target_class") or override.get("category") or "Object")
    dimension = str(override.get("dimension") or "100*100*100")
    parts = override.get("parts")
    lines = [f"Name: {target_name}", f"Category: {target_class}", f"Dimension: {dimension}", "Parts:"]
    if isinstance(parts, list) and parts:
        for index, raw in enumerate(parts):
            if not isinstance(raw, dict):
                continue
            part_name = str(raw.get("name") or f"part_{index}")
            affordance = str(raw.get("affordance_rank") or index + 1)
            material = str(raw.get("material") or override.get("default_material") or "Rigid material")
            density = str(raw.get("density") or override.get("default_density") or "0.7 g/cm^3")
            youngs = str(raw.get("youngs_modulus") or override.get("default_youngs_modulus") or "10.0")
            poisson = str(raw.get("poisson_ratio") or override.get("default_poisson_ratio") or "0.3")
            description = str(raw.get("description") or f"A visible {part_name} of the target object.")
            lines.append(f"l_{index}: {part_name}, {affordance}, {material}, {density}, {youngs}, {poisson}, {description}")
    else:
        for index, part_name in enumerate(override.get("expected_parts") or ["main body"]):
            lines.append(
                f"l_{index}: {part_name}, {index + 1}, Rigid material, 0.7 g/cm^3, 10.0, 0.3, "
                f"A visible {part_name} of the target object."
            )
    part_ids = ", ".join(f"'l_{index}'" for index in range(sum(1 for line in lines if re.match(r"^l_\d+:", line))))
    lines.extend(["Group_info:", f"group_0: [{part_ids}]; Type: E; Params: N/A"])
    return "\n".join(lines).strip() + "\n"


def parse_basic_info(text: str) -> dict[str, Any]:
    name = ""
    category = ""
    parts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("name:"):
            name = stripped.split(":", 1)[1].strip()
        elif stripped.lower().startswith("category:"):
            category = stripped.split(":", 1)[1].strip()
        elif re.match(r"^l_\d+\s*:", stripped):
            parts.append(stripped)
    return {"name": name, "category": category, "part_count": len(parts), "parts": parts}


def component_stats(voxels: np.ndarray) -> dict[str, Any]:
    if voxels.size == 0:
        return {
            "voxel_count": 0,
            "component_count": 0,
            "largest_component_voxels": 0,
            "largest_component_ratio": 0.0,
            "bbox_min": None,
            "bbox_max": None,
        }
    coords = {tuple(int(v) for v in row) for row in voxels.tolist()}
    remaining = set(coords)
    components: list[int] = []
    offsets = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    while remaining:
        start = remaining.pop()
        queue: deque[tuple[int, int, int]] = deque([start])
        count = 1
        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in offsets:
                neighbor = (x + dx, y + dy, z + dz)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    count += 1
        components.append(count)
    largest = max(components) if components else 0
    return {
        "voxel_count": int(len(coords)),
        "component_count": int(len(components)),
        "largest_component_voxels": int(largest),
        "largest_component_ratio": float(largest / len(coords)) if coords else 0.0,
        "bbox_min": [int(v) for v in voxels.min(axis=0)],
        "bbox_max": [int(v) for v in voxels.max(axis=0)],
    }


def summarize_output(save_dir: Path) -> dict[str, Any]:
    basic_path = save_dir / "basic_info.txt"
    basic = parse_basic_info(basic_path.read_text(encoding="utf-8")) if basic_path.is_file() else {}
    part_stats = []
    for path in sorted(save_dir.glob("ind_*.npy"), key=lambda item: int(re.search(r"ind_(\d+)", item.stem).group(1))):
        voxels = np.load(path)
        item = component_stats(voxels)
        item["part_id"] = int(re.search(r"ind_(\d+)", path.stem).group(1))
        part_stats.append(item)
    allind_path = save_dir / "allind.npy"
    all_stats = component_stats(np.load(allind_path)) if allind_path.is_file() else {}
    return {"basic_info": basic, "allind": all_stats, "parts": part_stats}


def load_model(args: argparse.Namespace) -> tuple[Any, Any]:
    patch_torch_pytree()
    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(args.ckpt),
        torch_dtype=torch.bfloat16,
        attn_implementation=args.attention_backend,
        device_map=args.device_map,
        local_files_only=args.local_files_only,
    )
    min_pixels = int(args.min_pixels)
    max_pixels = int(args.max_pixels)
    processor = AutoProcessor.from_pretrained(
        str(args.processor),
        min_pixels=min_pixels,
        max_pixels=max_pixels,
        local_files_only=args.local_files_only,
    )
    processor.image_processor.min_pixels = min_pixels
    processor.image_processor.max_pixels = max_pixels
    processor.image_processor.size["shortest_edge"] = min_pixels
    processor.image_processor.size["longest_edge"] = max_pixels
    return model, processor


def image_id(path: Path) -> str:
    return path.stem


def select_override(overrides: dict[str, Any], object_id: str) -> dict[str, Any]:
    raw = overrides.get(object_id) or overrides.get("objects", {}).get(object_id)
    if not isinstance(raw, dict):
        raise KeyError(f"No prompt override found for {object_id}")
    return raw


def run_one(
    args: argparse.Namespace,
    model: Any,
    processor: Any,
    image_path: Path,
    override: dict[str, Any],
    base_prompt: str,
) -> dict[str, Any]:
    object_id = str(override.get("output_id") or image_id(image_path))
    save_dir = args.output_root / object_id
    save_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
    if args.remove_bg:
        from rembg import remove

        image = remove(image).convert("RGB")
    prompt = build_overall_prompt(base_prompt, object_id, override)
    (save_dir / "prompt_overall.txt").write_text(prompt + "\n", encoding="utf-8")
    messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
    if args.seed_basic_from_overrides:
        basic_info = build_seeded_basic_info(object_id, override)
        (save_dir / "basic_info_source.txt").write_text("seeded_from_override\n", encoding="utf-8")
    else:
        basic_info = generate_text(model, processor, messages, args.max_new_tokens)
        (save_dir / "basic_info_source.txt").write_text("vlm_generated\n", encoding="utf-8")
    (save_dir / "basic_info.txt").write_text(basic_info, encoding="utf-8")
    parsed = parse_basic_info(basic_info)
    all_parts: list[np.ndarray] = []
    for part_id in range(int(parsed["part_count"])):
        coord_prompt = build_coord_prompt(part_id, basic_info, override)
        (save_dir / f"prompt_coord_{part_id}.txt").write_text(coord_prompt + "\n", encoding="utf-8")
        output = generate_text(model, processor, add_turn(messages, basic_info, coord_prompt), args.max_new_tokens)
        (save_dir / f"coord_{part_id}.txt").write_text(output, encoding="utf-8")
        indices = dash_str_to_ints(output)
        voxels = voxel_decode(indices)
        np.save(save_dir / f"ind_{part_id}.npy", voxels)
        all_parts.append(voxels)
        if args.save_part_ply:
            import trimesh

            trimesh.points.PointCloud(voxels).export(save_dir / f"ind_{part_id}.ply")
        print(f"[prompt-guided] {object_id} l_{part_id}: {len(voxels)} voxels")
    if all_parts:
        np.save(save_dir / "allind.npy", np.concatenate(all_parts, axis=0))
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "physx_anything_known_object_prompt_guided_vlm",
        "image": str(image_path),
        "output_dir": str(save_dir),
        "override": override,
        "seed_basic_from_overrides": bool(args.seed_basic_from_overrides),
        "summary": summarize_output(save_dir),
    }
    if args.reference_root:
        reference_dir = args.reference_root / object_id.replace("_prompted", "")
        if reference_dir.is_dir():
            report["reference_dir"] = str(reference_dir)
            report["reference_summary"] = summarize_output(reference_dir)
    write_json(save_dir / "prompt_guided_report.json", report)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("test_demo_prompted"))
    parser.add_argument("--overrides", type=Path, required=True)
    parser.add_argument("--object-id", action="append", help="Image stem to process. Repeatable. Defaults to all overrides present in demo-path.")
    parser.add_argument("--overall-prompt", type=Path, default=DEFAULT_OVERALL_PROMPT)
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--ckpt", type=Path, default=Path("./pretrain/vlm"))
    parser.add_argument("--processor", type=Path, default=Path("Qwen/Qwen2.5-VL-7B-Instruct"))
    parser.add_argument("--attention-backend", default="flash_attention_2")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--local-files-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--min-pixels", type=int, default=65_536)
    parser.add_argument("--max-pixels", type=int, default=262_144)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--remove-bg", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--save-part-ply", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--seed-basic-from-overrides",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip the first VLM description turn and feed a schema-valid basic_info from the override.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    overrides = read_json(args.overrides)
    base_prompt = args.overall_prompt.read_text(encoding="utf-8")
    image_paths = {path.stem: path for path in sorted(args.demo_path.iterdir()) if path.suffix.lower() in {".png", ".jpg", ".jpeg"}}
    selected = args.object_id or sorted(set(image_paths) & set(overrides.get("objects", overrides).keys()))
    if not selected:
        raise ValueError("No selected objects. Pass --object-id or add matching override keys.")
    model, processor = load_model(args)
    reports = []
    for object_id in selected:
        if object_id not in image_paths:
            raise FileNotFoundError(f"Missing demo image for {object_id} in {args.demo_path}")
        override = dict(select_override(overrides, object_id))
        override.setdefault("output_id", f"{object_id}_prompted")
        reports.append(run_one(args, model, processor, image_paths[object_id], override, base_prompt))
    write_json(args.output_root / "prompt_guided_index.json", {"reports": reports})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
