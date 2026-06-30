# Sim Anything / PhysSplat 论文调研：对 Video2Mesh 仿真资产线的启发

调研日期：2026-06-30  
面向项目：Video2Mesh 当前流水线

## 0. 结论先行

用户提到的 **Sim Anything** 对应的公开项目/论文线索目前主要指向
**PhysSplat: Efficient Physics Simulation for 3D Scenes via MLLM-Guided Gaussian Splatting**。
论文 arXiv 编号为 `2411.12789`，项目页早期使用 `sim-gs.github.io`，
GitHub 链接为 `Maxwell-Zhao/PhysSplat`。arXiv v3 标注为 ICCV 2025。

这篇论文不是从视频重建 3D 场景或 mesh 的方法；它假设已经有一个静态
3DGS 场景，然后自动找出可动对象、估计物理属性，并把 3DGS 变成可物理仿真的
动态粒子/高斯表示。它对 Video2Mesh 最有价值的部分是：

1. **把仿真问题拆成 semantic + physics + deformation + rendering 四层**，而不是只导出一个 mesh。
2. **用 MLLM/VLM 自动判断对象物理属性**，可补强 Video2Mesh 当前的 `prepare-simulator-physics-jobs` 和 `import-simulator-physics`。
3. **用可动对象 mask 驱动局部动态**，与 Video2Mesh 的 2D/3D mask、semantic splats、simulator bundle 很贴。
4. **用 Gaussian/particle 级表示做动态仿真**，适合做软体、液体、可形变物体展示；但它不能直接替代 Video2Mesh 的 mesh、collider、MuJoCo/Unity/Isaac 导出。

建议把它作为 Video2Mesh 的 **动态仿真增强方向**，而不是替代当前
`video -> COLMAP -> 3DGS -> masks -> object mesh -> simulator assets` 主链路。

## 1. 论文要解决的问题

传统 3DGS 主要擅长新视角渲染：给定一组图片和相机位姿，训练出静态高斯场景。
但是静态 3DGS 不知道哪些东西能动、是什么材质、受到外力后怎么变形，也没有
仿真器里的质量、刚体/软体、碰撞体等属性。

PhysSplat 的问题定义可以概括为：

```text
静态 3DGS 场景
  -> 自动识别可操作/可动对象
  -> 估计物理属性
  -> 把对象高斯转换为可仿真的粒子/高斯状态
  -> 用物理模拟更新对象形变和运动
  -> 仍然用 Gaussian splatting 渲染动态结果
```

它关心的是“让已有 3DGS 场景动起来”，而不是“从视频把场景建出来”。

## 2. 方法链路

### 2.1 场景理解与对象定位

论文使用多模态大模型辅助理解场景和物体。核心作用不是训练一个新的 open-vocabulary
segmenter，而是让模型根据渲染视图、语言提示和场景上下文判断：

- 哪些对象是目标对象。
- 哪些区域属于该对象。
- 对象更像刚体、软体、颗粒、液体或其他物理类别。
- 对象应采用哪些物理参数或交互规则。

这和 Video2Mesh 当前的 `auto-prompts`、`track-masks`、`fuse-masks` 分工不同：
Video2Mesh 更偏“先得到稳定 2D/3D mask”，PhysSplat 更强调“mask 之后的物理解释”。

### 2.2 3DGS 到物理表示

论文把 3DGS 中目标对象对应的高斯抽出来，并转成适合仿真的物理实体。
这一步的关键是：Gaussian 原本只是渲染 primitive，不天然等于物理粒子。
因此需要给每个对象或每个高斯/粒子附加：

- 位置、速度、质量。
- 材质参数。
- 刚度、阻尼、塑性或流体相关参数。
- 是否固定、是否受重力、是否可碰撞。
- 和场景背景/其他对象的碰撞关系。

Video2Mesh 当前已经有 `semantic_splats.ply`、`semantic_gaussian_probabilities.ply`
和 `simulator_asset_bundle.json`，但语义高斯和仿真 bundle 之间还不是同一个
物理粒子系统。PhysSplat 的价值就在这个连接处。

### 2.3 物理模拟

论文使用物理模拟更新对象状态，使高斯/粒子随时间运动或形变。它的重点是
高效地产生可视化动态效果，尤其适合：

- 软体/可变形物体。
- 颗粒或散落物。
- 受力后会形变的局部对象。
- 需要保持 3DGS 渲染外观的动态场景。

这和 MuJoCo/Isaac/Unity 的标准刚体资产导出不是同一个目标。MuJoCo/Isaac/Unity
更需要稳定 mesh、collider、joint、rigid body、body type 和可解释的物理参数；
PhysSplat 更像是在 Gaussian 表示上直接做动态视觉仿真。

### 2.4 动态渲染

仿真后，目标对象的 Gaussian/particle 状态发生变化，系统再用 splatting 渲染每个时间步。
因此最终结果更像动态 3DGS 视频或交互式 dynamic splat，而不是标准游戏引擎资产包。

