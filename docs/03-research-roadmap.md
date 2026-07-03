---
title: 技术调研与选型报告
category: Research
summary: 汇总 World Labs、Azureovo 网站、image-blaster、3DGS-to-mesh、SimAnything/PhysSplat 等路线，落到 Video2Mesh 的可执行技术选型。
tags:
  - Research
  - Scene Graph
  - Mesh
  - 3DGS
  - World Labs
  - SimAnything
---

# 技术调研与选型报告

## 总结判断

Video2Mesh 不应该追求“从视频一步生成一个完美 mesh”。更稳的产品形态是分层资产包：

```text
scan video
  -> pose / dense geometry
  -> 3DGS visual proxy
  -> semantic masks / semantic splats
  -> visual mesh / repaired object mesh
  -> collider mesh / primitive proxy
  -> scene graph / physics metadata
  -> Web / Unity / MuJoCo / Isaac adapters
```

本次调研后，推荐的主线是：

| 层 | 当前选型 | 为什么 |
|---|---|---|
| 位姿和稠密几何 | COLMAP dense workspace；失败时 MASt3R/DUSt3R/VGGT 兜底 | COLMAP 输出标准，能直接接 GraphDECO、Delaunay mesher、CloudCompare/Open3D |
| 视觉代理 | GraphDECO 3DGS，Web 端用 Spark/SuperSplat 类 runtime | 画质和实时展示最好，适合做扫描场景的 photoreal visual layer |
| 场景级碰撞代理 | COLMAP dense workspace + `delaunay_mesher`；辅以 Poisson/voxel mesh | 我们实测 Delaunay dense mesh 最接近 3MB collider 目标，碎片少于直接 raw fused Poisson |
| 物体 visual mesh | 3DGS rendered RGB/depth/mask + TSDF；GS2Mesh-style stereo depth 作为增强 | 不直接相信 Gaussian center / scale，而是把 3DGS 当多视角渲染器提取 depth evidence |
| 高质量 3DGS-to-mesh benchmark | GS2Mesh、SuGaR、2DGS/GOF、3DGS-to-PC | 用于对照和局部升级，不作为 P0 collider 主链路 |
| 遮挡补全 | image-blaster/Hunyuan3D/Meshy/TRELLIS 生成 object-local mesh，再 fit 回场景 | 生成式 mesh 擅长补全物体外观，但尺度、朝向、支撑面必须由 Video2Mesh 校准 |
| 语义和交互 | semantic splats/point labels + mesh face semantic sidecar + scene graph | 不把语义硬塞进视觉或碰撞资产，按 face/object/affordance 独立查询 |
| 动态仿真 | SimAnything/PhysSplat-style dynamic Gaussian 作为 P2 旁路线 | 它们解决动态 Gaussian/物理属性估计，不替代 mesh collider |

核心原则一句话：**3DGS 做视觉代理，mesh/collider 做碰撞代理，semantic sidecar 做语义查询，physics sidecar 做仿真合同。**

## 参考项目与边界

| 项目 / 来源 | 它真正提供什么 | Video2Mesh 应该怎么借 | 不应该误解成 |
|---|---|---|---|
| Azureovo 学长 3D Scene Research | 3DGS 视觉层 + CloudCompare/Poisson/Unity Collider 的可交互场景路线；网页 demo 中 `.splat/.sog` 视觉资产和 `.glb` collision mesh 分离 | 借它的“视觉代理 + 碰撞代理”架构、3MB 级 collider 目标、Web/Unity 对齐思路 | 直接从 3DGS PLY 点中心稳定得到高质量 mesh |
| World Labs / Marble | 静态 world/background 生成，资产中包含 splat/SPZ、pano、collider mesh 等多层输出 | 借 clean plate/background repair 思路，以及环境视觉资产和 collider 资产分开交付的产品形态 | 物体级仿真资产生成器或 Video2Mesh 替代品 |
| Spark / SuperSplat 类 Web runtime | 高斯场景实时渲染、压缩格式和浏览器展示 | 作为 Web visual proxy runtime；raycast/collision 仍交给 mesh | 3DGS 本身提供物理碰撞 |
| image-blaster | 从单图/裁剪图生成 object mesh；按 `worlds/<world>/output/<object>/` 管理资产；React/Three/Rapier viewer | 作为 object completion helper，接在 `prepare-object-images -> export-image-blaster -> import-object-meshes` 后 | `simulator_asset_bundle.json`、Unity/MuJoCo/Isaac adapter 的拥有者 |
| COLMAP / CloudCompare / PoissonRecon | 经典 SfM/MVS 和点云建面工具链 | P0 scene collider、对照 mesh、手工/半自动检查 | 遮挡物体补全或语义理解 |
| SuGaR | 让 Gaussians surface-aligned，再提取可编辑 mesh，并可把 Gaussians 绑定到 mesh | P2 visual mesh benchmark，适合单物体/小场景高质量对照 | P0 collider 主路线 |
| GS2Mesh | 从 3DGS 渲染 stereo novel views，用 stereo depth + TSDF 得 mesh | P1/P2 object mesh 质量增强，和我们的 rendered depth/mask 路线最契合 | 直接读取 Gaussian center 连面 |
| SimAnything / PhysSplat | MLLM 估计物理属性，semantic Gaussian/particle dynamics，动态 splat 渲染 | P2 动态对象和物理属性草稿路线 | mesh 补全、Unity collider 或 MuJoCo rigid body 替代品 |

