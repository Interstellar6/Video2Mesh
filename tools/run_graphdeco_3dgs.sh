#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/run_graphdeco_3dgs.sh /path/to/exports/<run>

Prepare a COLMAP-style source from a Video2Mesh run, train GraphDECO 3DGS,
then import/register the result back into the Video2Mesh project.

Optional environment overrides:
  VIDEO2MESH_ROOT=/root/autodl-tmp/workspace/Video2Mesh
  V2M_PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting
  GRAPHDECO_PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  ITERATIONS=30000
  SAVE_ITERATIONS="7000 30000"
  TEST_ITERATIONS="7000 30000"
  RESOLUTION=1
  DENSIFY_UNTIL_ITER=5000
  DENSIFY_FROM_ITER=1000
  DENSIFICATION_INTERVAL=300
  DENSIFY_GRAD_THRESHOLD=0.002
  OPACITY_RESET_INTERVAL=3000
  SH_DEGREE=3
  CLEAN_3DGS_FLOATERS=1
  CLEAN_KNN=24
  CLEAN_OUTLIER_MAD=2.5
  CLEAN_MAX_ELONGATION=25
  CLEAN_MIN_OPACITY=0.01
  CLEAN_LOW_OPACITY=0.08
  CLEAN_GEOMETRIC_OUTLIERS=0
  CLEAN_ELONGATION_FILTER=0
  STRICT_3DGS_CLEAN=1
  STRICT_REFERENCE_POINT_CLOUD=/path/to/external/colmap/dense/fused.ply
  STRICT_BBOX_PADDING_RATIO=0.12
  STRICT_CLUSTER_EPS_RATIO=0.015
  STRICT_CLUSTER_MIN_POINTS=300
  STRICT_PRESERVE_BACKGROUND_PLANES=1
  GRAPHDECO_CUDA_VISIBLE_DEVICES=""
  GRAPHDECO_EXTRA_ARGS=""
  TRAIN_IMAGES=images
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 1 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

PROJECT_ROOT="$1"
if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "[Video2Mesh GraphDECO] Project root not found: $PROJECT_ROOT" >&2
  exit 2
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

ROOT="${VIDEO2MESH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
V2M_PYTHON="${V2M_PYTHON:-/root/autodl-tmp/venvs/v2m-svpp/bin/python}"
GRAPHDECO_ROOT="${GRAPHDECO_ROOT:-/root/autodl-tmp/workspace/gaussian-splatting}"
GRAPHDECO_PYTHON="${GRAPHDECO_PYTHON:-$V2M_PYTHON}"
ITERATIONS="${ITERATIONS:-30000}"
RESOLUTION="${RESOLUTION:-1}"
SAVE_ITERATIONS="${SAVE_ITERATIONS:-7000 30000}"
TEST_ITERATIONS="${TEST_ITERATIONS:-7000 30000}"
DENSIFY_UNTIL_ITER="${DENSIFY_UNTIL_ITER:-5000}"
DENSIFY_FROM_ITER="${DENSIFY_FROM_ITER:-1000}"
DENSIFICATION_INTERVAL="${DENSIFICATION_INTERVAL:-300}"
DENSIFY_GRAD_THRESHOLD="${DENSIFY_GRAD_THRESHOLD:-0.002}"
OPACITY_RESET_INTERVAL="${OPACITY_RESET_INTERVAL:-3000}"
SH_DEGREE="${SH_DEGREE:-3}"
CLEAN_3DGS_FLOATERS="${CLEAN_3DGS_FLOATERS:-1}"
CLEAN_KNN="${CLEAN_KNN:-24}"
CLEAN_OUTLIER_MAD="${CLEAN_OUTLIER_MAD:-2.5}"
CLEAN_MAX_ELONGATION="${CLEAN_MAX_ELONGATION:-25}"
CLEAN_MIN_OPACITY="${CLEAN_MIN_OPACITY:-0.01}"
CLEAN_LOW_OPACITY="${CLEAN_LOW_OPACITY:-0.08}"
CLEAN_GEOMETRIC_OUTLIERS="${CLEAN_GEOMETRIC_OUTLIERS:-0}"
CLEAN_ELONGATION_FILTER="${CLEAN_ELONGATION_FILTER:-0}"
STRICT_3DGS_CLEAN="${STRICT_3DGS_CLEAN:-1}"
STRICT_REFERENCE_POINT_CLOUD="${STRICT_REFERENCE_POINT_CLOUD:-$PROJECT_ROOT/external/colmap/dense/fused.ply}"
STRICT_BBOX_PADDING_RATIO="${STRICT_BBOX_PADDING_RATIO:-0.12}"
STRICT_CLUSTER_EPS_RATIO="${STRICT_CLUSTER_EPS_RATIO:-0.015}"
STRICT_CLUSTER_MIN_POINTS="${STRICT_CLUSTER_MIN_POINTS:-300}"
STRICT_PRESERVE_BACKGROUND_PLANES="${STRICT_PRESERVE_BACKGROUND_PLANES:-1}"
GRAPHDECO_CUDA_VISIBLE_DEVICES="${GRAPHDECO_CUDA_VISIBLE_DEVICES:-}"
GRAPHDECO_EXTRA_ARGS="${GRAPHDECO_EXTRA_ARGS:-}"
TRAIN_IMAGES="${TRAIN_IMAGES:-images}"
SOURCE_PATH="${SOURCE_PATH:-$PROJECT_ROOT/external/graphdeco_3dgs/colmap_source}"
OUTPUT_PATH="${OUTPUT_PATH:-$PROJECT_ROOT/scene/reconstruction/3dgs_graphdeco}"
WORK_DIR="${WORK_DIR:-$PROJECT_ROOT/external/graphdeco_3dgs}"
LOG="${LOG:-$PROJECT_ROOT/logs/graphdeco_3dgs_train.log}"
FRAMES_DIR="${FRAMES_DIR:-$PROJECT_ROOT/scene/mast3r_keyframes}"
if [[ ! -d "$FRAMES_DIR" ]]; then
  FRAMES_DIR="$PROJECT_ROOT/scene/frames"
