# 前馈高斯与 Scene Graph 调研：对 Video2Mesh 的替代价值和落地路线

调研日期：2026-06-28  
面向项目：Video2Mesh  
问题：是否用 AnySplat、VGGT、VGGT-Omega 等前馈 3D/高斯模型替代当前 COLMAP + GraphDECO 3DGS；是否引入 scene graph。

## 0. 结论先行

不建议现在把 GraphDECO 3DGS 整体替换成前馈高斯模型。更稳的路线是：

```text
短期：前馈几何模型做预检、兜底、快速预览
中期：前馈模型输出 pose/depth/point map，作为 COLMAP/GraphDECO/mesh 的增强输入
长期：保留优化式高质量 3DGS，同时引入 scene graph 作为语义和仿真的结构层
```

核心判断：

1. **前馈高斯很有用，但先不要当最终资产源**。AnySplat、pixelSplat、MVSplat、Splatt3R、NoPoSplat 这类模型的强项是秒级或近实时生成可渲染 3DGS，尤其适合无位姿/稀疏视角/快速预览。但 Video2Mesh 的目标不只是 novel view synthesis，而是要输出物体 mask、mesh、碰撞体、物理属性和模拟器 adapter。前馈 splat 通常缺少稳定的 per-object identity、几何 QA、尺度校准和可仿真 mesh 约束。
2. **VGGT/VGGT-Omega 比“前馈高斯替代 3DGS”更应该优先接入**。VGGT 直接预测 camera intrinsics/extrinsics、depth、point maps、point tracks；VGGT-Omega 又增强了静态/动态场景能力和长视频扩展性。这正好补 Video2Mesh 的 COLMAP 脆弱点：低纹理、少视差、模糊、动态物体、注册帧少。
3. **GraphDECO 3DGS 仍适合作为生产级视觉表示**。GraphDECO 的优化式 3DGS 有成熟的 per-scene refinement、densification/pruning、SH appearance 和 viewer/export 生态。我们现在的 pipeline、QA 和 simulator asset contract 都围绕它建立。把它拿掉，短期会丢失很多稳定性和可解释中间产物。
4. **Scene graph 应该加，而且应该作为资产层的主索引**。Video2Mesh 现在已经有 object masks、3D bbox、semantic_splats、SVPP metadata、simulator_asset_bundle。下一步不是只追求更漂亮的 splat，而是把 `object -> relation -> support plane -> room/layout -> simulator affordance` 串起来。
5. **最值得做的 MVP**：新增一个 `feedforward-geometry` 后端，先接 VGGT 或 VGGT-Omega，输出 `camera_info.json`、dense depth/point cloud、confidence 和 preview；再新增 `scene_graph.json`，从已有 object metadata、3D bbox、background planes 和 labels 生成第一版结构图。

## 1. 当前 Video2Mesh 的真实边界

当前默认链路是：

```text
video
  -> real-frame extraction
  -> COLMAP poses + sparse/full point cloud
  -> GraphDECO 3DGS
  -> SAM prompts + SAM2 masks
  -> 2D-to-3D semantic mask fusion
  -> semantic/probability Gaussian export
  -> object frame selection
  -> object meshes
  -> MuJoCo / Unity / Isaac asset export
```

这意味着 3DGS 在项目里有三种角色：

| 角色 | 当前依赖 | 替代风险 |
|---|---|---|
| photorealistic scene viewer | GraphDECO 输出 PLY / SuperSplat 兼容 PLY | 前馈高斯可替代一部分 |
| semantic carrier | `semantic_splats.ply`、`semantic_gaussian_probabilities.ply`、`object_id` / probability | 前馈高斯需要 object id 和概率映射接口 |
| mesh/source evidence | 用相机、mask、depth/normal/semantic support 辅助物体 mesh | 单靠前馈 splat 不够，需要 depth/confidence/scale |

所以“替代 3DGS”不能只问渲染效果，还要问这些输出是否稳定：

