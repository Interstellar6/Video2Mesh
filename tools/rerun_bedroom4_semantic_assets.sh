#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/rerun_bedroom4_semantic_assets.sh /path/to/project_root /path/to/anysplat_run

Regenerate the GraphDECO and AnySplat semantic assets from real 2D masks.
The GraphDECO route registers the primary pipeline artifacts. The AnySplat
route is isolated and must not replace the primary manifest entries.

Optional environment overrides:
  V2M_PYTHON=/path/to/python
  GRAPHDECO_PLY=/path/to/visual_scene_3dgs.ply (normally leave unset)
  SCENE_MESH=/path/to/scene_mesh.ply
  ANYSPLAT_MESH=/path/to/anysplat_poisson_mesh.ply
  ANYSPLAT_IMAGE_SIZE=448
  SEMANTIC_ASSET_VERSION=v5
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 2 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

PROJECT_ROOT="$(cd "$1" && pwd)"
ANYSPLAT_RUN="$(cd "$2" && pwd)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
V2M_PYTHON="${V2M_PYTHON:-$(command -v python3)}"

GRAPHDECO_PLY="${GRAPHDECO_PLY:-}"
SCENE_MESH="${SCENE_MESH:-$PROJECT_ROOT/simulator_assets/scene_meshes/colmap_delaunay_dense/mesh.ply}"
ANYSPLAT_MESH="${ANYSPLAT_MESH:-$ANYSPLAT_RUN/mesh_poisson_from_gaussian_centers/anysplat_poisson_voxel01_depth8_mesh.ply}"
ANYSPLAT_IMAGE_SIZE="${ANYSPLAT_IMAGE_SIZE:-448}"
SEMANTIC_ASSET_VERSION="${SEMANTIC_ASSET_VERSION:-v5}"

for required in "$SCENE_MESH" "$ANYSPLAT_RUN/gaussians.ply" "$ANYSPLAT_MESH"; do
  if [[ ! -s "$required" ]]; then
    echo "Missing required input: $required" >&2
    exit 2
  fi
done
if [[ -n "$GRAPHDECO_PLY" && ! -s "$GRAPHDECO_PLY" ]]; then
  echo "Missing GRAPHDECO_PLY override: $GRAPHDECO_PLY" >&2
  exit 2
fi

GRAPHDECO_SOURCE_ARGS=()
if [[ -n "$GRAPHDECO_PLY" ]]; then
  GRAPHDECO_SOURCE_ARGS=(--splat-ply "$GRAPHDECO_PLY")
fi

cd "$ROOT"

# GraphDECO is the primary visual layer. The semantic core must preserve this
# exact cleaned Gaussian geometry, while the generated SuperSplat viewer asset
# is only a bounded overlay.
"$V2M_PYTHON" -B -m video2mesh.cli backproject-gaussian-probabilities \
  --project-root "$PROJECT_ROOT" \
  "${GRAPHDECO_SOURCE_ARGS[@]}" \
  --include-background-structures \
  --no-merge-background-structure-masks \
  --require-active-scene-geometry \
  --occlusion-filter \
  --pixel-stride 4 \
  --max-pixels-per-mask 3000 \
  --max-gaussians-per-frame 250000 \
  --output "$PROJECT_ROOT/simulator_assets/semantic_splats.ply" \
  --output-dir "$PROJECT_ROOT/simulator_assets/gaussian_probabilities_${SEMANTIC_ASSET_VERSION}" \
  --manifest-output "$PROJECT_ROOT/simulator_assets/semantic_splats_manifest.json" \
  --viewer-output-dir "$PROJECT_ROOT/simulator_assets/viewer_plys_${SEMANTIC_ASSET_VERSION}" \
  --viewer-prefix "graphdeco_semantic_${SEMANTIC_ASSET_VERSION}"

"$V2M_PYTHON" -B -m video2mesh.cli render-semantic-preview \
  --project-root "$PROJECT_ROOT" \
  --semantic-splats-ply "$PROJECT_ROOT/simulator_assets/semantic_splats.ply" \
  --semantic-manifest "$PROJECT_ROOT/simulator_assets/semantic_splats_manifest.json" \
  --output-dir "$PROJECT_ROOT/simulator_assets/semantic_preview_${SEMANTIC_ASSET_VERSION}" \
  --max-frames 6 \
  --max-points-per-frame 30000 \
  --occlusion-filter \
  --no-write-colored-ply

