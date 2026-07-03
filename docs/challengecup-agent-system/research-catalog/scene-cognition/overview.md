---
title: 场景认知环节 Overview
id: challengecup-scene-cognition-overview
category: 调研目录
research_stage: scene-cognition
research_doc_role: overview
visibility: public
summary: 场景认知环节把输入图像映射为 air/sea/urban/forest 等场景和可见度、噪声、地形条件，用于任务决策和数据闭环。
tags:
  - 场景认知
  - Places365
  - EfficientNet
---

# 场景认知环节 Overview

场景认知不是最终 mAP 的直接计算模块，但它决定后处理、demo 策略和数据闭环的方向。R1 文件名已经提供 `air/sea/urban/forest` 标签，因此场景认知可以作为轻量模型训练，也可以作为规则解析输入。

## 本项目位置

```text
image / frame
  -> scene cognition
  -> scene label + confidence
  -> task decision / scene prior
  -> detector thresholds and allowed classes
```

## 文档

| 文档 | 作用 |
|---|---|
| [Places365 / ResNet50 场景模型](places365-resnet50.md) | 当前配置中的推荐场景 backbone |
| [EfficientNet-B0](efficientnet-b0.md) | 轻量 fallback，历史上有 feature dim mismatch 风险 |
| [MobileCLIP / 零样本场景理解](mobileclip.md) | 未来用文本提示做场景/天气识别的候选 |

