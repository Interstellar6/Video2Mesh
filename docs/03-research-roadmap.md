---
title: 技术调研与路线图
category: Research
summary: 学术界、工业界和参考项目对 Video2Mesh 的启发，压缩为可执行路线图。
tags:
  - Research
  - Scene Graph
  - Mesh
  - 3DGS
---

# 技术调研与路线图

## 总结判断

Video2Mesh 不应该押注单一“3DGS 转 mesh”方法。更稳的路线是把问题拆成阶段：

```text
pose and reconstruction
  -> visual 3DGS
  -> semantic object masks
  -> mesh / collider / physics assets
  -> scene graph and simulator adapters
```

学术方法和工业产品给出的共同启发是：视觉表达、物理碰撞、语义结构和交互逻辑要分层。

## 方法横评

| 方向 | 代表方法 | 对 Video2Mesh 的价值 | 优先级 |
|---|---|---|---|
| 经典 SfM/MVS | COLMAP、OpenMVS | 稳定 baseline，输出标准相机和点云 | P0 |
| 学习式几何兜底 | DUSt3R、MASt3R、MegaSaM、VGGT | 当 COLMAP 失败时补 pose/depth/point map | P1 |
| 3DGS visual | GraphDECO 3DGS、Spark/SuperSplat | 高质量场景视觉层 | P0 |
| mask tracking | GroundingDINO、SAM、SAM2、DEVA/XMem | object masks 和语义入口 | P0/P1 |
| 2D-to-3D semantic | projection voting、SVLGaussian-style backprojection | semantic splats / object masks | P0/P1 |
| point-cloud meshing | Poisson、BPA、alpha shape | 快速 scene collider / baseline mesh | P0 |
| depth fusion mesh | 3DGS rendered depth/mask + TSDF | object visual mesh 主路线 | P1 |
| 3DGS-aware mesh | SuGaR、GS2Mesh、2DGS、GOF | 高质量 visual mesh 升级 | P2 |
| scene graph | SpatialLM、PQ3D、open-vocabulary 3D scene graph | 结构化关系、support、affordance | P1/P2 |
| generated completion | Hunyuan3D、Meshy、TRELLIS、InstantMesh | 遮挡物体 visual mesh 补全 | P1 |
| dynamic Gaussian | SimAnything / PhysSplat | 软体/颗粒/动态视觉仿真 | P2 |

## 学术路线

### 位姿与重建

COLMAP 仍是最稳的工程 baseline：可复现、输出标准、能接 GraphDECO 3DGS。问题是它对视频质量、视差、纹理、运动模糊敏感。

建议：

- 默认 COLMAP。
- readiness 失败时使用 learned pose/depth fallback。
- 保留 scan QA：覆盖、视差、模糊、注册率、点数。

### 3DGS

3DGS 适合做 visual scene，不适合直接做 collider。原始 Gaussian 是离散椭球体集合，没有 mesh topology。

建议：

- 3DGS 作为视觉层和多视角证据生成器。
- object mesh 从 rendered RGB/depth/normal/mask 融合得到。
- semantic splats 作为语义主数据之一。

### 语义与 scene graph

只得到 object mask 还不够。交互场景需要知道：

- object category。
- support relation，例如 chair supported_by floor。
- spatial relation，例如 cup on table。
- affordance，例如 chair sit-able、table placeable。
- background structure，例如 floor、wall、door、window、cabinet。

第一版 scene graph 可以是 sidecar JSON，不要强行写入 mesh：

```json
{
  "objects": [
    {
      "object_id": "chair_01",
      "category": "chair",
      "bbox": {},
      "support": {"type": "floor"},
      "affordances": ["sit"],
      "asset_refs": {
        "visual_mesh": "...",
        "collider": "...",
        "semantic_splats": "..."
      }
    }
  ]
}
```

## 业界路线

