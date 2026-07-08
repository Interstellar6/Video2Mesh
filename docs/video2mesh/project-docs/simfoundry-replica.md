---
title: SimFoundry 复刻分支运行说明
id: video2mesh-simfoundry-replica
category: 项目文档
visibility: public
summary: 记录 Video2Mesh 在 codex/simfoundry-replica 分支上按 SimFoundry 思路复刻 P0 collider-only scene 与 P1 static object scene 的当前重建结果、产物和仿真 smoke 结果。
tags:
  - SimFoundry
  - Collider
  - Simulator
  - Asset Contract
---

# SimFoundry 复刻分支运行说明

当前分支：`codex/simfoundry-replica`

当前边界：**从前到后一步步来，本轮最新验收到 P1 static object scene；仿真器可加载，但所有 object 仍保持 static。**

这份文档把当前完成口径收在 P0 collider-only scene 和 P1 static object scene。dynamic rigid body release、digital cousins、真实 provider 调用或 policy learning 仍不算完成项。下方保留早前 P2/P4/P5 探索记录，但它们不是本轮“先重建 collider 场景，再接 static object scene”的验收边界。

## 最新验收：2026-07-08 P0/P1 rebuild

本轮重新按“先能放进仿真模拟器”的最小前向路径跑了两组干净 timestamped 目录，避免把早期 dynamic gate、repair 和 provider-shaped dry-run 混进当前验收口径：

```text
P0:
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_p0_20260708_031553/

P1:
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260708_031841/
```

最新流程：

```text
bedroom4 COLMAP Delaunay mesh
  -> P0 scene_static_collider.obj
  -> P0 collider-only simulator bundle
  -> P0 MuJoCo / Unity / Isaac adapters
  -> P0 MuJoCo runtime smoke
  -> P1 local face semantics split
  -> P1 16 static semantic objects + bbox collision proxies
  -> P1 MuJoCo / Unity / Isaac adapters
  -> P1 MuJoCo runtime smoke
```

最新 P0 验收：

| 项 | 结果 |
|---|---:|
| scene static collider | 1 |
| collider vertices / triangles | 82,920 / 167,082 |
| objects | 0 |
| static colliders | 1 |
| adapters ready | 3 / 3 |
| smoke required issues | 0 |
| smoke warnings | 4 个非阻塞 warning：`scale_not_calibrated`、`up_axis_unknown` |
| MuJoCo runtime | pass |
| MuJoCo nbody / ngeom / nmesh | 2 / 2 / 1 |

最新 P1 验收：

| 项 | 结果 |
|---|---:|
| semantic object meshes | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxies | 16 / 16 |
| object body type | `static: 16` |
| object collider | `box: 16` |
| adapter ready | 3 / 3 |
| static scene report | `ready` |
| static scene required issues | 0 |
| smoke required issues | 0 |
| smoke warnings | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | pass |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| freejoint / dynamic scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

本轮安全边界：

- 不调用 provider，不使用用户提供的 API key，不生成 provider request。
- P0 collider-only bundle 内 `objects=[]`。
- P1 主 bundle 内 16 个对象全部是 `static`。
- MuJoCo XML 和产物目录扫描没有 `freejoint` / dynamic body。
- 当前只证明 simulator-ready static scene 能运行；不证明真实尺度已校准，也不证明 dynamic object release 已完成。

## 历史探索：P2/P4/P5 dynamic-readiness 与 repair

早前分支上已经探索过 P2 dynamic-readiness、provider-shaped repair dry-run、manual/local structural refit，以及 P5 dynamic-release sidecar。它们说明当前代码已经有继续向动态层推进的接口雏形，但本轮按用户最新要求先收口在 P0/P1：静态 collider 场景和 static object scene 能放进仿真器。

## 历史验收：2026-07-07 P0 collider-only rebuild

以下是上一组 P0 正式验收记录，保留为历史上下文；当前最新可复现证据以上方 2026-07-08 front-to-back run 为准。

本轮按最小前向路径复验：

```text
bedroom4 COLMAP Delaunay mesh
  -> scene_static_collider.obj
  -> simulator_asset_bundle.collider_only.json
  -> MuJoCo / Unity / Isaac adapter
  -> MuJoCo runtime load + 5-step smoke
```

不调用 provider，不使用用户提供的 API key，不生成 object body，不释放 dynamic body。所有验收只认下面这个 timestamped P0 目录：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_p0_20260707_234318/
```

这个目录已经补齐 P0 坐标合同：

```text
simulator_assets/simulator_calibration.json
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

当前 `up_axis=y` 已写入 bundle / adapter / smoke report；`scale_to_meters=1.0` 仍明确标记为未实测假设，`scale_calibrated=false`。这意味着当前资产可以做结构级仿真 smoke，但不能冒充真实尺度物理资产。

P0 验收结果：

| 项 | 结果 |
|---|---:|
| scene static collider | 1 |
| collider vertices / triangles | 82,920 / 167,082 |
| objects | 0 |
| object collision proxies | 0 |
| adapters ready | 3 / 3 |
| normal smoke status | `runtime_pass_with_warnings` |
| normal required issues | 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| coordinate up_axis | `y` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| MuJoCo runtime | pass |
| MuJoCo steps | 5 |
| MuJoCo nbody / ngeom / nmesh | 2 / 2 / 1 |
| strict scale gate | `fail` as expected |
| strict required issues | 2 个 `scale_not_calibrated` |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

P0 关键文件：

