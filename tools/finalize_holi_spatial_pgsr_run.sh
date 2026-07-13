#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT="${RUN_ROOT:?Set RUN_ROOT to the completed Holi-Spatial run directory}"
GPU="${GPU:-5}"
PGSR_ITERATION="${PGSR_ITERATION:-30000}"
MAX_DEPTH="${MAX_DEPTH:-35.0}"
VOXEL_SIZE="${VOXEL_SIZE:-0.05}"

HOLI_ROOT="${HOLI_ROOT:-/data/zyx/workspace/third_party/holi-spatial}"
PGSR_PYTHON="${PGSR_PYTHON:-/data/zyx/workspace/pgsr_env/bin/python}"
PGSR_SHIMS="${PGSR_SHIMS:-/data/zyx/workspace/pgsr_runs/python_shims}"
PROJECT="$RUN_ROOT/video2mesh"
MODEL="$RUN_ROOT/pgsr_scannetppv2_all/bedroom_4"
PGSR_PLY="$MODEL/point_cloud/iteration_${PGSR_ITERATION}/point_cloud.ply"
DA3_PLY="$RUN_ROOT/scannetppv2/data/bedroom_4/pointcloud_da3.ply"
SNAPSHOT="$RUN_ROOT/code_snapshot"
RENDER_WORKDIR="$RUN_ROOT/pgsr_render_workdir"

if [[ ! -s "$PGSR_PLY" ]]; then
  echo "Missing completed PGSR PLY: $PGSR_PLY" >&2
  exit 2
fi
if [[ ! -s "$MODEL/input.ply" ]]; then
  echo "Missing PGSR initialization copy: $MODEL/input.ply" >&2
  exit 2
fi
if [[ ! -s "$DA3_PLY" ]]; then
  echo "Missing DA3 point cloud: $DA3_PLY" >&2
  exit 2
fi

mkdir -p "$RUN_ROOT/logs"
mkdir -p "$RENDER_WORKDIR/output_scannet/scannetppv2/0b031f3119"
ln -sfn "$MODEL/input.ply" "$RENDER_WORKDIR/output_scannet/scannetppv2/0b031f3119/input.ply"

(
  cd "$RENDER_WORKDIR"
  env \
    CUDA_VISIBLE_DEVICES="$GPU" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="$PGSR_SHIMS:$HOLI_ROOT/PGSR" \
    "$PGSR_PYTHON" "$HOLI_ROOT/PGSR/render.py" \
      -s "$RUN_ROOT/scannetppv2/data/bedroom_4/dslr/nerfstudio" \
      -i "$RUN_ROOT/scannetppv2/data/bedroom_4/dslr/resized_undistorted_images" \
      -m "$MODEL" \
      --iteration "$PGSR_ITERATION" \
      --skip_test \
      --max_depth "$MAX_DEPTH" \
      --voxel_size "$VOXEL_SIZE" \
      --num_cluster 1
) 2>&1 | tee "$RUN_ROOT/logs/pgsr_render_mesh_30k.log"

cp "$PROJECT/simulator_assets/semantic_splats_manifest.json" \
  "$PROJECT/simulator_assets/semantic_da3_points_manifest.json"

env PYTHONUNBUFFERED=1 PYTHONPATH="$SNAPSHOT" \
  "$PGSR_PYTHON" -B -m video2mesh.cli export-semantic-palette-ply \
    --project-root "$PROJECT" \
    --semantic-ply "$PROJECT/simulator_assets/semantic_da3_points.ply" \
    --semantic-manifest "$PROJECT/simulator_assets/semantic_da3_points_manifest.json" \
    --output "$PROJECT/simulator_assets/semantic_da3_points_palette.ply" \
    --output-manifest "$PROJECT/simulator_assets/semantic_da3_points_palette_manifest.json" \
  2>&1 | tee "$RUN_ROOT/logs/semantic_da3_palette_export.log"

env PYTHONUNBUFFERED=1 PYTHONPATH="$SNAPSHOT" \
  "$PGSR_PYTHON" -B -m video2mesh.cli export-splat-masks \
    --project-root "$PROJECT" \
    --splat-ply "$PGSR_PLY" \
    --mask-source-ply "$DA3_PLY" \
    --transfer-mode nearest \
    --include-probabilities \
    --no-export-viewer-plys \
    --output "$PROJECT/simulator_assets/semantic_pgsr_30k.ply" \
    --manifest-output "$PROJECT/simulator_assets/semantic_pgsr_30k_manifest.json" \
  2>&1 | tee "$RUN_ROOT/logs/semantic_transfer_pgsr_30k.log"

env PYTHONUNBUFFERED=1 PYTHONPATH="$SNAPSHOT" \
  "$PGSR_PYTHON" -B -m video2mesh.cli render-semantic-preview \
    --project-root "$PROJECT" \
    --semantic-splats-ply "$PROJECT/simulator_assets/semantic_pgsr_30k.ply" \
    --semantic-manifest "$PROJECT/simulator_assets/semantic_pgsr_30k_manifest.json" \
    --output-dir "$PROJECT/simulator_assets/semantic_pgsr_preview" \
    --max-frames 10 \
    --max-points-per-frame 30000 \
    --occlusion-filter \
    --depth-tolerance 0.05 \
    --relative-depth-tolerance 0.03 \
    --no-write-colored-ply \
  2>&1 | tee "$RUN_ROOT/logs/semantic_pgsr_preview.log"

"$PGSR_PYTHON" "$SNAPSHOT/tools/summarize_holi_spatial_full_run.py" --run-root "$RUN_ROOT"

echo "PGSR finalization complete"
echo "PGSR PLY: $PGSR_PLY"
echo "PGSR mesh: $MODEL/mesh/tsdf_fusion_post.ply"
echo "Semantic PGSR: $PROJECT/simulator_assets/semantic_pgsr_30k.ply"
