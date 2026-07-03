---
title: 周报：场景扫描路线调研与 Video2Mesh Mesh 重建实验
category: 旧文档
visibility: private
summary: 汇报本周围绕场景扫描学术/工业方案、3DGS-to-mesh 重建路线、语义投影融合和视觉/碰撞代理 Demo 的工作进展。
tags:
  - Weekly Report
  - 3DGS
  - Mesh
  - Collider
  - SimAnything
---

# 周报：场景扫描路线调研与 Video2Mesh Mesh 重建实验

汇报周期：截至 2026-07-03

## 一、本周总体进展

本周主要围绕“扫描场景如何进入可交互仿真/游戏环境”做了两条线的工作：一是调研学术界和工业界的场景扫描、3DGS、Mesh 和交互资产方案；二是在 Video2Mesh 项目中实际测试多种 mesh 重建路线，并基于“视觉代理、碰撞代理、物体语义分层”的思路实现了一个初步 Web demo。

目前比较明确的判断是：项目不应追求从视频直接生成一个完美的统一 mesh，而应产出分层资产包，即 3DGS 负责高质量视觉层，mesh/collider 负责碰撞和交互，语义和物理属性通过 sidecar 或 scene graph 单独管理。这个判断和学长文档、World Labs / Icare、image-blaster 等工业实践中的“visual layer + collision layer + interaction metadata”思路基本一致。

## 二、场景扫描方案调研

本周重点调研和梳理了以下几类方案：

- 学术路线：COLMAP / MVS、3DGS、SuGaR、GS2Mesh、2DGS/GOF、TSDF/Poisson 等从图像或 3DGS 到 mesh 的方法。结论是，传统 COLMAP dense + Delaunay/Poisson 更适合作为场景级静态碰撞代理；GS2Mesh 和 SuGaR 更适合做高质量 visual mesh 的对照或后续升级，而不适合作为 P0 主链路直接替代 collider。
- 工业路线：学长文档、World Labs / Icare、image-blaster 等方案都倾向于把 3DGS/Spark/Splat 作为视觉代理，把 GLB mesh 或简化 collider 作为交互代理。World Labs 更偏 static world/background 生成，image-blaster 更偏 object mesh generation 和浏览器查看约定，最终 simulator asset bundle、物理属性和引擎适配仍需要 Video2Mesh 自己承接。
- 项目边界：Video2Mesh 的合理目标是从扫描视频生成可复用的多层资产，包括 3DGS visual scene、scene collider、object visual mesh、object collider、语义 face/object sidecar、physics metadata 和 Unity/MuJoCo/Isaac/Web adapter。

这一轮调研后，本周把后续方向收敛为三层：场景级 static collider 先稳定，物体级 visual mesh 再细化，最后再接入物体交互、补全和动态仿真。

## 三、Mesh 重建实验进展

本周在 bedroom 场景上实际尝试了 Open3D、COLMAP、CloudCompare/3D Recon/Poisson、SuGaR、GS2Mesh 等路线，主要结果如下。

### 1. GS2Mesh 路线

GS2Mesh 能从训练后的 3DGS 出发，通过渲染多视角/双目深度再做 TSDF 融合，整体思路比直接拿 Gaussian center 连面更合理。实测结果中，raw mesh 规模较大，约 4.48M vertices / 8.09M triangles，原始文件约 333MB；减面后可以得到约 10 万级别面数、几 MB 级别的 GLB。视觉上床、窗帘和大结构能被保留下来，但仍有墙面破碎、漂浮片和局部缺失，适合作为 P1/P2 object visual mesh 或 benchmark，不适合直接作为轻量 collider。

![图一：GS2Mesh 输出效果](assets/weekly-2026-07-03/01-gs2mesh.png)

### 2. Open3D Poisson / 3DGS 点云路线

Open3D Poisson 使用过滤后的 3DGS center point cloud 作为输入，本次 `alpha005_sample500k` 路线输入 50 万点，输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。优点是自动化程度高、输出体量可控；缺点是几何上容易出现透明壳状伪影、表面粘连、漂浮物和错面，说明 3DGS 的 Gaussian center 并不等价于真实表面采样。这个路线可以作为快速 baseline 或 fallback，但不是最终 visual mesh 的理想方案。

![图二：Open3D Poisson 3DGS alpha005 sample500k](assets/weekly-2026-07-03/02-open3d-poisson-3dgs-alpha005-sample500k.png)

### 3. COLMAP Delaunay Dense 路线

COLMAP dense + Delaunay mesher 的输出更加符合 static collider 的需求。本次输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB，体量接近 Web/Unity 里可用的碰撞代理。它的视觉细节不如 3DGS 和 GS2Mesh，局部也有大三角面和缺口，但作为地面、墙体、床体周围的 static collision mesh 更稳。这也是当前最适合作为 P0 场景级碰撞代理的路线。

![图三：COLMAP Delaunay dense mesh](assets/weekly-2026-07-03/03-colmap-delaunay-dense.png)

### 4. CloudCompare / 3D Recon / Poisson 与 SuGaR

CloudCompare + Poisson/3D Recon 主要用于人工检查和传统建面对照。它能较快形成可查看 mesh，但对 3DGS 点云和稠密点云都比较依赖法线质量，容易补出不真实的大薄片，因此更适合做 debug 或 collider fallback。SuGaR 方向也做了依赖和可行性验证，但当前 Video2Mesh 环境中的 Python/Torch/PyTorch3D 兼容性还没有完全打通，尚未形成稳定结果。后续如果继续做 SuGaR，建议单独建立环境，把它作为高质量对照实验，而不是塞进主流程。