```text
simulator_assets/colliders/scene_static_collider.obj
simulator_assets/simulator_asset_bundle.collider_only.json
simulator_assets/simulator_calibration.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/mujoco/mujoco_adapter.json
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

安全检查：

- collider-only bundle 内 `objects=[]`。
- MuJoCo XML 没有 `freejoint` 或 free body。
- 产物目录没有明文 API key。
- 本轮 P0 没有 provider request，也没有真实 provider 调用。
- `PYTHONPATH=. uv run --with pytest --with numpy pytest tests/test_simfoundry_replica.py -q` 通过：47 passed。

这个结果证明当前场景已经可以作为静态 collider asset 导入模拟器做结构级检查；它仍不证明真实尺度已校准，也不证明 object-level static scene、dynamic release 或完整 SimFoundry 复现已经完成。

## 下一格：scale / up-axis 校准边界

本轮已经把 `up_axis=y` 作为仿真导入约定写入 bundle；真正缺的是实测比例尺。当前 collider-only bundle 没有 object records，因此不能从 P0 自身自动挑选门、床、地板等 reference object。正确顺序是：

1. 在 P1 static object scene 中生成 object records 和 bbox/collider proxy。
2. 用 `prepare-scale-calibration-jobs --include-background` 导出量尺模板。
3. 人工填入一个真实 reference length 后再 `import-scale-calibration` 或 `calibrate-simulator-assets --reference-object ... --scale-calibrated`。
4. 重新导出 adapter，并跑 `simfoundry-simulator-smoke-test --require-scale-calibration`。

所以当前 P0 的 strict scale gate 失败是预期安全边界，不是结构导入失败。

P0 目录内已经导出一个校准任务模板，用来证明这个边界：

```text
simulator_assets/scale_calibration_jobs_p0/
  scale_calibration_job.json
  scale_calibration_template.json
  scale_calibration_readme.md
  run_scale_calibration_example.sh
```

该 job 的 `candidate_count=0`。这不是错误，而是 collider-only 场景没有 object/background records 的自然结果。

## 最新推进：2026-07-07 P1 static object scene rebuild

在 P0 collider-only 通过后，又单独开了一个干净 P1 目录，重建 static object scene：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260707_235133/
```

这一步继续保持保守边界：不调用 provider，不释放 dynamic body，不生成 freejoint；只把语义对象层、bbox collision proxy、静态物理 sidecar 和三套 adapter 接进 simulator bundle。

P1 流程：

```text
bedroom4 Delaunay mesh
  + local face semantics
  -> 16 semantic object meshes
  -> scene_static_collider.obj
  -> 16 bbox collision proxies
  -> simulator_asset_bundle.json
  -> MuJoCo / Unity / Isaac adapter
  -> MuJoCo runtime smoke
```

P1 验收结果：

| 项 | 结果 |
|---|---:|
| semantic object meshes | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxies | 16 / 16 |
| object body type | `static: 16` |
| object collider | `box: 16` |
| adapter ready | 3 / 3 |
| static scene report | `ready` |
| static scene required issues | 0 |
| normal smoke status | `runtime_pass_with_warnings` |
| normal required issues | 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | pass |
| MuJoCo steps | 5 |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| strict scale gate | `fail` as expected |
| strict required issues | 2 个 `scale_not_calibrated` |
| branch test | `tests/test_simfoundry_replica.py` 47 passed |

P1 关键文件：

```text
simulator_assets/semantic_object_meshes/semantic_object_meshes.json
simulator_assets/colliders/scene_static_collider.obj
simulator_assets/simulator_asset_bundle.json
simulator_assets/simfoundry_static_object_scene/static_object_scene_report.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

P1 scale calibration template 也已经生成：

```text
simulator_assets/scale_calibration_jobs_p1/
```

该 job 的 `candidate_count=16`，`selected_reference` 仍为空，没有导入实测值，也没有把 `scale_calibrated` 写成 true。

按当前 scene length 排序的量尺候选：

| object | category | axis | scene length |
|---|---|---:|---:|
| `gdino_object_floor` | floor | x | 27.8785 |
| `gdino_object_door` | door | z | 21.3139 |
| `gdino_object_wall` | wall | x | 20.1419 |
| `gdino_object_wall_2` | wall | y | 19.2179 |
| `gdino_object_window` | window | z | 16.2287 |
| `gdino_object_bed` | bed | x | 14.7931 |

这个结果把项目从 P0 “只有场景碰撞体能进模拟器”推进到 P1 “语义对象 + bbox proxy 的静态场景能进模拟器”。它仍不代表 dynamic release、真实尺度校准、真实 provider 修复或完整 SimFoundry 复现已经完成。

## 最新推进：2026-07-08 P2 dynamic-readiness gate

在最新 P1 static object scene 上，继续生成 P2 dynamic-readiness sidecar：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_p1_20260707_235133/simulator_assets/simfoundry_dynamic_readiness_p2_20260708_013632/
```

这一步不是把对象改成 dynamic，而是跑 SimFoundry-style 动态释放门禁：

```text
P1 static object scene
  -> tight bbox collider variant
  -> support / penetration gate
  -> dynamic candidate blocker report
  -> sidecar simulator adapters
  -> MuJoCo runtime smoke
```

P2 验收结果：

| 项 | 结果 |
|---|---:|
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
| sidecar body type | `static: 16` |
| adapter ready | 3 / 3 |
| smoke required issues | 0 |
| smoke warnings | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | pass |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
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

P2 关键文件：

