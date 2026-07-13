#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/run_video2mesh_quick.sh /path/to/video.mp4

Convention-over-configuration quick entrypoint for the full Video2Mesh baseline:
video -> dense real frames -> COLMAP sparse point cloud/poses -> GraphDECO 3DGS ->
GroundingDINO bbox prompts, with SAM/OpenCV auto prompts as fallback -> SAM2 masks ->
3D semantic masks/probabilities -> SVLGaussian frame selection -> coarse meshes ->
simulator assets and QA reports.
The default quick route now also builds a COLMAP dense Delaunay scene collider,
backfills semantic labels onto its faces, and splits one scene-space mesh per object.

Optional environment overrides:
  VIDEO2MESH_ROOT=/root/autodl-tmp/workspace/Video2Mesh
  PROJECT_ROOT=/custom/output/dir
  SCENE_ID=my_scene
  RUN_SAM2=1|0
  RUN_MAST3R=1|0
  RUN_COLMAP=1|0
  MAST3R_CONFIG=config/base.yaml
  MAST3R_CALIB=/path/to/intrinsics.yaml
  COLMAP_BINARY=colmap
  SCENE_MESH_COLMAP_BINARY=colmap
  COLMAP_MATCHER=exhaustive
  COLMAP_GPU_INDEX="-1"
  COLMAP_DENSE_GPU_INDEX="-1"
  GRAPHDECO_CUDA_VISIBLE_DEVICES=""
  SAM_DEVICE=cuda
  SAM2_DEVICE=cuda
  GROUNDINGDINO_DEVICE=auto
  COLMAP_MAPPER_EXTRA_ARGS=""
  GS_BACKEND=graphdeco|minimal|none
  GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting
  GRAPHDECO_ITERATIONS=30000
  GRAPHDECO_SAVE_ITERATIONS="7000 30000"
  GRAPHDECO_TEST_ITERATIONS="7000 30000"
  GRAPHDECO_DENSIFY_UNTIL_ITER=5000
  GRAPHDECO_DENSIFY_FROM_ITER=1000
  GRAPHDECO_DENSIFICATION_INTERVAL=300
  GRAPHDECO_DENSIFY_GRAD_THRESHOLD=0.002
  GRAPHDECO_OPACITY_RESET_INTERVAL=3000
  GRAPHDECO_SH_DEGREE=3
  GRAPHDECO_EXTRA_ARGS=""
  RENDER_GSPLAT_PREVIEW=1|0
  STRICT_3DGS_PRESERVE_BACKGROUND_PLANES=1
  STRICT_3DGS_GEOMETRIC_OUTLIERS=0
  STRICT_3DGS_ELONGATION_FILTER=0
  GAUSSIAN_BACKPROJECT=0|1
  PROMPT_DISCOVERY=groundingdino|auto-prompts
  GROUNDINGDINO_ROOT=/root/autodl-tmp/workspace/GroundingDINO
  GROUNDINGDINO_CHECKPOINT=/root/autodl-tmp/checkpoints/groundingdino/groundingdino_swint_ogc.pth
  GROUNDINGDINO_CONFIG=/path/to/GroundingDINO_SwinT_OGC.py
  OBJECT_PROMPT_QUERIES="bed,chair,table,window,curtain,door,lamp,plant,nightstand"
  MAX_FRAMES=200
  START_SEC=
  END_SEC=
  DURATION_SEC=
  AUTO_PROMPT_MAX_OBJECTS=20
  AUTO_PROMPT_MIN_AREA_RATIO=0.001
  AUTO_PROMPT_GRANULARITY=balanced
  MASK_MESH_METHOD=auto
  RECONSTRUCT_SCENE_MESHES=1|0
  TRANSFER_SCENE_MESH_SEMANTICS=1|0
  SPLIT_SCENE_MESH_BY_SEMANTICS=1|0
  SCENE_MESH_SEMANTIC_ROUTE=local|projected-splats|nearest
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
MAST3R_CONFIG="${MAST3R_CONFIG:-config/base.yaml}"
MAST3R_CALIB="${MAST3R_CALIB:-}"
SAM2_ROOT="${SAM2_ROOT:-/root/autodl-tmp/workspace/sam2}"
SAM2_PYTHON="${SAM2_PYTHON:-/root/autodl-tmp/workspace/venvs/v2m-sam2-clean/bin/python}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-${SAM2_ROOT}/checkpoints/sam2.1_hiera_tiny.pt}"
SAM2_MODEL_CFG="${SAM2_MODEL_CFG:-configs/sam2.1/sam2.1_hiera_t.yaml}"
SAM_CHECKPOINT="${SAM_CHECKPOINT:-/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth}"
SAM_MODEL_TYPE="${SAM_MODEL_TYPE:-vit_b}"
GRAPHDECO_ROOT="${GRAPHDECO_ROOT:-/root/autodl-tmp/workspace/gaussian-splatting}"
GRAPHDECO_PYTHON="${GRAPHDECO_PYTHON:-$V2M_PYTHON}"
GROUNDINGDINO_ROOT="${GROUNDINGDINO_ROOT:-/root/autodl-tmp/workspace/GroundingDINO}"
GROUNDINGDINO_CHECKPOINT="${GROUNDINGDINO_CHECKPOINT:-/root/autodl-tmp/checkpoints/groundingdino/groundingdino_swint_ogc.pth}"
GROUNDINGDINO_CONFIG="${GROUNDINGDINO_CONFIG:-}"
GROUNDINGDINO_DEVICE="${GROUNDINGDINO_DEVICE:-auto}"
SAM_DEVICE="${SAM_DEVICE:-cuda}"
SAM2_DEVICE="${SAM2_DEVICE:-cuda}"
OBJECT_PROMPT_QUERIES="${OBJECT_PROMPT_QUERIES:-}"