fi
CAMERA_INFO="${CAMERA_INFO:-$PROJECT_ROOT/scene/cameras/camera_info.json}"
DEFAULT_POINT_CLOUD="$PROJECT_ROOT/scene/reconstruction/point_cloud.ply"
if [[ -f "$PROJECT_ROOT/external/colmap/dense/fused.ply" ]]; then
  DEFAULT_POINT_CLOUD="$PROJECT_ROOT/external/colmap/dense/fused.ply"
fi
POINT_CLOUD="${POINT_CLOUD:-$DEFAULT_POINT_CLOUD}"

if [[ ! -x "$V2M_PYTHON" ]]; then
  echo "[Video2Mesh GraphDECO] Missing V2M_PYTHON: $V2M_PYTHON" >&2
  exit 2
fi
if [[ ! -x "$GRAPHDECO_PYTHON" ]]; then
  echo "[Video2Mesh GraphDECO] Missing GRAPHDECO_PYTHON: $GRAPHDECO_PYTHON" >&2
  exit 2
fi
if [[ ! -f "$GRAPHDECO_ROOT/train.py" ]]; then
  echo "[Video2Mesh GraphDECO] Missing GraphDECO train.py under: $GRAPHDECO_ROOT" >&2
  exit 2
fi
if [[ ! -f "$CAMERA_INFO" ]]; then
  echo "[Video2Mesh GraphDECO] Missing camera info: $CAMERA_INFO" >&2
  exit 2
fi
if [[ ! -f "$POINT_CLOUD" ]]; then
  echo "[Video2Mesh GraphDECO] Missing full point cloud: $POINT_CLOUD" >&2
  exit 2
fi
if [[ "$(basename "$POINT_CLOUD")" =~ ^point_cloud_([0-9]+|[0-9]+k|10k|30k)\.ply$ ]]; then
  echo "[Video2Mesh GraphDECO] Refusing downsampled initialization cloud: $POINT_CLOUD" >&2
  exit 2
fi

export PATH=/root/autodl-tmp/venvs/v2m-svpp/bin:/root/miniconda3/bin:$PATH
export PYTHONPATH="$GRAPHDECO_ROOT:${PYTHONPATH:-}"
export MAX_JOBS="${MAX_JOBS:-1}"
export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}"
CUDA_TARGET="${CUDA_TARGET:-/root/miniconda3/targets/x86_64-linux}"
TORCH_LIB="$("$V2M_PYTHON" - <<'PY'
from pathlib import Path
import torch
print(Path(torch.__file__).resolve().parent / "lib")
PY
)"
export CPATH="$CUDA_TARGET/include:${CPATH:-}"
export CPLUS_INCLUDE_PATH="$CUDA_TARGET/include:${CPLUS_INCLUDE_PATH:-}"
export LIBRARY_PATH="$CUDA_TARGET/lib:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$TORCH_LIB:$CUDA_TARGET/lib:/root/miniconda3/lib:${LD_LIBRARY_PATH:-}"

