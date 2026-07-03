---
title: Mesh 重建阶段
id: mesh-reconstruction
category: Research Catalog
summary: 按场景级 collider 和物体级 visual mesh 两个目标，整理 COLMAP Delaunay、Poisson、GS2Mesh、SuGaR、2DGS/GOF 等路线。
tags:
  - Research Catalog
  - Mesh
  - GS2Mesh
  - SuGaR
  - Poisson
---

# Mesh 重建阶段

Mesh 重建不能只问“哪个方法画面最好”，还要区分目标：场景级 static collider 需要稳定、轻量、可碰撞；物体级 visual mesh 需要更好的外观、边界和补全能力。

![Mesh 重建路线](../assets/stage-mesh.svg "Delaunay/Poisson 适合 static collider；GS2Mesh/TSDF、SuGaR/2DGS 更适合 visual mesh 对照和升级")

## 主要项目和模型

| 项目 / 方法 | 简介 | 当前定位 | 实测/判断 |
|---|---|---|---|
| COLMAP Delaunay mesher | 利用 COLMAP dense workspace 直接生成 mesh | P0 scene collider 主路线 | 本项目 bedroom 场景输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB，适合 Web/Unity 静态碰撞代理 |
| Open3D Poisson / BPA | 点云 + normals 到 watertight-ish mesh 的自动化 baseline | baseline / fallback / debug | 对 3DGS center point cloud 容易生成壳状伪影和漂浮面 |
| CloudCompare / PoissonRecon | 点云人工检查、法线估计、Poisson 建面工具链 | 人工检查和传统建面对照 | 快速可视化好用，但不应直接作为唯一生产路线 |
| GS2Mesh | 从训练后 3DGS 渲染 stereo/multiview，再估深并 TSDF fusion | P1/P2 object visual mesh benchmark | 思路比直接 Gaussian center 连面更合理；raw mesh 很大，需减面和清理 |
| SuGaR | surface-aligned Gaussians + mesh extraction + editable mesh | P2 高质量 visual mesh 对照 | 需要额外环境和优化，短期不放进 P0 主链路 |
| 2DGS / GOF | 从 Gaussian 表面约束角度改训练或优化形式 | P2/P3 研究升级 | 有潜力减少后处理 mesh 问题，但工程替换成本高 |
| Neural SDF / NeuS / VolSDF | 神经隐式表面重建 | P3 离线高质量资产 | 训练成本高，和当前 3DGS 主链路并行成本大 |

## 推荐路线

```text
scene collider:
  COLMAP dense workspace -> Delaunay mesh -> simplify -> GLB

object visual mesh:
  3DGS rendered RGB/depth/mask -> masked TSDF -> cleanup -> GLB

quality benchmark:
  GS2Mesh / SuGaR / 2DGS on selected objects or small scenes
```

## 判断

当前 P0 应把 COLMAP Delaunay 作为场景 collider 主链路；Open3D/CloudCompare Poisson 做 baseline 和人工检查；GS2Mesh/SuGaR 做后续 per-object visual mesh 对照。这样可以先完成交互闭环，再逐步提高物体 mesh 质量。
