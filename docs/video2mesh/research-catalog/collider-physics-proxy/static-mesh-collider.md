---
title: Static Mesh Collider
id: video2mesh-collider-physics-proxy-static-mesh-collider
category: 调研目录
visibility: public
summary: 场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Static Mesh Collider

![Static mesh collider](../assets/stage-collider.svg "Static mesh collider 用简化三角网格承担房间地面、墙面和大型静态结构的碰撞")

## 链接

- Unity Mesh Collider manual: https://docs.unity3d.com/6000.2/Documentation/Manual/mesh-colliders-introduction.html
- Rapier colliders: https://rapier.rs/docs/user_guides/javascript/colliders
- OpenUSD rigid body physics proposal: https://openusd.org/release/wp_rigid_body_physics.html

## 简介

场景级 static mesh collider 用一个简化三角网格承担地面、墙体、点击、导航边界和粗碰撞。它的目标不是视觉精美，而是稳定、轻量、尺度正确、能被 Web/Unity/MuJoCo/Isaac 等运行时消费。

Static mesh collider 适合房间壳体、地面、墙面、大型固定家具等“不需要被刚体求解器推动”的对象。动态物体不应直接使用复杂 concave mesh，而应走 primitive、convex hull 或 convex decomposition。

## Pipeline

| 阶段 | 作用 |
|---|---|
| scene mesh source | COLMAP Delaunay / cleaned Poisson / simplified mesh |
| cleanup | 移除飞面、孤立分量、过薄结构和远端噪声 |
| simplification | decimate 到 Web/engine 可消费体量 |
| export | GLB/OBJ/PLY + coordinate metadata |
| runtime binding | 作为 hidden collider，visual layer 仍由 3DGS 或 visual mesh 显示 |

## 输入与输出

输入：COLMAP Delaunay、Poisson 或其他场景级 mesh。输出：简化后的 GLB collider、face/material sidecar、scale/axis metadata。

## 在 Video2Mesh 中的位置

P0 必需，优先稳定和轻量。本周 formal semantic mesh 结果里，COLMAP Delaunay local transfer 的 82,920 vertices / 167,082 faces 规模适中，语义覆盖 84.98%，比 GS2Mesh 和 Open3D Poisson 更适合作为 static collider 基线。

## 接入判断

- P0：必须进入，先服务地面探测、点击和移动阻挡。
- P1：叠加 semantic face sidecar 和 object split。
- 风险：不要把 visual mesh 的破碎表面直接作为物理真实几何，需要清理和简化。
