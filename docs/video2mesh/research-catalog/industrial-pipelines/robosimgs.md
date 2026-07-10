---
title: RoboSimGS 调研与 mil8 部署判断
id: video2mesh-industrial-pipelines-robosimgs
category: 调研目录
visibility: public
summary: 调研 RoboSimGS 的 Real2Sim2Real 机器人数据生成管线、公开代码边界、mil8 现有环境状态，以及它能否接入 Video2Mesh 的 visual/collider/physics sidecar 资产合同。
tags:
  - 工业资产管线
  - Research Catalog
  - RoboSimGS
  - Real2Sim2Real
  - 3DGS
  - Robotics
---

# RoboSimGS 调研与 mil8 部署判断

检查日期：2026-07-11

## 一句话结论

RoboSimGS 值得继续跟，因为它和 SimFoundry 一样采用 **3DGS 负责视觉、mesh primitives 负责物理交互、MLLM 辅助补物理/关节属性、仿真生成机器人训练数据** 的混合资产思路。

但截至这次检查，RoboSimGS **还不是 mil8 上可直接一键部署的项目**：

- 官方 README 的 Installation 仍写着正在补充。
- GitHub 仓库放出了核心脚本、轻量资产、articulation/physics estimation 和 data generation 示例，但根 `requirements.txt` 是作者本机 freeze，包含多个不可直接复用的本地 editable 路径。
- `mil8` 已有源码 checkout，但没有可直接运行的 RoboSimGS conda 环境；现有 `max` / `3dgs` / base Python 均不适合作为立即可跑基底。
- 官方示例 HuggingFace 数据只有 3 个 3DGS PLY，能补背景 splat，不补 Genesis/Lerobot/pybullet，也不补 README 缺失的 camera pose alignment 代码。

因此当前判断是：**可以部署到“源码审计 + 依赖规划 + 小模块 smoke”的阶段；还不能声称跑通 simulated data generation，更不能声称可用于 policy training 或 sim2real。**

![RoboSimGS pipeline](../assets/robosimgs-pipeline.png "RoboSimGS 官方 pipeline 图：真实场景/物体重建、3DGS 背景、mesh 交互对象、物理属性/关节估计、仿真数据生成与策略训练。")

## 资料入口

| 项 | 链接 / 状态 |
|---|---|
| Project page | https://robosimgs.github.io/ |
| GitHub | https://github.com/Maxwell-Zhao/RoboSimGS |
| arXiv | https://arxiv.org/abs/2510.10637 |
| HuggingFace dataset | https://huggingface.co/datasets/haoyu1234/robosimgs |
| Paper title | High-Fidelity Simulated Data Generation for Real-World Zero-Shot Robotic Manipulation Learning with Gaussian Splatting |
| arXiv status | v1 submitted on 2025-10-12 |
| Local source inspected | `/tmp/RoboSimGS`, commit `3f767f53a27015719c001b486e7c9cfc52276031` |
| mil8 source inspected | `mil8:/data/zyx/workspace/robosimgs/RoboSimGS`, commit `3f767f53a27015719c001b486e7c9cfc52276031` |

注意：项目页当前 `Paper` 按钮抽取到的是 `https://arxiv.org/pdf/2508.08896`，README 和 arXiv 可访问页面对应的是 `2510.10637`。本文按 GitHub README 与 arXiv `2510.10637` 记录，并把这个链接不一致视作官方页面尚未完全整理好的证据之一。

## 它解决什么问题

RoboSimGS 的问题设定是机器人学习的数据瓶颈：真实机器人采集贵，普通仿真又有视觉、物理属性和物体交互 gap。它提出一个 Real2Sim2Real 框架，把多视角真实图像转成可交互仿真环境，再在仿真里批量生成机器人操作数据，最后用于真实机器人零样本或少样本迁移。

它不是单纯的 3DGS viewer，也不是单纯的 mesh reconstruction。它的核心是混合表示：

```text
multi-view real-world images
  -> 3DGS background reconstruction
  -> object mesh reconstruction
  -> MLLM articulation / physics estimation
  -> world coordinate frame alignment
  -> Genesis simulation and data generation
  -> policy training with IDP3 / deployment with Lerobot
```

在论文摘要和代码 README 中，RoboSimGS 明确把 3DGS 用作 photorealistic appearance，把 mesh primitives 用作 interactive objects 的物理仿真基础。这个分工和 Video2Mesh 当前的 layered asset contract 是一致的：visual layer 不能替代 collider / physics layer。

## 公开代码边界

当前 GitHub 仓库主要分四块：

