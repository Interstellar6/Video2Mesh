---
title: COCO 与 R1 数据集分析
id: challengecup-dataset-analysis
category: 赛题分析目录
visibility: public
summary: R1 是比赛核心数据，类别少、场景强相关、小目标比例高；COCO128 只适合工具链 sanity check，不适合和 R1 直接混训。
tags:
  - R1
  - COCO128
  - 数据集分析
---

# COCO 与 R1 数据集分析

## 数据集定位

| 数据集 | 本地路径 | 用途 |
|---|---|---|
| COCO128 | `datasets/coco128` | YOLO 工具链 sanity check、预训练语义参考 |
| R1 base train | `datasets/datasets_r1_base_train` | 比赛主数据、最终训练、验证和增量协议来源 |

COCO128 和 R1 的标签空间不兼容，不能直接混合训练。COCO128 的作用是验证环境和检测链路能跑通；R1 才是所有比赛指标的主数据。

## R1 数据结构

R1 是扁平 YOLO 格式目录：

```text
datasets/datasets_r1_base_train/
  classes.txt
  ir_r1_base_air_000003.png
  ir_r1_base_air_000003.txt
  sar_r1_base_forest_000024.png
  sar_r1_base_forest_000024.txt
```

文件名包含模态、阶段、场景和编号：

- 模态：`ir`、`sar`
- 场景：`air`、`sea`、`urban`、`forest`
- 类别：`soldier`、`small_aircraft`、`warship`、`tank`

当前修正标签版本统计：

| 指标 | 数值 |
|---|---:|
| 图像数 | 750 |
| 标注框数 | 2957 |
| 类别数 | 4 |
| train / val | 599 / 151 |
| 标签 sha256 | `c139f0909fcb1c22b96da1de1df755ad9c9239722a34fc859b154395fd10445c` |

## 关键瓶颈

R1 的目标整体很小，`soldier` 尤其困难。当前逐类 mAP50-95 里，`soldier` 长期明显低于其他类别。

| 类别 | 当前特征 | 工程含义 |
|---|---|---|
| soldier | 极小目标、urban/forest 漏检多 | 需要高分辨率、错例挖掘、hard crop 和更强 teacher |
| small_aircraft | air 场景强相关 | 场景先验较容易发挥作用 |
| warship | sea 场景强相关 | 比较稳定，适合做口径 sanity check |
| tank | 与 soldier 共现，FP 也偏多 | 需要 precision policy 控制展示误检 |

## 为什么场景模型有意义

R1 的类别组合不是随机的：

- `air` 多对应 `small_aircraft`
- `sea` 多对应 `warship`
- `urban/forest` 多对应 `soldier + tank`

因此场景认知不是装饰，它可以用来：

- 删除明显不合场景的预测。
- 给 demo 输出选择更稳的 precision policy。
- 作为离线数据 agent 的分组维度，定位薄弱场景和模态。

## 当前数据预检

根目录 `run.sh` 已在完整流程开始阶段调用：

```bash
uv run --project agent_system python tools/verify_r1_dataset.py \
  --source datasets/datasets_r1_base_train
```

如果标签 hash 或目录指向旧版本，流程会在训练/验证前停止。这条预检是后续复现实验的第一道门禁。

