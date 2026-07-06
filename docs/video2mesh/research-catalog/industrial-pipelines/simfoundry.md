---
title: SimFoundry 调研与 Video2Mesh 吸收方案
id: video2mesh-industrial-pipelines-simfoundry
category: 调研目录
visibility: public
summary: 调研 NVIDIA SimFoundry 的 real-to-sim-to-real 系统，并收敛到 Video2Mesh 如何吸收其 sim-ready asset contract，让扫描结果能稳定进入 MuJoCo / Isaac / Unity 等仿真模拟器。
tags:
  - 工业资产管线
  - Research Catalog
  - Real2Sim
  - Simulation
  - Simulator Asset
---

# SimFoundry 调研与 Video2Mesh 吸收方案

## 资料入口

- Project page: https://research.nvidia.com/labs/gear/simfoundry/
- Paper: https://arxiv.org/abs/2606.28276
- Title: SimFoundry: Modular and Automated Scene Generation for Policy Learning and Evaluation
- Version checked: arXiv v1, submitted 2026-06-26
- Related baseline mentioned by the paper: PolaRiS, SAM3D

## 结论先行

SimFoundry 不是一个单点 3D 重建模型，而是一套 real-to-sim-to-real 系统。它从一段真实视频出发，生成可交互的 sim-ready digital twin，并继续派生 object / scene / task cousins，用于机器人策略评估和训练。

对 Video2Mesh 来说，最有价值的不是照搬它的完整机器人训练闭环，而是吸收它对仿真资产的定义：

```text
visual asset
  + collider asset
  + physics sidecar
  + semantic / affordance metadata
  + stable pose
  + simulator adapter
  + preflight QA report
```

我们的目标如果收窄成“能放进 MuJoCo / Isaac / Unity 等仿真模拟器里稳定运行”，可以吸收 SimFoundry 约 70% 的系统设计思想，约 50% 的 P0/P1 工程功能；但不需要也不应该复刻它的闭源 VLM、机器人策略训练、真实硬件评测和完整 cousin 数据工厂。

## SimFoundry 做了什么

官网给出的定位是：单段真实世界视频自动转成可交互仿真环境，用于大规模策略训练和评估。论文把系统分成三段：Extraction、Generation、Augmentation。

| 阶段 | 输入 | 主要动作 | 典型输出 |
|---|---|---|---|
| Extraction | raw RGB video | 选代表帧，估计 depth，生成 scene point cloud，检测地面和前景物体，迭代分割、裁剪、移除并 inpaint | representative RGB-D、ground plane、object masks、per-object RGB-D crops |
| Generation | object crops、depth、point cloud | 2D-to-3D 生成物体 mesh，估计 6D pose/scale，处理 articulated objects，生成 collider 和物理属性，在物理引擎里稳定化 | object visual mesh、pose、scale、joint、collider、mass/friction、stable sim scene |
| Augmentation | reconstructed twin | 生成 affordance-preserving digital cousins | object cousins、scene cousins、task cousins |

它的核心 pipeline 可以抽象成：

```text
single video
  -> representative RGB-D / scene point cloud
  -> per-object masks and crops
  -> generated textured object meshes
  -> pose / scale / articulation / physics annotation
  -> collision geometry
  -> physics settling / depenetration
  -> simulator-ready scene
  -> object / scene / task cousins
  -> policy evaluation and policy training
```

这里最关键的变化是：系统不以“重建一个好看的 3D 场景”为终点，而以“这个场景能不能在仿真器里作为可执行任务环境”为终点。

## 系统组件开源程度

SimFoundry 目前没有看到完整官方系统代码 release。论文强调模块化，很多底层模块有公开替代或官方开源版本，但总装胶水、prompt/config、场景编辑器、机器人评测脚本和部分闭源模型调用并没有完整公开。

