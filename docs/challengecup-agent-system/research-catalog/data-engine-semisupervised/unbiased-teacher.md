---
title: Unbiased Teacher
id: challengecup-unbiased-teacher
category: 调研目录
research_stage: data-engine-semisupervised
visibility: public
summary: Unbiased Teacher 关注半监督检测中的伪标签偏置问题，本项目借鉴其 teacher-student 和 pseudo-label gate 思路。
tags:
  - Unbiased Teacher
  - Semi-supervised Detection
  - Teacher Student
---

# Unbiased Teacher

## 项目/论文链接

- 论文：[Unbiased Teacher for Semi-Supervised Object Detection](https://arxiv.org/abs/2102.09480)
- 官方实现：[facebookresearch/unbiased-teacher](https://github.com/facebookresearch/unbiased-teacher)
- 会议：ICLR 2021

## 摘要要点

Unbiased Teacher 研究半监督目标检测中的伪标签偏置问题：teacher 容易对某些类别或高置信预测过度自信，导致 student 学到偏置。方法通过 teacher-student 互相推进，并使用 class-balance loss 降低过度自信伪标签影响，在 COCO/VOC 低标注比例下显著提升检测效果。

## Pipeline

```text
labeled images + unlabeled images
  -> teacher generates pseudo boxes
  -> class-balance / bias control
  -> student learns supervised + pseudo-label losses
  -> EMA / progressive teacher update
```

## 在本项目中的作用

R1 数据只有 750 张，且 `soldier` 是极小目标。Unbiased Teacher 的价值不在于直接照搬框架，而在于提醒我们：

- teacher 不能无门禁地生成伪标签。
- 伪标签要按类别、场景、模态审计。
- 强 teacher 必须在减少漏检的同时避免引入大量 FP。

## 接入状态

思路已接入。相关入口：

- `data_tools/r1_teacher_pseudolabel.py`
- `data_tools/r1_active_pseudolabel_agent.py`
- `evaluation/gate_r1_teacher_candidate.py`
- `evaluation/evaluate_r1_teacher_student.py`

## 输出结果摘录

本地 `teacher_highres_s1280_e24` 没有成为可用伪标签 teacher：

- 相对 `train960` 有小幅 detector gate 收益。
- 但 teacher gap 为负，teacher gate 拒绝。
- 因此伪标签继续禁用，避免把错误框写回训练集。

结论：teacher 路线保留，但必须等更强 teacher 或开放词汇候选复核后再启用。
