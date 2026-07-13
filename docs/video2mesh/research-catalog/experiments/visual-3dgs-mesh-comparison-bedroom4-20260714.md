---
title: bedroom_4：GraphDECO、AnySplat 与 SuGaR 视觉和 Mesh 对照实验
id: video2mesh-experiments-visual-3dgs-mesh-comparison-bedroom4-20260714
category: 调研目录
summary: 基于 bedroom_4 的真实 PLY、Mesh 与新视角截图，对比 GraphDECO、AnySplat、SuGaR 三条视觉 3DGS / Mesh 路线，并明确各自能承担的资产角色。
tags:
  - 本项目实验
  - Video2Mesh
  - GraphDECO
  - AnySplat
  - SuGaR
  - 3DGS
  - Mesh
visibility: public
---

# bedroom_4：GraphDECO、AnySplat 与 SuGaR 视觉和 Mesh 对照实验

## 结论

这不是同一输入、同一训练预算下的严格 benchmark，而是对 `bedroom_4` 已真实跑出的资产做统一的视觉和几何审阅。三条路线的分工现在很清楚：

| 路线 | 已观测视角 | 新视角 / 几何问题 | 当前角色 |
|---|---|---|---|
| GraphDECO 30k | 床、墙、灯、窗和材质的照片感最好 | 远处 floaters、拉丝、高亮扩散和异常外扩 Gaussian 仍明显 | **P0 visual layer** |
| AnySplat | 19 张输入即可快速给出完整房间外观，背景比原始 GraphDECO 更收敛 | 墙、窗边和床上方会出现条带、白色漂浮片和拉伸；不是可碰撞表面 | 快速 visual baseline / pose-depth-Gaussian prior |
| SuGaR | 已观测视角下背景更贴墙、窗、地板，refined Gaussian 与可编辑 mesh 都有价值 | 新视角暴露未观测区空洞、薄片和碎裂；raw mesh 仍混入外部 / 背景组件 | P1/P2 visual mesh benchmark |

因此默认资产合同不变：**GraphDECO 负责视觉，COLMAP dense Delaunay 负责场景 collider，SuGaR 和 AnySplat 作为对照与后续升级候选。** 不能因为某一张前视截图更干净，就让 AnySplat 或 SuGaR mesh 直接替代碰撞代理。

## 实验范围与证据

本页只记录真实本地 / `mil8` 产物和实际 viewer QA 图。不同路线的相机、输入帧数和优化预算不同，不能把它们的 Gaussian 数量或训练视角 PSNR 当作可横向比较的 NVS 指标。

| 路线 | 真实输出 | 关键量化证据 | 本页如何解读 |
|---|---|---|---|
| GraphDECO | `bedroom_4` COLMAP -> 30k per-scene optimized Gaussian | 历史 fresh run 的 clean visual PLY 为约 95 万 Gaussian | 视觉主线；以截图检查 floaters 和背景保留 |
| AnySplat | 2 fps 抽帧，19 张 `448 x 448` 输入 | 2,079,470 Gaussian，141,404,377 bytes；inference 4.158s，peak CUDA 约 9.18GiB | 前馈 baseline；重点看新视角条带和相机 / 深度一致性 |
| SuGaR | GraphDECO 30k source -> surface-aligned refinement -> mesh | refined Gaussian 2,399,856；mesh 216,237 vertices / 399,976 faces | surface-aware visual mesh；重点区分 one-sided 显示与真实几何空洞 |

和本页直接相关的语义链路采用的是 **2D mask -> Gaussian probability -> mesh local multi-sample transfer**。早期 `nearest_xyz_transfer_from_base_semantic_3dgs` 结果是历史 baseline，不纳入本页语义质量结论。

## GraphDECO：照片感最好，但不是干净表面

![GraphDECO clean visual 3DGS](../assets/semantic-viewer-20260713/01-graphdeco-visual.png "GraphDECO 30k visual PLY：床、墙、窗和灯的照片感最好，但窗边、右侧和场景外壳存在明显的拉丝与高亮外扩")

GraphDECO 的优势仍是 per-scene optimization：在接近采集相机的视角，床、两侧床头柜、墙面、窗户和地板能形成最完整的视觉层。当前保背景的 clean 策略应该保留墙和地板，不应为了清掉远处小簇而把房间壳体一起删掉。

它的限制也不能被 clean 操作掩盖。图中窗边、右侧、天花和相机轨迹外区域仍有大范围拉丝、半透明高亮片和外扩 Gaussian。这些 Gaussian 可以贡献训练视角的颜色，却没有变成可解释的单层 surface；因此直接从它们的 center 抽 Poisson 或把它们当 collider，都会放大伪影。

