---
title: Web 视觉代理与碰撞代理演示
category: Simulation
summary: 一个参考 World Labs、image-blaster 和学长 TriSplat 演示结构的 Web demo：Spark 真实 3DGS 视觉层与 GLB collider mesh 分层交互。
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
real Spark 3DGS visual layer (.sog / .spz / .splat)
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
| image-blaster | `SparkRenderer` / `SplatMesh` + Rapier/mesh collider + object layer | Spark 负责 3DGS 视觉，Three.js mesh 负责射线和碰撞 |
| 学长 TriSplat 网页 | `Outdoor.splat` / `outdoor4.sog` + `outdoor4.collision.glb`，以及 `3DGS.sog` + `3dgsCollider.glb` player controller | 主路径复用真实 `.splat` 视觉资产和同源 GLB collider，旧 `.sog` 资产作为兜底 |
| Icare / SparkJS | splat 视觉资源与 walkable / characterCollision mesh 分离 | Splat 禁用 raycast，GLB mesh 独立承担交互 |

## 当前能力

- 视觉层：默认用本地 vendored Spark runtime 优先加载真实 `azureovo_outdoor.splat`，约 1,200,000 个 splats；若失败再加载 `azureovo_3dgs.sog`，最后才退回 PLY debug visual。视觉层只负责显示，默认不参与 raycast。
- 碰撞层：主路径加载同源 `azureovo_outdoor_collider.glb`，作为静态 mesh collider proxy；`.sog` 兜底会加载 `azureovo_3dgs_collider.glb`；Spark 路径都失败时才退回我们自己的 PLY + Poisson GLB fallback。
- Actor：WASD / 方向键 / 屏幕按钮移动；Real Assets 模式下用 GLB mesh 做向下地面探测和前向阻挡探测。
- Raycast：点击画面只命中 collider mesh，并显示红色命中点和法线。
- Debug：可切换 Real Assets / Procedural fallback、Visual 3DGS、Collider Mesh、Semantic Tint。

## 当前资产

| 层 | 文件 | 体积 | 用途 |
|---|---:|---:|---|
| 主视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor.splat` | 37MB | Spark `SplatMesh` 加载真实 `.splat` 3DGS，禁用 raycast |
| 主碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor_collider.glb` | 1.1MB | Three.js `GLTFLoader` + `DRACOLoader` 加载 outdoor collider，负责 raycast / ground probe |
| 兜底视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs.sog` | 11MB | Spark `SplatMesh` 加载 PC-SOGS 3DGS，禁用 raycast |
| 兜底碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs_collider.glb` | 3.4MB | `.sog` 路径失败前的同源 GLB collider |
| fallback 视觉 | `docs-blog/demos/visual-physics-proxy/assets/3dgs_iter30000_clean_filtered_xyzrgb.ply` | 7.4MB | Spark 失败时加载为 `THREE.Points` debug visual |
| fallback 碰撞 | `docs-blog/demos/visual-physics-proxy/assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb` | 1.8MB | 我们自己的 CloudCompare/Poisson collider fallback |

页面中的资产计数默认显示为 `3DGS / mesh`：主路径预期为约 `1.2M / outdoor GLB triangle count`。页面会把当前 `visualFormat`、`visualUrl`、`colliderUrl` 写入 `document.documentElement.dataset.visualPhysicsState`，方便确认线上实际命中的资产。`Collider Mesh` 按钮只控制可视化，mesh 即使隐藏仍参与交互。

## 后续替换方向

这个 demo 的接口可以逐步替换：

| 当前 demo | 后续增强 |
|---|---|
| Spark `.splat` / PC-SOGS `.sog` visual layer | 接入我们自己的 GraphDECO `.ply` / `.splat` / `.spz` 导出 |
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

- 当前默认 3DGS 和 collider 资产来自学长公开网页快照，用来证明 Web 端架构；下一步要替换成 Video2Mesh 自己导出的 `.splat/.spz` 与 collider。
- 没有接入 Rapier rigid body，只做了轻量 kinematic collision 与 mesh raycast。
- 真实碰撞 mesh 是场景级 collider proxy，还没有拆成桌子、椅子等 object-level collider。
- 没有加载真实 World Labs Marble `.spz` 或 `collider_mesh_url`，但运行结构与 image-blaster / Icare 的 Spark visual + mesh proxy 边界一致。

但它已经验证了我们要的最小闭环：真实视觉代理和真实碰撞代理可以完全分层，交互逻辑不依赖 3DGS 本身产生 collider。
