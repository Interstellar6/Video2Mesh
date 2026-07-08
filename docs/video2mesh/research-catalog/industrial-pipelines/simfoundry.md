---
title: SimFoundry 调研与 Video2Mesh 吸收方案
id: video2mesh-industrial-pipelines-simfoundry
category: 调研目录
visibility: public
summary: 调研 NVIDIA SimFoundry 的 real-to-sim-to-real 系统、开源边界和 Video2Mesh 的可吸收部分，并记录当前已完成的 P0 collider 与 P1 static object scene 验收。
tags:
  - 工业资产管线
  - Research Catalog
  - Real2Sim
  - Simulation
  - Simulator Asset
---

# SimFoundry 调研与 Video2Mesh 吸收方案

检查日期：2026-07-08

当前执行状态：Video2Mesh 已在 `codex/simfoundry-replica` 分支完成本轮 P0 collider-only scene 和 P1 static object scene 的本地复刻验收：P0 从真实 bedroom4 scene mesh 生成 scene-level static collider，P1 在同一 scene mesh + local face semantics 上生成 16 个静态语义对象、bbox collision proxy、物理 sidecar 和 MuJoCo / Unity / Isaac adapter。当前不声称完成 SimFoundry 全系统、动态物体释放、真实 provider 修复、digital cousins 或 policy learning。早前 P2/P4/P5 dynamic-readiness/repair 记录保留下来作为后续路线证据，但不是本轮验收口径。

## 最新复刻进度：2026-07-08

当前按“先能放进仿真模拟器”的边界，已经从 P0 collider-only 推进到 P1 static object scene：

```text
bedroom4 COLMAP Delaunay mesh
  -> scene_static_collider.obj
  -> collider-only simulator bundle
  -> local face semantics
  -> 16 static semantic objects + bbox collision proxies
  -> MuJoCo / Unity / Isaac adapters
  -> MuJoCo runtime smoke
```

最新产物：

| 阶段 | 输出目录 | 状态 |
|---|---|---|
| P0 collider-only | `exports/simfoundry_bedroom4_step1_collider_scene_rebuild_p0_20260708_031553/` | MuJoCo load + 5-step pass |
| P1 static object scene | `exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260708_031841/` | MuJoCo load + 5-step pass，16 objects all static |

P0 当前证据：

| 项 | 结果 |
|---|---:|
| scene static collider | 1 |
| collider vertices / triangles | 82,920 / 167,082 |
| objects | 0 |
| object collision proxies | 0 |
| adapter ready | 3 / 3 |
| MuJoCo runtime | pass |
| MuJoCo steps | 5 |
| MuJoCo nbody / ngeom / nmesh | 2 / 2 / 1 |
| required issues | 0 |
| remaining warnings | 4 个非阻塞 warning：`scale_not_calibrated`、`up_axis_unknown` |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

P1 当前证据：

| 项 | 结果 |
|---|---:|
| P1 semantic object meshes | 16 |
| P1 bbox collision proxies | 16 / 16 |
| P1 body type | 16 static |
| P1 foreground / background | 10 / 6 |
| P1 object collider | 16 box |
| P1 adapter ready | 3 / 3 |
| P1 smoke required issues | 0 |
| P1 smoke warnings | 2 个 `scale_not_calibrated` |
| P1 MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 无 API credential / Authorization token 命中 |

这一步吸收的是 SimFoundry 的 sim-ready asset contract：visual/object/collider/physics/adapter/preflight 分层。当前真正完成项到 P1 static object scene；P2/P4/P5 仍作为后续吸收路线的探索证据。不声称复刻了 NVIDIA 未完整公开的 foundation-model 编排或 policy-learning 闭环。

历史 P2 门禁证据：

| 项 | 结果 |
|---|---:|
| readiness status | `dynamic_blocked` |
| dynamic candidates | 8 |
| accepted dynamic | 0 |
| blocked candidates | 8 |
| unsupported candidates | 6 |
| penetration candidates | 8 |
| unique penetration blockers | 10 |
| sidecar body type | 16 static |
| sidecar collider | 16 box |
| sidecar smoke required issues | 0 |
| sidecar smoke warnings | 2 个 `scale_not_calibrated` |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| freejoint / dynamic scan | 0 命中 |

## 资料入口

- NVIDIA project page: https://research.nvidia.com/labs/gear/simfoundry/
- arXiv paper: https://arxiv.org/abs/2606.28276
- Related public code: https://github.com/nvidia-isaac/video_to_data
- Paper title: SimFoundry: Modular and Automated Scene Generation for Policy Learning and Evaluation
- arXiv status: v1 submitted on 2026-06-26, v2 revised on 2026-07-04

