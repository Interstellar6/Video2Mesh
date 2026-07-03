---
title: COLMAP Delaunay Mesher
id: video2mesh-mesh-reconstruction-colmap-delaunay
category: 调研目录
visibility: public
summary: COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。
tags:
  - Mesh 重建
  - Research Catalog
---

# COLMAP Delaunay Mesher

## 链接

- COLMAP docs: https://colmap.github.io/
- COLMAP dense reconstruction: https://colmap.github.io/tutorial.html
- Poisson/Delaunay meshing commands: `colmap poisson_mesher` / `colmap delaunay_mesher`

## 简介

COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。它的视觉质量通常不如 3DGS，但几何上更适合作为 collision proxy：mesh 较轻、位置和尺度跟 SfM/MVS workspace 一致、可直接导出 GLB/PLY 给 runtime 使用。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| sparse reconstruction | 从视频抽帧估计相机位姿 |
| image undistortion | 准备 dense stereo workspace |
| patch match stereo | 得到多视角深度 |
| stereo fusion | 融合为 dense point cloud |
| Delaunay meshing | 从 dense workspace/点云建场景级 mesh |
| GLB postprocess | double-sided/indexed/decimation，供 Web viewer 或 engine 使用 |

输入：COLMAP dense workspace 或 dense fused point cloud。输出：scene-level mesh，适合 static collision proxy。

## 在 Video2Mesh 中的位置

P0 scene collider 主路线，适合轻量静态碰撞代理。当前 bedroom4 实验里，COLMAP Delaunay 输出 82,920 vertices / 167,082 triangles，GLB 约 3.0MB；formal semantic run 的 local transfer 覆盖率 84.98%，能拆出 16 个 object mesh split。

![COLMAP Delaunay dense mesh](../assets/03-colmap-delaunay-dense.png "COLMAP Delaunay mesh 视觉细节有限，但轻量稳定，适合作为隐藏 collider")

## 接入判断

- P0：进入主链路，作为 hidden static collider。
- P1：结合 semantic sidecar，支持 raycast 后返回 object/label。
- 风险：薄结构和细节会缺失，所以不能替代 3DGS visual layer。