RUN_MAST3R="${RUN_MAST3R:-0}"
RUN_COLMAP="${RUN_COLMAP:-1}"
GS_BACKEND="${GS_BACKEND:-graphdeco}"
RUN_GSPLAT="${RUN_GSPLAT:-$([[ "$GS_BACKEND" == "minimal" ]] && printf 1 || printf 0)}"
RENDER_GSPLAT_PREVIEW="${RENDER_GSPLAT_PREVIEW:-1}"
RUN_SAM2="${RUN_SAM2:-1}"
MAX_FRAMES="${MAX_FRAMES:-200}"
EXTRACT_EVERY="${EXTRACT_EVERY:-1}"
START_SEC="${START_SEC:-}"
END_SEC="${END_SEC:-}"
DURATION_SEC="${DURATION_SEC:-}"
COLMAP_BINARY="${COLMAP_BINARY:-colmap}"
SCENE_MESH_COLMAP_BINARY="${SCENE_MESH_COLMAP_BINARY:-$COLMAP_BINARY}"
COLMAP_CAMERA_MODEL="${COLMAP_CAMERA_MODEL:-PINHOLE}"
COLMAP_CAMERA_PARAMS="${COLMAP_CAMERA_PARAMS:-}"
COLMAP_MATCHER="${COLMAP_MATCHER:-exhaustive}"
COLMAP_SEQUENTIAL_OVERLAP="${COLMAP_SEQUENTIAL_OVERLAP:-20}"
COLMAP_USE_GPU="${COLMAP_USE_GPU:-0}"
COLMAP_GPU_INDEX="${COLMAP_GPU_INDEX:-${CUDA_VISIBLE_DEVICES:--1}}"
COLMAP_GPU_INDEX="${COLMAP_GPU_INDEX// /}"
COLMAP_DENSE_GPU_INDEX="${COLMAP_DENSE_GPU_INDEX:-$COLMAP_GPU_INDEX}"
COLMAP_MAPPER_EXTRA_ARGS="${COLMAP_MAPPER_EXTRA_ARGS:-}"
COLMAP_REFINE_FOCAL_LENGTH="${COLMAP_REFINE_FOCAL_LENGTH:-1}"
COLMAP_REFINE_PRINCIPAL_POINT="${COLMAP_REFINE_PRINCIPAL_POINT:-0}"
COLMAP_REFINE_EXTRA_PARAMS="${COLMAP_REFINE_EXTRA_PARAMS:-0}"
GRAPHDECO_ITERATIONS="${GRAPHDECO_ITERATIONS:-30000}"
GRAPHDECO_RESOLUTION="${GRAPHDECO_RESOLUTION:-1}"
GRAPHDECO_SAVE_ITERATIONS="${GRAPHDECO_SAVE_ITERATIONS:-7000 30000}"
GRAPHDECO_TEST_ITERATIONS="${GRAPHDECO_TEST_ITERATIONS:-7000 30000}"
GRAPHDECO_DENSIFY_UNTIL_ITER="${GRAPHDECO_DENSIFY_UNTIL_ITER:-5000}"
GRAPHDECO_DENSIFY_FROM_ITER="${GRAPHDECO_DENSIFY_FROM_ITER:-1000}"
GRAPHDECO_DENSIFICATION_INTERVAL="${GRAPHDECO_DENSIFICATION_INTERVAL:-300}"
GRAPHDECO_DENSIFY_GRAD_THRESHOLD="${GRAPHDECO_DENSIFY_GRAD_THRESHOLD:-0.002}"
GRAPHDECO_OPACITY_RESET_INTERVAL="${GRAPHDECO_OPACITY_RESET_INTERVAL:-3000}"
GRAPHDECO_SH_DEGREE="${GRAPHDECO_SH_DEGREE:-3}"
GRAPHDECO_EXTRA_ARGS="${GRAPHDECO_EXTRA_ARGS:-}"
GRAPHDECO_CUDA_VISIBLE_DEVICES="${GRAPHDECO_CUDA_VISIBLE_DEVICES:-}"
GSPLAT_ITERATIONS="${GSPLAT_ITERATIONS:-500}"
GSPLAT_MAX_FRAMES="${GSPLAT_MAX_FRAMES:-6}"
GSPLAT_MAX_POINTS="${GSPLAT_MAX_POINTS:-24000}"
GSPLAT_WIDTH="${GSPLAT_WIDTH:-432}"
GSPLAT_HEIGHT="${GSPLAT_HEIGHT:-768}"
AUTO_PROMPT_MAX_OBJECTS="${AUTO_PROMPT_MAX_OBJECTS:-20}"
AUTO_PROMPT_FRAME_INDEX="${AUTO_PROMPT_FRAME_INDEX:-10}"
AUTO_PROMPT_MIN_AREA_RATIO="${AUTO_PROMPT_MIN_AREA_RATIO:-0.001}"
AUTO_PROMPT_MAX_AREA_RATIO="${AUTO_PROMPT_MAX_AREA_RATIO:-0.35}"
AUTO_PROMPT_MIN_WIDTH="${AUTO_PROMPT_MIN_WIDTH:-8}"
AUTO_PROMPT_MIN_HEIGHT="${AUTO_PROMPT_MIN_HEIGHT:-8}"
AUTO_PROMPT_NMS_IOU="${AUTO_PROMPT_NMS_IOU:-0.55}"
AUTO_PROMPT_CONTAINMENT_OVERLAP="${AUTO_PROMPT_CONTAINMENT_OVERLAP:-0.93}"
AUTO_PROMPT_CONTAINMENT_AREA_RATIO="${AUTO_PROMPT_CONTAINMENT_AREA_RATIO:-2.5}"
AUTO_PROMPT_GRANULARITY="${AUTO_PROMPT_GRANULARITY:-balanced}"
AUTO_PROMPT_MIN_PARENT_AREA_RATIO="${AUTO_PROMPT_MIN_PARENT_AREA_RATIO:-0.15}"
TRACK_MAX_FRAMES="${TRACK_MAX_FRAMES:-$MAX_FRAMES}"
PIXEL_STRIDE="${PIXEL_STRIDE:-3}"
MAX_PIXELS_PER_MASK="${MAX_PIXELS_PER_MASK:-5000}"
TOP_K="${TOP_K:-4}"
MASK_MESH_METHOD="${MASK_MESH_METHOD:-auto}"
MASK_MESH_FORMAT="${MASK_MESH_FORMAT:-ply}"
RUN_SIMULATOR_ADAPTERS="${RUN_SIMULATOR_ADAPTERS:-0}"
BACKGROUND_PLANE_INCLUDE_OTHER_PLANES="${BACKGROUND_PLANE_INCLUDE_OTHER_PLANES:-1}"
AUTO_MERGE_OBJECT_MASKS="${AUTO_MERGE_OBJECT_MASKS:-1}"
OBJECT_MERGE_APPLY="${OBJECT_MERGE_APPLY:-1}"
OBJECT_MERGE_MAX_COMPONENTS="${OBJECT_MERGE_MAX_COMPONENTS:-4}"
OBJECT_MERGE_MIN_COMPONENT_SCORE="${OBJECT_MERGE_MIN_COMPONENT_SCORE:-0.70}"
STRICT_3DGS_CLEAN="${STRICT_3DGS_CLEAN:-1}"
STRICT_3DGS_BBOX_PADDING_RATIO="${STRICT_3DGS_BBOX_PADDING_RATIO:-0.12}"
STRICT_3DGS_CLUSTER_EPS_RATIO="${STRICT_3DGS_CLUSTER_EPS_RATIO:-0.015}"
STRICT_3DGS_CLUSTER_MIN_POINTS="${STRICT_3DGS_CLUSTER_MIN_POINTS:-300}"
STRICT_3DGS_PRESERVE_BACKGROUND_PLANES="${STRICT_3DGS_PRESERVE_BACKGROUND_PLANES:-1}"
STRICT_3DGS_GEOMETRIC_OUTLIERS="${STRICT_3DGS_GEOMETRIC_OUTLIERS:-0}"
STRICT_3DGS_ELONGATION_FILTER="${STRICT_3DGS_ELONGATION_FILTER:-0}"
RECONSTRUCT_SCENE_MESHES="${RECONSTRUCT_SCENE_MESHES:-1}"
TRANSFER_SCENE_MESH_SEMANTICS="${TRANSFER_SCENE_MESH_SEMANTICS:-1}"
SPLIT_SCENE_MESH_BY_SEMANTICS="${SPLIT_SCENE_MESH_BY_SEMANTICS:-1}"
SCENE_MESH_SEMANTIC_ROUTE="${SCENE_MESH_SEMANTIC_ROUTE:-local}"
SCENE_MESH_SEMANTIC_MAX_POINTS="${SCENE_MESH_SEMANTIC_MAX_POINTS:-250000}"
SCENE_MESH_OBJECT_SPLITS_MIN_FACES="${SCENE_MESH_OBJECT_SPLITS_MIN_FACES:-20}"
GAUSSIAN_BACKPROJECT="${GAUSSIAN_BACKPROJECT:-1}"