| 组件 | SimFoundry 使用/描述 | 开源程度 | Video2Mesh 可替代方案 |
|---|---|---|---|
| 总控 pipeline | extraction / generation / augmentation orchestration | 未见完整开源 | Video2Mesh CLI 自己承接 |
| VLM / image editing | Gemini-Pro-3、Gemini image 类模型 | 闭源 API | 可先用手工规则、轻量 VLM、后续再接 API |
| Depth | DepthAnything3 / FoundationStereo | 有公开路线，但版本和权重需逐项确认 | COLMAP / MASt3R / DUSt3R / VGGT / DepthAnything |
| Segmentation | SAM3、SAM2、video segmentation | 多数可替代 | Grounded-SAM / SAM2 / 现有 mask tracking |
| 2D-to-3D mesh | Hunyuan2.1、TRELLIS.2 | 有公开实现或服务化接口 | image-blaster / Hunyuan3D / Meshy / TRELLIS |
| Pose refinement | FoundationPose | NVIDIA 有公开项目线 | P1 可接，P0 先用 bbox / point cloud alignment |
| Articulation | VLM + mesh part segmentation + URDF generation | 论文级复杂，难完整复刻 | P2 再做 articulated assets |
| Collider | CoACD | 可用 | P1 引入 CoACD / V-HACD / convex hull |
| Physics settling | PyBullet step until stable | 可用 | 新增 simulator preflight / settle pass |
| Simulator export | IsaacLab 等 | IsaacLab 可用，但生态重 | Video2Mesh 继续导出 MuJoCo / Unity / Isaac adapter |
| Policy eval/training | GR00T、DreamZero、π 系列、真实机器人 | 难复刻 | 不纳入当前目标 |

粗略判断：底层零件有 60-75% 能找到公开替代，但决定论文级效果的总装、闭源模型、真实机器人环境和细节调参没有开源。Video2Mesh 不应等待官方代码，而应吸收其合同和阶段设计。

## SimFoundry 的资产结构启发

论文和官网都展示了混合场景结构：背景可用 3D Gaussian Splat，前景物体用 textured object meshes，再配 collision geometry 和物理属性。这一点和 Video2Mesh 当前架构高度一致。

| 资产层 | SimFoundry 思路 | Video2Mesh 当前状态 | 应吸收的动作 |
|---|---|---|---|
| visual layer | background 3DGS + foreground textured meshes | 已有 GraphDECO 3DGS、object mesh/completion 方向 | 保持视觉层和物理层分离 |
| static collider | 背景可用 mesh reconstruction 或独立 collider | 已有 COLMAP dense / Delaunay collider 路线 | 固化为 P0 static scene collider |
| object collider | CoACD 生成 collision geometry | 现有 primitive / bbox / convex hull 方向 | P1 接 CoACD 或 convex decomposition |
| physics metadata | VLM 估计 mass、friction、joint damping | 已有 physics sidecar 思路 | 增加 provenance、confidence、QA status |
| stable pose | 在 PyBullet 中 settle 并缓存最终 pose | 目前更多是导出，不是仿真稳定化 | 新增 simulator preflight 和 settle report |
| simulator adapter | 导出给 IsaacLab 等 | 已有 MuJoCo / Unity / Isaac adapter 方向 | 统一 adapter 消费 collider + physics，不直接依赖 visual mesh |

关键原则：

- 3DGS 负责视觉真实感，不负责碰撞。
- visual mesh 可以很精细，dynamic collider 必须简化。
- physics sidecar 必须记录来源，不要把 VLM 猜测当真值。
- adapter 只应该消费稳定、尺度正确、坐标对齐的资产。

## 对 Video2Mesh 的目标收敛

当前用户目标是“能放到仿真模拟器里面仿真就可以”。因此我们不需要完整复刻 SimFoundry 的 policy learning，而应收敛到一个 simulator-ready bundle：

```text
Video2Mesh reconstruction
  -> simulator-ready asset bundle
  -> simulator preflight
  -> MuJoCo / Unity / Isaac adapter
  -> simulator smoke test
```

这条目标里，成功标准不是“渲染漂亮”，而是：

1. 场景能被仿真器加载。
2. static collider 存在并和视觉层同坐标。
3. movable objects 有 rigid body / collider / mass。
4. 物体不会大面积穿地、互相爆开或尺度离谱。
5. visual mesh 和 collider mesh 明确分离。
6. `sim_preflight_report.json` 能指出哪些对象不能进入仿真。
7. MuJoCo / Unity / Isaac adapter 至少一个可以跑通 smoke test。

## 推荐输出目录合同

建议把 `exports/<run>/simulator_assets/` 固化成下面结构：

```text
exports/<run>/simulator_assets/
  simulator_asset_bundle.json
  visual/
    scene_3dgs.ply
    scene_visual.glb
    objects/
      <object_id>/
        visual.glb
        preview.png
  colliders/
    scene_static_collider.glb
    objects/
      <object_id>/
        collider.glb
        collider_report.json
  physics/
    physics_properties.json
    physics_provenance.json
    sim_preflight_report.json
    stable_pose_cache.json
  semantic/
    object_sidecar.json
    mesh_face_sidecar.json
    scene_relations.json
  adapters/
    mujoco/
      scene.xml
      assets/
    unity/
      unity_adapter.json
      assets/
    isaac/
      scene_manifest.json
      assets/
  review/
    index.html
    screenshots/
```

