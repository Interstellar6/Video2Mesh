---
title: 正式 Semantic Mesh 结果 20260703
id: video2mesh-experiments-formal-semantic-mesh-20260703
category: 调研目录
visibility: public
summary: 新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。
tags:
  - 本项目实验
  - Research Catalog
---

# 正式 Semantic Mesh 结果 20260703

![bedroom4 formal semantic mesh](../assets/06-bedroom4-formal-semantic-mesh.png "正式 bedroom4 semantic mesh：相较早期 ray projection debug，主要语义区域更清晰，适合作为周报展示结果")

## 结果路径

- 本地 compact delivery: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`
- 原远端 export root: `/root/autodl-tmp/workspace/Video2Mesh/exports/bedroom_4_cli_colmap_dense_graphdeco30k_47_56_20260702_024145`
- 总结文件：`mesh_recon_results/semantic_bedroom4_formal_delivery/semantic_mesh_summary.json`
- 物体拆分总结：`mesh_recon_results/object_mesh_splits/object_mesh_split_summary.json`

## 输入与输出摘录

这次不是 smoke/debug 版本，而是 bedroom_4 formal run。流程里包含 GroundingDINO object discovery、SAM/SAM2 tracking、3D object masks、semantic dense/3DGS manifest，以及多条 mesh semantic transfer 路线。

## Pipeline

| 阶段 | 作用 |
|---|---|
| COLMAP / GraphDECO base | 使用 bedroom_4 COLMAP dense 和 GraphDECO 30k 结果作为几何与视觉输入 |
| object discovery / tracking | GroundingDINO 发现候选物体，SAM/SAM2 跨帧生成 object masks |
| semantic 3D evidence | 生成 semantic dense/3DGS manifest、3D object masks 和 semantic splats |
| mesh reconstruction routes | 对 COLMAP Delaunay、Open3D Poisson、GS2Mesh decim mesh 分别做语义 transfer |
| face sidecar / object split | 输出 per-face semantics、coverage 统计和 object mesh splits |

| 路线 | Mesh | Face | 已赋语义 face | 覆盖率 | object split |
|---|---:|---:|---:|---:|---:|
| COLMAP dense Delaunay + local semantic transfer | 82,920 vertices | 167,082 | 141,993 | 84.98% | 16 |
| COLMAP dense Delaunay + projected splats | 82,920 vertices | 167,082 | 133,876 | 80.13% | 15 |
| Open3D Poisson dense fused voxel10 | 100,705 vertices | 199,999 | 64,410 | 32.21% | 15 |
| GS2Mesh decim100k | 43,734 vertices | 120,144 | 66,667 | 55.49% | 13 |

COLMAP dense Delaunay local transfer 是当前最适合 P0/P1 之间衔接的路线：几何足够轻，语义覆盖高，能导出 object mesh split。Top labels 里 bed 占 40.82% faces，window 占 13.80%，floor 占 12.57%，wall/door/nightstand/curtain 等也都有可见分配。

## 在 Video2Mesh 中的位置

这版结果说明“mesh + semantic sidecar”已经可作为下一步交互资产的基础：

- scene collider：优先用 COLMAP Delaunay GLB/Ply，稳定且轻。
- semantic sidecar：使用 `mesh_mesh_semantics_local.json` 存 per-face semantic/object id。
- object mesh split：从 face semantics 拆出 bed、window、floor、wall、door、nightstand、curtain、lamp 等物体局部 mesh。
- simulator asset bundle：下一步把 object mesh split 与 body_type、collider、mass、friction/restitution 合并。

## 输出结果判断

从图上看，床、窗户/窗帘、地面、墙面挂画、小桌/灯等主要区域已经比早期 ray projection debug 清楚，能够作为周报正向结果展示。问题仍然在于细小物体和薄结构的边界会抖动；Open3D Poisson 的 unknown/background 比例过高，不适合做主语义 mesh。

## 下一步

- 把 `mesh_mesh_semantics_local.json` 接入 Web viewer，点击 face 或 raycast 时返回 object/label。
- 用 object split 生成 per-object bbox 和 collider candidates。
- 给 object split 加质量统计：闭合性、连通分量、face area、bbox 尺寸。
- 对 bed/nightstand/curtain 做 object completion 对照，测试 Hunyuan3D/image-blaster 回填。

## 接入判断

- P0：COLMAP Delaunay mesh 可以作为 static collider；semantic sidecar 可作为可选增强。
- P1：object split 和 per-face semantics 应进入下一步交互 demo。
- 风险：semantic transfer 的可信度依赖 2D masks 和空间距离阈值，仍需可视化审核和人工纠错入口。
