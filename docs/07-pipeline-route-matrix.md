---
title: 流水线阶段路线矩阵
category: Pipeline
summary: 按 Video2Mesh 流程逐阶段说明当前采用路线、备选路线、适用条件和风险，便于开会讨论和后续替换模块。
tags:
  - Pipeline
  - Route Matrix
  - Segmentation
  - Mesh
---

# 流水线阶段路线矩阵

这篇文档按流程组织，每一阶段都回答四个问题：

- 当前选定路线是什么。
- 为什么先选它。
- 还有哪些可替代路线。
- 什么时候应该切换或并行评估。

## 总览

```text
video
  -> frame selection / scan QA
  -> camera pose and point cloud
  -> 3DGS visual scene
  -> object discovery and semantic segmentation
  -> 2D-to-3D semantic fusion
  -> object mesh and completion
  -> collider / physics / scene graph
  -> simulator adapters and QA
```

| 阶段 | 当前主路线 | 近期备选 | 判断标准 |
|---|---|---|---|
| 视频抽帧 | 真实帧均匀采样 + 时间窗 | smart keyframing / coverage QA | COLMAP 注册率、模糊、视差 |
| 位姿/点云 | COLMAP | MASt3R / DUSt3R / VGGT / MegaSaM | COLMAP 失败或弱纹理场景 |
| 视觉场景 | GraphDECO 3DGS | 2DGS / SuGaR refined GS / Spark runtime | 画质、训练时间、几何可用性 |
| 语义分割 | SAM prompt + SAM2 tracking | Grounded-SAM2、YOLO-World+SAM、DEVA/XMem | mask 稳定性、类别覆盖、跨帧一致性 |
| 3D 语义融合 | 点云投影投票 + probability | SVLGaussian-style ray-to-Gaussian、graph refinement | object mask 干净度、可解释性 |
| object mesh | 3DGS rendered depth/mask + TSDF | GS2Mesh-style、SuGaR、generated mesh | 可见覆盖、遮挡程度、是否要编辑 |
| collider | static mesh + object proxy | CoACD / V-HACD / primitive fitting | 是否动态、是否进 Unity/MuJoCo |
| 物理属性 | 模板 + QA + 人工/外部导入 | MLLM physics draft / SimAnything-style | 是否需要可交互仿真 |
| scene graph | sidecar JSON | SpatialLM / PQ3D / VLM relation extraction | 是否需要任务、导航、交互逻辑 |

## 1. 视频抽帧与扫描质量

### 当前路线

真实 decoded frames + `MAX_FRAMES` 上限内均匀采样。指定时间窗时也只从真实帧中抽，不插值。

### 为什么先选

- 简单、稳定、可复现。
- 不引入合成帧造成的相机/几何假信号。
- 与 COLMAP / 3DGS 训练输入一致。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| smart keyframing | 提升视差覆盖，减少冗余帧 | 需要质量评分和调参 | 长视频、移动轨迹复杂 |
| blur / exposure QA | 提前过滤坏帧 | 可能丢掉少数关键视角 | 手机扫描、运动模糊明显 |
| coverage heatmap | 能提示补拍区域 | 需要已估 pose 或粗重建 | 产品化采集指导 |

## 2. 位姿与点云

### 当前路线

COLMAP 作为默认 SfM/MVS baseline，输出 `camera_info.json` 和 full `point_cloud.ply`。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| MASt3R / DUSt3R | 弱纹理或 COLMAP 失败时可兜底 | 尺度、全局一致性和工程依赖更复杂 | 短视频、低纹理、注册失败 |
| VGGT / VGGT-Omega | 前馈几何能力强，适合未来统一底座 | 方法和代码成熟度需评估 | 中长期替换或辅助 COLMAP |
| MegaSaM / learned depth | 提供 dense depth prior | 需要额外模型和标定处理 | TSDF mesh 或 GS2Mesh-style enhancement |

### 切换条件

当 readiness 出现注册帧过少、单 pose、空点云、覆盖率低时，优先换真实时间窗；仍失败再启用 learned fallback。

## 3. 3DGS 视觉场景

### 当前路线

GraphDECO 3DGS 是默认训练路线，用 full COLMAP point cloud 初始化。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| 2DGS | surface 更稳，mesh 友好 | 替换训练后端成本高 | mesh 质量优先 |
| SuGaR refined GS | 便于 editable mesh | 需要额外优化 | 单物体或小场景 benchmark |
| Spark / SuperSplat runtime | Web 端运行成熟 | 主要是渲染 runtime，不解决重建 | 展示和交互 viewer |

## 4. 语义分割与跟踪

### 当前选定路线

当前主线是：

```text
object prompt discovery
  -> SAM / SAM2 masks
  -> SAM2 video tracking
  -> mask QA
```

当前阶段更重视跨帧一致性和可投影性，而不是一次性得到完美类别名。类别和 affordance 可以后续用 VLM / open-vocabulary detector 补。

### 为什么先选

- SAM2 对视频 mask propagation 更适合我们的多帧融合。
- 和 2D-to-3D projection voting 直接兼容。
- mask 可以保留为可审计中间产物。
- 出错时容易人工检查和替换。

### 备选路线对比

