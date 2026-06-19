#!/usr/bin/env bash
set -euo pipefail

# Refresh the milscene3 full-frame SAM2 downstream artifacts.
# By default this reuses masks/2d_sam2_full72_tiny and does not rerun SAM2.
# Set RUN_SAM2=1 to regenerate the 72-frame SAM2 masks before refreshing.

ROOT="${VIDEO2MESH_ROOT:-/root/autodl-tmp/workspace/Video2Mesh}"
PROJECT_ROOT="${PROJECT_ROOT:-${ROOT}/exports/milscene3_full_20260618_124804}"
SAM2_ROOT="${SAM2_ROOT:-/root/autodl-tmp/workspace/sam2}"
V2M_PYTHON="${V2M_PYTHON:-/root/autodl-tmp/venvs/v2m-svpp/bin/python}"
SAM2_PYTHON="${SAM2_PYTHON:-/root/autodl-tmp/workspace/venvs/v2m-sam2-clean/bin/python}"

FRAMES_DIR="${FRAMES_DIR:-${PROJECT_ROOT}/scene/frames}"
PROMPTS="${PROMPTS:-${PROJECT_ROOT}/masks/auto_prompts.json}"
MASK_ROOT="${MASK_ROOT:-${PROJECT_ROOT}/masks/2d_sam2_full72_tiny}"
POINT_CLOUD="${POINT_CLOUD:-${PROJECT_ROOT}/scene/reconstruction/point_cloud.ply}"
SPLAT_PLY="${SPLAT_PLY:-${PROJECT_ROOT}/scene/reconstruction/3dgs/point_cloud/iteration_500/point_cloud.ply}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-${SAM2_ROOT}/checkpoints/sam2.1_hiera_tiny.pt}"
SAM2_MODEL_CFG="${SAM2_MODEL_CFG:-configs/sam2.1/sam2.1_hiera_t.yaml}"

RUN_SAM2="${RUN_SAM2:-0}"
MAX_FRAMES="${MAX_FRAMES:-72}"
PIXEL_STRIDE="${PIXEL_STRIDE:-4}"
MAX_PIXELS_PER_MASK="${MAX_PIXELS_PER_MASK:-3000}"

cd "$ROOT"

if [[ ! -x "$V2M_PYTHON" ]]; then
  echo "[Video2Mesh] Missing V2M_PYTHON: $V2M_PYTHON" >&2
  exit 2
fi

if [[ ! -f "$POINT_CLOUD" ]]; then
  echo "[Video2Mesh] Missing full point cloud: $POINT_CLOUD" >&2
  exit 2
fi
if [[ "$(basename "$POINT_CLOUD")" =~ ^point_cloud_([0-9]+|[0-9]+k|10k|30k)\.ply$ ]]; then
  echo "[Video2Mesh] Refusing downsampled point cloud for fusion/semantic refresh: $POINT_CLOUD" >&2
  exit 2
fi
if [[ ! -f "$SPLAT_PLY" ]]; then
  echo "[Video2Mesh] Missing active 3DGS PLY: $SPLAT_PLY" >&2
  exit 2
fi

echo "[Video2Mesh] project: $PROJECT_ROOT"
echo "[Video2Mesh] mask root: $MASK_ROOT"
echo "[Video2Mesh] point cloud: $POINT_CLOUD"
echo "[Video2Mesh] 3DGS PLY: $SPLAT_PLY"

if [[ "$RUN_SAM2" == "1" || "$RUN_SAM2" == "true" ]]; then
  if [[ ! -x "$SAM2_PYTHON" ]]; then
    echo "[Video2Mesh] Missing SAM2_PYTHON: $SAM2_PYTHON" >&2
    exit 2
  fi
  export PYTHONPATH="${SAM2_ROOT}:${ROOT}:${PYTHONPATH:-}"
  export SAM2_ROOT
  "$SAM2_PYTHON" -B -m video2mesh.cli track-masks \
    --project-root "$PROJECT_ROOT" \
    --prompts "$PROMPTS" \
    --frames-dir "$FRAMES_DIR" \
    --output-dir "$MASK_ROOT" \
    --clear-output \
    --mask-backend sam2 \
    --sam2-checkpoint "$SAM2_CHECKPOINT" \
    --sam2-model-cfg "$SAM2_MODEL_CFG" \
    --sam2-device cuda \
    --sam2-offload-video-to-cpu \
    --sam2-offload-state-to-cpu \
    --max-frames "$MAX_FRAMES"
