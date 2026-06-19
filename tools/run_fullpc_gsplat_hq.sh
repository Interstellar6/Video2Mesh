#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/run_fullpc_gsplat_hq.sh /path/to/exports/<run>

Run the highest currently supported in-repo Video2Mesh 3DGS baseline on a
project using the original MASt3R-SLAM full point cloud. This script does not
use point_cloud_10k.ply or other downsampled working clouds.

Optional environment overrides:
  PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  ITERATIONS=1200
  MAX_FRAMES=8
  WIDTH=480
  HEIGHT=270
  REGISTER=1
  RUN_NAME=fullpc_hq
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 1 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

PROJECT_ROOT="$1"
if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "[Video2Mesh] Project root not found: $PROJECT_ROOT" >&2
  exit 2
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if [[ -z "${PYTHON:-}" ]]; then
  if [[ -x /root/autodl-tmp/venvs/v2m-svpp/bin/python ]]; then
    PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  else
    PYTHON=python3
  fi
fi

ITERATIONS=${ITERATIONS:-1200}
MAX_FRAMES=${MAX_FRAMES:-8}
WIDTH=${WIDTH:-480}
HEIGHT=${HEIGHT:-270}
LOG_EVERY=${LOG_EVERY:-50}
REGISTER=${REGISTER:-1}
RUN_NAME=${RUN_NAME:-fullpc_hq_${ITERATIONS}iter_${MAX_FRAMES}f_${WIDTH}x${HEIGHT}}

FRAMES_DIR=${FRAMES_DIR:-"$PROJECT_ROOT/scene/mast3r_keyframes"}
if [[ ! -d "$FRAMES_DIR" ]]; then
  FRAMES_DIR="$PROJECT_ROOT/scene/frames"
fi
CAMERA_INFO=${CAMERA_INFO:-"$PROJECT_ROOT/scene/cameras/camera_info.json"}
POINT_CLOUD=${POINT_CLOUD:-"$PROJECT_ROOT/scene/reconstruction/point_cloud.ply"}
OUTPUT_DIR=${OUTPUT_DIR:-"$PROJECT_ROOT/scene/reconstruction/3dgs_real_${RUN_NAME}"}
PREVIEW_DIR=${PREVIEW_DIR:-"$PROJECT_ROOT/simulator_assets/gsplat_preview_real_${RUN_NAME}"}

export PATH=/root/autodl-tmp/venvs/v2m-svpp/bin:/root/miniconda3/bin:$PATH
export MAX_JOBS=${MAX_JOBS:-1}
export TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST:-8.9}

CUDA_TARGET=${CUDA_TARGET:-/root/miniconda3/targets/x86_64-linux}
export CPATH="$CUDA_TARGET/include:${CPATH:-}"
export CPLUS_INCLUDE_PATH="$CUDA_TARGET/include:${CPLUS_INCLUDE_PATH:-}"
export LIBRARY_PATH="$CUDA_TARGET/lib:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$CUDA_TARGET/lib:/root/miniconda3/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "$PROJECT_ROOT/logs" "$(dirname "$OUTPUT_DIR")" "$(dirname "$PREVIEW_DIR")"

if [[ ! -f "$CAMERA_INFO" ]]; then
  echo "[Video2Mesh] Missing camera info: $CAMERA_INFO" >&2
  exit 2
fi
if [[ ! -f "$POINT_CLOUD" ]]; then
  echo "[Video2Mesh] Missing full point cloud: $POINT_CLOUD" >&2
  exit 2
fi
if [[ "$(basename "$POINT_CLOUD")" =~ ^point_cloud_([0-9]+|[0-9]+k|10k|30k)\.ply$ ]]; then
  echo "[Video2Mesh] Refusing downsampled initialization cloud: $POINT_CLOUD" >&2
  exit 2
fi

register_flag=(--no-register)
if [[ "$REGISTER" == "1" || "$REGISTER" == "true" ]]; then
  register_flag=(--register --register-mode copy)
fi

echo "[Video2Mesh] project: $PROJECT_ROOT"
echo "[Video2Mesh] frames:  $FRAMES_DIR"
echo "[Video2Mesh] camera:  $CAMERA_INFO"
echo "[Video2Mesh] point cloud: $POINT_CLOUD"
echo "[Video2Mesh] output: $OUTPUT_DIR"
echo "[Video2Mesh] preview: $PREVIEW_DIR"
echo "[Video2Mesh] iterations=$ITERATIONS frames=$MAX_FRAMES size=${WIDTH}x${HEIGHT} register=$REGISTER"

"$PYTHON" -B -m video2mesh.cli train-gsplat \
  --project-root "$PROJECT_ROOT" \
  --frames-dir "$FRAMES_DIR" \
  --camera-info "$CAMERA_INFO" \
  --point-cloud "$POINT_CLOUD" \
  --output-dir "$OUTPUT_DIR" \
  --iterations "$ITERATIONS" \
  --max-frames "$MAX_FRAMES" \
  --max-points 0 \
  --device cuda \
  --width "$WIDTH" \
  --height "$HEIGHT" \
  --log-every "$LOG_EVERY" \
  "${register_flag[@]}"

"$PYTHON" -B -m video2mesh.cli render-gsplat-preview \
  --project-root "$PROJECT_ROOT" \
  --splat-ply "$OUTPUT_DIR/point_cloud/iteration_$ITERATIONS/point_cloud.ply" \
  --frames-dir "$FRAMES_DIR" \
  --camera-info "$CAMERA_INFO" \
  --output-dir "$PREVIEW_DIR" \
  --max-frames 6 \
  --width "$WIDTH" \
  --height "$HEIGHT" \
  --device cuda \
  --no-update-manifest

echo "[Video2Mesh] done"
echo "[Video2Mesh] train manifest: $OUTPUT_DIR/video2mesh_gsplat_train.json"
echo "[Video2Mesh] preview manifest: $PREVIEW_DIR/preview_manifest.json"
