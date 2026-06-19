# Video2Mesh 远端环境状态

更新时间：2026-06-20

## 1. 路径

```text
远端项目：/root/autodl-tmp/workspace/Video2Mesh
远端数据：/root/autodl-tmp/workspace/Video2Mesh/dataset
远端输出：/root/autodl-tmp/workspace/Video2Mesh/exports
MASt3R-SLAM：/root/autodl-tmp/workspace/MASt3R-SLAM
GraphDECO：/root/autodl-tmp/workspace/gaussian-splatting
SAM2：/root/autodl-tmp/workspace/sam2
主 venv：/root/autodl-tmp/venvs/v2m-svpp
SAM2 venv：/root/autodl-tmp/workspace/venvs/v2m-sam2-clean
```

## 2. GPU 和 Python

GPU：

```text
NVIDIA GeForce RTX 4080 SUPER
CUDA runtime: torch 2.5.1+cu124
```

主 Python：

```bash
/root/autodl-tmp/venvs/v2m-svpp/bin/python
```

已验证包：

- PyTorch CUDA 可用。
- OpenCV drawing 可用。
- Open3D / NumPy / SciPy / scikit-learn 可用于当前 CLI。
- `video2mesh.cli` 可编译。

不推荐默认使用 conda base 跑完整流程；base 里曾出现 OpenCV/NumPy/Scipy 组合问题。

## 3. 权重

远端权重：

```text
/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth
/root/autodl-tmp/workspace/sam2/checkpoints/sam2.1_hiera_tiny.pt
/root/autodl-tmp/workspace/MASt3R-SLAM/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
```

本地同步目标：

```text
/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/checkpoints/sam/sam_vit_b_01ec64.pth
/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/checkpoints/sam2/sam2.1_hiera_tiny.pt
/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/checkpoints/mast3r/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
```

这些文件不进 Git，已由 `.gitignore` 排除。

## 4. GraphDECO 状态

GraphDECO repo：

```text
/root/autodl-tmp/workspace/gaussian-splatting
```

已处理：

- 主 repo 已同步到远端。
- `submodules/simple-knn` 已安装并可导入。
- `submodules/diff-gaussian-rasterization` 已安装并可导入。
- `diff-gaussian-rasterization/third_party/glm` 已补齐。
- `fused-ssim` 是可选项；当前可不装，GraphDECO 会使用 fallback SSIM。
- `train.py --help` 已通过。

运行 GraphDECO 时需要把 torch shared library 加入 `LD_LIBRARY_PATH`。`tools/run_video2mesh_quick.sh` 和 `tools/run_graphdeco_3dgs.sh` 已自动处理。

## 5. 快速入口

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

脚本默认：

- `GS_BACKEND=graphdeco`
- `MASK_BACKEND=sam2`
- `GRAPHDECO_ITERATIONS=7000`
- `GRAPHDECO_RESOLUTION=1`
- 不降采样 MASt3R full cloud

单独补跑 GraphDECO：

```bash
ITERATIONS=7000 RESOLUTION=1 \
bash tools/run_graphdeco_3dgs.sh exports/<run>
```

## 6. MASt3R 超时策略

长视频规则：

- MASt3R-SLAM 运行小于 1.5 小时时，只要 GPU/CPU 有持续负载就不杀。
- 超过 1.5 小时仍未产出 `camera_info.json` 和 `point_cloud.ply`，中断当前 run。
- 裁剪前 60 秒到 `dataset/<name>_first60.mp4`。
- 对裁剪视频重新跑 quick script。

裁剪命令：

```bash
ffmpeg -y -i dataset/<name>.mp4 -t 60 -c copy dataset/<name>_first60.mp4
```

重编码 fallback：

```bash
ffmpeg -y -i dataset/<name>.mp4 -t 60 \
  -c:v libx264 -crf 18 -preset veryfast \
  -c:a copy dataset/<name>_first60.mp4
```

## 7. 网络和磁盘

GitHub/HuggingFace 下载前：

```bash
source /etc/network_turbo
```

注意事项：

- 大模型、数据集、exports、checkpoints 都放 `/root/autodl-tmp`。
- 清理 pip cache 可释放系统盘：`rm -rf /root/.cache/pip`。
- 不要把 `exports/`、`dataset/`、`checkpoints/` 推到 GitHub。

## 8. 当前风险

- 长视频 MASt3R 可能耗时超过 1.5 小时，需要裁剪策略。
- GraphDECO 训练真实质量依赖位姿质量、训练帧和分辨率；OOM 时优先降分辨率，不降 full cloud。
- SAM2 tiny 对复杂家具和植物仍可能过分割。
- 当前 mesh 是 baseline，生产质量需要外部物体重建。