- `scene/cameras/camera_info.json`
- `scene/reconstruction/point_cloud.ply`
- `scene/reconstruction/3dgs_graphdeco/**/point_cloud.ply`
- `masks/3d/<object_id>/point_indices.json`
- `simulator_assets/semantic_splats.ply`
- `simulator_assets/semantic_gaussian_probabilities.ply`
- `objects/<object_id>/object.json`
- `simulator_assets/simulator_asset_bundle.json`
- `simulator_assets/adapters/{unity,isaac,mujoco}/...`

如果某个前馈模型只输出一个能看的 splat，但不能对齐这些 contract，它就只能是 preview backend，不能直接当生产 backend。

## 2. 方法横向比较

| 方法 | 输入 | 输出 | 强项 | 对 Video2Mesh 的价值 | 不适合直接替代的原因 |
|---|---|---|---|---|---|
| GraphDECO 3DGS | 已知/估计相机 + sparse points | per-scene optimized 3D Gaussians | 高质量 NVS、成熟生态、可控训练 | 继续做生产视觉层和 semantic splat carrier | 慢、依赖 COLMAP，几何表面不一定 mesh-ready |
| pixelSplat | image pair | 3D Gaussians | 前馈、可编辑 radiance field、推理快 | 稀疏双视角快速预览参考 | 主要面向 NVS，不是扫描资产管线 |
| MVSplat | sparse posed multi-view images | clean feed-forward Gaussians | cost volume 带来几何定位，速度快 | 可作为 sparse-view preview / depth prior | 通常需要相机或多视角条件，语义和资产 contract 要另做 |
| Splatt3R | uncalibrated image pair | pose-free Gaussians | 基于 MASt3R，适合 in-the-wild 双图 | COLMAP 失败时的低成本 fallback | 双图/局部场景为主，长视频全局一致性仍需处理 |
| NoPoSplat | unposed sparse multi-view | 3D Gaussians | 不依赖准确 pose，实时 | 适合无位姿 sparse scan 的 preview | canonical frame、尺度和跨物体语义需再对齐 |
| AnySplat | uncalibrated image collection | 3D Gaussians + camera intrinsics/extrinsics | 一次前向预测 pose 和 splat，支持 sparse/dense views | 很适合做 `feedforward-gs-preview` 和 COLMAP fallback | 输出 splat 不等于 mesh/simulator asset；需要验证尺度、object labels、动态鲁棒性 |
| VGGT | one/few/hundreds views | camera params、depth maps、point maps、point tracks | 秒级多任务 3D 几何，直接补 pose/depth | 最适合先接入，用作 pose/depth/point cloud fallback | 它不是 3DGS renderer，本身不输出最终 splat |
| VGGT-Omega | images/video | camera + depth + confidence/point cloud style outputs | 更强静态/动态重建，长视频更可扩展 | 更适合 Video2Mesh 扫描视频，尤其动态/低纹理场景 | 模型权重可能 gated；license/算力/接口稳定性要评估 |

## 3. 对关键模型的判断

### 3.1 AnySplat：可以做前馈高斯预览，不宜直接替代生产 3DGS

AnySplat 的亮点是从未标定多视角图像中一次前向预测 3D Gaussian primitives 和相机内外参。它正好命中我们现在最慢、最容易失败的部分：COLMAP + GraphDECO 的组合。

可用场景：

- 用户上传视频后，几秒到几十秒内给出 preview splat。
- COLMAP readiness 失败时，生成粗 camera/scene 供用户判断是否值得重拍。
- 给 SAM2 mask fusion 提供临时相机和粗点云。
- 作为 GraphDECO 初始化候选：用 AnySplat/VGGT 预测 pose/depth，再转成 COLMAP-style source 或 point cloud。

不建议直接替代的点：

- Video2Mesh 需要 object-level stable id；AnySplat 主要解决 NVS 和几何/外观表示。
- 前馈 splat 的 Gaussian 分布可能更偏渲染，不一定适合做 object mesh support。
- 输出质量和尺度一致性需要按我们的真实房间视频测，不应只看论文 demo。

### 3.2 VGGT：比前馈高斯更适合优先集成

VGGT 的价值不是输出漂亮 splat，而是输出我们下游真正缺的几何中间量：

