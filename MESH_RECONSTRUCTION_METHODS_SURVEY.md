# 3DGS / 点云到 Mesh 重建方法调研报告

调研日期：2026-06-30  
面向项目：Video2Mesh  
核心问题：从 3DGS、COLMAP 点云、语义点云或多视角深度中生成可用于 Web / Unity / 仿真的 Mesh，尤其是轻量 collision mesh，并兼容后续语义资产。

## 0. 结论先行

我们不应该只选一种“3DGS 转 Mesh”方法，而应该把 Mesh 产物拆成三类：

```text
visual mesh       用于展示、贴图、编辑，追求几何和外观质量
collision mesh    用于碰撞、阻挡、角色行走，追求轻量、闭合、稳定
semantic mesh     用于语义查询、交互区域、对象归属，追求 label 可追溯
```

对 Video2Mesh 最合适的路线是：

1. **短期 P0：COLMAP dense fused PLY + Poisson / Delaunay / Open3D，生成 scene-level collision mesh**  
   这条路和 Azureovo 报告中的 CloudCompare PoissonRecon 思路一致，也是我们最容易自动化接入的 baseline。它适合做静态环境 collider，不适合作最终视觉模型。

2. **短期 P0：语义继续保留在 point / Gaussian 层，不强行塞进 collider**  
   `semantic_splats.ply`、`semantic_gaussian_probabilities.ply`、`masks/3d/*` 继续作为语义主数据。碰撞 Mesh 只做物理代理。

3. **中期 P1：对最终 Mesh 做语义回灌**  
   Mesh 建好、减面、清理之后，再用 KDTree / 半径投票把语义点云或语义 Gaussian 的 `object_id / probability` 转移到 Mesh 顶点或三角面，输出 `scene_collision_semantics.json`。

4. **中期 P1：物体 visual mesh 走 3DGS render depth/normal/mask -> TSDF fusion -> marching cubes / Poisson**  
   这比直接对 sparse object mask cloud 做三角化稳定，也和我们 README 里现有生产方向一致。

5. **长期 P2：引入 SuGaR / 2DGS / GOF / GS2Mesh 类 3DGS-aware surface 方法**  
   这些方法更适合提高 visual mesh 质量，但训练、依赖和数据约束更重，不应阻塞我们先把 collider 和语义层跑通。

最重要的架构判断：

```text
3DGS / semantic splat = 视觉与语义层
Poisson / TSDF / convex proxy mesh = 物理与导航层
scene_graph / sidecar JSON = 交互逻辑层
```

## 1. 当前 Video2Mesh 的约束

当前仓库已经具备几个关键接口：

- `run-colmap` 可以生成 COLMAP sparse model，并在 dense 模式下生成 `external/colmap/dense/fused.ply`。
- `scene/reconstruction/point_cloud.ply` 是默认训练和语义源。
- `fuse-masks` 把 2D masks 投影到点云，输出 `masks/3d/<object_id>/point_indices.json` 和概率文件。
- `export-splat-masks` 可以把 `object_id` 写入 PLY / splat 表示。
- `backproject-gaussian-probabilities` 可以把 2D mask 概率回投到 Gaussian。
- `reconstruct-object-meshes` 和 `reconstruct-3dgs-object-meshes` 已经有 object 级 mesh baseline。
- `export-simulator-assets` 已经有 `collider`、`collision-proxy`、Unity / MuJoCo / Isaac adapter 的概念。

还缺的是一个明确的 **scene-level collision mesh stage**：

```text
external/colmap/dense/fused.ply
  -> scene_collision_raw.ply
  -> scene_collision_clean.glb
  -> scene_collision_semantics.json 可选
  -> simulator_assets/collision/scene_collision.glb
  -> Unity MeshCollider / Web BVH / navmesh source
```

## 2. 方法横评

