"""Helpers for registering viewer-friendly PLY exports in project manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def alias_custom_viewer_export(
    exports: dict[str, Any],
    *,
    prefix: str | None,
    source_ply: Path | None,
    include_labels: bool,
) -> None:
    """Register a custom export under scene/semantic aliases when intent is clear."""
    custom_export = exports.get("custom")
    if not isinstance(custom_export, dict) or not custom_export.get("ok"):
        return
    custom_prefix = str(prefix or (source_ply.stem if source_ply else "")).lower()
    if include_labels or "semantic" in custom_prefix:
        exports["semantic"] = custom_export
    elif "scene" in custom_prefix:
        exports["scene"] = custom_export


def update_manifest_viewer_artifacts(manifest: dict[str, Any], manifest_path: Path, exports: dict[str, Any]) -> None:
    artifacts = manifest.setdefault("artifacts", {})
    artifacts["viewer_plys_manifest"] = str(manifest_path)

    scene_export = exports.get("scene")
    if isinstance(scene_export, dict) and scene_export.get("ok"):
        artifacts["scene_3dgs_point_cloud_ply"] = scene_export.get("point_cloud_ply")
        artifacts["scene_3dgs_supersplat_ply"] = scene_export.get("supersplat_ply")

    semantic_export = exports.get("semantic")
    if isinstance(semantic_export, dict) and semantic_export.get("ok"):
        artifacts["semantic_point_cloud_ply"] = semantic_export.get("point_cloud_ply")
        artifacts["semantic_supersplat_ply"] = semantic_export.get("supersplat_ply")


def current_requested_exports(exports: dict[str, Any], requested_exports: set[str]) -> dict[str, dict[str, Any]]:
    return {
        name: item
        for name, item in exports.items()
        if name in requested_exports and isinstance(item, dict)
    }