**判断：** 保留为默认 visual base，并让 2D semantic probability 直接写回同一份 clean Gaussian geometry；它不是 mesh truth，也不是语义 mesh 的替代品。

## AnySplat：快速且相对收敛，但新视角有前馈条带

![AnySplat observed view](../assets/semantic-viewer-20260713/05-anysplat-visual.png "AnySplat bedroom_4：正面能较完整地看到床、墙、窗和地板，房间外壳比原始 GraphDECO 更集中")

AnySplat 在单张 RTX 3090 上已真实跑通：模型读取 19 张 2fps 输入并预测 Gaussian、相机和深度，前向推理约 4.16 秒。它的正面结果表明模型并不是只拟合主体床，背景墙、地面和窗也被覆盖；相较 GraphDECO，远离主体的随机 floaters 更少，墙面外壳更收敛。

![AnySplat novel-view stripes](../assets/semantic-viewer-20260713/06-anysplat-stripes.png "AnySplat 斜侧视角：墙面、床上方和窗边出现带状漂浮片、白色薄层和局部拉伸")

但新视角暴露出另一类问题：条带和薄层不是普通孤立离群点，靠简单 KNN / DBSCAN 清理无法可靠去掉。它更像前馈 depth、pose 与局部多视角几何没有完全一致的结果。把它直接做 Poisson mesh 会把这些薄层固化；把它做 visual layer 也需要 opacity / scale-aware trimming 和多视角 reprojection consistency 检查。

语义方面，旧 AnySplat 结果曾把 `camera-to-world` 外参误当成 `world-to-camera`，并混用了原始 80 帧 COLMAP mask。当前有效版本使用自己的 19 帧预测相机和对应 `448 x 448` crop mask，先 inverse 成 world-to-camera，再做 2D probability backprojection；该修复只证明投影坐标合同成立，不证明当前实例类别已达到可用精度。

**判断：** 很适合无可靠 COLMAP 时的快速 visual / pose-depth prior，也可做 GraphDECO 初始化候选；不能直接进入 collider、物理或最终 simulator bundle。

## SuGaR：背景更贴表面，但 mesh 和新视角仍要分开审阅

![SuGaR refined Gaussian observed view](../assets/semantic-viewer-20260713/11-sugar-visual.png "SuGaR refined Gaussian：已观测视角下墙、窗、地板和床附近的背景比原始 GraphDECO 更贴近表面")

SuGaR 从 GraphDECO 30k 继续做 surface-aligned Gaussian 优化，refined PLY 有 2,399,856 个 Gaussian，约 595MB binary。它在照片覆盖较好的视角里，背景更贴近墙、窗和地板，房间结构也更像一个连续外壳。这是它优于单纯 Gaussian-center-to-mesh 的实际价值。

![SuGaR refined Gaussian novel view](../assets/semantic-viewer-20260713/12-sugar-new-view.png "SuGaR 换到新视角后，床头上方、窗边、外墙和地面边界出现空洞、拉丝和碎裂")

用户观察到的“墙面 Gaussian 没有规范到平面上去”在新视角里确实成立为现象：墙不再保持连续平面，而是暴露为稀疏碎片和薄层。更准确地说，这说明当前 surface alignment 和观测覆盖不足以约束未见区域；不能从单张图推断 SuGaR 完全没有平面约束。下一步应优先做 visibility / density trimming、墙地平面保护和未观测区 hole handling，而不是只增加 Gaussian 数量。

### SuGaR mesh：先排除单面显示，再判断真正缺失

| 文件 | 真实状态 | 审阅结论 |
|---|---|---|
| `scene_mesh_sugar_coarse.ply` | 16.2MB，216,237 vertices / 399,976 faces | raw coarse mesh 仍保留外部 / 背景组件，不能当作已完成 background removal 的 collider |
| `scene_mesh_sugar_refined.obj` | 48.9MB，216,237 vertices / 399,976 faces | 该 refined export 的主体视觉上更整齐，但它是独立的 refinement / export 路线，不能反推 raw coarse PLY 也做过相同的背景裁剪 |
| `*_double_sided.ply` | 反向复制 triangle winding 的 display companion | 只解决 backface culling 导致的“面消失”；不填洞、不删除外部碎片、不改变原 collider topology |

![SuGaR one-sided mesh symptom](../assets/semantic-viewer-20260713/13-sugar-mesh-before.png "SuGaR mesh 在单面查看时会显得大片缺失；这是 winding/normal 与 backface culling 的显示问题之一")

