---
title: Auto-SuperSplat 式 3DGS 剔除与修补
id: auto-supersplat-repair
category: 调研目录
summary: 调研如何把人工在 SuperSplat 中清理漂浮 splat、修补平面空洞的操作，转成 Video2Mesh 可执行的自动点云/3DGS 修复循环。
tags:
  - Research Catalog
  - 3DGS
  - Point Cloud Repair
  - SuperSplat
  - Floater Cleaning
visibility: public
---

# Auto-SuperSplat 式 3DGS 剔除与修补

这篇报告整理一个更贴近工程直觉的方向：把人类在 SuperSplat 里做的“看见悬浮点就框选删除、看见墙面/地面洞就局部补 splat、再换视角检查”的编辑流程，抽象成 Video2Mesh 的自动修复循环。

核心判断是：**剔除可以先做成高可靠的小模型/规则系统，修补必须先限制在平面和局部 patch，不能一上来让模型自由生成整片场景。**

## 我们的目标流程

```text
trained 3DGS / SuperSplat PLY
  -> 选择诊断视角并渲染 RGB / alpha / depth / normal hint
  -> 找出悬浮伪影、边缘光斑、平面洞、缺损薄片
  -> 用 2D mask 或屏幕框选定位问题区域
  -> 回投到 Gaussian id 或局部平面 patch
  -> 执行 delete / attenuate / copy-fill / refit
  -> 多视角重新渲染 QA
  -> 不合格则回滚或进入下一轮
```

这不是把 3DGS 变成真实 mesh，而是做一个 **visual repair layer**。修复后的 splat 仍然只负责视觉；碰撞、导航和交互仍然应该走 COLMAP Delaunay、primitive/convex collider 或人工确认的 mesh。

## 剔除：从人工框选到自动删除

人工在 SuperSplat 里删悬浮点时，通常依赖几类信号：

- 看起来漂在空中，没有连接到真实表面。
- 透明、细长、拉丝，常出现在物体边缘、墙角、窗帘边缘或视角覆盖不足处。
- 换一个视角后仍然像噪声，而不是薄结构。
- 删除后主要画面变干净，不造成真实物体缺口。

对应到自动系统，最好不要直接让 GroundingDINO 识别“伪影”。GroundingDINO 更适合开放词汇物体检测，而悬浮 splat 是几何/渲染异常。更轻的路线是：

```text
规则候选:
  opacity 低
  scale 过大或 anisotropy 过高
  kNN 邻域距离异常
  小连通分量
  远离 floor/wall/ceiling/object support
  多视角可见性不稳定

小模型判别:
  LightGBM / XGBoost / RandomForest / 小 MLP
  输入 Gaussian 属性 + 局部几何 + 多视角投影统计
  输出 delete_probability

安全执行:
  只删除高置信候选
  对薄结构、物体边界、背景平面做保护
  保存 deleted_gaussians sidecar 和 before/after QA
```

这个阶段可以直接复用 Video2Mesh 现有的 `clean-3dgs-floaters` 思路：先用 kNN、opacity、elongation 生成候选，再让小模型学习“人会删哪些候选”。第一版甚至可以不训练模型，只做规则 + 多视角 QA；等积累人工编辑样本后再训练分类器。

## 修补：先补平面洞，不补任意物体

平面洞和悬浮点相反：它不是“删掉坏 splat”，而是“在缺少视觉覆盖的位置插入一批可信 splat”。这件事风险更高，因为新加的 Gaussian 很容易变成新的光斑、糊块或跨视角漂浮。

第一版应该只支持 floor / wall / ceiling / cabinet side 这类近似平面：

```text
plane mask / plane equation
  -> 渲染 alpha/depth 找低覆盖洞
  -> 在同平面邻域采样 donor Gaussians
  -> 复制颜色、opacity、scale、rotation 的局部分布
  -> 将新 Gaussian 投影到洞所在平面
  -> 按邻域颜色和深度做平滑
  -> 多视角检查是否漂浮、闪烁、过糊
```

