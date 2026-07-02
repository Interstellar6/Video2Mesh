---
title: Video2Mesh 文档中心
category: Overview
summary: Video2Mesh 精简后的唯一主文档入口，按项目总览、流水线、研究路线、交互仿真、运行展示和网站运维分类。
tags:
  - Video2Mesh
  - Docs
---

# Video2Mesh 文档中心

这个目录是 Video2Mesh 的精简文档入口。旧的根目录长报告已经合并到这里，不再作为主文档维护。

## 文档结构

| 文档 | 读者问题 | 内容 |
|---|---|---|
| [01-project-overview.md](01-project-overview.md) | 这个项目到底做什么？ | 项目目标、资产分层、当前边界、参考项目角色 |
| [02-pipeline-and-commands.md](02-pipeline-and-commands.md) | 怎么跑？产物在哪里？ | 端到端流水线、远端命令、关键输出、QA |
| [07-pipeline-route-matrix.md](07-pipeline-route-matrix.md) | 每个流程阶段该选哪条路线？ | 当前选型、备选方法、适用场景和风险对比 |
| [03-research-roadmap.md](03-research-roadmap.md) | 学术和业界路线怎么选？ | 场景扫描、3DGS、mesh、Scene Graph、方法优先级 |
| [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) | 怎么让场景可交互？遮挡怎么补？ | 3DGS-to-mesh、collider、补全、语义、SimAnything 动态线 |
| [08-web-visual-physics-demo.md](08-web-visual-physics-demo.md) | Web 端能不能先演示视逻分离？ | 视觉代理 3DGS + 碰撞代理 mesh 的静态 Web demo |
| [05-operations-and-showcase.md](05-operations-and-showcase.md) | 展示和排错怎么做？ | 远端环境、历史 run、展示清单、常见失败处理 |
| [06-site-and-remote-control.md](06-site-and-remote-control.md) | relumeow.top 怎么更新？ | Markdown 网站、API、登录、远程控制边界 |

## 当前结论

Video2Mesh 的核心路线不是“从视频直接生成一个完美 mesh”，而是把真实扫描视频拆成多层资产：

```text
video
  -> COLMAP / learned pose fallback
  -> GraphDECO 3DGS visual scene
  -> 2D/3D object masks
  -> semantic / probability splats
  -> object visual mesh
  -> collider / physics proxy
  -> simulator adapters and review pack
```

最重要的工程判断：

- 3DGS 负责高质量视觉层，不直接负责碰撞。
- mesh/collider 是物理和交互代理，不要求和视觉 3DGS 一样精细。
- semantic layer 独立保存，必要时投到 mesh face、collider 或 trigger。
- 遮挡补全要分成 object visual completion、background clean plate、physics proxy completion 三件事。
- SimAnything / PhysSplat 应作为 dynamic Gaussian 和物理属性增强线，不替代 mesh/collider 主链路。

## 优先级

| 优先级 | 目标 | 当前推荐 |
|---|---|---|
| P0 | 跑通可展示闭环 | COLMAP + GraphDECO + SAM2 + 3D masks + simulator bundle |
| P0 | 场景级碰撞 | dense point cloud / Poisson / simplified static collider |
| P1 | 物体 visual mesh | 3DGS rendered RGB/depth/normal/mask -> TSDF / Poisson |
| P1 | 动态物体 collider | primitive compound / convex hull / CoACD or V-HACD |
| P1 | 遮挡补全 | Hunyuan3D / Meshy / TRELLIS / image-blaster 生成完整视觉 mesh，再按 bbox 对齐 |
| P2 | 高质量 3DGS-to-mesh | GS2Mesh-style stereo depth fusion、SuGaR、2DGS、GOF |
| P2 | 动态 Gaussian | SimAnything / PhysSplat-style semantic Gaussian -> physics object |

## 旧文档合并说明

| 旧主题 | 新位置 |
|---|---|
| `Video2Mesh_PROJECT_README.md`、`README.md` | [01-project-overview.md](01-project-overview.md) |
| `VIDEO2MESH_PIPELINE.md`、`SVLGaussian_frame_matching_notes.md` | [02-pipeline-and-commands.md](02-pipeline-and-commands.md) |
| `SCENE_SCANNING_SOLUTIONS_SURVEY.md`、`FEED_FORWARD_GAUSSIAN_SCENE_GRAPH_SURVEY.md` | [03-research-roadmap.md](03-research-roadmap.md) |
| `MESH_RECONSTRUCTION_METHODS_SURVEY.md`、`INTERACTIVE_GAME_SCENE_FROM_3DGS_SURVEY.md`、`SIM_ANYTHING_PHYS_SPLAT_SURVEY.md` | [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) |
| `REMOTE_SETUP_STATUS.md`、`Video2Mesh_real_demo_runbook.md`、`Video2Mesh_milscene*.md` | [05-operations-and-showcase.md](05-operations-and-showcase.md) |
| `docs-blog/content/*.md` | [06-site-and-remote-control.md](06-site-and-remote-control.md) |
