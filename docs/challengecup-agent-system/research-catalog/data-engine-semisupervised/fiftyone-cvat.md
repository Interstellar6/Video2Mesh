---
title: FiftyOne / CVAT 错例闭环
id: challengecup-fiftyone-cvat
category: 调研目录
research_stage: data-engine-semisupervised
visibility: public
summary: FiftyOne 和 CVAT 代表工程化错例发现、复核和回流标注流程，本项目用本地脚本实现了轻量替代。
tags:
  - FiftyOne
  - CVAT
  - 错例闭环
---

# FiftyOne / CVAT 错例闭环

## 项目/文档链接

- FiftyOne detection mistakes tutorial：[Detection Mistakes](https://docs.voxel51.com/tutorials/detection_mistakes.html)
- CVAT automatic annotation：[CVAT Automatic Annotation](https://docs.cvat.ai/docs/manual/advanced/automatic-annotation/)

## 摘要要点

FiftyOne 这类数据平台强调从模型输出中发现误检、漏检、难例和数据异常；CVAT 则提供人工标注和自动标注辅助。它们代表的是生产级数据闭环：不是只训练一次模型，而是不断发现错误、复核、回流、重训和验收。

## Pipeline

```text
model predictions + ground truth
  -> mistake mining
  -> visual review
  -> annotation / correction
  -> retrain or pseudo-label
  -> validation gate
```

## 在本项目中的作用

本项目没有直接部署 FiftyOne/CVAT 服务，而是用轻量脚本实现核心闭环：

- `audit_r1_mistakes.py`：挖掘 TP/FP/FN 和保存错例图。
- `build_r1_scene_hard_dataset.py`：根据错例和场景构建 hard 数据集。
- `verify_r1_dataset.py`：防止数据集版本漂移。
- `gate_r1_*`：所有候选必须过门禁。

## 输出结果摘录

当前 `1056 + TTA + scene-prior` 错例审计结论：

| 分组 | TP | FP | FN | 说明 |
|---|---:|---:|---:|---|
| all | 538 | 135 | 60 | 召回提高，但展示 FP 偏多 |
| soldier | 82 | 53 | 43 | 主要漏检类，也是 FP 大户 |
| tank | 176 | 54 | 11 | 主要问题是 FP |
| `soldier|urban` | 44 | 28 | 31 | 当前最困难组合 |

precision policy 后，FP 可从 135 降到 41，但 TP 也会从 538 降到 530，适合演示/应用端精度优先，不适合直接代表 mAP 提交口径。
