---
title: CloudCompare / PoissonRecon
id: video2mesh-mesh-reconstruction-cloudcompare-poisson
category: 调研目录
visibility: public
summary: CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。
tags:
  - Mesh 重建
  - Research Catalog
---

# CloudCompare / PoissonRecon

## 链接

- CloudCompare: https://www.cloudcompare.org/
- PoissonRecon: https://github.com/mkazhdan/PoissonRecon
- Open3D reconstruction docs: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html

## 简介

CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。它更像“诊断台”和人工 baseline，而不是无人值守 pipeline：优点是可视化、裁剪、法线检查很直观；缺点是人工步骤多，难以稳定复现成项目主链路。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| load point cloud | 导入 COLMAP dense / 3DGS center / fused point cloud |
| visual inspection | 人工检查漂浮点、空洞、尺度和噪声 |
| crop/clean | 裁剪 bbox、删除离群点、保留主连通结构 |
| normal estimation | 估计并定向 normals |
| PoissonRecon | 生成三角网格 |
| postprocess | 裁剪低 density、减面、导出 GLB/PLY |

输入：点云。输出：可视化检查结果、Poisson mesh、参数判断。

## 在 Video2Mesh 中的位置

人工诊断和方法对照，不建议直接作为无人值守主链路。它适合用来回答“为什么 Open3D/Poisson 输出坏了”“点云是不是本身就有漂浮/空洞”“法线方向是否错误”等问题。

在本周实验中，CloudCompare + PoissonRecon 的经验支持了一个判断：3DGS center point cloud 不能等同真实表面，直接建面会出现壳状伪影和粘连；更稳的 collider 应该回到 COLMAP dense/Delaunay 或经过严格清理的 MVS point cloud。

## 接入判断

- P0：不进入自动主链路。
- P1：作为人工 QA/诊断工具保留。
- P2：如果要把人工经验自动化，可把 CloudCompare 中有效步骤翻译成 Open3D/Trimesh 脚本。
