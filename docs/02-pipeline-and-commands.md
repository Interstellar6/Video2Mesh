---
title: Video2Mesh 流水线与命令
category: Pipeline
summary: 当前端到端运行方式、关键阶段、产物路径、恢复命令和 QA 命令。
tags:
  - Pipeline
  - COLMAP
  - GraphDECO
  - SAM2
---

# Video2Mesh 流水线与命令

## 端到端流程

```text
input video
  -> extract-frames
  -> run-colmap
  -> train/import GraphDECO 3DGS
  -> auto prompts
  -> SAM2 mask tracking
  -> fuse-masks
  -> export semantic splats
  -> select object frames
  -> prepare object images
  -> reconstruct or import object meshes
  -> export simulator assets
  -> QA / readiness / showcase reports
```

## 远端快速运行

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

常用高质量覆盖：

```bash
MAX_FRAMES=200 \
EXTRACT_EVERY=1 \
GRAPHDECO_ITERATIONS=30000 \
GRAPHDECO_SAVE_ITERATIONS="7000 30000" \
GRAPHDECO_TEST_ITERATIONS="7000 30000" \
GRAPHDECO_RESOLUTION=1 \
bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

指定真实视频时间窗：

```bash
START_SEC=47 \
END_SEC=56 \
MAX_FRAMES=200 \
EXTRACT_EVERY=1 \
bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

帧规则：只使用真实 decoded frames。如果候选帧数超过 `MAX_FRAMES`，就在真实帧中均匀采样，不插值。

## COLMAP 与点云

默认入口：

```bash
python -m video2mesh.cli run-colmap \
  --project-root exports/<run> \
  --frames-dir exports/<run>/scene/frames
```

关键产物：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

`point_cloud.ply` 是默认全量点云，供 3DGS、mask fusion、semantic transfer、object mask cloud 使用。`point_cloud_10k.ply` 或其他轻量版本只用于预览和 debug。

如果 COLMAP readiness 失败，通常应换真实时间窗重跑，而不是补插值帧。

## GraphDECO 3DGS

远端 GraphDECO 默认路径：

```text
/root/autodl-tmp/workspace/gaussian-splatting
```

对已有 run 单独补跑：

```bash
ITERATIONS=30000 \
SAVE_ITERATIONS="7000 30000" \
TEST_ITERATIONS="7000 30000" \
RESOLUTION=1 \
bash tools/run_graphdeco_3dgs.sh exports/<run>
```

默认生产设置：

```text
iterations: 30000
save/test: 7000, 30000
SH degree: 3
densify from: 500
densify until: 15000
opacity reset: 3000
```

低显存处理顺序：

1. 保持 full `point_cloud.ply`。
2. 降低 `GRAPHDECO_RESOLUTION`。
3. 降低 `GRAPHDECO_ITERATIONS` 做诊断。
4. 只有完全无法训练时才考虑点数限制。

## 语义 mask 与 semantic splats

核心输入：

```text
masks/2d/<object_id>/<frame>.png
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

核心命令：

```bash
python -m video2mesh.cli fuse-masks \
  --project-root exports/<run> \
  --point-cloud exports/<run>/scene/reconstruction/point_cloud.ply \
  --fusion-mode probability \
  --min-votes 1

python -m video2mesh.cli export-splat-masks \
  --project-root exports/<run> \
  --mask-source-ply exports/<run>/scene/reconstruction/point_cloud.ply \
  --transfer-mode nearest

python -m video2mesh.cli backproject-gaussian-probabilities \
  --project-root exports/<run>
```

关键输出：

```text
masks/3d/<object_id>/point_indices.json
masks/3d/<object_id>/point_probabilities.npz
simulator_assets/semantic_splats.ply
simulator_assets/semantic_gaussian_probabilities.ply
simulator_assets/viewer_plys/
```

大点云 run 可以先跳过最重的 Gaussian probability backprojection，等 object masks 和 simulator bundle 已经可用后再补。

## 选帧与物体图像

默认选帧策略来自 SVLGaussian-style protocol 的工程化版本：

```text
best visible anchor
  + frame offset 5
  + frame offset 10
  + random window 30
  + masked crop diversity fallback
```

命令：

```bash
python -m video2mesh.cli select-frames \
  --project-root exports/<run> \
  --selection-method svlgaussian \
  --top-k 4

python -m video2mesh.cli prepare-object-images \
  --project-root exports/<run> \
  --top-k 4 \
  --skip-missing
```

产物：

```text
objects/<object_id>/selected_frames/
objects/<object_id>/object_images/
```

## 物体 mesh

临时 baseline：

```bash
python -m video2mesh.cli reconstruct-object-meshes \
  --project-root exports/<run> \
  --method bbox \
  --skip-failed
```

这个 baseline 只用于尺度、位置和导出接口检查。它会有碎片、破洞、悬浮面片和非 watertight 问题，不作为最终物体模型。

生产路线：

```text
trained 3DGS + object masks + registered cameras
  -> render object-centric RGB/depth/normal/mask
  -> masked TSDF fusion
  -> marching cubes / Poisson
  -> optional NeuS-style SDF refinement
  -> texture baking + simplification + collider generation
```

入口：

```bash
python -m video2mesh.cli export-3dgs-mesh-observations \
  --project-root exports/<run> \
  --max-frames-per-object 6 \
  --device cuda

python -m video2mesh.cli reconstruct-3dgs-object-meshes \
  --project-root exports/<run> \
  --method auto \
  --format obj \
  --skip-failed

python -m video2mesh.cli prepare-neus-surface-jobs \
  --project-root exports/<run> \
  --provider external_neus_sdf
```

外部补全/生成 mesh 入口：

```bash
python -m video2mesh.cli export-image-blaster \
  --project-root exports/<run> \
  --provider hunyuan

python -m video2mesh.cli mesh-commands \
  --project-root exports/<run> \
  --provider hunyuan

python -m video2mesh.cli import-object-meshes \
  --project-root exports/<run> \
  --provider external_mesh
```

如果生成的 object-local mesh 尺度不可信，导出 simulator assets 时用 bbox 对齐。

## Simulator assets

```bash
python -m video2mesh.cli export-simulator-assets \
  --project-root exports/<run> \
  --simulator-format mujoco unity \
  --collision-proxy bbox \
  --use-collision-proxy \
  --collider box \
  --body-type dynamic
```

关键输出：

```text
simulator_assets/simulator_asset_bundle.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/review/index.html
```

## QA

推荐每个 run 结束后执行：

```bash
python -m video2mesh.cli evaluate \
  --project-root exports/<run> \
  --json \
  --output exports/<run>/simulator_assets/evaluation_report.json

python -m video2mesh.cli validate \
  --project-root exports/<run>

python -m video2mesh.cli production-readiness \
  --project-root exports/<run> \
  --no-require-scale-calibration

python -m video2mesh.cli qa-simulator-assets \
  --project-root exports/<run> \
  --require-physics

python -m video2mesh.cli simulator-physics-quality-report \
  --project-root exports/<run>
```

展示包检查：

```bash
bash tools/audit_showcase_artifacts.sh exports/<run>
```

## 恢复下游阶段

如果 COLMAP/GraphDECO 已经完成，只恢复 mask、mesh、simulator 资产：

```bash
bash tools/run_video2mesh_downstream_light.sh \
  exports/<run> \
  dataset/<video>.mp4
```

默认会跳过最重的 Gaussian probability backprojection，并限制背景 RANSAC/Fit 采样，但 object mask fusion 仍使用 full scene point cloud。
