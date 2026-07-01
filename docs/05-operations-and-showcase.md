---
title: 运行、展示与排错
category: Operations
summary: 远端环境、展示产物、历史 run、QA 命令和常见失败处理。
tags:
  - Runbook
  - Showcase
  - QA
---

# 运行、展示与排错

## 远端环境

常用路径：

```text
Video2Mesh: /root/autodl-tmp/workspace/Video2Mesh
dataset: /root/autodl-tmp/workspace/Video2Mesh/dataset
exports: /root/autodl-tmp/workspace/Video2Mesh/exports
GraphDECO: /root/autodl-tmp/workspace/gaussian-splatting
SAM2: /root/autodl-tmp/workspace/sam2
main venv: /root/autodl-tmp/venvs/v2m-svpp
SAM2 venv: /root/autodl-tmp/workspace/venvs/v2m-sam2-clean
```

登录后：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true
```

不推荐默认用 conda base 跑完整流程；历史上 base 的 OpenCV/NumPy/SciPy 组合出现过问题。

## 权重和依赖

常用权重：

```text
/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth
/root/autodl-tmp/workspace/sam2/checkpoints/sam2.1_hiera_tiny.pt
/root/autodl-tmp/workspace/MASt3R-SLAM/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
```

GraphDECO 运行时需要 torch shared library 在 `LD_LIBRARY_PATH` 中。`tools/run_video2mesh_quick.sh` 和 `tools/run_graphdeco_3dgs.sh` 已处理。

## 监控命令

进程：

```bash
ps -eo pid,ppid,pgid,etime,stat,pcpu,pmem,cmd | \
  grep -E "run_video2mesh_quick|MASt3R-SLAM|mast3r|graphdeco|train.py" | \
  grep -v grep
```

GPU：

```bash
nvidia-smi
```

关键输出：

```bash
find exports/<run>/scene -maxdepth 4 \
  \( -name camera_info.json -o -name point_cloud.ply \) -ls
```

日志：

```bash
tail -80 exports/<run>/logs/mast3r_slam_run.log
tail -80 exports/<run>/logs/graphdeco_train.log
```

## 展示产物

| 展示目标 | 文件 |
|---|---|
| 总览网页 | `simulator_assets/review/index.html` |
| 场景 SuperSplat | `simulator_assets/viewer_plys/scene_3dgs_supersplat.ply` |
| 普通点云 | `simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` |
| 语义 SuperSplat | `simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply` |
| Gaussian probability | `simulator_assets/semantic_gaussian_probability_supersplat.ply` |
| 3D object masks | `simulator_assets/object_masks_3d/*.ply` |
| object selected frames | `objects/<object_id>/selected_frames/` |
| object crops | `objects/<object_id>/object_images/` |
| object meshes | `simulator_assets/reconstructed_meshes/` 或 `simulator_assets/3dgs_object_meshes/` |
| simulator bundle | `simulator_assets/simulator_asset_bundle.json` |
| MuJoCo adapter | `simulator_assets/adapters/mujoco/scene.xml` |
| Unity adapter | `simulator_assets/adapters/unity/unity_adapter.json` |
| evaluation | `simulator_assets/evaluation_report.json` |
| showcase verification | `simulator_assets/showcase_pack_verification.json` |
| production readiness | `simulator_assets/production_readiness_report.json` |

刷新展示检查：

```bash
bash tools/audit_showcase_artifacts.sh exports/<run>
```

推荐展示顺序：

1. 打开 `review/index.html` 讲完整链路。
2. 用 SuperSplat 打开 `scene_3dgs_supersplat.ply`。
3. 展示 semantic splat / probability splat。
4. 展示 3D masks 和 object selected frames。
5. 展示 object mesh 和 simulator bundle。
6. 最后展示 QA，明确 demo-ready 和 production gap。

## 历史 run 定位

`milscene3_full_20260618_124804`：

- 已完成端到端 baseline。
- 证明 `video -> 3DGS -> 3D semantic masks -> object frames -> mesh -> simulator assets` 闭合。
- active 3DGS 是历史 minimal gsplat full-cloud baseline，不是当前 GraphDECO 默认。

`milscene2_hq_20260618_065920`：

- 更早的真实视频 baseline。
- 可展示系统闭环，但不代表当前最高质量。

新实验默认应看 GraphDECO quick pipeline 输出。

## 常见失败

### 重建只有单 pose 或空点云

症状：

```text
frames=1 poses=1 points=0
No points found in point cloud
```

处理：

- 不进入 GraphDECO。
- 换真实时间窗。
- 裁剪更稳定、更有视差的 10 秒片段。
- 不用插值帧填补。

OpenCV 裁剪：

```bash
python tools/crop_best_video_window.py dataset/<video>.mp4 \
  --duration 10 \
  --output dataset/<video>_best10.mp4 \
  --force
```

### MASt3R 或重建耗时过长

规则：

- 长视频小于 1.5 小时且 GPU/CPU 有负载时继续观察。
- 超过 1.5 小时无 `camera_info.json` 和有效 `point_cloud.ply`，中断。
- 先裁剪前 60 秒。
- 若 60 秒仍失败，再裁剪更稳定的 10 秒。

### 物体 mesh 破碎

这是 object mask cloud baseline 的预期问题，不是最终路线。处理：

- 不把 baseline OBJ 当最终展示 mesh。
- 使用 `export-3dgs-mesh-observations` + `reconstruct-3dgs-object-meshes`。
- 遮挡严重时接 external generated mesh，再 fit to bbox。
- collider 走 primitive / convex proxy。

### 物理字段缺失

处理：

```bash
python -m video2mesh.cli prepare-simulator-physics-jobs \
  --project-root exports/<run>

python -m video2mesh.cli import-simulator-physics \
  --project-root exports/<run> \
  --physics exports/<run>/simulator_assets/physics_properties.json

python -m video2mesh.cli simulator-physics-quality-report \
  --project-root exports/<run>
```

MLLM/VLM 可作为物理属性草稿来源，但必须进 QA。

## 展示口径

可以说：

- 系统已经跑通从真实视频到 3DGS、语义 mask、object assets、simulator bundle 的闭环。
- 当前 baseline mesh 用于验证尺度和接口，不是最终 visual mesh。
- 生产 mesh 主线是 3DGS rendered depth/mask + TSDF/Poisson。
- 交互层依赖 collider/proxy/physics sidecar，不依赖原始 3DGS 几何。

不要说：

- 已经能从任意视频稳定生成生产级 mesh。
- 3DGS 本身可以直接碰撞。
- SimAnything 可以替代 mesh/collider。
- generated mesh 可以不经对齐和 QA 直接进仿真。
