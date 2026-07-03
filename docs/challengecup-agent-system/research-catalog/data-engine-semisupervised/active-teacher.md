---
title: Active Teacher
id: challengecup-active-teacher
category: 调研目录
research_stage: data-engine-semisupervised
visibility: public
summary: Active Teacher 把主动学习和 teacher-student 半监督检测结合，本项目已部分吸收到离线数据 agent 中。
tags:
  - Active Teacher
  - Active Learning
  - Data Agent
---

# Active Teacher

## 项目/论文链接

- 论文：[Active Teacher for Semi-Supervised Object Detection](https://arxiv.org/abs/2303.08348)
- 官方实现：[HunterJ-Lin/ActiveTeacher](https://github.com/HunterJ-Lin/ActiveTeacher)
- 会议：CVPR 2022

## 摘要要点

Active Teacher 从数据初始化角度改造 teacher-student 框架。它不是一次性把所有未标注数据交给 teacher，而是根据样本难度、信息量和多样性逐步扩充标注集合。论文报告用较少标注数据就能接近或达到全监督效果，并给出了实际标注策略的经验。

## Pipeline

```text
small labeled set
  -> evaluate unlabeled samples by difficulty / information / diversity
  -> select useful samples
  -> teacher pseudo-label
  -> student training
  -> iterate selection and training
```

## 在本项目中的作用

本项目中的 “offline data agent” 本质上就是 Active Teacher 思路的工程化变体：

- 按类别、场景、模态统计错例。
- 优先关注 `soldier`、`urban`、`forest`、`SAR`。
- 只让通过 gate 的 hard sample、copy-paste、pseudo-label 或插值权重进入候选。

## 接入状态

部分接入。相关入口：

- `data_tools/r1_active_pseudolabel_agent.py`
- `data_tools/r1_offline_data_agent.py`
- `data_tools/mine_r1_hard_crops.py`
- `evaluation/audit_r1_mistakes.py`

## 输出结果摘录

当前 smoke 流程中，teacher=student 时 active pseudo accepted 为 `0`，这是正确行为：没有更强 teacher 时不应制造伪标签幻觉。scene-hard copy-paste 能构建数据，但直接微调未过 gate；更稳定的收益来自后续权重插值。
