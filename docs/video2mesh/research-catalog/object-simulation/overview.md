---
title: 物体仿真阶段
id: object-simulation
category: 调研目录
summary: 按刚体、软体、VLM 物理资产生成和 dynamic Gaussian 四条线整理物体交互、PhysX-Anything 与 Sim Anything / PhysSplat 的关系。
tags:
  - Research Catalog
  - Simulation
  - PhysX-Anything
  - PhysSplat
  - SimAnything
visibility: public
---

# 物体仿真阶段

物体仿真应分为刚体、软体、VLM 物理资产生成、sim-ready world engine 和 dynamic Gaussian 几条线。它们消费的资产合同不同，不应强行合并成一个 mesh。

![物体仿真](../assets/stage-simulation.svg "刚体、软体和 dynamic Gaussian 三种物体仿真路径")

## 主要路线

| 路线 | 简介 | 适合对象 | 对 Video2Mesh 的意义 |
|---|---|---|---|
| Rigid body simulation | 刚体 + collider + mass/friction/restitution | 桌椅、杯子、柜门、盒子 | P1 物体交互闭环，最容易进入 Unity/MuJoCo/Isaac |
| Soft body / cloth | 布料、枕头、被子、植物叶片等形变对象 | pillow、blanket、curtain、plant | 需要比刚体更复杂的材质和 solver |
| [EmbodiedGen V2](../industrial-pipelines/embodiedgen-v2.md) | 生成 sim-ready object/world，带 visual/collision/inertial/affordance 合同和 URDF/MJCF/USD 导出 | 任务驱动机器人训练场景、跨仿真器资产包、Vibe Coding 编辑 | 对 Video2Mesh 是 simulator_asset_bundle 设计参考，不替代视频重建 |
| [PhysX-Anything](physx-anything.md) | 单图生成 part mesh、URDF/XML、关节和物理属性 | cabinet、laptop、faucet、eyeglass 等单物体 | P1/P2 单物体补全与 physics sidecar；不替代房间级重建 |
| [PhysSplat / Sim Anything](physsplat-sim-anything.md) | MLLM 估计物理属性，粒子/高斯动态模拟，动态 splat 渲染 | 非刚体、局部形变、动态视觉展示 | P2 研究旁线，可为物理属性估计和 dynamic Gaussian 提供启发 |
| VLM physical property inference | 用 VLM/MLLM 估计材质、质量范围、摩擦、可移动性 | 所有 object metadata | 可作为 simulator_asset_bundle 的初稿，但必须 QA |

## PhysX-Anything 的定位

PhysX-Anything 的目标是从单张物体图像生成仿真就绪资产，输出 part mesh、URDF/XML、关节结构和物理属性。它适合补 Video2Mesh 的单物体物理 sidecar 和 articulated object 资产，不适合直接吃 `bedroom_4` 整房间帧并宣称得到房间级 simulator scene。

当前 mil8 已完成官方源码部署、bedroom_4 单帧 smoke input 准备和依赖审计，但还没有跑通官方四步推理链路；详见 [PhysX-Anything](physx-anything.md)。

## Sim Anything / PhysSplat 的定位

PhysSplat 的目标不是把 3DGS 转成传统 mesh，而是把物理属性估计和动态模拟注入 semantic Gaussian/particle 表示中。它对我们后续做布料、枕头、植物等非刚体交互有启发，但短期不替代 mesh/collider 主链路。

当前建议：

- P0/P1：先做 rigid-body 资产合同，即 visual mesh + collider + physics sidecar。
- P2：对特定对象探索 dynamic Gaussian 或 PhysSplat-style 物理属性估计。
- 所有自动推理出的质量、摩擦、恢复系数都要标注来源和置信度。
