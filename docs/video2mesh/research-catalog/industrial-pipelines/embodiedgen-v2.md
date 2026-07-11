---
title: EmbodiedGen V2 调研
id: video2mesh-industrial-pipelines-embodiedgen-v2
category: 调研目录
visibility: public
summary: 调研 Horizon Robotics / WuwenAI 的 EmbodiedGen V2：从任务描述、图片和资产生成 sim-ready 3D 世界，支持跨仿真器导出、Vibe Coding 编辑和机器人策略训练。
tags:
  - 工业资产管线
  - EmbodiedGen
  - Simulation
  - Vibe Coding
  - Robotics
  - Research Catalog
---

# EmbodiedGen V2 调研

EmbodiedGen V2 是 Horizon Robotics / WuwenAI 在 2026-07 发布的 sim-ready 3D world engine。微信文章《地平线把 "VibeCoding" 搬进 3D 物理世界：说一句话，拍一张照片就能生成可训练机器人的 3D 场景，让机器人训练快 8 倍，仿真成功率飙到 79.8%》指向的核心项目就是这篇论文和官方项目页。

![EmbodiedGen V2 与 Video2Mesh 的资产合同](../assets/embodiedgen-v2-video2mesh-contract.svg "EmbodiedGen V2 对 Video2Mesh 最值得借鉴的是 sim-ready 分层资产合同、验证闭环和跨仿真器导出，而不是替代扫描重建")

## 链接

- 微信入口: https://mp.weixin.qq.com/s/ss2zoYr2hVpJfGlwufiMwQ?scene=1
- Project page: https://horizonrobotics.github.io/EmbodiedGen/
- Code: https://github.com/HorizonRobotics/EmbodiedGen
- Paper: https://arxiv.org/abs/2607.07459
- arXiv HTML: https://arxiv.org/html/2607.07459v1
- RoboVerse real asset example: https://roboverse.wiki/metasim/get_started/quick_start/14_real_asset
- RoboVerse embodied layout example: https://roboverse.wiki/metasim/get_started/quick_start/16_embodiedgen_layout

## 基本信息

| 项 | 内容 |
|---|---|
| 论文标题 | EmbodiedGen V2: An Agentic, Simulation-Ready 3D World Engine for Embodied AI |
| arXiv | 2607.07459v1, submitted on 2026-07-08 |
| 机构 | Horizon Robotics, WuwenAI |
| 作者 | Xinjie Wang, Liu Liu, Taojun Ding, Andrew Choi, Chaodong Huang, Mengao Zhao, Ziang Li, Jackson Jiang, Chunlei Yu, Shengxiang Liu, Wei Xu, Zhizhong Su |
| 项目目标 | 生成可执行、可编辑、可复用、可跨仿真器部署的 sim-ready 3D 环境 |
| 输入形态 | 自然语言任务、图片条件、3D asset seed、场景图、multi-room layout、对话式编辑指令 |
| 输出形态 | sim-ready object asset、affordance、task-driven world、multi-room scene、URDF/MJCF/USD 等仿真器包 |
| 对 Video2Mesh 的定位 | 可借鉴的 simulator asset contract、验证闭环和世界编辑接口；不是视频扫描到 3DGS/mesh 的替代链路 |

## 一句话结论

EmbodiedGen V2 不是传统意义的 video-to-mesh 或 3DGS 重建模型，而是一个 **从生成资产到可训练仿真世界的工程系统**。它最有价值的地方在于把“视觉看起来像”推进到“机器人策略能在物理仿真里训练和迁移”：资产必须有 visual mesh、collision mesh、惯性参数、材质、affordance、稳定抓取点、坐标和跨仿真器格式。

对 Video2Mesh 来说，它不应替换当前的 `视频帧 -> COLMAP -> GraphDECO 3DGS -> scene mesh/collider -> semantic sidecar -> simulator bundle` 主链路。更实际的接入方式是借鉴 EmbodiedGen V2 的 **sim-ready 资产合同、generate-verify-retry 质量门、URDF/MJCF/USD 导出和 Vibe Coding 状态编辑**，把我们已有的扫描资产包装成更像机器人训练数据的可执行世界。

## 摘要要点