mkdir -p "$WORK_DIR" "$OUTPUT_PATH" "$(dirname "$LOG")"

echo "[Video2Mesh GraphDECO] project: $PROJECT_ROOT"
echo "[Video2Mesh GraphDECO] source:  $SOURCE_PATH"
echo "[Video2Mesh GraphDECO] output:  $OUTPUT_PATH"
echo "[Video2Mesh GraphDECO] graphdeco: $GRAPHDECO_ROOT"
echo "[Video2Mesh GraphDECO] iterations=$ITERATIONS resolution=$RESOLUTION"
echo "[Video2Mesh GraphDECO] densify_until_iter=$DENSIFY_UNTIL_ITER densify_from_iter=$DENSIFY_FROM_ITER"
echo "[Video2Mesh GraphDECO] cuda_visible_devices=${GRAPHDECO_CUDA_VISIBLE_DEVICES:-inherit}"

graphdeco_cuda_prefix=""
if [[ -n "$GRAPHDECO_CUDA_VISIBLE_DEVICES" ]]; then
  graphdeco_cuda_prefix="CUDA_VISIBLE_DEVICES=${GRAPHDECO_CUDA_VISIBLE_DEVICES} "
fi

"$V2M_PYTHON" -B -m video2mesh.cli run-3dgs \
  --project-root "$PROJECT_ROOT" \
  --source-path "$SOURCE_PATH" \
  --output-path "$OUTPUT_PATH" \
  --work-dir "$WORK_DIR" \
  --frames-dir "$FRAMES_DIR" \
  --camera-info "$CAMERA_INFO" \
  --point-cloud "$POINT_CLOUD" \
  --camera-model PINHOLE \
  --image-mode copy \
  --clean-init-point-cloud \
  --prepare-only \
  --command-template "cd $GRAPHDECO_ROOT && ${graphdeco_cuda_prefix}$GRAPHDECO_PYTHON train.py -s {source_path} -m {output_path} --iterations $ITERATIONS --save_iterations $SAVE_ITERATIONS --test_iterations $TEST_ITERATIONS --resolution $RESOLUTION --images $TRAIN_IMAGES --sh_degree $SH_DEGREE --densify_until_iter $DENSIFY_UNTIL_ITER --densify_from_iter $DENSIFY_FROM_ITER --densification_interval $DENSIFICATION_INTERVAL --densify_grad_threshold $DENSIFY_GRAD_THRESHOLD --opacity_reset_interval $OPACITY_RESET_INTERVAL $GRAPHDECO_EXTRA_ARGS --disable_viewer"

(
  cd "$GRAPHDECO_ROOT"
  if [[ -n "$GRAPHDECO_CUDA_VISIBLE_DEVICES" ]]; then
    export CUDA_VISIBLE_DEVICES="$GRAPHDECO_CUDA_VISIBLE_DEVICES"
  fi
  "$GRAPHDECO_PYTHON" train.py \
    -s "$SOURCE_PATH" \
    -m "$OUTPUT_PATH" \
    --iterations "$ITERATIONS" \
    --save_iterations $SAVE_ITERATIONS \
    --test_iterations $TEST_ITERATIONS \
    --resolution "$RESOLUTION" \
    --images "$TRAIN_IMAGES" \
    --sh_degree "$SH_DEGREE" \
    --densify_until_iter "$DENSIFY_UNTIL_ITER" \
    --densify_from_iter "$DENSIFY_FROM_ITER" \
    --densification_interval "$DENSIFICATION_INTERVAL" \
    --densify_grad_threshold "$DENSIFY_GRAD_THRESHOLD" \
    --opacity_reset_interval "$OPACITY_RESET_INTERVAL" \
    $GRAPHDECO_EXTRA_ARGS \
    --disable_viewer
) 2>&1 | tee "$LOG"