| 目录 | 作用 | 当前可用性 |
|---|---|---|
| `Gaussians/` | 加载和渲染 3DGS PLY，依赖 `diff_gaussian_rasterization` | 有源码，但默认路径仍含作者本机路径，例如 `/home/haoyu/code/GSim/...` |
| `DataGeneration/` | Genesis 场景、SO-100 机械臂、banana/box 示例任务、采集图像和 action/qpos | 有脚本和轻量资产，但依赖 Genesis；`pick_banana.py` 还从不存在的 `tasks.base_task` 导入 |
| `Articulation/` | GLB 分割、hinge 检测、URDF 生成、物理属性估计、SAM/CLIP/GPT 辅助 | 有 `openbox` 示例输出；GPT 调用使用旧 OpenAI ChatCompletion 风格 |
| `third_party/` | 两份 Gaussian rasterization CUDA extension | 有源码，可作为本地编译来源 |

仓库自带轻量资产：

| 资产 | 路径 |
|---|---|
| SO-100 机械臂 | `assets/so100/urdf/so_arm100.urdf`, `assets/so100/urdf/so_arm100.xml`, `assets/so100/assets/*.stl` |
| banana/box 物体 | `assets/objects/banana/*`, `assets/objects/box/*` |
| articulation 示例 | `Articulation/openbox.glb`, `Articulation/openbox_output/` |
| pipeline 图和 demo | `imgs/pipeline.png`, `imgs/demo.gif` |

HuggingFace 示例数据核验结果：

| 文件 | 大小 |
|---|---:|
| `single-view-scene/splat-transform.ply` | 260,913,900 bytes |
| `mult-view-scene/left-transform.ply` | 223,453,499 bytes |
| `mult-view-scene/right-transform.ply` | 210,732,091 bytes |

这些 PLY 正好对应代码里的默认路径：

```text
exports/single-view-scene/splat-transform.ply
exports/mult-view-scene/left-transform.ply
exports/mult-view-scene/right-transform.ply
```

但多视角 path 还会继续读取 Nerfstudio transform 目录：

```text
outputs/left-processed/splatfacto/2025-08-26_112829/dataparser_transforms.json
outputs/right-processed/splatfacto/2025-08-26_105600/dataparser_transforms.json
images/left-processed/transforms.json
images/right-processed/transforms.json
```

也就是说，下载 HuggingFace PLY 只能补上背景 splat 文件，不能自动补齐完整 data generation 所需的相机对齐数据。

## 与 Video2Mesh 的关系

RoboSimGS 对 Video2Mesh 的价值不在于替换 COLMAP / GraphDECO / mesh reconstruction，而在于提供一个机器人数据生成侧的目标合同：

```text
Video2Mesh scene outputs
  -> 3DGS background visual layer
  -> object-local mesh / GLB
  -> physics sidecar: mass, friction, density, stiffness
  -> articulation sidecar: hinge / slider / joint limits
  -> Genesis or MuJoCo / Isaac task scene
  -> policy dataset frames, actions, qpos
```

当前可以吸收的点：

| RoboSimGS 设计 | Video2Mesh 可吸收方式 |
|---|---|
| 3DGS 背景 + mesh 交互对象 | 延续 `3DGS visual proxy + GLB/collider object proxy` 分层，不把 3DGS 当 collider |
| MLLM 估计物理属性 | 作为 `object_asset.json` / physics sidecar 的候选自动填充器 |
| MLLM 推断 articulated joint | 对柜门、抽屉、盒盖这类对象补 hinge / slider sidecar |
| Genesis 数据生成 | 未来作为机器人任务数据生成后端之一，但不能直接吃当前 bedroom_4 场景 |
| SO-100 / Lerobot / IDP3 | 适合机器人学习方向，不是 Video2Mesh P0 场景资产验收项 |

不应该混淆的边界：

- RoboSimGS 不负责从任意房间视频自动输出高质量 scene mesh collider。
- RoboSimGS 的 object reconstruction README 依赖 iPhone 16 Pro 的 AR Code app 扫描物体，不是纯从 `bedroom_4` 视频自动恢复每个对象。
- RoboSimGS 的 camera pose alignment 代码仍未发布，不能把它当成完整开放 pipeline。
- RoboSimGS 的 policy training / sim2real 依赖 IDP3 和 Lerobot，不属于当前 Video2Mesh “资产六件套”验收范围。

## mil8 环境审计

远端机器：`mil8`

