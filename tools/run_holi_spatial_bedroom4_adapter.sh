#!/usr/bin/env bash
set -euo pipefail

ROOT="${VIDEO2MESH_ROOT:-/data/zyx/workspace/Video2MeshWorkspace/Video2Mesh}"
WORKSPACE="${VIDEO2MESH_WORKSPACE:-/data/zyx/workspace/Video2MeshWorkspace}"
SOURCE_PROJECT="${SOURCE_PROJECT:-${WORKSPACE}/video2mesh_runs/bedroom_4_scene_only_v2mw_20260709_030359}"
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d_%H%M%S)}"
PROJECT_ROOT="${PROJECT_ROOT:-${WORKSPACE}/video2mesh_runs/bedroom_4_holi_adapter_${RUN_TAG}}"
HOLI_ROOT="${HOLI_ROOT:-/data/zyx/workspace/holi_spatial_runs/bedroom_4_holi_adapter_${RUN_TAG}}"

V2M_PYTHON="${V2M_PYTHON:-/data/anaconda3/envs/sam2/bin/python}"
DINO_PYTHON="${DINO_PYTHON:-/opt/envs/max/bin/python}"
HOLI_PYTHON="${HOLI_PYTHON:-/data/anaconda3/bin/python}"
GROUNDINGDINO_ROOT="${GROUNDINGDINO_ROOT:-${WORKSPACE}/third_party/GroundingDINO}"
GROUNDINGDINO_CHECKPOINT="${GROUNDINGDINO_CHECKPOINT:-${WORKSPACE}/checkpoints/groundingdino/groundingdino_swint_ogc.pth}"
GROUNDINGDINO_CONFIG="${GROUNDINGDINO_CONFIG:-${GROUNDINGDINO_ROOT}/groundingdino/config/GroundingDINO_SwinT_OGC.py}"
SAM2_ROOT="${SAM2_ROOT:-${WORKSPACE}/third_party/sam2}"
SAM2_CHECKPOINT="${SAM2_CHECKPOINT:-${WORKSPACE}/checkpoints/sam2/sam2.1_hiera_tiny.pt}"
SAM2_MODEL_CFG="${SAM2_MODEL_CFG:-configs/sam2.1/sam2.1_hiera_t.yaml}"
DA3_ROOT="${DA3_ROOT:-/data/wzj/Depth-Anything-3}"
HOLI_CODE_ROOT="${HOLI_CODE_ROOT:-/data/zyx/workspace/third_party/holi-spatial}"

MAX_FRAMES="${MAX_FRAMES:-80}"
OBJECT_QUERIES="${OBJECT_QUERIES:-bed,nightstand,lamp,plant,window,wall art,floor,wall,ceiling,door,curtain,cabinet,desk,table}"
RUN_DA3_PROBE="${RUN_DA3_PROBE:-1}"
RUN_HOLI_QA="${RUN_HOLI_QA:-1}"
RESUME="${RESUME:-0}"
USE_EXISTING_BASELINE="${USE_EXISTING_BASELINE:-0}"

export PYTHONPATH="${ROOT}:${GROUNDINGDINO_ROOT}:${SAM2_ROOT}:${PYTHONPATH:-}"
export SAM2_ROOT

mkdir -p "$PROJECT_ROOT/logs/holi_adapter"
LOG_DIR="$PROJECT_ROOT/logs/holi_adapter"
SUMMARY="$PROJECT_ROOT/logs/holi_adapter_summary.json"

run_step() {
  local name="$1"
  shift
  echo "[Holi adapter] >>> $name"
  mkdir -p "$LOG_DIR"
  {
    echo "## $name"
    date -Is
    printf 'command:'
    printf ' %q' "$@"
    printf '\n\n'
    "$@"
  } 2>&1 | tee "$LOG_DIR/${name}.log"
}

if [[ ! -d "$SOURCE_PROJECT" ]]; then
  echo "[Holi adapter] Missing SOURCE_PROJECT: $SOURCE_PROJECT" >&2
  exit 2
fi
if [[ ! -x "$V2M_PYTHON" ]]; then
  echo "[Holi adapter] Missing V2M_PYTHON: $V2M_PYTHON" >&2
  exit 2
fi
if [[ ! -x "$DINO_PYTHON" ]]; then
  echo "[Holi adapter] Missing DINO_PYTHON: $DINO_PYTHON" >&2
  exit 2
fi
if [[ ! -x "$HOLI_PYTHON" ]]; then
  echo "[Holi adapter] Missing HOLI_PYTHON: $HOLI_PYTHON" >&2
  exit 2
fi

echo "[Holi adapter] source:  $SOURCE_PROJECT"
echo "[Holi adapter] project: $PROJECT_ROOT"
echo "[Holi adapter] holi:    $HOLI_ROOT"

