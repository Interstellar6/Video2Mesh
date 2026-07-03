---
title: image-blaster
id: video2mesh-industrial-pipelines-image-blaster
category: 调研目录
visibility: public
summary: image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。
tags:
  - 工业资产管线
  - Research Catalog
---

# image-blaster

## 简介

image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。

## 输入与输出

输入：object crop、prompt、world config。输出：object mesh、object.json、viewer 目录。

## 在 Video2Mesh 中的位置

P1 物体补全后端和目录约定参考。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