PROMPT_DISCOVERY="${PROMPT_DISCOVERY:-groundingdino}"
prompt_discovery_args=()
prompt_discovery_label=""
groundingdino_fallback_reason=""
case "$PROMPT_DISCOVERY" in
  groundingdino)
    groundingdino_config_args=()
    if [[ -n "$GROUNDINGDINO_CONFIG" ]]; then
      if [[ -f "$GROUNDINGDINO_CONFIG" ]]; then
        groundingdino_config_args=(--groundingdino-config "$GROUNDINGDINO_CONFIG")
      else
        groundingdino_fallback_reason="GroundingDINO config not found: $GROUNDINGDINO_CONFIG"
      fi
    fi
    if [[ -z "$groundingdino_fallback_reason" && ! -f "$GROUNDINGDINO_CHECKPOINT" ]]; then
      groundingdino_fallback_reason="GroundingDINO checkpoint not found: $GROUNDINGDINO_CHECKPOINT"
    fi
    if [[ -z "$groundingdino_fallback_reason" && ! -d "$GROUNDINGDINO_ROOT" && -z "$GROUNDINGDINO_CONFIG" ]]; then
      groundingdino_fallback_reason="GroundingDINO root not found and no config was provided: $GROUNDINGDINO_ROOT"
    fi
    if [[ -z "$groundingdino_fallback_reason" ]]; then
      gdino_pythonpath="${PYTHONPATH:-}"
      if [[ -d "$GROUNDINGDINO_ROOT" ]]; then
        gdino_pythonpath="${GROUNDINGDINO_ROOT}:${gdino_pythonpath}"
      fi
      if ! PYTHONPATH="$gdino_pythonpath" "$V2M_PYTHON" - <<'PY' >/dev/null 2>&1