## World Labs、Spark 与网页架构

World Labs / Marble 和学长网页给出的工程信号很一致：交付的不是“一个万能 3D 文件”，而是一组分层资产。

```text
world visual splat / SPZ / SOG
  + pano / environment map
  + collider mesh GLB
  + semantic / scale / ground metadata
  + viewer/controller/runtime code
```

本地 `image-blaster` 的 world 路径也印证了这一点：

- `image-blaster/.claude/scripts/world/generate-world.mjs` 调 World Labs Marble `worlds:generate`，下载 `collider_mesh_url` 为 `*-world.glb`，下载 `pano_url`，并保存 `spz_urls`。
- `image-blaster/app/src/utils/worldLoader.ts` 和 `WorldViewer.tsx` 只接受 `/worlds/...` 本地资产 URL，不在 viewer 里直接读 provider URL。
- `SplatRenderer.tsx` 用 Spark `SparkRenderer` / `SplatMesh` 渲染 splat，并显式禁用 raycast。
- `WorldCollider.tsx` 把 GLB 放进 Rapier fixed trimesh rigid body；object 侧 `SceneObject.tsx` 则用 GLB visual + box collider/rigid body 处理交互。

这和我们现在的 Web demo 方向一致：

```text
GraphDECO 3DGS PLY / SPZ / SOG
  -> Spark visual layer

COLMAP Delaunay / Poisson / simplified GLB
  -> raycast
  -> ground probe
  -> forward block
  -> Unity MeshCollider / Web physics proxy
```

因此 Video2Mesh 的目标不是把 3DGS 变成物理引擎，而是产出一个“视觉、碰撞、语义、物理”分层的 asset bundle。

## image-blaster 技术定位

image-blaster 更像 object mesh generation + viewer asset convention，而不是扫描重建 pipeline。

它的可借点：

- 目录约定：`worlds/<world>/output/<object>/object.json`、编号参考图、编号 mesh。
- 生成链路：先得到干净 reference image，再调用 Hunyuan3D/Meshy/FAL 类后端生成 mesh。
- Viewer 约定：GLB 是最稳的交互模型格式；Three.js 加载 visual，Rapier 包裹 collider。
- World 链路：World Labs 负责 static world/background，object mesh 单独生成和摆放。

接入 Video2Mesh 的正确位置：

```text
Video2Mesh object masks / selected frames
  -> prepare-object-images
  -> export-image-blaster
  -> image-blaster / Hunyuan / Meshy jobs
  -> import-object-meshes
  -> fit-object-local-meshes-to-bbox
  -> export-simulator-assets
```

注意边界：

- image-blaster 生成的是 object-local visual mesh；它不知道我们场景的真实尺度、相机坐标、support plane 和 object_id 置信度。
- `simulator_asset_bundle.json`、physics defaults、Unity/MuJoCo/Isaac adapter 仍应该由 Video2Mesh 生成。
- 遮挡补全要拆成 object completion 和 background clean plate，不能用物体 mesh 自动修复背后的地板/墙面。

## 3DGS 到 Mesh 路线横评

我们已经验证过：直接从 3DGS PLY 里的 Gaussian center 当点云去 Poisson，容易得到碎片、大薄片、漂浮物和错位面。原因是 3DGS 优化目标主要是照片一致性，不保证 Gaussian center 采样在真实表面上，也不保证 `scale/rot/opacity` 可以直接解释成 watertight surface。

更合理的路线如下：

