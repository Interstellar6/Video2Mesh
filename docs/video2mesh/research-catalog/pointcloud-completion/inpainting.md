---
title: 2D/3D Inpainting
id: video2mesh-pointcloud-completion-inpainting
category: 调研目录
visibility: public
summary: 2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# 2D/3D Inpainting

![2D/3D inpainting](../assets/stage-completion.svg "2D/3D inpainting 可以修复纹理或几何缺口，但不能直接替代物理可信 collider")

## 链接

- LaMa image inpainting: https://github.com/advimman/lama
- Stable Diffusion inpainting: https://huggingface.co/docs/diffusers/using-diffusers/inpaint
- Instruct-NeRF2NeRF reference: https://instruct-nerf2nerf.github.io/

## 简介

2D inpainting 修复单帧图像纹理，3D inpainting 或 scene completion 尝试补点、补 surface 或补 radiance field。它们适合修复视觉缺口，但不能直接被当作物理真实 collider。对 Video2Mesh 来说，inpainting 最好服务 clean plate、纹理补全和 visual mesh；碰撞层仍要保守处理。

多视角一致性是最大挑战：单帧看起来合理，不代表从其他相机角度也成立。

## Pipeline

| 阶段 | 作用 |
|---|---|
| mask selection | 定义缺损区域或要移除的物体 |
| 2D inpainting | 修复单帧图像 |
| multi-view consistency | 检查跨帧纹理/深度一致性 |
| optional 3D update | 重建或更新 3DGS/mesh/texture |
| metadata | 标注 synthetic region 和置信度 |

## 输入与输出

输入：masks、images、depth、point cloud 或 mesh。输出：修复图像、修复纹理、补点/补 surface 或 clean plate evidence。

## 在 Video2Mesh 中的位置

P1/P2，不应直接伪造物理可信 collider。短期可以作为 object/background visual repair 的候选，而不是 simulator bundle 的物理来源。

## 接入判断

- P0：不进入。
- P1：用于 clean plate 和纹理补全。
- 风险：生成内容必须可追踪，不能和真实扫描混淆。