import groundingdino  # noqa: F401
PY
      then
        groundingdino_fallback_reason="GroundingDINO is not importable in $V2M_PYTHON"
      fi
    fi
    if [[ -z "$groundingdino_fallback_reason" ]]; then
      prompt_discovery_args=(--discover-object-prompts)
      if [[ -d "$GROUNDINGDINO_ROOT" ]]; then
        prompt_discovery_args+=(--groundingdino-root "$GROUNDINGDINO_ROOT")
      fi
      prompt_discovery_args+=(
        "${groundingdino_config_args[@]}"
        --groundingdino-checkpoint "$GROUNDINGDINO_CHECKPOINT"
        --groundingdino-device "$GROUNDINGDINO_DEVICE"
      )
      if [[ -n "$OBJECT_PROMPT_QUERIES" ]]; then
        prompt_discovery_args+=(--object-prompt-queries "$OBJECT_PROMPT_QUERIES")
      fi
      prompt_discovery_label="groundingdino"
    else
      prompt_discovery_args=(--auto-prompts)
      prompt_discovery_label="auto-prompts-fallback"
    fi
    ;;
  auto-prompts|auto_prompt|auto)
    prompt_discovery_args=(--auto-prompts)
    prompt_discovery_label="auto-prompts"
    ;;
  *)
    echo "[Video2Mesh quick] Unknown PROMPT_DISCOVERY: $PROMPT_DISCOVERY" >&2
    exit 2
    ;;
