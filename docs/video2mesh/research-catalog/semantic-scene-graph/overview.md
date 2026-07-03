---
title: 语义与 Scene Graph 阶段
id: semantic-scene-graph
category: 调研目录
summary: 整理 2D/3D 语义分割、semantic splats、mesh face sidecar 和 scene graph 在交互场景中的作用。
tags:
  - Research Catalog
  - Semantics
  - Scene Graph
  - SAM
visibility: public
---

# 语义与 Scene Graph 阶段

语义层要服务交互查询：点击到哪个 face、属于哪个 object、是什么材质、能不能移动、能不能抓取、和其他物体有什么关系。

![语义与 Scene Graph](../assets/stage-semantics.svg "从 2D masks 到 3D labels，再到 mesh face sidecar 和交互查询")

## 主要项目和方法

| 项目 / 方法 | 简介 | 对 Video2Mesh 的作用 | 风险 |
|---|---|---|---|
| Segment Anything / SAM | 通用 2D mask 生成/提示分割 | 生成 object masks，支持视频帧中的对象区域 | 无语义类别，需要 detector/VLM 命名 |
| GroundingDINO / Grounded-SAM | 文本提示驱动检测 + mask | 开放词汇发现床、桌、椅、窗帘等对象 | 边界和类别稳定性需多帧融合 |
| 2D-to-3D mask fusion | 将每帧 mask 投影/投票到 3D 点或 Gaussian | 生成 3D object masks、semantic/probability splats | 遮挡和深度误差会造成串色 |
| Semantic splats | 给 3DGS/point cloud 携带 object probability | 支持可视化、hover、语义筛选和 mesh 回灌 | 不等同于 mesh face 语义 |
| Mesh face sidecar | 按 triangle index 保存 label/probability/material/affordance | 点击 collider 后直接查 object_id 和交互属性 | mesh 简化/替换时需要重建索引或映射 |
| Scene graph / VLM relation QA | 物体关系、支撑关系、可交互属性推理 | 给 simulator asset bundle 补 affordance、support、material | VLM 输出必须可复核 |

## 推荐数据合同

```json
{
  "mesh": "colliders/scene_collision.glb",
  "face_semantics": [
    {
      "face": 1024,
      "object_id": "bed_01",
      "label": "bed",
      "probability": 0.91,
      "material": "cloth",
      "affordance": ["support", "sit_or_lie"]
    }
  ]
}
```

## 当前项目状态

本周已验证 P0 KDTree 语义回灌和 P1 ray projection debug 路线。P1 当前没有真实 2D masks，只能用 projected semantic point label masks 调试，因此串色明显，暂时不能作为生产级语义融合结果。下一步应接入真实 2D mask、深度可见性过滤和 face graph smoothing。
