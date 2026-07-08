---
title: 点云清理与背景补全阶段
id: pointcloud-completion
category: 调研目录
summary: 整理点云去噪、背景 clean plate、2D/3D inpainting 和场景结构补全在 Video2Mesh 中的位置。
tags:
  - Research Catalog
  - Completion
  - Point Cloud
  - Inpainting
visibility: public
---

# 点云清理与背景补全阶段

补全不是一个单独按钮。对 Video2Mesh 来说，至少要拆成三件事：点云/高斯清理、背景 clean plate、场景结构补全。

![点云与补全阶段](../assets/stage-completion.svg "物体外观补全、背景 clean plate 和物理代理补全需要拆开处理")

## 主要方向

| 方向 | 简介 | 项目中的作用 | 风险 |
|---|---|---|---|
| 3DGS floater cleaning | 根据 opacity、scale、elongation、空间离群过滤高斯 | 让 3DGS 视觉层更干净，也避免后续点云建面被远端漂浮点拉坏 | 过度清理会删掉真实薄结构 |
| Auto-SuperSplat repair | 模拟人工在 SuperSplat 中框选、删除、补平面洞、换视角 QA 的编辑循环 | 将 3DGS 视觉层修复变成可记录、可回滚、可训练的小模型/规则系统 | 补点只能先限制在平面 patch，不能当真实几何 |
| Point cloud outlier removal | quantile bbox、statistical/radius outlier、voxel downsample | 给 Poisson、Delaunay preview、semantic projection 提供更稳输入 | 参数依赖场景 |
| Background clean plate | 移除前景物体后补全地板/墙面/背景图像，再更新背景 3D 表征 | 当物体可移动时，恢复被遮挡的地面/墙面 | 需要真实 2D masks 和多视角一致性 |
| 2D image/video inpainting | 对视频帧局部缺失区域补图 | clean plate 的前置工具 | 单帧好看不代表多视角一致 |
| Scene layout / plane fitting | floor/wall/ceiling/door/window/cabinet 等结构化估计 | 给 collider、navmesh、support plane 提供稳定结构 | 自动识别门窗柜等细类仍需 VLM/scene graph 增强 |

## 和物体补全的边界

```text
object completion:
  补全被遮挡物体本身

background clean plate:
  补全物体移开后露出的地板/墙面

physics proxy completion:
  补全交互需要的保守碰撞形状
```

这三件事不能混在一起。一个完整椅子 mesh 不能自动恢复椅子背后的地板；一个好看的 inpainted 背景也不能直接提供椅子的碰撞体。

## 新增调研

- [Auto-SuperSplat 式 3DGS 剔除与修补](auto-supersplat-repair.md)：把人工清理漂浮 splat、修补地面/墙面洞和多视角 QA 的经验，转成可执行的自动修复 agent loop。
- [3DGS 漂浮点剔除与剪枝方法](gs-floater-pruning.md)：对比 TIDI-GS、PUP 3D-GS、LightGaussian、Clean-GS 等思路，整理如何做高置信删除、保护真实薄结构和回滚 QA。
- [Gaussian RoI 分割与局部编辑](gaussian-roi-editing.md)：借鉴 Gaussian Grouping、SAGA、LangSplat、GaussianEditor，把 2D mask/点击/语言指令提升为 Gaussian id 级编辑区域。
- [3DGS Inpainting 与背景 Clean Plate](gs-inpainting-clean-plate.md)：梳理 Inpaint360GS、SplatFill、3DGIC 类路线，说明背景洞修补应先做平面 copy-fill，再评估生成式 clean plate。
- [学习式点云去噪与上采样](learning-pointcloud-denoise-upsample.md)：借鉴 PointCleanNet、score-based denoising、PU-Net/PU-GAN，为小模型剔除和局部补点提供几何特征。