## 一句话结论

我们不能“完全用他的模型复刻它的项目”。SimFoundry 论文系统依赖一整套还没有完整公开的模型编排、提示词、物理修复、cousin 生成和机器人策略训练/评估闭环。

但我们可以吸收它最关键的工程思想：**不要把扫描结果当成单个 mesh，而要把它整理成 visual layer、collision layer、physics sidecar、semantic sidecar、simulator adapter 和 preflight QA。**

对 Video2Mesh 当前目标“能放进仿真模拟器里仿真”来说，最值得吸收的是 sim-ready asset contract，而不是直接复制 SimFoundry 的全部机器人学习系统。

## SimFoundry 做了什么

SimFoundry 的定位是 real-to-sim-to-real。它从单段真实视频出发，把真实场景转成可以交互的仿真环境，然后生成 object / scene / task cousins，用于机器人策略评估和训练。

抽象流程是：

```text
single real-world video
  -> representative frames / RGB-D / depth
  -> scene point cloud and background
  -> foreground object masks and crops
  -> object visual mesh generation
  -> pose / scale / articulation / physics annotation
  -> collider generation
  -> physics sanity check and settling
  -> sim-ready digital twin
  -> object cousins / scene cousins / task cousins
  -> policy evaluation and policy training
```

这里真正值得 Video2Mesh 学的是终点定义：不是“看起来像”，而是“能在物理模拟器里稳定运行，能承载任务”。

## 系统组件开源程度

截至 2026-07-07，NVIDIA 已公开相邻的 `nvidia-isaac/video_to_data` 仓库。这个仓库提供 video ingestion、reconstruction、typed contract、文件化 dataflow、Docker/module 边界等材料，并说明 robotic grounding 会后续发布。它很有价值，但它不是 SimFoundry 论文完整系统的一键复现包。

| 组件 | 当前公开程度 | Video2Mesh 处理方式 |
|---|---|---|
| 论文、项目页、demo 展示 | 公开 | 用作系统设计和验收目标参考 |
| V2D video ingestion | 公开 | 可参考它的文件化 pipeline 和 scene graph 思路 |
| V2D reconstruction modules | 部分公开 | 可参考 typed contract、Docker module、depth/mask/pose/mesh 输出边界 |
| V2D robotic grounding | README 标为 later release / coming soon | 暂不依赖，Video2Mesh 先做 simulator asset |
| SimFoundry full orchestration | 未完整公开 | 不能直接复刻，只能实现兼容的本地 CLI 合同 |
| object / scene / task cousin factory | 未完整公开 | 后续用 sidecar/job contract 仿照接口，不宣称同源实现 |
| foundation model prompts/config | 未完整公开 | 用可替换 provider contract 承接 |
| policy training/evaluation scripts | 未完整公开 | 当前不做，等 simulator asset 稳定后再评估 |
| reconstructed asset dataset | 页面有展示，不等于完整可下载训练集 | 不依赖，使用本项目 bedroom4 数据 |

所以开源边界可以概括成：

```text
公开：论文、项目页、相邻 V2D 外壳、部分 reconstruction/data contract 思路
未完整公开：SimFoundry 全流程配置、闭源/重模型调用、cousin factory、策略训练评测闭环
```

## 能吸收多少

按“能放进仿真模拟器”的目标估算：

| 层级 | 可吸收比例 | 说明 |
|---|---:|---|
| 系统设计思想 | 高，约 70% | 分层资产、文件化合同、preflight QA、adapter 边界都能吸收 |
| P0 static simulator asset | 高，当前已开始落地 | scene collider、collider-only bundle、MuJoCo/Unity/Isaac adapter 已跑通 |
| P1 object collider / physics sidecar | 中高 | 可以用现有 semantic mesh 和 bbox/convex proxy 做替代 |
| dynamic readiness / stability gate | 中 | 可以先用 penetration/support/bbox gate，后续再接真实物理修复 |
| provider-based structural repair | 中 | 可以用 `custom/Sub2API/responses/gpt-5-codex/gpt-image-2` 做合同层，但不能说等同官方模型 |
| object / scene / task cousins | 中低 | 可以先做 job template 和 sidecar，不宜一开始追完整自动化 |
| policy learning / real robot eval | 低 | 当前没有官方完整代码、真实机器人环境和任务数据，不作为近期目标 |

对我们最现实的吸收目标是：

```text
Video2Mesh output
  -> simulator_assets/
  -> static collider scene
  -> object collider and physics sidecar
  -> MuJoCo / Unity / Isaac adapter
  -> preflight QA
```

## 本轮怎么吸收进项目

