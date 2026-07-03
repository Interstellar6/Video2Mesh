---
title: 目标检测环节 Overview
id: challengecup-target-detection-overview
category: 调研目录
research_stage: target-detection
research_doc_role: overview
visibility: public
summary: 目标检测环节负责 R1 四类目标定位，是当前指标上限的主战场。
tags:
  - 目标检测
  - YOLOv8
  - 小目标检测
---

# 目标检测环节 Overview

目标检测环节负责把红外/SAR 图像转成目标类别和边界框，是当前性能指标的核心。R1 数据中 `soldier` 极小，因此这个环节重点关注：

- 轻量 detector 是否能端侧部署。
- 多尺度特征和输入尺寸如何影响小目标。
- 切片/ROI 推理是否能提升 tiny object 召回。
- 候选检测器必须用原始 validation gate 验收。

## 文档

| 文档 | 作用 |
|---|---|
| [Ultralytics YOLOv8](yolov8.md) | 当前主检测器和训练/验证/导出基座 |
| [FPN / Feature Pyramid Networks](fpn.md) | 多尺度小目标检测的经典解释框架 |
| [SAHI / Slicing Aided Hyper Inference](sahi.md) | 小目标切片推理，已尝试但暂不默认 |