论文把 sim-ready 定义为：一个环境可以直接被物理仿真消费，不需要人工补物理属性、修 collision、调整坐标、重写导出脚本或手动验证交互。EmbodiedGen V2 因此不是单一模型，而是一套分层 pipeline：

```text
prompt / image / task
  -> sim-ready object asset generation
  -> mesh fixing / convex decomposition / physical recovery
  -> affordance autolabeling and grasp validation
  -> scene graph and task-driven interactive world composition
  -> large-scale multi-room / whole-house scene generation
  -> stateful Vibe Coding edits
  -> URDF / MJCF / USD / simulator-specific packages
  -> policy training, evaluation, and sim-to-real deployment
```

论文报告的关键结果包括：

| 评估项 | 结果 |
|---|---:|
| sim-ready asset human acceptance | 96.5% |
| collision success | 98.6% |
| full asset pipeline runtime | 2.6 ± 0.4 min / asset |
| task-driven interactive worlds 可直接用于下游仿真 | 83.3% |
| fully online world generation runtime | 47.7 ± 5.4 min / world |
| online RL simulation success | 9.7% -> 79.8% |
| real robot task success | 21.7% -> 75.0% |
| OOD success, N=1 -> N=50 generated scenes | 53.2% -> 77.9% |
| ID-OOD gap | 41.1 -> 2.6 percentage points |
| cube stacking real-world success | 43.1% -> 88.9% across 144 trials |

微信文章里“机器人训练快 8 倍”更准确地说，对应论文消融中 **去掉 mesh fixing 后资产处理耗时从 2.6 ± 0.4 min 增加到 21.3 ± 22.8 min，约 8 倍**；这不是“所有训练时间直接缩短 8 倍”，而是 sim-ready asset pipeline 的一个工程效率结果。

## 方法拆解

### 1. Sim-ready 3D asset generation

EmbodiedGen V2 的第一层是把生成式 3D 输出修成仿真能用的 object asset。论文强调 simulation compatibility 不是最后随手 export 一下，而是在 candidate screening、3D generation、physical recovery 里反复执行质量约束。

| 子环节 | 作用 | 产物 |
|---|---|---|
| 条件生成 | 从 text / image / seed 生成初始 3D object | raw mesh / visual asset |
| mesh fixing | 修复洞、非流形、异常面、尺度和坐标问题 | cleaner visual mesh |
| convex decomposition | 为物理引擎准备 collision proxy | collision mesh / convex parts |
| physical recovery | 写入 mass、friction、inertia、material 等物理属性 | physics metadata |
| hierarchical quality checker | 检查感知质量、几何可用性、仿真接触稳定性 | accept / retry / reject |
| URDF canonical package | 把 visual/collision/inertial/metadata 放进统一中间表示 | URDF asset package |

论文在 200 个 held-out assets 上做消融，full pipeline 达到 96.5% human acceptance、98.6% collision success。Human Acceptance 关注输入一致性、几何合理性、不可见面补全和作为仿真资产的可用性；Collision Success 用 SAPIEN 中 Franka Panda top-down grasp-and-lift trials 评估，4 个 yaw angle trial 中能稳定抬起才算成功。

### 2. Affordance autolabeling

第二层是把物体从“可碰撞”推进到“可交互”。论文的 affordance pipeline 会做 part segmentation、part semantic annotation、grasp coverage 和 SAPIEN grasp validation。每个 retained grasp 都要经过仿真验证，如果物体相对 gripper 滑移超过 5 cm 或 30 degrees 就丢弃。

| 组件 | 输入 | 输出 | 角色 |
|---|---|---|---|
| part segmentation | object mesh / visual evidence | part masks / segments | 找出把手、门板、容器等可交互部件 |
| VLM semantic annotation | part candidates + prompt | part label / affordance | 给部件语义和功能 |
| VLM-guided merging | fragmented part labels | merged functional part | 减少过分割和重复部件 |
| grasp planner | object/part geometry | grasp candidates | 为机器人操作生成候选抓取点 |
| SAPIEN validation | grasp candidates + physics asset | stable grasps | 筛掉接触不稳定的候选 |

对 Video2Mesh 来说，这层可以对应 `semantic_object_meshes.json`、`semantic_object_glbs.json` 之后的 physics sidecar：除了 label/object_id，还要逐步补 `affordance`、`grasp_pose`、`joint_type`、`mass`、`friction`、`confidence` 和 `source`。

