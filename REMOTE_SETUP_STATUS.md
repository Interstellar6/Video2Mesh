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
- GraphDECO 默认 `DENSIFY_UNTIL_ITER=0` / `GRAPHDECO_DENSIFY_UNTIL_ITER=0`，即保留 full cloud 初始化但关闭 densification，避免 16M+ 初始化点在 32GB 显存上 OOM。

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
- 对 `*_first60.mp4` 使用 30 分钟 MASt3R 预算；如果超时，或虽然结束但 readiness 显示单 pose / 空点云，则裁剪更稳定的 10 秒片段到 `dataset/<name>_best10.mp4` 继续。
- 远端没有 `ffmpeg` 时，用 `python tools/crop_best_video_window.py ...`，该脚本基于 OpenCV 写出新 dataset 视频。

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

OpenCV fallback：

```bash
python tools/crop_best_video_window.py dataset/<name>_first60.mp4 \
  --duration 10 \
  --output dataset/<name>_first60_best10.mp4 \
  --force
```

远端恢复下游阶段：

```bash
bash tools/run_video2mesh_downstream_light.sh \
  exports/<run> \
  dataset/<name>_first60_best10.mp4
```

该入口默认使用 SAM2，但限制 prompt/object 数和 tracking 帧数，并跳过最重的 Gaussian semantic backprojection。若只需要补语义 splat，可设置 `SEMANTIC_SPLATS=1`；若机器负载正常再设置 `GAUSSIAN_BACKPROJECT=1`。

注意：该入口不降采样 object mask fusion 使用的 full cloud，但默认限制背景平面 RANSAC/Fit 采样点数，避免背景结构推断在 16M+ 点云上把机器压到无法 SSH。

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

## 9. 2026-06-20 bedroom_100 检查点

输入数据：

```text
dataset/bedroom_100.mp4
```

执行结果：

- 原始 604.5 秒视频运行 MASt3R-SLAM 超过 1.5 小时仍未产出 `camera_info.json` 和有效 `point_cloud.ply`，已按规则中断。
- 已用 OpenCV 裁剪前 60 秒为新数据集：

```text
dataset/bedroom_100_first60.mp4
```

裁剪文件信息：

```text
duration: 59.993s
fps: 29.97
frames: 1798
resolution: 640x360
size: 42 MB
```

first60 GraphDECO quick run：

```text
exports/bedroom_100_first60_quick_first60_graphdeco_20260620_052824
```

状态：

- `tools/run_video2mesh_quick.sh` 已确认使用 `GS_BACKEND=graphdeco`，命令中包含 `3dgs_graphdeco` 和 GraphDECO `train.py --disable_viewer`。
- first60 在 30 分钟阈值内结束 MASt3R，但只导入 `1` 个 pose。
- `scene/reconstruction/point_cloud.ply` 是空 PLY，Open3D 报 `Read PLY failed: number of vertex <= 0`。
- `reconstruction-readiness` 已能提前诊断该状态：`frames=1 poses=1 points=0`，`ok=False colmap=False 3dgs=False mask_fusion=False`。
- pipeline 现在会在 GraphDECO source/point-cloud 准备前写 `simulator_assets/reconstruction_readiness_report.json` 并停止，避免空点云继续进入训练。
- 该 first60 片段未进入 GraphDECO 训练；后续已裁剪更稳定的 10 秒片段继续。

后续执行：

1. 已对 `bedroom_100_first60.mp4` 选择更有视差和稳定运动的 10 秒片段，保存为 `dataset/bedroom_100_first60_best10.mp4`。
2. 该 best10 片段已跑通 MASt3R full cloud，并进入 GraphDECO/SAM2 后半段验证。
3. `video2mesh/cli.py` 在 GraphDECO 训练跑通后做了第一批低风险拆分，把 3DGS path/helper 逻辑移到 `video2mesh/gsplat_utils.py`。
