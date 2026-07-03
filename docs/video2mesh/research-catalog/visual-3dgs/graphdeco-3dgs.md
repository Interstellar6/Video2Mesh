---
title: GraphDECO 3D Gaussian Splatting
id: video2mesh-visual-3dgs-graphdeco-3dgs
category: 调研目录
visibility: public
summary: GraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# GraphDECO 3D Gaussian Splatting

![3DGS visual layer](../assets/stage-visual-3dgs.svg "GraphDECO 3DGS 在 Video2Mesh 中承担 visual proxy，不直接承担 collider")

## 链接

- Project page: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/
- GitHub: https://github.com/graphdeco-inria/gaussian-splatting
- Paper: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/3d_gaussian_splatting_high.pdf
- Venue: SIGGRAPH 2023

## 摘要要点

3D Gaussian Splatting 的核心是用 COLMAP sparse points 初始化一组 3D Gaussians，通过颜色、opacity、位置、尺度、旋转和各向异性协方差优化来拟合多视角图像。论文同时提出 density control 和 visibility-aware splatting renderer，使训练和实时渲染都比传统 NeRF 路线更适合交互展示。

对 Video2Mesh 来说，3DGS 是最强 visual proxy：它让扫描房间看起来真实，也能渲染 novel view、截图和语义可视化。但 Gaussian 并不等价于真实 surface，直接拿 Gaussian center 做 Poisson 或 collider 会产生壳状伪影、飞面和语义串色。

## Pipeline

| 阶段 | 作用 | 输出 |
|---|---|---|
| COLMAP initialization | 用 sparse points 和 camera 初始化 Gaussian | 初始 3D Gaussians |
| differentiable splatting | 将 Gaussians 渲染回训练视角 | RGB reconstruction loss |
| densification / pruning | 补充细节并移除低贡献 Gaussian | 更密的 visual proxy |
| export / viewer | 导出 PLY、Splat、SPZ/SOG 等 | Web/桌面 visual layer |

## 输入与输出

输入：COLMAP 相机、图像、稀疏点云。输出：Gaussian PLY / point_cloud.ply、viewer 可消费的 splat 资产、可选 semantic/probability splats。

## 在 Video2Mesh 中的位置

P0 visual layer。当前 bedroom_4 formal run 中，GraphDECO 30k 提供主要视觉资产，并作为语义投影、GS2Mesh、semantic splats 和 Web proxy demo 的输入。它不直接承担 mesh collider，但可以给 mesh 重建提供 novel-view RGB/depth/mask evidence。

## 输出结果摘录

本周实验说明：3DGS 视觉层对展示非常有价值，但由 Gaussian center 直接做 Poisson 的路线效果不稳定。`open3d_poisson_3dgs_alpha005_sample500k` 体量可控，却有壳状伪影和粘连；正式 semantic mesh 中 Open3D Poisson 语义覆盖率只有 32.21%，明显弱于 COLMAP Delaunay local transfer。

## 接入判断

- P0：继续作为 visual proxy 主线。
- P1：接 semantic splats、face sidecar、object crop/ref image 生成。
- 风险：严禁把 Gaussian center 直接解释成物理表面；碰撞层必须另走 mesh/collider proxy。