"$V2M_PYTHON" -B -m video2mesh.cli transfer-mesh-semantics-local \
  --project-root "$PROJECT_ROOT" \
  --mesh "$SCENE_MESH" \
  --semantic-splats-ply "$PROJECT_ROOT/simulator_assets/semantic_splats.ply" \
  --semantic-manifest "$PROJECT_ROOT/simulator_assets/semantic_splats_manifest.json" \
  --output-dir "$PROJECT_ROOT/simulator_assets/mesh_semantics_local_2d_probability_${SEMANTIC_ASSET_VERSION}"

"$V2M_PYTHON" -B -m video2mesh.cli export-double-sided-mesh-preview \
  --mesh "$SCENE_MESH" \
  --output "${SCENE_MESH%.ply}_double_sided.ply"

# AnySplat owns a separate Gaussian/camera coordinate system. Its helper maps
# the 19 AnySplat inputs to matching Video2Mesh masks and converts predicted
# camera-to-world poses before the probability backprojection.
"$V2M_PYTHON" -B tools/prepare_anysplat_semantic_projection.py \
  --project-root "$PROJECT_ROOT" \
  --anysplat-run "$ANYSPLAT_RUN" \
  --image-size "$ANYSPLAT_IMAGE_SIZE" \
  --output-dir "$ANYSPLAT_RUN/semantic_projection_inputs_${SEMANTIC_ASSET_VERSION}"

"$V2M_PYTHON" -B -m video2mesh.cli backproject-gaussian-probabilities \
  --project-root "$PROJECT_ROOT" \
  --splat-ply "$ANYSPLAT_RUN/gaussians.ply" \
  --camera-info "$ANYSPLAT_RUN/semantic_projection_inputs_${SEMANTIC_ASSET_VERSION}/camera_info_anysplat.json" \
  --mask-root "$ANYSPLAT_RUN/semantic_projection_inputs_${SEMANTIC_ASSET_VERSION}/masks_2d" \
  --include-background-structures \
  --no-merge-background-structure-masks \
  --occlusion-filter \
  --pixel-stride 4 \
  --max-pixels-per-mask 3000 \
  --max-gaussians-per-frame 250000 \
  --output "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}.ply" \
  --output-dir "$ANYSPLAT_RUN/gaussian_probabilities_${SEMANTIC_ASSET_VERSION}" \
  --manifest-output "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}_manifest.json" \
  --viewer-output-dir "$ANYSPLAT_RUN/viewer_plys_${SEMANTIC_ASSET_VERSION}" \
  --viewer-prefix "anysplat_semantic_${SEMANTIC_ASSET_VERSION}" \
  --no-register-artifacts

"$V2M_PYTHON" -B -m video2mesh.cli render-semantic-preview \
  --project-root "$PROJECT_ROOT" \
  --semantic-splats-ply "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}.ply" \
  --semantic-manifest "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}_manifest.json" \
  --frames-dir "$ANYSPLAT_RUN/images" \
  --camera-info "$ANYSPLAT_RUN/semantic_projection_inputs_${SEMANTIC_ASSET_VERSION}/camera_info_anysplat.json" \
  --output-dir "$ANYSPLAT_RUN/semantic_preview_${SEMANTIC_ASSET_VERSION}" \
  --max-frames 6 \
  --max-points-per-frame 30000 \
  --occlusion-filter \
  --no-write-colored-ply \
  --no-register-artifacts

"$V2M_PYTHON" -B -m video2mesh.cli transfer-mesh-semantics-local \
  --project-root "$PROJECT_ROOT" \
  --mesh "$ANYSPLAT_MESH" \
  --semantic-splats-ply "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}.ply" \
  --semantic-manifest "$ANYSPLAT_RUN/semantic_anysplat_gaussians_2d_probability_${SEMANTIC_ASSET_VERSION}_manifest.json" \
  --output-dir "$ANYSPLAT_RUN/mesh_semantics_local_2d_probability_${SEMANTIC_ASSET_VERSION}" \
  --no-register-artifacts

"$V2M_PYTHON" -B -m video2mesh.cli export-double-sided-mesh-preview \
  --mesh "$ANYSPLAT_MESH" \
  --output "${ANYSPLAT_MESH%.ply}_double_sided.ply"

echo "Semantic asset rerun complete."
