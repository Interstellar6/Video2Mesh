---
title: Rapier / Unity Physics
id: video2mesh-collider-physics-proxy-rapier-unity
category: 调研目录
visibility: public
summary: Rapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Rapier / Unity Physics

![Rapier / Unity Physics](../assets/stage-collider.svg "Rapier 用于 Web demo，Unity Physics/PhysX 用于引擎侧交互验证")

## 链接

- Rapier JavaScript docs: https://rapier.rs/docs/user_guides/javascript/rigid_bodies/
- React Three Rapier: https://github.com/pmndrs/react-three-rapier
- Unity Mesh Collider manual: https://docs.unity3d.com/6000.2/Documentation/Manual/mesh-colliders-introduction.html
- Unity Rigidbody collider rules: https://docs.unity3d.com/6000.0/Documentation/Manual/rigidbody-configure-colliders.html

## 简介

Rapier 适合 Web demo 和 Three.js 场景中的实时碰撞；Unity Physics/PhysX 适合后续引擎集成和更完整的游戏交互。二者都强调同一个工程事实：rigid body 和 collider 是分离概念，动态刚体通常不能直接使用复杂 concave mesh。

因此 Video2Mesh 的导出不能只给一个漂亮 GLB，而要同时给 visual mesh、collider、body type、mass、friction、restitution、pose、scale 和 material hints。

## Pipeline

| 阶段 | Web / Rapier | Unity |
|---|---|---|
| visual layer | Three.js / Spark / GLB | MeshRenderer / Splat renderer |
| collider layer | trimesh/static、cuboid、ball、capsule、convex hull | MeshCollider static、Box/Capsule/Sphere、Convex MeshCollider |
| physics metadata | rigid body type、friction、restitution | Rigidbody、PhysicMaterial、layer |
| QA | raycast、ground probe、movement blocking | play mode collision、CharacterController、rigidbody stability |

## 输入与输出

输入：collider mesh/primitive、body type、material、object pose。输出：runtime collision、raycast result、movement blocking、rigid body response。

## 在 Video2Mesh 中的位置

P1 runtime 集成验证。本周 visual/physics proxy demo 已经验证浏览器里可以让 visual layer 和 collider layer 分开：可见的是 3DGS/visual mesh，交互查询和碰撞走隐藏 mesh 或 primitive。

## 接入判断

- P0：Web demo 可以先用 static collider + raycast 验证。
- P1：进入 object interaction 和 Unity adapter。
- 风险：同一个 mesh 在 Web/Unity/MuJoCo/Isaac 的坐标轴和 collider 限制不同，需要 adapter 层显式转换。
