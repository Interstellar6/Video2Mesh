---
title: Grounding DINO
id: challengecup-grounding-dino
category: 调研目录
research_stage: data-engine-semisupervised
visibility: public
summary: Grounding DINO 是开放词汇检测器，可按文本提示发现候选目标，适合做 R1 漏标/漏检候选挖掘而不是端侧实时模型。
tags:
  - Grounding DINO
  - Open Vocabulary
  - Pseudo Label
---

# Grounding DINO

## 项目/论文链接

- 论文：[Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection](https://arxiv.org/abs/2303.05499)
- 官方实现：[IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO)
- 会议：ECCV 2024

## 摘要要点

Grounding DINO 把 DINO 检测器和 grounded pre-training 结合，引入语言作为开放词汇检测入口。用户可以输入类别名或指代表达，模型用视觉-语言融合机制检测任意文本描述的目标。论文在 COCO、LVIS、ODinW 和 referring expression benchmarks 上展示了强零样本能力。

## Pipeline

```text
image + text prompt
  -> visual features + language features
  -> language-guided query selection
  -> cross-modality decoder
  -> open-set boxes
```

## 在本项目中的作用

Grounding DINO 不适合作为 Ascend 310B 端侧实时检测器，但很适合做离线候选挖掘：

- 用 `soldier`, `tank`, `warship`, `small aircraft` 文本提示找疑似漏检。
- 与 YOLO teacher/student 做一致性过滤。
- 给人工复核和 pseudo-label pipeline 提供候选框。

## 接入状态

尚未接入。当前计划是把它放到 P1/P2 数据闭环，而不是主检测链路。

## 输出结果摘录

本项目目前没有 Grounding DINO 本地输出。已有相关结论是：弱 YOLO teacher 不足以启用伪标签，所以开放词汇 teacher 是下一步提高候选召回的合理方向。