### 3. Task-driven interactive worlds

第三层把任务描述变成可以加载的交互场景。论文采用“背景 + 任务相关 interactive assets”的分解，类似电影绿幕：背景不一定每次重生成，关键是任务相关物体必须能被物理引擎接触、抓取和移动。

```text
natural-language task
  -> LLM parses task into Scene Graph
  -> background synthesis / retrieval
  -> required object asset generation or reuse
  -> BFS-based spatial placement
  -> SAPIEN gravity settling
  -> direct-load interactive world layout
```

论文的 150 个 interactive worlds 覆盖了 778 个 sim-ready object asset instances、128 个 object categories，平均每个世界 5.19 个 interactive assets。最终 83.3% 的世界被人工检查为可直接用于下游仿真，不需要手工修改。失败主要来自 object-scale mismatch、local geometry defects 和 imperfect initial spatial placement。

### 4. Large-scale multi-room scenes

EmbodiedGen V2 相比 V1 的另一个升级是 large-scale world generation。论文指出 V1 更像 panorama-back-projected single-mesh background，有限 camera translation 会限制导航和移动操作；V2 则生成 structured multi-room / whole-house scenes，显式保留 room topology、traversable openings 和 individually addressable furniture。

多房间场景不是把所有房间糊成一个单 mesh，而是分三步：

| 阶段 | 说明 |
|---|---|
| semantic planning | 生成房间类型、连接关系、家具类别、复杂度等级 |
| geometric solving | 根据房间拓扑、门洞、可通行区域和物体碰撞关系求布局 |
| simulator-agnostic canonicalization | 分解 instance、生成 collision proxy、坐标归一化、导出 URDF/USD |

复杂度等级包含 Minimalist、Simple、Medium、Detail，用来控制家具和 clutter 密度。这个设计对 Video2Mesh 有启发：房间扫描资产也应该按 room / floor / object / traversable opening 分层，而不是只输出一个整房间 GLB。

### 5. Vibe Coding for 3D world editing

论文使用 Vibe Coding 指代“通过自然语言对话迭代生成和编辑 sim-ready 3D 世界”，但它不是纯聊天式改场景。关键是 agent 只负责解析意图，真正的约束检查和执行由 deterministic, physics-aware skill backends 完成。

论文中的世界状态可以概括为：

```text
S_t = (G_t, A_t, P_t, H_t)

G_t: typed Scene Graph
A_t: sim-ready assets
P_t: asset 6-DoF poses
H_t: dialogue and skill-invocation history
```

每条编辑指令走 `Parse -> Ground -> Invoke -> Commit`。成功时只提交 bounded state delta，失败时返回结构化诊断，不污染当前世界状态。技能抽象分为四类：

| 抽象 | 责任 | 对 Video2Mesh 的可迁移设计 |
|---|---|---|
| Asset grounding | 把用户说的 object / room / asset 解析到 instance_key、room_id、asset_id | 文档/网页 viewer 中选中物体后写回 object_id 和 mesh/glb 路径 |
| World composition | 生成/放置/替换物体，维护空间关系 | 支持 `ON` / `BESIDE` / `IN` / free-floor placement |
| Stateful editing | 每次编辑是 bounded delta，可撤销、可审计 | simulator bundle 的 patch log 和 version history |
| Execution validation | 检查碰撞、支撑、稳定性、可导出性 | 生成后跑 collision preflight、raycast、ground probe、physics smoke |

这个部分和本地 Codex 工作流最接近：Video2Mesh 后续也可以把编辑器里的“把床头柜换成带抽屉的可交互模型”“给椅子加质量和摩擦”“把这个物体导出 MuJoCo”等操作做成可审计 skill，而不是让大模型直接改 JSON。

## 跨仿真器资产格式

EmbodiedGen V2 采用 URDF 作为统一中间表示，再转换到 XML/MJCF 和 USD。论文明确提到的部署目标包括 SAPIEN、PyBullet/Bullet、Isaac Gym、MuJoCo、Genesis、Isaac Sim。格式转换要处理：

