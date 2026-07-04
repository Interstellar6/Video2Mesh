---
title: Video2Mesh README
id: video2mesh-home
category: 总目录
doc_type: overview
visibility: public
summary: Video2Mesh 的项目 README，集中展示项目目标、目录结构、技术路线、进度入口和运行文档入口。
tags:
  - Video2Mesh
  - README
  - 总目录
  - 3D Scene Assets
---

# Video2Mesh README

Video2Mesh 是一个从真实扫描视频生成可交互 3D 场景资产的项目。它不追求把所有信息压成一个“万能 mesh”，而是把视觉、几何、碰撞、语义、物理和运行时适配拆成互相对齐的多层资产。

![Video2Mesh 文档地图](research-catalog/assets/pipeline-overview.svg "Video2Mesh 从扫描视频到视觉层、mesh、语义、碰撞代理、物体仿真和引擎适配的文档地图")

## 项目目标

```text
scan video
  -> camera / point cloud
  -> 3DGS visual proxy
  -> scene mesh / collider proxy
  -> object visual mesh / completion
  -> semantic sidecar / scene graph
  -> physics metadata
  -> Web / Unity / MuJoCo / Isaac adapters
```

当前核心判断：

- 3DGS / Spark / SuperSplat 负责视觉真实感。
- mesh / collider 负责碰撞、导航、点击和交互。
- 语义应保存在 sidecar，而不是绑死在会被简化或替换的 mesh 里。
- 物体补全、背景 clean plate、物理代理补全要拆开。
- Sim Anything / PhysSplat 这类动态 Gaussian 方法值得跟踪，但短期不替代 mesh/collider 主链路。

## 文档目录

| 目录 | 内容边界 |
|---|---|
| [调研文档目录](research-catalog/overview.md) | 按输入位姿、3DGS、Mesh 重建、点云/背景补全、物体补全、语义、碰撞代理、仿真和工业管线拆分的技术调研 |
| [项目进度文档目录](progress/overview.md) | 当前 P0/P1 优先级、周报和可展示实验结果 |
| [项目运行文档目录](project-docs/overview.md) | 项目简介、pipeline 合同、运行命令和本地/远端边界 |

## 当前 P0 主链路

```text
video frames
  -> COLMAP sparse/dense
  -> GraphDECO 3DGS visual layer
  -> COLMAP Delaunay static collider
  -> semantic sidecar
  -> visual/physics proxy demo
```

P0 的目标是展示和交互闭环，不是最佳画质。当前最稳的场景级碰撞代理仍是 COLMAP dense + Delaunay mesh；3DGS 作为 visual layer；语义与物理属性通过 sidecar 管理。

## 代表性结果

| 实验 | 当前结论 |
|---|---|
| GS2Mesh | raw mesh 能保留床、窗帘、大型家具和房间轮廓，但体量大、墙面破碎、漂浮片明显，适合作 P1/P2 visual mesh benchmark |
| Open3D Poisson | 输出体量可控，但对 3DGS center point cloud 容易形成壳状伪影和漂浮面，适合作 baseline/fallback |
| COLMAP Delaunay | 视觉细节不如 3DGS，但作为 static collider 更稳定，是当前 P0 推荐 |
| 语义投影融合 | 适合把 object labels、materials 和 affordance 放入 face/object sidecar，而不是直接写死进 mesh |

![COLMAP Delaunay dense mesh](progress/assets/03-colmap-delaunay-dense.png "COLMAP Delaunay dense mesh 更适合作为场景级 static collision proxy")

## 接入 relumeow.top 的规则

Video2Mesh 仓库继续维护自己的文档、实验记录、资产说明和 README；relumeow.top 只负责统一首页、导航、主题、权限、构建、部署和后台覆盖层。新增内容应优先放入本目录下的三个顶层目录，站点会通过 `projects.yaml` 聚合。