```text
dynamic_readiness_report.json
tight_collider_variant/simulator_asset_bundle.tight_collider.json
dynamic_variant/simulator_asset_bundle.dynamic_variant.json
dynamic_variant/dynamic_blocker_report.json
dynamic_variant/dynamic_blocker_report.md
adapters/mujoco/scene.xml
adapters/unity/unity_adapter.json
adapters/isaac/isaac_adapter.json
sim_preflight_report.json
```

正确结论：P2 gate 已经能运行，并且正确拒绝了不安全的 dynamic release。当前仍不是动态场景完成，而是得到了下一步 structural repair / collider refinement 的 blocker queue。

## 后续探索状态

页面下方保留了更早的 P1 static object scene、dynamic-readiness gate 和 provider-shaped structural repair dry-run 历史记录。当前最新可验收进度已经推进到 P2 dynamic-readiness gate：门禁运行成功，但 accepted dynamic 仍为 0；structural repair 和 cousins 仍只作为后续探索证据，不混进本轮完成口径。

关键后续目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/simfoundry_dynamic_readiness_rebuild_20260707_195700/
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/simfoundry_structural_repair_plan_rebuild_20260707_195700/
```

## 当前结论

Video2Mesh 已经能从真实 bedroom4 的 COLMAP Delaunay scene mesh 生成一个 SimFoundry-style `scene_static_collider.obj`，打包成 collider-only simulator bundle，并导出 MuJoCo / Unity / Isaac 三套 adapter。

MuJoCo Python runtime 已真实加载 `scene.xml` 并 step 5 帧通过。这个结果说明第一阶段 static collider scene 已经可以进入仿真器做结构级 smoke test。

它还不代表完成了：

- dynamic object release
- 真实尺度实测校准
- articulated object
- object / scene / task cousins
- policy training / evaluation
- 真实外部 provider 调用

## 输入

使用已有的 bedroom4 mesh 重建结果：

```text
tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply
```

这是场景级 mesh，不依赖新的闭源模型请求，也不使用 API key。

## 输出目录

最初 clean current run 目录为：

```text
exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/
```

最新 collider-only 复跑目录为：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707/
```

核心文件：

```text
manifest.json
simulator_assets/simfoundry_collider_scene/collider_scene_manifest.json
simulator_assets/colliders/scene_static_collider.obj
simulator_assets/simulator_asset_bundle.collider_only.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/mujoco/mujoco_adapter.json
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/physics/sim_preflight_report.json
```

## 运行命令

### 1. 初始化空项目

```bash
PYTHONPATH=. uv run python -m video2mesh.cli init \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --scene-id simfoundry-bedroom4-step1-collider-scene-current-20260707
```

### 2. 从 scene mesh 生成 static collider

```bash
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
```

### 3. 导出三套 simulator adapter

```bash
PYTHONPATH=. uv run python -m video2mesh.cli export-simulator-adapter \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_current_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --format mujoco unity isaac \
  --copy-assets \
  --mode copy
```

### 4. MuJoCo runtime smoke test

```bash
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

## 验收结果

| 项 | 结果 |
|---|---|
| run 目录 | `exports/simfoundry_bedroom4_step1_collider_scene_current_20260707/` |
| 输入 mesh | bedroom4 COLMAP Delaunay `mesh.ply` |
| collider 文件 | `simulator_assets/colliders/scene_static_collider.obj` |
| collider QA | `pass` |
| required issue | 0 |
| warning | collider 生成阶段 0；smoke 阶段 4 个非阻塞 warning |
| 顶点数 | 82,920 |
| 三角面数 | 167,082 |
| simulator bundle | `simulator_asset_bundle.collider_only.json` |
| simulator objects | 0，刻意不引入 object 阶段 |
| static colliders | 1 |
| adapters | MuJoCo / Unity / Isaac 共 3 个 |
| adapter ready | 3 / 3 |
| MuJoCo runtime | `require` 模式真实 load + step 5 帧通过 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |
| smoke status | `runtime_pass_with_warnings` |
| smoke required issue | 0 |

smoke 阶段的 warning 都来自当前没有实测尺度和 up-axis：

- `scale_not_calibrated`
- `up_axis_unknown`

这两个 warning 不阻塞结构级仿真导入目标，因为这一段历史 P0/P1 只要求静态场景能进入模拟器。它们会阻塞后续真实物理尺度、动态刚体和机器人任务评估。

## 当前 asset contract

本轮最小合同是：

```json
{
  "scene_id": "simfoundry-bedroom4-step1-collider-scene-current-20260707",
  "objects": [],
  "static_colliders": [
    {
      "id": "scene_static",
      "role": "static_scene_collider",
      "path": "simulator_assets/colliders/scene_static_collider.obj",
      "body_type": "static",
      "collider": "mesh"
    }
  ],
  "scene_assets": {
    "scene_static_collider_mesh": "simulator_assets/colliders/scene_static_collider.obj"
  }
}
```

它对齐 SimFoundry 的思路：视觉层、碰撞层、物理/语义 sidecar、adapter 要分开；当前只先把碰撞层和 adapter 跑通。

## 为什么这一步先做

SimFoundry 的完整系统目标很大：单段视频到 sim-ready digital twin，再生成 object / scene / task cousins，用于策略训练和评估。直接追完整系统会立刻碰到闭源模型、未开源配置、机器人策略代码和数据集边界。

但对 Video2Mesh 来说，最底层必须先回答一个更硬的问题：

```text
已有 3D scene mesh 能不能变成模拟器可消费的 static collision scene？
```

这一步已经得到肯定结果。它让后续 object collider、scale calibration、dynamic gate、provider repair 都有一个稳定地基。

## 历史 P0 建议记录

以下是 P0 collider-only 通过时的建议记录。当前页面顶部的最新状态已经推进到 P2 dynamic-readiness gate；这段保留为历史上下文，不作为最新验收口径。

当时建议不要直接跳到 policy learning。更合理的顺序是：

1. 做真实 scale calibration，消掉 `scale_not_calibrated` warning。
2. 在不覆盖 P0 基线的前提下，单独推进并复验 P1 static object scene。当前已完成。
3. 继续优化 object collider，用 bbox / convex decomposition / compound primitive 降低互穿。
4. 跑 penetration / support / dynamic-readiness gate。
5. 只有当 gate 发现明确 blocker 时，再接入 provider-shaped structural repair。

当前最新验收已经到 P2：collider-only scene、static object scene 和 dynamic-readiness gate 都已经 rebuilt and simulator-smoked；P2 的 accepted dynamic 仍为 0。后续仍不能跳过真实尺度校准、collider refinement 与 structural repair。

## P0.1: up-axis / scale calibration probe

在 collider-only 基线通过后，下一步先处理仿真坐标合同，而不是直接跳到 object 或 dynamic。最新 timestamped rebuild 目录已经补齐这一层：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rebuild_20260707_195216/
```