| 方法 | 输入 | 输出 | 优点 | 风险 | 语义兼容 | Video2Mesh 定位 |
|---|---|---|---|---|---|---|
| CloudCompare PoissonRecon | oriented point cloud | watertight triangle mesh | Azureovo 已验证，GUI 成熟，适合大点云 | GUI/插件自动化弱，Poisson 会补洞和“糊面” | 后处理回灌语义 | collision baseline，可作为人工验证工具 |
| COLMAP poisson_mesher / delaunay_mesher | COLMAP dense fused point cloud | mesh PLY | 和现有 COLMAP dense 直接衔接，CLI 自动化好 | 质量取决于 fused.ply 和照片覆盖 | 后处理回灌语义 | P0 自动化首选 |
| Open3D Alpha / BPA / Poisson | point cloud + normals | mesh | Python 可控，易接入现有 CLI | 参数敏感，稀疏点云会碎 | 可按 object_id 分组或后投影 | P0/P1 编程化 baseline |
| OpenMVS | camera poses + images + sparse cloud | dense cloud, refined textured mesh | 完整 photogrammetry mesh/texturing | 依赖重，AGPL，资源消耗高 | 可从相机和点云回灌 | P1 视觉 mesh 对照组 |
| TSDF fusion / Marching Cubes | posed depth maps / RGB-D / 3DGS rendered depth | smooth mesh | 多视角融合抗噪，适合 object mesh | 需要可靠 depth、尺度、mask | 天然可做 masked semantic fusion | P1 物体 visual mesh 主路线 |
| SuGaR | trained 3DGS | editable mesh + refined GS | 3DGS-aware，几分钟提 mesh | 需要额外训练/优化，集成成本中等 | 可用 semantic splat 约束或回灌 | P2 visual mesh 升级 |
| 2DGS | multi-view images / COLMAP | surface-aligned Gaussians + mesh | 几何比原始 3DGS 更稳 | 替换训练后端，工程改动大 | 需要重新做 semantic transfer | P2 研究后端 |
| GOF | 3DGS-style optimization | level-set mesh | 针对 3DGS surface reconstruction | 新方法，依赖和鲁棒性待验证 | 后处理回灌 | P2 高质量 surface 方向 |
| GS2Mesh | trained 3DGS render stereo pairs | TSDF fused mesh | 不直接相信 Gaussian 几何，用 stereo depth 正则 | 需要 stereo model 和渲染管线 | 可用 semantic mask 渲染做筛选 | P2 适合 in-the-wild 场景 |
| NeuS / VolSDF / Neuralangelo | posed images | neural SDF mesh | 高质量 surface，适合视觉资产 | 训练重，调参重，不适合快速 collider | 可 mask / object-wise 训练 | P3 高质量离线资产 |
| RealityCapture / Metashape | photos / video frames / LiDAR | textured mesh, simplified mesh | 工业成熟，贴图和简化强 | 商业闭源，不好嵌入开源 pipeline | 可外部回灌 | 对照组 / 人工 benchmark |
| V-HACD / CoACD | existing mesh | convex parts | 物理引擎友好，适合动态物体 collider | 不生成视觉表面，只做碰撞近似 | 继承 object 级语义 | P1 dynamic object collider |

## 3. 经典点云建面路线

### 3.1 CloudCompare PoissonRecon

Azureovo 报告中的路线是：

```text
3DGS / splat / PLY
  -> 导出 Gaussian center point cloud
  -> CloudCompare Poisson Surface Reconstruction
  -> Blender / MeshLab 减面
  -> Unity Mesh Collider
```

它的价值是已经被 Web/Unity demo 验证过：视觉层用 3DGS，碰撞层用单独的 GLB mesh。我们本地抓到的 Azureovo public snapshot 也显示 demo 不是动态生成 mesh，而是直接加载：

```text
3dscene/game/3DGS/3DGS.sog
3dscene/game/glb/3dgsCollider.glb
3dscene/game/3DGS/outdoor4.sog
3dscene/game/glb/outdoor4.collision.glb
```

CloudCompare 的 qPoissonRecon 是 Kazhdan Poisson Surface Reconstruction 的界面封装，适合点云到闭合网格。CloudCompare 本身也强调它能处理大型点云和 triangle mesh。

落地判断：

- 适合做人工验证和论文式 baseline。
- 自动化接入时不建议依赖 CloudCompare GUI。
- 如果要自动化，可以优先考虑 COLMAP 自带 `poisson_mesher`、Open3D Poisson，或 CloudComPy 的 PoissonRecon wrapper。
- Poisson 会补洞，可能生成“封口”和虚假表面，所以作为 collider 可以接受，作为 visual mesh 要谨慎。

语义兼容：

- 不要依赖原始点索引，因为 Poisson 会重建新拓扑。
- 建成并减面后，再从 semantic point cloud / semantic splat 向 mesh face center 做 nearest-neighbor / radius vote。

