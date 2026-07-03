---
title: Segment Anything / SAM
id: video2mesh-semantic-scene-graph-sam
category: 调研目录
visibility: public
summary: SAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Segment Anything / SAM

![SAM semantic masks](../assets/stage-semantics.svg "SAM 给 Video2Mesh 提供 2D masks，是后续 2D-to-3D 语义融合的基础")

## 链接

- Project page: https://segment-anything.com/
- GitHub: https://github.com/facebookresearch/segment-anything
- Paper: https://arxiv.org/abs/2304.02643
- Venue: ICCV 2023

## 摘要要点

Segment Anything 提出 promptable segmentation：给定点、框、文本外部提示或自动采样点，它可以在图像中生成候选 masks。论文强调大规模数据和模型的可迁移性，使 SAM 成为很多开放词汇分割、视频跟踪和 2D-to-3D 语义管线的基础模块。

SAM 本身不负责“知道这是床还是窗帘”，它只给 mask。类别命名需要 GroundingDINO、YOLO-World、VLM 或人工标签；跨帧一致性需要 tracker；投到 3D 后还需要可见性过滤和多视角投票。

## Pipeline

| 阶段 | 作用 |
|---|---|
| prompt generation | 自动点、检测框或人工点框生成 SAM prompt |
| mask prediction | 输出单帧候选 masks |
| tracking / association | 跨帧保持 object id |
| 2D-to-3D fusion | 将 masks 投票到点云、Gaussian 或 mesh faces |
| semantic sidecar | 生成 object id / label / probability |

## 输入与输出

输入：图像、点/框/自动提示、可选文本检测结果。输出：2D masks、mask confidence、后续 tracking/fusion 所需的 per-frame object regions。

## 在 Video2Mesh 中的位置

P0/P1 语义输入，但要配合跟踪、投影和可见性过滤。当前 Video2Mesh 已有 SAM v1 相关路径，适合继续服务 object masks、semantic splats 和 mesh face sidecar。

## 输出/接入记录

本周 P1 ray projection debug 因没有真实 2D masks，只能用 projected semantic point label masks 调试，所以串色明显。正式 semantic mesh run 的结果说明：一旦 3D object masks 和 mesh transfer 更完整，COLMAP Delaunay local transfer 可以达到 84.98% face semantic coverage。

## 接入判断

- P0：作为 2D mask 输入保留。
- P1：接 Grounded-SAM、tracking 和 face sidecar。
- 风险：mask 边界错误会沿投影传播到 mesh，必须有可视化审核。