补点时不能只复制 `xyz + RGB`。GraphDECO / SuperSplat PLY 里还包含 `opacity`、`scale_0/1/2`、`rot_0/1/2/3`、`f_dc_0/1/2` 等属性；这些属性决定 splat 的大小、方向、透明度和视角外观。更稳的策略是从洞周围同平面、同颜色、同尺度的 donor splats 采样属性，而不是凭空生成。

物体缺损不建议用这套平面复制法硬补。床头柜、椅子、被遮挡物体这类缺损，应该走 object-level completion：selected frames + mask + depth -> 多视角补图 -> InstantMesh / Hunyuan3D / Restore3D-like object mesh -> bbox 回填。

## 学术方法映射

| 方向 | 代表方法 | 可借鉴点 | 对 Video2Mesh 的定位 |
|---|---|---|---|
| Floater 专项抑制 | TIDI-GS | 训练中周期性识别 floaters，结合跨视角一致性、空间关系、重要性分数和 monocular depth regularizer | P1/P2，可把当前 post-cleaner 升级成训练中 cleanup hook |
| 语义 mask 引导剪枝 | Clean-GS | 用少量语义 mask 做 whitelist filtering、depth-buffered color validation 和邻域离群清理 | 适合 object/background 局部清理，不适合作无语义的全局修补 |
| 后验重要性剪枝 | PUP 3D-GS、LightGaussian | 用 sensitivity/global significance 判断哪些 Gaussian 对重建贡献小，剪掉后再 refine | 可作为“删除不重要 splat”的二级信号，但不等价于视觉伪影检测 |
| 表面约束 3DGS | 2DGS、SuGaR、GOF | 把 Gaussian 推向可解释表面，减少 disconnected/unorganized Gaussians，支持 mesh extraction | 更适合从训练路线减少空洞/伪影，不是简单后处理 |
| 从 3DGS 渲染到 mesh | GS2Mesh | 让 3DGS 渲染 stereo views，再估深并 TSDF fusion，绕开直接连 Gaussian center 的噪声 | 可作为平面/物体修补后的 visual mesh benchmark |
| Gaussian 级分割编辑 | Gaussian Grouping、SAGA、LangSplat、GaussianEditor | 把 SAM/语言/文本指令映射到 Gaussian RoI，支持局部删除、颜色修改、object removal/inpainting | 支撑“像人一样圈选 Gaussian”的交互与自动化 |
| 点云去噪/上采样 | PointCleanNet、Score-Based Denoising、PU-Net | 学习 outlier classification、点投影修正、局部上采样 | 可用于小模型训练数据和几何特征设计，但需适配 Gaussian 属性 |
| 3DGS inpainting | Inpaint360GS、SplatFill、3DGIC 等 | object removal 后用多视角/深度一致 inpainting 重建缺失背景 | 适合作 P2 背景 clean plate，不是 P0 稳定链路 |

这组方法给出的共同结论很清楚：**真正可靠的 3DGS 修复不是单张图检测，而是 Gaussian 属性、2D mask、深度、跨视角一致性和局部几何约束一起投票。**

## 工业界和工具链启发

SuperSplat 的价值不只是能打开 `.ply`，而是它把 3DGS 后处理变成了一组很具体的编辑动作：选择、裁剪、删除、变换、优化、发布。PlayCanvas 官方文档也明确把清理 raw splat captures、trim floaters、crop scenes、retouch colors 作为编辑器核心功能。

这说明工业工作流默认承认一件事：**3DGS 训练结果经常需要人工清理**。我们的方向就是把这一步变成可重复、可记录、可 QA 的自动过程：

```text
SuperSplat manual edit
  -> operation log
  -> Gaussian id mask
  -> before/after render QA
  -> train keep/delete classifier
  -> auto edit proposal
  -> human approval only for uncertain patches
```

移动扫描工具如 Scaniverse、Luma、KIRI 等也在把 Gaussian capture 推向消费级，但它们通常更强调采集、裁剪、导出和浏览；对 Video2Mesh 来说，真正要补的是“可解释的修复 sidecar”和“可回滚的编辑历史”。