| 产品 / 实践 | 启发 |
|---|---|
| Matterport | 标准化资产包、测量、mesh/点云/E57/MatterPak 分层 |
| Apple RoomPlan | 参数化 room layout 比纯 mesh 更适合交互和编辑 |
| Polycam / Scaniverse | Gaussian splat 和 mesh 分用途输出 |
| RealityCapture / RealityScan | meshing 前做 quality heatmap 和 mask/align QA |
| PlayCanvas / SuperSplat | 3DGS 可做实时视觉层，但碰撞需要传统代理 |
| Unity / Unreal | 交互依赖 collider、prefab/component、navmesh 和 metadata |

## SuGaR 与 GS2Mesh

SuGaR 的思路是让 Gaussian 更贴近表面，再提取 editable mesh。它适合做 visual mesh 升级，但不是第一版 collider。

![SuGaR pipeline and editing result](https://anttwo.github.io/sugar/results/full_teaser.png "SuGaR 官方项目页图：从 3DGS 提取可编辑 mesh，并保持高质量 Gaussian rendering / compositing 效果")

GS2Mesh 的思路是把 3DGS 当渲染器，生成 stereo-aligned novel views，用 stereo depth 得深度，再 TSDF fusion 成 mesh。它和 Video2Mesh 当前 “render views -> TSDF” 方向更契合。

推荐顺序：

1. 先强化现有 `3DGS render depth/mask -> TSDF`。
2. 加 GS2Mesh-style stereo depth 作为 depth quality enhancement。
3. 用 SuGaR 对单物体/小场景做高级 visual mesh benchmark。

## SceneVerse++ 的位置

SceneVerse++ 不做 3DGS-to-mesh。它更像结构化 3D scene understanding / data generation 框架，使用已有 mesh/point cloud/metadata，服务 SpatialLM、PQ3D、VQA、VLN 等任务。

Video2Mesh 可借：

- `mesh.ply`、`camera_info.json`、`metadata.json`、`data_info.json` 等数据组织。
- PQ3D / SpatialLM 对 object/layout understanding 的评估思路。
- scene graph、object relation、language supervision 的数据结构。

不能指望它替代：

- 从视频重建 3DGS。
- 从 3DGS 自动生成 mesh。
- simulator collider / physics bundle。

## image-blaster 的位置

image-blaster 主要提供：

- object crop / reference image 到 generated mesh 的资产约定。
- `worlds/<world>/output/<object>/` 目录结构。
- browser viewer 和 local asset loading 思路。
- 可接 Hunyuan3D / Meshy / FAL / InstantMesh 等后端。

Video2Mesh 应把它当作 object visual mesh completion helper。simulator bundle、physics、collider 和 adapter 仍由 Video2Mesh 负责。

## SimAnything / PhysSplat 的位置

SimAnything / PhysSplat 关注的是：

```text
static 3DGS
  -> movable object discovery
  -> physics property inference
  -> Gaussian / particle dynamics
  -> dynamic splat rendering
```

它不是 mesh 补全方法，也不能替代 Unity/MuJoCo collider。最值得借的是：

- MLLM/VLM 估计物理属性草稿。
- semantic Gaussian 到 physical object 的转换层。
- dynamic Gaussian object 与 static background collider 的分层。

短期落地应该先做 `mllm_physics` provider，自动生成质量、材质、摩擦、刚体/软体候选，再进 `simulator-physics-quality-report`。

## 路线图

### P0：稳定可展示闭环

- COLMAP + GraphDECO 3DGS。
- SAM2 mask tracking。
- full point cloud 2D-to-3D mask fusion。
- semantic / viewer PLY。
- simulator bundle + Unity/MuJoCo adapter。
- review pack 和 QA。

### P1：让资产可交互

- scene-level static collider。
- object visual mesh 从 3DGS rendered depth/mask 做 TSDF。
- collider proxy：box、convex hull、compound primitive。
- object label、support plane、affordance sidecar。
- external object completion backend。

### P2：高质量 mesh 和动态仿真

- GS2Mesh-style stereo depth fusion。
- SuGaR / 2DGS / GOF benchmark。
- MLLM physics annotation。
- dynamic Gaussian assets for deformable/particle objects。
- scene graph integration with SpatialLM/PQ3D-style outputs。

### P3：产品化

- scan QA and capture guidance。
- scale calibration workflow。
- texture baking and material estimation。
- game-scene bundle。
- deterministic validation and regression demos。
