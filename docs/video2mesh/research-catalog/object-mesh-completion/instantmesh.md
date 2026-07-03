---
title: InstantMesh
id: video2mesh-object-mesh-completion-instantmesh
category: 调研目录
visibility: public
summary: InstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# InstantMesh

![InstantMesh](../assets/stage-completion.svg "InstantMesh 代表快速 image-to-mesh 的 feed-forward 物体补全路线")

## 链接

- Project page: https://jiahao.ai/instantmesh/
- GitHub: https://github.com/TencentARC/InstantMesh
- Paper: https://arxiv.org/abs/2404.07191

## 摘要要点

InstantMesh 是 feed-forward sparse-view 3D mesh reconstruction 路线，目标是从单图或少量视图快速生成带纹理的 3D mesh。相比逐物体优化，它的优势是速度和批量化；相比 Hunyuan3D/Meshy 等生成服务，它更适合作为本地可控 baseline。

对 Video2Mesh 来说，InstantMesh 可以作为 object completion 的快速对照：同一批 object crops 同时跑 Hunyuan3D/image-blaster 和 InstantMesh，比较闭合性、尺度拟合、纹理一致性和 collider 生成难度。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object image preparation | 从 selected frame / mask 中取 object crop |
| novel-view / reconstruction | feed-forward 生成多视角或 3D 表示 |
| mesh extraction | 输出 textured mesh |
| bbox fitting | 对齐回 Video2Mesh object bbox |
| collider proxy | 生成 primitive/convex collider |

## 输入与输出

输入：单图或少量多视角物体图像。输出：object mesh、texture、预览图和可回填 Video2Mesh 的 object-local visual asset。

## 在 Video2Mesh 中的位置

P1 批量候选，可能需要更多纹理和尺度修正。它适合先跑 2-3 个清晰物体，作为 Hunyuan3D/Meshy 的开源 baseline。

## 接入判断

- P0：不进入。
- P1：用于批量 object mesh baseline。
- 风险：真实室内物体遮挡严重时，单图生成可能和原场景外观不一致。
