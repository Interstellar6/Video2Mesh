---
title: Background Clean Plate
id: video2mesh-pointcloud-completion-background-clean-plate
category: 调研目录
visibility: public
summary: clean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Background Clean Plate

![Background clean plate](../assets/stage-completion.svg "Clean plate 把前景物体移除后暴露的背景补齐，是 World Labs / image-blaster 类工业路线的关键思想")

## 链接

- World Labs: https://www.worldlabs.ai/
- Marble API docs: https://docs.worldlabs.ai/
- image-blaster world generation reference: `image-blaster/scripts/generate-world.mjs`

## 简介

Clean plate 是把前景物体移除后，补齐被遮挡的地板、墙面、柜体或背景。World Labs / Marble 与 image-blaster 的工业路线都体现了这个思想：背景世界和前景物体分开处理，背景可以生成 static world/splat/collider，物体再单独生成或回填。

对 Video2Mesh 来说，clean plate 和 object mesh completion 必须分开。补一个完整椅子 mesh 不等于恢复椅子后面的地板；修复背景图也不等于生成可碰撞物体。

## Pipeline

| 阶段 | 作用 |
|---|---|
| foreground masks | 识别要移除或单独处理的物体 |
| scene description | 形成去掉 foreground 后的 clean background prompt |
| background inpainting/generation | 修复图像、3DGS 或 static world |
| geometry consistency | 与原 COLMAP/mesh 坐标对齐 |
| collider update | 补地面/墙体等 static collider 缺口 |

## 输入与输出

输入：场景描述、移除物体 masks、背景参考图、相机和深度。输出：修复背景图、static world assets、补全地面/墙体 mesh 或 clean plate provenance。

## 在 Video2Mesh 中的位置

P1 背景补全，和 object mesh completion 分开。短期可以先从被床/柜遮挡的地面与墙面区域做实验，不直接依赖生成整套 world。

## 接入判断

- P0：不进入，P0 先基于真实扫描。
- P1：用于物体移除后的背景/地面修复。
- 风险：多视角一致性难，生成内容必须标注为 synthetic。
