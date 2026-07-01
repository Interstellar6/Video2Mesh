---
title: Video2Mesh 项目总览
category: Overview
summary: Video2Mesh 的目标、系统边界、资产分层、参考项目角色和当前工程状态。
tags:
  - Video2Mesh
  - 3DGS
  - Simulator
---

# Video2Mesh 项目总览

## 项目目标

Video2Mesh 的目标是把一段真实空间扫描视频转换成可展示、可拆分、可进入仿真器或游戏引擎的 3D 场景资产。

它不是单图 3D 生成工具，也不是只输出一个好看 mesh 的 photogrammetry pipeline。它的目标产物是一组分层资产：

```text
scene visual representation
object and background semantic masks
object visual meshes
collision and physics proxies
scene graph / semantic sidecars
Unity / MuJoCo / Isaac adapters
review and QA reports
```

## 当前默认链路

```text
scan video
  -> real-frame extraction
  -> COLMAP poses and full point cloud
  -> GraphDECO 3D Gaussian Splatting
  -> SAM prompt discovery + SAM2 tracking
  -> 2D mask to 3D mask fusion
  -> semantic / probability Gaussian export
  -> object frame selection
  -> object mesh and completion jobs
  -> simulator asset bundle
  -> adapters and QA
```

默认 3DGS 后端是 GraphDECO。旧的 minimal gsplat 路线只作为 debug/smoke fallback，不作为真实实验默认结果。

## 资产分层

| 层 | 主要产物 | 作用 |
|---|---|---|
| Visual | 3DGS / semantic splat / visual mesh | 看起来像真实场景 |
| Geometry | point cloud / object mesh / background planes | 支撑重建、对齐和导出 |
| Collision | simplified mesh / box / convex hull / compound collider | 让角色、物体、射线和物理系统可交互 |
| Semantic | object ids / labels / probabilities / scene graph | 查询“这是什么、能做什么、和谁相邻” |
| Physics | body type / mass / friction / restitution / material | 进入 MuJoCo、Unity、Isaac 的仿真合同 |
| Adapter | `unity_adapter.json`、MuJoCo XML、review HTML | 给不同 runtime 消费 |

核心原则：3DGS 是视觉层；碰撞、导航、交互和语义必须有独立资产承接。

## 项目边界

Video2Mesh 当前负责：

- 从真实视频抽帧并建立相机/点云/3DGS。
- 跟踪 2D masks 并融合成 3D object masks。
- 生成 semantic splats / probability splats。
- 选择 object frames 和 object crops。
- 导出 object mesh baseline、3DGS-derived mesh jobs、external mesh jobs。
- 生成 simulator asset bundle、adapter 和 QA 报告。

Video2Mesh 不应伪装负责：

- 商业级 photogrammetry texture baking。
- 完整神经 SDF 训练器。
- 物理引擎内部 solver。
- 所有遮挡区域的真实几何恢复。
- 自动生成百分百可信的质量、摩擦、恢复系数。

这些能力可以通过外部 backend 接入，但要保留输入/输出合同和 QA。

## 参考项目角色

| 项目 / 方法 | 角色 | 不能误解成 |
|---|---|---|
| SceneVerse++ | 结构化 3D scene understanding、PQ3D/SpatialLM 数据桥接 | 任意视频到 3DGS-to-mesh 的完整系统 |
| image-blaster | 单物体图像到 mesh、world 目录、Three.js viewer 资产约定 | Video2Mesh 的 simulator bundle 生成器 |
| World Labs / Marble | 静态 world/background 生成和 clean plate 思路 | 物体级仿真资产导出器 |
| SuGaR | 从 3DGS 提取 editable visual mesh 的高级后端 | P0 collider 主路线 |
| GS2Mesh | 用 3DGS 渲染 stereo views，再 depth fusion 成 mesh | 直接读取 Gaussian centers 连面 |
| SimAnything / PhysSplat | semantic Gaussian 到 dynamic Gaussian / physical object | mesh 补全或 Unity collider 替代品 |

## 当前系统状态

已闭合：

- 视频到相机/点云/3DGS 的工程链路。
- SAM2 2D mask tracking 和 2D-to-3D mask fusion。
- semantic/probability PLY 导出。
- object frame selection 和 object crops。
- simulator bundle、Unity/MuJoCo adapter、review pack。
- QA/readiness/showcase 报告。

仍是 baseline：

- 物体 mesh 对遮挡和细结构还不够稳定。
- object label 和 affordance 需要 open-vocabulary detector / VLM 增强。
- 真实尺度、质量、摩擦、恢复系数仍需校准或人工复核。
- 背景结构目前以 floor/wall/ceiling 等基础结构为主，door/window/cabinet 等需要更强 layout/scene graph。

## 仓库主要目录

```text
video2mesh/                 # Python CLI and pipeline implementation
tools/                      # shell helpers, remote run scripts, audit scripts
configs/                    # reusable config
docs/                       # current canonical docs
docs-blog/                  # relumeow.top static docs site and admin API
SceneVersepp/               # submodule / reference project
image-blaster/              # submodule / reference object generation project
exports/                    # generated runs, ignored by Git
dataset/                    # source videos, ignored by Git
checkpoints/                # model weights, ignored by Git
```

Generated videos, exports, model weights and 3D assets are intentionally ignored by Git.
