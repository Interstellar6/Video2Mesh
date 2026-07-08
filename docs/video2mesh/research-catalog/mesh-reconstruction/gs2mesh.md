---
title: GS2Mesh
id: video2mesh-mesh-reconstruction-gs2mesh
category: 调研目录
visibility: public
summary: GS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。
tags:
  - Mesh 重建
  - Research Catalog
---

# GS2Mesh

![GS2Mesh pipeline](https://gs2mesh.github.io/static/images/pipeline.jpeg "GS2Mesh pipeline：场景拍摄与位姿估计 -> 3DGS 和双目 novel view 渲染 -> stereo depth estimation -> depth fusion 到三角网格")

## 链接

- Project page: https://gs2mesh.github.io/
- Code: https://github.com/yanivw12/gs2mesh
- Paper: https://arxiv.org/abs/2404.01810
- Venue: ECCV 2024

## 摘要要点

GS2Mesh 解决的问题是：3DGS 的视觉渲染很好，但 Gaussian 本身是按 photometric loss 优化出来的，直接从 Gaussian center 或属性抽 surface 容易得到噪声面。它的核心做法不是直接连 Gaussian，而是把训练好的 3DGS 当作 novel-view renderer，渲染 stereo-aligned image pairs，再用预训练 stereo matching model 得到深度，最后将多视角深度融合成单个 smooth mesh。

这条路线的亮点是工程上比较模块化：只要有稳定的 3DGS 和相机位姿，就可以把 depth prior 插进来，不需要重新训练一个复杂 SDF。代价是会引入 stereo model、渲染视角选择、TSDF/depth fusion 和 mesh 清理等额外环节。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| scene capture + pose estimation | 用 COLMAP/SfM 得到相机位姿，并训练 3DGS |
| stereo-calibrated novel view rendering | 从 3DGS 渲染匹配的双目视角 |
| stereo depth estimation | 用预训练 stereo model 预测每个视角深度 |
| depth fusion | 将多视角 depth profiles 融合为三角 mesh |

输入：训练后的 3DGS、相机位姿、渲染视角参数。输出：场景级 visual mesh，通常还需要 decimation、component cleanup、double-side/indexed GLB 等后处理，才能放到 Web 或引擎里。

## 在 Video2Mesh 中的位置

适合作为 P1/P2 的 visual mesh benchmark 或 per-object visual mesh 升级路线。它不适合作为 P0 collider 主链路直接替代 COLMAP Delaunay，因为输出 mesh 的体量和局部破碎仍需要清理，且运行依赖比传统 MVS/Poisson 重。

在当前项目实验中，GS2Mesh 的 raw mesh 大约 4.48M vertices / 8.09M triangles，原始文件约 333MB；减面后可以压到几 MB 级 GLB。结构上能保留床、窗帘、大型家具和房间轮廓，但墙面破碎、漂浮片和局部缺失仍明显。

![本项目 GS2Mesh 输出](../../experiments/assets/01-gs2mesh.png "Video2Mesh GS2Mesh 实验输出：保留了床和大结构，但墙面与局部表面仍不稳定")

## 接入判断

- P0：不进入主 collider 链路，避免把视觉 mesh 的噪声带到物理层。
- P1：可以保留为 visual mesh 对照，尤其用于比较 Open3D Poisson、COLMAP Delaunay 和 SuGaR/2DGS 的质量。
- P2：如果后面做 per-object mesh，可尝试对单个物体或局部空间运行，降低场景级噪声和体量。