esac

AUTO_PROMPT_METHOD="${AUTO_PROMPT_METHOD:-sam}"
if [[ "$AUTO_PROMPT_METHOD" == "sam" && ! -f "$SAM_CHECKPOINT" ]]; then
  echo "[Video2Mesh quick] SAM checkpoint not found, falling back to OpenCV auto prompts: $SAM_CHECKPOINT" >&2
  AUTO_PROMPT_METHOD="opencv"
fi
MASK_BACKEND="${MASK_BACKEND:-$([[ "$RUN_SAM2" == "1" || "$RUN_SAM2" == "true" ]] && printf sam2 || printf opencv)}"
mast3r_calib_args=()
if [[ -n "$MAST3R_CALIB" ]]; then
  mast3r_calib_args=(--calib "$MAST3R_CALIB")
fi
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
echo "[Video2Mesh quick] prompt_discovery: $prompt_discovery_label" | tee -a "$LOG"
if [[ -n "$groundingdino_fallback_reason" ]]; then
  echo "[Video2Mesh quick] prompt_discovery_fallback_reason: $groundingdino_fallback_reason" | tee -a "$LOG"
fi
echo "[Video2Mesh quick] auto_prompt_method: $AUTO_PROMPT_METHOD" | tee -a "$LOG"
echo "[Video2Mesh quick] mask_backend: $MASK_BACKEND" | tee -a "$LOG"
echo "[Video2Mesh quick] gs_backend: $GS_BACKEND" | tee -a "$LOG"
echo "[Video2Mesh quick] reconstruction: colmap=${RUN_COLMAP} mast3r=${RUN_MAST3R} max_frames=${MAX_FRAMES} every=${EXTRACT_EVERY}" | tee -a "$LOG"
echo "[Video2Mesh quick] gpu: colmap=${COLMAP_GPU_INDEX} colmap_dense=${COLMAP_DENSE_GPU_INDEX} graphdeco_visible=${GRAPHDECO_CUDA_VISIBLE_DEVICES:-inherit} groundingdino=${GROUNDINGDINO_DEVICE} sam=${SAM_DEVICE} sam2=${SAM2_DEVICE}" | tee -a "$LOG"
echo "[Video2Mesh quick] gsplat_preview: ${RENDER_GSPLAT_PREVIEW}" | tee -a "$LOG"
echo "[Video2Mesh quick] scene_mesh: reconstruct=${RECONSTRUCT_SCENE_MESHES} transfer=${TRANSFER_SCENE_MESH_SEMANTICS} split=${SPLIT_SCENE_MESH_BY_SEMANTICS} route=${SCENE_MESH_SEMANTIC_ROUTE} colmap=${SCENE_MESH_COLMAP_BINARY}" | tee -a "$LOG"
echo "[Video2Mesh quick] defaults: strict_3dgs_clean=${STRICT_3DGS_CLEAN} scene_only=${STRICT_3DGS_GEOMETRIC_OUTLIERS}/${STRICT_3DGS_ELONGATION_FILTER} auto_merge=${AUTO_MERGE_OBJECT_MASKS}/${OBJECT_MERGE_APPLY} gaussian_backproject=${GAUSSIAN_BACKPROJECT} mask_mesh_format=${MASK_MESH_FORMAT} simulator_adapters=${RUN_SIMULATOR_ADAPTERS}" | tee -a "$LOG"

