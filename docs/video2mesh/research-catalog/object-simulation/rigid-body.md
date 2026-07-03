---
title: Rigid Body Interaction
id: video2mesh-object-simulation-rigid-body
category: 调研目录
visibility: public
summary: 刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。
tags:
  - 物体仿真
  - Research Catalog
---

# Rigid Body Interaction

![Rigid body interaction](../assets/stage-simulation.svg "刚体交互是 Video2Mesh 物体交互的第一步：visual mesh、collider 和 physics metadata 必须分离")

## 链接

- Rapier rigid bodies: https://rapier.rs/docs/user_guides/javascript/rigid_bodies/
- Unity Rigidbody manual: https://docs.unity3d.com/6000.0/Documentation/Manual/RigidbodiesOverview.html
- MuJoCo modeling: https://mujoco.readthedocs.io/en/stable/modeling.html

## 简介

刚体是物体交互第一步，要求 visual mesh、collider、mass、friction、restitution 和 body type 分离。对于室内扫描场景，很多物体先不需要复杂软体仿真：床头柜、灯、盒子、杯子、椅子、门等都可以先用 rigid body 或 static body 建交互闭环。

刚体交互的关键不是 mesh 好不好看，而是 collider 是否保守、重心是否合理、支撑关系是否正确、物理参数是否稳定。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object split | 从 semantic mesh 拆出物体候选 |
| collider selection | primitive / convex hull / convex decomposition |
| physics metadata | 估计 body_type、mass、friction、restitution |
| engine binding | Rapier/Unity/MuJoCo/Isaac adapter |
| QA | 推动、掉落、支撑、穿透、稳定性测试 |

## 输入与输出

输入：object mesh、collider、physics metadata、scene support relations。输出：可移动或可碰撞物体、rigid body config、engine adapter。

## 在 Video2Mesh 中的位置

P1 首选。当前 formal semantic mesh 已经能给出 object split，下一步可以从 bed/nightstand/lamp 这类对象开始：bed 大概率 static/support，nightstand 可 static 或 dynamic，lamp 可 dynamic/fragile。

## 接入判断

- P0：不阻塞，但 static collider 是刚体交互基础。
- P1：进入 object interaction 主线。
- 风险：物理参数不能只靠类别猜测，需要可视化 QA 和默认值表。
