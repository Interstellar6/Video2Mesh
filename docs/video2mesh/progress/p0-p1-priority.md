---
title: P0/P1 模块优先级
id: video2mesh-p0-p1-priority
category: 进度目录
visibility: public
summary: 记录 Video2Mesh 当前 P0/P1/P2 模块优先级、状态和下一步实验。
tags:
  - P0
  - P1
  - Roadmap
---

# P0/P1 模块优先级

## 当前优先级

| 优先级 | 模块 | 当前状态 | 下一步 |
|---|---|---|---|
| P0 | 场景级 visual/collider 分层 | 已有 Web demo 验证，3DGS visual + COLMAP Delaunay collider 可分离 | 保持稳定，减少大资产发布压力 |
| P0 | 场景级 static collider | COLMAP dense + Delaunay 效果最稳 | 加入 simplify、尺度检查和 face sidecar |
| P0 | 语义 mesh | 新结果 `bedroom4_formal_semantic_mesh_results_20260703` 明显优于前一版 debug 投影 | 统计 face/object 覆盖率，接入评论周报展示 |
| P1 | per-object visual mesh | GS2Mesh/SuGaR/Open3D/Poisson 已有对比 | 针对床、窗帘、桌椅做 object-local 重建 |
| P1 | 物体补全 | image-blaster / Hunyuan3D / Meshy / TRELLIS 适合作为候选后端 | 选择一两个遮挡物体做回填对齐 |
| P1 | 物体交互 | 需要 collider、semantic sidecar、physics metadata | 先做 rigid body/primitive proxy，再看 dynamic Gaussian |
| P2 | Sim Anything / PhysSplat | 思想有价值，但模型/代码可用性不足 | 跟踪论文和复现，作为物理信息注入方向 |

## 验收指标

- visual layer 和 collider 在同一视角下不明显错位。
- 公开文档能解释每个模块为什么在 P0 或 P1。
- 语义 mesh 能在导师汇报中直观看出床、窗帘、地毯等主要物体区域。
- 每个外部模型都有明确输入、输出、接入阶段和限制。
