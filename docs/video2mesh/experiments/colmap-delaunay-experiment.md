---
title: COLMAP Delaunay Dense 实验
id: video2mesh-experiments-colmap-delaunay-experiment
category: 实验目录
visibility: public
summary: COLMAP dense + Delaunay mesher 生成场景级 mesh。
tags:
  - 本项目实验
---

# COLMAP Delaunay Dense 实验

![COLMAP Delaunay dense mesh](assets/03-colmap-delaunay-dense.png "COLMAP Delaunay dense mesh 视觉细节不如 3DGS，但几何轻量稳定，更适合场景级 static collision proxy")

## 实验目的

COLMAP dense + Delaunay mesher 生成场景级 mesh，用来验证传统 MVS mesh 能否作为 Video2Mesh 的 P0 static collider。

## 输入与输出

| 项目 | 数值/说明 |
|---|---|
| 输入 | COLMAP dense fused point cloud |
| 输出 | 82,920 vertices / 167,082 triangles |
| GLB | 约 3.0MB |
| formal semantic local transfer | 141,993 / 167,082 faces assigned |
| semantic coverage | 84.98% |
| object split | 16 个 object/local mesh |

## 在 Video2Mesh 中的位置

当前最适合 P0 static collider。它视觉上不如 3DGS/GS2Mesh，但作为碰撞代理有三个优势：轻量、拓扑更连续、可直接进入 GLB/physics runtime。formal semantic mesh 结果也说明它能承载 per-face semantic sidecar。

在下一步交互 demo 里，它应当作为隐藏 collider；视觉层仍由 3DGS/Splat 或 visual mesh 承担。

## 接入判断

- P0：进入主链路，作为 static mesh collider。
- P1：结合 semantic sidecar 支持点击查询、object split、可交互代理。
- 风险：视觉细节不足，不能单独替代 3DGS visual layer。
