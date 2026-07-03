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

## 简介

Meshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。

## 输入与输出

输入：图片或文本 prompt。输出：mesh / texture。

## 在 Video2Mesh 中的位置

P1 快速补全候选，需记录 provenance 和人工 QA。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