### 3.2 COLMAP dense fused PLY + poisson_mesher / delaunay_mesher

COLMAP 官方 CLI 覆盖了完整的 classic pipeline：

```text
feature_extractor
matcher
mapper
image_undistorter
patch_match_stereo
stereo_fusion
poisson_mesher / delaunay_mesher
mesh_simplifier / mesh_texturer
```

这和我们仓库最契合，因为 `cmd_run_colmap` 已经能跑 dense reconstruction，并把 `colmap_dense_fused_ply` 写进 manifest。也就是说我们不需要重新找数据源，直接从已有 `external/colmap/dense/fused.ply` 往后接就行。

推荐命令形态：

```bash
python -m video2mesh.cli reconstruct-scene-collision-mesh \
  --project-root exports/<run> \
  --source exports/<run>/external/colmap/dense/fused.ply \
  --method poisson \
  --target-triangles 50000 \
  --output exports/<run>/simulator_assets/collision/scene_collision.glb
```

内部可以先封装为：

```text
fused.ply
  -> normal estimation
  -> Poisson / Delaunay
  -> remove low-density vertices
  -> largest components / floor-wall filter 可选
  -> simplify
  -> export PLY/OBJ/GLB
  -> write QA report
```

适用范围：

- 场景级静态 collider。
- 地面、墙体、大型背景结构。
- Web 端 BVH collision mesh。
- Unity static MeshCollider。

不适合：

- 细节展示 mesh。
- 动态刚体 collider。
- 直接承载可靠 object semantic label。

### 3.3 Open3D point-cloud reconstruction

Open3D 官方 surface reconstruction 教程覆盖三类经典方法：

- Alpha shapes
- Ball Pivoting Algorithm
- Poisson surface reconstruction

对我们有两个优点：

1. Python 集成简单，适合直接写进 `video2mesh/cli.py`。
2. 能和语义点云一起工作，比如按 `object_id` 分组重建，或在建面前过滤点云。

方法选择：

| 方法 | 适合 | 不适合 |
|---|---|---|
| Alpha shape | 稀疏、小物体、快速 hull-like baseline | 大场景、噪声多、参数泛化 |
| Ball Pivoting | 点密度均匀、有 normals 的扫描表面 | 点云不均匀、孔洞多 |
| Poisson | 需要闭合/平滑 surface，场景 collider | 开放结构、薄片、真实边界 |

推荐先用 Open3D 做第一个自动化版本，因为现有 object mesh baseline 已经有类似依赖和参数结构。

## 4. 多视角 / 深度融合路线

### 4.1 OpenMVS

OpenMVS 官方 README 明确它补的是 SfM 后半段：输入相机位姿和 sparse point cloud，输出完整 surface，包含：

- dense point-cloud reconstruction
- mesh reconstruction
- mesh refinement
- mesh texturing

典型链路：

```text
COLMAP / OpenMVG sparse model
  -> InterfaceCOLMAP / InterfaceOpenMVG
  -> DensifyPointCloud
  -> ReconstructMesh
  -> RefineMesh
  -> TextureMesh
```

对 Video2Mesh 的价值：

- 可以作为 photogrammetry visual mesh 对照组。
- 比单纯 Poisson collider 更接近 textured visual mesh。
- 可用于评估我们 3DGS-to-mesh 的表面质量。

风险：

- 工程依赖重。
- AGPL 许可证需要谨慎，建议先作为外部 CLI 可选工具，而不是直接链接进核心库。
- 对图片质量、内参、位姿仍然敏感。
- 输出 mesh 未必适合直接做 collider，仍需 decimate / convex decomposition / QA。

### 4.2 TSDF fusion / Marching Cubes

TSDF 是更适合我们“语义 object mesh”的中期路线。

输入可以来自：

```text
真实 RGB-D / LiDAR depth
估计深度
3DGS rendered depth
3DGS rendered normal
object mask / semantic mask
registered camera poses
```

输出：

```text
object_tsdf_volume
object_mesh_raw.ply
object_mesh_clean.glb
object_collider_proxy.glb
```

为什么适合我们：

- 能把多视角 noisy depth 融成一个平滑表面。
- 可以在 integration 前用 object mask 裁剪，只融合目标物体。
- 可以在 integration 时保存 semantic_id / object probability。
- Open3D 和 VDBFusion 都提供可参考的实现路径。

推荐 object mesh 主路线：

