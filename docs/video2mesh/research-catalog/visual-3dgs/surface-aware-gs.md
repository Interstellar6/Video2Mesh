---
title: Surface-aware Gaussian 路线
id: video2mesh-visual-3dgs-surface-aware-gs
category: 调研目录
visibility: public
summary: SuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# Surface-aware Gaussian 路线

![Surface-aware GS](../assets/stage-visual-3dgs.svg "Surface-aware Gaussian 路线把视觉高斯约束到更明确的表面，为后续 mesh extraction 降低噪声")

## 链接

- SuGaR: https://anttwo.github.io/sugar/
- 2DGS: https://github.com/hbb1/2d-gaussian-splatting
- GOF: https://niujinshuchong.github.io/gaussian-opacity-fields/
- GS2Mesh: https://gs2mesh.github.io/

## 摘要要点

Surface-aware Gaussian 是一个路线族，而不是单个模型。它们共同解决的问题是：传统 3DGS 对视觉渲染很强，但没有天然 surface topology。SuGaR 通过 surface alignment 和 Poisson extraction 得到 mesh + Gaussian hybrid；2DGS 把 Gaussian 改为更像 surfel 的二维 oriented disks；GOF 从 opacity field 和 tetrahedral extraction 方向得到更紧凑 surface；GS2Mesh 则用 3DGS novel-view 渲染 + stereo depth + fusion 避免直接连 Gaussian center。

这些方法比“3DGS center -> Poisson”更合理，但通常需要新训练、新环境或额外深度/TSDF 流程。

## Pipeline

| 路线 | Pipeline | 输出 |
|---|---|---|
| SuGaR | 3DGS warm-up -> surface alignment -> Poisson mesh -> hybrid refinement | editable mesh + surface-bound Gaussians |
| 2DGS | images -> 2D Gaussian disks -> normal/depth regularization -> meshing | surfel-like visual representation and mesh |
| GOF | Gaussian opacity field -> geometry-aware optimization -> marching tetrahedra | adaptive surface mesh |
| GS2Mesh | 3DGS render stereo views -> depth estimation -> TSDF/depth fusion | visual mesh |

## 输入与输出

输入：训练图像、COLMAP 相机、已有 3DGS 或方法专用训练结果。输出：更贴近表面的 Gaussian 表示、visual mesh、可编辑 hybrid asset。

## 在 Video2Mesh 中的位置

P2 研究升级线，短期不替代 GraphDECO P0。当前结论是：COLMAP Delaunay 更适合 P0 static collider；GS2Mesh/SuGaR/2DGS/GOF 更适合作为 high-quality visual mesh benchmark 或后续 per-object mesh 升级方向。

## 输出/接入记录

本周已尝试 GS2Mesh 和 SuGaR/GS2Mesh 类 mesh 重建对照。GS2Mesh 原始 mesh 体量较大，减面后可展示，但墙面破碎和漂浮片仍需要清理；因此它更适合做 visual mesh 对照，不适合直接替代 collider 主链路。

## 接入判断

- P0：不进入主 collider 链路。
- P1：可作为 visual mesh benchmark。
- P2/P3：探索 per-object mesh、editable asset 和 surface-aware training。