这次不追完整 SimFoundry，而是把它的 sim-ready asset contract 落到 Video2Mesh 已有 CLI：

```text
prepare-simfoundry-collider-scene
  -> simulator_asset_bundle.collider_only.json
  -> export-simulator-adapter --format mujoco unity isaac
  -> simfoundry-simulator-smoke-test --mujoco-runtime require
  -> strict scale gate keeps failing until real measurement exists
```

本轮吸收的具体组件是：

| SimFoundry/V2D 思路 | Video2Mesh 落点 | 当前状态 |
|---|---|---|
| file-based artifact flow | `exports/<run>/simulator_assets/` | 已落地 |
| typed simulator asset contract | `simulator_asset_bundle.collider_only.json` | 已落地 |
| collision layer separate from visual layer | `colliders/scene_static_collider.obj` | 已落地 |
| simulator adapter boundary | `adapters/mujoco`、`adapters/unity`、`adapters/isaac` | 已落地 |
| preflight QA | `sim_preflight_report.current_p0_only.json` | 已通过 |
| coordinate and scale sidecar | `simulator_calibration.json` | up-axis 已写入，scale 未实测 |
| production safety gate | `--require-scale-calibration` | 按预期失败，防止误用 |

所以“吸收”不是把 NVIDIA 的未公开模型硬搬过来，而是先把我们自己的 reconstruction 输出改造成仿真器稳定消费的资产合同。P0 已经可以作为 MuJoCo/Unity/Isaac 的静态 collider 场景输入；下一步才轮到 P1 object layer。

## 当前已完成：collider-only scene

本轮按最新边界只做第一步：

```text
真实 bedroom4 scene mesh
  -> scene_static_collider.obj
  -> simulator_asset_bundle.collider_only.json
  -> MuJoCo / Unity / Isaac adapters
  -> MuJoCo runtime smoke
```

输出目录：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_20260707_195216/
```

关键结果：

| 项 | 结果 |
|---|---|
| source mesh | `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply` |
| collider mesh | `simulator_assets/colliders/scene_static_collider.obj` |
| vertex / triangle | 82,920 / 167,082 |
| collider QA | `pass` |
| collider required issue | 0 |
| collider-only bundle | `simulator_assets/simulator_asset_bundle.collider_only.json` |
| objects | 0，刻意保持 collider-only |
| static colliders | 1 |
| adapters | MuJoCo / Unity / Isaac |
| adapter ready | 3 / 3 |
| smoke status | `runtime_pass_with_warnings` |
| smoke required issue | 0 |
| up_axis | `y` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |

非阻塞 warning：

- `scale_not_calibrated`

这说明当前可以作为结构 smoke 进入模拟器；`up_axis_unknown` 已在最新 P0.1 中消失，但还没有到真实物理尺度和动态交互阶段。

## P0.1 已推进：up-axis / calibration sidecar

在 collider-only scene 跑通之后，最新 timestamped rebuild 目录已经补齐校准 sidecar：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_20260707_195216/
```

这一步吸收的是 SimFoundry/V2D 风格的 typed contract：坐标系、尺度、adapter、preflight report 都必须文件化，而不是靠口头约定。具体结果：

| 项 | 结果 |
|---|---|
| collider mesh | 仍为 `scene_static_collider.obj` |
| vertex / triangle | 82,920 / 167,082 |
| calibration artifact | `simulator_assets/simulator_calibration.json` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| up_axis | `y` |
| object_count | 0 |
| adapter | MuJoCo / Unity / Isaac |
|普通 smoke | `runtime_pass_with_warnings`，required issue 0 |
| 普通 smoke warning | 只剩 `scale_not_calibrated`，`up_axis_unknown` 已消失 |
| 严格 smoke | `--require-scale-calibration` 下按预期 `fail` |
| 严格 required issue | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | 两种 smoke 都能 load + step 5 帧 |

这里没有把 `scale_calibrated` 写成 true，因为当前没有真实量尺证据。这个选择很重要：它让 collider scene 可以继续进入模拟器做结构级验证，同时保留生产级物理仿真的硬门槛。

最新 P0.1 证据文件：

```text
simulator_assets/simulator_calibration.json
simulator_assets/simulator_asset_bundle.collider_only.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

## P0 最新复跑：collider-only rebuild

为了把“当前可复现步骤”和早期 probe / exploration 产物分开，又跑了一次最新 collider-only rebuild：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_p0_20260707_234318/
```

这次仍然严格限制在第一阶段：

```text
existing bedroom4 Delaunay mesh
  -> scene_static_collider.obj
  -> simulator_asset_bundle.collider_only.json
  -> simulator_calibration.json
  -> MuJoCo / Unity / Isaac adapter
  -> normal smoke + strict scale gate
```

