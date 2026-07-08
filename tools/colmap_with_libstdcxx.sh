#!/usr/bin/env bash
set -euo pipefail

# Wrapper for servers where the COLMAP binary needs a newer libstdc++ than the
# host default, while system libraries such as glog/ceres should remain in use.
if [[ -n "${COLMAP_LIBSTDCXX_DIR:-}" ]]; then
  export LD_LIBRARY_PATH="${COLMAP_LIBSTDCXX_DIR}:${LD_LIBRARY_PATH:-}"
fi

if [[ -n "${COLMAP_REAL_BINARY:-}" ]]; then
  exec "$COLMAP_REAL_BINARY" "$@"
fi

if [[ -x "/data/zyx/workspace/Video2MeshWorkspace/colmap_cuda/bin/colmap" ]]; then
  exec "/data/zyx/workspace/Video2MeshWorkspace/colmap_cuda/bin/colmap" "$@"
fi

exec colmap "$@"