这个结构把 SimFoundry 的系统精神拆成可执行工程合同：视觉、碰撞、物理、语义、adapter 和 QA 分开。

## `simulator_asset_bundle.json` 建议字段

现有 bundle 可以继续作为总入口，但建议加入 sim-readiness 字段：

```json
{
  "scene_id": "bedroom4_formal",
  "coordinate_system": {
    "up_axis": "z",
    "unit": "meter",
    "source_scale": "colmap_metric_or_estimated",
    "world_origin": "ground_aligned"
  },
  "visual_layer": {
    "type": "3dgs",
    "path": "visual/scene_3dgs.ply",
    "role": "render_only"
  },
  "static_colliders": [
    {
      "id": "scene_static",
      "path": "colliders/scene_static_collider.glb",
      "body_type": "static",
      "source": "colmap_delaunay",
      "qa_status": "pass"
    }
  ],
  "objects": [
    {
      "object_id": "chair_001",
      "label": "chair",
      "visual_mesh": "visual/objects/chair_001/visual.glb",
      "collider": "colliders/objects/chair_001/collider.glb",
      "body_type": "dynamic",
      "pose": {
        "translation": [0.0, 0.0, 0.0],
        "rotation_xyzw": [0.0, 0.0, 0.0, 1.0]
      },
      "physics": {
        "mass_kg": 4.5,
        "friction": 0.65,
        "restitution": 0.05,
        "source": "default_by_category",
        "confidence": 0.45
      },
      "qa_status": "needs_review"
    }
  ],
  "adapters": {
    "mujoco": "adapters/mujoco/scene.xml",
    "unity": "adapters/unity/unity_adapter.json",
    "isaac": "adapters/isaac/scene_manifest.json"
  },
  "preflight": "physics/sim_preflight_report.json"
}
```

注意这里 `visual_layer.role = render_only` 很重要：它明确告诉下游不要拿 3DGS 直接做碰撞。

## `sim_preflight_report.json` 应该检查什么

SimFoundry 的 PyBullet settling 思路可以先简化成一个 preflight report。报告不一定一开始就真的运行完整物理仿真，但必须能指出资产是否有资格进仿真器。

| 检查项 | P0 做法 | 失败影响 |
|---|---|---|
| asset existence | 检查 visual/collider/adapter 文件是否存在 | adapter 加载失败 |
| unit / scale | bbox 尺寸是否落在合理范围 | 物体巨大或微小 |
| up axis / ground | floor/support plane 是否可定义 | 物体穿地或悬空 |
| visual-collider alignment | visual bbox 与 collider bbox 是否接近 | 看得见但撞不到 |
| collider complexity | triangle count / convex parts 数量是否超阈值 | 仿真器性能差或 dynamic collider 不可用 |
| physics fields | mass/friction/restitution/body_type 是否缺失 | 不能创建 rigid body |
| penetration | object bbox 或 collider 与 static scene 是否明显互穿 | 一启动就爆开 |
| support relation | movable object 是否有 support surface | 物体掉落或漂移 |
| stable settle | 运行若干 step 后位移/旋转是否过大 | 初始状态不稳定 |

报告建议形态：

```json
{
  "status": "warn",
  "summary": {
    "objects_total": 12,
    "objects_pass": 7,
    "objects_warn": 4,
    "objects_fail": 1
  },
  "checks": [
    {
      "check": "missing_collider",
      "status": "fail",
      "object_id": "lamp_003",
      "message": "dynamic object has no collider asset"
    },
    {
      "check": "physics_defaults",
      "status": "warn",
      "object_id": "pillow_002",
      "message": "mass/friction are default estimates; manual review recommended"
    }
  ],
  "recommended_next_steps": [
    "generate collider for lamp_003",
    "review soft body candidate pillow_002 before rigid-body simulation"
  ]
}
```

这个文件是从“能看”走向“能仿真”的核心门禁。

## 物理属性 provenance

SimFoundry 使用 VLM 推断物理属性，但 Video2Mesh 不应直接相信自动估计。建议每个物理字段都带 provenance：

```json
{
  "object_id": "mug_001",
  "properties": {
    "body_type": {
      "value": "dynamic",
      "source": "semantic_category_rule",
      "confidence": 0.8
    },
    "mass_kg": {
      "value": 0.35,
      "source": "default_by_category",
      "confidence": 0.45
    },
    "friction": {
      "value": 0.55,
      "source": "material_prior",
      "confidence": 0.5
    },
    "restitution": {
      "value": 0.05,
      "source": "default_by_category",
      "confidence": 0.4
    }
  }
}
```

