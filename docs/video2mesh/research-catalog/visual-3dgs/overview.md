---
title: 视觉重建与 3DGS 阶段
id: visual-3dgs
category: 调研目录
summary: 梳理 GraphDECO 3DGS、前馈 3DGS、AnySplat、DepthSplat、Spark、SuperSplat 等视觉代理方案，以及它们和 mesh/collider 的边界。
tags:
  - Research Catalog
  - 3DGS
  - Feed-forward 3DGS
  - AnySplat
  - DepthSplat
  - PGSR
  - Spark
  - SuperSplat
visibility: public
---

# 视觉重建与 3DGS 阶段

3DGS 在 Video2Mesh 中应该被定位为 **visual proxy**：它负责让扫描场景看起来真实，但不直接承担碰撞、导航、刚体交互和语义查询。

![3DGS 视觉代理在 Video2Mesh 中的位置](../assets/pipeline-overview.svg "3DGS 是视觉真实感层，不直接承担 collider、导航网格或 simulator physics body")

## 主要项目和模型

| 项目 / 方法 | 简介 | 适合承担 | 不适合承担 |
|---|---|---|---|
| GraphDECO 3D Gaussian Splatting | 经典 3DGS 训练实现，用 COLMAP 相机和点云初始化高斯场景 | 当前 P0/P1 真实场景视觉层，生成高质量 splat/PLY | 直接输出可靠 mesh topology 或 collider |
| [PGSR](pgsr.md) | Planar-based Gaussian Splatting，把 3DGS 约束到更接近表面的局部平面，并渲染 depth/normal 做 TSDF mesh | P1/P2 surface-aware visual mesh、mask lifting depth、Holi-Spatial 几何后端候选 | 直接当作 simulator collider 或无需 QA 的 mesh 真值 |
| [前馈 3DGS](feed-forward-3dgs.md) | 用预训练模型从少量 posed/unposed/unconstrained views 直接预测 Gaussians、depth 或 cameras | P1 快速 baseline、初始化、depth prior、候选视角分析 | 直接替代经过全局优化的 GraphDECO visual layer |
| [AnySplat](anysplat.md) | 2025 年 unconstrained-view 前馈 3DGS，预测 Gaussians、depth 和 camera poses | P1 无位姿/弱位姿 baseline，GraphDECO 初始化候选 | 直接当作真实 COLMAP 世界坐标或 mesh/collider |
| [DepthSplat](depthsplat.md) | CVPR 2025，连接 Gaussian Splatting 和 depth estimation，可导出 depth 与 Gaussian PLY | P1 前馈 3DGS / depth prior 实验；可接短程 GraphDECO refinement | 直接当作全局 fused scene、mesh source 或 collider |
| Spark / SparkJS | 浏览器端 3DGS/Splat 渲染 runtime，World Labs / Icare 生态中常见 | Web visual layer，加载 `.ply/.splat/.spz/.sog` 等视觉资产 | 物理碰撞和复杂交互本身 |
| SuperSplat | 3DGS 浏览器查看、编辑和导出工具 | 本地/远端检查 splat 质量、清理 floaters、截图展示 | simulator asset bundle 生成 |
| 2DGS / GOF / surface-aware GS | 让 Gaussian 更贴近表面、改善 mesh extraction 的研究路线 | P2 替换或增强训练端，提高后续 mesh 质量 | 短期 P0 工程主链路 |

## 核心边界

```text
GraphDECO 3DGS
  -> visual display
  -> rendered RGB / depth / mask evidence
  -> object visual mesh reconstruction helper

feed-forward 3DGS
  -> quick Gaussian/depth/camera prior
  -> optional GraphDECO refinement
  -> visual QA baseline

not:
  -> collider
  -> navigation mesh
  -> final simulator physics body
```

## 对 Video2Mesh 的结论

3DGS 应该继续作为视觉质量最强的场景层，同时为后续 mesh 重建提供 rendered RGB/depth/mask evidence。GraphDECO 仍是当前 P0 visual layer；前馈 3DGS，包括 DepthSplat 和 AnySplat，更适合作为快速 baseline、初始化或 depth prior。不要直接把 Gaussian center 当作真实表面点云去建最终 mesh，因为当前实验证明这会导致壳状伪影、漂浮片和语义串色；也不要把前馈模型导出的多组 Gaussian PLY 直接视为已经全局融合的房间。

## 2026-07-11 bedroom_4 对比结论

![GraphDECO bedroom_4 原版 3DGS](../assets/graphdeco-bedroom4-original-3dgs.png "原版 GraphDECO 3DGS 渲染质量最好，但新视角下有大量拉丝、漂浮片和高亮伪影")

| 路线 | 本周观察 | 当前定位 |
|---|---|---|
| GraphDECO 原版 3DGS | 渲染质量最好，但新视角下 floaters、拉丝和异常远包围盒明显 | P0 visual layer，继续保留，但要做 viewer-safe / floater cleanup |
| SuGaR | 少了很多远处伪影，double-sided mesh 主体观感不错；主要问题是新视角未扫描区域空洞 | P1/P2 high-quality visual / mesh benchmark |
| AnySplat | 主体和背景渲染不错，点云更贴近表面；仍有前馈 3DGS 带状伪影 | P1 快速 baseline / GraphDECO 初始化候选 |
| DepthSplat | 单组局部结果伪影最少；当前像 6 个 context-view 局部点云，未稳定融合成完整房间 | P1 depth prior / feed-forward baseline，不直接当全局场景 |