关键验收：

| 项 | 结果 |
|---|---|
| collider QA | `pass` |
| vertex / triangle | 82,920 / 167,082 |
| objects | 0 |
| static colliders | 1 |
| adapter ready | 3 / 3 |
| up_axis | `y` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| normal smoke | `runtime_pass_with_warnings`，required issue 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| strict scale gate | `fail`，2 个 required `scale_not_calibrated` |
| MuJoCo runtime | normal / strict 两种 smoke 都能 load + step 5 帧 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |

这一步是当前“先重建生成 collider 场景即可”的最新证据。它证明我们已经能把 static collision scene 放进模拟器做结构级 smoke；同时它也保留了真实尺度校准的硬门槛，没有把工程假设伪装成生产物理资产。

下一格不是 dynamic release，而是 scale calibration：P0 collider-only bundle 没有 object records，不能自动挑 reference object。当前已在 P0 目录导出 `simulator_assets/scale_calibration_jobs_p0/`，其 `candidate_count=0`，这正好说明不能从 collider-only 层伪造量尺。需要先进入 P1 static object scene，导出 object/background reference candidate，再填入真实量尺，最后让 strict scale gate 通过。

## P1 最新复跑：static object scene rebuild

P0 之后，已经在新的 timestamped 目录里重建了 P1 static object scene：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260707_235133/
```

这一步用同一个 bedroom4 Delaunay mesh 和本地 face semantics，重新拆出 16 个 semantic object mesh，并给每个对象生成 bbox collision proxy。所有 object body type 仍为 `static`，没有 `freejoint`，没有 dynamic release，也没有 provider 调用。

P1 验收：

| 项 | 结果 |
|---|---|
| semantic object meshes | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxy | 16 / 16 |
| object body type | `static: 16` |
| object collider | `box: 16` |
| adapter ready | 3 / 3 |
| static scene report | `ready`，required issue 0 |
| normal smoke | `runtime_pass_with_warnings`，required issue 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| strict scale gate | `fail`，2 个 required `scale_not_calibrated` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

P1 还生成了真实尺度校准模板：

```text
simulator_assets/scale_calibration_jobs_p1/
```

该模板 `candidate_count=16`，但 `selected_reference` 为空。也就是说，P1 已经能提出可量尺候选，但还没有导入任何真实量尺，不应把 `scale_calibrated` 改成 true。

按当前 scene length 排序的量尺候选：

| object | category | axis | scene length |
|---|---|---:|---:|
| `gdino_object_floor` | floor | x | 27.8785 |
| `gdino_object_door` | door | z | 21.3139 |
| `gdino_object_wall` | wall | x | 20.1419 |
| `gdino_object_wall_2` | wall | y | 19.2179 |
| `gdino_object_window` | window | z | 16.2287 |
| `gdino_object_bed` | bed | x | 14.7931 |

这个 P1 rebuild 是当前从前到后的第二格：已经不是只有 scene collider，而是完整静态对象场景可以进入 MuJoCo / Unity / Isaac。但下一步仍应先做真实 scale calibration 和 collider refinement，而不是直接释放 dynamic。

## P2 最新复跑：dynamic-readiness gate

在 P1 static object scene 之后，已经运行 P2 dynamic-readiness gate：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260707_235133/simulator_assets/simfoundry_dynamic_readiness_p2_20260708_013632/
```

这一步继续吸收 SimFoundry 的保守动态释放逻辑：先用 tight collider、support、penetration 和 smoke gate 证明对象安全，再考虑把 body type 变成 dynamic。当前结果是 `dynamic_blocked`，说明门禁正常工作，但现有 geometry 还不能安全释放动态体。

| 项 | 结果 |
|---|---:|
| readiness status | `dynamic_blocked` |
| object count | 16 |
| tight collider updated | 16 |
| penetration before / after tight | 42 / 19 |
| candidate count | 8 |
| accepted dynamic | 0 |
| blocked candidates | 8 |
| unsupported candidates | 6 |
| penetration candidates | 8 |
| unique penetration blockers | 10 |
| sidecar body type | `static: 16` |
| adapter ready | 3 / 3 |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

Top blockers：

| blocker | category | affected candidates | max penetration depth |
|---|---|---:|---:|
| `gdino_object_wall` | wall | 5 | 2.3342 |
| `gdino_object_door` | door | 4 | 3.9599 |
| `gdino_object_nightstand_3` | nightstand | 4 | 1.3199 |
| `gdino_object_wall_2` | wall | 2 | 2.0731 |
| `gdino_object_nightstand` | nightstand | 1 | 1.3199 |

