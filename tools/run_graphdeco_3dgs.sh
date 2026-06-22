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
  DENSIFY_UNTIL_ITER=15000
  DENSIFY_FROM_ITER=500
  DENSIFICATION_INTERVAL=100
  OPACITY_RESET_INTERVAL=3000
  SH_DEGREE=3
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
DENSIFY_UNTIL_ITER="${DENSIFY_UNTIL_ITER:-15000}"
DENSIFY_FROM_ITER="${DENSIFY_FROM_ITER:-500}"
DENSIFICATION_INTERVAL="${DENSIFICATION_INTERVAL:-100}"
OPACITY_RESET_INTERVAL="${OPACITY_RESET_INTERVAL:-3000}"
SH_DEGREE="${SH_DEGREE:-3}"
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
POINT_CLOUD="${POINT_CLOUD:-$PROJECT_ROOT/scene/reconstruction/point_cloud.ply}"

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
  --prepare-only \
  --command-template "cd $GRAPHDECO_ROOT && $GRAPHDECO_PYTHON train.py -s {source_path} -m {output_path} --iterations $ITERATIONS --save_iterations $SAVE_ITERATIONS --test_iterations $TEST_ITERATIONS --resolution $RESOLUTION --images $TRAIN_IMAGES --sh_degree $SH_DEGREE --densify_until_iter $DENSIFY_UNTIL_ITER --densify_from_iter $DENSIFY_FROM_ITER --densification_interval $DENSIFICATION_INTERVAL --opacity_reset_interval $OPACITY_RESET_INTERVAL $GRAPHDECO_EXTRA_ARGS --disable_viewer"

(
  cd "$GRAPHDECO_ROOT"
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
    --opacity_reset_interval "$OPACITY_RESET_INTERVAL" \
    $GRAPHDECO_EXTRA_ARGS \
    --disable_viewer
) 2>&1 | tee "$LOG"

"$V2M_PYTHON" -B -m video2mesh.cli import-3dgs-result \
  --project-root "$PROJECT_ROOT" \
  --path "$OUTPUT_PATH" \
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