| 资产层 | 需要保持的合同 |
|---|---|
| visual geometry | 给人看、给相机渲染，不一定适合作 collision |
| collision geometry | 简化、凸分解、稳定接触、可快速物理求解 |
| local transforms | visual/collision/inertial frame 对齐 |
| inertial parameters | mass、center of mass、inertia tensor |
| material mapping | friction、restitution、density 或引擎等价参数 |
| auxiliary metadata | affordance、grasp candidates、joint、semantic labels、source confidence |

这正好贴合 Video2Mesh 的长期目标：3DGS 或高质量 mesh 负责视觉，mesh collider / primitive proxy 负责碰撞，semantic/physics sidecar 负责 object-level 语义和物理，引擎 adapter 负责 Web / Unity / MuJoCo / Isaac。

## 与 Video2Mesh 的关系

### 官方 EmbodiedGen V2 与本地 Video2Mesh 的边界

| 维度 | EmbodiedGen V2 | Video2Mesh 当前路线 |
|---|---|---|
| 起点 | prompt、image、task、生成式 object asset、scene graph | 扫描视频帧、相机、COLMAP/GraphDECO 资产 |
| 核心目标 | 生成可执行、可编辑、可训练的 sim-ready world | 从真实视频生成分层可交互资产包 |
| 视觉层 | object mesh / background / generated world | 3DGS visual proxy、scene GLB、object GLB |
| 几何层 | mesh fixing、convex decomposition、physics settling | COLMAP dense/Delaunay、Poisson/Open3D、semantic mesh transfer |
| 语义层 | affordance、part label、grasp、task scene graph | mask fusion、semantic object mesh、sidecar |
| 导出层 | URDF、MJCF/XML、USD、多仿真器 | 目前以 GLB/JSON/Web demo 为主，MuJoCo/Isaac/Unity adapter 待加强 |
| 验证层 | human acceptance、collision success、world acceptance、policy validation | 文件 manifest、PLY/GLB 可读、mesh counts、viewer/raycast，需要补 physics preflight |

### 可接入的工程路线

短期最值得借鉴的是 asset contract，而不是重跑 EmbodiedGen V2。建议把 Video2Mesh 的 simulator bundle 逐步改成：

```text
scene_bundle/
  visual/
    scene.splat or scene_3dgs.ply
    scene.glb
    object_visuals/*.glb
  collision/
    scene_collider.glb
    object_colliders/*.glb
    convex_parts/*.glb
  semantics/
    semantic_object_meshes.json
    semantic_object_glbs.json
    face_semantics.json
  physics/
    materials.json
    rigid_bodies.json
    joints.json
    grasps.json
  adapters/
    scene.urdf
    scene.mjcf.xml
    scene.usd
  validation/
    collision_preflight.json
    raycast_ground_probe.json
    simulator_smoke_report.json
```

然后用 EmbodiedGen V2 的思路给每层加质量门：

| Video2Mesh 阶段 | EmbodiedGen V2 启发 | 推荐动作 |
|---|---|---|
| object split | object asset canonicalization | 给每个 object GLB 记录尺度、坐标原点、bbox、mesh stats |
| collider | convex decomposition / collision success | 为 object collider 跑简单抓取/推挤/落地 smoke test |
| semantic sidecar | affordance autolabeling | 从 label 扩展到 affordance、material、joint、grasp candidates |
| scene layout | scene graph + physics settling | 对物体位姿跑 support/contact 检查，过滤悬空/穿模 |
| export | URDF -> MJCF/USD | 新增 MuJoCo/Isaac adapter，而不是只停在 GLB |
| edit UI | Vibe Coding state deltas | 让自然语言编辑走 typed operation 和 validation log |

### 不建议的接入方式

- 不建议把 EmbodiedGen V2 当成 Video2Mesh 的 3D 重建替代品。它不负责从任意扫描视频恢复真实相机、3DGS 和整房间几何。
- 不建议只拿它的自然语言 demo 概念做 UI，而不做 deterministic backend 和 validation。没有质量门的 Vibe Coding 只是聊天式场景编辑，不能保证 sim-ready。
- 不建议把 visual mesh 直接拿来做 collision。论文的关键恰恰是 visual/collision/inertial/metadata 分层。
- 不建议把 79.8% / 75.0% 当成本地 Video2Mesh 指标。这是论文 protocol 下的 downstream policy validation，不是我们本地 bedroom_4 或 SimFoundry baseline 的结果。

## 环境与成本判断

