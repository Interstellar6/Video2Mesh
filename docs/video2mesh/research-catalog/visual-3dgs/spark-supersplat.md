---
title: Spark / SuperSplat
id: video2mesh-visual-3dgs-spark-supersplat
category: 调研目录
visibility: public
summary: Spark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# Spark / SuperSplat

![Spark / SuperSplat](../assets/stage-visual-3dgs.svg "Spark 和 SuperSplat 代表工业界对 3DGS visual proxy 的浏览器查看、编辑和发布约定")

## 链接

- Spark docs: https://sparkjs.dev/
- Spark 2.0 / World Labs blog: https://www.worldlabs.ai/blog/spark-2.0
- SuperSplat product: https://playcanvas.com/products/supersplat
- SuperSplat GitHub: https://github.com/playcanvas/supersplat

## 简介

Spark 是浏览器端 3DGS renderer，面向 Three.js 集成，支持把 splats 与普通 meshes 一起放在 Web 场景里。SuperSplat 是 PlayCanvas 生态的浏览器编辑/优化/发布工具，适合检查、裁剪、优化和发布 3D Gaussian Splats。

它们给 Video2Mesh 的启发不是“浏览器能自动做物理”，而是明确了工业界分层：splat 负责视觉，mesh/collider/primitive 才负责交互和物理。Web viewer 可以同时加载 visual proxy 与隐藏 collider proxy。

## Pipeline

| 工具 | Pipeline | 输出 |
|---|---|---|
| Spark | PLY/SPZ/SOG/SPLAT -> Three.js renderer -> Web visual layer | 可和 mesh/controls/physics scene 同屏 |
| SuperSplat | splat import -> cleanup/edit/optimize -> export/publish | PLY、compressed PLY、SOG、截图和发布链接 |

## 输入与输出

输入：PLY/SPZ/SOG/SPLAT 等 splat 资产。输出：浏览器可视化、编辑结果、优化后的 splat、截图、发布资产。

## 在 Video2Mesh 中的位置

Web 展示和 QA 工具，不负责 simulator bundle。当前项目可以借鉴 Spark/SuperSplat 的 viewer 约定：3DGS visual layer 独立加载，碰撞/点击/导航走 hidden GLB collider 或 primitive bodies。

## 输出/接入记录

本周完成的 visual/physics proxy demo 已验证类似分层：浏览器显示视觉层，同时用 mesh collision layer 做 raycast、地面探测和阻挡。这条路线比直接给 splat 加碰撞更稳。

## 接入判断

- P0：作为 Web visual layer/QA 参考。
- P1：用于交互 viewer，和 collider proxy、semantic sidecar 同屏。
- 风险：viewer 资产格式不能替代 simulator asset bundle；物理属性和引擎适配仍由 Video2Mesh 导出。