本次只写入工程坐标合同：

| 项 | 最新 P0.1 结果 |
|---|---|
| calibration artifact | `simulator_assets/simulator_calibration.json` |
| method | `manual_scale_to_meters` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| up_axis | `y` |
| updated objects | 0，仍是 collider-only |
| estimate physics | `false` |
| normal smoke | `runtime_pass_with_warnings` |
| normal required issue | 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| `up_axis_unknown` | 已消失 |
| strict scale gate | `fail`，2 个 required `scale_not_calibrated` |
| MuJoCo runtime | normal / strict 两种 smoke 都能 load + step 5 帧 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |

最新执行命令：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli calibrate-simulator-assets \
  --project-root /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step1_collider_scene_rebuild_20260707_195216 \
  --bundle /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step1_collider_scene_rebuild_20260707_195216/simulator_assets/simulator_asset_bundle.collider_only.json \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --no-estimate-physics \
  --no-overwrite-physics \
  --notes "P0.1 latest rebuild engineering calibration probe: up_axis is set for simulator adapter smoke; scale_to_meters=1.0 remains unmeasured and must not be treated as production calibration."
```

然后重导出 MuJoCo / Unity / Isaac adapter，并分别写入：

```text
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

这里没有把 `scale_calibrated` 写成 true，因为当前没有真实量尺证据。这个选择让 collider scene 可以继续进入模拟器做结构级验证，同时保留生产级物理仿真的硬门槛。

历史上还保留了一个不覆盖基线的 P0.1 探针目录：

```text
exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707/
```

这一步仍然只用同一个 bedroom4 scene mesh 生成 `scene_static_collider.obj`，然后调用 `calibrate-simulator-assets` 写入 simulator calibration sidecar：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli calibrate-simulator-assets \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --no-estimate-physics \
  --no-overwrite-physics \
  --notes "P0.1 engineering calibration probe: up_axis is set for simulator adapter smoke; scale_to_meters=1.0 remains unmeasured and must not be treated as production calibration."
```

关键点是：这里**只确认 up-axis 和 calibration sidecar 能进入 bundle / adapter / smoke 流程**，没有把尺度伪装成实测值。`simulator_calibration.json` 明确记录：

| 项 | 结果 |
|---|---|
| method | `manual_scale_to_meters` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| up_axis | `y` |
| updated objects | 0，仍是 collider-only |
| estimate physics | `false` |

重导出 MuJoCo / Unity / Isaac adapter 后，普通 smoke 结果为：

| 项 | P0.1 普通 smoke |
|---|---|
| status | `runtime_pass_with_warnings` |
| required issue | 0 |
| warning | 2 |
| warning 类型 | 只剩 `scale_not_calibrated` |
| `up_axis_unknown` | 已消失 |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |

同时又跑了严格生产门禁：

```bash
PYTHONPATH=. uv run --with mujoco --with numpy python -m video2mesh.cli simfoundry-simulator-smoke-test \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --format mujoco unity isaac \
  --require-scale-calibration \
  --mujoco-runtime require \
  --mujoco-steps 5 \
  --output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step1_collider_scene_calibration_probe_20260707/simulator_assets/physics/sim_preflight_report.require_scale_calibration.json \
  --json \
  --fail-on-required
```

严格门禁按预期失败：

| 项 | P0.1 严格 smoke |
|---|---|
| status | `fail` |
| required issue | 2 |
| required issue 类型 | `scale_not_calibrated` |
| MuJoCo runtime | 仍然 load + step 5 帧通过 |

这个结果是有意保留的安全边界：当前场景可以作为结构级 collider simulation 进入 MuJoCo / Unity / Isaac，但生产级真实物理仿真仍必须补实测 scale calibration。

P0.1 证据文件：

```text
simulator_assets/simulator_calibration.json
simulator_assets/simulator_asset_bundle.collider_only.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/physics/sim_preflight_report.up_axis_probe.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

## P0.1 rerun: latest collider-only scene

为避免把旧 probe 目录和最新证据混在一起，又单独跑了一次 collider-only rerun：

```text
exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707/
```

