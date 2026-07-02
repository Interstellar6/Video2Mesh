---
title: Web 视觉代理与碰撞代理演示
category: Simulation
summary: 一个参考 World Labs、image-blaster 和学长 TriSplat 演示结构的 Web demo：真实 PLY 视觉点云与真实 GLB collider mesh 分层交互。
tags:
  - Web Demo
  - 3DGS
  - Mesh Collider
  - World Labs
---

# Web 视觉代理与碰撞代理演示

在线演示入口：[Visual Proxy Demo](/demos/visual-physics-proxy/)

## 目标

这个 demo 验证的是架构，而不是最终画质：

```text
real PLY visual layer
  -> only for rendering

real lightweight GLB collider mesh
  -> movement
  -> raycast hit test
  -> floor probing / obstacle blocking
  -> future Unity / Web physics proxy
```

它对应我们项目里的核心判断：3DGS 负责视觉真实感，mesh/collider 负责物理、导航、点击、交互和 runtime 逻辑。

## 参考对象

| 来源 | 借鉴点 | demo 中的实现 |
|---|---|---|
| World Labs / Marble | 环境视觉资产和 collider 资产分开输出 | 视觉点云和 collider mesh 分成两个 layer |
| image-blaster | Spark splat + Rapier/mesh collider + object layer | Three.js 场景中显式区分 visual layer 与 collider layer |
| 学长 TriSplat 网页 | 全屏 canvas、HUD、FPV 小窗、agent 控制 | 保留全屏 canvas、Live FPV、移动控制、射线命中反馈 |
| Icare / SparkJS | splat 视觉资源与 walkable / characterCollision mesh 分离 | PLY 点云禁用 raycast，GLB mesh 独立承担交互 |

## 当前能力

- 视觉层：加载真实 `3dgs_iter30000_clean_filtered_xyzrgb.ply`，约 516k 个 3DGS 中心点，保留 PLY RGB，只负责显示，默认不参与 raycast。
- 碰撞层：加载真实 `true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb`，来自 3DGS 点云过滤后经 CloudCompare/Poisson 重建与减面得到的轻量 mesh。
- Actor：WASD / 方向键 / 屏幕按钮移动；Real Assets 模式下用 GLB mesh 做向下地面探测和前向阻挡探测。
- Raycast：点击画面只命中 collider mesh，并显示红色命中点和法线。
- Debug：可切换 Real Assets / Procedural fallback、Visual 3DGS、Collider Mesh、Semantic Tint。

## 当前资产

| 层 | 文件 | 体积 | 用途 |
|---|---:|---:|---|
| 视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/3dgs_iter30000_clean_filtered_xyzrgb.ply` | 7.4MB | Three.js `PLYLoader` 加载为 `THREE.Points`，禁用 raycast |
| 碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb` | 1.8MB | Three.js `GLTFLoader` 加载为 mesh collider，负责 raycast / ground probe |

页面中的资产计数会显示为 `516k / 40k` 左右，分别对应视觉点数量和碰撞 mesh 三角面数量。`Collider Mesh` 按钮只控制可视化，mesh 即使隐藏仍参与交互。

## 后续替换方向

这个 demo 的接口可以逐步替换：

| 当前 demo | 后续增强 |
|---|---|
| `THREE.Points` 真实 PLY visual layer | Spark / GraphDECO `.splat`, `.spz` 真实 3DGS renderer |
| 真实 Poisson GLB collider | object-level mesh / convex hull / V-HACD / CoACD |
| 轻量 kinematic collision | Rapier / Unity CharacterController / robot controller |
| mock semantic tint | Video2Mesh semantic/probability splats 或 semantic sidecar |

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

- 视觉层当前是 PLY 点云显示，还不是 Spark 真实 3DGS renderer。
- 没有接入 Rapier rigid body，只做了轻量 kinematic collision 与 mesh raycast。
- 真实碰撞 mesh 是场景级 collider proxy，还没有拆成桌子、椅子等 object-level collider。
- 没有加载真实 World Labs Marble `.spz` 或 `collider_mesh_url`。

但它已经验证了我们要的最小闭环：真实视觉代理和真实碰撞代理可以完全分层，交互逻辑不依赖 3DGS 本身产生 collider。
