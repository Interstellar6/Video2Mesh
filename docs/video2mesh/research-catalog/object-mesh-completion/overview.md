---
title: 物体 Mesh 补全阶段
id: object-mesh-completion
category: 调研目录
summary: 梳理 Hunyuan3D、Meshy、TRELLIS、InstantMesh、NOVA3R、image-blaster 等物体级生成和补全方案。
tags:
  - Research Catalog
  - Object Mesh
  - Hunyuan3D
  - image-blaster
visibility: public
---

# 物体 Mesh 补全阶段

物体级补全适合从 object crops、selected frames、mask 和粗 3D bbox 出发，生成 object-local visual mesh，再对齐回原始场景。

![物体补全阶段输入输出](../assets/stage-completion.svg "物体补全从 selected frames 和 mask 出发生成 object-local mesh，再由 Video2Mesh 对齐回场景")

## 主要项目和模型

| 项目 / 方法 | 简介 | 输入输出 | 对 Video2Mesh 的作用 | 注意 |
|---|---|---|---|---|
| Hunyuan3D | 单图/少图到 3D asset 的生成式模型/服务生态 | 输入 reference image，输出 mesh/texture | 可作为 image-blaster object mesh backend，补全遮挡物体外观 | 尺度、朝向、支撑面必须由 Video2Mesh 校准 |
| Meshy | 商业 3D asset 生成服务 | 文本/图片到 mesh | 可作为 object mesh alternative backend | 结果需要 provenance 和 QA |
| TRELLIS | 3D asset generation 研究/开源路线 | 图片/文本到 3D asset | 可作为本地或远端 object completion 候选 | 环境、质量和授权需单独评估 |
| NOVA3R | 非像素对齐 amodal 3D reconstruction | 1-2 张未标定位姿 RGB 图像或点云，到完整点云 PLY | 适合作为遮挡物体/局部场景点云补全，再接 mesh reconstruction 或 TRELLIS active voxel 路径 | 输出不是 textured mesh，尺度/坐标/碰撞代理必须由 Video2Mesh 后处理 |
| InstantMesh | feed-forward image-to-3D mesh 方案 | 单图/多视图到 mesh | 快速生成 object-local mesh baseline | 复杂遮挡和真实尺度需要后处理 |
| Restore3D | 面向破损/遮挡物体的形状与纹理联合修复 | 多视角 broken-object images 到 textured mesh | 适合处理局部缺失、破损或严重遮挡物体，保留 observed/restored provenance | 需要稳定多视角 crop、mask/depth rectification 和 bbox 回填 |
| image-blaster | 管理 world/object 目录、reference image、Hunyuan/Meshy jobs 和 React/Three viewer 的工程项目 | `worlds/<world>/output/<object>/object.json`、GLB/OBJ | 可复用其 object mesh generation convention 和 viewer 思路 | 它不是 simulator bundle 生成器 |

## 接入 Video2Mesh 的正确位置

```text
object masks / selected frames
  -> prepare-object-images
  -> export-image-blaster
  -> Hunyuan3D / Meshy / TRELLIS / NOVA3R / InstantMesh / Restore3D
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
