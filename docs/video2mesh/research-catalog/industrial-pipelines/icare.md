---
title: Icare / 学长文档路线
id: video2mesh-industrial-pipelines-icare
category: 调研目录
visibility: public
summary: 学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。
tags:
  - 工业资产管线
  - Research Catalog
---

# Icare / 学长文档路线

![Icare / 学长文档路线](../assets/pipeline-overview.svg "学长/工业路线共同强调 visual proxy、collider proxy 和 metadata sidecar 的分层")

## 链接

- Local notes: 学长文档 / Icare 调研材料
- Related industrial pattern: World Labs / Marble static world assets
- Related implementation reference: image-blaster viewer and object job conventions

## 简介

学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部 metadata。这个分层和 Video2Mesh 当前方向高度一致：3DGS 负责看，COLMAP/Poisson/primitive/convex collider 负责碰撞，face/object sidecar 负责语义与物理属性。

这类方案的重点不在单个算法，而在 asset bundle contract：viewer 能加载什么、engine 需要什么、哪些资产是 visual-only、哪些资产可参与 raycast/physics。

## Pipeline 摘要

| 阶段 | 作用 |
|---|---|
| visual proxy | 3DGS/Splat/Spark/SuperSplat 等承担高质量显示 |
| interaction proxy | GLB mesh、simplified collider、primitive bodies 承担交互 |
| semantic metadata | object id、label、face/material sidecar |
| physics metadata | body type、mass、friction、restitution、constraints |
| adapter | Web/Unity/MuJoCo/Isaac 运行时转换 |

## 输入与输出

输入：扫描/生成资产、3DGS、mesh、object metadata。输出：viewer 可消费的 visual + collider + metadata bundle。

## 在 Video2Mesh 中的位置

作为 Video2Mesh 架构参考，不能替代本项目导出合同。它帮助确认本周 demo 的方向：视觉代理与碰撞代理分开，最终由 Video2Mesh 自己承接语义、物理属性和引擎 adapter。

## 接入判断

- P0：借鉴分层合同。
- P1：将 object sidecar、physics sidecar 和 adapter 做成项目自己的 bundle。
- 风险：外部文档/演示不是可直接复用代码，需要 Video2Mesh 自己承接导出和 QA。
