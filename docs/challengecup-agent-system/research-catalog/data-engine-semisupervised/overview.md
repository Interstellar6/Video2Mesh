---
title: 数据闭环与半监督环节 Overview
id: challengecup-data-engine-semisupervised-overview
category: 调研目录
research_stage: data-engine-semisupervised
research_doc_role: overview
visibility: public
summary: 数据闭环与半监督环节负责错例挖掘、teacher 候选、伪标签、Copy-Paste 和人工复核，是后续继续涨分的主路线。
tags:
  - 数据闭环
  - Teacher Student
  - Pseudo Label
---

# 数据闭环与半监督环节 Overview

当前 R1 指标已经不是“训练一次 YOLO”就能大幅提升的阶段。更高价值的工作是让数据 agent 找到真实弱点，再谨慎引入 teacher、伪标签、Copy-Paste 和人工复核。

## 本项目位置

```text
validation errors
  -> hard groups and mistake images
  -> teacher / open vocabulary candidates
  -> pseudo-label or copy-paste dataset
  -> train specialist
  -> gate or weight interpolation
```

## 文档

| 文档 | 作用 |
|---|---|
| [Unbiased Teacher](unbiased-teacher.md) | 伪标签偏置控制和 teacher gate 思想 |
| [Soft Teacher](soft-teacher.md) | soft pseudo label 和 box jitter 筛选思路 |
| [Active Teacher](active-teacher.md) | 主动学习式样本选择，已部分接入 offline data agent |
| [Grounding DINO](grounding-dino.md) | 开放词汇候选挖掘，待接入 |
| [Simple Copy-Paste](copy-paste.md) | scene-hard 数据增强，已尝试 |
| [FiftyOne / CVAT 错例闭环](fiftyone-cvat.md) | 工程化错例复核和回流标注参考 |