RAW_SPLAT="$OUTPUT_PATH/point_cloud/iteration_$ITERATIONS/point_cloud.ply"
CLEAN_SPLAT="$OUTPUT_PATH/point_cloud/iteration_$ITERATIONS/point_cloud_clean.ply"
CLEAN_STRICT_SPLAT="$OUTPUT_PATH/point_cloud/iteration_$ITERATIONS/point_cloud_clean_strict.ply"
IMPORT_SPLAT="$RAW_SPLAT"
if [[ "$CLEAN_3DGS_FLOATERS" == "1" ]]; then
  if [[ ! -f "$RAW_SPLAT" ]]; then
    echo "[Video2Mesh GraphDECO] Missing trained 3DGS PLY for cleaning: $RAW_SPLAT" >&2
    exit 2
  fi
  clean_output="$CLEAN_SPLAT"
  clean_args=()
  if [[ "$STRICT_3DGS_CLEAN" == "1" || "$STRICT_3DGS_CLEAN" == "true" ]]; then
    clean_output="$CLEAN_STRICT_SPLAT"
    clean_args+=(
      --strict-scene-filter
      --bbox-padding-ratio "$STRICT_BBOX_PADDING_RATIO"
      --cluster-eps-ratio "$STRICT_CLUSTER_EPS_RATIO"
      --cluster-min-points "$STRICT_CLUSTER_MIN_POINTS"
    )
    if [[ "$STRICT_PRESERVE_BACKGROUND_PLANES" == "1" || "$STRICT_PRESERVE_BACKGROUND_PLANES" == "true" ]]; then
      clean_args+=(--preserve-background-planes)
    else
      clean_args+=(--no-preserve-background-planes)
    fi
    if [[ -n "$STRICT_REFERENCE_POINT_CLOUD" && -f "$STRICT_REFERENCE_POINT_CLOUD" ]]; then
      clean_args+=(--reference-point-cloud "$STRICT_REFERENCE_POINT_CLOUD")
    fi
  fi
  if [[ "$CLEAN_GEOMETRIC_OUTLIERS" == "1" || "$CLEAN_GEOMETRIC_OUTLIERS" == "true" ]]; then
    clean_args+=(--geometric-outliers)
  else
    clean_args+=(--no-geometric-outliers)
  fi
  if [[ "$CLEAN_ELONGATION_FILTER" == "1" || "$CLEAN_ELONGATION_FILTER" == "true" ]]; then
    clean_args+=(--elongation-filter)
  else
    clean_args+=(--no-elongation-filter)
  fi
  "$V2M_PYTHON" -B -m video2mesh.cli clean-3dgs-floaters \
    --project-root "$PROJECT_ROOT" \
    --input "$RAW_SPLAT" \
    --output "$clean_output" \
    --knn "$CLEAN_KNN" \
    --outlier-mad "$CLEAN_OUTLIER_MAD" \
    --max-elongation "$CLEAN_MAX_ELONGATION" \
    --min-opacity "$CLEAN_MIN_OPACITY" \
    --low-opacity "$CLEAN_LOW_OPACITY" \
    "${clean_args[@]}"
  if [[ "$STRICT_3DGS_CLEAN" == "1" || "$STRICT_3DGS_CLEAN" == "true" ]]; then
    IMPORT_SPLAT="$CLEAN_STRICT_SPLAT"
  else
    IMPORT_SPLAT="$CLEAN_SPLAT"
  fi
fi

"$V2M_PYTHON" -B -m video2mesh.cli import-3dgs-result \
  --project-root "$PROJECT_ROOT" \
  --path "$OUTPUT_PATH" \
  --splat-ply "$IMPORT_SPLAT" \
  --provider graphdeco \
  --mode symlink \
  --preview-max-frames 6 \
  --render-semantic-preview \
  --semantic-preview-max-frames 6 \
  --semantic-preview-max-points 20000

"$V2M_PYTHON" -B -m video2mesh.cli production-readiness \
  --project-root "$PROJECT_ROOT" \
  --no-require-scale-calibration || true

"$V2M_PYTHON" -B -m video2mesh.cli verify-showcase-pack \
  --project-root "$PROJECT_ROOT" \
  --require-semantic-probability \
  --no-require-review-tar \
  --no-scan-common-remote-roots || true

echo "[Video2Mesh GraphDECO] complete: $OUTPUT_PATH"
