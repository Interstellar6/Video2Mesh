#!/usr/bin/env bash
# Source this file on the AutoDL/SeetaCloud server before running Video2Mesh tools.

export WORK=/root/autodl-tmp/workspace/Video2Mesh
export TMPDIR=/root/autodl-tmp/tmp
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
export HF_HOME=/root/autodl-tmp/hf
export TORCH_HOME=/root/autodl-tmp/torch
export CONDA_PKGS_DIRS=/root/autodl-tmp/conda/pkgs
export CONDA_ENVS_PATH=/root/autodl-tmp/conda/envs
export PATH=/root/autodl-tmp/.bun/bin:/root/miniconda3/bin:$PATH

# CUDA headers/libraries for PyTorch CUDA extensions such as gsplat.
# torch.utils.cpp_extension detects /root/miniconda3 as CUDA_HOME on this
# image, but cuda_runtime_api.h lives under the CUDA target include dir.
export CUDA_HOME=${CUDA_HOME:-/usr/local/cuda-12.4}
export CPATH=$CUDA_HOME/targets/x86_64-linux/include:${CPATH:-}
export LIBRARY_PATH=$CUDA_HOME/targets/x86_64-linux/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=$CUDA_HOME/targets/x86_64-linux/lib:${LD_LIBRARY_PATH:-}

# SceneVersepp main runtime. It uses Python 3.11 and has CUDA PyTorch,
# Open3D, Transformers, SpatialLM/PQ3D light dependencies installed.
source /root/autodl-tmp/venvs/v2m-svpp/bin/activate

# Optional acceleration for GitHub/HuggingFace downloads only:
# source /etc/network_turbo

echo "Video2Mesh remote environment loaded."
echo "WORK=$WORK"
python - <<'PY'
import torch
print("python ok")
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
PY
