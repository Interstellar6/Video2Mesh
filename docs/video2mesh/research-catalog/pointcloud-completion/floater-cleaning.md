---
title: Floater Cleaning
id: video2mesh-pointcloud-completion-floater-cleaning
category: 调研目录
visibility: public
summary: 先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Floater Cleaning

![Floater cleaning](../assets/stage-completion.svg "清理点云和 3DGS 漂浮点能显著改善后续 mesh 重建与相机 framing")

## 链接

- Open3D statistical outlier removal: https://www.open3d.org/docs/latest/tutorial/Advanced/pointcloud_outlier_removal.html
- SuperSplat editing: https://playcanvas.com/products/supersplat
- 3DGS pruning reference: https://github.com/graphdeco-inria/gaussian-splatting

## 简介

Floater cleaning 指清理 3DGS/点云中的漂浮点、长尾离群点、低 opacity 结构和异常尺度高斯。它能改善截图、viewer framing、mesh reconstruction 和 semantic transfer。尤其是把 Gaussian center 当作点云做 Poisson 时，未清理的飞点会把 surface 拉成壳状或大面积粘连。

清理不能过度：窗帘、椅腿、灯、床品边缘等真实薄结构也可能看起来像离群点，需要分类型阈值和人工 QA。

## Pipeline

| 阶段 | 作用 |
|---|---|
| statistics | 统计 bbox quantile、opacity、scale、distance、component |
| outlier filtering | 移除远端点、低贡献高斯和孤立分量 |
| optional manual edit | 用 SuperSplat/CloudCompare 人工检查 |
| rebuild downstream | 重新导出 mesh、semantic splats 或 viewer assets |
| QA | 对比截图、mesh face coverage 和 object labels |

## 输入与输出

输入：point cloud、Gaussian PLY、semantic splats。输出：cleaned point cloud / cleaned Gaussian、过滤报告、QA 截图。

## 在 Video2Mesh 中的位置

P0 预处理，应放在 semantic transfer 和 mesh 重建前。本周 Open3D Poisson 的壳状伪影说明，点云/高斯清理是直接影响 mesh 质量的上游步骤。

## 接入判断

- P0：进入，至少记录过滤前后统计。
- P1：和 semantic/object-aware cleanup 结合，避免删真实物体。
- 风险：阈值场景相关，需要可视化审核。