g3dgs_args=()
if [[ "$GS_BACKEND" == "graphdeco" ]]; then
  graphdeco_cuda_prefix=""
  if [[ -n "$GRAPHDECO_CUDA_VISIBLE_DEVICES" ]]; then
    graphdeco_cuda_prefix="CUDA_VISIBLE_DEVICES=${GRAPHDECO_CUDA_VISIBLE_DEVICES} "
  fi
  g3dgs_args=(
    --prepare-3dgs-source
    --g3dgs-output-path scene/reconstruction/3dgs_graphdeco
    --g3dgs-work-dir external/graphdeco_3dgs
    --g3dgs-clean-init-point-cloud
    --g3dgs-command-template "cd ${GRAPHDECO_ROOT} && ${graphdeco_cuda_prefix}${GRAPHDECO_PYTHON} train.py -s {source_path} -m {output_path} --iterations ${GRAPHDECO_ITERATIONS} --save_iterations ${GRAPHDECO_SAVE_ITERATIONS} --test_iterations ${GRAPHDECO_TEST_ITERATIONS} --resolution ${GRAPHDECO_RESOLUTION} --images images --sh_degree ${GRAPHDECO_SH_DEGREE} --densify_until_iter ${GRAPHDECO_DENSIFY_UNTIL_ITER} --densify_from_iter ${GRAPHDECO_DENSIFY_FROM_ITER} --densification_interval ${GRAPHDECO_DENSIFICATION_INTERVAL} --densify_grad_threshold ${GRAPHDECO_DENSIFY_GRAD_THRESHOLD} --opacity_reset_interval ${GRAPHDECO_OPACITY_RESET_INTERVAL} ${GRAPHDECO_EXTRA_ARGS} --disable_viewer"
  )
  if [[ "$STRICT_3DGS_CLEAN" == "1" || "$STRICT_3DGS_CLEAN" == "true" ]]; then
    g3dgs_args+=(
      --g3dgs-clean-strict-scene-filter
      --g3dgs-clean-bbox-padding-ratio "$STRICT_3DGS_BBOX_PADDING_RATIO"
      --g3dgs-clean-cluster-eps-ratio "$STRICT_3DGS_CLUSTER_EPS_RATIO"
      --g3dgs-clean-cluster-min-points "$STRICT_3DGS_CLUSTER_MIN_POINTS"
    )
    if [[ "$STRICT_3DGS_GEOMETRIC_OUTLIERS" == "1" || "$STRICT_3DGS_GEOMETRIC_OUTLIERS" == "true" ]]; then
      g3dgs_args+=(--g3dgs-clean-geometric-outliers)
    else
      g3dgs_args+=(--no-g3dgs-clean-geometric-outliers)
    fi
    if [[ "$STRICT_3DGS_ELONGATION_FILTER" == "1" || "$STRICT_3DGS_ELONGATION_FILTER" == "true" ]]; then
      g3dgs_args+=(--g3dgs-clean-elongation-filter)
    else
      g3dgs_args+=(--no-g3dgs-clean-elongation-filter)
    fi
    if [[ "$STRICT_3DGS_PRESERVE_BACKGROUND_PLANES" == "1" || "$STRICT_3DGS_PRESERVE_BACKGROUND_PLANES" == "true" ]]; then
      g3dgs_args+=(--g3dgs-clean-preserve-background-planes)
    else
      g3dgs_args+=(--no-g3dgs-clean-preserve-background-planes)
    fi
  else
    g3dgs_args+=(--no-g3dgs-clean-strict-scene-filter)
  fi
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

time_window_args=()
if [[ -n "$START_SEC" ]]; then
  time_window_args+=(--start-sec "$START_SEC")
fi
if [[ -n "$END_SEC" ]]; then
  time_window_args+=(--end-sec "$END_SEC")
fi
if [[ -n "$DURATION_SEC" ]]; then
  time_window_args+=(--duration-sec "$DURATION_SEC")
fi

