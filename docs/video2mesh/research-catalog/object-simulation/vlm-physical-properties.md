---
title: VLM Physical Properties
id: video2mesh-object-simulation-vlm-physical-properties
category: 调研目录
visibility: public
summary: VLM 可估计物体类别、材质、可抓取性、是否可移动等属性，但数值物理参数仍需校准。
tags:
  - 物体仿真
  - Research Catalog
---

# VLM Physical Properties

## 简介

VLM 可估计物体类别、材质、可抓取性、是否可移动等属性，但数值物理参数仍需校准。

## 输入与输出

输入：图像、object crop、语义标签。输出：material/body hints。

## 在 Video2Mesh 中的位置

P1 辅助填写 simulator asset bundle。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
