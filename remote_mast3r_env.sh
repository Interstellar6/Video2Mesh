#!/usr/bin/env bash
# Source this file on the AutoDL/SeetaCloud server before running MASt3R-SLAM.

export V2M_WORK=/root/autodl-tmp/workspace/Video2Mesh
export MAST3R_SLAM_ROOT=/root/autodl-tmp/workspace/MASt3R-SLAM
export TMPDIR=/root/autodl-tmp/tmp
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
export HF_HOME=/root/autodl-tmp/hf
export TORCH_HOME=/root/autodl-tmp/torch
export PATH=/root/autodl-tmp/.bun/bin:/root/miniconda3/bin:$PATH

source /root/autodl-tmp/venvs/v2m-svpp/bin/activate

# MASt3R-SLAM imports DUSt3R/MASt3R modules from the vendored checkout.
export PYTHONPATH="$MAST3R_SLAM_ROOT:$MAST3R_SLAM_ROOT/thirdparty/mast3r:$MAST3R_SLAM_ROOT/thirdparty/mast3r/dust3r:${PYTHONPATH:-}"

# CUDA extensions such as curope and mast3r_slam_backends need torch shared libs.
TORCH_LIB=$(python - <<'PY'
import pathlib
import torch

print(pathlib.Path(torch.__file__).resolve().parent / "lib")
PY
)
export LD_LIBRARY_PATH="$TORCH_LIB:${LD_LIBRARY_PATH:-}"

echo "MASt3R-SLAM remote environment loaded."
echo "MAST3R_SLAM_ROOT=$MAST3R_SLAM_ROOT"
python - <<'PY'
import torch

print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY
