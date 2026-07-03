---
title: ChallengeCup 赛题分析
id: challengecup-contest-analysis
category: 赛题分析目录
visibility: public
summary: 赛题要求构建可运行在 Ascend 310B 端侧的多模态模型协同自主智能体系统，核心是场景理解、任务决策、目标检测和增量学习闭环。
tags:
  - ChallengeCup
  - Ascend 310B
  - 增量学习
---

# ChallengeCup 赛题分析

## 赛题定位

赛题要求构建一套面向动态探测场景的多模态模型协同自主智能体系统，目标平台是华为昇腾 310B 嵌入式计算环境。输入包括红外、雷达/SAR 等多模态数据，系统需要完成：

```text
场景理解 -> 任务策略决策 -> 目标检测识别 -> 小样本增量学习 -> 端侧部署
```

因此项目不能只提交一个检测权重。比较合理的作品形态是：

- 场景认知模型：识别场景类型、可见度、噪声、地形和模态条件。
- 任务决策模型：根据场景输出置信度阈值、NMS 阈值、后处理策略和是否启用高精评估。
- 目标检测模型：完成 `soldier`、`small_aircraft`、`warship`、`tank` 的检测。
- 增量学习模块：模拟小样本新类注入和旧类知识保持。
- 部署模块：导出 ONNX，并保留 Ascend ATC / OM 转换入口。

## 当前实现对应关系

| 赛题要求 | 当前代码/文档入口 | 状态 |
|---|---|---|
| 场景认知 | `agent_system/models/scene_cognition.py`、`pipelines/train_r1_scene_classifier.py` | 已有轻量场景头和训练入口 |
| 任务决策 | `agent_system/models/task_decision.py`、`evaluation/evaluate_r1_scene_prior.py` | 已接场景先验和 precision policy |
| 目标检测 | `models/target_detection.py`、`pipelines/train_r1_detector.py` | 当前主力为 YOLOv8n 960/1056 评估路线 |
| 增量学习 | `pipelines/run_r1_incremental_protocol.py`、`run_r1_multiround_incremental.py` | 已有单轮/多轮协议，当前不是主冲分路径 |
| 端侧部署 | `deploy_ascend310b.sh`、`outputs/deploy/*.onnx` | 本地保留接口，真机 FPS 需要后续补测 |

## 评分指标拆解

| 指标 | 分值 | 当前策略 |
|---|---:|---|
| 基础目标检测 mAP | 30 | 优先报告 mAP50，同时保留 mAP50-95 严格口径 |
| 增量 New-mAP | 10 | 用 R1 类别模拟新类注入，输出可复评 split 和 summary |
| 增量 KRR | 10 | 通过 replay buffer 保持旧类，避免单轮 fine-tune 忘掉基础类 |
| 端侧 FPS | 10 | 保持 YOLOv8n + ONNX + Ascend 转换脚本，真机补测 |
| 主观设计 | 40 | 三模型协同、离线数据 agent、错例闭环、部署脚本和可解释报告 |

## 当前判断

赛题最强路线不是换一个更大的 detector，而是在端侧约束下形成可复评、可解释、可部署的闭环。当前有效工作集中在：

- 用 YOLOv8n 作为端侧主模型。
- 用高分辨率、TTA、NMS sweep 和权重插值提高验证结果。
- 用场景 agent 和错例审计定位 `soldier`、`urban`、`forest`、`SAR` 等薄弱区域。
- 把 teacher、Grounding DINO、Copy-Paste、WBF 等外部技术放在离线数据闭环中，而不是直接放到端侧实时路径里。

