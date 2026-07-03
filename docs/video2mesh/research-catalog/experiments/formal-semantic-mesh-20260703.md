---
title: 正式 Semantic Mesh 结果 20260703
id: video2mesh-experiments-formal-semantic-mesh-20260703
category: 调研目录
visibility: public
summary: 新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。
tags:
  - 本项目实验
  - Research Catalog
---

# 正式 Semantic Mesh 结果 20260703

## 简介

新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。

## 输入与输出

主要区域如床、窗帘/绿色大面、蓝色物体、地毯和小物件颜色区分更清楚。

## 在 Video2Mesh 中的位置

下一步统计 face/object 覆盖率，并接入 object/collider sidecar。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
