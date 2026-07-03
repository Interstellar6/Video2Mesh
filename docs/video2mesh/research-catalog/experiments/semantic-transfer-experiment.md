---
title: 语义投影融合实验
id: video2mesh-experiments-semantic-transfer-experiment
category: 调研目录
visibility: public
summary: 早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。
tags:
  - 本项目实验
  - Research Catalog
---

# 语义投影融合实验

![mesh 语义投影融合调试结果](../assets/05-mesh-semantic-transfer-ray-projection.png "早期 ray projection debug 覆盖更高，但床、墙、窗帘、地面之间存在明显串色")

## 实验位置

- Early debug route: `tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_semantic_transfer_P0_P1_delivery/p1_ray_projected_debug`
- Formal replacement: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`
- 相关文档：正式 Semantic Mesh 结果 20260703

## 实验简介

早期 P1 ray projection debug 尝试把语义投到 mesh face/点上，目标是支持点击 face 查询 object id、label 和后续交互属性。这个实验跑通了流程，但由于没有真实 2D masks，只能用 projected semantic point labels 调试，床、墙、窗帘、地面之间存在明显串色。

后来 formal semantic mesh run 进一步补齐 GroundingDINO object discovery、SAM/SAM2 tracking、3D object masks 和多条 semantic transfer 路线，效果明显更适合汇报。

## Pipeline

| 阶段 | 作用 |
|---|---|
| mesh source | COLMAP Delaunay / Open3D Poisson / GS2Mesh |
| semantic evidence | semantic point cloud、semantic splats、object masks |
| face assignment | 投影、KDTree、local transfer 或 projected splats |
| sidecar export | 写出 face -> label/object id/probability |
| viewer QA | 用颜色渲染检查串色、unknown 和边界 |

## 输入与输出

输入：mesh、semantic points/splats、相机、object masks。输出：face semantics、colored semantic mesh、object split 和 coverage statistics。

## 在 Video2Mesh 中的位置

保留路线，但需要真实 2D mask、深度可见性过滤和 smoothing。

## 输出结果摘录

早期图五可以作为“问题案例”：覆盖更高但颜色串扰严重。新 formal run 中，COLMAP Delaunay local transfer 覆盖率 84.98%，projected splats 80.13%，Open3D Poisson 32.21%，GS2Mesh decim100k 55.49%。因此下一步应优先推进 COLMAP Delaunay local transfer + face sidecar。

## 接入判断

- P0：语义 sidecar 可作为增强，不阻塞 static collider。
- P1：进入交互查询主线。
- 风险：串色和 unknown 区域必须用可见性过滤、face graph smoothing 和人工审核控制。