colmap_args=()
if [[ "$RUN_COLMAP" == "1" || "$RUN_COLMAP" == "true" ]]; then
  colmap_args=(
    --run-colmap
    --colmap-binary "$COLMAP_BINARY"
    --colmap-camera-model "$COLMAP_CAMERA_MODEL"
    --colmap-matcher "$COLMAP_MATCHER"
    --colmap-sequential-overlap "$COLMAP_SEQUENTIAL_OVERLAP"
    --colmap-gpu-index "$COLMAP_GPU_INDEX"
    --colmap-dense-gpu-index "$COLMAP_DENSE_GPU_INDEX"
  )
  if [[ -n "$COLMAP_CAMERA_PARAMS" ]]; then
    colmap_args+=(--colmap-camera-params "$COLMAP_CAMERA_PARAMS")
  fi
  if [[ -n "$COLMAP_MAPPER_EXTRA_ARGS" ]]; then
    colmap_args+=(--colmap-mapper-extra-args "$COLMAP_MAPPER_EXTRA_ARGS")
  fi
  if [[ "$COLMAP_USE_GPU" == "1" || "$COLMAP_USE_GPU" == "true" ]]; then
    colmap_args+=(--colmap-use-gpu)
  else
    colmap_args+=(--no-colmap-use-gpu)
  fi
  if [[ "$COLMAP_REFINE_FOCAL_LENGTH" == "1" || "$COLMAP_REFINE_FOCAL_LENGTH" == "true" ]]; then
    colmap_args+=(--colmap-refine-focal-length)
  else
    colmap_args+=(--no-colmap-refine-focal-length)
  fi
  if [[ "$COLMAP_REFINE_PRINCIPAL_POINT" == "1" || "$COLMAP_REFINE_PRINCIPAL_POINT" == "true" ]]; then
    colmap_args+=(--colmap-refine-principal-point)
  else
    colmap_args+=(--no-colmap-refine-principal-point)
  fi
  if [[ "$COLMAP_REFINE_EXTRA_PARAMS" == "1" || "$COLMAP_REFINE_EXTRA_PARAMS" == "true" ]]; then
    colmap_args+=(--colmap-refine-extra-params)
  else
    colmap_args+=(--no-colmap-refine-extra-params)
  fi
fi

scene_mesh_args=()
if [[ "$RECONSTRUCT_SCENE_MESHES" == "1" || "$RECONSTRUCT_SCENE_MESHES" == "true" ]]; then
  scene_mesh_args+=(
    --reconstruct-scene-meshes
    --scene-mesh-colmap-binary "$SCENE_MESH_COLMAP_BINARY"
  )
fi
if [[ "$TRANSFER_SCENE_MESH_SEMANTICS" == "1" || "$TRANSFER_SCENE_MESH_SEMANTICS" == "true" ]]; then
  scene_mesh_args+=(
    --transfer-scene-mesh-semantics
    --scene-mesh-semantic-route "$SCENE_MESH_SEMANTIC_ROUTE"
    --scene-mesh-semantic-max-points "$SCENE_MESH_SEMANTIC_MAX_POINTS"
  )
fi
if [[ "$SPLIT_SCENE_MESH_BY_SEMANTICS" == "1" || "$SPLIT_SCENE_MESH_BY_SEMANTICS" == "true" ]]; then
  scene_mesh_args+=(
    --split-scene-mesh-by-semantics
    --scene-mesh-object-splits-min-faces "$SCENE_MESH_OBJECT_SPLITS_MIN_FACES"
    --scene-mesh-object-splits-register-as-object-meshes
  )
fi

background_plane_args=()
if [[ "$BACKGROUND_PLANE_INCLUDE_OTHER_PLANES" == "1" || "$BACKGROUND_PLANE_INCLUDE_OTHER_PLANES" == "true" ]]; then
  background_plane_args+=(--background-plane-include-other-planes)
fi

object_merge_args=()
if [[ "$AUTO_MERGE_OBJECT_MASKS" == "1" || "$AUTO_MERGE_OBJECT_MASKS" == "true" ]]; then
  object_merge_args+=(
    --auto-merge-object-masks
    --object-merge-apply-max-components "$OBJECT_MERGE_MAX_COMPONENTS"
    --object-merge-apply-min-component-score "$OBJECT_MERGE_MIN_COMPONENT_SCORE"
  )
  if [[ "$OBJECT_MERGE_APPLY" == "1" || "$OBJECT_MERGE_APPLY" == "true" ]]; then
    object_merge_args+=(--object-merge-apply)
  else
    object_merge_args+=(--no-object-merge-apply)
  fi
else
  object_merge_args+=(--no-auto-merge-object-masks)
fi

simulator_adapter_args=()
if [[ "$RUN_SIMULATOR_ADAPTERS" == "1" || "$RUN_SIMULATOR_ADAPTERS" == "true" ]]; then
  simulator_adapter_args+=(--no-skip-simulator-adapters)
