---
title: 3DGS 漂浮点剔除与剪枝方法
id: video2mesh-pointcloud-completion-gs-floater-pruning
category: 调研目录
visibility: public
summary: 对比 TIDI-GS、Clean-GS、PUP 3D-GS、LightGaussian 等剪枝/抑制路线，整理它们如何帮助 Video2Mesh 自动删除光斑、空中飞点和低贡献 Gaussian。
tags:
  - 点云清理与背景补全
  - Research Catalog
  - 3DGS
  - Floater Pruning
---

# 3DGS 漂浮点剔除与剪枝方法

![3DGS 漂浮点剔除流程](../assets/gs-floater-pruning.svg "从多视角诊断、Gaussian 属性和局部几何出发，生成可回滚的删除/降权编辑")

## 链接

- TIDI-GS: Floater Suppression in 3D Gaussian Splatting for Enhanced Indoor Scene Fidelity: https://arxiv.org/abs/2601.09291
- Clean-GS: Semantic Mask-Guided Pruning for 3D Gaussian Splatting: https://arxiv.org/abs/2601.00913
- PUP 3D-GS: pruning utility preserving 3D Gaussian Splatting: https://arxiv.org/abs/2406.10219
- LightGaussian: Unbounded 3D Gaussian Compression: https://arxiv.org/abs/2311.17245
- GraphDECO 3DGS: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/
- SuperSplat: https://playcanvas.com/products/supersplat

## 摘要要点

3DGS 的光斑、空中飞点和边缘毛刺，很多时候来自 densification 的歧义：优化器为了降低训练视图 photometric error，会在薄结构、遮挡边界或视角稀疏区域放出一些视觉上“能解释一两张图”的 Gaussian。这些 Gaussian 在训练视角可能贡献不大，但在新视角会变成悬浮碎片、拉丝或透明光斑。

TIDI-GS 代表训练中抑制思路：把 densification 的候选点放到更稳定的跨视角和空间关系约束下，减少无组织的 floaters。PUP 3D-GS、LightGaussian 更像后验压缩/剪枝思路：评估 Gaussian 的贡献、敏感度或全局重要性，删掉低贡献 Gaussian 后再 fine-tune。Clean-GS 类思路则强调语义 mask、可见性和局部邻域过滤，避免只靠一个 opacity 阈值误删真实薄结构。

对 Video2Mesh 来说，这类方法最值得借鉴的是“多信号投票”而不是某一个具体阈值：Gaussian 属性、kNN 局部几何、训练视图贡献、语义保护区、多视角 QA 必须一起决定是否删除。

## Pipeline

| 阶段 | 方法启发 | Video2Mesh 可落地做法 |
|---|---|---|
| 诊断渲染 | 训练视角和 novel view 中检查 floaters 是否稳定存在 | 渲染 RGB / alpha / depth / contribution map，保留 before/after 对比 |
| 候选生成 | 低 opacity、异常 scale、anisotropy、远离表面的小连通分量 | 扩展 `clean-3dgs-floaters` 的统计字段，输出 candidate sidecar |
| 重要性估计 | PUP / LightGaussian 关注删点后对重建质量的影响 | 用 train-view photometric contribution 和 visibility count 做二级过滤 |
| 语义保护 | Clean-GS 类路线避免删掉真实物体边界 | floor/wall/ceiling、物体 bbox、线缆/椅腿/窗帘边缘进入保护或 uncertain |
| 执行与回滚 | pruning 后通常需要 fine-tune 或 QA | 先 delete/attenuate 高置信点；所有操作写 `deleted_gaussians.json` |

## 输入与输出

| 类型 | 内容 |
|---|---|
| 输入 | Gaussian PLY、camera poses、可选 depth/semantic/background masks、多视角渲染图 |
| 输出 | cleaned PLY、deleted/attenuated Gaussian id 集合、每个候选的 feature/score/reason、QA renders |

## 在 Video2Mesh 中的位置

它应当是 P0/P1 的视觉层修复工具，位于 3DGS 训练后、mesh/semantic transfer/viewer export 之前：

```text
raw 3DGS
  -> floater candidate extraction
  -> protected pruning / opacity attenuation
  -> multiview QA
  -> cleaned visual splat
  -> mesh benchmark / viewer / semantic projection
```

这一步不能替代 mesh/collider。它只让 visual proxy 更干净，减少后续截图、点云建面和 SuperSplat 查看里的明显伪影。

## 接入判断

- P0：进入。先把规则版 cleaner 的报告做完整，输出每个被删 Gaussian 的原因和可视化。
- P1：引入 LightGBM / XGBoost 小模型，学习人工 SuperSplat 编辑日志里的 keep/delete 偏好。
- P2：考虑训练中 hook，接近 TIDI-GS 思路，在 densification 阶段抑制未来会变成 floaters 的候选。

## 风险

- 重要性剪枝不等于伪影检测。低贡献 Gaussian 可能是真实薄结构，高贡献 Gaussian 也可能是坏光斑。
- 只看单视角会误删遮挡边界，需要多视角一致性和保护区。
- 删除后可能暴露新的空洞，所以每轮必须有 no-new-hole gate。