if [[ "$RESUME" == "1" || "$RESUME" == "true" ]]; then
  if [[ ! -f "$PROJECT_ROOT/manifest.json" ]]; then
    echo "[Holi adapter] RESUME=1 but PROJECT_ROOT has no manifest.json: $PROJECT_ROOT" >&2
    exit 2
  fi
  echo "[Holi adapter] RESUME=1; reusing existing project root"
elif [[ "$PROJECT_ROOT" != "$SOURCE_PROJECT" ]]; then
  rm -rf "$PROJECT_ROOT"
  mkdir -p "$(dirname "$PROJECT_ROOT")"
  run_step copy_source rsync -a --delete \
    --exclude 'logs/holi_adapter' \
    "$SOURCE_PROJECT/" "$PROJECT_ROOT/"
fi
mkdir -p "$LOG_DIR"

if [[ "$RESUME" == "1" || "$RESUME" == "true" ]]; then
  echo "[Holi adapter] RESUME=1; skipping localize_paths"
else
  run_step localize_paths "$V2M_PYTHON" -B -m video2mesh.cli localize-export-paths \
    --project-root "$PROJECT_ROOT" \
    --local-root "$PROJECT_ROOT" \
    --no-infer-common-remote-roots \
    --fail-on-residual
fi

DA3_STATUS="not_run"
if [[ "$RUN_DA3_PROBE" == "1" || "$RUN_DA3_PROBE" == "true" ]]; then
  if timeout 30 env PYTHONPATH="${DA3_ROOT}/src:${PYTHONPATH:-}" "$V2M_PYTHON" - <<'PY' >"$LOG_DIR/da3_probe.log" 2>&1
from depth_anything_3.api import DepthAnything3
print("DA3 import ok", DepthAnything3)
PY
  then
    DA3_STATUS="import_ok_not_executed"
  else
    DA3_STATUS="probe_failed_or_timed_out"
  fi
fi

if [[ "$USE_EXISTING_BASELINE" == "1" || "$USE_EXISTING_BASELINE" == "true" ]]; then
  for required in \
    "$PROJECT_ROOT/masks/object_prompts_groundingdino.json" \
    "$PROJECT_ROOT/masks/2d/tracking_manifest.json" \
    "$PROJECT_ROOT/masks/3d/object_masks.json" \
    "$PROJECT_ROOT/masks/object_labels.json" \
    "$PROJECT_ROOT/simulator_assets/object_images.json" \
    "$PROJECT_ROOT/simulator_assets/semantic_splats.ply"; do
    if [[ ! -s "$required" ]]; then
      echo "[Holi adapter] USE_EXISTING_BASELINE=1 but missing required artifact: $required" >&2
      exit 2
    fi
  done
  echo "[Holi adapter] USE_EXISTING_BASELINE=1; reusing existing GroundingDINO/SAM2/2D-to-3D artifacts"
