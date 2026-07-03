---
title: 视觉重建与 3DGS 阶段
id: visual-3dgs
category: Research Catalog
summary: 梳理 GraphDECO 3DGS、Spark、SuperSplat 等视觉代理方案，以及它们和 mesh/collider 的边界。
tags:
  - Research Catalog
  - 3DGS
  - Spark
  - SuperSplat
---

# 视觉重建与 3DGS 阶段

3DGS 在 Video2Mesh 中应该被定位为 **visual proxy**：它负责让扫描场景看起来真实，但不直接承担碰撞、导航、刚体交互和语义查询。

## 主要项目和模型

| 项目 / 方法 | 简介 | 适合承担 | 不适合承担 |
|---|---|---|---|
| GraphDECO 3D Gaussian Splatting | 经典 3DGS 训练实现，用 COLMAP 相机和点云初始化高斯场景 | 当前 P0/P1 真实场景视觉层，生成高质量 splat/PLY | 直接输出可靠 mesh topology 或 collider |
| Spark / SparkJS | 浏览器端 3DGS/Splat 渲染 runtime，World Labs / Icare 生态中常见 | Web visual layer，加载 `.ply/.splat/.spz/.sog` 等视觉资产 | 物理碰撞和复杂交互本身 |
| SuperSplat | 3DGS 浏览器查看、编辑和导出工具 | 本地/远端检查 splat 质量、清理 floaters、截图展示 | simulator asset bundle 生成 |
| 2DGS / GOF / surface-aware GS | 让 Gaussian 更贴近表面、改善 mesh extraction 的研究路线 | P2 替换或增强训练端，提高后续 mesh 质量 | 短期 P0 工程主链路 |

## 核心边界

```text
GraphDECO 3DGS
  -> visual display
  -> rendered RGB / depth / mask evidence
  -> object visual mesh reconstruction helper

not:
  -> collider
  -> navigation mesh
  -> final simulator physics body
```

## 对 Video2Mesh 的结论

3DGS 应该继续作为视觉质量最强的场景层，同时为后续 mesh 重建提供 rendered RGB/depth/mask evidence。不要直接把 Gaussian center 当作真实表面点云去建最终 mesh，因为当前实验证明这会导致壳状伪影、漂浮片和语义串色。
