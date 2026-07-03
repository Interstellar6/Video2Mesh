---
title: Weighted Boxes Fusion
id: challengecup-weighted-boxes-fusion
category: 调研目录
research_stage: task-decision-postprocess
visibility: public
summary: WBF 用置信度加权融合多个检测框，本项目已尝试多尺度 WBF，但当前不作为默认提交口径。
tags:
  - WBF
  - Ensemble
  - Postprocess
---

# Weighted Boxes Fusion

## 项目/论文链接

- 论文：[Weighted Boxes Fusion: Ensembling Boxes from Different Object Detection Models](https://arxiv.org/abs/1910.13302)
- GitHub：[ZFTurbo/Weighted-Boxes-Fusion](https://github.com/ZFTurbo/Weighted-Boxes-Fusion)

## 摘要要点

WBF 是一种融合多个检测器预测框的方法。不同于 NMS/Soft-NMS 直接删除重叠框，WBF 会用所有候选框的置信度计算加权平均框。论文在 Open Images 和 COCO 相关挑战中验证了集成检测框的有效性。

## Pipeline

```text
model A boxes + model B boxes + model C boxes
  -> group overlapping boxes
  -> confidence-weighted average coordinates
  -> fused boxes
```

## 在本项目中的作用

WBF 可用于：

- 多输入尺寸预测融合，如 928/960/1024。
- teacher ensemble 生成更稳的候选框。
- 比赛高精离线评估，而不是实时端侧默认。

## 接入状态

已尝试。相关输出位于：

- `agent_system/outputs/r1_multiscale_ensemble/928_960_wbf.json`
- `agent_system/outputs/r1_multiscale_ensemble/928_960_1024_wbf.json`

## 输出结果摘录

当前多尺度 WBF 没有成为默认路线。主要原因是它增加离线/推理复杂度，且在 R1 修正标签主评估上没有稳定超过 `1056 + TTA` 和权重插值候选。保留为 teacher ensemble 和提交前探针。
