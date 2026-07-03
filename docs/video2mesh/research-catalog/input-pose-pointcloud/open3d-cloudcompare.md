---
title: Open3D / CloudCompare
id: video2mesh-input-pose-pointcloud-open3d-cloudcompare
category: 调研目录
visibility: public
summary: Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。
tags:
  - 输入、位姿与点云
  - Research Catalog
---

# Open3D / CloudCompare

![点云处理阶段](../assets/stage-input-pose.svg "Open3D 更适合脚本化处理，CloudCompare 更适合人工检查和可视化诊断")

## 链接

- Open3D docs: https://www.open3d.org/docs/latest/
- Open3D surface reconstruction: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html
- CloudCompare: https://www.cloudcompare.org/
- CloudCompare PoissonRecon plugin: https://www.cloudcompare.org/doc/wiki/index.php/Poisson_Surface_Reconstruction_%28plugin%29

## 简介

Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计、手动分割和可视化对比。两者在 Video2Mesh 里都应该定位为工程诊断与 baseline 工具，而不是最终产品形态。

Open3D 的优势是可以被 CLI 批量调用，便于统一下采样、法线估计、outlier removal、Poisson reconstruction 和 mesh decimation。CloudCompare 的优势是肉眼检查非常快，适合判断某条路线为什么漂浮、破碎、壳化或语义串色。

## Pipeline

| 工具 | Pipeline | 适合用途 |
|---|---|---|
| Open3D | PLY/point cloud -> downsample/filter -> normal estimation -> Poisson/BPA/alpha shape -> mesh cleanup | 批量 baseline、自动统计、可复现实验 |
| CloudCompare | cloud/mesh -> manual crop -> normal/recon plugin -> visual inspection -> screenshots | 人工 QA、参数调试、汇报截图 |

## 输入与输出

输入：PLY/PCD/OBJ/GLB 等点云或 mesh。输出：cleaned point cloud、normals、Poisson/BPA mesh、diagnostic screenshot、density/connected component 等质量线索。

## 在 Video2Mesh 中的位置

debug 和 baseline 工具。Open3D Poisson 已经用于本周 mesh 重建实验；CloudCompare + 3D recon + Poisson 用于手动对照。结果说明它们能快速出 mesh，但对 3DGS center 或不干净点云非常敏感，容易生成壳状面、粘连面和 unknown/background 过高的语义区域。

## 接入判断

- P0：只保留 Open3D 的轻量清理/统计脚本，不把 Poisson 作为唯一 collider 主链路。
- P1：作为可复现实验 baseline 和失败诊断工具。
- 风险：Poisson 会在低密度区域补面，必须配合 density filter、connected-component cleanup 和人工 QA。