- camera intrinsics/extrinsics
- depth maps
- point maps
- 3D point tracks

这几个输出可以直接接入 Video2Mesh：

```text
frames
  -> VGGT
  -> camera_info_vggt.json
  -> depth_maps/*.npy or .exr
  -> point_cloud_vggt.ply
  -> confidence_maps/*.npy
```

然后有三条用法：

1. **COLMAP fallback**：COLMAP pose 少或点云空时，用 VGGT 产物继续跑低质量预览和语义融合。
2. **COLMAP scorer**：不替代 COLMAP，只用 VGGT 预估视差、重叠、深度稳定性，帮用户选 8-15 秒最佳窗口。
3. **mesh evidence**：物体 mesh 阶段用 VGGT depth/confidence 做 TSDF/Poisson 输入，减少 raw sparse cloud 的破碎。

### 3.3 VGGT-Omega：中长期最值得关注的扫描视频几何底座

VGGT-Omega 相比 VGGT 更贴近我们的目标：它强调更大规模训练、更低训练内存、静态和动态场景能力、视频数据、自监督，以及 reconstruction latents 对 spatial understanding / language alignment 的帮助。

对 Video2Mesh 的意义：

- 可能比 MASt3R-SLAM 更适合短视频和动态室内扫描。
- 可以将动态物体作为低置信区域或独立 track 处理，减少 COLMAP 被动态前景拖垮。
- learned registers / latents 未来可作为 scene graph node feature 或 VLM/LLM grounding feature。

风险：

- 权重访问、license、模型版本和工程接口仍需实测。
- 目前不应把它写死进默认生产路径；适合做 optional backend。
- 需要专门评估 metric scale、长视频分块一致性、rolling shutter/blur、室内重复纹理。

## 4. 推荐架构：不要“替代”，要“双轨”

建议把 Video2Mesh 的重建层改成双轨：

```text
输入视频
  -> frame QA / window selection
  -> feed-forward geometry backend
       - VGGT / VGGT-Omega
       - optional AnySplat preview
       - outputs: pose, depth, point cloud, confidence, preview splat
  -> classical/optimized backend
       - COLMAP
       - GraphDECO 3DGS
       - optional geometry-aware 3DGS cleanup
  -> semantic fusion
  -> object mesh
  -> scene graph
  -> simulator assets
```

这样能同时获得：

- 前馈模型的速度和鲁棒先验。
- COLMAP/GraphDECO 的可控 refinement 和成熟输出。
- 下游语义、mesh、simulator contract 的连续性。

## 5. Scene Graph：应该加在哪

Scene graph 不应该替代 3DGS/mesh。它应该是 Video2Mesh 的结构化索引层：

```text
scene_graph.json
  nodes:
    scene / room / floor / wall / object / background_structure
  edges:
    contains
    supported_by
    on / under / next_to / inside / attached_to
    near
    blocks / affords / movable / static
  evidence:
    3D bbox
    point indices
    semantic splat ids
    source frames
    mask confidence
    mesh path
    physics metadata
```

### 5.1 为什么需要 scene graph

当前资产包已经能把物体导出到模拟器，但缺一个统一表达：

- 床在地面上。
- 枕头在床上。
- 桌子靠墙。
- 椅子在桌子旁边。
- 墙、地、天花板是固定结构，不应该当可动物体 mesh。
- 柜门/抽屉/椅子等物体具有不同 affordance。

这些关系对下游很重要：

- 物体摆放和碰撞初始化。
- QA：物体 mesh 是否偏离自己的 support plane。
- 仿真：可动/不可动、mass/friction/collider 默认值。
- 语言查询：`find the chair near the desk`。
- 场景补全：如果物体 mesh 缺失，可以用 scene graph 找合适的替代生成 prompt。

### 5.2 代表方案

