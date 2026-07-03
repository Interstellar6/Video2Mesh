---
title: Mesh Face Sidecar
id: video2mesh-semantic-scene-graph-mesh-face-sidecar
category: 调研目录
visibility: public
summary: mesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Mesh Face Sidecar

![Mesh face sidecar](../assets/stage-semantics.svg "Mesh face sidecar 将 triangle index 映射到 object id、label、material 和交互属性")

## 链接

- glTF extensions registry: https://github.com/KhronosGroup/glTF/tree/main/extensions
- Unity Mesh API: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh.html
- Video2Mesh formal output: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`

## 简介

Mesh face sidecar 把 triangle face index 映射到 object id、label、material、affordance 和置信度，不把语义烘死在顶点色或贴图里。这样 collider raycast 命中某个 face 后，可以直接查“这是床、窗帘还是地板”，再决定交互、物理和 UI。

它是 Video2Mesh 从“能看见 mesh”走向“能和物体交互”的关键合同。sidecar 还方便在 mesh 减面、替换、补全时记录版本和 provenance。

## Pipeline

| 阶段 | 作用 |
|---|---|
| mesh source | COLMAP Delaunay / Poisson / GS2Mesh / object split |
| semantic evidence | 3D object masks、semantic splats、2D masks |
| face assignment | KDTree / projection / voting / smoothing |
| sidecar export | face -> object_id/label/prob/material |
| runtime query | raycast face index -> object semantic and interaction rule |

## 输入与输出

输入：mesh、semantic points/masks、投票结果、object metadata。输出：`mesh_mesh_semantics_local.json`、`face_labels.json` 或等价 sidecar。

## 在 Video2Mesh 中的位置

P0/P1 交互查询关键合同。正式 semantic mesh 结果已经可以产出 per-face semantic transfer 和 object split，总体上比早期 ray projection debug 更适合接交互 demo。

## 输出结果摘录

`bedroom4_formal_semantic_mesh_results_20260703` 中 COLMAP Delaunay local transfer 覆盖 141,993 / 167,082 faces，覆盖率 84.98%，并能拆出 16 个 object split，是当前最值得推进的 mesh semantic sidecar 路线。

## 接入判断

- P0：进入，至少支持 click/raycast 查 label。
- P1：接 material、affordance、body_type 和 object split。
- 风险：mesh 简化后 face index 会变化，必须记录 source mesh hash 或重建映射。
