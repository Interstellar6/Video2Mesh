---
title: Video2Mesh Pipeline
id: video2mesh-pipeline
category: 项目文档
visibility: public
summary: 按流程说明 Video2Mesh 从视频输入到可交互仿真资产的主要阶段和输出合同。
tags:
  - Pipeline
  - COLMAP
  - 3DGS
  - Mesh
---

# Video2Mesh Pipeline

## 总流程

```text
input video
  -> extract frames
  -> COLMAP / pose fallback
  -> dense point cloud
  -> GraphDECO 3DGS visual layer
  -> 2D masks and tracking
  -> 2D-to-3D semantic fusion
  -> mesh reconstruction
  -> object mesh completion
  -> collider / physics proxy
  -> simulator asset bundle
  -> Web / Unity / MuJoCo / Isaac adapters
```

## 阶段合同

| 阶段 | 输入 | 输出 | 当前建议 |
|---|---|---|---|
| 输入与位姿 | scan video | frames、cameras、sparse/dense points | COLMAP 主线，MASt3R/DUSt3R/VGGT 作为 fallback 调研 |
| 视觉层 | posed images | 3DGS / splat | GraphDECO 3DGS，Spark/SuperSplat 做浏览器查看 |
| Mesh 重建 | dense workspace / 3DGS renders / point cloud | GLB/PLY mesh | P0 用 COLMAP Delaunay collider，P1 做 per-object visual mesh |
| 语义 | GroundingDINO/SAM2 2D masks、clean 3DGS、mesh | binary semantic core、限额轻量 SuperSplat overlay、face sidecar | 2D probability 直接投影到同一份 clean 3DGS；full core 不直接作为 viewer 输入 |
| 补全 | crops、masks、bbox、clean plate | 完整 object mesh / background asset | image-blaster、Hunyuan3D、Meshy、TRELLIS 等作为后端 |
| 物理代理 | mesh、bbox、semantic label | collider、mass、friction、body type | static mesh + primitive/convex proxy 先跑通 |

## 当前 P0 主链路

P0 的目标是展示和交互闭环，不是最佳画质：COLMAP dense + Delaunay mesh 做场景 collider，GraphDECO 3DGS 做 visual layer，语义与物理属性通过 sidecar 管理。默认语义路线使用 2D mask probability backprojection 写 binary semantic core，并从中生成 semantic mesh；SuperSplat 检查时打开 scene 3DGS 加轻量 semantic overlay，不直接加载 full semantic core。默认 overlay 只保留高置信语义 Gaussian，最多 180,000 个，且不会生成第二份完整 semantic SuperSplat 复制件。所有 mesh 同时输出单面 collider/source 和双面 display companion，避免 viewer 的 backface culling 改变质量判断。