Repair queue 前几项：

| object | priority | reasons | penetration count | support candidates |
|---|---|---|---:|---:|
| `gdino_object_nightstand_3` | `p0_support_and_penetration` | penetration, unsupported | 6 | 0 |
| `gdino_object_lamp_3` | `p0_support_and_penetration` | penetration, unsupported | 3 | 0 |
| `gdino_object_bed` | `p0_support_and_penetration` | penetration, unsupported | 2 | 0 |
| `gdino_object_lamp_4` | `p0_support_and_penetration` | penetration, unsupported | 2 | 0 |
| `gdino_object_plant_3` | `p0_support_and_penetration` | penetration, unsupported | 2 | 0 |

正确结论不是“动态已经完成”，而是：Video2Mesh 已经能运行 SimFoundry-style dynamic gate，并能保守拒绝不安全对象。下一步应沿 blocker queue 做 collider refinement、semantic split repair 或 structural repair sidecar。

## P1 已推进：static object scene

当前又新增了一个干净静态对象场景目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/
```

这一步开始吸收 SimFoundry 的 object-level asset contract，但仍保持保守：所有对象都是 static，不生成 dynamic body，不调用 provider，不做 structural repair。

| 项 | 结果 |
|---|---|
| input mesh | bedroom4 COLMAP Delaunay `mesh.ply` |
| semantics | `mesh_mesh_semantics_local.json` |
| semantic object mesh | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxy | 16 / 16 |
| object body type | 全部 `static` |
| dynamic object | 0 |
| adapter | MuJoCo / Unity / Isaac |
| adapter ready | 3 / 3 |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| freejoint | 0 |
| normal smoke | `runtime_pass_with_warnings`，required issue 0 |
| strict scale gate | `fail`，2 个 `scale_not_calibrated` |

这一步的意义是：Video2Mesh 不再只证明“scene collider 能进模拟器”，而是已经能把语义对象层和 bbox collision proxy 一起打包进 simulator-ready static scene。它还是基线层，不是动态层。

上一轮 front-to-back 复跑又生成了独立 P1 目录，避免和早期 P2/P3/P4 实验产物混在一起：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/
```

这轮历史 P1 验收结果：

| 项 | 结果 |
|---|---|
| semantic object mesh | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxy | 16 / 16 |
| object body type | `static: 16` |
| collider shape | `box: 16` |
| dynamic object | 0 |
| missing mesh object | 0 |
| coordinate up_axis | `y` |
| scale_calibrated | `false` |
| adapter ready | 3 / 3 |
| static scene report | `ready`，required issue 0 |
| smoke status | `runtime_pass_with_warnings` |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 46 passed |

这个历史目录证明了“先做到能放进仿真模拟器”的 P1 路线：它已经是 simulator-ready static object scene，但还没有真实尺度标定，也没有进入 dynamic release 或真实 provider 修复。当前最新证据以上方 2026-07-08 P0/P1/P2 front-to-back run 为准。

## P1.1 已推进：真实尺度校准 job

在上一轮 P1 静态对象场景目录上，已经生成了真实尺度校准的候选模板，但还没有导入任何实测值：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/scale_calibration_jobs_rebuild_20260707_195700/
```

产物：

```text
scale_calibration_job.json
scale_calibration_template.json
scale_calibration_readme.md
run_scale_calibration_example.sh
```

这一步的意义是把 “scale calibration” 从口头 TODO 变成可交接的工程 job。它只准备 measurement template，不修改主 bundle，也不会把 `scale_calibrated` 写成 true。

| 项 | 结果 |
|---|---:|
| provider | `manual_measurement` |
| candidate count | 16 |
| include background structure | true |
| selected reference | empty |
| bundle scale_calibrated | false |
| bundle up_axis | y |
| test | `tests/test_simfoundry_replica.py` 47 passed |

推荐人工量尺候选：

| object | category | axis | scene length | priority |
|---|---|---:|---:|---:|
| `gdino_object_door` | door | z | 21.3139 | 100 |
| `gdino_object_bed` | bed | x | 14.7931 | 95 |
| `gdino_object_floor` | floor | x | 27.8785 | 85 |
| `gdino_object_wall` | wall | x | 20.1419 | 75 |
| `gdino_object_window` | window | z | 16.2287 | 70 |

下一步如果要让严格 scale gate 通过，必须先从真实场景或可信数据源得到一个实际长度，填入 `scale_calibration_template.json` 的 `selected_reference`，再运行 `run_scale_calibration_example.sh` 或 `calibrate-simulator-assets`。在此之前，当前场景仍只能作为结构级仿真输入，不是生产级真实尺度物理资产。

## P2/P3 已推进：tight collider + dynamic-readiness blocker queue

在静态对象场景之后，继续按 SimFoundry 的安全释放思路做动态前置门禁：

```text
static object scene
  -> tight bbox collider variant
  -> support / penetration checks
  -> dynamic candidate gate
  -> blocker report and repair queue
  -> simulator adapter smoke
