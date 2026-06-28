# 场景扫描学术与工业方案调研：对 Video2Mesh 流水线的改进建议

调研日期：2026-06-28  
面向项目：Video2Mesh 当前流水线

## 0. 结论先行

Video2Mesh 现在的路线是正确的：视频抽帧、COLMAP 位姿、3DGS 重建、GroundingDINO + SAM2 分割、2D mask 投回 3D、再切物体 mesh 和仿真资产。这条链路和近两年学术界/工业界的主流方向一致，不是“换一个大模型”就能解决，而是要把每个阶段的质量控制、跨视角一致性和资产化细节补强。

最值得优先做的提升有五类：

1. **采集和抽帧 QA 前置**：工业产品做得好的地方不是算法更神秘，而是采集时就告诉用户哪里缺覆盖、哪里模糊、哪里视差不足。Video2Mesh 应增加 blur/overlap/parallax/registered-pose 预检和 smart keyframing。
2. **COLMAP 失败时用学习式几何兜底**：COLMAP 对低纹理、少视差、运动模糊、动态物体敏感。可以把 DUSt3R/MASt3R/MegaSaM 类方法作为 pose/depth fallback 或候选时间窗评分器，而不是完全替代 COLMAP。
3. **2D mask 到 3D 不只投票，要做一致性优化**：当前 vote/probability fusion 是基础版。可以参考 SAM3D、SA3D、Gaussian Grouping、SAGA、GaussianCut，把 2D mask 投影、跨帧关联、3D 图优化/连通性/边界细化合起来。
4. **物体 mesh 不应从稀疏点云直接三角化**：工业可用 mesh 更接近 “多视角 RGB/depth/normal/mask 融合 -> TSDF/Poisson/marching cubes -> texture bake -> collider 简化”。GS2Mesh、SuGaR、2DGS 等方法都说明，3DGS 很适合渲染，但直接从原始 Gaussian 属性取表面会噪。
5. **资产输出要从 debug 几何升级为产品化包**：Matterport、Apple RoomPlan、RealityScan 的共同点是输出结构明确：点云/mesh/材质/平面/房间结构/测量/标准格式。Video2Mesh 应把 `metadata.json`、object visibility、mesh quality、collider、mass/friction 估计和 Unity/Isaac/MuJoCo adapter 做成稳定契约。

## 1. 当前 Video2Mesh 对标位置

当前流水线可以拆成这些能力：

| Video2Mesh 阶段 | 现有方案 | 外部对标 | 主要短板 |
|---|---|---|---|
| 视频采集/抽帧 | ffmpeg/OpenCV 均匀抽帧 | Polycam smart keyframing、RealityScan quality heatmap、Matterport scan guidance | 没有前置质量评分和用户反馈 |
| 位姿/稀疏点云 | COLMAP SfM | COLMAP、DUSt3R、MASt3R、MegaSaM、RGB-D SLAM | 低纹理/少视差/动态视频会断 |
| 场景表示 | GraphDECO 3DGS | 3DGS、2DGS、SuGaR、Gaussian Surfels | 外观好，几何表面不一定稳 |
| 2D 检测/分割 | GroundingDINO + SAM2 | Grounded-SAM2、SAM3D、SA3D、OpenMask3D | 依赖 prompt 和单视角 mask 质量 |
| 2D->3D 融合 | mask 投影 + vote/probability | Gaussian Grouping、SAGA、GaussianCut、FlashSplat | 缺少 3D 正则、边界细化、实例关联 |
| 背景结构 | RANSAC plane fitting | RoomPlan、SpatialLM、Matterport floor/BIM | 只能拟合平面，缺少结构化 layout |
| 单物体 mesh | Open3D alpha/ball/convex/bbox 等 | GS2Mesh、SuGaR、2DGS、TSDF fusion | debug 可用，仿真/展示质量不足 |
| 仿真资产 | 自定义导出 | MatterPak、USD/USDZ、E57、RealityScan mesh/texture | 标准化、质量指标和 collider 还可增强 |

## 2. 学术界怎么做

### 2.1 位姿与重建：从经典 SfM 到学习式几何兜底

**COLMAP** 仍是可靠基线。官方文档将其定位为通用 SfM + MVS 工具，支持有序/无序图像集合，并提供自动重建入口；GraphDECO 3DGS 也默认依赖 COLMAP sparse points 初始化。对 Video2Mesh 来说，COLMAP 的优势是成熟、可复现、输出标准，短板是对扫描视频质量很挑剔。

可借鉴做法：

- 保留 COLMAP 作为默认生产路径。
- 在抽帧后立即输出 COLMAP readiness 之前的 **预估质量报告**：blur score、feature count、frame overlap、baseline/parallax、动态区域比例。
- 把失败原因具体化：不是只说 “pose 少”，而是说“低纹理、强反光、视差不足、运动模糊、时间窗太短、过多动态前景”。

代表资料：