```text
trained GraphDECO 3DGS
  + registered cameras
  + 2D/3D object masks
  -> render RGB/depth/normal/mask from selected views
  -> masked TSDF fusion
  -> marching cubes
  -> cleanup / simplify / texture bake
  -> visual mesh + simplified collider
```

对 scene-level collider 也可以用 TSDF，但前提是我们有可靠 depth。纯 RGB + COLMAP dense fused PLY 的情况下，Poisson 更快落地。

## 5. 3DGS-aware surface 方法

### 5.1 SuGaR

SuGaR 的目标是从 3D Gaussian Splatting 表示中快速提取 editable mesh。它通过 surface-aligned regularization 让 Gaussian 更贴近真实表面，再进行 mesh extraction。

优点：

- 比原始 3DGS Gaussian centers 直接建面更合理。
- 项目和代码较成熟。
- 输出 mesh 可以编辑、动画、组合。

风险：

- 需要额外训练/优化，不是从现有 splat 文件一键出稳定 collider。
- 对我们来说更偏 visual mesh，不是 P0 collider。

推荐定位：

- P2：作为 `reconstruct-3dgs-object-meshes` 的高级后端。
- 可以先对小场景或单物体试验，不影响 P0 collider 工程。

### 5.2 2D Gaussian Splatting

2DGS 把 3D Gaussian 体表示压成 2D oriented disks / surfels，并加入几何正则以改善表面一致性。官方实现也强调它设计了 Gaussian splatting 的 meshing approaches。

优点：

- 从表示层减少 3DGS 多视角几何不一致。
- 更适合 surface extraction。

风险：

- 相当于替换/新增训练后端。
- 我们现有 GraphDECO 资产、semantic transfer、viewer PLY 都要适配。

推荐定位：

- P2/P3：研究型后端。
- 如果未来目标是“视觉 mesh 质量优先”，可以和 GraphDECO 并行比较。

### 5.3 GOF

Gaussian Opacity Fields 试图直接从 3D Gaussians 构建 opacity field，并通过 level-set / Marching Tetrahedra 进行自适应紧凑 mesh extraction。

优点：

- 明确针对 3DGS surface reconstruction 的难点。
- 更适合 unbounded scenes。

风险：

- 工程成熟度和鲁棒性需要实测。
- 和我们的语义 pipeline 需要额外桥接。

推荐定位：

- P2：作为 3DGS visual mesh 高质量候选。
- 不作为第一版 collider 路线。

### 5.4 GS2Mesh

GS2Mesh 的核心思想很适合我们：不要直接相信 Gaussian 属性里的几何，而是用 3DGS 渲染能力生成 stereo-aligned novel views，再用预训练 stereo model 得深度，最后 TSDF 融合成 mesh。

这和我们现有方向高度一致：

```text
3DGS render
  -> depth / stereo depth
  -> TSDF fusion
  -> mesh
```

优点：

- 对 in-the-wild 手机扫描友好。
- 把 3DGS 当作多视角渲染器，而不是直接把 Gaussian centers 连面。
- 可以自然接 object mask 和 semantic mask。

风险：

- 需要 stereo model 和渲染/视角采样工程。
- 成本高于 P0 Poisson collider。

推荐定位：

- P1/P2：object visual mesh 的强候选。
- 如果我们已经能从 3DGS 渲染 RGB/depth/mask，GS2Mesh-style stereo depth 可以作为质量增强。

## 6. Neural SDF / NeRF mesh 路线

NeuS、VolSDF、Neuralangelo 都属于 neural implicit surface reconstruction。共同点是用 SDF 或类似隐式场表达表面，再通过体渲染监督从多视角图像中优化几何。

优点：

- 表面质量潜力高。
- 适合复杂物体和高质量离线资产。
- Neuralangelo 对 RGB 视频大场景有代表性。

风险：

- 训练成本高。
- 对相机位姿、曝光、mask、动态物体很敏感。
- 输出到游戏/仿真仍要 decimate、UV、texture bake、collider proxy。

推荐定位：

- P3：高质量离线 visual mesh。
- 不作为当前 collider 主线。
- 可以作为特定 object 的 repair/refinement 后端。

## 7. 工业 Photogrammetry 路线

### 7.1 RealityCapture / RealityScan

RealityCapture / RealityScan 的工业链路通常是：

```text
align images
reconstruct high-poly model
texture
simplify
export
```

