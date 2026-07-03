---
title: Visual / Physics Proxy Demo
id: video2mesh-experiments-visual-physics-proxy-demo
category: 调研目录
visibility: public
summary: 本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。
tags:
  - 本项目实验
  - Research Catalog
---

# Visual / Physics Proxy Demo

## 简介

本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。

## 输入与输出

入口曾为 http://127.0.0.1:4173/demos/visual-physics-proxy/。

## 在 Video2Mesh 中的位置

证明交互逻辑不需要依赖 3DGS 自身产生 collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
