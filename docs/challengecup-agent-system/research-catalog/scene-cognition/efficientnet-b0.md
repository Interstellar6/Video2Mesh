---
title: EfficientNet-B0
id: challengecup-efficientnet-b0
category: 调研目录
research_stage: scene-cognition
visibility: public
summary: EfficientNet-B0 是轻量 CNN backbone，适合作为场景认知 fallback，但本项目历史上需要注意 1280/2048 特征维度不匹配。
tags:
  - EfficientNet
  - Backbone
  - 场景认知
---

# EfficientNet-B0

## 项目/论文链接

- 论文：[EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks](https://arxiv.org/abs/1905.11946)
- PyTorch 入口：[torchvision EfficientNet](https://pytorch.org/vision/stable/models/efficientnet.html)

## 摘要要点

EfficientNet 提出 compound scaling，同时按深度、宽度和分辨率缩放网络，以更少参数获得更高精度。EfficientNet-B0 是最小基线模型，参数量低，适合作为端侧或轻量场景分类 backbone。

## Pipeline

```text
input image
  -> EfficientNet-B0 features
  -> scene head
  -> scene label / feature vector
  -> task decision
```

## 在本项目中的作用

EfficientNet-B0 可以作为没有 Places365 权重时的 fallback，但它输出特征维度通常是 1280，而当前 ResNet50 Places365 配置是 2048。并行 orchestrator 或 novelty detector 如果仍假设 2048，就会出现维度不匹配。

## 接入状态

已存在 fallback 路径，但不作为推荐主路径。相关文件：

- `agent_system/models/scene_cognition.py`
- `agent_system/live_camera.py`
- `agent_system/config.py`

## 输出结果摘录

历史 smoke test 的主要风险就是 fallback backbone 输出 1280 维，而下游仍按 `SCENE_FEATURE_DIM=2048` 初始化。因此当前使用 Places365 ResNet50 更稳；如切回 EfficientNet，需要同步更新下游 feature dim。

