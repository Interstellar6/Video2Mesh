---
title: image-blaster Object Jobs
id: video2mesh-object-mesh-completion-image-blaster-object-jobs
category: 调研目录
visibility: public
summary: image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# image-blaster Object Jobs

## 简介

image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。

## 输入与输出

输入：object crop / prompt / world object config。输出：object.json、GLB/OBJ、viewer 资产。

## 在 Video2Mesh 中的位置

可借用目录约定和 object job 思路，但 simulator bundle 仍由 Video2Mesh 导出。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
