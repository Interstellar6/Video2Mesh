---
title: Primitive Fitting
id: video2mesh-collider-physics-proxy-primitive-fitting
category: 调研目录
visibility: public
summary: 对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Primitive Fitting

![Primitive fitting](../assets/stage-collider.svg "Primitive fitting 用 box、plane、sphere、capsule、cylinder 等形体给物体生成稳定交互代理")

## 链接

- Unity collider types: https://docs.unity3d.com/6000.0/Documentation/Manual/collider-types-introduction.html
- Rapier colliders: https://rapier.rs/docs/user_guides/javascript/colliders
- Open3D bounding boxes: https://www.open3d.org/docs/latest/python_api/open3d.geometry.OrientedBoundingBox.html

## 简介

Primitive fitting 是把床、桌、柜、墙、门、地面等对象拟合成 box、plane、sphere、capsule、cylinder 或少量组合体。它牺牲外观细节，但换来物理稳定、求解快、体量小、易编辑。

这条路线尤其适合 Video2Mesh 的 P1 object interaction：很多室内物体不需要每个凹凸都参与碰撞。床可以用 box + support surface，桌子可以用 tabletop box + leg cylinders，墙面/地面可以用 planes 或 thin boxes，小物体可先用 bbox/convex hull。

## Pipeline

| 阶段 | 作用 |
|---|---|
| semantic object split | 从 face sidecar 或 point mask 得到物体局部几何 |
| bbox / plane estimation | 估计 AABB/OBB、support plane、principal axes |
| primitive selection | 根据类别和形状选择 box/cylinder/sphere/capsule/plane |
| fit and validate | 对齐尺度、支撑面、交互范围 |
| export sidecar | 写入 collider type、params、pose、material |

## 输入与输出

输入：语义点云、object mesh split、bbox、物体类别和支撑关系。输出：primitive collider、局部 pose、物理参数初稿。

## 在 Video2Mesh 中的位置

P1 object collider，适合刚体交互。正式 semantic mesh 已经可以拆出 bed、window、floor、wall、door、nightstand、curtain、lamp 等对象，下一步就是对 bed/nightstand/floor/wall 先做 primitive fitting，再把小物体留给 convex decomposition 或 object mesh completion。

## 接入判断

- P0：不阻塞 P0，但 floor/wall primitive 可以作为快速 fallback。
- P1：进入 object interaction 主线。
- 风险：自动类别判断可能错，需要可视化审核和人工纠错入口。
