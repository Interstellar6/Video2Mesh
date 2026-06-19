#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNITY_PROJECT="${ROOT_DIR}/UnityProject"
ADAPTER="${1:-${ROOT_DIR}/exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json}"

UNITY_BIN="${UNITY_BIN:-}"
if [[ -z "${UNITY_BIN}" ]]; then
  if [[ -x "${HOME}/Unity/Hub/Editor/2023.2.20f1/Unity.app/Contents/MacOS/Unity" ]]; then
    UNITY_BIN="${HOME}/Unity/Hub/Editor/2023.2.20f1/Unity.app/Contents/MacOS/Unity"
  elif [[ -x "/Applications/Unity/Hub/Editor/2023.2.20f1/Unity.app/Contents/MacOS/Unity" ]]; then
    UNITY_BIN="/Applications/Unity/Hub/Editor/2023.2.20f1/Unity.app/Contents/MacOS/Unity"
  else
    UNITY_BIN="$(
      {
        find "${HOME}/Unity/Hub/Editor" -path '*/Unity.app/Contents/MacOS/Unity' -type f 2>/dev/null
        find /Applications/Unity/Hub/Editor -path '*/Unity.app/Contents/MacOS/Unity' -type f 2>/dev/null
      } | sort | tail -1 || true
    )"
  fi
fi

if [[ -z "${UNITY_BIN}" || ! -x "${UNITY_BIN}" ]]; then
  echo "Unity editor binary not found. Install Unity Editor first, or set UNITY_BIN=/path/to/Unity." >&2
  exit 1
fi

mkdir -p "${UNITY_PROJECT}/Logs"
LOG_FILE="${UNITY_PROJECT}/Logs/video2mesh-import.log"

if ! "${UNITY_BIN}" \
    -batchmode \
    -quit \
    -projectPath "${UNITY_PROJECT}" \
    -executeMethod Video2MeshUnityImporter.ImportFromCommandLine \
    -adapter "${ADAPTER}" \
    -logFile "${LOG_FILE}"; then
  echo "Unity import failed. Last log lines:" >&2
  tail -80 "${LOG_FILE}" >&2 || true
  exit 1
fi

echo "Imported Video2Mesh adapter into ${UNITY_PROJECT}"
echo "Scene: ${UNITY_PROJECT}/Assets/Scenes/Video2MeshScene.unity"
echo "Log: ${LOG_FILE}"
