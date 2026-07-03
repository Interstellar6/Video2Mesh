---
title: Simple Copy-Paste
id: challengecup-copy-paste
category: 调研目录
research_stage: data-engine-semisupervised
visibility: public
summary: Copy-Paste 是简单但有效的数据增强思想，本项目已用于 scene-hard 数据构建，但直接微调没有过 gate。
tags:
  - Copy-Paste
  - Data Augmentation
  - Scene Hard
---

# Simple Copy-Paste

## 项目/论文链接

- 论文：[Simple Copy-Paste is a Strong Data Augmentation Method for Instance Segmentation](https://arxiv.org/abs/2012.07177)
- 会议：CVPR 2021

## 摘要要点

论文系统研究了把目标实例随机复制粘贴到其他图像上的增强方式。作者发现，即使不做复杂上下文建模，简单 Copy-Paste 也能在强 baseline 上继续带来收益，并且可与半监督伪标签方法叠加，在 COCO 和 LVIS 上提升实例分割/检测相关指标。

## Pipeline

```text
source object crop / mask
  -> paste into target image
  -> update labels
  -> train detector
  -> validate with unchanged original val set
```

## 在本项目中的作用

R1 的 `soldier` 和 `tank` 在 `urban/forest` 中困难，Copy-Paste 可用于：

- 增强 tiny soldier 的出现频率。
- 构造 scene-hard 训练集。
- 与错例审计结合，优先复制 hard group 的目标。

## 接入状态

已尝试。相关入口：

- `data_tools/build_r1_scene_hard_dataset.py`
- `data_tools/mine_r1_hard_crops.py`
- `run.sh` 中 `RUN_SCENE_HARD_BUILD`

## 输出结果摘录

当前结论比较清楚：scene-hard copy-paste 对 soldier/forest/urban 局部有帮助，但整体 mAP50-95 没有稳定超过 baseline，因此不能直接替换主模型。它更适合作为专家模型来源，再通过 Model Soup/权重插值小比例注入。
