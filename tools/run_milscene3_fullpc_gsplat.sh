#!/usr/bin/env bash
set -euo pipefail

# Reproduce the milscene3 full-point-cloud minimal gsplat baseline.
# Run this on the AutoDL/SeetaCloud GPU server from the Video2Mesh repo root.
#
# The important contract is --max-points 0 with scene/reconstruction/point_cloud.ply:
# it uses the original MASt3R-SLAM point cloud as Gaussian initialization, not the
# downsampled point_cloud_30000.ply working cloud.

PROJECT_ROOT=${PROJECT_ROOT:-/root/autodl-tmp/workspace/Video2Mesh/exports/milscene3_full_20260618_124804}
if [[ -z "${PYTHON:-}" ]]; then
  if [[ -x /root/autodl-tmp/venvs/v2m-svpp/bin/python ]]; then
    PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  else
    PYTHON=python3
  fi
fi

ITERATIONS=${ITERATIONS:-500}
MAX_FRAMES=${MAX_FRAMES:-6}
WIDTH=${WIDTH:-480}
HEIGHT=${HEIGHT:-270}
LOG_EVERY=${LOG_EVERY:-50}
REGISTER=${REGISTER:-0}

RUN_NAME=${RUN_NAME:-fullpc_${ITERATIONS}iter_${MAX_FRAMES}f_${WIDTH}x${HEIGHT}}
OUTPUT_DIR=${OUTPUT_DIR:-"$PROJECT_ROOT/scene/reconstruction/3dgs_real_${RUN_NAME}"}
PREVIEW_DIR=${PREVIEW_DIR:-"$PROJECT_ROOT/simulator_assets/gsplat_preview_real_${RUN_NAME}"}

FRAMES_DIR=${FRAMES_DIR:-"$PROJECT_ROOT/scene/mast3r_keyframes"}
CAMERA_INFO=${CAMERA_INFO:-"$PROJECT_ROOT/scene/cameras/camera_info.json"}
POINT_CLOUD=${POINT_CLOUD:-"$PROJECT_ROOT/scene/reconstruction/point_cloud.ply"}
ALLOW_DOWNSAMPLED_POINT_CLOUD=${ALLOW_DOWNSAMPLED_POINT_CLOUD:-0}

export PATH=/root/autodl-tmp/venvs/v2m-svpp/bin:/root/miniconda3/bin:$PATH
export MAX_JOBS=${MAX_JOBS:-1}
export TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCH_LIST:-8.9}

CUDA_TARGET=${CUDA_TARGET:-/root/miniconda3/targets/x86_64-linux}
export CPATH="$CUDA_TARGET/include:${CPATH:-}"
export CPLUS_INCLUDE_PATH="$CUDA_TARGET/include:${CPLUS_INCLUDE_PATH:-}"
export LIBRARY_PATH="$CUDA_TARGET/lib:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$CUDA_TARGET/lib:/root/miniconda3/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "$PROJECT_ROOT/logs" "$(dirname "$OUTPUT_DIR")" "$(dirname "$PREVIEW_DIR")"

register_flag=(--no-register)
if [[ "$REGISTER" == "1" || "$REGISTER" == "true" ]]; then
  register_flag=(--register --register-mode copy)
fi

echo "[Video2Mesh] project: $PROJECT_ROOT"
echo "[Video2Mesh] output:  $OUTPUT_DIR"
echo "[Video2Mesh] preview: $PREVIEW_DIR"
echo "[Video2Mesh] point cloud: $POINT_CLOUD"
echo "[Video2Mesh] iterations=$ITERATIONS frames=$MAX_FRAMES size=${WIDTH}x${HEIGHT} register=$REGISTER"

if [[ "$ALLOW_DOWNSAMPLED_POINT_CLOUD" != "1" && "$(basename "$POINT_CLOUD")" =~ ^point_cloud_([0-9]+|[0-9]+k|10k|30k)\.ply$ ]]; then
  echo "[Video2Mesh] Refusing downsampled initialization cloud: $POINT_CLOUD" >&2
  echo "[Video2Mesh] Use scene/reconstruction/point_cloud.ply, or set ALLOW_DOWNSAMPLED_POINT_CLOUD=1 intentionally." >&2
  exit 2
fi

"$PYTHON" -m video2mesh.cli train-gsplat \
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

"$PYTHON" -m video2mesh.cli render-gsplat-preview \
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