fi

"$V2M_PYTHON" -B -m video2mesh.cli mask-track-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli fuse-masks \
  --project-root "$PROJECT_ROOT" \
  --mask-root "$MASK_ROOT" \
  --point-cloud "$POINT_CLOUD" \
  --fusion-mode probability

"$V2M_PYTHON" -B -m video2mesh.cli export-splat-masks \
  --project-root "$PROJECT_ROOT" \
  --splat-ply "$SPLAT_PLY" \
  --mask-source-ply "$POINT_CLOUD" \
  --transfer-mode nearest \
  --include-probabilities

"$V2M_PYTHON" -B -m video2mesh.cli backproject-gaussian-probabilities \
  --project-root "$PROJECT_ROOT" \
  --mask-root "$MASK_ROOT" \
  --splat-ply "$SPLAT_PLY" \
  --pixel-stride "$PIXEL_STRIDE" \
  --max-pixels-per-mask "$MAX_PIXELS_PER_MASK" \
  --include-background-structures \
  --merge-background-structure-masks \
  --background-mask-source-ply "$POINT_CLOUD"

"$V2M_PYTHON" -B -m video2mesh.cli export-viewer-plys \
  --project-root "$PROJECT_ROOT" \
  --kind scene \
  --kind semantic

"$V2M_PYTHON" -B -m video2mesh.cli export-object-mask-clouds \
  --project-root "$PROJECT_ROOT" \
  --skip-missing

"$V2M_PYTHON" -B -m video2mesh.cli render-semantic-preview \
  --project-root "$PROJECT_ROOT" \
  --max-frames 6

"$V2M_PYTHON" -B -m video2mesh.cli gaussian-probability-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli select-frames \
  --project-root "$PROJECT_ROOT" \
  --selection-method svlgaussian \
  --svlgaussian-offsets 5 10 \
  --svlgaussian-random-window 30 \
  --svlgaussian-visibility-window 3 \
  --top-k 4

"$V2M_PYTHON" -B -m video2mesh.cli frame-selection-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli prepare-object-images \
  --project-root "$PROJECT_ROOT" \
  --top-k 4 \
  --skip-missing

"$V2M_PYTHON" -B -m video2mesh.cli reconstruct-object-meshes \
  --project-root "$PROJECT_ROOT" \
  --method bbox \
  --skip-missing \
  --skip-failed

"$V2M_PYTHON" -B -m video2mesh.cli export-simulator-assets \
  --project-root "$PROJECT_ROOT" \
  --collision-proxy bbox \
  --use-collision-proxy \
  --collider box \
  --body-type dynamic

"$V2M_PYTHON" -B -m video2mesh.cli calibrate-simulator-assets \
  --project-root "$PROJECT_ROOT" \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --estimate-physics \
  --overwrite-physics \
  --collider box

"$V2M_PYTHON" -B -m video2mesh.cli export-simulator-adapter \
  --project-root "$PROJECT_ROOT" \
  --format mujoco unity

"$V2M_PYTHON" -B -m video2mesh.cli qa-simulator-assets \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli mesh-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli simulator-physics-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli label-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli object-instance-quality-report \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli evaluate \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli validate \
  --project-root "$PROJECT_ROOT" \
  --output "$PROJECT_ROOT/simulator_assets/validation_report.json"

"$V2M_PYTHON" -B -m video2mesh.cli production-readiness \
  --project-root "$PROJECT_ROOT" \
  --no-require-scale-calibration

"$V2M_PYTHON" -B -m video2mesh.cli target-capability-matrix \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli export-advisor-demo-summary \
  --project-root "$PROJECT_ROOT"

"$V2M_PYTHON" -B -m video2mesh.cli verify-showcase-pack \
  --project-root "$PROJECT_ROOT" \
  --require-semantic-probability \
  --no-require-review-tar \
  --no-scan-common-remote-roots

echo "[Video2Mesh] milscene3 SAM2 full-frame downstream refresh complete."
echo "[Video2Mesh] showcase: $PROJECT_ROOT/simulator_assets/showcase_pack_verification.json"
