---
title: FPN / Feature Pyramid Networks
id: challengecup-fpn
category: 调研目录
research_stage: target-detection
visibility: public
summary: FPN 是多尺度检测的经典结构，解释了为什么小目标检测需要低层空间细节和高层语义融合。
tags:
  - FPN
  - 小目标检测
  - 多尺度
---

# FPN / Feature Pyramid Networks

## 项目/论文链接

- 论文：[Feature Pyramid Networks for Object Detection](https://arxiv.org/abs/1612.03144)
- 会议：CVPR 2017

## 摘要要点

FPN 的核心观点是：卷积网络天然形成从高分辨率低语义到低分辨率高语义的层级结构，可以用自顶向下路径和 lateral connection 低成本构造多尺度特征金字塔。论文在 Faster R-CNN 系统中验证了 FPN 作为通用特征提取器的效果，说明多尺度语义特征对不同尺度目标检测非常关键。

## Pipeline

```text
backbone bottom-up features
  -> top-down semantic pathway
  -> lateral connections
  -> multi-scale feature maps
  -> detector heads at multiple levels
```

## 在本项目中的作用

FPN 没有作为独立模块直接接入当前代码，但它解释了 R1 的核心矛盾：`soldier` 目标太小，单纯低分辨率输入会丢失空间细节。当前项目吸收它的方式是：

- 提升验证输入尺寸到 1056。
- 保留小目标 hard crop 和 ROI refine 实验。
- 选择具备多尺度检测结构的 YOLO 系列作为工程基座。

## 输出结果摘录

输入尺寸扫描显示盲目增大并不总是有效，但从 960 到 1056 的高精模式确实带来 mAP50-95 提升：

| 方案 | mAP50 | mAP50-95 |
|---|---:|---:|
| 960 + TTA | 0.8818 | 0.4425 |
| 1056 + TTA | 0.8885 | 0.4445 |

结论：多尺度思想有效，但 R1 不适合无限放大输入；1088/1152 在严格定位口径上反而退化。
