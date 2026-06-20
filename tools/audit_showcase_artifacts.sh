#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage:
  bash tools/audit_showcase_artifacts.sh /path/to/project_root

Refresh and list the artifacts that matter for an advisor/demo review:
evaluation, production readiness, target capability matrix, advisor summary,
showcase verification, review HTML, viewer PLYs, semantic/object previews,
object meshes, and simulator adapters.

Optional environment overrides:
  VIDEO2MESH_ROOT=/root/autodl-tmp/workspace/Video2Mesh
  V2M_PYTHON=/root/autodl-tmp/venvs/v2m-svpp/bin/python
  REQUIRE_SEMANTIC_PROBABILITY=0|1
  REQUIRE_REVIEW_TAR=0|1
  FAIL_ON_ISSUES=0|1
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -ne 1 ]]; then
  usage
  exit $([[ $# -eq 1 ]] && [[ "${1:-}" =~ ^(-h|--help)$ ]] && echo 0 || echo 2)
fi

PROJECT_ROOT="$1"
ROOT="${VIDEO2MESH_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [[ ! -d "$PROJECT_ROOT" ]]; then
  echo "[Video2Mesh showcase audit] Project root not found: $PROJECT_ROOT" >&2
  exit 2
fi
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

V2M_PYTHON="${V2M_PYTHON:-/root/autodl-tmp/venvs/v2m-svpp/bin/python}"
if [[ ! -x "$V2M_PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    V2M_PYTHON="$(command -v python)"
  else
    echo "[Video2Mesh showcase audit] No Python interpreter found; set V2M_PYTHON." >&2
    exit 2
  fi
fi

REQUIRE_SEMANTIC_PROBABILITY="${REQUIRE_SEMANTIC_PROBABILITY:-0}"
REQUIRE_REVIEW_TAR="${REQUIRE_REVIEW_TAR:-0}"
FAIL_ON_ISSUES="${FAIL_ON_ISSUES:-0}"

cd "$ROOT"
mkdir -p "$PROJECT_ROOT/logs"
LOG="${PROJECT_ROOT}/logs/showcase_audit_$(date +%Y%m%d_%H%M%S).log"

run_optional() {
  local label="$1"
  shift
  echo "== $label ==" | tee -a "$LOG"
  "$@" 2>&1 | tee -a "$LOG" || true
}

show_file() {
  local label="$1"
  local path="$2"
  if [[ -e "$path" ]]; then
    printf 'OK   %-34s %10s %s\n' "$label" "$(du -h "$path" | awk '{print $1}')" "$path"
  else
    printf 'MISS %-34s %10s %s\n' "$label" "-" "$path"
  fi
}

show_glob() {
  local label="$1"
  local pattern="$2"
  local count=0
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    show_file "$label" "$path"
    count=$((count + 1))
  done < <(find "$PROJECT_ROOT" -path "$pattern" -type f 2>/dev/null | sort | head -20)
  if [[ "$count" -eq 0 ]]; then
    printf 'MISS %-34s %10s %s\n' "$label" "-" "$pattern"
  fi
}

verify_args=(--project-root "$PROJECT_ROOT" --no-scan-common-remote-roots)
if [[ "$REQUIRE_SEMANTIC_PROBABILITY" == "1" || "$REQUIRE_SEMANTIC_PROBABILITY" == "true" ]]; then
  verify_args+=(--require-semantic-probability)
fi
if [[ "$REQUIRE_REVIEW_TAR" != "1" && "$REQUIRE_REVIEW_TAR" != "true" ]]; then
  verify_args+=(--no-require-review-tar)
fi
if [[ "$FAIL_ON_ISSUES" == "1" || "$FAIL_ON_ISSUES" == "true" ]]; then
  verify_args+=(--fail-on-issues)
fi

echo "[Video2Mesh showcase audit] project: $PROJECT_ROOT" | tee "$LOG"
run_optional evaluate "$V2M_PYTHON" -B -m video2mesh.cli evaluate --project-root "$PROJECT_ROOT"
run_optional production-readiness "$V2M_PYTHON" -B -m video2mesh.cli production-readiness --project-root "$PROJECT_ROOT" --no-require-scale-calibration
run_optional target-capability-matrix "$V2M_PYTHON" -B -m video2mesh.cli target-capability-matrix --project-root "$PROJECT_ROOT"
run_optional export-advisor-demo-summary "$V2M_PYTHON" -B -m video2mesh.cli export-advisor-demo-summary --project-root "$PROJECT_ROOT"
run_optional verify-showcase-pack "$V2M_PYTHON" -B -m video2mesh.cli verify-showcase-pack "${verify_args[@]}"

echo
echo "Showcase artifact checklist:"
show_file "review_html" "$PROJECT_ROOT/simulator_assets/review/index.html"
show_file "advisor_summary_md" "$PROJECT_ROOT/simulator_assets/advisor_demo_summary.md"
show_file "showcase_verification" "$PROJECT_ROOT/simulator_assets/showcase_pack_verification.json"
show_file "production_readiness" "$PROJECT_ROOT/simulator_assets/production_readiness_report.json"
show_file "target_capability_matrix" "$PROJECT_ROOT/simulator_assets/target_capability_matrix.json"
show_file "evaluation_report" "$PROJECT_ROOT/simulator_assets/evaluation_report.json"
show_file "simulator_bundle" "$PROJECT_ROOT/simulator_assets/simulator_asset_bundle.json"
show_file "unity_adapter" "$PROJECT_ROOT/simulator_assets/adapters/unity/unity_adapter.json"
show_file "mujoco_adapter" "$PROJECT_ROOT/simulator_assets/adapters/mujoco/mujoco_adapter.xml"
show_file "viewer_scene_point_cloud" "$PROJECT_ROOT/simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply"
show_file "viewer_scene_supersplat" "$PROJECT_ROOT/simulator_assets/viewer_plys/scene_3dgs_supersplat.ply"
show_file "semantic_supersplat" "$PROJECT_ROOT/simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply"
show_glob "reconstruction_preview" "$PROJECT_ROOT/simulator_assets/reconstruction_preview/*"
show_glob "semantic_preview" "$PROJECT_ROOT/simulator_assets/semantic_preview/*"
show_glob "object_mesh" "$PROJECT_ROOT/simulator_assets/objects/*/mesh.*"
show_glob "object_crop" "$PROJECT_ROOT/simulator_assets/object_images/*"

echo
echo "Log: $LOG"