## 推荐实现：Auto-SuperSplat Editor

### P0：自动剔除候选和回滚

输入：`scene_3dgs_ply`、camera_info、可选 semantic/background masks。

输出：

| 产物 | 说明 |
|---|---|
| `edited_clean.ply` | 删除或降低 opacity 后的 splat |
| `deleted_gaussians.json` | 被删除 Gaussian id、原因、置信度 |
| `repair_report.json` | before/after 指标和阈值 |
| `qa_renders/` | 多视角对比图 |

第一版策略：

```text
clean-3dgs-floaters candidates
  -> background plane protection
  -> feature extraction
  -> rule score / optional LightGBM score
  -> delete only high-confidence floaters
  -> render QA
```

关键保护：

- floor / wall / ceiling 大平面不因低密度被误删。
- curtain、plant、chair leg、lamp wire 等薄结构进入 uncertain，不直接删。
- 每次编辑生成 sidecar，支持恢复 raw splat。

### P1：平面洞 copy-fill

输入：平面 mask、plane equation、diagnostic views、clean splat。

输出：

| 产物 | 说明 |
|---|---|
| `edited_filled.ply` | 增加平面 patch 后的 splat |
| `inserted_gaussians.json` | 新增 Gaussian 的来源、donor、属性生成规则 |
| `hole_masks/` | 每个视角的洞区域 mask |
| `fill_qa_report.json` | alpha/depth/color/multiview consistency 指标 |

第一版只做保守复制：

```text
hole alpha mask
  -> fit local plane
  -> sample target positions on plane
  -> find donor splats from same plane ring
  -> copy color/opacity/scale/rotation statistics
  -> clamp scale and opacity
  -> QA: if new view flicker or depth off-plane -> rollback
```

### P2：小模型学习人的编辑偏好

训练数据来源：

- 现有规则 cleaner 的候选。
- SuperSplat 人工删除记录。
- before/after render 中人工标注的 `keep/delete/uncertain`。
- 合成数据：从干净 3DGS 中随机插入 floater、挖平面洞、生成伪影。

推荐模型：

```text
Gaussian keep/delete classifier:
  LightGBM / XGBoost / RandomForest / MLP

Plane-hole repair acceptor:
  小 CNN / MLP / rule ensemble
  判断填补 patch 是否需要 rollback
```

特征建议：

| 特征组 | 内容 |
|---|---|
| Gaussian 属性 | opacity、scale、anisotropy、rotation norm、SH/RGB |
| 局部几何 | kNN 距离、局部密度、PCA 平面性、connected component size |
| 视角证据 | 可见视角数、mask 覆盖、alpha contribution、depth residual |
| 语义/结构 | 是否在 floor/wall/ceiling/object bbox 内，是否接近 support plane |
| 编辑历史 | 规则 cleaner 是否命中、人工是否删除、上轮 QA 结果 |

## QA 指标

剔除成功不等于删得多，修补成功也不等于填得满。建议用这些 gate：

| Gate | 通过条件 |
|---|---|
| visual artifact reduction | 目标区域漂浮 splat / 光斑 alpha 面积下降 |
| no-new-hole | 真实表面 alpha 覆盖不能显著下降 |
| multiview consistency | 多个诊断视角下 patch 不闪烁、不漂浮 |
| plane consistency | 新 splat 到目标平面的距离低于阈值 |
| color continuity | 新 patch 与邻域颜色差低于阈值 |
| edit budget | 单轮删除/新增 Gaussian 数量受限 |
| provenance | 每次 delete/insert 都能追溯原因和来源 |

## 和当前 Video2Mesh 的接点

当前仓库已经有三个重要入口：

- `clean-3dgs-floaters`：已有 kNN、opacity、elongation 的后处理 cleaner。
- `backproject-gaussian-probabilities`：已有 2D mask 回投到 Gaussian 的 SVLGaussian-style 雏形。
- `infer-background-plane-masks`：已有 floor/wall/ceiling 等背景平面结构推断入口。

因此新增模块不需要推翻 pipeline，建议只加一个实验命令：

