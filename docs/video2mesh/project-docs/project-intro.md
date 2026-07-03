---
title: Video2Mesh 项目简介
id: video2mesh-project-intro
category: 项目文档
visibility: public
summary: 说明 Video2Mesh 的目标、资产分层、当前边界和对外部方案的承接关系。
tags:
  - Video2Mesh
  - 3DGS
  - Simulator
---

# Video2Mesh 项目简介

Video2Mesh 关注的是真实扫描视频到可交互 3D 资产的工程闭环。它不把 3DGS、mesh、语义、物理都压进一个文件，而是拆成多个互相对齐的层。

## 目标产物

```text
scan video
  -> camera / point cloud
  -> 3DGS visual proxy
  -> scene mesh / collider proxy
  -> object visual mesh / completion
  -> semantic sidecar / scene graph
  -> physics metadata
  -> Web / Unity / MuJoCo / Isaac adapters
```

## 分层原则

| 层 | 代表产物 | 主要职责 |
|---|---|---|
| Visual | GraphDECO 3DGS、Spark/SuperSplat 可视化资产 | 真实感显示 |
| Geometry | COLMAP dense mesh、Poisson mesh、object mesh | 重建、定位、对齐 |
| Collision | static collider、primitive/convex proxy | 点击、移动、碰撞、导航 |
| Semantic | object id、face label、probability splat、scene graph | 查询与交互逻辑 |
| Physics | mass、friction、restitution、body type | 仿真引擎消费 |
| Adapter | simulator asset bundle、Unity/MuJoCo/Isaac 输出 | runtime 集成 |

## 边界

World Labs / Marble、image-blaster、Hunyuan3D、Meshy、SuGaR、GS2Mesh 等都可以成为某一阶段的后端或参考，但 Video2Mesh 自己要承接统一坐标、语义、物理属性、资产索引和引擎适配。