## 3. 和 Video2Mesh 当前流水线对照

| 阶段 | Video2Mesh 当前做法 | PhysSplat / Sim Anything 做法 | 关系 |
|---|---|---|---|
| 输入 | 空间扫描视频 | 已训练静态 3DGS 场景 | Video2Mesh 更前置 |
| 位姿/重建 | COLMAP + GraphDECO 3DGS | 依赖已有 3DGS | PhysSplat 不替代重建 |
| 2D mask | SAM prompt + SAM2 tracking | MLLM/VLM 辅助对象理解 | 可互补 |
| 2D-to-3D | 点云/高斯语义融合 | 从 3DGS 中抽目标对象 | Video2Mesh 可提供对象高斯 |
| 物体 mesh | 3DGS rendered depth/normal/mask -> TSDF/Poisson | 不以 mesh 为核心 | 不能替代 mesh 导出 |
| 物理属性 | 默认估计 + 外部/manual physics jobs | MLLM-guided physics property inference | 可借鉴 |
| 仿真表示 | simulator bundle + collider + adapters | Gaussian/particle dynamics | 两条输出线 |
| 输出 | MuJoCo/Unity/Isaac + review pack | dynamic 3DGS simulation | 目标不同 |

最重要的边界：PhysSplat 不能帮 Video2Mesh 解决 COLMAP 失败、3DGS 几何质量差、
2D mask 漂移、object mesh 破碎这些上游问题。它主要帮的是“已经有语义对象之后，
如何让它们具备动态物理行为”。

## 4. Video2Mesh 可以怎么借

### 4.1 增加 `dynamic_gaussian_assets` 输出线

当前 Video2Mesh 的 simulator 输出可以继续保持：

```text
simulator_assets/simulator_asset_bundle.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/adapters/isaac/...
```

在旁边新增一条 Gaussian 动态仿真线：

```text
simulator_assets/dynamic_gaussian_assets/
  scene_dynamic_config.json
  objects/<object_id>/gaussians.ply
  objects/<object_id>/physics.json
  objects/<object_id>/constraints.json
  simulations/<sim_id>/trajectory.npz
  simulations/<sim_id>/frames/
```

这条线服务于 dynamic splat 展示和局部物理实验，不强行塞进 MuJoCo/Unity
标准 mesh/collider 合同。

### 4.2 用 VLM/MLLM 生成物理属性草稿

Video2Mesh 已经有：

```bash
python -m video2mesh.cli prepare-simulator-physics-jobs
python -m video2mesh.cli import-simulator-physics
python -m video2mesh.cli simulator-physics-quality-report
```

可以新增一个 provider，例如：

```text
provider = "mllm_physics"
```

输入给 VLM/MLLM：

- object crop / selected frames。
- object mask。
- object category / label。
- world bbox size。
- support plane。
- 当前 mesh 或 object splat preview。

输出：

```json
{
  "object_id": "chair_01",
  "body_type": "dynamic",
  "material": "wood",
  "mass_kg": 5.0,
  "friction": 0.55,
  "restitution": 0.1,
  "rigidity": "rigid",
  "deformable": false,
  "confidence": 0.72,
  "rationale": "wooden dining chair with rigid frame"
}
```

这样可以先补齐仿真 bundle 的物理字段，再由人工或真实测量校准。

### 4.3 把对象分成刚体输出和可形变输出

推荐在 `object_asset.json` 或 `simulator_asset_bundle.json` 中增加动态类型：

```json
{
  "simulation_role": "rigid_body",
  "dynamic_gaussian_candidate": false
}
```

或：

```json
{
  "simulation_role": "deformable_gaussian",
  "dynamic_gaussian_candidate": true
}
```

分类规则可以先简单做：

- chair/table/cabinet/book：默认 rigid body。
- cloth/pillow/blanket/plant/liquid/food/sand：候选 deformable/particle。
- floor/wall/ceiling/background：static collider。

PhysSplat 更适合第二类，不适合把所有物体都 Gaussian 化仿真。

### 4.4 对 semantic Gaussian 做物理属性扩展

Video2Mesh 当前语义高斯更偏：

```text
object_id
semantic_id
object_probability
```

可借鉴 PhysSplat 增加物理相关 sidecar，而不是直接污染 viewer PLY：

```text
simulator_assets/gaussian_physics/
  gaussian_physics_manifest.json
  object_<id>_gaussian_indices.npy
  object_<id>_particle_state.npz
```

字段示例：

```json
{
  "object_id": "pillow_01",
  "semantic_id": 3,
  "particle_source": "semantic_gaussian_probabilities.ply",
  "gaussian_count": 12843,
  "physics_model": "deformable",
  "material": {
    "density": 35.0,
    "youngs_modulus": 20000.0,
    "poisson_ratio": 0.35,
    "friction": 0.6
  }
}
```

