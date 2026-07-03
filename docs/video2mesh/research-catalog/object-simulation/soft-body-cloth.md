---
title: Soft Body / Cloth
id: video2mesh-object-simulation-soft-body-cloth
category: 调研目录
visibility: public
summary: 窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。
tags:
  - 物体仿真
  - Research Catalog
---

# Soft Body / Cloth

![Soft body / cloth](../assets/stage-simulation.svg "窗帘、被子、枕头等软体对象需要独立仿真路线，短期先用静态代理")

## 链接

- NVIDIA Isaac Sim physics fundamentals: https://docs.isaacsim.omniverse.nvidia.com/4.5.0/physics/simulation_fundamentals.html
- Unity cloth component: https://docs.unity3d.com/6000.0/Documentation/Manual/class-Cloth.html
- Taichi cloth simulation reference: https://docs.taichi-lang.org/docs/cloth_simulation

## 简介

窗帘、床品、枕头、植物叶片等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。短期 Video2Mesh 不应该为了这些对象阻塞 P1 刚体闭环，可以先把它们标记为 soft/deformable candidate，并用 static proxy 或简化面片做保守交互。

后续如果要做可拉动窗帘、可变形被子或枕头碰撞，需要 cloth mesh、constraints、material stiffness、damping、collision thickness 等更复杂数据。

## Pipeline

| 阶段 | 作用 |
|---|---|
| soft object detection | 从 label/shape 识别 curtain、blanket、pillow 等 |
| proxy selection | 短期用 static mesh、thin box 或 support surface |
| cloth/soft mesh prep | 清理拓扑、生成边约束、质量点 |
| material estimation | 估计 stiffness、damping、mass density |
| engine simulation | Unity cloth、Isaac deformable、MPM 等 |

## 输入与输出

输入：cloth mesh、constraints、material、collision proxy。输出：软体/布料仿真配置、动态 visual mesh 或 dynamic Gaussian candidate。

## 在 Video2Mesh 中的位置

P2，先用静态代理或简化面片。formal semantic mesh 中 curtain 和 bed/blanket 类区域可以先标注为 soft candidate，为后续 Sim Anything/PhysSplat 方向留接口。

## 接入判断

- P0：不进入。
- P1：只保留 static/primitive proxy。
- P2/P3：探索 cloth/MPM/dynamic Gaussian。
