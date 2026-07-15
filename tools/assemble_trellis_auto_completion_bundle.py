#!/usr/bin/env python3
"""Assemble accepted baseline, prompt-completed, and externally split TRELLIS assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def qa_index(summary_path: Path) -> dict[str, dict[str, Any]]:
    summary = read_json(summary_path)
    results = summary.get("results")
    if not isinstance(results, list):
        raise ValueError(f"Missing QA results in {summary_path}")
    indexed: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            continue
        source = result.get("source_ply")
        if not isinstance(source, str):
            continue
        object_id = Path(source).stem.removesuffix("_trellis_gaussian")
        indexed[object_id] = result
    return indexed


def accepted_asset(
    asset_id: str,
    parent_object_id: str,
    category: str,
    source_kind: str,
    fidelity_tier: str,
    output_dir: Path,
    qa: dict[str, dict[str, Any]],
    final_dir: Path,
) -> dict[str, Any]:
    source_ply = output_dir / f"{asset_id}_trellis_gaussian.ply"
    report = qa.get(asset_id)
    if report is None:
        return {
            "asset_id": asset_id,
            "parent_object_id": parent_object_id,
            "category": category,
            "source_kind": source_kind,
            "fidelity_tier": fidelity_tier,
            "status": "blocked",
            "reason": "missing_qa_result",
        }
    if report.get("status") != "passed":
        return {
            "asset_id": asset_id,
            "parent_object_id": parent_object_id,
            "category": category,
            "source_kind": source_kind,
            "fidelity_tier": fidelity_tier,
            "status": "blocked",
            "reason": "qa_failed",
            "qa": report,
        }
    if not source_ply.is_file() or source_ply.stat().st_size <= 0:
        return {
            "asset_id": asset_id,
            "parent_object_id": parent_object_id,
            "category": category,
            "source_kind": source_kind,
            "fidelity_tier": fidelity_tier,
            "status": "blocked",
            "reason": "missing_output_ply",
            "expected_source_ply": str(source_ply),
        }
    final_dir.mkdir(parents=True, exist_ok=True)
    destination = final_dir / source_ply.name
    shutil.copy2(source_ply, destination)
    status = "accepted_with_fidelity_caveat" if "category_proxy" in fidelity_tier else "accepted"
    return {
        "asset_id": asset_id,
        "parent_object_id": parent_object_id,
        "category": category,
        "source_kind": source_kind,
        "fidelity_tier": fidelity_tier,
        "status": status,
        "source_ply": str(source_ply),
        "final_ply": str(destination),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "vertex_count": report.get("vertex_count"),
        "file_status": report.get("file_status"),
        "geometry": report.get("geometry"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completion-plan", type=Path, required=True)
    parser.add_argument("--baseline-output-dir", type=Path, required=True)
    parser.add_argument("--baseline-qa", type=Path, required=True)
    parser.add_argument("--generated-output-dir", type=Path, required=True)
    parser.add_argument("--generated-qa", type=Path, action="append", required=True)
    parser.add_argument("--external-output-dir", type=Path, required=True)
    parser.add_argument("--external-qa", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = read_json(args.completion_plan)
    items = plan.get("items")
    if not isinstance(items, list):
        raise ValueError(f"Missing completion plan items in {args.completion_plan}")
    baseline_qa = qa_index(args.baseline_qa)
    generated_qa: dict[str, dict[str, Any]] = {}
    for summary_path in args.generated_qa:
        generated_qa.update(qa_index(summary_path))
    external_qa = qa_index(args.external_qa)
    output_root = args.output_root.resolve()
    final_dir = output_root / "final_assets"
    results: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        object_id = str(item.get("object_id") or "")
        category = str(item.get("category") or "")
        strategy = str(item.get("strategy") or "reject")
        fidelity = str(item.get("fidelity_tier") or "unknown")
        if strategy == "reuse_baseline":
            results.append(accepted_asset(
                object_id,
                object_id,
                category,
                "baseline_scan_conditioned",
                fidelity,
                args.baseline_output_dir,
                baseline_qa,
                final_dir,
            ))
        elif strategy == "prompt_complete":
            results.append(accepted_asset(
                object_id,
                object_id,
                category,
                "prompt_completed_reference",
                fidelity,
                args.generated_output_dir,
                generated_qa,
                final_dir,
            ))
        elif strategy == "prompt_split":
            replacement_ids = item.get("replacement_ids")
            if not isinstance(replacement_ids, list):
                replacement_ids = []
            for replacement_id in replacement_ids:
                results.append(accepted_asset(
                    str(replacement_id),
                    object_id,
                    category,
                    "prompt_completed_instance_split",
                    fidelity,
                    args.generated_output_dir,
                    generated_qa,
                    final_dir,
                ))
            if not replacement_ids:
                results.append({
                    "asset_id": object_id,
                    "parent_object_id": object_id,
                    "category": category,
                    "source_kind": "prompt_completed_instance_split",
                    "fidelity_tier": fidelity,
                    "status": "blocked",
                    "reason": "no_replacement_ids",
                })
        elif strategy == "external_split":
            replacement_ids = item.get("replacement_ids")
            if not isinstance(replacement_ids, list):
                replacement_ids = []
            for replacement_id in replacement_ids:
                results.append(accepted_asset(
                    str(replacement_id),
                    object_id,
                    category,
                    "external_instance_split",
                    fidelity,
                    args.external_output_dir,
                    external_qa,
                    final_dir,
                ))
            if not replacement_ids:
                results.append({
                    "asset_id": object_id,
                    "parent_object_id": object_id,
                    "category": category,
                    "source_kind": "external_instance_split",
                    "fidelity_tier": fidelity,
                    "status": "blocked",
                    "reason": "no_replacement_ids",
                })
        else:
            results.append({
                "asset_id": object_id,
                "parent_object_id": object_id,
                "category": category,
                "source_kind": "none",
                "fidelity_tier": fidelity,
                "status": "blocked",
                "reason": str(item.get("reason") or "completion_policy_rejected"),
            })

    accepted_statuses = {"accepted", "accepted_with_fidelity_caveat"}
    accepted_count = sum(result.get("status") in accepted_statuses for result in results)
    blocked_count = len(results) - accepted_count
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "fail_closed_trellis_auto_completion_asset_assembly",
        "completion_plan": str(args.completion_plan.resolve()),
        "asset_count": len(results),
        "accepted_count": accepted_count,
        "accepted_with_fidelity_caveat_count": sum(
            result.get("status") == "accepted_with_fidelity_caveat" for result in results
        ),
        "blocked_count": blocked_count,
        "assets": results,
    }
    write_json(output_root / "auto_completion_asset_manifest.json", manifest)
    print(f"assets={len(results)} accepted={accepted_count} blocked={blocked_count} output={output_root}")
    return 1 if blocked_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
