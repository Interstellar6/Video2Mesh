---
title: Meshy
id: video2mesh-object-mesh-completion-meshy
category: 调研目录
visibility: public
summary: Meshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# Meshy

![Meshy](../assets/stage-completion.svg "Meshy 是商业 image/text-to-3D 服务，适合快速得到展示级 object mesh")

## 链接

- Meshy: https://www.meshy.ai/
- Meshy API docs: https://docs.meshy.ai/
- image-blaster backend reference: `image-blaster/scripts/generate-single-asset.mjs`

## 简介

Meshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。它的优势是工程接入成本低、生成结果适合汇报预览；缺点是外部服务依赖、结果可控性和 provenance/授权需要记录。

在 image-blaster 里，Meshy 可以作为 Hunyuan3D 的 alternative backend。Video2Mesh 需要把它定位为 object visual completion provider，而不是仿真资产生成器。

## Pipeline

| 阶段 | 作用 |
|---|---|
| prompt/reference image | 从 object crop 或文字描述构造任务 |
| Meshy generation | 调用 image/text-to-3D 服务 |
| asset download | 获取 mesh、texture、thumbnail |
| Video2Mesh import | 按 object id 回填并 bbox fitting |
| collider rebuild | 生成 primitive/convex collider |

## 输入与输出

输入：图片或文本 prompt。输出：mesh、texture、thumbnail、服务端任务记录和下载链接。

## 在 Video2Mesh 中的位置

P1 快速补全候选，需记录 provenance 和人工 QA。适合在导师汇报里快速展示 object completion 的潜力，但最终主链路仍要可复现和可控。

## 接入判断

- P0：不进入。
- P1：作为商业 baseline/快速 demo 后端。
- 风险：外部 API、费用、服务端版本变化和生成尺度不确定。
