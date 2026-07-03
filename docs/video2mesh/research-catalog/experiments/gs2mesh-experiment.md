---
title: GS2Mesh 实验
id: video2mesh-experiments-gs2mesh-experiment
category: 调研目录
visibility: public
summary: 本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。
tags:
  - 本项目实验
  - Research Catalog
---

# GS2Mesh 实验

## 简介

本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。

## 输入与输出

raw mesh 约 4.48M vertices / 8.09M triangles，原始文件约 333MB。

## 在 Video2Mesh 中的位置

效果能保留床、窗帘和大结构，但仍有墙面破碎、漂浮片和局部缺失。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
