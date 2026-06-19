#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/run_video2mesh_quick.sh /path/to/video.mp4

Convention-over-configuration quick entrypoint for the full Video2Mesh baseline:
video -> frames -> MASt3R-SLAM full point cloud -> GraphDECO 3DGS -> SAM2 masks ->
3D semantic masks/probabilities -> SVLGaussian frame selection -> coarse meshes ->
simulator assets and QA reports.

Optional environment overrides:
  VIDEO2MESH_ROOT=/root/autodl-tmp/workspace/Video2Mesh
  PROJECT_ROOT=/custom/output/dir
  SCENE_ID=my_scene
  RUN_SAM2=1|0
  RUN_MAST3R=1|0
  GS_BACKEND=graphdeco|minimal|none
  GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting
  GRAPHDECO_ITERATIONS=7000
  MAX_FRAMES=72
  SAM_CHECKPOINT=/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 1 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

VIDEO_INPUT="$1"
ROOT="${VIDEO2MESH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [[ ! -f "$VIDEO_INPUT" ]]; then
  echo "[Video2Mesh quick] Video not found: $VIDEO_INPUT" >&2
  exit 2
fi
VIDEO_INPUT="$(cd "$(dirname "$VIDEO_INPUT")" && pwd)/$(basename "$VIDEO_INPUT")"

slugify() {
  local value="$1"
  value="${value%.*}"
  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//')"
  if [[ -z "$value" ]]; then
    value="video2mesh_scene"
  fi
  printf '%s' "$value"
}

SCENE_ID="${SCENE_ID:-$(slugify "$(basename "$VIDEO_INPUT")")}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
PROJECT_ROOT="${PROJECT_ROOT:-${ROOT}/exports/${SCENE_ID}_quick_${RUN_TAG}}"
WORLD="${WORLD:-${SCENE_ID}_quick}"

V2M_PYTHON="${V2M_PYTHON:-/root/autodl-tmp/venvs/v2m-svpp/bin/python}"
if [[ ! -x "$V2M_PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python)"
  else
    echo "[Video2Mesh quick] No Python interpreter found; set V2M_PYTHON." >&2
    exit 2
  fi
fi

MAST3R_ROOT="${MAST3R_ROOT:-/root/autodl-tmp/workspace/MASt3R-SLAM}"
MAST3R_CONFIG="${MAST3R_CONFIG:-config/video_scan.yaml}"
SAM2_ROOT="${SAM2_ROOT:-/root/autodl-tmp/workspace/sam2}"
SAM2_PYTHON="${SAM2_PYTHON:-/root/autodl-tmp/workspace/venvs/v2m-sam2-clean/bin/python}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-${SAM2_ROOT}/checkpoints/sam2.1_hiera_tiny.pt}"
SAM2_MODEL_CFG="${SAM2_MODEL_CFG:-configs/sam2.1/sam2.1_hiera_t.yaml}"
SAM_CHECKPOINT="${SAM_CHECKPOINT:-/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth}"
SAM_MODEL_TYPE="${SAM_MODEL_TYPE:-vit_b}"
GRAPHDECO_ROOT="${GRAPHDECO_ROOT:-/root/autodl-tmp/workspace/gaussian-splatting}"
GRAPHDECO_PYTHON="${GRAPHDECO_PYTHON:-$V2M_PYTHON}"

RUN_MAST3R="${RUN_MAST3R:-1}"
GS_BACKEND="${GS_BACKEND:-graphdeco}"
RUN_GSPLAT="${RUN_GSPLAT:-$([[ "$GS_BACKEND" == "minimal" ]] && printf 1 || printf 0)}"
RUN_SAM2="${RUN_SAM2:-1}"
MAX_FRAMES="${MAX_FRAMES:-72}"
EXTRACT_EVERY="${EXTRACT_EVERY:-2}"
GRAPHDECO_ITERATIONS="${GRAPHDECO_ITERATIONS:-7000}"
GRAPHDECO_RESOLUTION="${GRAPHDECO_RESOLUTION:-1}"
GSPLAT_ITERATIONS="${GSPLAT_ITERATIONS:-500}"
GSPLAT_MAX_FRAMES="${GSPLAT_MAX_FRAMES:-6}"
GSPLAT_MAX_POINTS="${GSPLAT_MAX_POINTS:-24000}"
GSPLAT_WIDTH="${GSPLAT_WIDTH:-432}"
GSPLAT_HEIGHT="${GSPLAT_HEIGHT:-768}"
AUTO_PROMPT_MAX_OBJECTS="${AUTO_PROMPT_MAX_OBJECTS:-8}"
AUTO_PROMPT_FRAME_INDEX="${AUTO_PROMPT_FRAME_INDEX:-10}"
TRACK_MAX_FRAMES="${TRACK_MAX_FRAMES:-$MAX_FRAMES}"
PIXEL_STRIDE="${PIXEL_STRIDE:-3}"
MAX_PIXELS_PER_MASK="${MAX_PIXELS_PER_MASK:-5000}"
TOP_K="${TOP_K:-4}"

AUTO_PROMPT_METHOD="${AUTO_PROMPT_METHOD:-sam}"
if [[ "$AUTO_PROMPT_METHOD" == "sam" && ! -f "$SAM_CHECKPOINT" ]]; then
  echo "[Video2Mesh quick] SAM checkpoint not found, falling back to OpenCV auto prompts: $SAM_CHECKPOINT" >&2
  AUTO_PROMPT_METHOD="opencv"
fi
MASK_BACKEND="${MASK_BACKEND:-$([[ "$RUN_SAM2" == "1" || "$RUN_SAM2" == "true" ]] && printf sam2 || printf opencv)}"
if [[ "$MASK_BACKEND" == "sam2" ]]; then
  export PYTHONPATH="${SAM2_ROOT}:${ROOT}:${PYTHONPATH:-}"
  export SAM2_ROOT
fi
if [[ "$GS_BACKEND" == "graphdeco" ]]; then
  if [[ ! -f "${GRAPHDECO_ROOT}/train.py" ]]; then
    echo "[Video2Mesh quick] Missing GraphDECO train.py under: $GRAPHDECO_ROOT" >&2
    exit 2
  fi
  TORCH_LIB="$("$V2M_PYTHON" - <<'PY'
from pathlib import Path
import torch
print(Path(torch.__file__).resolve().parent / "lib")
PY
)"
  CUDA_TARGET="${CUDA_TARGET:-/root/miniconda3/targets/x86_64-linux}"
  export PYTHONPATH="${GRAPHDECO_ROOT}:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="$TORCH_LIB:$CUDA_TARGET/lib:/root/miniconda3/lib:${LD_LIBRARY_PATH:-}"
  export MAX_JOBS="${MAX_JOBS:-1}"
  export TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.9}"
