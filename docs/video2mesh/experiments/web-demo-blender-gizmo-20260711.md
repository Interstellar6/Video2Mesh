---
title: "Web Demo: Blender-like 视口与机器人交互"
id: video2mesh-experiments-web-demo-blender-gizmo-20260711
category: 实验目录
visibility: public
updated: 2026-07-11
summary: 记录 relumeow.top/video2mesh/web-demo 中 3DGS 视觉代理、语义 mesh 碰撞代理、Blender-like 视口球、滚轮缩放和 WASD 机器人控制的本地验证结果。
tags:
  - Web Demo
  - 3DGS
  - Collider
  - Interaction
---

# Web Demo: Blender-like 视口与机器人交互

![Video2Mesh Web Demo Blender-like gizmo](assets/07-web-demo-blender-gizmo.png "右侧 Rotate / Pan 视口球用于旋转和平移观察目标，画布滚轮缩放，WASD 控制机器人在 mesh collider 上移动")

## Demo 链接

- 本地验证入口：`http://127.0.0.1:4173/video2mesh/web-demo/?v=gizmo-local`
- 部署入口：`https://relumeow.top/video2mesh/web-demo/`
- 前端实现目录：`/Users/zhangyuxiang/Desktop/worksplace/interstellar6.github.io/static/video2mesh/web-demo/`

## 实验目标

这次更新的目标不是重新训练 3DGS，也不是修改点云和 mesh 的真实配准，而是把浏览器 demo 从“可看”推进到“可探索”。交互层需要像 Blender / SuperSplat 一样让用户快速旋转、平移和缩放视角，同时保留 Video2Mesh 的分层资产边界：

| 层 | 资产 | 职责 |
|---|---|---|
| 视觉代理 | AnySplat GraphDECO Gaussian PLY | 负责浏览器端 3DGS 渲染，不参与 raycast 和碰撞 |
| 碰撞代理 | semantic mesh PLY | 负责 collider、点击命中、地面探测和机器人移动 |
| 交互代理 | viewport camera + robot controller | 负责视角旋转/平移/缩放、WASD 机器人控制 |
| 语义 sidecar | mesh face attributes | 通过 `object_id`、`object_probability`、`source_face` 支持后续语义查询 |

## 真实资产

本次 demo 使用的不是占位模型，而是 bedroom_4 的真实输出资产：

| 项目 | 数值 / 路径 |
|---|---|
| 视觉 3DGS | `/Users/zhangyuxiang/Desktop/worksplace/AnySplat/tmp_anysplat_results/bedroom_4_anysplat_20260709_044525/gaussians.ply` |
| 视觉 splats | `1,313,391` |
| 碰撞 mesh | `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/bedroom_4_full_pipeline_valid_1280_20260708_160328/simulator_assets/mesh_semantics_local/mesh_semantic_local_debug.ply` |
| collider vertices / faces | `426,657` vertices / `142,219` faces |
| manifest version | `local-bedroom4-anysplat-semanticmesh-gizmo-20260711` |
| 视觉到碰撞配准 | `anysplat_to_video2mesh_camera_umeyama_20260711 + viewer_default`，RMSE `0.199813` scene units |

## 交互设计

### 右侧视口球

右侧新增两个球形控件：

| 控件 | 行为 |
|---|---|
| `Rotate` | 拖动时围绕当前 `controls.target` 改变相机球坐标，相当于 orbit 旋转 |
| `Pan` | 拖动时平移相机位置和 `controls.target`，相当于移动观察中心 |

这两个控件是 viewport 操作，只改变相机，不改变 3DGS PLY 或 semantic mesh PLY 的世界坐标。这样可以避免为了“看起来对齐”而破坏视觉代理和碰撞代理的真实配准合同。

### 滚轮缩放

画布滚轮现在直接控制相机到 target 的距离。向上滚动拉近，向下滚动拉远；`OrbitControls` 自带 zoom 被关闭，避免浏览器滚轮事件和自定义缩放逻辑打架。

### WASD 机器人

`W/A/S/D` 和方向键优先控制机器人在 mesh collider 上移动。为了避免和 Fly Camera 抢键盘，当前规则是：

| 状态 | WASD 行为 |
|---|---|
| Robot 开启 | WASD 控制机器人，连续按住移动，轻按也会有一次短步进 |
| Robot 关闭 + Fly Camera | WASD 控制相机飞行 |
| Robot Follow 开启 | 机器人移动后相机会跟随机器人 |

## 相机预设

保留并增强了快速视角预设：

| 按钮 | 作用 |
|---|---|
| `Front / Back / Left / Right` | 从房间中心低机位切入室内，而不是只看外部斜俯视 |
| `Top` | 从上方观察整体结构和 collider/visual overlay |
| `Robot Cam` | 以机器人为锚点查看机器人附近区域 |
| `Cycle Interior` | 在多个室内预设之间循环 |
| `View ←/→/↑/↓` | 备用按钮式 orbit 微调 |
| `Zoom In / Zoom Out` | 备用按钮式缩放 |

## 本地验证

本地通过 `python3 build_site.py` 构建聚合站点，并在 `http://127.0.0.1:4173/video2mesh/web-demo/?v=gizmo-local` 验证：

| 检查项 | 结果 |
|---|---|
| 页面加载 | 通过 |
| 真实 AnySplat PLY | `visualReady=true`，`visualCount=1,313,391` |
| 真实 semantic mesh PLY | `colliderReady=true`，`colliderFaces=142,219` |
| 右侧 `Rotate` 球 | 拖动后 `cameraPosition` 改变，`viewportGizmo` 正常回到 `idle` |
| 右侧 `Pan` 球 | 拖动后 `cameraTarget` 改变，`viewportGizmo` 正常回到 `idle` |
| 滚轮缩放 | `cameraDistance` 从 `9.8043` 变为 `8.6278` |
| WASD 机器人 | 按 `W` 后 `robotPosition` 从 `(-0.947493, -9.157697, 18.919588)` 移动到 `(-0.750465, -8.98, 19.283698)` |
| Console | 无 `error` / `warn` |

## 工程边界

本 demo 的交互升级只解决浏览器端探索和调试效率，不代表 mesh/3DGS 的真实配准误差已经消失。当前仍应区分：

| 问题 | 当前处理 |
|---|---|
| 视觉与碰撞轻微偏差 | 通过 manifest Sim(3) + viewer default offset 展示，保留 Align 控件做临时检查 |
| mesh 是否适合物理 | 当前作为 static mesh collider / ground probe baseline，后续还需要 object-level collider、convex decomposition 或 primitive fitting |
| 遮挡物体补全 | demo 不做生成式补全，仍需物体级路线如 GenRecon、Hunyuan3D、InstantMesh 或 clean-plate/inpainting |
| 语义查询 | 当前 face sidecar 已存在 `object_id` 字段，但 UI 只展示基础命中信息，后续可接 scene graph 和物理材质 |

## 下一步

1. 把 robot movement 从 ground-only baseline 升级为 mesh obstacle + capsule collision，并显示当前踩到的 object / floor label。
2. 给 collider 增加 object-level debug 面板：点击 face 后展开 object id、probability、source face、material、affordance。
3. 把 camera/collider/robot 状态导出为可复现 JSON，方便和 Unity、MuJoCo、Isaac adapter 对齐。
4. 对手机端做进一步 UI 压缩：右侧 gizmo 保留，底部调试按钮折叠成 tabs。
