---
title: Scene Layout Completion
id: video2mesh-pointcloud-completion-scene-layout
category: 调研目录
visibility: public
summary: 场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Scene Layout Completion

![Scene layout completion](../assets/stage-completion.svg "Scene layout completion 把墙、地、天花板、门窗和支撑面抽象成可交互结构")

## 链接

- Open3D plane segmentation: https://www.open3d.org/docs/latest/python_api/open3d.geometry.PointCloud.html#open3d.geometry.PointCloud.segment_plane
- PlaneRCNN reference: https://github.com/NVlabs/planercnn
- Structured3D dataset reference: https://structured3d-dataset.org/

## 简介

Scene layout completion 关注墙、地、天花板、门窗、柜体等大结构，用于 collider、导航边界、支撑关系和可编辑场景结构。它比单纯补纹理更接近交互需求：用户要走、点击、放置物体，首先需要稳定 floor/wall/support planes。

对室内场景，布局补全可以从 plane fitting、semantic labels 和 VLM 关系推理开始，不一定要先跑复杂生成模型。

## Pipeline

| 阶段 | 作用 |
|---|---|
| semantic mesh / point cloud | 提供 floor/wall/window/door/cabinet 等候选 |
| plane / primitive fitting | 拟合 floor、wall、ceiling、support plane |
| topology repair | 补齐墙角、地面边界和被遮挡支撑面 |
| collider export | 输出 layout primitives 或 simplified structure mesh |
| scene graph binding | 标注 support/on/near/inside 等关系 |

## 输入与输出

输入：点云、mesh、语义、VLM/scene graph。输出：layout primitives、结构 mesh、support planes、navigation/collider boundaries。

## 在 Video2Mesh 中的位置

P1 物理代理补全，比视觉补纹理更重要。正式 semantic mesh 已经有 floor、wall、window、door 等标签，下一步可以先从 floor/wall plane fitting 做起。

## 接入判断

- P0：不作为首要阻塞，但 floor/wall primitive 可作为 collider fallback。
- P1：进入支持放置、导航和物体关系推理。
- 风险：自动补全可能改变真实空间尺度，必须和 COLMAP 坐标对齐。