官方 CLI 支持 `simplify`、`smooth`、`exportSparsePointCloud`、texture reprojection 等命令。Simplify 工具的目标是降低 triangle count，例如把近似平面的密集三角面合并为更少的面。

对我们有两种价值：

- 作为商业 photogrammetry benchmark，比较我们的 COLMAP/OpenMVS/3DGS-to-mesh 结果。
- 作为人工生产流程参考：高质量视觉 mesh 和轻量 collider 是两套产物。

### 7.2 Agisoft Metashape

Metashape Python API 支持 align photos、build dense cloud、build mesh、texture、decimate model、export results。它适合批处理 photogrammetry，但同样是商业闭源路线。

对我们：

- 不适合作为核心开源依赖。
- 可以用于 benchmark 和对外展示对比。
- 其“模型构建 + decimate + export”的产物组织方式值得参考。

## 8. Collision proxy 和物理约束

Mesh reconstruction 只是第一步。进 Unity / Web / 仿真后，还要把 mesh 变成物理友好的 collider。

### 8.1 Unity MeshCollider 限制

Unity 官方文档强调，concave MeshCollider 有限制：通常只能用于 static 或 kinematic 场景，concave colliders 之间不会直接碰撞。动态刚体更应该使用 convex collider 或 primitive / compound colliders。

所以策略应是：

| 对象 | 推荐 collider |
|---|---|
| 大场景地面/墙体 | simplified static MeshCollider |
| 桌椅柜等静态家具 | box / convex hull / compound collider |
| 动态可交互物体 | primitive / convex decomposition |
| 楼梯/斜坡 | ramp proxy + navmesh |
| 视觉细节复杂物体 | visual mesh 和 physics mesh 分离 |

### 8.2 Blender Decimate

Blender Decimate modifier 用于降低 mesh 顶点/面数，同时尽量保留形状。它适合人工/批处理做 collider 简化，但自动 pipeline 里也可以用 Open3D / trimesh / meshoptimizer 做类似处理。

### 8.3 V-HACD / CoACD

V-HACD 和 CoACD 都是 approximate convex decomposition。它们不是 mesh 重建算法，而是把已有复杂 mesh 拆成多个近似凸部件，方便物理引擎高效碰撞。

对我们：

- scene-level static collider：不一定需要 convex decomposition，简化 mesh 即可。
- dynamic object collider：建议加 CoACD/V-HACD 作为 P1。
- 语义 object 已经分好时，可以按 object mesh 单独做 convex decomposition。

## 9. 语义兼容方案

语义点云和 mesh 重建可以兼容，但要遵守一个原则：

```text
语义不要绑定到 Poisson 前的点索引上，
而要绑定到最终发布的 mesh / object / face group 上。
```

### 9.1 推荐数据流

```text
semantic_splats.ply / semantic_point_cloud.ply
  object_id
  object_probability
  semantic_id
  category
          |
          | KDTree / radius vote / top-k weighted vote
          v
scene_collision.glb
scene_collision_semantics.json
```

### 9.2 Face-level sidecar 格式草案

```json
{
  "schema_version": "0.1",
  "mesh": "scene_collision.glb",
  "source_semantics": "semantic_splats.ply",
  "label_transfer": {
    "method": "face_center_knn_vote",
    "k": 8,
    "max_distance": 0.08,
    "min_probability": 0.5
  },
  "face_groups": [
    {
      "object_id": "floor",
      "semantic_id": 1,
      "category": "floor",
      "face_indices": [0, 1, 2],
      "mean_probability": 0.92
    }
  ]
}
```

### 9.3 语义回灌算法

1. 读取最终发布的 mesh，而不是 raw Poisson mesh。
2. 对每个 triangle 计算 face center 和 normal。
3. 对 semantic point cloud / Gaussian centers 建 KDTree。
4. 查 top-k 邻居，按距离、概率、可见次数加权投票。
5. 设置 `unknown` 阈值，避免强行标注远离语义点云的补洞区域。
6. 对 face graph 做连通域平滑，去掉小碎片标签。
7. 输出 sidecar JSON 和可视化 QA PLY/GLB。

### 9.4 两种语义 mesh 策略

| 策略 | 做法 | 适合 |
|---|---|---|
| 先分割再建面 | 按 object_id 切点云，每个 object 单独建 mesh | 物体 visual mesh、对象级编辑 |
| 先建面再贴语义 | 先生成全场景 collider，再把语义投到 face | 场景 collider、navmesh、floor/wall trigger |

