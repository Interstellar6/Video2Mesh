#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/run_video2mesh_downstream_light.sh /path/to/project_root /path/to/video.mp4

Resume downstream Video2Mesh stages after MASt3R/GraphDECO already succeeded.
This entrypoint is for recovery runs on large full-cloud projects: it keeps the
original MASt3R point cloud as the fusion source, but defaults to a lighter
semantic path so SSH/GPU memory are less likely to be saturated.

Optional environment overrides:
  VIDEO2MESH_ROOT=/root/autodl-tmp/workspace/Video2Mesh
  V2M_PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  SCENE_ID=my_scene
  WORLD=my_world
  MAX_FRAMES=48
  TRACK_MAX_FRAMES=48
  AUTO_PROMPT_MAX_OBJECTS=6
  SEMANTIC_SPLATS=0|1
  GAUSSIAN_BACKPROJECT=0|1
  RENDER_SEMANTIC_PREVIEW=0|1
  RECONSTRUCT_MASK_MESHES=1|0
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 2 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

PROJECT_ROOT="$1"
VIDEO_INPUT="$2"
ROOT="${VIDEO2MESH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "[Video2Mesh downstream] Project root not found: $PROJECT_ROOT" >&2
  exit 2
fi
if [[ ! -f "$VIDEO_INPUT" ]]; then
  echo "[Video2Mesh downstream] Video not found: $VIDEO_INPUT" >&2
  exit 2
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
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
WORLD="${WORLD:-${SCENE_ID}_downstream}"

