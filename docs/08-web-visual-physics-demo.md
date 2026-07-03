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
real Spark 3DGS visual layer (.ply / .sog / .spz / .splat)
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
| World Labs / Marble | 环境视觉资产和 collider 资产分开输出 | Spark 3DGS 视觉资产和 collider mesh 分成两个 layer |
| image-blaster | `SparkRenderer` / `SplatMesh` + Rapier/mesh collider + object layer | Spark 负责 3DGS 视觉，Three.js mesh 负责射线和碰撞 |
| 学长 TriSplat 网页 | `Outdoor.splat` / `outdoor4.sog` + `outdoor4.collision.glb`，以及 `3DGS.sog` + `3dgsCollider.glb` player controller | 保留真实 `.splat/.sog` 视觉资产和同源 GLB collider 作为兜底 |
| Icare / SparkJS | splat 视觉资源与 walkable / characterCollision mesh 分离 | Splat 禁用 raycast，GLB mesh 独立承担交互 |

## 当前能力

- 视觉层：默认用 Spark `SplatMesh` 加载 bedroom_4 CLI30K 真实生成的 clean GraphDECO Gaussian PLY `bedroom_4_cli30k_graphdeco_clean_iteration30000.ply`，971,305 个高斯；若失败再退回 repaired GraphDECO PLY、cleaned XYZRGB PLY、Spark `azureovo_outdoor.splat` / `azureovo_3dgs.sog` 和旧 PLY debug visual。视觉层只负责显示，默认不参与 raycast。
- 碰撞层：主路径加载同一 CLI30K run 的 `bedroom_4_cli30k_colmap_delaunay_dense_collider.glb`，来自 `mesh_recon_results/colmap_delaunay_dense/mesh.glb`，作为静态 mesh collider proxy；若失败再走旧 bedroom_4 collider、Spark 同源 GLB collider 与旧 Poisson GLB fallback。
- Actor：WASD / 方向键 / 屏幕按钮移动；Real Assets 模式下用 GLB mesh 做向下地面探测和前向阻挡探测。
- Raycast：单击画面只命中 collider mesh，并显示红色命中点、法线、face index、surface type 和 surface role；单击还会把 Orbit 相机焦点移到命中点，方便像 SuperSplat 一样快速检查局部表面。
- Debug：默认同时显示 Visual 3DGS 和 Collider Mesh overlay；可切换 Real Assets / Procedural fallback、Visual 3DGS、Collider render mode、Orbit/Fly Camera、Spark quality、Semantic Tint。
- Collider render mode：`wire` 显示线框 + 透明实体，`solid` 显示半透明 mesh，`hidden` 隐藏可视化但继续参与 ground probe、forward block 和 raycast。这个模式对应 image-blaster / Icare 中“碰撞代理是逻辑资产，不必总是可见”的做法。
- Camera：Orbit 模式用于总览和点击聚焦；Fly 模式用于进入房间内部，鼠标拖拽看向，WASD 平移，Q/E 下/上。
- Spark quality：`Balanced` 保持默认，`Crisp` 收紧 splat 半径便于检查边界，`Fast` 降低像素半径和 alpha 负担便于本地交互。

## 当前资产