fi

cd "$ROOT"
mkdir -p "$PROJECT_ROOT/logs"
LOG="${PROJECT_ROOT}/logs/quick_run.log"

echo "[Video2Mesh quick] root: $ROOT" | tee "$LOG"
echo "[Video2Mesh quick] video: $VIDEO_INPUT" | tee -a "$LOG"
echo "[Video2Mesh quick] project: $PROJECT_ROOT" | tee -a "$LOG"
echo "[Video2Mesh quick] scene_id: $SCENE_ID" | tee -a "$LOG"
echo "[Video2Mesh quick] python: $V2M_PYTHON" | tee -a "$LOG"
echo "[Video2Mesh quick] auto_prompt_method: $AUTO_PROMPT_METHOD" | tee -a "$LOG"
echo "[Video2Mesh quick] mask_backend: $MASK_BACKEND" | tee -a "$LOG"
echo "[Video2Mesh quick] gs_backend: $GS_BACKEND" | tee -a "$LOG"

g3dgs_args=()
if [[ "$GS_BACKEND" == "graphdeco" ]]; then
  g3dgs_args=(
    --prepare-3dgs-source
    --g3dgs-output-path scene/reconstruction/3dgs_graphdeco
    --g3dgs-work-dir external/graphdeco_3dgs
    --g3dgs-command-template "cd ${GRAPHDECO_ROOT} && ${GRAPHDECO_PYTHON} train.py -s {source_path} -m {output_path} --iterations ${GRAPHDECO_ITERATIONS} --save_iterations ${GRAPHDECO_ITERATIONS} --test_iterations ${GRAPHDECO_ITERATIONS} --resolution ${GRAPHDECO_RESOLUTION} --images images --disable_viewer"
  )
elif [[ "$GS_BACKEND" == "minimal" ]]; then
  g3dgs_args=(
    --train-gsplat
    --g3dgs-output-path scene/reconstruction/3dgs
    --gsplat-iterations "$GSPLAT_ITERATIONS"
    --gsplat-max-frames "$GSPLAT_MAX_FRAMES"
    --gsplat-max-points "$GSPLAT_MAX_POINTS"
    --gsplat-device cuda
    --gsplat-width "$GSPLAT_WIDTH"
    --gsplat-height "$GSPLAT_HEIGHT"
    --gsplat-log-every 50
  )
elif [[ "$GS_BACKEND" == "none" ]]; then
  g3dgs_args=()
else
  echo "[Video2Mesh quick] Unknown GS_BACKEND: $GS_BACKEND" >&2
  exit 2