这次仍然只使用 scene mesh，不读语义 object split，不生成 dynamic body，也不调用 provider。流程是：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli init \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707 \
  --scene-id simfoundry-bedroom4-step1-collider-scene-rerun-20260707

PYTHONPATH=. uv run python -m video2mesh.cli prepare-simfoundry-collider-scene \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707 \
  --scene-mesh tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply \
  --collider-format obj \
  --mode copy \
  --min-vertices 1000 \
  --min-triangles 1000 \
  --write-collider-only-bundle \
  --json \
  --fail-on-fail

PYTHONPATH=. uv run python -m video2mesh.cli calibrate-simulator-assets \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --no-estimate-physics \
  --notes "Collider-only rerun P0.1: y-up is declared for simulator import; scale remains an engineering assumption and is not measured."

PYTHONPATH=. uv run python -m video2mesh.cli export-simulator-adapter \
  --project-root exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707 \
  --bundle exports/simfoundry_bedroom4_step1_collider_scene_rerun_20260707/simulator_assets/simulator_asset_bundle.collider_only.json \
  --format mujoco unity isaac \
  --copy-assets \
  --mode copy
```

最新 rerun 验收：

| 项 | 结果 |
|---|---|
| collider QA | `pass` |
| vertex / triangle | 82,920 / 167,082 |
| object count | 0 |
| static collider count | 1 |
| adapter ready | 3 / 3 |
| coordinate up_axis | `y` |
| scale_to_meters | 1.0 |
| scale_calibrated | `false` |
| normal smoke | `runtime_pass_with_warnings` |
| normal required issue | 0 |
| normal warning | 2 个 `scale_not_calibrated` |
| strict scale gate | `fail`，2 个 required `scale_not_calibrated` |
| MuJoCo runtime | 两次 smoke 都能 load + step 5 帧 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |

这说明当前 collider-only scene 已经可以作为结构级仿真输入；同时严格 gate 会阻止它被误标为生产级真实尺度仿真资产。

最新 rerun 证据文件：

```text
simulator_assets/simfoundry_collider_scene/collider_scene_manifest.json
simulator_assets/colliders/scene_static_collider.obj
simulator_assets/simulator_asset_bundle.collider_only.json
simulator_assets/simulator_calibration.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

## P1: static object scene current run

这一节是早期 P1 探索记录；当前最新 P1 验收请以上方 `20260708_014805` timestamped front-to-back rebuild 为准。

在 P0 / P0.1 之后，继续按同一条从前到后的顺序生成静态对象场景。新建目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/
```

这一步接入 bedroom4 的 mesh semantics，把 scene mesh 拆成 semantic object meshes，再导出 simulator bundle、bbox collision proxy 和 MuJoCo / Unity / Isaac adapter。它仍然不释放 dynamic rigid body，不调用 provider，不生成 repair sidecar。

输入：

```text
tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply
tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/semantic_bedroom4_formal_colmap_delaunay_dense_local/mesh_mesh_semantics_local.json
```

运行命令：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli init \
  --project-root exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707 \
  --scene-id simfoundry-bedroom4-step2-static-object-scene-current-20260707

PYTHONPATH=. uv run --with numpy python -m video2mesh.cli prepare-simfoundry-static-object-scene \
  --project-root exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707 \
  --mesh tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply \
  --scene-mesh tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/colmap_delaunay_dense/mesh.ply \
  --semantics tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703/mesh_recon_results/semantic_bedroom4_formal_colmap_delaunay_dense_local/mesh_mesh_semantics_local.json \
  --refresh-object-splits \
  --body-type static \
  --collision-proxy bbox \
  --collider mesh \
  --calibrate \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --calibration-notes "P1 static object scene keeps scale_to_meters=1.0 as an unmeasured engineering assumption; real scale calibration is still required before physics-critical simulation." \
  --format mujoco unity isaac \
  --mode copy \
  --json \
  --fail-on-required \
  --fail-on-empty
```

静态对象场景报告：

| 项 | 结果 |
|---|---|
| status | `ready` |
| semantic object mesh | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxy | 16 / 16 |
| object body type | 16 个全部 `static` |
| dynamic object | 0 |
| estimated physics | 16 个，来源为 bbox/default physics |
| adapter | MuJoCo / Unity / Isaac |
| adapter ready | 3 / 3 |
| static scene report required issue | 0 |

普通 MuJoCo smoke：

| 项 | 结果 |
|---|---|
| status | `runtime_pass_with_warnings` |
| required issue | 0 |
| warning | 2 个 `scale_not_calibrated` |
| object count | 16 |
| foreground count | 10 |
| static collider count | 1 |
| declared / existing object proxy | 16 / 16 |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| MuJoCo freejoint | 0，XML 中没有 `freejoint` |

严格 scale gate 继续按预期失败：

| 项 | 结果 |
|---|---|
| strict report | `simulator_assets/physics/sim_preflight_report.require_scale_calibration.json` |
| status | `fail` |
| required issue | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | 仍然 load + step 5 帧通过 |

这一步证明当前分支已经从“只有 scene collider 能进模拟器”推进到“完整静态对象场景能进模拟器”。但它仍不是 dynamic scene；下一步如果继续吸收 SimFoundry，应先做真实尺度校准、tight collider / penetration gate，再考虑 provider-shaped repair 或 dynamic release。

P1 主要证据文件：

