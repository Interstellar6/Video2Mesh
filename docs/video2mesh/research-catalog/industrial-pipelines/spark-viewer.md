---
title: Spark Viewer
id: video2mesh-industrial-pipelines-spark-viewer
category: 调研目录
visibility: public
summary: Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。
tags:
  - 工业资产管线
  - Research Catalog
---

# Spark Viewer

## 简介

Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。

## 输入与输出

输入：splat/ply/spz/sog。输出：Web 视觉层。

## 在 Video2Mesh 中的位置

P0/P1 展示层，不承担 physics。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
