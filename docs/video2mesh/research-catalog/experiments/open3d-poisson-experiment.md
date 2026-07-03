---
title: Open3D Poisson 实验
id: video2mesh-experiments-open3d-poisson-experiment
category: 调研目录
visibility: public
summary: 使用过滤后的 3DGS center point cloud 做 Poisson baseline。
tags:
  - 本项目实验
  - Research Catalog
---

# Open3D Poisson 实验

![Open3D Poisson 3DGS alpha005 sample500k](../assets/02-open3d-poisson-3dgs-alpha005-sample500k.png "Open3D Poisson 输出体量可控，但壳状伪影、粘连和漂浮面明显")

## 实验目的

使用过滤后的 3DGS center point cloud 做 Poisson baseline，验证“直接把 Gaussian center 当点云重建 mesh”是否足够作为 Video2Mesh fallback。

## 输入与输出

| 项目 | 数值/说明 |
|---|---|
| 输入 | `alpha005_sample500k`，50 万个 3DGS center samples |
| 输出 | 约 100,965 vertices / 200,000 triangles |
| GLB | 约 5.23MB |
| formal semantic run | 100,705 vertices / 199,999 faces |
| semantic coverage | 32.21%，unknown/background 67.79% |

## 在 Video2Mesh 中的位置

适合 fallback/debug，不适合最终 surface。它的问题不是文件大小，而是几何语义都不够稳定：3DGS center 并不等于真实表面，因此 Poisson 会产生壳状伪影、粘连、漂浮面和大量 unknown/background。

## 接入判断

- P0：不作为主 collider。
- P1：保留 debug/fallback，帮助检查点云清理、bbox crop 和 postprocess 参数。
- 风险：semantic transfer 覆盖低，不能用它代表正式 semantic mesh 质量。
