"""Small 3DGS path and command helpers used by the Video2Mesh CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _safe_read_json(path: Path | None) -> Any | None:
    if path is None or not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _provider_slug(value: str, fallback: str = "object") -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or fallback


def find_latest_splat_ply(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.rglob("point_cloud.ply"), key=lambda item: (len(str(item)), str(item)))
    if not candidates:
        candidates = sorted(path.rglob("*.ply"), key=lambda item: (len(str(item)), str(item)))
    if not candidates:
        raise FileNotFoundError(f"No PLY file found under {path}")

    def iteration_key(item: Path) -> tuple[int, str]:
        match = re.search(r"iteration[_-]?(\d+)", str(item))
        return (int(match.group(1)) if match else -1, str(item))

    return sorted(candidates, key=iteration_key)[-1]


def local_registered_path(src: Path, dst: Path, path: Path) -> Path:
    if src.is_dir():
        try:
            return dst / path.resolve().relative_to(src.resolve())
        except Exception:
            return path
    if path.resolve() == src.resolve():
        return dst / src.name
    return path


def gsplat_viewer_companion_paths(splat_ply: Path) -> dict[str, Path]:
    stem = splat_ply.with_suffix("")
    return {
        "point_cloud_ply": stem.parent / f"{stem.name}_point_cloud.ply",
        "supersplat_ply": stem.parent / f"{stem.name}_supersplat.ply",
    }


def gsplat_train_manifest_for_output(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "video2mesh_gsplat_train.json"
    data = _safe_read_json(manifest_path)
    return data if isinstance(data, dict) else {}


def default_3dgs_command_template(provider: str) -> str:
    normalized = _provider_slug(provider)
    if normalized in {"graphdeco", "gaussian-splatting", "graphdeco-gaussian-splatting"}:
        return "python train.py -s {source_path} -m {output_path}"
    if normalized in {"nerfstudio", "splatfacto", "ns-splatfacto"}:
        return "ns-train splatfacto --data {source_path} --output-dir {output_path}"
    if normalized in {"gsplat", "full-gsplat"}:
        return "python train_gsplat_full.py --data {source_path} --output {output_path}"
    return "echo Fill in external 3DGS command for provider={provider} source={source_path} output={output_path}"


def gsplat_result_has_ply(path: Path) -> bool:
    try:
        find_latest_splat_ply(path)
        return True
    except Exception:
        return False
