---
title: 任务决策与后处理环节 Overview
id: challengecup-task-decision-postprocess-overview
category: 调研目录
research_stage: task-decision-postprocess
research_doc_role: overview
visibility: public
summary: 任务决策与后处理环节把场景认知结果转为阈值、类别先验、融合策略、模型选择和门禁。
tags:
  - 任务决策
  - 后处理
  - Model Soups
---

# 任务决策与后处理环节 Overview

这个环节决定“同一个 detector 输出怎样被使用”。它既包括在线策略，如场景先验和 precision policy，也包括离线模型选择，如权重插值和 candidate gate。

## 本项目位置

```text
scene label + detector predictions
  -> allowed classes / thresholds / NMS
  -> candidate metrics
  -> gate
  -> selected runtime profile
```

## 文档

| 文档 | 作用 |
|---|---|
| [Weighted Boxes Fusion](weighted-boxes-fusion.md) | 多尺度/多模型框融合，已尝试但不默认 |
| [Model Soups / 权重平均](model-soups.md) | 当前主力权重插值路线 |