fi

"$V2M_PYTHON" -B -m video2mesh.cli run-pipeline \
  --project-root "$PROJECT_ROOT" \
  --scene-id "$SCENE_ID" \
  --world "$WORLD" \
  --video "$VIDEO_INPUT" \
  --dataset "$VIDEO_INPUT" \
  --extract-frames \
  --every "$EXTRACT_EVERY" \
  --max-frames "$MAX_FRAMES" \
  --overwrite-frames \
  $([[ "$RUN_MAST3R" == "1" || "$RUN_MAST3R" == "true" ]] && printf '%s ' --run-mast3r-slam) \
  --mast3r-root "$MAST3R_ROOT" \
  --mast3r-config "$MAST3R_CONFIG" \
  --mast3r-save-as "$SCENE_ID" \
  --focal-scale 1.2 \
  --use-mast3r-keyframes \
  --render-reconstruction-preview \
  --reconstruction-preview-max-frames 4 \
  --reconstruction-preview-max-points 12000 \
  "${g3dgs_args[@]}" \
  --render-gsplat-preview \
  --preview-max-frames 6 \
  --preview-width "$GSPLAT_WIDTH" \
  --preview-height "$GSPLAT_HEIGHT" \
  --auto-prompts \
  --auto-prompt-method "$AUTO_PROMPT_METHOD" \
  --auto-prompt-frame-index "$AUTO_PROMPT_FRAME_INDEX" \
  --auto-prompt-max-objects "$AUTO_PROMPT_MAX_OBJECTS" \
  --auto-prompt-granularity object \
  --sam-checkpoint "$SAM_CHECKPOINT" \
  --sam-model-type "$SAM_MODEL_TYPE" \
  --sam-device cuda \
  --mask-backend "$MASK_BACKEND" \
  --sam2-checkpoint "$SAM2_CHECKPOINT" \
  --sam2-model-cfg "$SAM2_MODEL_CFG" \
  --sam2-device cuda \
  --sam2-offload-video-to-cpu \
  --sam2-offload-state-to-cpu \
  --track-max-frames "$TRACK_MAX_FRAMES" \
  --clear-mask-output \
  --fusion-mode probability \
  --min-votes 1 \
  --depth-tolerance 0.05 \
  --relative-depth-tolerance 0.03 \
  --infer-background-plane-masks \
  --background-plane-max-planes 8 \
  --background-plane-min-points 300 \
  --transfer-mode nearest \
  --backproject-gaussian-probabilities \
  --gaussian-backproject-pixel-stride "$PIXEL_STRIDE" \
  --gaussian-backproject-max-pixels-per-mask "$MAX_PIXELS_PER_MASK" \
  --gaussian-backproject-include-background-structures \
  --render-semantic-preview \
  --semantic-preview-max-frames 6 \
  --semantic-preview-max-points 20000 \
  --top-k "$TOP_K" \
  --frame-selection-method svlgaussian \
  --frame-svlgaussian-offsets 5 10 \
  --frame-svlgaussian-random-window 30 \
  --frame-svlgaussian-visibility-window 3 \
  --reconstruct-mask-meshes \
  --mask-mesh-method bbox \
  --skip-failed-mask-meshes \
  --skip-export-image-blaster \
  --simulator-format mujoco unity \
  --collision-proxy bbox \
  --use-collision-proxy \
  --collider box \
  --body-type dynamic \
  --calibrate-simulator-assets \
  --no-calibration-scale-calibrated \
  --calibration-scale-to-meters 1.0 \
  --calibration-up-axis y \
  --calibration-estimate-physics \
  --calibration-overwrite-physics \
  --allow-incomplete 2>&1 | tee -a "$LOG"

"$V2M_PYTHON" -B -m video2mesh.cli production-readiness \
  --project-root "$PROJECT_ROOT" \
  --no-require-scale-calibration 2>&1 | tee -a "$LOG" || true

"$V2M_PYTHON" -B -m video2mesh.cli target-capability-matrix \
  --project-root "$PROJECT_ROOT" 2>&1 | tee -a "$LOG" || true

"$V2M_PYTHON" -B -m video2mesh.cli export-advisor-demo-summary \
  --project-root "$PROJECT_ROOT" 2>&1 | tee -a "$LOG" || true

"$V2M_PYTHON" -B -m video2mesh.cli verify-showcase-pack \
  --project-root "$PROJECT_ROOT" \
  --require-semantic-probability \
  --no-require-review-tar \
  --no-scan-common-remote-roots 2>&1 | tee -a "$LOG" || true

echo "[Video2Mesh quick] complete: $PROJECT_ROOT" | tee -a "$LOG"
