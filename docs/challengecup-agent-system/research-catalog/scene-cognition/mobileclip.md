---
title: MobileCLIP / 零样本场景理解
id: challengecup-mobileclip
category: 调研目录
research_stage: scene-cognition
visibility: public
summary: MobileCLIP 是轻量视觉-语言模型候选，可用文本提示做零样本场景、天气和可见度理解，当前仍是实验方向。
tags:
  - MobileCLIP
  - CLIP
  - Zero-shot
---

# MobileCLIP / 零样本场景理解

## 项目/模型链接

- 论文：[MobileCLIP: Fast Image-Text Models through Multi-Modal Reinforced Training](https://arxiv.org/abs/2311.17049)
- 模型仓库：[apple/ml-mobileclip](https://github.com/apple/ml-mobileclip)

## 摘要要点

MobileCLIP 目标是在移动端约束下获得快速图文对齐能力。相比直接使用大型 CLIP，MobileCLIP 更强调低延迟和较小模型。它可以用文本 prompt 做零样本分类，例如让图像和 “urban infrared scene”“forest SAR scene”“sea warship scene” 等文本比较相似度。

## Pipeline

```text
image
  -> lightweight vision encoder
text prompts
  -> text encoder
cosine similarity
  -> scene / condition label
```

## 在本项目中的作用

MobileCLIP 的潜在价值是补足固定场景分类头：

- 当 R1 文件名标签不可用时，用文本 prompt 识别场景。
- 对天气、噪声、可见度做零样本描述。
- 给任务决策模型提供更细粒度上下文。

## 接入状态

未接入。`config.py` 中保留了 `mobileclip_s1` 作为实验选项，但实现和权重尚未完成。

## 输出结果摘录

当前没有本地输出。优先级低于目标检测和数据闭环，适合在主指标稳定后作为主观创新点补充。