```

输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/simulator_assets/simfoundry_dynamic_readiness_current/
```

关键结果：

| 项 | 结果 |
|---|---|
| readiness status | `dynamic_blocked` |
| gate ok | `true`，门禁运行成功 |
| object count | 16 |
| tight collider updated | 16 |
| bbox penetration | 42 -> 19 |
| dynamic candidates | 8 |
| accepted dynamic | 0 |
| blocked candidates | 8 |
| unsupported candidates | 6 |
| penetration candidates | 8 |
| unique penetration blockers | 10 |
| adapter ready | 3 / 3 |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| freejoint | 0 |
| body_type | 16 个全部仍为 `static` |

最主要的 blocker 是：

| blocker | 类别 | 影响候选数 | 最大 penetration depth |
|---|---|---:|---:|
| `gdino_object_wall` | wall / background | 5 | 2.334 |
| `gdino_object_door` | door | 4 | 3.960 |
| `gdino_object_nightstand_3` | nightstand | 4 | 1.320 |
| `gdino_object_wall_2` | wall / background | 2 | 2.073 |
| `gdino_object_nightstand` | nightstand | 1 | 1.320 |

repair queue 的最高优先级集中在 nightstand、lamp、bed、plant 等对象，原因多为 `penetration` + `unsupported`。这说明当前系统已经吸收了 SimFoundry 很关键的一点：**动态不是一个开关，而是一个必须经过 geometry / support / collision gate 的释放流程。**

当前不应声称 dynamic scene 已完成；正确说法是：Video2Mesh 已经能生成 dynamic-readiness blocker report，并且能保守拒绝不安全的 dynamic release。

上一轮 front-to-back P1 目录也已经重新跑过 dynamic-readiness gate：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_dynamic_readiness_front_to_back/
```

这轮历史 gate 摘要：

| 项 | 结果 |
|---|---|
| readiness status | `dynamic_blocked` |
| object count | 16 |
| tight collider updated | 16 |
| bbox penetration | 42 -> 19 |
| dynamic candidates | 8 |
| accepted dynamic | 0 |
| blocked candidates | 8 |
| unsupported candidates | 6 |
| penetration candidates | 8 |
| unique penetration blockers | 10 |
| smoke required issue | 0 |
| main bundle body type | `static: 16` |
| dynamic variant body type | `static: 16` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |
| MuJoCo runtime | load + step 5 帧通过，`nbody=18`、`ngeom=18`、`nmesh=1` |

最新 top blockers 仍集中在 wall / door / nightstand 一类结构或语义切分边界：

```text
gdino_object_wall
gdino_object_door
gdino_object_nightstand_3
gdino_object_wall_2
gdino_object_nightstand
```

这一步是继续吸收 SimFoundry 思路的关键：动态释放不是“改 body_type”这么简单，而是先要用 support / penetration / smoke gate 证明对象能安全进入物理仿真。当前门禁运行成功，但释放结果为 0，这个保守结果是正确的。

## P4 dry-run 已推进：provider-shaped structural repair contract

在 blocker queue 之后，继续做 SimFoundry-style structural repair 的合同层，但仍保持 dry-run：

```text
dynamic_blocker_report.json
  -> structural_repair_plan.json
  -> structural_repair_review_request.json
  -> dry-run review patch
```

这一步没有调用真实 provider，没有导入 patch，没有覆盖主 bundle，也没有释放 dynamic body。它的价值是把后续模型/人工修复需要看的上下文、输出 schema 和安全边界先固定下来。

输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/
```

Provider-shaped contract 已按用户指定模型选型落地：

| 项 | 值 |
|---|---|
| provider_name | `Sub2API` |
| model_provider | `custom` |
| base_url | `https://plbbl.com` |
| wire_api | `responses` |
| model | `gpt-5-codex` |
| image_model | `gpt-image-2` |
| reasoning effort | `high` |
| disable response storage | `true`，request body `store=false` |
| auth | 只保存环境变量名 `OPENAI_API_KEY` |
| provider called | `false` |

Repair plan 摘要：