else
  run_step discover_object_prompts "$DINO_PYTHON" -B -m video2mesh.cli discover-object-prompts \
    --project-root "$PROJECT_ROOT" \
    --frames-dir "$PROJECT_ROOT/scene/frames" \
    --queries "$OBJECT_QUERIES" \
    --max-frames "$MAX_FRAMES" \
    --anchor-frame-count 5 \
    --groundingdino-root "$GROUNDINGDINO_ROOT" \
    --groundingdino-config "$GROUNDINGDINO_CONFIG" \
    --groundingdino-checkpoint "$GROUNDINGDINO_CHECKPOINT" \
    --groundingdino-device cuda \
    --max-objects 20 \
    --max-instances-per-label 4 \
    --single-instance-labels bed \
    --overwrite

  run_step track_masks_sam2 "$V2M_PYTHON" -B -m video2mesh.cli track-masks \
    --project-root "$PROJECT_ROOT" \
    --prompts "$PROJECT_ROOT/masks/object_prompts_groundingdino.json" \
    --frames-dir "$PROJECT_ROOT/scene/frames" \
    --output-dir "$PROJECT_ROOT/masks/2d" \
    --clear-output \
    --mask-backend sam2 \
    --sam2-checkpoint "$SAM2_CHECKPOINT" \
    --sam2-model-cfg "$SAM2_MODEL_CFG" \
    --sam2-device cuda \
    --sam2-offload-video-to-cpu \
    --sam2-offload-state-to-cpu \
    --max-frames "$MAX_FRAMES"

  run_step mask_track_quality "$V2M_PYTHON" -B -m video2mesh.cli mask-track-quality-report \
    --project-root "$PROJECT_ROOT" \
    --output "$PROJECT_ROOT/simulator_assets/mask_track_quality_report.json"

  run_step fuse_masks "$V2M_PYTHON" -B -m video2mesh.cli fuse-masks \
    --project-root "$PROJECT_ROOT" \
    --mask-root "$PROJECT_ROOT/masks/2d" \
    --point-cloud "$PROJECT_ROOT/scene/reconstruction/point_cloud.ply" \
    --fusion-mode probability \
    --min-votes 1 \
    --depth-tolerance 0.05 \
    --relative-depth-tolerance 0.03

  run_step infer_background_planes "$V2M_PYTHON" -B -m video2mesh.cli infer-background-plane-masks \
    --project-root "$PROJECT_ROOT" \
    --point-cloud "$PROJECT_ROOT/scene/reconstruction/point_cloud.ply" \
    --max-planes 8 \
    --min-points 300 \
    --replace-existing

  run_step export_splat_masks "$V2M_PYTHON" -B -m video2mesh.cli export-splat-masks \
    --project-root "$PROJECT_ROOT" \
    --splat-ply "$PROJECT_ROOT/scene/reconstruction/3dgs/point_cloud/iteration_30000/point_cloud_clean_strict.ply" \
    --mask-source-ply "$PROJECT_ROOT/scene/reconstruction/point_cloud.ply" \
    --transfer-mode nearest \
    --include-probabilities

  run_step backproject_gaussian_probabilities "$V2M_PYTHON" -B -m video2mesh.cli backproject-gaussian-probabilities \
    --project-root "$PROJECT_ROOT" \
    --mask-root "$PROJECT_ROOT/masks/2d" \
    --splat-ply "$PROJECT_ROOT/scene/reconstruction/3dgs/point_cloud/iteration_30000/point_cloud_clean_strict.ply" \
    --pixel-stride 3 \
    --max-pixels-per-mask 5000 \
    --include-background-structures \
    --merge-background-structure-masks \
    --background-mask-source-ply "$PROJECT_ROOT/scene/reconstruction/point_cloud.ply"

  run_step gaussian_probability_quality "$V2M_PYTHON" -B -m video2mesh.cli gaussian-probability-quality-report \
    --project-root "$PROJECT_ROOT" \
    --output "$PROJECT_ROOT/simulator_assets/gaussian_probability_quality_report.json"

  run_step export_viewer_plys "$V2M_PYTHON" -B -m video2mesh.cli export-viewer-plys \
    --project-root "$PROJECT_ROOT" \
    --kind all

  run_step export_object_mask_clouds "$V2M_PYTHON" -B -m video2mesh.cli export-object-mask-clouds \
    --project-root "$PROJECT_ROOT" \
    --point-cloud "$PROJECT_ROOT/scene/reconstruction/point_cloud.ply" \
    --skip-missing

  run_step select_frames "$V2M_PYTHON" -B -m video2mesh.cli select-frames \
    --project-root "$PROJECT_ROOT" \
    --selection-method svlgaussian \
    --svlgaussian-offsets 5 10 \
    --svlgaussian-random-window 30 \
    --svlgaussian-visibility-window 3 \
    --top-k 4

  run_step prepare_object_images "$V2M_PYTHON" -B -m video2mesh.cli prepare-object-images \
    --project-root "$PROJECT_ROOT" \
    --top-k 4 \
    --skip-missing

  run_step object_instance_quality "$V2M_PYTHON" -B -m video2mesh.cli object-instance-quality-report \
    --project-root "$PROJECT_ROOT" \
    --output "$PROJECT_ROOT/simulator_assets/object_instance_quality_report.json"
fi

run_step prepare_holi_package "$V2M_PYTHON" "$ROOT/tools/prepare_holi_spatial_bedroom4.py" \
  --source-root "$PROJECT_ROOT" \
  --output-root "$HOLI_ROOT" \
  --scene bedroom_4 \
  --max-masks-per-object "$MAX_FRAMES"

if [[ "$RUN_HOLI_QA" == "1" || "$RUN_HOLI_QA" == "true" ]]; then
  if [[ ! -f "$HOLI_ROOT/postprocess_3d_bbox_aabb.py" ]]; then
    cp "$HOLI_CODE_ROOT/postprocess_3d_bbox_aabb.py" "$HOLI_ROOT/"
  fi
  if [[ ! -d "$HOLI_ROOT/qa_generation" ]]; then
    cp -a "$HOLI_CODE_ROOT/qa_generation" "$HOLI_ROOT/"
  fi
  (
    cd "$HOLI_ROOT"
    run_step holi_postprocess_aabb "$HOLI_PYTHON" postprocess_3d_bbox_aabb.py \
      --input_dir output_scannetppv2_new \
      --output_dir output_scannetppv2_new_aabb \
      --floor_label floor \
      --axis_method largest_face \
      --extent_mode keep
    run_step holi_generate_qa "$HOLI_PYTHON" qa_generation/generate_two_view_qa.py \
      --scene-id bedroom_4 \
      --data-root scannetppv2/data \
      --wai-root scannetppv2_wai \
      --bbox-json-folder output_scannetppv2_new_aabb \
      --output output_QA_new_lang \
      --num 2 \
      --covis-threshold 0.05 \
      --marker-types language_description
  )