| 项 | 实测 |
|---|---|
| 时间 | 2026-07-11 04:42 CST |
| GPU | 8 x NVIDIA GeForce RTX 3090, 24GB |
| GPU 利用率 | 8 张均 0% |
| driver / CUDA | NVIDIA-SMI 530.30.02, CUDA 12.1 |
| `/` | 440G total, 331-332G used, 86G available |
| `/data` | 3.5T total, 3.3T used, 56G available, 99% |
| RoboSimGS checkout | `/data/zyx/workspace/robosimgs/RoboSimGS` |
| checkout commit | `3f767f53a27015719c001b486e7c9cfc52276031` |
| source dirty state | 仅 Python `__pycache__` 未跟踪 |
| network turbo | 未看到 `/etc/network_turbo` |
| compiler | `gcc 9.5.0`; `nvcc` 未在当前 shell 探测到 |

磁盘判断：`/data` 太满，不适合继续铺大模型和大数据；如果继续部署，应该把 conda env、pip cache、HF cache 放在根盘侧，例如 `/root/autodl-tmp/robosimgs_envs` 和 `/root/autodl-tmp/hf_cache`，源码和小日志可继续放 `/data/zyx/workspace/robosimgs`。

## 现有 Python 环境检查

这次没有找到可以直接跑 RoboSimGS 的现成环境。

| Python | 状态 |
|---|---|
| `/data/anaconda3/envs/max/bin/python` | Python 3.10 可启动；`torch` 查到存在，但 import torch 约 49.5 秒仍未稳定完成；缺 `genesis`, `gsplat`, `diff_gaussian_rasterization`, `open3d`, `lerobot`, `pybullet` |
| `/data/anaconda3/envs/3dgs/bin/python` | Python 3.9；静态探测显示有 `torch`, `gsplat`, `diff_gaussian_rasterization`, `open3d`, `trimesh`, `cv2`, `scipy`，但缺 `genesis`, `lerobot`, `pybullet`, `nerfstudio`；实际 `python -S` 和 smoke 命令 20-40 秒均超时 |
| `/data/anaconda3/bin/python` | Python 3.11；有 `torch`, `gsplat`, `open3d`, `trimesh`, `cv2`, `scipy`，缺 `genesis`, `diff_gaussian_rasterization`, `nerfstudio`, `lerobot`, `pybullet`；smoke 命令超时 |
| `/usr/bin/python3` | Python 3.7；缺全部关键包 |

部署审计日志：

```text
mil8:/data/zyx/workspace/robosimgs/deploy_audit_20260711/smoke.log
mil8:/data/zyx/workspace/robosimgs/deploy_audit_20260711/smoke_fast.log
```

smoke 尝试结果：

```text
/data/anaconda3/envs/3dgs/bin/python -u -c "import torch; import diff_gaussian_rasterization"
  -> EXIT=124

/data/anaconda3/envs/3dgs/bin/python -u -c "find_spec('genesis')..."
  -> EXIT=124

/data/anaconda3/envs/3dgs/bin/python -u -c "import Gaussians.render"
  -> EXIT=124

/data/anaconda3/envs/3dgs/bin/python -u -c "import DataGeneration.pick_banana"
  -> EXIT=124

/data/anaconda3/envs/3dgs/bin/python -u DataGeneration/pick_banana.py --start 0 --num_steps 1 ...
  -> EXIT=124
```

`EXIT=124` 来自 timeout。这里不能写成“依赖装好了但样例失败”；更准确地说，是远端现有 Python 环境启动/导入层面已经不够稳定，不能作为 RoboSimGS 部署通过证据。

## 源码层阻塞点

即使重建环境，仍需要处理以下源码/数据边界：

| 阻塞点 | 证据 | 影响 |
|---|---|---|
| README 安装说明未完成 | README Installation 段写正在补充 | 需要自己整理最小依赖集 |
| 根 requirements 不可直接安装 | 含 `/media/haoyu/...`, `/home/haoyu/...` editable 路径 | 不能 `pip install -r requirements.txt` |
| `pick_banana.py` 导入路径错误 | `from tasks.base_task import DataCollector`，仓库实际为 `DataGeneration/base_task.py` | 官方 README 数据生成命令会先卡在入口修复 |
| `--use_gs` 不是标准 bool flag | `parser.add_argument("--use_gs", default=True)` | 传 `--use_gs False` 仍可能 truthy，需要改成 `BooleanOptionalAction` 或 store_true/store_false |
| Genesis 缺失 | 现有环境均缺 `genesis` | 数据生成主链路无法跑 |
| Lerobot / IDP3 缺失 | 现有环境缺 `lerobot`; requirements 依赖作者本地 iDP3 | policy training / sim2real 不可验收 |
| camera pose alignment 未发布 | README 标为 TODO | 多视角数据生成无法完整复刻 |
| 3DGS 示例数据未在 mil8 checkout 下落位 | HuggingFace 有 PLY，但远端 checkout 未见 `exports/single-view-scene` / `exports/mult-view-scene` | 即使装好依赖，`--use_gs True` 也会缺文件 |
| MLLM 代码使用旧 OpenAI SDK 风格 | `openai.ChatCompletion.create` | 接入 Sub2API/gpt-5-codex 要改 provider wrapper，且不能写入明文 key |

