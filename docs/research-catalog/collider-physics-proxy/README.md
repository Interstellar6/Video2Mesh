---
title: Collider 与物理代理阶段
id: collider-physics-proxy
category: Research Catalog
summary: 整理 static collider、primitive proxy、convex decomposition、Rapier/Unity 交互代理在 Video2Mesh 中的职责。
tags:
  - Research Catalog
  - Collider
  - Physics
  - Unity
---

# Collider 与物理代理阶段

碰撞代理的目标不是“看起来最真实”，而是“交互稳定、体量可控、运行时可消费”。这也是学长文档、World Labs / Icare、image-blaster viewer 给出的共同工程信号。

## 主要方法和项目

| 方法 / 项目 | 简介 | 适合对象 | Video2Mesh 用法 |
|---|---|---|---|
| Static triangle mesh collider | 简化后的 GLB/mesh 作为静态环境碰撞 | 地面、墙体、大型静态家具、房间壳体 | COLMAP Delaunay / Poisson mesh -> simplified GLB |
| Primitive fitting | box、capsule、sphere、cylinder 等基本形体 | 桌、柜、床、椅腿、花盆等 | 物体交互 P1 的首选 collider |
| Convex hull / convex decomposition | 用凸包或多个 convex parts 近似复杂物体 | 可移动刚体、可抓取物体 | 后续可接 CoACD / V-HACD |
| Rapier | Web 端物理引擎 | 浏览器 demo 和 image-blaster-style viewer | 可加载 GLB collider 或 primitive rigid body |
| Unity MeshCollider / Rigidbody | Unity 运行时物理组件 | 项目引擎适配 | static 用 concave mesh，dynamic 优先 convex/compound |
| MuJoCo / Isaac | 仿真环境 | 机器人和物理仿真 | 需要质量、摩擦、joint、body type 等 metadata |

## 推荐策略

| 资产 | 推荐 collider |
|---|---|
| 房间地面/墙体 | static simplified mesh |
| 床/柜/桌等大型静态家具 | box / convex hull / compound primitive |
| 可移动小物体 | primitive / convex decomposition |
| 布料、枕头、植物叶片 | visual mesh + soft/dynamic side route，不直接用复杂 concave collider |

## 和视觉层的关系

```text
3DGS visual layer
  -> visible only

collider mesh / primitive proxy
  -> raycast
  -> ground probe
  -> movement blocking
  -> physics body
```

本项目 Web demo 已验证：3DGS 视觉层可以完全不参与 raycast，隐藏的 COLMAP Delaunay GLB collider 仍能承担点击、地面探测和移动阻挡。