官方仓库公开了项目入口，但完整复现不是轻量任务。论文 pipeline 涉及生成式 3D、mesh processing、VLM/LLM、SAPIEN physics validation、URDF/MJCF/USD conversion、task world generation 和 RL/policy validation。论文实验中的 asset / world generation 主要报告在单张 NVIDIA RTX 4090 上测得。

| 层 | 可能需求 |
|---|---|
| 3D generation | image/text-to-3D model weights，GPU 推理，mesh post-processing |
| mesh processing | mesh repair、convex decomposition、坐标/尺度规范化 |
| physics validation | SAPIEN / PyBullet / MuJoCo / Genesis / Isaac 之一或多个 |
| VLM/LLM | task-to-graph、part semantic annotation、quality checking、agentic editing |
| policy validation | RL/VLA 训练环境、机器人任务定义、sim-to-real protocol |
| 存储 | generated object assets、collision meshes、multi-world layouts、logs、validation reports |

本地 Mac 适合调研、写 adapter、检查小 GLB/JSON、构建网站；不适合完整复现实验。`mil8` 这类多 GPU 服务器可以跑单场景或小规模 smoke，但若要下载多个大模型和跑 policy training，需要先确认磁盘、CUDA、SAPIEN/MuJoCo/Isaac 环境和具体任务 protocol。

## 风险

| 风险 | 说明 | Video2Mesh 处理方式 |
|---|---|---|
| 论文系统很大 | 它是世界引擎，不是单模型 pip install 后可复现全部结果 | 先复刻资产合同和验证器，不急于复现 RL |
| 指标不可直接迁移 | 79.8% / 75.0% 来自论文下游 study | 本地文档只引用为官方结果，不写成本地结果 |
| 生成资产可能偏离真实扫描 | EmbodiedGen 从 prompt/image 生成，Video2Mesh 追求真实场景还原 | 用它补 object/physics sidecar，不覆盖真实扫描几何 |
| Vibe Coding 容易被误解 | 没有 typed skill 和 physics validation 就不是 sim-ready 编辑 | 所有编辑都必须输出 delta、manifest 和 preflight report |
| collision proxy 质量难 | 凸分解过粗会影响交互，过细会拖慢物理 | 每个 object 记录 visual/collider stats，并做 smoke test |
| 多仿真器参数不一致 | friction、mass、joint 在各引擎里的语义不同 | 保留 canonical 参数和 per-engine mapping，不只保留导出文件 |

## 接入判断

- P0：不改 Video2Mesh 主重建链路。继续保持 COLMAP、GraphDECO 3DGS、scene mesh、object split、semantic transfer 的分层资产路线。
- P1：把 EmbodiedGen V2 的 asset contract 落到 `simulator_asset_bundle` manifest：visual/collision/physics/semantic/adapters/validation 分目录。
- P1：新增 collision preflight：mesh stats、non-manifold 检查、bbox/scale 检查、ground probe、简单 rigid-body drop/settle。
- P1/P2：给 object sidecar 扩展 material、mass、friction、affordance、grasp pose 和 source/confidence 字段。
- P2：实现 URDF/MJCF/USD adapter。优先 MuJoCo/Genesis，再看 Isaac Sim/Unity。
- P2：做一个 Video2Mesh-style Vibe Coding 编辑器：自然语言只产生 typed operation，后端负责碰撞、支撑、坐标、导出和回滚。

## 下一步建议

1. 先基于当前 `semantic_object_glbs.json` 设计一个 `simulator_asset_bundle.schema.json`，字段向 EmbodiedGen V2 的 visual/collision/inertial/affordance 合同靠齐。
2. 给已有 bedroom_4 / SimFoundry asset-only 输出加一个 `validation/` 目录，记录 GLB 可读性、mesh counts、bbox、scale、raycast、ground probe 和 object collision proxy。
3. 选择 1-2 个 object 做刚体 smoke：生成 collider、写 mass/friction、导出 MuJoCo MJCF，并跑一个加载 + 落地 + 碰撞检查。
4. 把自然语言编辑先限制在可验证命令：move / replace / scale / set material / set collider / export，而不是开放式改世界。
5. 若后续要复现 EmbodiedGen V2 官方 demo，应单独建隔离分支和远端环境，先跑 asset generation + SAPIEN validation 的最小闭环，不直接进入 RL 训练。