else
  simulator_adapter_args+=(--skip-simulator-adapters)
fi

gaussian_backproject_args=()
if [[ "$GAUSSIAN_BACKPROJECT" == "1" || "$GAUSSIAN_BACKPROJECT" == "true" ]]; then
  gaussian_backproject_args+=(
    --backproject-gaussian-probabilities
    --gaussian-backproject-pixel-stride "$PIXEL_STRIDE"
    --gaussian-backproject-max-pixels-per-mask "$MAX_PIXELS_PER_MASK"
    --gaussian-backproject-include-background-structures
  )
fi

gsplat_preview_args=()
if [[ "$RENDER_GSPLAT_PREVIEW" == "1" || "$RENDER_GSPLAT_PREVIEW" == "true" ]]; then
  gsplat_preview_args+=(
    --render-gsplat-preview
    --preview-max-frames 6
    --preview-width "$GSPLAT_WIDTH"
    --preview-height "$GSPLAT_HEIGHT"
  )
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
  "${time_window_args[@]}" \
  --overwrite-frames \
  $([[ "$RUN_MAST3R" == "1" || "$RUN_MAST3R" == "true" ]] && printf '%s ' --run-mast3r-slam) \
  --mast3r-root "$MAST3R_ROOT" \
  --mast3r-config "$MAST3R_CONFIG" \
  "${mast3r_calib_args[@]}" \
  --mast3r-save-as "$SCENE_ID" \
  --focal-scale 1.2 \
  "${colmap_args[@]}" \
  --render-reconstruction-preview \
  --reconstruction-preview-max-frames 4 \
  --reconstruction-preview-max-points 12000 \
  "${g3dgs_args[@]}" \
  "${gsplat_preview_args[@]}" \
  "${prompt_discovery_args[@]}" \
  --auto-prompt-method "$AUTO_PROMPT_METHOD" \
  --auto-prompt-frame-index "$AUTO_PROMPT_FRAME_INDEX" \
  --auto-prompt-max-objects "$AUTO_PROMPT_MAX_OBJECTS" \
  --auto-prompt-min-area-ratio "$AUTO_PROMPT_MIN_AREA_RATIO" \
  --auto-prompt-max-area-ratio "$AUTO_PROMPT_MAX_AREA_RATIO" \
  --auto-prompt-min-width "$AUTO_PROMPT_MIN_WIDTH" \
  --auto-prompt-min-height "$AUTO_PROMPT_MIN_HEIGHT" \
  --auto-prompt-nms-iou "$AUTO_PROMPT_NMS_IOU" \
  --auto-prompt-containment-overlap "$AUTO_PROMPT_CONTAINMENT_OVERLAP" \
  --auto-prompt-containment-area-ratio "$AUTO_PROMPT_CONTAINMENT_AREA_RATIO" \
  --auto-prompt-granularity "$AUTO_PROMPT_GRANULARITY" \
  --auto-prompt-min-parent-area-ratio "$AUTO_PROMPT_MIN_PARENT_AREA_RATIO" \
  --sam-checkpoint "$SAM_CHECKPOINT" \
  --sam-model-type "$SAM_MODEL_TYPE" \
  --sam-device "$SAM_DEVICE" \
  --mask-backend "$MASK_BACKEND" \
  --sam2-checkpoint "$SAM2_CHECKPOINT" \
  --sam2-model-cfg "$SAM2_MODEL_CFG" \
  --sam2-device "$SAM2_DEVICE" \
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
  "${background_plane_args[@]}" \
  "${object_merge_args[@]}" \
  --transfer-mode nearest \
  "${gaussian_backproject_args[@]}" \
  --render-semantic-preview \
  --semantic-preview-max-frames 6 \
  --semantic-preview-max-points 20000 \
  "${scene_mesh_args[@]}" \
  --top-k "$TOP_K" \
  --frame-selection-method svlgaussian \
  --frame-svlgaussian-offsets 5 10 \
  --frame-svlgaussian-random-window 30 \
  --frame-svlgaussian-visibility-window 3 \
  --reconstruct-mask-meshes \
  --mask-mesh-method "$MASK_MESH_METHOD" \
  --mask-mesh-format "$MASK_MESH_FORMAT" \
  --skip-failed-mask-meshes \
  --skip-export-image-blaster \
  --simulator-format mujoco unity \
  "${simulator_adapter_args[@]}" \
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