```text
simulator_assets/semantic_object_meshes/semantic_object_meshes.json
simulator_assets/simfoundry_static_object_scene/static_object_scene_report.json
simulator_assets/simfoundry_collider_scene/collider_scene_manifest.json
simulator_assets/simulator_asset_bundle.json
simulator_assets/simulator_calibration.json
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/physics/sim_preflight_report.json
simulator_assets/physics/sim_preflight_report.require_scale_calibration.json
```

P1.1 真实尺度校准 job 已准备，但尚未导入真实量尺：

```text
simulator_assets/scale_calibration_jobs_rebuild_20260707_195700/scale_calibration_job.json
simulator_assets/scale_calibration_jobs_rebuild_20260707_195700/scale_calibration_template.json
simulator_assets/scale_calibration_jobs_rebuild_20260707_195700/scale_calibration_readme.md
simulator_assets/scale_calibration_jobs_rebuild_20260707_195700/run_scale_calibration_example.sh
```

这一步只生成 measurement template，不改 `simulator_asset_bundle.json`，因此当前仍是 `scale_calibrated=false`。候选对象数为 16，包含 foreground object 和 background structure。推荐人工量尺优先级如下：

| object | category | reference axis | scene length | priority |
|---|---|---:|---:|---:|
| `gdino_object_door` | door | z | 21.3139 | 100 |
| `gdino_object_bed` | bed | x | 14.7931 | 95 |
| `gdino_object_floor` | floor | x | 27.8785 | 85 |
| `gdino_object_wall` | wall | x | 20.1419 | 75 |
| `gdino_object_window` | window | z | 16.2287 | 70 |

真正导入前必须填写 `selected_reference.object_id`、`selected_reference.reference_axis` 和 `selected_reference.reference_length_m`。否则严格 scale gate 继续失败，这是正确的安全边界。

## Historical front-to-back static run

为了回应“从前到后一步步来”的复刻方式，当时又重新跑了一组不覆盖旧证据的 P0/P1 目录：

```text
exports/simfoundry_bedroom4_step1_collider_scene_front_to_back_20260707_182816/
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/
```

P0 collider-only run：

| 项 | 结果 |
|---|---|
| source mesh | bedroom4 COLMAP Delaunay `mesh.ply` |
| collider mesh | `simulator_assets/colliders/scene_static_collider.obj` |
| vertex / triangle | 82,920 / 167,082 |
| object count | 0 |
| static collider count | 1 |
| coordinate up_axis | `y` |
| scale_calibrated | `false` |
| adapter ready | 3 / 3 |
| smoke status | `runtime_pass_with_warnings` |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=2`、`ngeom=2`、`nmesh=1` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |

P1 static object scene run：

| 项 | 结果 |
|---|---|
| semantic object mesh | 16 |
| foreground / background | 10 / 6 |
| scene static collider | 1 |
| object bbox proxy | 16 / 16 |
| object body type | 16 个全部 `static` |
| dynamic object | 0 |
| missing mesh object | 0 |
| body type check | `static: 16` |
| collider check | `box: 16` |
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

这组历史探索证据说明：当前分支具备把 bedroom4 从 raw scene mesh 推到 simulator-ready static object scene 的路线。它仍然保留 `scale_calibrated=false`，所以不能被误用成生产级真实尺度物理资产；当前正式验收以上方 2026-07-08 P0/P1/P2 front-to-back run 为准。

## P2/P3: tight collider and dynamic-readiness gate

在 P1 静态对象场景通过后，继续做 SimFoundry-style 的动态释放前门禁。这里仍然不调用 provider，不把对象释放成 dynamic，而是先生成 tighter bbox proxy、penetration/support 诊断和 blocker queue。

输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/simulator_assets/simfoundry_dynamic_readiness_current/
```

运行命令：

```bash
PYTHONPATH=. uv run --with mujoco --with numpy python -m video2mesh.cli prepare-simfoundry-dynamic-readiness \
  --project-root exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707 \
  --bundle exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/simulator_assets/simulator_asset_bundle.json \
  --output-dir exports/simfoundry_bedroom4_step2_static_object_scene_current_20260707/simulator_assets/simfoundry_dynamic_readiness_current \
  --up-axis y \
  --up-direction positive \
  --format mujoco isaac unity \
  --mujoco-runtime require \
  --mujoco-steps 5 \
  --json \
  --fail-on-required
```

Dynamic-readiness 总结：

| 项 | 结果 |
|---|---|
| status | `dynamic_blocked` |
| ok | `true`，门禁自身通过 |
| object count | 16 |
| tight collider updated | 16 / 16 |
| bbox penetration | 42 -> 19 |
| dynamic candidate | 8 |
| accepted dynamic | 0 |
| blocked candidate | 8 |
| unsupported candidate | 6 |
| penetration candidate | 8 |
| unique penetration blocker | 10 |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| dynamic variant | `dynamic_variant_empty` |
| body_type 统计 | 16 个全部 `static` |
| MuJoCo runtime | load + step 5 帧通过 |
| MuJoCo model | `nbody=18`、`ngeom=18`、`nmesh=1` |
| MuJoCo freejoint | 0，XML 中没有 `freejoint` |

Top penetration blockers：

| blocker | 类别 | 影响候选数 | 最大 penetration depth |
|---|---|---:|---:|
| `gdino_object_wall` | wall / background | 5 | 2.334 |
| `gdino_object_door` | door | 4 | 3.960 |
| `gdino_object_nightstand_3` | nightstand | 4 | 1.320 |
| `gdino_object_wall_2` | wall / background | 2 | 2.073 |
| `gdino_object_nightstand` | nightstand | 1 | 1.320 |

