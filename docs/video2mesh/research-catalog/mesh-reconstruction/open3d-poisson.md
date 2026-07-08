---
title: Open3D Poisson
id: video2mesh-mesh-reconstruction-open3d-poisson
category: 调研目录
visibility: public
summary: Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。
tags:
  - Mesh 重建
  - Research Catalog
---

# Open3D Poisson

## 链接

- Open3D surface reconstruction docs: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html
- Open3D Poisson API: https://www.open3d.org/docs/latest/python_api/open3d.geometry.TriangleMesh.html
- Kazhdan Poisson reconstruction reference implementation: https://github.com/mkazhdan/PoissonRecon

## 简介

Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。它的优点是工程成本低、容易放进 CLI、输出 GLB/PLY 很方便；缺点是强依赖点云质量和法线方向，遇到 3DGS center cloud 时容易把“视觉采样点”错误当作真实 surface。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| point filtering | 去除低 alpha、尺度异常、拉长 Gaussian 或离群点 |
| normal estimation/orientation | 用 Open3D 估计并朝向一致化法线 |
| Poisson reconstruction | 从带法线点云重建 watertight-ish surface |
| density/component cleanup | 按 density、连通分量、bbox 裁剪坏面 |
| decimation/export | 减面并导出 PLY/GLB |

输入：带法线点云，可以来自 COLMAP dense fused point cloud，也可以来自过滤后的 3DGS centers。输出：Poisson mesh、decimated mesh、预览图和 route report。

## 在 Video2Mesh 中的位置

baseline/fallback。3DGS center point cloud 上容易生成壳状伪影，因此不适合被解释为真实表面；如果输入换成 COLMAP dense fused point cloud，会更接近传统 MVS mesh，但仍不如 Delaunay route 稳定。

本项目 `alpha005_sample500k` 实验输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。formal semantic run 中 Open3D Poisson dense fused voxel10 的 semantic coverage 只有 32.21%，unknown/background 高达 67.79%，说明它不适合承载主 semantic sidecar。

![Open3D Poisson 实验输出](../../experiments/assets/02-open3d-poisson-3dgs-alpha005-sample500k.png "3DGS center Poisson 输出体量可控，但有壳状伪影、粘连和漂浮面")

## 接入判断

- P0：不作为主 collider，只保留 fallback。
- P1：用于快速 debug 点云清理和 postprocess 参数。
- 风险：如果输入是 3DGS centers，结果容易“看起来有面但语义和物理都不可靠”。
