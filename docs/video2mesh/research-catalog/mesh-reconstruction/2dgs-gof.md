---
title: 2DGS / GOF
id: video2mesh-mesh-reconstruction-2dgs-gof
category: 调研目录
visibility: public
summary: 2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。
tags:
  - Mesh 重建
  - Research Catalog
---

# 2DGS / GOF

![2DGS surfel and meshing teaser](https://github.com/hbb1/2d-gaussian-splatting/raw/main/assets/teaser.jpg "2DGS 将场景表示为 2D oriented Gaussian disks / surfels，并支持 surface normal 和 mesh extraction")

## 链接

- 2DGS project/code: https://github.com/hbb1/2d-gaussian-splatting
- 2DGS paper: https://arxiv.org/abs/2403.17888
- GOF project page: https://niujinshuchong.github.io/gaussian-opacity-fields/
- GOF code: https://github.com/autonomousvision/gaussian-opacity-fields
- Venues: 2DGS 为 SIGGRAPH 2024；GOF 为 SIGGRAPH Asia 2024 / TOG

## 摘要要点

2DGS 和 GOF 都是在回应同一个问题：传统 3DGS 视觉质量强，但其 3D Gaussians 是显式、离散、视角相关的体元，不天然形成稳定 surface。2DGS 将体状 Gaussian 压成 2D oriented planar disks / surfels，让几何更接近表面；GOF 则把 3D Gaussians 组织成 opacity field，通过 level set 和 Marching Tetrahedra 做 adaptive mesh extraction。

这两类方法比“从 Gaussian center 做 Poisson”更接近 surface-aware Gaussian 路线，适合未来做高质量 visual mesh 或对比论文结果。但它们通常需要按各自方法重新训练或改训练过程，不是简单接在现有 GraphDECO 3DGS 后面就能稳定产出 collider。

## Pipeline 摘要

## 输入与输出

| 方法 | Pipeline | 输出 |
|---|---|---|
| 2DGS | multi-view images -> 2D oriented Gaussian disks -> perspective-correct splatting -> depth/normal regularization -> meshing | surfel-like Gaussian 表示、normal/depth、mesh |
| GOF | 3DGS-like optimization -> opacity field / ray-Gaussian geometry -> normal regularization -> Gaussian-induced tetrahedral grid -> Marching Tetrahedra | adaptive compact mesh、unbounded scene reconstruction |

![GOF teaser](https://niujinshuchong.github.io/gaussian-opacity-fields/resources/teaser_gof.png "GOF 通过 Gaussian Opacity Field 和 adaptive extraction 得到更紧凑的 surface mesh")

## 在 Video2Mesh 中的位置

它们适合作为 P2/P3 的研究升级路线，用于回答“如果从训练阶段就考虑几何一致性，是否能减少后续 mesh 清理压力”。短期 Video2Mesh 已经有 GraphDECO 3DGS 输出，所以这条线不能直接替代现有 P0；更适合新实验分支，和 GS2Mesh/SuGaR 比较 visual mesh 质量。

## 接入判断

- P0：不进入，当前 collider 仍以 COLMAP Delaunay / cleaned Poisson 为主。
- P1：如果想系统评估 surface-aware Gaussian，需要新增训练配置和评估脚本。
- P2/P3：适合作为论文调研和后续 visual mesh 升级方向，尤其关注 unbounded scene 和背景几何。
