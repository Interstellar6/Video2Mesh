---
title: Web 视觉代理与碰撞代理演示
category: Simulation
summary: 一个参考 World Labs、image-blaster 和学长 TriSplat 演示结构的 Web demo：视觉层近似 3DGS，碰撞层使用独立 mesh proxy。
tags:
  - Web Demo
  - 3DGS
  - Mesh Collider
  - World Labs
---

# Web 视觉代理与碰撞代理演示

在线演示入口：[Visual Proxy Demo](/demos/visual-physics-proxy/)

## 目标

这个 demo 验证的是架构，而不是画质：

```text
splat-like visual layer
  -> only for rendering

lightweight mesh collider layer
  -> movement
  -> raycast hit test
  -> floor / obstacle blocking
  -> future Unity / Web physics proxy
```

它对应我们项目里的核心判断：3DGS 负责视觉真实感，mesh/collider 负责物理、导航、点击、交互和 runtime 逻辑。

## 参考对象

| 来源 | 借鉴点 | demo 中的实现 |
|---|---|---|
| World Labs / Marble | 环境视觉资产和 collider 资产分开输出 | 视觉点云和 collider mesh 分成两个 layer |
| image-blaster | Spark splat + Rapier/mesh collider + object layer | Three.js 场景中显式区分 visual layer 与 collider layer |
| 学长 TriSplat 网页 | 全屏 canvas、HUD、FPV 小窗、agent 控制 | 保留全屏 canvas、Live FPV、移动控制、射线命中反馈 |

## 当前能力

- 视觉层：用 splat-like `THREE.Points` 近似 3DGS 高斯点云，默认不参与 raycast。
- 碰撞层：用 floor shape 和 box collider proxy 表示地面、墙、桌、椅、柜子、沙发。
- Actor：WASD / 方向键 / 屏幕按钮移动，只根据 collider proxy 阻挡。
- Raycast：点击画面只命中 collider mesh，并显示红色命中点和法线。
- Debug：可切换显示 Visual 3DGS、Collider Mesh、Semantic Tint。

## 下一步替换真实资产

这个 demo 的接口可以逐步替换：

| 当前 demo | 后续真实数据 |
|---|---|
| `THREE.Points` splat-like visual layer | GraphDECO / Spark `.ply`, `.splat`, `.spz` |
| 手写 floor shape | COLMAP dense fused PLY -> Poisson -> decimated mesh |
| 手写 box colliders | object mesh / convex hull / V-HACD / CoACD |
| 手写 semantic tint | Video2Mesh semantic/probability splats |
| 简单 kinematic actor | Rapier / Unity CharacterController / robot controller |

## 和 Video2Mesh 的接入位置

```text
exports/<run>/
  semantic_supersplat.ply          # visual / semantic layer
  simulator_assets/
    background/collider_mesh.glb   # static collider proxy
    objects/*/visual_mesh.glb      # object visual mesh
    objects/*/collider.glb         # object collider proxy
    simulator_asset_bundle.json    # pose / scale / semantic / physics sidecar
```

最终 Web viewer 可以从 `simulator_asset_bundle.json` 加载每个资产：

- visual assets 放在可见层。
- collider assets 放进 physics/raycast 层。
- semantic sidecar 决定 hover label、可抓取性、affordance、材质参数。

## 当前限制

- 还不是 Spark 真实 3DGS renderer。
- 没有接入 Rapier rigid body，只做了轻量 kinematic collision。
- 碰撞 mesh 是演示用低模代理，不来自真实点云重建。
- 没有加载真实 World Labs Marble `.spz` 或 `collider_mesh_url`。

但它已经验证了我们要的最小闭环：视觉代理和碰撞代理可以完全分层，交互逻辑不依赖 3DGS 本身产生 collider。