- [COLMAP documentation](https://colmap.github.io/)
- [Structure-from-Motion Revisited](https://demuc.de/papers/schoenberger2016sfm.pdf)
- [COLMAP GitHub](https://github.com/colmap/colmap)

**DUSt3R / MASt3R / MASt3R-SLAM** 的价值在于：它们把相机位姿、匹配、深度估计的一部分问题转成学习式 pointmap / dense matching。DUSt3R 可以在未知内外参的图像集合上做 dense reconstruction；MASt3R 强化了跨视角匹配；MASt3R-SLAM 把这种 3D prior 做成实时 monocular dense SLAM。它们不一定替代 COLMAP，但很适合做：

- COLMAP 失败时间窗的候选兜底。
- 抽帧前的 scan quality scorer。
- 对低纹理、宽基线、弱校准视频提供粗 pose/depth。
- 给 3DGS 或 TSDF object mesh 提供额外 depth prior。

代表资料：

- [DUSt3R: Geometric 3D Vision Made Easy](https://arxiv.org/abs/2312.14132)
- [MASt3R: Grounding Image Matching in 3D](https://arxiv.org/abs/2406.09756)
- [MASt3R-SLAM](https://arxiv.org/abs/2412.12392)
- [MegaSaM](https://arxiv.org/abs/2412.04463)

**RGB-D/SLAM 系路线** 更偏工业可靠性。BundleFusion、NICE-SLAM、Open3D TSDF 都说明：一旦有深度，mesh 会稳定很多。Video2Mesh 当前是 RGB 视频，如果未来支持 iPhone LiDAR/ARKit/Depth Anything/MegaSaM depth，可以加一个 optional depth path：

```text
RGB video + optional depth/estimated depth + camera poses
  -> masked depth rendering/fusion
  -> TSDF volume per object
  -> marching cubes / Poisson
  -> texture bake + collider simplification
```

代表资料：

- [BundleFusion](https://graphics.stanford.edu/projects/bundlefusion/)
- [NICE-SLAM](https://pengsongyou.github.io/nice-slam)
- [Open3D RGB-D integration / Scalable TSDF](https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html)
- [BundleSDF](https://bundlesdf.github.io/)

### 2.2 3DGS：外观强，几何要另补

GraphDECO 3DGS 的核心优势是：从 SfM sparse points 初始化，把场景表示成可优化的 3D Gaussians，用实时 splatting 渲染获得高质量新视角。原始论文强调 sparse points 初始化、各向异性 Gaussian、density control 和 visibility-aware splatting，这与 Video2Mesh 当前 GraphDECO 路径一致。

代表资料：

- [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079)
- [GraphDECO official repo](https://github.com/graphdeco-inria/gaussian-splatting)

但论文和工业实践都显示：3DGS 的视觉质量不等于 mesh 几何质量。Gaussians 是为 photometric rendering 优化的，表面可能漂浮、膨胀、半透明、断裂。因此外部方案通常会做几何增强：

- **2DGS**：把 3D 体 Gaussian 变成 2D oriented disks，用 depth distortion 和 normal consistency 改善表面几何。
- **SuGaR**：加入 surface-aligned regularization，再用 Poisson 提取 mesh，适合从 3DGS 取可编辑 mesh。
- **Gaussian Surfels**：用 surfel-like 表示强化 surface alignment。
- **GS2Mesh**：不直接读 Gaussian 表面，而是渲染 stereo novel views，用预训练 stereo model 估深，再多视角融合 mesh。

对 Video2Mesh 的启发：

- 保留 3DGS 作为可视化和 mask carrier。
- 物体 mesh 走 “3DGS render RGB/depth/normal/mask -> TSDF/Poisson”。
- 给 mesh 阶段增加 view selection：优先用物体 mask 面积大、视角互补、重投影一致、低模糊的帧。
- 增加几何正则选项：2DGS/SuGaR/GS2Mesh-style 后处理，而不是只对 sparse object cloud 做 alpha shape。

代表资料：

- [2D Gaussian Splatting](https://arxiv.org/abs/2403.17888)
- [SuGaR](https://arxiv.org/abs/2311.12775)
- [GS2Mesh](https://arxiv.org/abs/2404.01810)
- [Gaussian Surfels](https://arxiv.org/abs/2404.17774)

### 2.3 开集检测与视频分割：GroundingDINO + SAM2 是合理组合

GroundingDINO 的强项是 open-set / language-guided detection，可以用类别名或 referring expression 找 bbox。SAM2 的强项是 promptable image/video segmentation，使用 streaming memory 做视频目标传播。当前 Video2Mesh 用 GroundingDINO 找框、SAM2 跨帧传播 mask，是业界和开源 demo 里常见组合。

代表资料：

- [GroundingDINO](https://arxiv.org/abs/2303.05499)
- [GroundingDINO GitHub](https://github.com/IDEA-Research/GroundingDINO)
- [SAM2](https://arxiv.org/abs/2408.00714)
- [SAM2 GitHub](https://github.com/facebookresearch/sam2)
- [Grounded-SAM2](https://github.com/IDEA-Research/grounded-sam-2)

可以提升的点：

- prompt 不能只用单个 label。应维护 prompt set：`chair`, `wooden chair`, `dining chair`, `seat`, 中文/英文别名，合并候选框。
- 对每个 object track 做 mask health check：面积突变、bbox 跳变、mask 断裂、出画、遮挡、和 3D 投影不一致。
- 对 anchor frame 自动重选：如果第一帧 prompt 很弱，选择可见面积最大/锐度最高/视角最正的帧重新 prompt SAM2。
- 用 3D projection 反向纠错：3D object mask 投回视频后，发现某帧 IoU 太低时重新跑 SAM2/局部 SAM。

### 2.4 2D mask 到 3D：从投票融合升级为优化问题

Video2Mesh 当前的 2D->3D fusion 已经有正确骨架：相机投影 + 2D mask + 点/高斯概率累积。但学术界更进一步，会引入跨视角一致性、3D 连通性、语义特征和图优化。

**SAM3D** 的思路是：对有 pose 的 RGB 图像跑 SAM，投到点云，再通过相邻帧双向 merging 逐步合成 3D mask。这和 Video2Mesh 的点云投票非常接近，但更强调 mask 合并顺序、双向一致和 over-segmentation 辅助。

**SA3D** 的思路是：在 radiance field 中从一个视角 prompt 开始，通过密度引导 inverse rendering 得到 3D mask，再渲染到其他视角作为 self-prompt，形成跨视角闭环。

**Gaussian Grouping / SAGA / GaussianCut** 直接把 segmentation 能力注入 3DGS：

- Gaussian Grouping：给每个 Gaussian 加 identity encoding，用 SAM 2D masks 监督，并加 3D spatial consistency。
- SAGA：给每个 Gaussian 学 affinity feature，支持 2D prompt 后毫秒级 3D Gaussian segmentation。
- GaussianCut：把 Gaussians 建图，用 graph cut 结合用户输入、2D/video segmentation 和 scene properties 做前景/背景划分，不必重新训练。
- FlashSplat / Unified-Lift / Lifting by Gaussians：强调把 2D mask 到 Gaussian label 的 lifting 做得更快、更全局一致。

对 Video2Mesh 的落地路线：

1. 短期：在已有 probability fusion 后加 3D 连通域、半径图平滑、平面/背景排除、visibility-weighted vote。
2. 中期：把 Gaussians 建 kNN graph，对每个 object 做 GaussianCut-style graph refinement。
3. 长期：训练/优化 semantic Gaussian attributes，让 object id / semantic id 成为 Gaussian 的一等属性，而不是只在导出 PLY 时附加。

代表资料：

- [SAM3D](https://arxiv.org/abs/2306.03908)
- [SA3D: Segment Anything in 3D with NeRFs](https://proceedings.neurips.cc/paper_files/paper/2023/hash/525d24400247f884c3419b0b7b1c4829-Abstract-Conference.html)
- [Gaussian Grouping](https://arxiv.org/abs/2312.00732)
- [SAGA: Segment Any 3D Gaussians](https://arxiv.org/abs/2312.00860)
- [GaussianCut](https://arxiv.org/abs/2411.07555)
- [FlashSplat](https://arxiv.org/abs/2409.08270)

### 2.5 开词表 3D 语义与场景图：别只切物体，要形成结构化场景

Video2Mesh 现在偏 “找到物体 -> 切物体 -> 导出资产”。如果想进一步提升场景理解和仿真可用性，需要把物体、平面、房间结构和关系组织起来。

可参考方案：

- **OpenMask3D**：先有 class-agnostic 3D instance masks，再用多视角 CLIP image features 给每个 3D mask 聚合开放词表语义。
- **ConceptGraphs**：从 posed RGB-D 序列中做 2D instance segmentation，投影到 3D 点云，跨视角关联融合，形成 object-level 3D scene graph。
- **LangSplat / Feature 3DGS / Semantic Gaussians / OpenGaussian**：把 2D foundation model 的语义特征蒸馏到 3DGS，让自然语言查询、语义分割和编辑在 3D 表示里完成。
- **SpatialLM**：把点云转成结构化室内建模输出，包括墙、门、窗和 oriented object boxes。
- **SceneVerse++**：把未标注互联网视频提升为 instance-level point clouds、object layouts、spatial VQA、导航等监督，说明 “自动数据引擎 + 多模块互补 + 质量筛选” 是未来方向。

对 Video2Mesh 的启发：

- 在 `metadata.json` 中把 object mask、semantic label、3D bbox、support plane、room/layout relation、source frames、confidence 统一记录。
- 每个 object 生成视觉语言 caption 和 affordance：例如 `chair: sit-able, supported_by=floor, near=desk`。
- 用 SpatialLM/规则几何为仿真提供结构先验：墙/地/天花板/门窗/柜体等不一定都要生成可动物体 mesh。
- 对同一物体的多个文本标签做 CLIP/LLM 合并，减少 “chair/seat/stool” 重复实例。

代表资料：

- [OpenMask3D](https://arxiv.org/abs/2306.13631)
- [ConceptGraphs](https://concept-graphs.github.io/)
- [LangSplat](https://arxiv.org/abs/2312.16084)
- [Feature 3DGS](https://arxiv.org/abs/2312.03203)
- [Semantic Gaussians](https://semantic-gaussians.github.io/)
- [OpenGaussian](https://proceedings.neurips.cc/paper_files/paper/2024/file/21f7b745f73ce0d1f9bcea7f40b1388e-Paper-Conference.pdf)
- [SpatialLM](https://arxiv.org/abs/2506.07491)
- [SceneVerse++](https://sv-pp.github.io/)

## 3. 工业界怎么做

### 3.1 Matterport：硬件 + 云端重建 + 标准资产包

Matterport 的强项是产品闭环：采集设备、空间对齐、云端处理、数字孪生 viewer、测量、BIM/CAD 导出。Pro3 使用 LiDAR，官方资料强调室内外、较大空间、较高测量精度、E57/MatterPak/BIM 工作流。Cortex AI 则把计算机视觉、图像处理和深度学习用于自动生成空间数据和属性。

可借鉴点：

- 扫描引导比后处理更重要：明确告诉用户扫描间距、楼层、窗户、移动物体等风险。
- 输出不是单一 mesh：MatterPak/E57 这样的包包含点云、图像、metadata，可进入第三方 CAD/BIM。
- 把质量和用途绑定：营销展示、测量、BIM、设施管理对应不同精度和输出格式。

对 Video2Mesh 的建议：

- 增加 `scan_readiness_report.md/json`：记录有效帧、模糊帧、注册帧、点云密度、遮挡/动态风险。
- 增加 `asset_bundle_manifest.json`：统一列出 scene splat、semantic splat、object mesh、collider、Unity/Isaac/MuJoCo adapter。
- 输出 E57/PLY/GLB/USDZ 的兼容层，至少在 manifest 里明确每个资产的坐标系、单位、up axis。

代表资料：

- [Matterport Cortex AI](https://matterport.com/cortex-ai)
- [Matterport Pro3 overview](https://support.matterport.com/s/article/Overview-of-Pro3?language=en_US)
- [MatterPak bundle](https://support.matterport.com/s/article/Download-the-MatterPak-Bundle?language=en_US)
- [Matterport E57 file](https://support.matterport.com/s/article/Overview-of-Matterport-E57-File?language=en_US)

### 3.2 Apple RoomPlan / Object Capture：参数化结构和拍摄规范

RoomPlan 不是通用 photorealistic 3DGS，而是面向室内结构化扫描：用 ARKit + camera + LiDAR 生成房间 floor plan，输出 USD/USDZ，包含墙、柜体、家具类别、尺寸和位置。Object Capture 则强调用多张照片生成物体 3D 模型，并给出拍摄对象选择和图像采集最佳实践。

可借鉴点：

- 房间结构用参数化表达，不一定用高密 mesh 表达。
- 家具、墙、门窗、柜体等对象要有 dimensions 和 semantic type。
- 采集阶段有 coaching UI，而不是等重建失败后才告诉用户。

对 Video2Mesh 的建议：

- 背景结构输出分两层：`layout.json` 记录墙/地/天花板/门窗/柜体参数，`scene.splat` 负责视觉展示。
- 对室内仿真，优先让背景平面 watertight 和尺度正确，外观细节留给 3DGS。
- 增加 ARKit/LiDAR 输入适配：如果用户有 iPhone LiDAR，直接把 depth/pose 作为可选增强信号。

代表资料：

- [Apple RoomPlan](https://developer.apple.com/augmented-reality/roomplan/)
- [Apple Object Capture WWDC](https://developer.apple.com/videos/play/wwdc2021/10076/)
- [Capturing photographs for RealityKit Object Capture](https://developer.apple.com/documentation/realitykit/capturing-photographs-for-realitykit-object-capture)

### 3.3 Polycam：Photogrammetry 和 Gaussian Splat 分用途

Polycam 明确区分两类输出：photogrammetry mesh 适合 3D printing、engineering、architecture、insurance documentation；Gaussian Splats 适合 photorealistic visualization、复杂材质、透明/反光对象和艺术展示。它也提供了上传图片/视频生成 photogrammetry 或 Gaussian splat 的流程，并强调 60-80% overlap、足够覆盖、steady footage、smart keyframing、过滤模糊或冗余帧。

可借鉴点：

- 不同目标采用不同表示：mesh 用于工程/仿真，splat 用于展示。
- smart keyframing 是视频输入的关键产品功能。
- 采集引导包括多高度环绕、均匀漫射光、避免动态主体、避免纯白低纹理表面。

对 Video2Mesh 的建议：

- 把抽帧从 “均匀抽帧” 升级为 “均匀覆盖 + blur filter + baseline diversity + object visibility”。
- 保留 `MAX_FRAMES=200`，但从候选帧中选择更适合 COLMAP/3DGS/SAM2 的帧。
- 给用户输出 capture tips：如果检测到低纹理/强反光/运动模糊，建议重拍方式。

代表资料：

- [Polycam Object Mode](https://learn.poly.cam/hc/en-us/articles/27425185907348-How-to-Use-Object-Mode)
- [Polycam upload images/videos](https://learn.poly.cam/hc/en-us/articles/30549121659412-How-to-Create-Photogrammetry-and-Gaussian-splats-from-Existing-Images-and-Videos)
- [Polycam Gaussian Splatting tool](https://poly.cam/tools/gaussian-splatting)

### 3.4 Scaniverse / Niantic：移动端 3DGS、mesh、SPZ 压缩和大规模空间数据

Scaniverse/Niantic Spatial 的亮点是把高保真扫描、Gaussian Splats、mesh 和开放格式 SPZ 做成移动端/企业级数据入口。官方企业页强调 iOS/Android、360 相机、无人机、多传感器输入，输出标准 3D 格式和开源 SPZ，SPZ 可减少文件体积。

可借鉴点：

- 3DGS 需要压缩和标准交换格式，不然很难进入产品链路。
- 移动端 capture 的价值在于“快速 intake”，后端再做标准化清洗和资产发布。
- mesh 与 splat 并存：mesh 做碰撞/测量/编辑，splat 做真实感查看。

对 Video2Mesh 的建议：

- 加 SPZ 或压缩 PLY 导出适配，至少提供 SuperSplat/PlayCanvas 友好版本。
- asset bundle 同时输出 `scene.splat/spz` 和 `scene_collision.glb`。
- 对每个 object 同时保存 `object_visual.splat` 和 `object_physics.glb`，不要强行让一个表示承担所有任务。

代表资料：

- [Niantic Spatial Capture](https://www.nianticspatial.com/products/capture)
- [Scaniverse](https://dev.scaniverse.com/)
- [Scaniverse Gaussian splatting announcement](https://medium.com/scaniverse/scaniverse-introduces-support-for-3d-gaussian-splatting-9f7f63f5469b)

### 3.5 RealityScan / RealityCapture：AI mask、alignment、quality heatmap

RealityScan 2.0 的新功能很贴近 Video2Mesh 的痛点：AI-assisted masking、alignment 改进、visual quality inspection、aerial LiDAR support。它强调在 meshing 前用 heatmap 找到覆盖不足区域，避免后期返工。

可借鉴点：

- AI mask 不只是为了语义，也可以用于重建前去背景、去动态干扰。
- alignment failure 是产品级重点，需要默认参数和质量检查降低人工干预。
- heatmap/coverage report 是扫描产品最有价值的反馈之一。

对 Video2Mesh 的建议：

- 在 COLMAP 前用 segmentation 去掉人、屏幕、水面、镜面、窗外强动态等干扰区域，至少可作为 feature mask。
- 生成 object/scene coverage heatmap：每个表面/物体有多少视角支持、mask 是否一致。
- 在 `advisor_demo_summary.md` 里加入 “为什么这个 mesh 不能展示/哪里缺视角” 的具体解释。

代表资料：

- [RealityScan 2.0 release](https://www.realityscan.com/news/realityscan-20-new-release-brings-powerful-new-features-to-a-rebranded-realitycapture)

### 3.6 Luma AI：低门槛 scene capture 和在线交互展示

Luma Interactive Scenes 把视频/图片输入转成可交互 3D 场景，重点是小文件、快速流式加载、嵌入网页和商业可用。它对 Video2Mesh 的启发不是算法细节，而是发布体验：产物要能一键预览、一键分享、一眼看懂质量。

可借鉴点：

- viewer 是资产质量评估的一部分，不只是展示。
- 场景要能边加载边查看，资产体积要控制。
- 每个导出资产应有快速可视化入口。

代表资料：

- [Luma Interactive Scenes](https://lumalabs.ai/interactive-scenes)

## 4. 对 Video2Mesh 的具体改进方案

### 4.1 采集/抽帧：加入 smart keyframing 和质量报告

现状：均匀抽帧，真实帧上限 200。  
问题：均匀不等于好；模糊、低视差、重复帧会拖累 COLMAP/3DGS/SAM2。

建议实现：

```text
video
  -> decode candidate frames
  -> compute blur, exposure, feature count, optical flow, scene change
  -> estimate baseline diversity and overlap
  -> remove blurry/redundant frames
  -> keep uniform temporal coverage
  -> write frame_selection_report.json
```

核心指标：

| 指标 | 用途 |
|---|---|
| Laplacian blur / motion blur | 过滤模糊帧 |
| feature count / matchability | 预测 COLMAP 成功率 |
| optical flow magnitude | 保证视差，不选几乎静止帧 |
| frame overlap | 避免跨度太大导致匹配断 |
| dynamic mask ratio | 剔除人/屏幕/运动物体占比高的帧 |
| object visibility | 为每个物体选好 anchor 和 mesh source views |

短期改动位置：

- `extract-frames` 增加 `--selection-method smart_uniform`
- 输出 `scene/frames/frame_quality.json`
- `reconstruction_readiness_report.json` 加入抽帧质量统计

### 4.2 COLMAP 兜底：增加 learned pose/depth fallback

建议分三层，不要一开始重构主链路：

1. **时间窗推荐器**：用 blur/flow/feature/match 评分，帮用户找更适合 COLMAP 的 8-15 秒窗口。
2. **MASt3R/DUSt3R 辅助匹配**：当 SIFT matching 弱时，用学习式匹配补 candidate pairs。
3. **MegaSaM/MASt3R-SLAM fallback**：COLMAP 注册率太低时输出 coarse pose/depth，供下游低质量预览或重拍建议使用。

成功判据：

- registered frame ratio 提升。
- camera coverage 提升。
- 3DGS train 不再因 sparse cloud 太弱直接失败。
- 失败时能明确提示重拍，而不是下游生成一堆坏资产。

### 4.3 分割：从单 prompt 跑通升级为 track QA

建议为每个 object track 记录：

```json
{
  "object_id": "chair_01",
  "prompts": ["chair", "wooden chair", "seat"],
  "anchor_frame": "000084.png",
  "track_health": {
    "mean_mask_area": 0.071,
    "area_jump_frames": [],
    "lost_frames": ["000121.png"],
    "projection_iou_mean": 0.64,
    "needs_reprompt": false
  }
}
```

改进策略：

- 多 prompt 合并候选 bbox。
- 从最高可见面积帧重新初始化 SAM2。
- 传播后做 temporal smoothing。
- 用 3D 重投影检查 bad frames，bad frames 局部重跑 SAM/SAM2。
- 小物体增加 high-res crop segmentation，不只在整图上分。

### 4.4 2D->3D 融合：visibility-weighted probability + graph refinement

当前投票可以升级为：

```text
for each point/gaussian g:
  for each visible camera c:
    project g -> pixel p
    if p inside valid image and depth-consistent:
      add vote weighted by:
        mask probability
        viewing angle
        projected area
        object visibility score
        frame quality score
        depth consistency
```

然后做后处理：

- 3D kNN graph smoothing。
- connected component filtering。
- plane-aware background suppression。
- object bbox prior。
- GaussianCut-style foreground/background graph cut。
- 多 object 冲突解算：同一个 Gaussian 不能高置信属于多个实例，除非是透明/薄结构特殊标记。

输出建议：

```text
masks/3d/<object_id>/
  point_indices.json
  gaussian_indices.json
  probabilities.npz
  fusion_report.json
  projection_debug/
```

### 4.5 Semantic Gaussian：让语义成为 3DGS 属性

短期不用训练新模型，也可以先加字段：

```text
semantic_id
instance_id
semantic_prob
object_prob_topk
visibility_count
source_frame_count
```

中期参考 Gaussian Grouping / SAGA：

- 给每个 Gaussian 增加 compact identity embedding。
- 用 SAM2 masks + 当前 3D fusion 作为 pseudo-label。
- 加 spatial consistency loss。
- 支持 “点一下/输入文本 -> 返回 object Gaussian subset”。

收益：

- 物体编辑/删除/导出更稳定。
- 同一物体跨帧 mask 不再只是后处理标签，而是训练/优化目标的一部分。
- 后续 viewer 可以直接按语义开关显示。

### 4.6 Object mesh：从 debug OBJ 升级为生产路线

推荐生产路线：

```text
trained 3DGS + object 3D mask + selected source/rendered views
  -> render RGB/depth/normal/alpha/mask
  -> filter views by visibility, sharpness, angle diversity
  -> masked TSDF fusion
  -> marching cubes / Poisson
  -> mesh cleanup: connected component, hole fill, remesh, decimate
  -> texture bake from selected RGB views
  -> collider: bbox / convex decomposition / simplified proxy
  -> export GLB/USD/OBJ + metadata
```

关键实现点：

- 不从稀疏点云直接 alpha shape 作为最终 mesh。
- 对每个 object 单独 TSDF volume，避免背景粘连。
- 如果 3DGS depth 不可靠，尝试 GS2Mesh-style stereo depth 或 external monocular/depth model。
- mesh 输出分 visual mesh 和 collision proxy。
- 质量指标写入 `mesh_quality.json`：面数、连通分量、watertightness、bbox 尺寸、source view count、texture coverage。

### 4.7 背景结构：从 RANSAC plane 到 layout

当前 RANSAC plane fitting 可以继续保留，但建议升级为：

```text
point cloud / Gaussian mask
  -> dominant planes: floor, ceiling, walls
  -> Manhattan alignment if indoor
  -> openings: doors/windows if visible
  -> support relation: object supported_by floor/table/shelf
  -> layout.json
```

可以先用规则几何实现：

- floor: lowest large horizontal plane
- ceiling: highest large horizontal plane
- walls: vertical large planes
- object support: object bbox bottom center 到最近水平 plane

后续可接 SpatialLM，把点云转成结构化 room layout 和 oriented object boxes。

### 4.8 仿真资产：输出分层，而不是只导 mesh

建议每个 object 输出：

```text
objects/<object_id>/
  visual.glb
  collision.glb
  object.splat.ply or object.spz
  masks/
  source_frames/
  metadata.json
  mesh_quality.json
```

`metadata.json` 建议字段：

```json
{
  "object_id": "chair_01",
  "category": "chair",
  "aliases": ["seat", "wooden chair"],
  "bbox_world": {
    "center": [0, 0, 0],
    "size": [0.5, 0.5, 0.9],
    "rotation_z": 0.0
  },
  "support": {
    "type": "floor",
    "plane_id": "floor_00"
  },
  "assets": {
    "visual_mesh": "visual.glb",
    "collision_proxy": "collision.glb",
    "splat": "object.spz"
  },
  "physics": {
    "mass_kg_estimate": 5.0,
    "friction_estimate": 0.6,
    "movable": true
  },
  "quality": {
    "source_view_count": 12,
    "mask_confidence": 0.82,
    "mesh_status": "preview"
  }
}
```

## 5. 分阶段路线图

### 5.1 立刻可做：1-2 周

| 优先级 | 改动 | 预期收益 |
|---|---|---|
| P0 | Smart keyframing：blur/filter/redundancy/feature count | COLMAP 和 3DGS 成功率提升 |
| P0 | `frame_quality.json` + `scan_readiness_report` | 失败可解释，方便重拍 |
| P0 | object track health report | 及时发现 SAM2 漂移/丢失 |
| P1 | visibility-weighted mask fusion | 3D mask 少粘连、少噪声 |
| P1 | connected component + plane-aware cleanup | 物体 mask 更干净 |
| P1 | mesh_quality.json | 防止 debug mesh 被当最终资产展示 |

### 5.2 中期增强：2-6 周

| 优先级 | 改动 | 预期收益 |
|---|---|---|
| P1 | MASt3R/DUSt3R 辅助时间窗评分或 fallback | 少视差/弱纹理场景更稳 |
| P1 | GaussianCut-style graph refinement | 3D object mask 边界更稳 |
| P1 | 3DGS render depth/normal/mask -> object TSDF mesh | mesh 从 debug 升级到可展示 |
| P2 | layout.json：墙/地/天花板/支撑关系 | 仿真资产更有结构 |
| P2 | prompt ensemble + CLIP/LLM label merge | open-vocabulary 检测更少漏检/重复 |

### 5.3 长期方向：1-3 个月

| 优先级 | 改动 | 预期收益 |
|---|---|---|
| P2 | Semantic Gaussian identity embedding | 语义成为 3DGS 一等属性 |
| P2 | ConceptGraphs-style object graph | 可做空间问答、任务规划、机器人仿真 |
| P2 | SuGaR/2DGS/GS2Mesh 替代或补充 GraphDECO mesh path | 高质量 mesh 输出 |
| P3 | ARKit/LiDAR optional depth input | iPhone/移动扫描显著更稳 |
| P3 | SPZ/splat compression/export | 展示和分发更轻 |

## 6. 建议增加的评测指标

### 6.1 重建阶段

| 指标 | 说明 |
|---|---|
| registered_frame_ratio | COLMAP 成功注册帧比例 |
| mean_reprojection_error | SfM 几何质量 |
| sparse_point_count / density | sparse cloud 是否足够 |
| camera_coverage | 参与后续阶段的相机覆盖 |
| train PSNR/SSIM/LPIPS | 3DGS 外观质量 |

### 6.2 分割/语义阶段

| 指标 | 说明 |
|---|---|
| mask_area_stability | SAM2 track 是否漂移 |
| projection_iou | 3D mask 投回 2D 与原 mask 的一致性 |
| visibility_count | 物体有多少可靠视角支持 |
| object_conflict_ratio | 同一点/高斯被多个物体高置信占用比例 |
| connected_components | 3D mask 是否碎裂 |

### 6.3 mesh/仿真阶段

| 指标 | 说明 |
|---|---|
| component_count | mesh 是否碎成很多块 |
| watertightness / boundary_edges | 是否适合碰撞/仿真 |
| texture_coverage | 贴图是否完整 |
| collider_volume_ratio | collider 与 visual bbox 是否合理 |
| support_plane_consistency | 物体是否漂浮/穿地 |
| asset_manifest_completeness | Unity/Isaac/MuJoCo 导出是否完整 |

## 7. 推荐的扫描规范

给用户的短版拍摄建议：

1. 每个房间/局部空间拍 8-20 秒，移动慢，不要快速转身。
2. 先做一圈完整大范围，再补高/低视角。
3. 保持 60-80% 画面重叠，避免连续帧几乎一样或跨度过大。
4. 避免强反光、纯白墙面、透明玻璃、水面、强背光。
5. 尽量关掉电视/屏幕，避免人和宠物进入画面。
6. 重要物体至少让它在 8-12 个清晰视角中出现。
7. 如果是要导出单物体 mesh，绕物体补一圈近景，比只扫房间整体更重要。

系统内的自动提示应该对应这些规则，例如：

```text
该视频 COLMAP 风险较高：
- 42% 帧运动模糊偏高
- 关键物体 chair_01 只有 3 个可靠视角
- 低纹理墙面占比高，建议增加斜向视角
- 第 5-8 秒存在快速转身，建议截取 12-22 秒重跑
```

## 8. 推荐下一步实现清单

最值得在当前代码库里先落的功能：

1. `smart_uniform` 抽帧模式：质量评分 + 均匀覆盖。
2. `frame_quality.json`：每帧 blur、feature、flow、selected_reason。
3. `track_health.json`：每个 object 的 SAM2 mask 稳定性、lost frames、needs_reprompt。
4. `fuse-masks` 增加 visibility/depth/frame-quality 权重。
5. `cleanup-3d-mask`：连通域、kNN 平滑、平面背景剔除。
6. `render-object-observations`：从 3DGS 渲染 object RGB/depth/normal/mask。
7. `reconstruct-object-meshes --method tsdf_from_gs`：生产 mesh 路线。
8. `mesh_quality.json` 和 “debug/preview/production” 资产状态。
9. `layout.json`：floor/walls/ceiling/support relations。
10. `asset_bundle_manifest.json`：稳定资产契约。

## 9. 参考资料

### 基础重建与位姿

- COLMAP: <https://colmap.github.io/>
- COLMAP GitHub: <https://github.com/colmap/colmap>
- Structure-from-Motion Revisited: <https://demuc.de/papers/schoenberger2016sfm.pdf>
- DUSt3R: <https://arxiv.org/abs/2312.14132>
- MASt3R: <https://arxiv.org/abs/2406.09756>
- MASt3R-SLAM: <https://arxiv.org/abs/2412.12392>
- MegaSaM: <https://arxiv.org/abs/2412.04463>
- BundleFusion: <https://graphics.stanford.edu/projects/bundlefusion/>
- NICE-SLAM: <https://pengsongyou.github.io/nice-slam>
- Open3D RGB-D integration: <https://www.open3d.org/docs/latest/tutorial/pipelines/rgbd_integration.html>
- BundleSDF: <https://bundlesdf.github.io/>

### 3DGS 与 mesh

- 3D Gaussian Splatting: <https://arxiv.org/abs/2308.04079>
- GraphDECO 3DGS: <https://github.com/graphdeco-inria/gaussian-splatting>
- 2D Gaussian Splatting: <https://arxiv.org/abs/2403.17888>
- SuGaR: <https://arxiv.org/abs/2311.12775>
- GS2Mesh: <https://arxiv.org/abs/2404.01810>
- Gaussian Surfels: <https://arxiv.org/abs/2404.17774>

### 检测、分割与 2D-to-3D lifting

- GroundingDINO: <https://arxiv.org/abs/2303.05499>
- GroundingDINO GitHub: <https://github.com/IDEA-Research/GroundingDINO>
- SAM2: <https://arxiv.org/abs/2408.00714>
- SAM2 GitHub: <https://github.com/facebookresearch/sam2>
- Grounded-SAM2: <https://github.com/IDEA-Research/grounded-sam-2>
- SAM3D: <https://arxiv.org/abs/2306.03908>
- SA3D: <https://proceedings.neurips.cc/paper_files/paper/2023/hash/525d24400247f884c3419b0b7b1c4829-Abstract-Conference.html>
- Gaussian Grouping: <https://arxiv.org/abs/2312.00732>
- SAGA: <https://arxiv.org/abs/2312.00860>
- GaussianCut: <https://arxiv.org/abs/2411.07555>
- FlashSplat: <https://arxiv.org/abs/2409.08270>

### 开词表 3D 语义和场景理解

- OpenMask3D: <https://arxiv.org/abs/2306.13631>
- ConceptGraphs: <https://concept-graphs.github.io/>
- LangSplat: <https://arxiv.org/abs/2312.16084>
- Feature 3DGS: <https://arxiv.org/abs/2312.03203>
- Semantic Gaussians: <https://semantic-gaussians.github.io/>
- OpenGaussian: <https://proceedings.neurips.cc/paper_files/paper/2024/file/21f7b745f73ce0d1f9bcea7f40b1388e-Paper-Conference.pdf>
- SpatialLM: <https://arxiv.org/abs/2506.07491>
- SceneVerse++: <https://sv-pp.github.io/>

### 工业产品和实践

- Matterport Cortex AI: <https://matterport.com/cortex-ai>
- Matterport Pro3 overview: <https://support.matterport.com/s/article/Overview-of-Pro3?language=en_US>
- MatterPak bundle: <https://support.matterport.com/s/article/Download-the-MatterPak-Bundle?language=en_US>
- Matterport E57: <https://support.matterport.com/s/article/Overview-of-Matterport-E57-File?language=en_US>
- Apple RoomPlan: <https://developer.apple.com/augmented-reality/roomplan/>
- Apple Object Capture: <https://developer.apple.com/videos/play/wwdc2021/10076/>
- Apple Object Capture photo guidance: <https://developer.apple.com/documentation/realitykit/capturing-photographs-for-realitykit-object-capture>
- Polycam Object Mode: <https://learn.poly.cam/hc/en-us/articles/27425185907348-How-to-Use-Object-Mode>
- Polycam image/video upload: <https://learn.poly.cam/hc/en-us/articles/30549121659412-How-to-Create-Photogrammetry-and-Gaussian-splats-from-Existing-Images-and-Videos>
- Polycam Gaussian Splatting: <https://poly.cam/tools/gaussian-splatting>
- Niantic Spatial Capture: <https://www.nianticspatial.com/products/capture>
- Scaniverse: <https://dev.scaniverse.com/>
- Scaniverse Gaussian splatting: <https://medium.com/scaniverse/scaniverse-introduces-support-for-3d-gaussian-splatting-9f7f63f5469b>
- RealityScan 2.0: <https://www.realityscan.com/news/realityscan-20-new-release-brings-powerful-new-features-to-a-rebranded-realitycapture>
- Luma Interactive Scenes: <https://lumalabs.ai/interactive-scenes>