| 方法 | 输入 | 产物 | 优点 | 风险 | 当前优先级 |
|---|---|---|---|---|---|
| COLMAP dense + Delaunay | dense workspace / fused geometry | scene mesh / GLB collider | 与 COLMAP 原生数据一致，我们实测体量和效果最接近 collider 目标 | 适合场景级 static collider，不适合物体补全 | P0 |
| CloudCompare/Open3D Poisson | 点云 + normals | watertight-ish mesh | 快速、传统、好自动化；voxel/downsample 后可得到较平滑场景 mesh | 会补洞，可能生成悬浮物/薄片；语义边界差 | P0/P1 |
| Voxel / TSDF fusion | posed depth maps / rendered depth | smooth mesh | 抗噪，适合 object visual mesh 和场景代理 | 依赖 depth 和 mask 质量 | P1 |
| GS2Mesh-style | trained 3DGS -> stereo rendered views -> stereo depth -> TSDF | geometrically consistent mesh | 不直接相信 Gaussian geometry，借 3DGS novel view + stereo prior | 需要视角采样、stereo 模型、TSDF 参数 | P1/P2 |
| SuGaR | 3DGS checkpoint + surface alignment optimization | editable mesh + refined Gaussian | 适合可编辑 visual mesh 和高质量 benchmark | 额外训练/优化，P0 成本高 | P2 |
| 2DGS / GOF / surface-aware GS | 替换或增强 Gaussian 表面约束 | 更 surface-friendly 的 GS/mesh | 从训练端解决几何不贴面问题 | 替换后端成本较高 | P2 |
| 3DGS-to-PC / sampled surface Gaussians | 3DGS -> sampled point cloud -> Poisson | point cloud / mesh | 可作为无重训转换工具 | 仍需处理 floaters、normal、采样策略 | P2 |
| Neural SDF / NeuS / VolSDF | posed images / masks | high-quality mesh | 表面质量强 | 训练慢，和 3DGS 主链路并行成本高 | P3 |

当前最实用的落地策略：

```text
scene collider:
  COLMAP dense workspace -> delaunay_mesher -> simplify -> GLB

object visual mesh:
  3DGS render RGB/depth/mask -> masked TSDF -> cleanup -> GLB

high-quality benchmark:
  GS2Mesh and SuGaR on selected objects / small scenes
```

## COLMAP、CloudCompare 与 PoissonRecon 选型

CloudCompare 是点云/三角网格处理软件，PoissonRecon 是其常用建面插件/功能。它适合人工检查和半自动对照：

```text
point cloud
  -> normal estimation
  -> Poisson Surface Reconstruction
  -> trim / clean / simplify
  -> PLY/OBJ/GLB
```

但对我们当前 bedroom 类场景，经验结论是：

- 直接对 `fused.ply` 或 3DGS center PLY 跑 Poisson，容易得到大薄片和悬浮壳。
- dense point cloud 先做 voxel/downsample/outlier cleanup，再 Poisson，能得到较平滑 scene mesh，但仍要清理悬浮物。
- COLMAP 原生 `delaunay_mesher` 从 dense workspace 建面更稳，适合做 3MB 级 static collider。
- Poisson/voxel mesh 可以作为 visual inspection 或 fallback collider，不应该作为唯一生产路线。

因此选型是：

| 用途 | 推荐 |
|---|---|
| Web/Unity static scene collider | COLMAP dense + Delaunay mesh |
| 快速人工检查 | CloudCompare PoissonRecon / MeshLab / Blender |
| 自动化 fallback | Open3D Poisson with voxel/downsample/outlier cleanup |
| object visual mesh | 3DGS rendered depth/mask + TSDF，而不是 raw point Poisson |

## 语义回灌与 Mesh 分类

Mesh 分类不能只靠三角面最近的一个 semantic point。床面、墙面、桌面和薄片很容易串语义。更稳的做法是分层回灌：

```text
P0: semantic splats / semantic point cloud -> mesh face KDTree vote
P1: mesh face center -> project to multi-view masks -> visibility weighted vote
P2: face graph smoothing + object support constraints + VLM relation QA
```

推荐的 semantic sidecar 结构：

```json
{
  "mesh": "colliders/scene_collision.glb",
  "face_semantics": [
    {
      "face": 1024,
      "object_id": "bed_01",
      "label": "bed",
      "probability": 0.91,
      "source": "semantic_splats+multiview_masks"
    }
  ]
}
```

交互时：

```text
raycast hit
  -> triangleIndex
  -> face_semantics[triangleIndex]
  -> object_id / label / affordance / physics material
```

这比把语义直接烘进 GLB 顶点色更可靠，因为 collider 可以简化、替换、双面化，但 sidecar 仍能保留 face/object 级语义合同。

## SimAnything / PhysSplat 选型

SimAnything / PhysSplat 的目标不是把 3DGS 转成 mesh，而是让 static 3D scene 获得可交互动态：

```text
static 3DGS / scene reconstruction
  -> object-level open-vocabulary segmentation
  -> MLLM physical property estimation
  -> particle / Gaussian dynamics
  -> dynamic splat rendering
```

对 Video2Mesh 的价值：

- 用 MLLM/VLM 给每个 object 生成物理属性草稿：材质、质量范围、摩擦、恢复系数、刚体/软体候选。
- 对 pillow、blanket、cloth、plant、liquid、granular 等对象探索 dynamic Gaussian assets。
- 作为展示层显示“物体受力后的视觉变形”，而不是只输出传统 rigid-body mesh。

不适合：