## 可执行部署路线

如果继续推进，建议不要复用 `max` 或 `3dgs` 环境，重新建一个窄环境，先跑最小 Genesis + no-GS 数据生成，再补 3DGS 背景。

### P0：no-GS Genesis smoke

目标：先证明 SO-100 + banana/box 任务能在 Genesis 里跑，输出仿真 RGB、action、qpos。暂不加载 3DGS 背景。

关键动作：

```text
1. 在根盘侧新建隔离 env，避免继续占 /data。
2. 安装 torch/cu121、genesis-world、pybullet、trimesh、opencv-python、scipy、numpy。
3. 给 `DataGeneration/pick_banana.py` 加兼容导入 shim：优先 `DataGeneration.base_task`，fallback `tasks.base_task`。
4. 把 `--use_gs` 改成可靠 bool，或 smoke 时直接从代码构造 `PickBanana(use_gs=False)`。
5. 跑 `num_steps=1` 的短采集，检查 `collected_data` 是否产生 frame/action/qpos。
```

这一步通过后，只能说明仿真和机器人任务基础可用，不能说明 3DGS 背景融合可用。

### P1：3DGS 背景 smoke

目标：证明 RoboSimGS 自带的 `diff_gaussian_rasterization` 能编译/导入，并能读取 HuggingFace PLY 做 single-view 背景渲染。

关键动作：

```text
1. 下载 HuggingFace 三个 PLY 到 `exports/single-view-scene/` 和 `exports/mult-view-scene/`。
2. 编译 `third_party/diff-gaussian-rasterization-w-pose-main`。
3. 先跑 `Gaussians.render.Renderer.update_gaussian_data('exports/single-view-scene/splat-transform.ply')`。
4. 再跑 `PickBanana(use_gs=True, single_view=True, num_steps=1)`。
```

这一步通过后，可以说“single-view 3DGS 背景 + Genesis 前景合成 smoke 通过”。多视角仍需要额外相机 transform 数据。

### P2：多视角和相机对齐

目标：补齐 README 里尚未开源或尚未文档化的 camera pose alignment。

对 Video2Mesh 来说，不建议直接等 RoboSimGS 官方补齐，而是可以尝试把 Video2Mesh 已有相机轨迹转成 RoboSimGS 期望的 `dataparser_transforms.json` / `transforms.json` 合同。但这属于适配开发，不是原仓库部署。

### P3：MLLM 物理/关节 sidecar

目标：把 `Articulation/` 作为独立工具，给 Video2Mesh 单体 GLB 估计 material、mass/friction/stiffness、hinge/slider joint。

这一步需要把旧 `openai.ChatCompletion.create` 包装成 Responses API / Sub2API provider，并坚持：

```text
model_provider = "custom"
model = "gpt-5-codex"
model_reasoning_effort = "high"
disable_response_storage = true
```

但文件里只应读取 `OPENAI_API_KEY` 环境变量，不能写入明文 key。

## 接入建议

短期不要把 RoboSimGS 放进 Video2Mesh 主 pipeline。更稳的接法是作为 `industrial-pipelines` 参考项目和后续机器人数据生成后端：

| 优先级 | 工作 | 原因 |
|---|---|---|
| P0 | 写一个 `tools/run_robosimgs_smoke.sh`，只做 env check + no-GS Genesis smoke | 能最快判断 mil8 能不能跑 Genesis |
| P1 | 下载 HuggingFace single-view PLY，跑 3DGS background smoke | 验证视觉合成，不碰多视角相机坑 |
| P2 | 把 Video2Mesh object GLB 转给 `Articulation/` 生成 URDF/physics sidecar | 与现有 simulator asset bundle 最贴近 |
| P3 | 研究 Genesis backend 是否可替代当前 MuJoCo/Isaac adapter 的部分 smoke | 服务机器人数据生成，而不是替代 collider asset |
| P4 | policy training / Lerobot / IDP3 | 依赖重、磁盘和数据大，等资产层稳定后再说 |

当前最务实的结论是：**能部署，但不是今天用现有环境直接跑通；需要重新建隔离环境、修 README 入口、补 HuggingFace PLY 和相机合同。** 如果只为 Video2Mesh 当前目标，优先借鉴它的分层资产思想和 MLLM physics/articulation sidecar，不要把机器人 policy training 当成本阶段目标。
