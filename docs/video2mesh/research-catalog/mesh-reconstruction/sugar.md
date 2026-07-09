---
title: SuGaR
id: video2mesh-mesh-reconstruction-sugar
category: 调研目录
visibility: public
summary: SuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。
tags:
  - Mesh 重建
  - Research Catalog
---

# SuGaR

![SuGaR hybrid mesh editing](https://github.com/Anttwo/SuGaR/raw/main/media/blender/blender_edit.png "SuGaR 将 Gaussian 绑定到 mesh surface 后，可在 Blender 等传统工具中通过 mesh 操作编辑/动画化 Gaussian 场景")

## 链接

- Project / Code: https://github.com/Anttwo/SuGaR
- Project page: https://anttwo.github.io/sugar/
- Paper: https://arxiv.org/abs/2311.12775
- Venue: CVPR 2024

## 摘要要点

SuGaR 的目标是从 3D Gaussian Splatting 中快速抽取可编辑 mesh，并把 mesh 与 surface-aligned Gaussians 绑定成 hybrid representation。它先让 Gaussians 更好贴合真实表面，再从贴合后的 Gaussians 采样 surface points 并用 Poisson reconstruction 得到 mesh；后续还可以联合优化 mesh 和 Gaussians，让传统 mesh 编辑、rigging、animation、relighting 可以间接作用到 Gaussian 场景。

这条路线的意义不是“给 P0 碰撞一个更快替代品”，而是把 3DGS 从纯视觉表示推进到可编辑资产表示。它对后续 Unity/Blender/Unreal 工作流更友好，但训练、环境和后处理成本比 Delaunay collider 更高。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| vanilla 3DGS warm-up | 先训练短程 3DGS，让 Gaussians 粗略覆盖场景 |
| SuGaR optimization | 加 surface alignment regularization，使 Gaussians 更贴近 scene surface |
| mesh extraction | 从 aligned Gaussians 采样 surface points，并通过 Poisson 抽 mesh |
| SuGaR refinement | 联合优化 mesh 和 Gaussians，形成 Mesh + Gaussians hybrid 表示 |
| optional textured mesh | 导出传统 textured mesh，便于 Blender/Unity/Unreal 检查和编辑 |

输入：COLMAP 格式数据或已有 3DGS 训练结果。输出：coarse/refined mesh、surface-bound Gaussians、可选 textured mesh。

## bedroom_4 实测观察

这次用 `bedroom_4` 片段跑通后，最有价值的结论是：SuGaR 的 refined PLY / Gaussian 视觉层已经有可用质量，但从它抽出来的 mesh 还不能直接当 Video2Mesh 的 visual mesh 或 collider。局部房间结构、床、窗、墙面和地板在 refined PLY 里都能被看出来，虽然仍有漂浮片、墙面糊成片和窗口高亮拉丝，整体已经明显比纯稀疏点云更像一个可检查的室内场景。

本次关键输出：

| artifact | 本地路径 | 观察 |
|---|---|---|
| refined PLY / 3DGS layer | `/Users/zhangyuxiang/Desktop/worksplace/SuGaR/output/refined_ply/bedroom4_scene_only_sugar_source/sugarfine_3Dgs30000_sdfestim02_sdfnorm02_level03_decim200000_normalconsistency01_gaussperface6.ply` | 约 2,399,946 Gaussians，视觉效果不错，房间主体结构连贯 |
| coarse mesh | `/Users/zhangyuxiang/Desktop/worksplace/SuGaR/output/coarse_mesh/bedroom4_scene_only_sugar_source/sugarmesh_3Dgs30000_sdfestim02_sdfnorm02_level03_decim200000.ply` | Open3D Poisson mesh，约 216,384 vertices / 399,991 faces，但存在明显正反面/可见性问题 |

![SuGaR bedroom_4 refined PLY 正面视角](../assets/sugar-bedroom4-refined-ply-front.png "bedroom_4 refined PLY：床、墙、窗等主体结构已经能稳定辨认，但墙面与窗边仍有糊片和漂浮伪影")

![SuGaR bedroom_4 refined PLY 斜侧视角](../assets/sugar-bedroom4-refined-ply-oblique.png "换到斜侧视角后，refined PLY 的房间外壳仍较完整，说明 Gaussian 视觉层本身有继续优化和作为展示 baseline 的价值")

真正的问题出在 mesh：从一个外侧/特定方向看，mesh 外壳显得还比较完整；但是把视角切到室内方向后，大片表面会碎裂、消失或只剩零散三角片。这不是单纯“几何不够细”的问题，更像 mesh triangle winding / normal 朝向 / 单面材质可见性出了问题：如果查看器启用了 backface culling，朝向反了的室内墙面、床面和窗边面片会被剔掉，于是图三里看起来像正反弄反了，室内视角变得很碎甚至不显示。

![SuGaR bedroom_4 mesh 正反面问题](../assets/sugar-bedroom4-mesh-backface-issue.png "bedroom_4 mesh：从室内视角看大量面片被剔除或碎裂，疑似 winding/normal 朝向与 one-sided rendering 组合导致的正反面问题")

这会直接影响接入判断：当前 refined PLY 可以作为 `bedroom_4` 的 visual baseline 继续保留，但 mesh 必须先做双面渲染检查、normal/winding 翻转测试、法线重计算和破碎面清理，才能进入 Video2Mesh 的 simulator asset bundle。更严格地说，在修复前它不适合承担 collider、ground probe、camera collision 或室内第一人称浏览，因为这些 runtime 依赖稳定、双侧可解释且拓扑不太破碎的表面。

## 在 Video2Mesh 中的位置

适合作为 P2 高质量 visual mesh 路线。它可以帮助回答“如果我们后续需要可编辑场景资产，而不是只要 collider，应该往哪里走”。但是短期不应该进入 P0，因为 P0 的目标是稳定的 static collision proxy 和 simulator asset bundle，而不是最漂亮的 mesh。

## 接入判断

- P0：不进入，依赖和训练时间不适合当前闭环。
- P1：refined PLY 可作为 high-quality visual baseline，和 GS2Mesh、2DGS/GOF 放在同一组对照；mesh 需要先修 normal/winding、双面可见性和碎片清理。
- P2/P3：如果后面要把 mesh 编辑、物体动画、Blender/Unity 资产修改接入 Video2Mesh，可以重新评估 SuGaR hybrid representation。