对我们建议两条都保留：

- scene collision mesh：先建面再贴语义。
- object visual mesh：先分割再建面 / TSDF。

## 10. 推荐落地路线图

### P0：自动生成 scene collision mesh

新增 CLI：

```bash
python -m video2mesh.cli reconstruct-scene-collision-mesh \
  --project-root exports/<run> \
  --source auto \
  --method poisson \
  --target-triangles 50000 \
  --output-format glb \
  --write-qa
```

默认 source 查找顺序：

```text
manifest.artifacts.colmap_dense_fused_ply
external/colmap/dense/fused.ply
scene/reconstruction/point_cloud.ply
```

默认输出：

```text
simulator_assets/collision/scene_collision_raw.ply
simulator_assets/collision/scene_collision.glb
simulator_assets/collision/scene_collision_report.json
```

最小 QA：

- vertex / triangle count
- bbox extent
- connected component count
- non-manifold edge count
- watertight flag
- simplification ratio
- source point to mesh distance

### P1：语义回灌到 collider mesh

新增 CLI：

```bash
python -m video2mesh.cli transfer-semantics-to-mesh \
  --project-root exports/<run> \
  --mesh simulator_assets/collision/scene_collision.glb \
  --semantic-ply simulator_assets/semantic_splats.ply \
  --output simulator_assets/collision/scene_collision_semantics.json \
  --method face_center_knn_vote
```

输出还可以包括：

```text
simulator_assets/collision/scene_collision_semantic_preview.glb
simulator_assets/collision/scene_collision_semantic_report.json
```

### P1：object mesh 继续走 TSDF / 3DGS render

我们已有 `reconstruct-3dgs-object-meshes`，应该继续加强：

- view selection
- semantic-support filter
- masked TSDF
- mesh cleanup
- texture bake
- collider simplification

不要把 sparse mask cloud OBJ 当最终物体 mesh。

### P1：dynamic object collider

在 object visual mesh 出来后：

```text
object_mesh.glb
  -> CoACD / V-HACD
  -> object_collider_compound.glb
  -> export-simulator-assets
```

### P2：3DGS-aware mesh 后端试验

候选顺序：

1. SuGaR：最直接的 3DGS-to-editable-mesh 实验。
2. GS2Mesh-style：最符合我们“render views -> TSDF”方向。
3. 2DGS / GOF：适合评估替换训练后端或高质量 surface extraction。

## 11. 和 Azureovo / Icare 案例的关系

Azureovo 报告验证的是一种很实用的架构：

```text
3DGS visual layer
  + invisible collision mesh
  + player controller / interaction logic
```

它没有公开 3DGS-to-mesh 生成脚本，只公开了生成后的 `.sog` 和 `.glb` 资产，以及 Web demo 的加载逻辑。因此我们不能直接“拿它的转换代码”，但可以复用它的架构判断：

- 3DGS 不负责碰撞。
- Mesh collider 不必和视觉 3DGS 一样精细。
- 交互逻辑跑在传统 mesh / physics / controller 上。
- semantic layer 应独立保存，必要时投到 collider 或 trigger 上。

Icare / World Labs 类项目也符合这个分层：Spark/3DGS 做 visual runtime，角色、碰撞、任务、NPC 和 authoring collision helpers 是传统游戏架构。

## 12. 最终推荐

对我们项目，方法优先级如下：

| 优先级 | 要做什么 | 用什么方法 | 原因 |
|---|---|---|---|
| P0 | scene-level static collider | COLMAP dense fused PLY + Open3D/COLMAP Poisson + simplify | 最快补上 Web/Unity 交互闭环 |
| P0 | 保留语义点云主数据 | semantic_splats / gaussian probabilities | 不被 mesh 重建破坏语义 |
| P1 | mesh semantic sidecar | face center KDTree vote | 让 floor/wall/object trigger 可查语义 |
| P1 | object visual mesh | 3DGS rendered depth/mask + TSDF | 比 sparse point cloud mesh 稳 |
| P1 | dynamic collider | CoACD / V-HACD / primitive compound | 符合 Unity/物理引擎要求 |
| P2 | 高质量 3DGS-to-mesh | SuGaR / GS2Mesh / GOF / 2DGS | 提升展示 mesh，不阻塞 collider |
| P3 | neural SDF asset refinement | NeuS / VolSDF / Neuralangelo | 离线高质量，成本高 |