来源优先级建议：

1. `manual`: 人工标注或真实测量。
2. `imported`: 从外部 simulator asset 或 CAD metadata 导入。
3. `category_table`: 类别默认值，例如 mug/chair/book。
4. `vlm_estimate`: VLM/MLLM 草稿。
5. `fallback_default`: 没有依据的兜底值。

P0 可以先做 `category_table + fallback_default`，P1 再加 VLM 草稿，P2 才考虑真实测量或可学习估计。

## Collider 策略

SimFoundry 用 CoACD 生成 collision geometry。Video2Mesh 里建议按对象类型分层：

| 对象类型 | visual | collider | body type | 说明 |
|---|---|---|---|---|
| room / wall / floor / bed frame | 3DGS 或 scene mesh | simplified static mesh / Delaunay mesh | static | P0 先稳定 |
| table / shelf / cabinet body | visual mesh | primitive compound / convex decomposition | static 或 kinematic | 看任务是否需要移动 |
| cup / book / box / plate | object visual mesh | convex hull / CoACD | dynamic | P1 重点 |
| pillow / cloth / curtain / plant | visual mesh / 3DGS | primitive 或先 static | static / soft body candidate | P0 不做真实软体 |
| articulated object | part meshes | per-part convex + joints | articulated | P2 |

P0 不应拿高精 visual mesh 直接当 dynamic collider。复杂 mesh collider 在 Unity/MuJoCo/Isaac 里要么性能差，要么限制多，要么很容易出现初始穿插。

## Adapter 吸收路线

### MuJoCo

MuJoCo 适合作为最小仿真闭环，因为 XML 明确、刚体/关节/碰撞材质容易检查。

P0 目标：

```text
simulator_asset_bundle.json
  -> adapters/mujoco/scene.xml
  -> mujoco load smoke test
  -> step 100 frames
  -> report qpos drift / contact explosions
```

优先支持：

- static scene collider as mesh geom
- dynamic objects as box / sphere / convex-like simplified mesh
- material friction / restitution
- gravity settle

### Unity

Unity 更适合展示和交互验证。

P0 目标：

- visual mesh 用 MeshRenderer。
- static collider 用 MeshCollider。
- dynamic object 用 Rigidbody + BoxCollider/Convex MeshCollider。
- 通过 `unity_adapter.json` 明确 visual/collider 路径。

### Isaac / IsaacLab

Isaac 更接近 SimFoundry 的机器人策略环境，但工程成本高。

P0/P1 先只生成 manifest，不强行完成完整机器人任务：

- stage unit / axis
- static collision layer
- dynamic rigid objects
- material parameters
- future robot spawn points
- future task predicates

## scene relations 和任务入口

为了以后能从“仿真场景”走向“可执行任务”，建议提前加 `semantic/scene_relations.json`：

```json
{
  "relations": [
    {
      "subject": "book_001",
      "predicate": "OnTopOf",
      "object": "table_001",
      "source": "bbox_support_inference",
      "confidence": 0.72
    },
    {
      "subject": "cup_001",
      "predicate": "Near",
      "object": "plate_001",
      "source": "spatial_threshold",
      "confidence": 0.61
    }
  ]
}
```

这不是 P0 必需，但它是 SimFoundry task cousins 的最小前置条件。后续 `task_specs/` 可以只消费 predicate：

```yaml
task_name: place_cup_on_table
goal_predicates_all:
  - state: OnTopOf
    group: cup
    other_group: table
    value: true
```

短期我们不训练机器人，只把任务目标定义清楚。

## 分阶段吸收计划

### P0: 让场景能进仿真器

目标：从一个 Video2Mesh export 生成 MuJoCo 或 Unity 能加载的 scene。

必须完成：

- 固化 `simulator_assets/` 目录合同。
- `scene_static_collider.glb` 与 visual layer 对齐。
- object 级 visual/collider/physics 字段齐全。
- `sim_preflight_report.json` 能列出 pass/warn/fail。
- 至少一个 adapter 可以 load + step。

验收：

```text
python -m video2mesh.cli export-simulator-assets ...
python -m video2mesh.cli simulator-preflight ...
python -m video2mesh.cli export-simulator-adapter --target mujoco ...
python -m video2mesh.cli simulator-smoke-test --target mujoco ...
```

### P1: 让可移动物体稳定

目标：物体不再只是静态摆件，而是能作为 rigid body 参与碰撞。

