---
title: Grounded-SAM / Open-vocabulary Detection
id: video2mesh-semantic-scene-graph-grounded-sam
category: 调研目录
visibility: public
summary: Grounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Grounded-SAM / Open-vocabulary Detection

## 简介

Grounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。

## 输入与输出

输入：图像和文本类别。输出：带标签的 masks。

## 在 Video2Mesh 中的位置

P1 提升 object label 和 affordance。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