### 4.5 对背景和对象做不同处理

PhysSplat 的动态对象需要和静态背景碰撞。Video2Mesh 已经把 background structure
作为 `asset_role=background_structure` 的一等记录，这一点很适合承接：

```text
floor/wall/table surface
  -> static collider / boundary condition

foreground deformable object
  -> dynamic gaussian/particle object
```

不要把背景也当成可动高斯对象。背景更应该导出为静态 collider 或 layout plane。

## 5. 不建议直接照搬的地方

### 5.1 不要用 PhysSplat 替代 object mesh

Video2Mesh 的目标包括 MuJoCo/Unity/Isaac asset export。标准仿真器仍然更吃：

- watertight 或近似 watertight visual mesh。
- 简化 collision proxy。
- 明确尺度、坐标系、body type。
- joint/constraint/contact material。

PhysSplat 输出的 dynamic Gaussian simulation 对展示很好，但不能直接等价于
Unity/MuJoCo 可复用资产。

### 5.2 不要让 MLLM 决定所有物理参数而不做 QA

MLLM 可以给材料和参数初值，但物理字段需要质量报告：

- 是否缺 mass。
- mass 是否和 bbox 尺寸/类别严重不符。
- friction/restitution 是否超范围。
- rigid/deformable 是否和类别冲突。
- static background 是否被误标成 dynamic object。

这些可以接入现有 `simulator-physics-quality-report`。

### 5.3 不要忽略上游 mask 质量

动态仿真对 mask 质量非常敏感。对象 Gaussian 混入背景后，仿真会出现：

- 墙/地板跟着物体动。
- 物体边缘飞散。
- 软体对象粘连到桌面。
- 碰撞体和视觉对象错位。

因此在接 PhysSplat-style 动态之前，应先保证：

- object 3D mask 有足够 visibility support。
- semantic Gaussian probability 足够高。
- 3D 连通域干净。
- 支撑平面和对象 bbox 合理。

## 6. 推荐落地路线

### 6.1 短期：先做物理属性自动草稿

优先级最高的是补强现有 simulator bundle，而不是先做完整 Gaussian 动力学：

```text
selected object frames + masks + bbox
  -> VLM/MLLM physics annotation
  -> import-simulator-physics
  -> simulator-physics-quality-report
```

收益：

- 最贴近现有 CLI 和 QA。
- 对导师展示有直接价值。
- 即使不做 dynamic Gaussian，也能改善 Unity/MuJoCo/Isaac bundle。

### 6.2 中期：导出动态 Gaussian 候选对象

新增命令可以设计为：

```bash
python -m video2mesh.cli export-dynamic-gaussian-assets \
  --project-root exports/<run> \
  --semantic-splats-ply exports/<run>/simulator_assets/semantic_gaussian_probabilities.ply \
  --min-probability 0.6 \
  --roles deformable_gaussian particle
```

输出每个候选对象的 Gaussian 子集、物理属性草稿和背景 collider 引用。

### 6.3 长期：接入 MPM / differentiable physics 后端

长期才考虑类似 PhysSplat 的完整闭环：

```text
semantic object gaussians
  -> particle initialization
  -> MPM / deformable simulation
  -> per-timestep gaussian update
  -> dynamic splat viewer
  -> optional rendered video / interaction demo
```

这部分建议作为独立 backend，避免把 Video2Mesh 主 CLI 变成重型物理引擎。

## 7. 对当前项目的具体判断

Video2Mesh 和 PhysSplat 的关系可以一句话概括：

```text
Video2Mesh 负责从真实扫描视频生成有语义、几何和仿真合同的资产；
PhysSplat 启发我们把其中一部分语义 Gaussian 对象升级成可动态仿真的物理对象。
```

最值得借的不是它的最终 demo，而是三个设计：

1. **semantic Gaussian -> physical object** 的转换层。
2. **MLLM/VLM -> physics property draft** 的自动标注层。
3. **dynamic Gaussian object** 和 **static background collider** 的分层。

如果要和当前代码对接，最自然的插入点是：

```text
backproject-gaussian-probabilities
  -> gaussian-probability-quality-report
  -> export-dynamic-gaussian-assets
  -> prepare/import simulator physics
  -> simulator-physics-quality-report
```

而不是替换 `reconstruct-3dgs-object-meshes` 或 `export-simulator-assets`。

## 8. 参考资料

- PhysSplat arXiv: <https://arxiv.org/abs/2411.12789>
- PhysSplat arXiv HTML: <https://arxiv.org/html/2411.12789>
- Project page: <https://sim-gs.github.io/>
- GitHub: <https://github.com/Maxwell-Zhao/PhysSplat>
- Video2Mesh current pipeline: `VIDEO2MESH_PIPELINE.md`
- Video2Mesh scene scanning survey: `SCENE_SCANNING_SOLUTIONS_SURVEY.md`