| 方案 | 核心思路 | 对 Video2Mesh 的启发 |
|---|---|---|
| ConceptGraphs | 2D foundation model 输出经多视角关联融合为 open-vocabulary 3D scene graph | 可借鉴 object-level map + spatial relation，用于 planning/语言任务 |
| Open3DSG | 从 point cloud 预测 open-vocabulary object classes 和 open-set relationships | 可借鉴关系预测，不只预测 `near/on` 这类固定关系 |
| HOV-SG | floor/room/object 层级 open-vocabulary graph，用于机器人导航 | 对室内/多房间结构特别适合，能让 layout 成为一等节点 |
| SceneGraphLoc | 用 object-level graph 做视觉定位，减少对大图像库依赖 | 可用于 scan resume、局部重定位、后续增量扫描 |
| GaussianGraph | 在 3DGS 上做 semantic clustering 和 scene graph generation | 适合我们已有 semantic splat 的中期升级 |
| SplatTalk | 用 generalizable 3DGS 生成 3D tokens，接 LLM 做 3D VQA | 可作为未来 QA/自然语言解释层，而不是第一版资产层 |

### 5.3 第一版 schema 建议

建议新增：

```text
simulator_assets/scene_graph.json
```

最小结构：

```json
{
  "scene_id": "bedroom_4",
  "coordinate_frame": "video2mesh_world",
  "nodes": [
    {
      "id": "object:gdino_object_bed",
      "type": "object",
      "label": "bed",
      "bbox_3d": {"center": [0, 0, 0], "extent": [2, 1.5, 0.5]},
      "semantic_id": 3,
      "point_count": 120345,
      "mesh": "objects/gdino_object_bed/mesh.obj",
      "source_frames": ["000010", "000034"],
      "confidence": 0.82
    },
    {
      "id": "structure:floor",
      "type": "background_structure",
      "label": "floor",
      "plane": {"normal": [0, 1, 0], "offset": 0.0},
      "static": true
    }
  ],
  "edges": [
    {
      "source": "object:gdino_object_bed",
      "target": "structure:floor",
      "type": "supported_by",
      "confidence": 0.91,
      "evidence": {"bbox_bottom_distance": 0.03}
    }
  ]
}
```

第一版关系可以不用训练模型，直接用几何规则：

- `contains`: scene/room contains object。
- `supported_by`: object bbox bottom 接近 floor/table/bed top。
- `on`: A 的底面高于 B 的顶面且 XY overlap 足够。
- `next_to`: 3D bbox 水平距离小于阈值且高度重叠。
- `attached_to`: object bbox 与 wall/ceiling 接近。
- `static`: floor/wall/ceiling/large background structures。
- `movable`: 小家具/小物体，后续由 label + size + mass 估计。

## 6. 落地路线

### 6.1 短期，一周内

目标：不破坏现有生产管线，增加可试验接口。

1. 写 `feedforward_geometry_manifest.json` contract：
   - provider: `vggt`, `vggt_omega`, `anysplat`
   - input frames
   - camera output
   - point cloud output
   - depth/confidence output
   - preview output
   - scale/alignment status
2. 新增 `prepare-feedforward-geometry-job`：
   - 从 `scene/frames` 导出模型输入列表。
   - 记录 frame ids 和原始尺寸。
3. 新增 `import-feedforward-geometry-result`：
   - 导入 `camera_info.json`
   - 导入 `point_cloud.ply`
   - 可选导入 `depth_maps`
   - 写入 manifest artifact。
4. 新增 `export-scene-graph`：
   - 从 objects、masks、background planes、semantic manifest、simulator bundle 生成 `scene_graph.json`。

短期不要做：

- 不要把 AnySplat/VGGT-Omega 设为默认。
- 不要删除 GraphDECO。
- 不要让 scene graph 依赖 LLM 在线推理。

### 6.2 中期，两到四周

目标：让前馈几何真正增强质量。

1. 用 VGGT/VGGT-Omega 结果做 COLMAP readiness 预估：
   - depth consistency
   - pose baseline
   - frame overlap
   - confidence heatmap
2. 在 COLMAP 失败时启用 fallback：
   - `scene/cameras/camera_info_vggt.json`
   - `scene/reconstruction/point_cloud_vggt.ply`
   - 后续 SAM2/mask fusion 使用 fallback geometry。