- 替代 COLMAP/3DGS 重建。
- 替代 object visual mesh。
- 替代 Unity/MuJoCo/Isaac collider。
- 直接生成可相信的工程物理参数。

Video2Mesh 的接入点应该是：

```text
prepare-simulator-physics-jobs
  -> mllm_physics provider
  -> import-simulator-physics
  -> simulator-physics-quality-report

simulator_assets/dynamic_gaussian_assets/
  objects/<object_id>/gaussians.ply
  objects/<object_id>/physics.json
  simulations/<sim_id>/trajectory.npz
```

也就是说，SimAnything/PhysSplat 是 P2 动态旁路线，不动 P0/P1 的 visual 3DGS + collider mesh 主合同。

## 当前阶段技术选型

### P0：可展示、可交互、可传回本地

- COLMAP dense + GraphDECO 30k 3DGS。
- 3DGS PLY 清理 floaters 后做 visual proxy。
- COLMAP dense workspace + Delaunay mesh 做 scene collider。
- Web demo / Unity 用 collider mesh 做 raycast、ground probe、obstacle blocking。
- semantic sidecar 先用 point/splat -> face KDTree voting。

验收标准：

- 3DGS 视觉层和 collider mesh 对齐。
- collider 体量在几 MB 到几十 MB 可控范围。
- raycast 命中的是 mesh，不是 splat。
- semantic face debug PLY 至少能看出大类区域，低置信度可标 unknown。

### P1：物体级资产和补全

- 对床、桌、椅、柜等 foreground object 做 3DGS rendered depth/mask + TSDF。
- 对遮挡严重物体，用 image-blaster/Hunyuan/Meshy/TRELLIS 生成完整 visual mesh。
- 生成式 mesh 必须经过 bbox fit、support plane align、scale QA。
- collider 用 primitive/convex/compound proxy，不直接拿复杂 visual mesh 当 dynamic collider。
- mesh semantic 回灌升级到 multi-view projection voting。

验收标准：

- 物体 visual mesh 不再是碎点云连面。
- dynamic object collider 稳定，不穿地、不爆炸。
- `simulator_asset_bundle.json` 能明确记录 visual/collider/semantic/physics 的资产引用。

### P2：高质量 Mesh 与动态 Gaussian

- GS2Mesh-style stereo depth 对 selected objects / small scenes 做 benchmark。
- SuGaR / 2DGS / GOF 对比训练端 surface-aware 方法。
- SimAnything/PhysSplat-style MLLM physics draft 和 dynamic Gaussian demo。
- Scene graph 引入 support/on/inside/near/affordance 关系。

验收标准：

- 能证明 GS2Mesh/SuGaR 相比 TSDF 或 Delaunay 的质量收益。
- dynamic Gaussian 只作为视觉动态层接入，不破坏传统 simulator adapter。
- 语义、物理、交互逻辑可以在 Web/Unity 中按 object_id 查询。

## 实现建议

近期最值得做的不是再盲跑更多 raw Poisson，而是把已经验证有效的几条路线固化成稳定命令和报告：

1. 固化 `COLMAP dense -> delaunay_mesher -> simplify -> GLB collider`。
2. 固化 `3DGS clean PLY -> Spark visual layer`。
3. 固化 `collider GLB + semantic face sidecar -> Web/Unity raycast label`。
4. 把 `3DGS rendered depth/mask -> TSDF object mesh` 作为 P1 主开发。
5. 把 image-blaster/Hunyuan/Meshy 作为 object completion provider，而不是主重建器。
6. 把 GS2Mesh/SuGaR 作为 benchmark 后端，选 1-2 个物体或小场景做对照即可。
7. SimAnything/PhysSplat 先落到 physics draft 和 dynamic Gaussian 目录合同，不进入 P0 collider。

## 参考资料

| 主题 | 链接 |
|---|---|
| Azureovo  3D scene research | [https://azureovo.github.io/3dscene/research/](https://azureovo.github.io/3dscene/research/) |
| World Labs | [https://www.worldlabs.ai/](https://www.worldlabs.ai/) |
| World Labs Platform | [https://platform.worldlabs.ai/](https://platform.worldlabs.ai/) |
| Spark | [https://sparkjs.dev/](https://sparkjs.dev/) |
| image-blaster | [https://github.com/neilsonnn/image-blaster](https://github.com/neilsonnn/image-blaster) |
| COLMAP | [https://colmap.github.io/](https://colmap.github.io/) |
| CloudCompare | [https://www.cloudcompare.org/](https://www.cloudcompare.org/) |
| GS2Mesh | [https://gs2mesh.github.io/](https://gs2mesh.github.io/) |
| SuGaR | [https://anttwo.github.io/sugar/](https://anttwo.github.io/sugar/) |
| PhysSplat / SimAnything paper | [https://arxiv.org/abs/2411.12789](https://arxiv.org/abs/2411.12789) |
