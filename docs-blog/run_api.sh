#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 docs-blog/api_server.py
