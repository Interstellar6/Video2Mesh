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

## 在 Video2Mesh 中的位置

适合作为 P2 高质量 visual mesh 路线。它可以帮助回答“如果我们后续需要可编辑场景资产，而不是只要 collider，应该往哪里走”。但是短期不应该进入 P0，因为 P0 的目标是稳定的 static collision proxy 和 simulator asset bundle，而不是最漂亮的 mesh。

## 接入判断

- P0：不进入，依赖和训练时间不适合当前闭环。
- P1：可作为 high-quality visual mesh baseline，和 GS2Mesh、2DGS/GOF 放在同一组对照。
- P2/P3：如果后面要把 mesh 编辑、物体动画、Blender/Unity 资产修改接入 Video2Mesh，可以重新评估 SuGaR hybrid representation。
