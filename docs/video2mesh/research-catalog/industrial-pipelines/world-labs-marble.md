---
title: World Labs / Marble
id: video2mesh-industrial-pipelines-world-labs-marble
category: 调研目录
visibility: public
summary: World Labs Marble 更偏 static world/background 生成，可提供 splat、collider、pano 等世界资产。
tags:
  - 工业资产管线
  - Research Catalog
---

# World Labs / Marble

## 链接

- World Labs: https://www.worldlabs.ai/
- Marble API docs: https://docs.worldlabs.ai/
- image-blaster local script: `image-blaster/scripts/generate-world.mjs`

## 简介

World Labs / Marble 更偏 static world/background 生成。它的价值不在于替 Video2Mesh 做每个物体的交互资产，而在于给一个 clean plate / static world 层：splat 负责视觉，collider mesh 负责基础空间约束，pano/thumbnail 用于 viewer 和预览。

在 image-blaster 的使用方式里，World Labs 主要被当作 background/world generator：先从场景描述中去掉需要单独处理的 foreground objects，形成 clean plate prompt，再请求 Marble 生成世界资产。

## Pipeline 摘要

![World/background 与 object mesh 的分层](../assets/pipeline-overview.svg "World Labs 更靠近 static world/background 层；object mesh 和 simulator bundle 仍由 Video2Mesh/image-blaster 后续模块处理")

## 输入与输出

| 阶段 | 作用 |
|---|---|
| scene description / clean plate | 描述去掉 foreground objects 后的背景世界 |
| world generation | 调用 Marble world generation API |
| asset download/cache | 下载 splat、collider mesh、panorama、thumbnail 等世界资产 |
| local viewer loading | 运行时消费本地 `/worlds/` 路径，不直接依赖 provider URL |

输入：场景描述、clean plate 或生成请求。输出：static world assets，包括视觉层 splat、基础 collider、pano/thumbnail 和 provenance/resume 信息。

## 在 Video2Mesh 中的位置

适合借鉴两个点：

- 静态背景和前景物体分层。背景可以是 splat/world layer，物体由 object mesh/jobs 单独处理。
- visual proxy 与 collider proxy 分开保存。即使视觉是 splat，交互也需要独立 collider/physics contract。

Video2Mesh 如果后续做背景补全，可以把 World Labs 类方法放在 background clean plate 方向，但仍要自己生成 simulator asset bundle、semantic IDs、physics sidecar 和 Unity/MuJoCo/Isaac adapter。

## 接入判断

- P0：不进入，当前 P0 依赖真实扫描视频和本项目可控输出。
- P1：可借鉴 clean plate/background repair 的资产分层合同。
- P2/P3：如果需要生成缺损背景或静态世界替换，可作为工业方案对照。