必须完成：

- object collider 生成策略：bbox / convex hull / CoACD。
- physics defaults table。
- stable pose cache。
- penetration repair 或至少 penetration report。
- Unity / MuJoCo object-level interaction demo。

验收：

- 动态物体 step 后不爆开。
- visual mesh 与 collider bbox 偏差可控。
- 物体质量/摩擦不是空字段。

### P2: 关节、背景 clean plate 和任务

目标：接近 SimFoundry 的更完整能力，但不影响 P0/P1 主链路。

候选方向：

- articulated object generation：柜门、抽屉、门、微波炉。
- background clean plate / 3DGS automatic inpainting。
- task_specs 自动生成。
- object / scene cousins。
- IsaacLab 机器人任务模板。

这些不应阻塞 P0 的“能进仿真器”。

## 与现有 Video2Mesh 命令的映射

现有路线已经具备很多承接口：

```text
run-pipeline
  -> train-gsplat
  -> auto-prompts / track-masks
  -> fuse-masks / export-splat-masks
  -> export-object-mask-clouds
  -> prepare-object-images
  -> export-image-blaster
  -> import-object-meshes
  -> export-simulator-assets
  -> export-simulator-adapter
```

建议新增或强化：

| 命令 | 作用 |
|---|---|
| `simulator-preflight` | 读取 bundle，输出 QA report |
| `generate-object-colliders` | 为 object visual mesh 生成 bbox / convex / CoACD collider |
| `settle-simulator-scene` | 在 PyBullet / MuJoCo 中短跑，缓存 stable pose |
| `export-scene-relations` | 从 bbox、support plane、语义推断 scene predicates |
| `simulator-smoke-test` | 自动加载 adapter 并 step 若干帧 |

这些命令比直接追求“完整 SimFoundry”更现实，也更符合 Video2Mesh 当前工程状态。

## 风险与边界

| 风险 | 表现 | 处理 |
|---|---|---|
| scale 不准 | 物体巨大/微小，重力效果异常 | bundle 写 unit/source_scale，preflight 检 bbox |
| collider 过细 | 仿真器慢或 dynamic collider 不支持 | dynamic object 默认 primitive/convex |
| 视觉和碰撞错位 | 看得到但撞不到 | preflight 做 bbox/centroid alignment |
| 自动物理属性不可信 | mass/friction 乱猜 | provenance + confidence + warn |
| 物体互穿 | 一启动就爆开 | penetration report + settle cache |
| 软体对象误当刚体 | 枕头、窗帘、植物行为奇怪 | 标为 soft_body_candidate，P0 static |
| 背景 3DGS 不能碰撞 | 角色穿过视觉墙面 | 必须有独立 static collider |
| adapter 目标差异 | MuJoCo/Unity/Isaac 支持能力不同 | adapter 分开生成，不共用错误假设 |

## 最小落地清单

短期最值得做的 10 个文件/能力：

1. `simulator_assets/simulator_asset_bundle.json`
2. `simulator_assets/colliders/scene_static_collider.glb`
3. `simulator_assets/colliders/objects/<object_id>/collider.glb`
4. `simulator_assets/physics/physics_properties.json`
5. `simulator_assets/physics/physics_provenance.json`
6. `simulator_assets/physics/sim_preflight_report.json`
7. `simulator_assets/physics/stable_pose_cache.json`
8. `simulator_assets/semantic/object_sidecar.json`
9. `simulator_assets/adapters/mujoco/scene.xml`
10. `simulator_assets/adapters/unity/unity_adapter.json`

如果这 10 个东西能稳定生成，Video2Mesh 就已经吸收了 SimFoundry 对“可仿真资产”的核心价值。

## 当前判断

SimFoundry 对 Video2Mesh 的意义不在于“它有一个神奇模型可以直接复刻”，而在于它把真实场景重建的终点从 visual reconstruction 推到了 simulator execution。

Video2Mesh 应该吸收的是：

- sim-ready asset bundle
- visual/collider/physics/semantic 分层
- collider 和 physics 的 QA 门禁
- stable pose / depenetration 思路
- 后续 object / scene / task predicates

不应短期吸收的是：

- 完整机器人策略训练。
- 闭源 VLM 依赖。
- 单帧 RGB-D 替代多帧扫描主链路。
- 无 QA 的自动物理属性估计。

一句话：**把 SimFoundry 当成仿真资产合同的参考，而不是要复刻的仓库。Video2Mesh 的下一步应该是从“能展示”升级到“能被仿真器稳定消费”。**
