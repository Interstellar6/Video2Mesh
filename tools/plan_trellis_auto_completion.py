#!/usr/bin/env python3
"""Plan evidence-aware prompt completion and reuse for TRELLIS object assets."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_STRATEGIES = {"reuse_baseline", "prompt_complete", "prompt_split", "external_split", "reject"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def evidence_tier(item: dict[str, Any], thresholds: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    width = int(item.get("bbox_width") or 0)
    height = int(item.get("bbox_height") or 0)
    short_side = min(width, height)
    alpha_pixels = int(item.get("alpha_pixels") or 0)
    support_ratio = float(item.get("support_ratio") or 0.0)
    low_detail_input = bool(item.get("low_detail_input", False))
    high = (
        short_side >= int(thresholds.get("high_min_short_side", 144))
        and alpha_pixels >= int(thresholds.get("high_min_alpha_pixels", 8000))
        and support_ratio >= float(thresholds.get("high_min_support_ratio", 0.75))
    )
    medium = (
        short_side >= int(thresholds.get("medium_min_short_side", 80))
        and alpha_pixels >= int(thresholds.get("medium_min_alpha_pixels", 2000))
        and support_ratio >= float(thresholds.get("medium_min_support_ratio", 0.45))
    )
    tier = "low" if low_detail_input else "high" if high else "medium" if medium else "low"
    return tier, {
        "tier": tier,
        "bbox_width": width,
        "bbox_height": height,
        "short_side": short_side,
        "alpha_pixels": alpha_pixels,
        "support_ratio": support_ratio,
        "low_detail_input": low_detail_input,
    }


def completion_fidelity(strategy: str, tier: str) -> str:
    if strategy == "reuse_baseline":
        return "scan_evidence_preserving"
    if strategy == "external_split":
        return "prompt_completed_external_split"
    if strategy == "prompt_split":
        return "prompt_completed_instance_split"
    if strategy == "prompt_complete" and tier == "low":
        return "category_proxy_from_low_detail_evidence"
    if strategy == "prompt_complete":
        return "prompt_completed_from_partial_evidence"
    return "rejected"


def completion_prompt(category_policy: dict[str, Any], background: str) -> str:
    subject = str(category_policy.get("subject") or "physical object")
    view = str(category_policy.get("view") or "Centered front three-quarter catalog view showing the complete object.")
    completion = str(category_policy.get("completion") or "Complete only missing or occluded parts conservatively.")
    avoid = str(category_policy.get("avoid") or "background structure, nearby objects, duplicate parts")
    return " ".join(
        [
            "Use case: precise-object-edit.",
            "Image 1 is the edit target: a segmented object observation from an indoor scan that may be partial, occluded, or truncated.",
            f"Create a clean catalog reference of exactly one complete independent {subject}.",
            "Preserve all visible identity cues, colors, materials, proportions, surface profiles, and distinctive parts from Image 1.",
            "Do not redesign visible evidence. Complete only unseen portions by conservative symmetry and category-consistent continuation.",
            completion,
            view,
            "The whole object must fit inside the image with generous padding and no crop.",
            f"Place it on a perfectly flat solid {background} chroma-key background.",
            "The background must have no shadow, floor plane, gradient, texture, reflection, text, or watermark.",
            f"Remove and do not generate: {avoid}.",
        ]
    )


def merged_policy(category_policy: dict[str, Any], object_override: dict[str, Any]) -> dict[str, Any]:
    result = dict(category_policy)
    result.update(object_override)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--policy-config", type=Path, required=True)
    parser.add_argument("--source-image-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--objects", nargs="*")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_manifest = read_json(args.input_manifest)
    prepared = source_manifest.get("prepared")
    if not isinstance(prepared, list):
        raise ValueError(f"Missing prepared list in {args.input_manifest}")
    policy = read_json(args.policy_config)
    categories = policy.get("categories")
    object_overrides = policy.get("objects", {})
    thresholds = policy.get("evidence_thresholds", {})
    provider = policy.get("provider", {})
    if not isinstance(categories, dict) or not isinstance(object_overrides, dict):
        raise ValueError("Policy config must contain category and object mappings")
    if not isinstance(thresholds, dict) or not isinstance(provider, dict):
        raise ValueError("Policy config has invalid evidence_thresholds or provider")
    provider_name = str(provider.get("name") or "external_image_editor")
    quality = str(provider.get("quality") or "medium")
    background = str(provider.get("background") or "#ff00ff")
    wanted = set(args.objects or [])
    source_image_dir = args.source_image_dir.resolve()
    output_root = args.output_root.resolve()
    plan_dir = output_root / "plan"
    items: list[dict[str, Any]] = []
    reference_objects: dict[str, dict[str, Any]] = {}
    edit_jobs: list[dict[str, Any]] = []
    generation_items: list[dict[str, Any]] = []

    def add_prompt_job(
        asset_id: str,
        source_item: dict[str, Any],
        applied_policy: dict[str, Any],
        local_source: Path,
    ) -> dict[str, Any]:
        geometry_contract = applied_policy.get("geometry_contract")
        if not isinstance(geometry_contract, dict):
            raise ValueError(f"Missing geometry contract for prompt-completed object {asset_id}")
        prompt = completion_prompt(applied_policy, background)
        expected_subject = str(applied_policy.get("expected_subject") or f"one complete {source_item.get('category')}")
        size = str(applied_policy.get("size") or "1024x1024")
        reference_objects[asset_id] = {
            "provider": provider_name,
            "prompt": prompt,
            "expected_subject": expected_subject,
            "geometry_contract": dict(geometry_contract),
        }
        edit_jobs.append({
            "object_id": asset_id,
            "source_image": str(local_source),
            "prompt": prompt,
            "provider": provider_name,
            "quality": quality,
            "size": size,
            "raw_output_filename": f"{asset_id}.png",
            "rgba_output_filename": f"{asset_id}.png",
        })
        generation_item = dict(source_item)
        generation_item["object_id"] = asset_id
        generation_items.append(generation_item)
        return {
            "prompt": prompt,
            "expected_subject": expected_subject,
            "provider": provider_name,
            "quality": quality,
            "size": size,
        }

    for raw_item in prepared:
        if not isinstance(raw_item, dict):
            continue
        object_id = str(raw_item.get("object_id") or "")
        if not object_id or (wanted and object_id not in wanted):
            continue
        category = str(raw_item.get("category") or "")
        category_policy = categories.get(category)
        if not isinstance(category_policy, dict):
            category_policy = {"strategy": "reject", "reason": "unsupported_category"}
        object_override = object_overrides.get(object_id, {})
        if not isinstance(object_override, dict):
            raise ValueError(f"Object override must be an object: {object_id}")
        applied = merged_policy(category_policy, object_override)
        strategy = str(applied.get("strategy") or "reject")
        if strategy not in SUPPORTED_STRATEGIES:
            raise ValueError(f"Unsupported strategy for {object_id}: {strategy}")
        tier, evidence = evidence_tier(raw_item, thresholds)
        local_source = source_image_dir / f"{object_id}_rgba.png"
        item: dict[str, Any] = {
            "object_id": object_id,
            "name": raw_item.get("name"),
            "category": category,
            "strategy": strategy,
            "evidence": evidence,
            "fidelity_tier": completion_fidelity(strategy, tier),
            "source_manifest_rgba_path": raw_item.get("rgba_path"),
            "local_source_rgba_path": str(local_source),
            "geometry_contract": applied.get("geometry_contract"),
        }
        if strategy == "prompt_complete":
            if not local_source.is_file():
                raise FileNotFoundError(f"Missing local source image for {object_id}: {local_source}")
            item.update(add_prompt_job(object_id, raw_item, applied, local_source))
        elif strategy == "prompt_split":
            if not local_source.is_file():
                raise FileNotFoundError(f"Missing local source image for {object_id}: {local_source}")
            units = applied.get("units")
            if not isinstance(units, list) or not units:
                raise ValueError(f"Missing prompt_split units for {object_id}")
            replacement_ids: list[str] = []
            split_jobs: list[dict[str, Any]] = []
            for unit in units:
                if not isinstance(unit, dict):
                    raise ValueError(f"Invalid prompt_split unit for {object_id}")
                unit_id = str(unit.get("unit_id") or "")
                if not unit_id:
                    raise ValueError(f"Missing unit_id for prompt_split {object_id}")
                child_id = f"{object_id}_{unit_id}"
                child_policy = merged_policy(applied, unit)
                child_item = dict(raw_item)
                child_item["object_id"] = child_id
                child_item["parent_object_id"] = object_id
                child_item["name"] = f"{raw_item.get('name') or object_id} {unit_id}"
                job = add_prompt_job(child_id, child_item, child_policy, local_source)
                replacement_ids.append(child_id)
                split_jobs.append({"object_id": child_id, **job})
            item["replacement_ids"] = replacement_ids
            item["split_jobs"] = split_jobs
        elif strategy == "external_split":
            replacements = applied.get("replacement_ids")
            if not isinstance(replacements, list) or not all(isinstance(value, str) and value for value in replacements):
                raise ValueError(f"Missing replacement_ids for external split {object_id}")
            item["replacement_ids"] = list(replacements)
        elif strategy == "reject":
            item["reason"] = str(applied.get("reason") or "policy_rejected")
        items.append(item)

    if not items:
        raise ValueError("No objects were planned")
    reference_config = {
        "schema_version": 1,
        "kind": "video2mesh.trellis_prompted_reference_config",
        "provider": provider_name,
        "objects": reference_objects,
    }
    jobs_manifest = {
        "schema_version": 1,
        "kind": "video2mesh.image_edit_jobs",
        "provider": provider_name,
        "background": background,
        "job_count": len(edit_jobs),
        "jobs": edit_jobs,
    }
    prompt_input_manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "auto_completion_prompt_generation_items",
        "source_input_manifest": str(args.input_manifest.resolve()),
        "prepared": generation_items,
    }
    plan = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "evidence_aware_category_policy_for_trellis_object_completion",
        "source_input_manifest": str(args.input_manifest.resolve()),
        "policy_config": str(args.policy_config.resolve()),
        "source_image_dir": str(source_image_dir),
        "object_count": len(items),
        "prompt_completion_count": len(edit_jobs),
        "items": items,
    }
    write_json(plan_dir / "completion_plan.json", plan)
    write_json(plan_dir / "reference_config.json", reference_config)
    write_json(plan_dir / "image_edit_jobs.json", jobs_manifest)
    write_json(plan_dir / "prompt_input_manifest.json", prompt_input_manifest)
    counts = {strategy: sum(item["strategy"] == strategy for item in items) for strategy in sorted(SUPPORTED_STRATEGIES)}
    print(f"planned={len(items)} strategies={counts} edit_jobs={len(edit_jobs)} output={plan_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
