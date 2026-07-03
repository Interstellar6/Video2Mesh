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

## 简介

World Labs Marble 更偏 static world/background 生成，可提供 splat、collider、pano 等世界资产。

## 输入与输出

输入：场景描述、clean plate 或生成请求。输出：static world assets。

## 在 Video2Mesh 中的位置

可借鉴 visual/collider 分层和 clean plate 思路，不负责 Video2Mesh simulator bundle。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
