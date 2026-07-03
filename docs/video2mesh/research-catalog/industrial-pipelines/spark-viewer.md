---
title: Spark Viewer
id: video2mesh-industrial-pipelines-spark-viewer
category: 调研目录
visibility: public
summary: Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。
tags:
  - 工业资产管线
  - Research Catalog
---

# Spark Viewer

![Spark Viewer](../assets/stage-visual-3dgs.svg "Spark viewer 代表浏览器端 splat visual layer，物理仍需独立 collider")

## 链接

- Spark docs: https://sparkjs.dev/
- Spark 2.0 blog: https://www.worldlabs.ai/blog/spark-2.0
- Three.js: https://threejs.org/
- Rapier JS: https://rapier.rs/docs/user_guides/javascript/getting_started_js

## 简介

Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。它和 image-blaster/World Labs 类工具的共同点是：视觉层可以是 splat，交互层仍然要另有 mesh/collider/physics。

这对 Video2Mesh 的 Web demo 很重要：用户看到的是高质量 splat 或 visual mesh，点击、导航、碰撞和物体选择则走隐藏 collider 或 semantic sidecar。

## Pipeline 摘要

| 阶段 | 作用 |
|---|---|
| splat asset | 载入 PLY/SPZ/SOG/SPLAT |
| Web renderer | Three.js / Spark 渲染 visual proxy |
| collider overlay | 同场景加载 hidden GLB/primitive collider |
| interaction query | raycast 命中 collider，再查 semantic sidecar |
| engine handoff | 将 visual/collider/metadata 打包给后续 adapter |

## 输入与输出

输入：splat/ply/spz/sog、相机、可选 mesh collider。输出：Web 视觉层、交互查询和 QA 截图。

## 在 Video2Mesh 中的位置

P0/P1 展示层，不承担 physics。本周 visual-physics-proxy demo 就是沿着这个方向做的最小验证。

## 接入判断

- P0：作为 viewer 参考和 visual QA。
- P1：接 collider/semantic sidecar，形成交互 demo。
- 风险：浏览器 viewer 很容易掩盖物理资产缺失，必须显示/检查 collider 和 metadata。
