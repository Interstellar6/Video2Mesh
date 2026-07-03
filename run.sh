#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash run.sh /path/to/video.mp4

If no video is passed, run.sh uses VIDEO=/path/to/video.mp4 or the first
video found under dataset/ or inputs/.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

VIDEO_INPUT="${1:-${VIDEO:-}}"
if [[ -z "$VIDEO_INPUT" ]]; then
  VIDEO_INPUT="$(find "$ROOT/dataset" "$ROOT/inputs" -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' \) 2>/dev/null | sort | head -n 1 || true)"
fi

if [[ -z "$VIDEO_INPUT" ]]; then
  echo "[Video2Mesh] No input video found." >&2
  usage
  exit 2
fi

if [[ ! -f "$VIDEO_INPUT" ]]; then
  echo "[Video2Mesh] Video not found: $VIDEO_INPUT" >&2
  exit 2
fi

export VIDEO2MESH_ROOT="${VIDEO2MESH_ROOT:-$ROOT}"
export RECONSTRUCT_SCENE_MESHES="${RECONSTRUCT_SCENE_MESHES:-1}"
export TRANSFER_SCENE_MESH_SEMANTICS="${TRANSFER_SCENE_MESH_SEMANTICS:-1}"
export SPLIT_SCENE_MESH_BY_SEMANTICS="${SPLIT_SCENE_MESH_BY_SEMANTICS:-1}"
export SCENE_MESH_SEMANTIC_ROUTE="${SCENE_MESH_SEMANTIC_ROUTE:-local}"

exec bash "$ROOT/tools/run_video2mesh_quick.sh" "$VIDEO_INPUT"