原始 / coarse mesh 的“背景没有剔除”是实质问题，和单面可见性不是一回事。关闭 backface culling 或使用 double-sided display 后，床、窗和墙的已存在面片会更完整，但外部背景片、顶边碎片、窗边薄片和真实的新视角空洞仍然存在。`scene_mesh_sugar_refined.obj` 看起来更干净，说明 refined export 具有不同的 surface / visibility 筛选效果；后续应把其筛选步骤显式复用到 raw mesh，而不是只靠 viewer 里换一个显示模式。

**判断：** SuGaR mesh 可以做 visual mesh benchmark 和编辑资产研究，不进入当前 P0 collider。进入 Unity / simulator 前至少需要 normal/winding 修复、双面检查、连通域清理、背景/外壳 ROI 裁剪、洞处理和独立的 collider 简化。

## SuGaR 语义：采用 2D probability，不把旧 nearest baseline 重新包装

![SuGaR semantic mesh inspection](../assets/semantic-viewer-20260713/14-sugar-semantic-mesh-before.png "SuGaR semantic mesh 的早期查看症状图：语义颜色审阅仍受单面 mesh 可见性影响，不能仅凭颜色完整度判断分类正确")

当前有效的 SuGaR semantic Gaussian 使用 `svlgaussian_style_ray_to_gaussian_probability_backprojection`：80 帧 2D object probability masks 投影到 refined Gaussian，Top-8 近邻、3px ray radius、4px stride，并启用 occlusion filter。它不是 dense semantic point cloud、3D mask，也不是从旧 GraphDECO semantic PLY 最近邻复制标签。

| 产物 | 实测体量 / 合同 | 使用边界 |
|---|---|---|
| `semantic_sugar_refined_gaussians_2d_probability.ply` | 2,399,856 Gaussian，1.70GB ASCII；foreground 792,631 / background 1,607,225 | 语义回灌 / audit core，**不应直接丢给 SuperSplat** |
| `semantic_scene_mesh_sugar_refined_2d_probability_fixed.ply` | 87.9MB，399,975 faces，1,199,925 个为 face-color debug 重复写出的 vertices | semantic mesh inspection，不替代原始 mesh collider |
| `semantic_scene_mesh_sugar_refined_2d_probability_fixed.json` | local multi-sample face transfer，`inner4`，每 face 4 sample，SciPy cKDTree | 可追溯 face label / probability；还需单独评估 instance merge 和类别准确率 |

语义全量 PLY 太大导致无法直接打开，不是“语义更多所以视觉更好”。它需要像 GraphDECO / AnySplat 一样拆成 binary semantic core 和受预算限制的轻量 overlay；语义颜色用于审阅，原始 visual PLY 仍是展示底图。当前 29 个 label 中仍存在多 lamp / plant 等重复实例，这反映 2D discovery / tracking 的实例合并问题，不能用 3D mesh 上的颜色去掩盖。

## 推荐的分层接入

```text
COLMAP dense Delaunay mesh
  -> 低面数、保守的 scene collider / raycast / ground probe
GraphDECO clean 3DGS
  -> 默认 visual layer
2D mask probability -> semantic Gaussian / semantic mesh sidecar
  -> object query、inspection、后续 instance merge，不替代视觉或碰撞
AnySplat
  -> 快速 prior / baseline / COLMAP 失败 fallback
SuGaR refined Gaussian + repaired visual mesh
  -> P1/P2 high-quality visual mesh and editable-asset benchmark
```

后续修复优先级应为：

1. 保持 GraphDECO 的背景保护 clean，单独清除远离 COLMAP dense bbox 的孤岛簇。
2. 对 AnySplat 做 depth / pose consistency、opacity-scale trimming 和固定相机 QA，而不是盲目增大输入帧数后直接建 mesh。
3. 将 SuGaR refined OBJ 的有效 visibility / surface 筛选拆成显式、可复现步骤，再对 raw mesh 做 connected-component / background ROI 清理。
4. 对语义实例做跨帧 identity 和 3D spatial merge，随后重新做 2D probability 投影融合；不从 3D mask 或历史 semantic PLY 回灌。

## 相关记录

- [语义 3DGS、SuperSplat 与双面 Mesh 修复](#/doc/video2mesh-experiments-semantic-3dgs-viewer-contract-20260713)
- [AnySplat 研究与 bedroom_4 实测](#/doc/video2mesh-visual-3dgs-anysplat)
- [SuGaR 研究与 bedroom_4 mesh 观察](#/doc/video2mesh-mesh-reconstruction-sugar)
- [COLMAP Delaunay 场景 collider 实验](#/doc/video2mesh-experiments-colmap-delaunay-experiment)