V2M_PYTHON="${V2M_PYTHON:-/root/autodl-tmp/venvs/v2m-svpp/bin/python}"
if [[ ! -x "$V2M_PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python)"
  else
    echo "[Video2Mesh downstream] No Python interpreter found; set V2M_PYTHON." >&2
    exit 2
  fi
fi

SAM2_ROOT="${SAM2_ROOT:-/root/autodl-tmp/workspace/sam2}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-${SAM2_ROOT}/checkpoints/sam2.1_hiera_tiny.pt}"
SAM2_MODEL_CFG="${SAM2_MODEL_CFG:-configs/sam2.1/sam2.1_hiera_t.yaml}"
SAM_CHECKPOINT="${SAM_CHECKPOINT:-/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth}"
SAM_MODEL_TYPE="${SAM_MODEL_TYPE:-vit_b}"

MAX_FRAMES="${MAX_FRAMES:-48}"
TRACK_MAX_FRAMES="${TRACK_MAX_FRAMES:-$MAX_FRAMES}"
AUTO_PROMPT_MAX_OBJECTS="${AUTO_PROMPT_MAX_OBJECTS:-6}"
AUTO_PROMPT_FRAME_INDEX="${AUTO_PROMPT_FRAME_INDEX:-10}"
AUTO_PROMPT_METHOD="${AUTO_PROMPT_METHOD:-sam}"
MASK_BACKEND="${MASK_BACKEND:-sam2}"
TOP_K="${TOP_K:-4}"
SEMANTIC_SPLATS="${SEMANTIC_SPLATS:-0}"
GAUSSIAN_BACKPROJECT="${GAUSSIAN_BACKPROJECT:-0}"
RENDER_SEMANTIC_PREVIEW="${RENDER_SEMANTIC_PREVIEW:-0}"
RECONSTRUCT_MASK_MESHES="${RECONSTRUCT_MASK_MESHES:-1}"
PIXEL_STRIDE="${PIXEL_STRIDE:-6}"
MAX_PIXELS_PER_MASK="${MAX_PIXELS_PER_MASK:-1500}"
SEMANTIC_PREVIEW_MAX_POINTS="${SEMANTIC_PREVIEW_MAX_POINTS:-8000}"

if [[ "$AUTO_PROMPT_METHOD" == "sam" && ! -f "$SAM_CHECKPOINT" ]]; then
  echo "[Video2Mesh downstream] SAM checkpoint not found, falling back to OpenCV auto prompts: $SAM_CHECKPOINT" >&2
  AUTO_PROMPT_METHOD="opencv"
fi

if [[ "$MASK_BACKEND" == "sam2" ]]; then
  export PYTHONPATH="${SAM2_ROOT}:${ROOT}:${PYTHONPATH:-}"
  export SAM2_ROOT
fi
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

cd "$ROOT"
mkdir -p "$PROJECT_ROOT/logs"
LOG="${PROJECT_ROOT}/logs/downstream_light_$(date +%Y%m%d_%H%M%S).log"

echo "[Video2Mesh downstream] root: $ROOT" | tee "$LOG"
echo "[Video2Mesh downstream] project: $PROJECT_ROOT" | tee -a "$LOG"
echo "[Video2Mesh downstream] video: $VIDEO_INPUT" | tee -a "$LOG"
echo "[Video2Mesh downstream] scene_id: $SCENE_ID" | tee -a "$LOG"
echo "[Video2Mesh downstream] mask_backend: $MASK_BACKEND" | tee -a "$LOG"
echo "[Video2Mesh downstream] semantic_splats: $SEMANTIC_SPLATS" | tee -a "$LOG"
echo "[Video2Mesh downstream] gaussian_backproject: $GAUSSIAN_BACKPROJECT" | tee -a "$LOG"

semantic_args=()
if [[ "$SEMANTIC_SPLATS" == "1" || "$SEMANTIC_SPLATS" == "true" ]]; then
  semantic_args+=(--transfer-mode nearest)
  if [[ "$GAUSSIAN_BACKPROJECT" == "1" || "$GAUSSIAN_BACKPROJECT" == "true" ]]; then
    semantic_args+=(
      --backproject-gaussian-probabilities
      --gaussian-backproject-pixel-stride "$PIXEL_STRIDE"
      --gaussian-backproject-max-pixels-per-mask "$MAX_PIXELS_PER_MASK"
      --gaussian-backproject-include-background-structures
    )
  fi
  if [[ "$RENDER_SEMANTIC_PREVIEW" == "1" || "$RENDER_SEMANTIC_PREVIEW" == "true" ]]; then
    semantic_args+=(
      --render-semantic-preview
      --semantic-preview-max-frames 4
      --semantic-preview-max-points "$SEMANTIC_PREVIEW_MAX_POINTS"
    )
  fi
else
  semantic_args+=(--skip-export-splat-masks --skip-export-viewer-plys)
fi

mesh_args=()
if [[ "$RECONSTRUCT_MASK_MESHES" == "1" || "$RECONSTRUCT_MASK_MESHES" == "true" ]]; then
  mesh_args+=(--reconstruct-mask-meshes --mask-mesh-method bbox --skip-failed-mask-meshes)
fi

"$V2M_PYTHON" -B -m video2mesh.cli run-pipeline \
  --project-root "$PROJECT_ROOT" \
  --scene-id "$SCENE_ID" \
  --world "$WORLD" \
  --video "$VIDEO_INPUT" \
  --dataset "$VIDEO_INPUT" \
  --use-mast3r-keyframes \
  --auto-prompts \
  --auto-prompt-method "$AUTO_PROMPT_METHOD" \
  --auto-prompt-frame-index "$AUTO_PROMPT_FRAME_INDEX" \
  --auto-prompt-max-objects "$AUTO_PROMPT_MAX_OBJECTS" \
  --auto-prompt-granularity object \
  --auto-prompt-min-area-ratio 0.008 \
  --auto-prompt-min-parent-area-ratio 0.10 \
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
  --background-plane-max-planes 6 \
  --background-plane-min-points 300 \
  "${semantic_args[@]}" \
  --top-k "$TOP_K" \
  --frame-selection-method svlgaussian \
  --frame-svlgaussian-offsets 5 10 \
  --frame-svlgaussian-random-window 30 \
  --frame-svlgaussian-visibility-window 3 \
  --skip-export-image-blaster \
  "${mesh_args[@]}" \
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

"$V2M_PYTHON" -B -m video2mesh.cli evaluate \
  --project-root "$PROJECT_ROOT" 2>&1 | tee -a "$LOG" || true

"$V2M_PYTHON" -B -m video2mesh.cli production-readiness \
  --project-root "$PROJECT_ROOT" \
  --no-require-scale-calibration 2>&1 | tee -a "$LOG" || true

"$V2M_PYTHON" -B -m video2mesh.cli target-capability-matrix \
  --project-root "$PROJECT_ROOT" 2>&1 | tee -a "$LOG" || true

echo "[Video2Mesh downstream] complete: $PROJECT_ROOT" | tee -a "$LOG"