fi

"$HOLI_PYTHON" - <<'PY' "$PROJECT_ROOT" "$HOLI_ROOT" "$SUMMARY" "$DA3_STATUS" "$SOURCE_PROJECT" "$MAX_FRAMES"
import json
import pathlib
import sys

project = pathlib.Path(sys.argv[1])
holi = pathlib.Path(sys.argv[2])
summary_path = pathlib.Path(sys.argv[3])
da3_status = sys.argv[4]
source_project = sys.argv[5]
max_frames = int(sys.argv[6])

def read_json(path):
    return json.loads(path.read_text()) if path.exists() else None

prompts = read_json(project / "masks/object_prompts_groundingdino.json") or {}
tracking = read_json(project / "masks/2d/tracking_manifest.json") or {}
object_masks = read_json(project / "masks/3d/object_masks.json") or {}
gauss_q = read_json(project / "simulator_assets/gaussian_probability_quality_report.json") or {}
instance_q = read_json(project / "simulator_assets/object_instance_quality_report.json") or {}
holi_manifest = read_json(holi / "run_manifest.json") or {}
qa = read_json(holi / "output_QA_new_lang/bedroom_4.json") or []
bbox = read_json(holi / "output_scannetppv2_new_aabb/bedroom_4.json") or []

tracking_objects = tracking.get("objects", {}) if isinstance(tracking, dict) else {}
summary = {
    "schema_version": 1,
    "status": "completed",
    "source_project": source_project,
    "project_root": str(project),
    "holi_root": str(holi),
    "max_frames": max_frames,
    "stage_status": {
        "DA3": da3_status,
        "3DGS": "reused_existing_graphdeco",
        "VLM": "groundingdino_object_discovery",
        "SAM3": "proxy_sam2_due_to_local_hardware",
        "2D_to_3D_lifting": "video2mesh_fuse_masks_probability",
        "bbox_postprocess": "holi_spatial_postprocess_3d_bbox_aabb",
        "QA": "holi_spatial_generate_two_view_qa",
    },
    "counts": {
        "groundingdino_objects": prompts.get("object_count", len(prompts.get("objects", []))) if isinstance(prompts, dict) else 0,
        "groundingdino_candidates": prompts.get("candidate_count", 0) if isinstance(prompts, dict) else 0,
        "sam2_objects": len(tracking_objects),
        "sam2_masks": sum(int(v.get("frames_written", 0)) for v in tracking_objects.values() if isinstance(v, dict)),
        "fused_objects": len(object_masks.get("objects", {})) if isinstance(object_masks, dict) else 0,
        "fused_points": object_masks.get("num_points") if isinstance(object_masks, dict) else None,
        "holi_bbox_instances": len(bbox) if isinstance(bbox, list) else 0,
        "holi_qa_records": len(qa) if isinstance(qa, list) else 0,
        "mask_index_items": holi_manifest.get("counts", {}).get("mask_index_items") if isinstance(holi_manifest, dict) else None,
    },
    "quality_reports": {
        "gaussian_probability_status": gauss_q.get("status") or gauss_q.get("ok"),
        "object_instance_status": instance_q.get("status") or instance_q.get("ok"),
    },
    "outputs": {
        "groundingdino_prompts": str(project / "masks/object_prompts_groundingdino.json"),
        "sam2_masks": str(project / "masks/2d"),
        "object_masks_3d": str(project / "masks/3d/object_masks.json"),
        "semantic_splats": str(project / "simulator_assets/semantic_splats.ply"),
        "gaussian_probabilities": str(project / "simulator_assets/semantic_gaussian_probabilities.ply"),
        "holi_bbox_aabb": str(holi / "output_scannetppv2_new_aabb/bedroom_4.json"),
        "holi_qa": str(holi / "output_QA_new_lang/bedroom_4.json"),
        "holi_manifest": str(holi / "run_manifest.json"),
    },
    "notes": [
        "This is a Video2Mesh/Holi-Spatial adapter run, not a full official Holi-Spatial DA3+PGSR+SAM3 rerun.",
        "SAM2 replaces SAM3 because SAM3 is not locally deployed; 3DGS is reused from the existing bedroom_4 run.",
    ],
}
summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY

echo "[Holi adapter] complete"
echo "[Holi adapter] summary: $SUMMARY"