| 项 | 结果 |
|---|---|
| repair plan status | `structural_repair_plan_ready` |
| object repair plans | 8 |
| structural blocker plans | 8 |
| background structural blockers | 3 |
| support repair plans | 6 |
| penetration repair plans | 8 |
| review worker status | `dry_run_request_prepared` |
| placeholder object patches | 11 |
| import_ready | `false` |
| main bundle overwritten | `false` |
| dynamic_release | `false` |
| request endpoint | `https://plbbl.com/v1/responses` |
| request `store` | `false` |
| provider called | `false` |
| freejoint scan | 0 命中 |
| secret scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 46 passed |

Object repair queue：

```text
gdino_object_nightstand_3
gdino_object_lamp_3
gdino_object_bed
gdino_object_lamp_4
gdino_object_plant_3
gdino_object_plant_4
gdino_object_nightstand
gdino_object_nightstand_2
```

Structural blocker queue：

```text
gdino_object_wall
gdino_object_door
gdino_object_nightstand_3
gdino_object_wall_2
gdino_object_nightstand
gdino_object_plant_4
gdino_object_lamp_4
gdino_object_lamp_3
```

安全检查结果：主 `simulator_asset_bundle.json` 和 dynamic variant bundle 都仍然是 16 个 `static` body；MuJoCo XML 没有 `freejoint`。这说明 P4 dry-run 只是 review/repair 合同，不是修复导入或 dynamic release。

## P4.1 已推进：manual/local repair sidecar import

dry-run 之后，为了验证 import pipeline，又导入了一个本地 manual/local patch。这个 patch 来源是已有 tight bbox 变体，不是 provider 结果；它的作用是验证 sidecar bundle、adapter 和 smoke test 能跑通。

输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/
```

关键结果：

| 项 | 结果 |
|---|---:|
| import status | `structural_repair_imported` |
| object patches | 9 |
| applied patches | 9 |
| skipped patches | 0 |
| main bundle overwritten | `false` |
| provider called | `false` |
| object count | 16 |
| body type | `static: 16` |
| collision proxies | 16 / 16 |
| adapter ready | 3 / 3 |
| sidecar smoke | `runtime_pass_with_warnings` |
| MuJoCo runtime | pass，5 steps |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| required issue | 0 |
| warning | 2 个 `scale_not_calibrated` |

和 baseline dynamic-readiness 对比：

| 指标 | baseline | manual/local import 后 |
|---|---:|---:|
| status | `dynamic_blocked` | `dynamic_blocked` |
| tight updated | 16 | 7 |
| penetration before tight variant | 42 | 28 |
| penetration after tight variant | 19 | 19 |
| dynamic candidates | 8 | 8 |
| accepted dynamic | 0 | 0 |
| blocked candidates | 8 | 8 |
| unsupported candidates | 6 | 6 |
| unique penetration blockers | 10 | 10 |

这个结果是一个保守进展：sidecar import/smoke 已经闭环，早期 penetration 数下降，但最终 dynamic gate 仍然拒绝全部候选。正确结论是“structural repair import pipeline 可用”，不是“动态场景已完成”。

## 当前实现命令

```bash
PYTHONPATH=. uv run python -m video2mesh.cli init \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --scene-id simfoundry-bedroom4-step1-collider-scene-current-20260707

PYTHONPATH=. uv run python -m video2mesh.cli prepare-simfoundry-collider-scene \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --scene-mesh tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply \
  --collider-format obj \
  --mode copy \
  --min-vertices 1000 \
  --min-triangles 1000 \
  --write-collider-only-bundle \
  --json \
  --fail-on-fail

PYTHONPATH=. uv run python -m video2mesh.cli export-simulator-adapter \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --format mujoco unity isaac \
  --copy-assets \
  --mode copy

PYTHONPATH=. uv run --with mujoco --with numpy python -m video2mesh.cli simfoundry-simulator-smoke-test \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --format mujoco unity isaac \
  --mujoco-runtime require \
  --mujoco-steps 5 \
  --output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/simulator_assets/physics/sim_preflight_report.json \
  --json \
  --fail-on-required
```

## 推荐资产结构

Video2Mesh 应该长期把产物拆成这些层：

```text
simulator_assets/
  colliders/
    scene_static_collider.obj
  objects/
    <object_id>/object_asset.json
  semantic/
    scene_graph.json
    relations.json
  physics/
    sim_preflight_report.json
    scale_calibration.json
  adapters/
    mujoco/scene.xml
    unity/unity_adapter.json
    isaac/isaac_adapter.json
  simulator_asset_bundle.json
