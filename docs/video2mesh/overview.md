---
title: Video2Mesh 总目录
id: video2mesh-home
category: 总目录
doc_type: overview
visibility: public
summary: Video2Mesh 的公开文档入口，集中展示项目文档、调研目录、实验记录、进度结果和当前路线判断。
tags:
  - Video2Mesh
  - 总目录
  - 3D Scene Assets
---

# Video2Mesh 总目录

这个文档空间挂载在 `/video2mesh/` 子路由下，用来集中展示 Video2Mesh 从真实扫描视频到可交互 3D 场景资产的项目说明、技术调研、实验记录、进度记录和运行方式。

![Video2Mesh 文档地图](research-catalog/assets/pipeline-overview.svg "Video2Mesh 从扫描视频到视觉层、mesh、语义、碰撞代理、物体仿真和引擎适配的文档地图")

## 阅读路径

| 路径 | 内容边界 |
|---|---|
| 项目文档 | 项目定位、pipeline 合同、运行命令和本地/远端边界 |
| 调研目录 | 按输入、3DGS、mesh、补全、语义、collider、仿真和工业管线拆分的技术路线 |
| 实验目录 | 已在本项目 bedroom 场景真实跑过的 mesh、语义回灌、object split 和 demo 结果 |
| 进度目录 | 当前 P0/P1 优先级、周报和可展示实验结果 |
| Legacy | 旧长文、历史草稿和内部记录，默认不作为公开入口 |

## 当前一句话

Video2Mesh 的目标不是把视频压成一个单一 mesh，而是生成一组分层资产：3DGS 负责视觉真实感，mesh/collider 负责碰撞和交互，semantic sidecar 负责语义和物理属性，最终由 Web、Unity、MuJoCo、Isaac 等 runtime 消费。
