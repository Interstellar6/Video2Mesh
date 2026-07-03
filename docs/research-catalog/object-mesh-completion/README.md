---
title: 物体 Mesh 补全阶段
id: object-mesh-completion
category: Research Catalog
summary: 梳理 Hunyuan3D、Meshy、TRELLIS、InstantMesh、image-blaster 等物体级生成和补全方案。
tags:
  - Research Catalog
  - Object Mesh
  - Hunyuan3D
  - image-blaster
---

# 物体 Mesh 补全阶段

物体级补全适合从 object crops、selected frames、mask 和粗 3D bbox 出发，生成 object-local visual mesh，再对齐回原始场景。

## 主要项目和模型

| 项目 / 方法 | 简介 | 输入输出 | 对 Video2Mesh 的作用 | 注意 |
|---|---|---|---|---|
| Hunyuan3D | 单图/少图到 3D asset 的生成式模型/服务生态 | 输入 reference image，输出 mesh/texture | 可作为 image-blaster object mesh backend，补全遮挡物体外观 | 尺度、朝向、支撑面必须由 Video2Mesh 校准 |
| Meshy | 商业 3D asset 生成服务 | 文本/图片到 mesh | 可作为 object mesh alternative backend | 结果需要 provenance 和 QA |
| TRELLIS | 3D asset generation 研究/开源路线 | 图片/文本到 3D asset | 可作为本地或远端 object completion 候选 | 环境、质量和授权需单独评估 |
| InstantMesh | feed-forward image-to-3D mesh 方案 | 单图/多视图到 mesh | 快速生成 object-local mesh baseline | 复杂遮挡和真实尺度需要后处理 |
| image-blaster | 管理 world/object 目录、reference image、Hunyuan/Meshy jobs 和 React/Three viewer 的工程项目 | `worlds/<world>/output/<object>/object.json`、GLB/OBJ | 可复用其 object mesh generation convention 和 viewer 思路 | 它不是 simulator bundle 生成器 |

## 接入 Video2Mesh 的正确位置

```text
object masks / selected frames
  -> prepare-object-images
  -> export-image-blaster
  -> Hunyuan3D / Meshy / TRELLIS / InstantMesh
  -> import-object-meshes
  -> fit-object-local-meshes-to-bbox
  -> export-simulator-assets
```

## 关键 QA

- object-local mesh 是否对齐 observed 3D bbox。
- 支撑面是否贴近 floor/table/chair seat。
- scale 是否可信。
- 是否需要拆分 visual mesh 和 collider proxy。
- 补全来源和置信度是否写入 metadata，便于导师/用户知道哪些部分是生成的。