一句话版本：

```text
先用 COLMAP dense fused PLY + Poisson 把场景 collider 做出来；
语义点云继续独立保存；
再把语义回灌到最终 collider face；
物体 mesh 继续走 3DGS render + TSDF；
高质量 3DGS-aware mesh 方法作为后续增强。
```

## 参考资料

### 当前项目和已抓取案例

- Azureovo 3DGS report: <https://azureovo.github.io/3dscene/research/>
- Local public snapshot inventory: `external_code_snapshots/2026-06-30/README.md`
- Video2Mesh pipeline: `README.md`, `VIDEO2MESH_PIPELINE.md`

### Classic SfM / MVS / point-cloud meshing

- COLMAP documentation: <https://colmap.github.io/>
- COLMAP command-line interface: <https://colmap.github.io/cli.html>
- COLMAP tutorial: <https://colmap.github.io/tutorial.html>
- OpenMVS GitHub: <https://github.com/cdcseacave/openMVS>
- OpenMVG OpenMVS docs: <https://openmvg.readthedocs.io/en/latest/software/MVS/OpenMVS/>
- Open3D surface reconstruction: <https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html>
- Open3D RGB-D integration: <https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html>
- Open3D TSDF integration: <https://www.open3d.org/docs/release/tutorial/t_reconstruction_system/integration.html>
- VDBFusion GitHub: <https://github.com/PRBonn/vdbfusion>

### CloudCompare / Poisson

- CloudCompare Poisson Surface Reconstruction plugin: <https://www.cloudcompare.org/doc/wiki/index.php/Poisson_Surface_Reconstruction_%28plugin%29>
- CloudCompare GitHub: <https://github.com/cloudcompare/cloudcompare>
- CloudComPy PoissonRecon wrapper: <https://www.simulation.openfields.fr/documentation/CloudComPy/html/PoissonRecon.html>

### 3DGS-aware mesh

- SuGaR paper: <https://arxiv.org/abs/2311.12775>
- SuGaR project: <https://imagine.enpc.fr/~guedona/sugar/>
- SuGaR GitHub: <https://github.com/Anttwo/SuGaR>
- 2D Gaussian Splatting project: <https://surfsplatting.github.io/>
- 2D Gaussian Splatting GitHub: <https://github.com/hbb1/2d-gaussian-splatting>
- GOF paper: <https://arxiv.org/abs/2404.10772>
- GOF GitHub: <https://github.com/autonomousvision/gaussian-opacity-fields>
- GS2Mesh paper: <https://arxiv.org/abs/2404.01810>
- GS2Mesh project: <https://gs2mesh.github.io/>
- GS2Mesh GitHub: <https://github.com/yanivw12/gs2mesh>

### Neural implicit / NeRF mesh

- Neuralangelo project: <https://research.nvidia.com/labs/cosmos-lab/neuralangelo/>
- Neuralangelo GitHub: <https://github.com/nvlabs/neuralangelo>
- NeuS paper: <https://arxiv.org/abs/2106.10689>
- NeuS project: <https://lingjie0206.github.io/papers/NeuS/>
- VolSDF paper: <https://arxiv.org/abs/2106.12052>
- VolSDF project: <https://lioryariv.github.io/volsdf/>
- Nerfstudio export geometry: <https://docs.nerf.studio/quickstart/export_geometry.html>
- Nerfstudio `ns-export`: <https://docs.nerf.studio/reference/cli/ns_export.html>

### Industry / DCC / physics

- Unity Mesh Collider manual: <https://docs.unity3d.com/6000.2/Documentation/Manual/mesh-colliders-introduction.html>
- Blender Decimate modifier: <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/decimate.html>
- RealityScan CLI commands: <https://rshelp.capturingreality.com/en-US/appbasics/allcommands.htm>
- RealityScan Simplify tool: <https://rshelp.capturingreality.com/en-US/tools/simplify.htm>
- Agisoft Metashape Python API: <https://www.agisoft.com/pdf/metashape_python_api_2_2_0.pdf>
- V-HACD GitHub: <https://github.com/kmammou/v-hacd>
- Unity V-HACD fork: <https://github.com/Unity-Technologies/VHACD>
- CoACD GitHub: <https://github.com/SarahWeiii/CoACD>
- CoACD project: <https://colin97.github.io/CoACD/>