| 层 | 文件 | 体积 | 用途 |
|---|---:|---:|---|
| 主视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_cli30k_graphdeco_clean_iteration30000.ply` | 230MB | CLI dense GraphDECO 30k clean Gaussian PLY，971,305 splats，带 `f_dc_*` / `opacity` / `scale_*` / `rot_*`，由 Spark `SplatMesh` 渲染，禁用 raycast |
| 主碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_cli30k_colmap_delaunay_dense_collider.glb` | 2.9MB | 同一 CLI30K run 的 `colmap_delaunay_dense/mesh.glb`，82,920 vertices / 167,082 triangles，负责 raycast / ground probe |
| GraphDECO fallback | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_supersplat.ply` | 207MB | bedroom_4 dense100/repaired GraphDECO Gaussian PLY，874,472 splats，Spark 主路径失败时兜底 |
| 点云视觉 fallback | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.ply` | 37MB | bedroom_4 dense100/repaired viewer PLY 的 cleaned XYZRGB 版本，872,374 points，移除 2,098 个长尾离群点，Spark 主路径失败时用 `THREE.Points` 显示 |
| 主视觉清理报告 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.outlier_clean_report.json` | 2KB | 记录 cleaned PLY 的 quantile bbox 参数、输入/输出 bbox 和移除数量 |
| 兜底视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor.splat` | 37MB | Spark `SplatMesh` 加载真实 `.splat` 3DGS，禁用 raycast |
| 兜底碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor_collider.glb` | 1.1MB | Three.js `GLTFLoader` + `DRACOLoader` 加载 outdoor collider，负责 raycast / ground probe |
| 二级兜底视觉 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs.sog` | 11MB | Spark `SplatMesh` 加载 PC-SOGS 3DGS，禁用 raycast |
| 二级兜底碰撞 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs_collider.glb` | 3.4MB | `.sog` 路径失败前的同源 GLB collider |
| fallback 视觉 | `docs-blog/demos/visual-physics-proxy/assets/3dgs_iter30000_clean_filtered_xyzrgb.ply` | 7.4MB | Spark 失败时加载为 `THREE.Points` debug visual |
| fallback 碰撞 | `docs-blog/demos/visual-physics-proxy/assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb` | 1.8MB | 我们自己的 CloudCompare/Poisson collider fallback |

## 线上发布形态

`relumeow.top` 的公开站仍由 GitHub Pages 构建 `docs-blog/_public/`。为了避开 GitHub 普通仓库和 Pages 对 100MB 以上单文件的限制，两个 GraphDECO 大 PLY 在线上不直接发布 raw 文件，也不放进 Pages artifact：

```text
assets/large-asset-manifest.json
https://raw.githubusercontent.com/Interstellar6/Video2Mesh/main/docs-blog/demos/visual-physics-proxy/assets/chunks/*.partNN
```

每个分片约 48MB，保存在 GitHub repo 中并由 `raw.githubusercontent.com` 提供跨域下载。前端先读取 `large-asset-manifest.json`，再按 manifest 拉取 raw 分片、合并成 `Uint8Array`，通过 `SplatMesh({ fileBytes, fileName, fileType: "ply" })` 初始化 Spark。这样线上 URL 仍展示同一套 3DGS 内容，但 Pages 发布产物不会包含 230MB / 207MB 的 raw PLY 或 437MB 分片目录。

页面中的资产计数默认显示为 `3DGS / mesh`：bedroom_4 CLI30K Spark 主路径预期为 `971.3K / 167.1K`。页面会把当前 `visualAssetId`、`visualFormat`、`visualUrl`、`visualUsesSpark`、`visualRawCount`、`visualRemovedOutliers`、`visualCleanupReportUrl`、`colliderUrl`、`sparkRendererVisible`、`visibleColliderMeshes`、`visibleColliderWires`、`colliderRenderMode`、`cameraMode`、`splatQuality`、`lastHitInfo` 写入 `document.documentElement.dataset.visualPhysicsState`，方便确认线上实际命中的资产、显示状态和射线命中的 collider face。`Collider` 按钮只控制可视化，mesh 即使隐藏仍参与交互。

当前 collider mesh 会标记这些 runtime roles：

```json
{
  "surfaceType": "scene-collider",
  "walkable": true,
  "characterCollision": true,
  "cameraCollision": true
}
```

这参考了 Icare 的角色拆分：后续可以把同一个 GLB 或拆分后的 object colliders 分成 `walkable`、`characterCollision`、`cameraCollision`、`trigger` 等集合，再接入语义 face sidecar。

本地 demo 额外放宽了 OrbitControls：相机可以绕完整球面旋转，并提供 `Reset View` 按钮按当前 3DGS/collider 包围盒自动重新构图。bedroom_4 的视觉层和碰撞层会作为同一组资产应用 SuperSplat 验证过的 Z 轴 180° 旋转、缩放和落地 offset，避免视觉层正了但 collider 错位。

## 点云清理插入点

当前 demo 主资产来自 `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/3dgs_point_cloud_clean_iteration30000.ply`，manifest 中记录原始输入 1,348,957 个高斯、清理后保留 971,305 个、移除 377,652 个。前端仍使用 per-axis 0.1% / 99.9% quantile bbox 加 2% padding 做相机和对齐用的稳健边界，避免少量远端高斯把视角拉远。项目流水线里可以用同样入口在语义投影融合和 mesh 重建前清理 plain XYZ/RGB 点云：

```bash
python -m video2mesh.cli clean-point-cloud-outliers \
  --project-root exports/<run> \
  --input exports/<run>/simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply \
  --output exports/<run>/simulator_assets/viewer_plys/scene_3dgs_point_cloud_clean.ply \
  --quantile-min 0.001 \
  --quantile-max 0.999 \
  --padding-ratio 0.02 \
  --register-as scene_3dgs_point_cloud_ply
```

如果输入是带 opacity / scale / rotation 的 GraphDECO/SuperSplat PLY，仍优先使用已有的 `clean-3dgs-floaters`，它会额外过滤低透明度、细长和孤立高斯。

## 后续替换方向

这个 demo 的接口可以逐步替换：

| 当前 demo | 后续增强 |
|---|---|
| Spark GraphDECO `.ply` visual layer | 当前线上使用 48MB 分片 + manifest；后续可转 `.spz` / `.sog` 或走 CDN/LFS 进一步减小体积 |
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

- 当前默认 bedroom_4 3DGS 和 collider 已来自 Video2Mesh 自己的 CLI dense GraphDECO 30k 本地导出；学长 `.splat/.sog` 资产只作为 Spark 路径兜底。
- 230MB / 207MB GraphDECO raw PLY 不直接进入线上发布目录；当前通过 48MB 分片在浏览器端合并加载。长期仍建议转 `.spz` / `.sog` 或外链模型文件，减少首屏下载和内存压力。
- 没有接入 Rapier rigid body，只做了轻量 kinematic collision 与 mesh raycast。
- 真实碰撞 mesh 是场景级 collider proxy，还没有拆成桌子、椅子等 object-level collider。
- 没有加载真实 World Labs Marble `.spz` 或 `collider_mesh_url`，但运行结构与 image-blaster / Icare 的 Spark visual + mesh proxy 边界一致。

但它已经验证了我们要的最小闭环：真实视觉代理和真实碰撞代理可以完全分层，交互逻辑不依赖 3DGS 本身产生 collider。
