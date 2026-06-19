#!/usr/bin/env bash
set -euo pipefail

ROOT="${VIDEO2MESH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [[ -z "${PYTHON:-}" ]]; then
  if [[ -x /root/autodl-tmp/venvs/v2m-svpp/bin/python ]]; then
    PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  else
    PYTHON=python3
  fi
fi
SOURCE_DIR="${SOURCE_DIR:-${ROOT}/dataset/sceneversepp_sample/bedroom_100_3o5KSzfdOSE}"
PROJECT="${PROJECT:-${ROOT}/exports/sceneversepp_official_bedroom_sample}"
SCENE_ID="${SCENE_ID:-sceneversepp_official_bedroom_sample}"

cd "$ROOT"

"$PYTHON" -m video2mesh.cli import-svpp-scene \
  --project-root "$PROJECT" \
  --source-dir "$SOURCE_DIR" \
  --scene-id "$SCENE_ID" \
  --mode symlink \
  --replace \
  --min-points 100

"$PYTHON" -m video2mesh.cli extract-svpp-object-meshes \
  --project-root "$PROJECT" \
  --roles foreground \
  --face-mode all \
  --fallback-any \
  --skip-failed

"$PYTHON" -m video2mesh.cli export-object-mask-clouds \
  --project-root "$PROJECT" \
  --skip-missing

"$PYTHON" -m video2mesh.cli export-splat-masks \
  --project-root "$PROJECT" \
  --splat-ply "$PROJECT/scene/reconstruction/point_cloud.ply" \
  --mask-source-ply "$PROJECT/scene/reconstruction/point_cloud.ply" \
  --transfer-mode index

"$PYTHON" -m video2mesh.cli export-viewer-plys \
  --project-root "$PROJECT" \
  --kind semantic

"$PYTHON" -m video2mesh.cli export-viewer-plys \
  --project-root "$PROJECT" \
  --splat-ply "$PROJECT/scene/reconstruction/point_cloud.ply" \
  --prefix sceneversepp_source_scene

"$PYTHON" -m video2mesh.cli export-svpp-metadata \
  --project-root "$PROJECT" \
  --scene-id "$SCENE_ID" \
  --mode symlink \
  --skip-missing \
  --skip-small \
  --min-points 100 \
  --default-category chair

"$PYTHON" -m video2mesh.cli background-structure-quality-report \
  --project-root "$PROJECT" \
  --expected-categories floor wall ceiling window cabinet \
  --production-expected-categories floor wall ceiling door window cabinet

"$PYTHON" -m video2mesh.cli export-simulator-assets \
  --project-root "$PROJECT" \
  --collision-proxy bbox \
  --use-collision-proxy \
  --collider box \
  --body-type dynamic

"$PYTHON" -m video2mesh.cli calibrate-simulator-assets \
  --project-root "$PROJECT" \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --estimate-physics \
  --overwrite-physics \
  --collider box

"$PYTHON" -m video2mesh.cli export-simulator-adapter \
  --project-root "$PROJECT" \
  --format mujoco unity

"$PYTHON" -m video2mesh.cli qa-simulator-assets \
  --project-root "$PROJECT"

"$PYTHON" -m video2mesh.cli mesh-quality-report \
  --project-root "$PROJECT"

"$PYTHON" -m video2mesh.cli simulator-physics-quality-report \
  --project-root "$PROJECT"

"$PYTHON" -m video2mesh.cli evaluate \
  --project-root "$PROJECT" || true

"$PYTHON" -m video2mesh.cli validate \
  --project-root "$PROJECT" \
  --output "$PROJECT/simulator_assets/validation_report.json" || true

"$PYTHON" -m video2mesh.cli production-readiness \
  --project-root "$PROJECT" \
  --no-require-scale-calibration

"$PYTHON" -m video2mesh.cli target-capability-matrix \
  --project-root "$PROJECT"

"$PYTHON" -m video2mesh.cli export-advisor-demo-summary \
  --project-root "$PROJECT"

"$PYTHON" -m video2mesh.cli verify-svpp-import-pack \
  --project-root "$PROJECT" \
  --min-instances 37 \
  --min-foreground-objects 25 \
  --min-background-structures 12 \
  --min-object-meshes 25 \
  --fail-on-issues

echo "SceneVerse++ official sample pack ready: $PROJECT"