3. 物体 mesh 阶段接入 depth/confidence：
   - masked depth fusion
   - confidence-weighted TSDF
   - semantic support crop。
4. scene graph 加 QA：
   - floating object
   - unsupported object
   - duplicate object
   - object mesh too large for bbox
   - wall/floor/ceiling missing。

### 6.3 长期

目标：Video2Mesh 从“扫描到资产”升级为“扫描到可推理、可仿真的场景”。

1. GaussianGraph / ConceptGraphs-style semantic graph：
   - Gaussian/point/node features
   - open-vocabulary labels
   - relationship prediction
2. VGGT-Omega registers/latents 做 node feature：
   - object-level pooling
   - language alignment
   - affordance estimation
3. 动态场景：
   - dynamic foreground track
   - static background graph
   - movable object state graph。
4. 增量扫描：
   - SceneGraphLoc-style relocalization
   - merge new scan into existing scene graph。

## 7. 推荐实验

选择 3 个已有视频窗口：

| 场景 | 目的 |
|---|---|
| COLMAP 成功的 bedroom 窗口 | 比较 GraphDECO vs VGGT/AnySplat 的几何和渲染 |
| COLMAP 注册少/失败的窗口 | 测前馈 geometry fallback 是否能继续下游 |
| 动态/遮挡多的视频 | 测 VGGT-Omega 对动态场景是否更稳 |

指标：

- camera coverage / pose count
- point cloud density
- depth consistency
- semantic mask fusion coverage
- object bbox stability
- mesh support quality
- simulator QA pass rate
- preview generation time
- end-to-end wall time

验收标准不是“splat 看起来更好”，而是：

```text
前馈模型加入后，至少一个失败视频能继续生成可检查的 semantic/object/simulator 资产；
且成功视频的 GraphDECO 质量不下降，现有 artifacts contract 不破。
```

## 8. 我的建议排序

优先级从高到低：

1. **接 VGGT/VGGT-Omega 作为 feed-forward geometry fallback**。
2. **新增 `scene_graph.json`，先用规则生成几何关系**。
3. **接 AnySplat 作为 preview/alternative 3DGS backend，不替换 GraphDECO**。
4. **把 VGGT depth/confidence 用到 object mesh 的 TSDF/Poisson 阶段**。
5. **中期调研 GaussianGraph / ConceptGraphs，把 scene graph 从规则升级为 open-vocabulary graph**。

一句话：  
**前馈模型解决“快”和“失败兜底”，GraphDECO 解决“高质量可视化”，scene graph 解决“资产可理解、可仿真、可推理”。三者应互补，不要互相硬替代。**

## 参考资料

- [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079)
- [GraphDECO official gaussian-splatting repository](https://github.com/graphdeco-inria/gaussian-splatting)
- [AnySplat: Feed-forward 3D Gaussian Splatting from Unconstrained Views](https://arxiv.org/abs/2505.23716)
- [AnySplat project page](https://city-super.github.io/anysplat/)
- [VGGT: Visual Geometry Grounded Transformer](https://arxiv.org/abs/2503.11651)
- [VGGT project page](https://vgg-t.github.io/)
- [VGGT GitHub](https://github.com/facebookresearch/vggt)
- [VGGT-Omega](https://arxiv.org/abs/2605.15195)
- [VGGT-Omega project page](https://vggt-omega.github.io/)
- [VGGT-Omega GitHub](https://github.com/facebookresearch/vggt-omega)
- [pixelSplat](https://arxiv.org/abs/2312.12337)
- [MVSplat](https://arxiv.org/abs/2403.14627)
- [Splatt3R](https://arxiv.org/abs/2408.13912)
- [NoPoSplat](https://noposplat.github.io/)
- [ConceptGraphs](https://arxiv.org/abs/2309.16650)
- [Open3DSG](https://arxiv.org/abs/2402.12259)
- [HOV-SG](https://arxiv.org/abs/2403.17846)
- [SceneGraphLoc](https://arxiv.org/abs/2404.00469)
- [GaussianGraph](https://arxiv.org/abs/2503.04034)
- [SplatTalk](https://arxiv.org/abs/2503.06271)
