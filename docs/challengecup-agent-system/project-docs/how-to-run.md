---
title: ChallengeCup Agent System 如何运行
id: challengecup-how-to-run
category: 项目使用文档目录
visibility: public
summary: 使用 uv 运行 ChallengeCup agent_system 的完整流程、快速复验、demo 和部署准备。
tags:
  - How to Run
  - uv
  - run.sh
---

# ChallengeCup Agent System 如何运行

## 工作目录

推荐从父目录运行，因为数据集、根流程脚本和 `agent_system` 子项目分属不同层级：

```bash
cd /Users/zhangyuxiang/Desktop/worksplace/ChallengeCup
```

Python 依赖由 `uv` 管理，子项目是 `agent_system`：

```bash
uv sync --project agent_system
```

## 主流程

完整当前流程：

```bash
bash run.sh
```

这条命令会依次执行：

1. 校验修正标签 R1 数据集指纹。
2. 生成 R1 YOLO split。
3. 训练/验证场景分类头。
4. 验证当前最佳 detector。
5. 执行 1056 + TTA 高精评估。
6. 执行严格 `val-iou=0.7432` 候选评估。
7. 运行场景先验、precision policy 和门禁。
8. 审计错例并重新生成 GT/预测可视化。
9. 汇总 `r1_fixed_label_eval_summary.json`。

## 快速复验

只复验关键输出时，可以关闭耗时探针：

```bash
RUN_IMGSZ_SWEEP=0 \
RUN_BOX_CALIBRATION=0 \
RUN_ROI_GRID=0 \
bash run.sh
```

## 单脚本入口

| 任务 | 命令 |
|---|---|
| 数据集预检 | `uv run --project agent_system python tools/verify_r1_dataset.py --source datasets/datasets_r1_base_train` |
| 生成 YOLO split | `uv run --project agent_system python -m agent_system.data_tools.prepare_r1_yolo --source datasets/datasets_r1_base_train --out agent_system/outputs/r1_yolo` |
| 验证 detector | `uv run --project agent_system python -m agent_system.pipelines.train_r1_detector --validate-only --data agent_system/outputs/r1_yolo/r1_base.yaml --weights agent_system/outputs/yolo_r1/interp_cp_a252/weights/best.pt --imgsz 1056 --tta` |
| 错例审计 | `uv run --project agent_system python -m agent_system.evaluation.audit_r1_mistakes --data agent_system/outputs/r1_yolo/r1_base.yaml --weights agent_system/outputs/yolo_r1/interp_cp_a252/weights/best.pt --out-dir agent_system/outputs/r1_mistake_audit_tta1056_scene_prior --imgsz 1056 --tta --scene-prior` |

## Demo

单图 demo：

```bash
uv run --project agent_system python agent_system/demo.py \
  --image datasets/datasets_r1_base_train/ir_r1_base_air_000003.png
```

实时摄像头 demo：

```bash
uv run --project agent_system python agent_system/live_camera.py
```

## Ascend 310B 部署准备

本地 Mac 不能直接完成 Ascend ATC 和真机 benchmark，但项目保留部署入口：

```bash
bash agent_system/deploy_ascend310b.sh
```

部署报告中应明确区分：

- 已完成：YOLOv8n 轻量模型、ONNX 导出入口、ATC 脚本骨架。
- 未完成：Ascend 310B 真机 FPS 和 OM 精度校验。

## 常用环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `DATASET_DIR` | `datasets/datasets_r1_base_train` | R1 数据集路径 |
| `BEST_WEIGHTS` | `agent_system/outputs/yolo_r1/interp_cp_a252/weights/best.pt` | 当前主权重 |
| `DEVICE` | `mps` | 本地设备 |
| `HIGH_PRECISION_IMGSZ` | `1056` | 高精验证输入尺寸 |
| `STRICT_VAL_IOU` | `0.7432` | 严格 mAP50-95 候选 NMS IoU |