## 四、语义投影融合尝试

本周还尝试了把语义信息回灌到 mesh face 上的方法。P0 最近邻/KDTree 方案速度快，可以生成 face-level semantic sidecar；P1 多视角投影方案尝试把 mesh face 投回相机视角后根据语义 mask 投票。当前图五对应的是 `p1_ray_projected_debug` 的调试结果。

这条路线目前效果不理想，主要问题是：当前 run 缺少真正的 SAM/GDINO 2D mask，只能用 semantic point label 投影出的 debug mask 代替；多视角投票虽然覆盖面更高，但标签串色明显，床、墙、窗帘、地面之间容易互相污染，平均置信度也偏低。因此目前可以保留为实验工具，但暂时不能作为生产级语义融合结果。后续需要接入真实 2D mask、深度可见性过滤、face graph smoothing 和 object support 约束。

![图五：mesh 语义投影融合调试结果](assets/weekly-2026-07-03/05-mesh-semantic-transfer-ray-projection.png)

## 五、视觉代理 + 碰撞代理 Demo

基于前面的调研和实验，本周实现了一个初步 Web demo：`http://127.0.0.1:4173/demos/visual-physics-proxy/`。（还没找到服务器）

这个 demo 的核心不是最终画质，而是验证分层架构：GraphDECO/3DGS 只负责视觉显示，COLMAP Delaunay GLB 作为隐藏但有效的 collider mesh，射线检测、地面探测和角色移动都只依赖 mesh，不依赖 3DGS 点云本身。这个 demo 对应后续进入 Unity/Web/MuJoCo 时需要的资产拆分方式，也能直观展示“视觉真实”和“物理可交互”为什么应该分开做。

![图四：视觉代理 3DGS + 碰撞代理 mesh Demo](assets/weekly-2026-07-03/04-visual-physics-proxy-demo.png)

## 六、本周形成的主要判断

1. 场景级可交互闭环应优先走 `COLMAP dense/Delaunay -> simplified collider GLB -> Web/Unity raycast/physics`，不要把 3DGS 本身当 collider。
2. 物体级 mesh 应优先研究 per-object 重建，而不是整场景一次性重建。整场景 mesh 更适合做静态碰撞，物体 mesh 更适合做视觉补全、抓取、移动和语义交互。
3. 直接从 3DGS center point cloud 做 Poisson 容易出壳状伪影，后续更应依赖 3DGS rendered RGB/depth/mask、TSDF fusion、GS2Mesh-style stereo depth 或 SuGaR/2DGS 这类 surface-aware 方法。
4. 语义不应硬烘进 mesh 顶点色，而应保存为 face/object sidecar。这样 collider 后续可以减面、替换或拆分，语义合同仍然可查询。
5. image-blaster、Hunyuan3D、Meshy、TRELLIS 等生成式方法更适合 object completion；背景 clean plate、物体 visual completion 和 physics proxy completion 要分开处理。

## 七、Sim Anything / PhysSplat 方向

本周还关注到 Sim Anything / PhysSplat 这条方向。它和我们当前“视觉代理 + 碰撞代理 + 语义/物理 sidecar”的分层思路不同：PhysSplat 更倾向于把物理属性估计、粒子采样和动态仿真信息注入到 3DGS/semantic Gaussian 体系里，让静态 3D scene 获得动态形变和交互效果。

这条线对我们后续做物体交互有启发，尤其是对枕头、被子、布料、植物等非刚体对象，可以作为 P2 动态 Gaussian 或物理属性估计方向继续探索。不过它不能直接替代我们当前的 mesh/collider 主链路。当前能看到 PhysSplat 官方 GitHub 入口和 README，但完整模型/权重、数据和工程复现质量仍需要进一步确认。因此短期仍建议把它作为研究旁线，先不影响 P0/P1 的 mesh 和 collider 闭环。

参考：

- PhysSplat / Sim Anything official repository: <https://github.com/Maxwell-Zhao/PhysSplat>
- PhysSplat paper: <https://arxiv.org/pdf/2411.12789>

## 八、下一步计划

下周建议重点推进三件事：

1. Per-object mesh 重建：从当前整场景重建转向物体级重建，利用 object mask、3DGS rendered depth/mask 和 TSDF fusion，对床、桌子、椅子等对象分别生成 visual mesh，并和 GS2Mesh / SuGaR 结果做对照。
2. 残缺物体补全：把遮挡补全拆成 object visual completion、background clean plate 和 physics proxy completion。短期可先用 image-blaster/Hunyuan3D/Meshy/TRELLIS 生成 object-local mesh，再用 observed 3D bbox、support plane 和语义信息 fit 回原场景。
3. 物体交互闭环：在 Web demo 的基础上，把 collider 从单一 scene mesh 拆成 object-level collider / primitive proxy，并把 face/object semantics、物理材质、可移动性、可点击 affordance 接入到交互逻辑中。

如果时间允许，可以继续做 Sim Anything / PhysSplat 的复现性检查，重点看它是否能为 Video2Mesh 提供物体物理属性估计或动态 Gaussian 展示，而不是替代已有的 mesh/collider 管线。