```text
python -m video2mesh.cli auto-supersplat-repair \
  --project-root exports/<run> \
  --mode prune \
  --splat-ply scene/reconstruction/3dgs/.../point_cloud_clean.ply \
  --camera-info scene/cameras/camera_info.json \
  --preserve-background-planes \
  --write-qa-renders

python -m video2mesh.cli auto-supersplat-repair \
  --project-root exports/<run> \
  --mode fill-plane-holes \
  --plane-source masks/background_planes \
  --max-inserted-gaussians 20000 \
  --write-provenance
```

## 风险和边界

- 不能把修补后的 splat 当作真实几何。它只服务视觉层。
- 自动删除必须有回滚；过度清理会把窗帘、椅腿、灯具、小物体边缘删掉。
- 平面洞 copy-fill 只适合近似平面，不适合复杂物体。
- 生成式 3DGS inpainting 可以作为 P2/P3，但短期不应替代保守的 patch repair。
- QA 必须基于多视角，而不是只看一个漂亮截图。

## 结论

这个方向值得做。它比“调一个大模型直接修 3DGS”更可控，也比纯统计 cleaner 更接近真实使用体验。

推荐路线：

```text
P0: rule-based prune + background plane protection + QA report
P1: plane hole copy-fill + inserted_gaussians provenance
P2: train Gaussian keep/delete classifier from manual SuperSplat edits
P3: 接入 Gaussian Grouping / SAGA / Inpaint360GS 类模型做更强的局部编辑
```

一句话：**把 SuperSplat 的人工修图经验变成一个有 mask、有 Gaussian id、有 provenance、有 QA、有回滚的自动编辑循环。**

## 参考资料

- [TIDI-GS: Floater Suppression in 3D Gaussian Splatting for Enhanced Indoor Scene Fidelity](https://arxiv.org/abs/2601.09291)
- [Clean-GS: Semantic Mask-Guided Pruning for 3D Gaussian Splatting](https://arxiv.org/abs/2601.00913)
- [PUP 3D-GS: Principled Uncertainty Pruning for 3D Gaussian Splatting](https://arxiv.org/abs/2406.10219)
- [LightGaussian: Unbounded 3D Gaussian Compression with 15x Reduction and 200+ FPS](https://arxiv.org/abs/2311.17245)
- [2D Gaussian Splatting for Geometrically Accurate Radiance Fields](https://arxiv.org/abs/2403.17888)
- [SuGaR: Surface-Aligned Gaussian Splatting for Efficient 3D Mesh Reconstruction](https://arxiv.org/abs/2311.12775)
- [Gaussian Opacity Fields](https://arxiv.org/abs/2404.10772)
- [GS2Mesh: Surface Reconstruction from Gaussian Splatting via Novel Stereo Views](https://arxiv.org/abs/2404.01810)
- [Gaussian Grouping: Segment and Edit Anything in 3D Scenes](https://arxiv.org/abs/2312.00732)
- [Segment Any 3D Gaussians](https://arxiv.org/abs/2312.00860)
- [LangSplat: 3D Language Gaussian Splatting](https://arxiv.org/abs/2312.16084)
- [GaussianEditor: Editing 3D Gaussians Delicately with Text Instructions](https://arxiv.org/abs/2311.16037)
- [Inpaint360GS: Efficient Object-Aware 3D Inpainting via Gaussian Splatting](https://arxiv.org/abs/2511.06457)
- [SplatFill: 3D Scene Inpainting via Depth-Guided Gaussian Splatting](https://arxiv.org/html/2509.07809v1)
- [PointCleanNet: Learning to Denoise and Remove Outliers from Dense Point Clouds](https://arxiv.org/abs/1901.01060)
- [Score-Based Point Cloud Denoising](https://arxiv.org/abs/2107.10981)
- [PU-Net: Point Cloud Upsampling Network](https://arxiv.org/abs/1801.06761)
- [SuperSplat official product page](https://playcanvas.com/products/supersplat)
- [SuperSplat Editor documentation](https://developer.playcanvas.com/user-manual/supersplat/editor/)
