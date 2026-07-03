---
title: 端侧部署环节 Overview
id: challengecup-deployment-overview
category: 调研目录
research_stage: deployment
research_doc_role: overview
visibility: public
summary: 端侧部署环节负责把训练权重导出为 ONNX/OM，并在 Ascend 310B 上补测 FPS 和精度。
tags:
  - 部署
  - Ascend
  - ONNX
---

# 端侧部署环节 Overview

赛题要求 Ascend 310B 嵌入式平台，因此本项目不能只报告 Mac 本地指标。当前策略是先保持轻量模型和导出接口，真机部分后补。

## 文档

| 文档 | 作用 |
|---|---|
| [Ascend CANN / ATC 部署链路](ascend-cann-atc.md) | ONNX -> ATC -> OM -> 310B benchmark 的部署准备 |

