---
title: Visual / Physics Proxy Demo
id: video2mesh-experiments-visual-physics-proxy-demo
category: 实验目录
visibility: public
summary: 本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。
tags:
  - 本项目实验
---

# Visual / Physics Proxy Demo

![视觉代理 3DGS + 碰撞代理 mesh Demo](assets/04-visual-physics-proxy-demo.png "Web demo 验证了 3DGS visual layer 与 mesh collision layer 可以分离")

## Demo 链接

- Local demo: http://127.0.0.1:4173/demos/visual-physics-proxy/
- 相关调研：Icare / 学长文档路线、Spark Viewer、Static Mesh Collider

## 实验简介

这是根据视觉代理、碰撞代理、物体语义等分层思想实现的 Web demo。核心不是“做一个漂亮页面”，而是验证架构：3DGS/Splat/visual mesh 只负责显示，隐藏 mesh collider 或 primitive proxy 负责 raycast、地面探测、移动阻挡和交互命中。

这个 demo 对导师汇报很有价值，因为它把调研结论落实成了一个可操作的最小系统：工业界的 visual proxy + collider proxy 思路在 Video2Mesh 中是可实现的。

## Pipeline

| 阶段 | 作用 |
|---|---|
| visual layer | 加载 3DGS / visual scene asset |
| collider layer | 加载 hidden GLB mesh 或 primitive collider |
| semantic layer | 命中 collider 后查询 object/label |
| interaction | raycast、ground probe、movement blocking |
| UI QA | 展示 visual/collider 分层开关和结果 |

## 输入与输出

输入：3DGS visual layer 和 mesh collider。输出：浏览器交互 demo。

## 在 Video2Mesh 中的位置

证明交互逻辑不需要依赖 3DGS 自身产生 collider。

## 输出结果摘录

图四显示 demo 已能表达分层代理思想：用户看到视觉场景，但实际交互可绑定到碰撞代理。下一步应把 formal semantic mesh 的 face sidecar 接进去，让点击 collider 后能返回 object id、label、material 和可交互属性。

## 2026-07-11 更新

本周对 demo 的定位进一步明确为三个代理/层次：

| 层 | 职责 |
|---|---|
| 视觉代理 | 负责 3DGS、splat 或 visual mesh 的前端展示 |
| 碰撞代理 | 负责 mesh collider / primitive proxy、raycast、ground probe 和 movement blocking |
| scene graph / semantic sidecar | 负责 object id、label、material、关系、affordance，以及点云/mesh face 的语义索引 |

这个边界避免把 3DGS 当作 collider，也避免把语义强行塞进会被简化或替换的 mesh。后续 demo 应优先接真实 `simulator_asset_bundle.json`、semantic splats / mesh face sidecar 和 object-level GLB，而不是只展示单一模型。

## 接入判断

- P0：作为架构验证，不阻塞重建主线。
- P1：继续接 semantic sidecar、object split 和 physics metadata。
- 风险：demo 里的资产合同要和真实 export schema 对齐，避免只在演示数据里成立。