| 路线 | 做法 | 优点 | 风险 | 适用场景 |
|---|---|---|---|---|
| SAM2 + 自动 prompts | 先发现候选框/点，再跟踪 | 当前最贴合 pipeline，跨帧一致性好 | 类别名弱，复杂家具会过分割 | 默认路线 |
| Grounded-SAM2 | 文本检测框 + SAM2 mask | open-vocabulary 类别更清楚 | prompt 质量影响大，漏检小物体 | 需要“椅子/桌子/柜子”等明确类别 |
| YOLO-World + SAM | open-vocabulary detector 给框，SAM 出 mask | 工程快，类别更稳定 | 框级误检会传给 SAM | 室内常见物体 |
| OWL-ViT / OWLv2 + SAM | 文本-图像检测 + mask refinement | 类别灵活 | 速度和置信度需评估 | 自定义类别集合 |
| DEVA / XMem | video object segmentation / tracking | 长视频跟踪强 | 初始化 mask 仍依赖上游 | SAM2 跟踪漂移时 |
| Mask2Former / OneFormer | panoptic segmentation | 稳定类别和 stuff 区域 | 类别集合固定，开放性弱 | floor/wall/ceiling 背景结构 |
| VLM 逐帧审查 | 用 GPT-4o/MLLM 过滤候选 | 可解释，能输出描述 | 成本高，不适合作每帧主干 | label / affordance / QA |

### 推荐组合

第一版保持：

```text
SAM2 tracking
  + object mask QA
  + VLM label refinement
```

P1 增强：

```text
GroundingDINO or YOLO-World
  -> SAM2
  -> track QA
  -> VLM merge/split suggestions
```

背景结构单独处理：

```text
floor / wall / ceiling
  -> plane fitting + panoptic/stuff segmentation
  -> layout sidecar
```

## 5. 2D 到 3D 语义融合

### 当前路线

把 3D 点投影到每个带 mask 的帧，使用可见性和 mask 命中统计做投票或 probability fusion。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| visibility-weighted vote | 可解释、易调试 | 对 pose/depth 敏感 | 默认 object masks |
| SVLGaussian-style Gaussian probability | 直接把语义写到 Gaussian | 计算重，需过滤漂浮高斯 | semantic splats / viewer |
| graph refinement | 用相邻点/高斯平滑语义 | 可能过度平滑边界 | mask 噪声较大 |
| mesh face backprojection | 给 collider / mesh face 贴语义 | 依赖 mesh 质量 | trigger、navmesh、Unity 交互 |

## 6. Object Mesh 与遮挡补全

### 当前路线

```text
3DGS rendered RGB/depth/normal/mask
  -> masked TSDF fusion
  -> Poisson / marching cubes
  -> cleanup and simplify
```

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| GS2Mesh-style stereo depth | 不直接相信 Gaussian geometry | 需要 stereo model 和视角采样 | in-the-wild 3DGS mesh |
| SuGaR | 3DGS-aware editable mesh | 额外优化，不适合 P0 collider | 高质量 visual mesh |
| Hunyuan3D / Meshy / TRELLIS | 能补全遮挡物体 | 尺度和真实形状需对齐 QA | 桌椅柜等常见物体补全 |
| OpenMVS / RealityCapture | 工业 mesh/texturing 强 | 依赖重或闭源 | 对照 benchmark |

## 7. Collider 与物理代理

### 当前路线

- 场景级 static collider：dense point cloud / Poisson / simplified mesh。
- 物体 collider：bbox、convex hull、compound primitive。
- 动态物体：优先 primitive / convex decomposition。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| CloudCompare PoissonRecon | 快速稳定 | 自动化需封装 | scene collider baseline |
| CoACD / V-HACD | 物理引擎友好 | 需要已有 mesh | dynamic rigid body |
| 手工 primitive fitting | 稳定、轻量 | 视觉不精确 | 桌椅柜、箱体、平面 |
| mesh collider | 几何贴合 | dynamic 限制多 | static environment |

## 8. 物理属性与动态对象

### 当前路线

先用 template/manual/external import 补 `body_type`、`mass_kg`、`friction`、`restitution`，再跑 QA。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| MLLM physics draft | 自动给材料和质量初值 | 不能无 QA 直接相信 | 大量 object 初筛 |
| SimAnything / PhysSplat | semantic Gaussian 动态仿真 | 不替代 mesh/collider | 软体、颗粒、局部动态展示 |
| 真实测量 / 标定 | 最可信 | 成本高 | 关键 demo 或实验 |

## 9. Scene Graph 与交互逻辑

### 当前路线

使用 sidecar JSON 记录 object id、类别、bbox、support、affordance、asset refs。

### 备选路线

| 路线 | 优点 | 风险 | 适用场景 |
|---|---|---|---|
| SpatialLM / PQ3D style | 结构化 3D 理解成熟 | 依赖数据格式和模型 | layout / object relation |
| VLM relation extraction | 可解释、灵活 | 需要多视角证据 | support、on/near/inside |
| rule-based geometry | 稳定、便宜 | 语义表达有限 | floor support、bbox relation |

## 10. 推荐迭代顺序

1. 保持 COLMAP + GraphDECO + SAM2 + projection fusion 主线稳定。
2. 给语义分割加 GroundingDINO / YOLO-World 候选路线，但不要立刻替换 SAM2 tracking。
3. object mesh 先加强 TSDF，再评估 GS2Mesh-style depth。
4. 遮挡补全接 generated mesh，但必须 fit to bbox + support plane。
5. collider 和 physics sidecar 独立于 visual mesh。
6. 长期再加 SimAnything / PhysSplat dynamic Gaussian 旁路线。