```

当前已完成并验收的是 P0 `colliders/`、collider-only bundle、`adapters/`，P1 static object `objects/`、bbox collision proxy、static physics sidecar 和三套 simulator adapter，以及 P2 dynamic-readiness gate sidecar。dynamic body release、真实 provider 修复和 task/cousin sidecar 仍不计入完成项。

## 下一阶段怎么吸收

不要直接把 SimFoundry 复刻成一个大而全脚本。建议继续分阶段：

### P0: Static collider scene

状态：已完成本轮验收。

目标是只保证场景碰撞体能进入模拟器。当前 `scene_static_collider.obj` 和三套 adapter 已经满足。

### P0.1 / P1.1: Scale and up-axis calibration

当前 P1 已经把 `up_axis=y` 写入 bundle，并生成 16 个量尺候选；尺度仍未实测，所以 strict scale gate 仍应失败，这是正确行为。下一步要做真实量尺：

- 选一个真实场景中的参考长度，比如床宽、门高、桌面高度。
- 写入 `scale_calibration.json`。
- 在 adapter 导出时明确 `scale_to_meters` 和 `up_axis`。
- 重新跑 smoke，目标是消掉 `scale_not_calibrated` 和 `up_axis_unknown`。

### P1: Static object scene

状态：已完成当前 P1 验收。

在不覆盖 P0 基线的前提下，已接入 semantic mesh：

```text
scene collider
  + semantic object meshes
  + bbox collision proxy
  + all objects static
```

这一层已经证明完整静态对象场景可以沿同一 adapter/smoke 路径进入 MuJoCo / Unity / Isaac，并且 MuJoCo load + step 通过。它故意不释放 dynamic；下一步应先做真实 scale calibration 和 collider refinement。

### P2: Dynamic-readiness gate

状态：已完成当前 P2 验收，但结果是 `dynamic_blocked`，accepted dynamic 为 0。

当前已经生成 tight collider variant、support / penetration gate、dynamic blocker report 和 sidecar adapters，并通过 MuJoCo load + step smoke。它证明门禁能运行，也证明现有几何还不能安全释放 dynamic body。

### P3: Object collider refinement

先用 bbox proxy，后续替换为：

- CoACD
- V-HACD
- compound primitive
- manually reviewed proxy

目标是降低互穿和不稳定接触，不追求视觉 mesh 本身直接参与碰撞。

### P4: Dynamic release retry

在 P2 blocker queue 被修复后，再重跑动态释放门禁：

- object 是否 foreground
- mass / material 是否可信
- support relation 是否合理
- collider 是否与 static scene 或其他 object 明显互穿
- MuJoCo load / step 是否稳定

只有通过 gate 的 object 才能加 `freejoint` 或 dynamic body。

### P5: Provider-shaped repair

如果 gate 发现 wall / door / nightstand 这类结构 blocker，再接 provider-shaped review：

```text
repair_plan.json
  -> review request
  -> model/human response patch
  -> structural_repair sidecar bundle
  -> smoke test
```

可以使用用户指定的 provider contract：

```toml
model_provider = "custom"
model = "gpt-5-codex"
model_reasoning_effort = "high"
disable_response_storage = true

[model_providers.custom]
name = "Sub2API"
base_url = "https://plbbl.com"
wire_api = "responses"
requires_openai_auth = true
```

安全要求：仓库和文档只保存 `OPENAI_API_KEY` 这个环境变量名，不能保存明文 key。

### P6: Cousins and tasks

等 P0 到 P4 稳定后再做：

- object cousins：同 affordance 的替代物体
- scene cousins：背景和布局扰动
- task cousins：目标谓词和初始状态扰动

这一层可以借鉴 SimFoundry，但不应该在 collider scene 未稳定时提前做。

## 当前不能过度宣称的点

- 不能说已经完全复刻 SimFoundry。
- 不能说使用了 NVIDIA 官方 SimFoundry 模型。
- 不能说动态物体已经稳定释放。
- 不能说物理尺度已经真实校准。
- 不能把 mock/provider-shaped patch 当真实模型输出。
- 不能把单次 MuJoCo smoke 当作 policy learning benchmark。

## 当前判断

Video2Mesh 现在应该吸收 SimFoundry 的工程骨架，而不是硬拷贝未开源模型。

最小可行路线是：

```text
collider-only scene
  -> scale calibration
  -> static object scene
  -> dynamic readiness gate
  -> object collider refinement / structural repair
  -> dynamic release retry
  -> task/cousin sidecar
```

当前验收已完成前三格：**collider-only scene rebuilt**、**static object scene rebuilt** 和 **dynamic-readiness gate**。三层都已导出 MuJoCo / Unity / Isaac adapter 或 sidecar adapter，并通过 MuJoCo runtime load + step smoke；dynamic gate 正确给出 `dynamic_blocked`，accepted dynamic 为 0。下一步重点是真实 scale calibration、object collider refinement / structural repair，然后再重跑 dynamic release retry。
