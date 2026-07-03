---
title: Convex Decomposition
id: video2mesh-collider-physics-proxy-convex-decomposition
category: 调研目录
visibility: public
summary: V-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Convex Decomposition

![Convex decomposition](../assets/stage-collider.svg "Convex decomposition 把复杂物体拆成多个凸体，适合动态刚体和可抓取物体")

## 链接

- V-HACD GitHub: https://github.com/kmammou/v-hacd
- CoACD project: https://colin97.github.io/CoACD/
- CoACD GitHub: https://github.com/SarahWeiii/CoACD
- CoACD Rust wrapper: https://github.com/Jondolf/CoACD-rs

## 摘要要点

Convex decomposition 把复杂 mesh 拆成多个凸体，让物理引擎能稳定处理动态刚体。V-HACD 是常见工程方案；CoACD 更强调 collision-aware concavity，希望用更少凸部件保留碰撞条件，适合游戏和交互应用。

对 Video2Mesh 来说，它不是场景级 static collider 的替代品，而是 object-level dynamic collider 的候选。床、柜子这种大型静态物体未必需要拆很多凸体；可移动椅子、盒子、杯子、小摆件更适合用 convex compound。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object mesh cleanup | 先去飞面、封孔、减面，避免分解结果过碎 |
| convex decomposition | 用 V-HACD/CoACD 拆为多个 convex hull |
| hull filtering | 去掉太小或重叠严重的 hull |
| physics binding | 写入 compound collider、mass、friction、restitution |
| runtime QA | 检查穿透、稳定性和帧率 |

## 输入与输出

输入：object mesh、object bbox、类别和是否可移动。输出：convex hull compound、collider sidecar、运行时可用的动态刚体代理。

## 在 Video2Mesh 中的位置

P1 动态物体 collider。它可以接在 object split 或 Hunyuan3D/image-blaster object mesh 回填之后，作为 visual mesh 的物理替代层。

## 接入判断

- P0：不进入，P0 static collider 不需要复杂分解。
- P1：用于可移动物体和 object completion 输出。
- 风险：输入 mesh 质量差会导致 hull 过多或形状异常，需要限制 hull 数量和最小体积。
