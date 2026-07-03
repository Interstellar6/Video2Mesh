---
title: Semantic Splats
id: video2mesh-semantic-scene-graph-semantic-splats
category: 调研目录
visibility: public
summary: semantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Semantic Splats

![Semantic splats](../assets/stage-semantics.svg "Semantic splats 把 3DGS visual proxy 与 object/label probability 绑定，用于可视化和查询")

## 链接

- LangSplat: https://langsplat.github.io/
- Feature 3DGS / semantic Gaussian survey reference: https://github.com/MrNeRF/awesome-3D-gaussian-splatting
- Segment Anything: https://segment-anything.com/

## 简介

Semantic splats 是给 Gaussian 或点云附加 object id、label 或 probability 的路线。它可以让 3DGS visual layer 支持 hover、筛选、按类别渲染、点击查询和调试语义传播质量。

它和 mesh face sidecar 的职责不同：semantic splats 适合看和查视觉层，mesh face sidecar 适合 collider raycast 后查 face/object/material。最终交互系统往往两个都要有。

## Pipeline

| 阶段 | 作用 |
|---|---|
| 2D masks / labels | SAM、Grounded-SAM 或 VLM 提供每帧语义证据 |
| projection / voting | 将 2D mask 证据投到 3D points/Gaussians |
| probability aggregation | 为每个 Gaussian/point 保存 label probabilities |
| viewer export | 导出 semantic PLY / colored splats |
| mesh transfer | 可选把 semantic splats 再映射到 mesh faces |

## 输入与输出

输入：3DGS/点云、相机、2D masks 和 labels。输出：semantic/probability PLY、colored splats、object mask clouds、后续 face transfer 证据。

## 在 Video2Mesh 中的位置

P0/P1 语义可视化，不替代 mesh face sidecar。本周 formal semantic mesh 结果中也包含 semantic dense/3DGS manifest，可以作为 mesh semantic transfer 的输入之一。

## 输出/接入记录

正式结果里，COLMAP Delaunay projected splats 路线达到了 80.13% face semantic coverage，低于 local transfer 的 84.98%，但仍说明 semantic splats 可以作为 mesh 语义回灌证据。

## 接入判断

- P0：作为语义可视化和 transfer evidence。
- P1：与 face sidecar、object split 联动。
- 风险：投影误差和遮挡会造成串色，需要深度可见性过滤和 face graph smoothing。
