---
title: MuJoCo / Isaac
id: video2mesh-collider-physics-proxy-mujoco-isaac
category: 调研目录
visibility: public
summary: MuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的 body、joint、mass、friction、scale 合同。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# MuJoCo / Isaac

## 简介

MuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的 body、joint、mass、friction、scale 合同。

## 输入与输出

输入：simulator asset bundle 和 mesh/collider。输出：XML/USD/adapter。

## 在 Video2Mesh 中的位置

P1/P2 仿真适配，需 QA 物理参数。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