Repair queue 前几项：

| object | priority | reasons | penetration count |
|---|---|---|---:|
| `gdino_object_nightstand_3` | `p0_support_and_penetration` | penetration, unsupported | 6 |
| `gdino_object_lamp_3` | `p0_support_and_penetration` | penetration, unsupported | 3 |
| `gdino_object_bed` | `p0_support_and_penetration` | penetration, unsupported | 2 |
| `gdino_object_lamp_4` | `p0_support_and_penetration` | penetration, unsupported | 2 |
| `gdino_object_plant_3` | `p0_support_and_penetration` | penetration, unsupported | 2 |
| `gdino_object_plant_4` | `p0_support_and_penetration` | penetration, unsupported | 1 |
| `gdino_object_nightstand` | `p1_penetration` | penetration | 3 |
| `gdino_object_nightstand_2` | `p1_penetration` | penetration | 2 |

这一步的意义是：当前分支已经有了“动态释放前的安全闸”。它拒绝了所有不安全候选对象，没有写入 `freejoint`，也没有覆盖主静态 bundle。后续如果要继续向 SimFoundry 靠近，应先按 blocker queue 做 structural repair / tighter decomposition / real scale calibration，再重新跑这个 gate。

## Historical front-to-back dynamic-readiness gate

在上一轮 P1 静态场景目录上又单独跑了一次 dynamic-readiness gate：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_dynamic_readiness_front_to_back/
```

命令保持保守：只生成 tight collider variant、dynamic variant sidecar、blocker report 和 adapter smoke，不覆盖主 `simulator_asset_bundle.json`，也不调用 provider。

这轮历史 gate 结果：

| 项 | 结果 |
|---|---|
| status | `dynamic_blocked` |
| gate ok | `true` |
| object count | 16 |
| tight collider updated | 16 |
| bbox penetration | 42 -> 19 |
| dynamic candidates | 8 |
| accepted dynamic | 0 |
| blocked candidates | 8 |
| unsupported candidates | 6 |
| penetration candidates | 8 |
| unique penetration blockers | 10 |
| adapter count | 3 |
| smoke required issue | 0 |
| smoke warning | 2 个 `scale_not_calibrated` |
| main bundle body type | `static: 16` |
| dynamic variant body type | `static: 16` |
| freejoint / dynamic scan | 0 命中 |
| secret scan | 0 命中 |
| MuJoCo runtime | load + step 5 帧通过，`nbody=18`、`ngeom=18`、`nmesh=1` |

Top blockers：

| blocker | category | affected candidates | max penetration depth |
|---|---|---:|---:|
| `gdino_object_wall` | wall | 5 | 2.334 |
| `gdino_object_door` | door | 4 | 3.960 |
| `gdino_object_nightstand_3` | nightstand | 4 | 1.320 |
| `gdino_object_wall_2` | wall | 2 | 2.073 |
| `gdino_object_nightstand` | nightstand | 1 | 1.320 |

Repair queue 前 8 项：

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

这个结果说明当时的 front-to-back P1 目录已经能产出 SimFoundry-style 动态释放前门禁报告；同时门禁正确地拒绝了当前几何里不安全的动态释放。当前最新验收请以上方 2026-07-08 P2 gate 为准；它仍不是 dynamic scene。

P2/P3 证据文件：

```text
simulator_assets/simfoundry_dynamic_readiness_current/dynamic_readiness_report.json
simulator_assets/simfoundry_dynamic_readiness_current/tight_collider_variant/tight_collider_variant_report.json
simulator_assets/simfoundry_dynamic_readiness_current/tight_collider_variant/simulator_asset_bundle.tight_collider.json
simulator_assets/simfoundry_dynamic_readiness_current/dynamic_variant/dynamic_variant_report.json
simulator_assets/simfoundry_dynamic_readiness_current/dynamic_variant/dynamic_blocker_report.json
simulator_assets/simfoundry_dynamic_readiness_current/dynamic_variant/dynamic_blocker_report.md
simulator_assets/simfoundry_dynamic_readiness_current/dynamic_variant/simulator_asset_bundle.dynamic_variant.json
simulator_assets/simfoundry_dynamic_readiness_current/adapters/simulator_adapters.json
simulator_assets/simfoundry_dynamic_readiness_current/adapters/mujoco/scene.xml
simulator_assets/simfoundry_dynamic_readiness_current/sim_preflight_report.json
```

## P4 dry-run: structural repair plan and review request

Dynamic-readiness gate 产出了 blocker queue 后，下一步不是直接调用模型或导入 patch，而是先生成 structural repair plan 和 provider-shaped review request。当前仍然是 dry-run：不调用 provider、不导入 patch、不修改主 bundle、不释放 dynamic。

输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/
```

Repair plan 生成命令：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli prepare-simfoundry-structural-repair-plan \
  --project-root exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333 \
  --bundle /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simulator_asset_bundle.json \
  --blocker-report /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_dynamic_readiness_front_to_back/dynamic_variant/dynamic_blocker_report.json \
  --output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_plan.json \
  --markdown-output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_plan.md \
  --max-objects 8 \
  --provider structural_repair_review_worker \
  --model-provider custom \
  --provider-name Sub2API \
  --base-url https://plbbl.com \
  --wire-api responses \
  --model gpt-5-codex \
  --image-model gpt-image-2 \
  --model-reasoning-effort high \
  --disable-response-storage \
  --auth-env OPENAI_API_KEY \
  --json \
  --fail-on-required \
  --fail-on-empty
