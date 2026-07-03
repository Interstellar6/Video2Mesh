---
title: 工业资产管线阶段
id: industrial-pipelines
category: Research Catalog
summary: 按 World Labs / Icare、image-blaster、Spark viewer 等工业方案整理 visual layer、collider 和 simulator asset bundle 的边界。
tags:
  - Research Catalog
  - World Labs
  - image-blaster
  - Spark
---

# 工业资产管线阶段

工业界给出的最重要信号是：真实可交互 3D 场景通常不是一个单文件 mesh，而是由视觉资产、碰撞资产、语义/交互 metadata 和 runtime viewer 组成。

## 主要项目和案例

| 项目 / 案例 | 简介 | 可借鉴点 | 边界 |
|---|---|---|---|
| World Labs / Marble | 面向 static world/background 的生成和资产输出，通常包含 splat/SPZ、pano、collider mesh 等多层资产 | clean plate / world generation；视觉资产和 collider 分开交付 | 不直接负责 Video2Mesh 的物体级仿真 asset bundle |
| Icare / World Labs game | 真实浏览器 3D 游戏案例，使用 Spark/Splat 类视觉层和独立碰撞/交互资产 | 证明 visual proxy + collision proxy 是产业级可落地架构 | 不是从任意扫描视频自动得到所有物理属性 |
| image-blaster | 管理 world/object 目录、reference image、object mesh jobs、React/Three/Rapier viewer | object mesh generation convention、GLB viewer、Rapier 交互分层 | 不生成 MuJoCo/Isaac/Unity adapter，也不拥有 simulator_asset_bundle |
| Spark / SuperSplat runtime | 浏览器端 splat 渲染和查看工具 | Web 视觉展示与调试 | 不能替代 collider / physics solver |

## 对 Video2Mesh 的分层启发

```text
visual layer:
  3DGS / SPZ / SOG / Splat

collision layer:
  GLB collider / primitive proxy / convex parts

semantic and physics sidecar:
  object_id / label / affordance / material / mass / friction

runtime adapter:
  Web / Unity / MuJoCo / Isaac
```

## 与 image-blaster 的正确关系

image-blaster 可以成为 Video2Mesh 的 object mesh helper：

```text
Video2Mesh selected object frames
  -> image-blaster world/object folder
  -> Hunyuan3D / Meshy mesh job
  -> generated object-local mesh
  -> Video2Mesh import and fit
  -> simulator asset bundle
```

但最终 simulator bundle、坐标对齐、物理属性、引擎 adapter 仍应由 Video2Mesh 负责。
