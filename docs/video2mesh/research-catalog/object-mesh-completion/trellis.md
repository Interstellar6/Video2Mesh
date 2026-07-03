---
title: TRELLIS
id: video2mesh-object-mesh-completion-trellis
category: 调研目录
visibility: public
summary: TRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# TRELLIS

![TRELLIS](../assets/stage-completion.svg "TRELLIS 是较新的 3D asset generation 路线，可作为物体补全候选")

## 链接

- Project page: https://microsoft.github.io/TRELLIS/
- GitHub: https://github.com/microsoft/TRELLIS
- Paper: https://arxiv.org/abs/2412.01506

## 摘要要点

TRELLIS 代表新一代 3D asset generation 路线，关注从图像或文本条件生成结构较完整的 3D assets。它对 Video2Mesh 的价值和 Hunyuan3D 类似：不是替代场景级重建，而是补全单个 object visual mesh。

这类模型通常能生成更完整、更规整的物体外观，但物理尺度、真实场景对齐和碰撞代理仍需要 Video2Mesh 后处理。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object crop/prompt | 从语义物体准备图像或文字条件 |
| asset generation | 生成 3D asset representation |
| mesh/texture export | 导出 GLB/OBJ 或等价格式 |
| scene alignment | bbox/pose 对齐回扫描场景 |
| physics proxy | 重建 collider 和 material metadata |

## 输入与输出

输入：单图、多视图或文本/图像条件。输出：3D asset、visual mesh、texture 和预览。

## 在 Video2Mesh 中的位置

P1/P2 物体补全候选，重点测试遮挡物体。可以作为 Hunyuan3D/Meshy/InstantMesh 的对照模型。

## 接入判断

- P0：不进入。
- P1：用于 object mesh completion 对照。
- P2：评估更复杂 object asset generation。
- 风险：环境和显存需求、授权、尺度一致性都要单独确认。