```

Review worker dry-run 命令：

```bash
PYTHONPATH=. uv run python -m video2mesh.cli run-simfoundry-structural-review-worker \
  --project-root exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333 \
  --bundle /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simulator_asset_bundle.json \
  --repair-plan /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_plan.json \
  --output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_patch.worker.json \
  --request-output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_request.json \
  --report /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_worker_report.json \
  --markdown-output /Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/simfoundry_bedroom4_step2_static_object_scene_front_to_back_20260707_183333/simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_worker_report.md \
  --max-objects 8 \
  --provider structural_repair_review_worker \
  --model-provider custom \
  --provider-name Sub2API \
  --base-url https://plbbl.com \
  --wire-api responses \
  --model gpt-5-codex \
  --image-model gpt-image-2 \
  --model-reasoning-effort high \
  --disable-response-storage \
  --auth-env OPENAI_API_KEY \
  --no-run-provider \
  --json \
  --fail-on-required
```

Provider contract：

| 项 | 值 |
|---|---|
| provider_name | `Sub2API` |
| model_provider | `custom` |
| base_url | `https://plbbl.com` |
| wire_api | `responses` |
| model | `gpt-5-codex` |
| image_model | `gpt-image-2` |
| reasoning effort | `high` |
| store | `false` |
| auth | 只引用 `OPENAI_API_KEY` 环境变量 |

Repair plan / review worker 结果：

| 项 | 结果 |
|---|---|
| repair plan status | `structural_repair_plan_ready` |
| object repair plans | 8 |
| structural blocker plans | 8 |
| background structural blockers | 3 |
| support repair plans | 6 |
| penetration repair plans | 8 |
| review worker status | `dry_run_request_prepared` |
| provider called | `false` |
| request `store` | `false` |
| request endpoint | `https://plbbl.com/v1/responses` |
| placeholder object patches | 11 |
| import_ready | `false` |
| main bundle overwritten | `false` |
| dynamic_release | `false` |
| body_type after dry-run | 主 bundle 和 dynamic variant 都仍是 16 个 `static` |
| freejoint scan | 0 命中 |
| secret scan | 0 命中 |
| branch test | `tests/test_simfoundry_replica.py` 46 passed |

Repair plan 中的 object queue：

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

P4 dry-run 证据文件：

```text
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_plan.json
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_plan.md
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_request.json
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_patch.worker.json
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_worker_report.json
simulator_assets/simfoundry_structural_repair_plan_front_to_back/structural_repair_review_worker_report.md
```

## P4.1 manual/local structural repair import sidecar

在 dry-run contract 之后，又做了一次不调用 provider 的本地导入验证。这个 patch 来源是已有 tight bbox 变体，不是 Sub2API / gpt-5-codex / gpt-image-2 输出；它只用于验证 structural repair import pipeline、sidecar bundle 和 adapter/smoke 闭环。

输入 patch：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/simfoundry_structural_repair_plan_rebuild_20260707_195700/structural_repair_review_patch.manual_local_tight_bbox.json
```

导入输出目录：

```text
exports/simfoundry_bedroom4_step2_static_object_scene_rebuild_20260707_195700/simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/
```

导入结果：

| 项 | 结果 |
|---|---:|
| import status | `structural_repair_imported` |
| object patches | 9 |
| applied patches | 9 |
| skipped patches | 0 |
| object count | 16 |
| static collider count | 1 |
| adapter count | 3 |
| required issue | 0 |
| warning | 0 |
| main bundle overwritten | `false` |
| provider called | `false` |
| dynamic release | `false` |

sidecar smoke：

| 项 | 结果 |
|---|---:|
| smoke status | `runtime_pass_with_warnings` |
| adapter ready | 3 / 3 |
| object collision proxies | 16 / 16 |
| body type | `static: 16` |
| collider shape | `box: 16` |
| MuJoCo runtime | pass |
| MuJoCo steps | 5 |
| MuJoCo nbody / ngeom / nmesh | 18 / 18 / 1 |
| required issue | 0 |
| warning | 2 个 `scale_not_calibrated` |

dynamic-readiness 对比：

| 指标 | baseline | manual/local import 后 |
|---|---:|---:|
| status | `dynamic_blocked` | `dynamic_blocked` |
| object count | 16 | 16 |
| tight updated | 16 | 7 |
| penetration before tight variant | 42 | 28 |
| penetration after tight variant | 19 | 19 |
| dynamic candidates | 8 | 8 |
| accepted dynamic | 0 | 0 |
| blocked candidates | 8 | 8 |
| unsupported candidates | 6 | 6 |
| penetration candidates | 8 | 8 |
| unique penetration blockers | 10 | 10 |
| smoke required issue | 0 | 0 |

这个结果说明 manual/local sidecar 能被仿真器加载，但还没有解决动态释放 blocker：它降低了 tight-variant 前的 penetration 计数，最终 tight 后仍停在 19，accepted dynamic 仍为 0。因此它是一个可验收的 import/smoke 进展，不是 dynamic scene 完成。

P4.1 证据文件：

```text
simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/structural_repair_import_manifest.json
simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/simulator_asset_bundle.structural_repair.json
simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/adapters/simulator_adapters.json
simulator_assets/simfoundry_structural_repair_import_manual_local_20260707_195700/sim_preflight_report.json
simulator_assets/simfoundry_dynamic_readiness_after_manual_local_repair_20260707_195700/dynamic_readiness_report.json
```
