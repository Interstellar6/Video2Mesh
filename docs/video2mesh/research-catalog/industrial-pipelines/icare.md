---
title: Icare / 学长文档路线
id: video2mesh-industrial-pipelines-icare
category: 调研目录
visibility: public
summary: 学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。
tags:
  - 工业资产管线
  - Research Catalog
---

# Icare / 学长文档路线

## 简介

学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。

## 输入与输出

输入：扫描/生成资产。输出：viewer 可消费的 visual + collider + metadata。

## 在 Video2Mesh 中的位置

作为 Video2Mesh 架构参考，不能替代本项目导出合同。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
