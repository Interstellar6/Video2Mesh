---
title: 输入、位姿与点云阶段
id: input-pose-pointcloud
category: 调研目录
summary: 调研从扫描视频获得相机、稠密点云和统一坐标系的模型与项目，包括 COLMAP、MASt3R/DUSt3R/VGGT 和 MVS。
tags:
  - Research Catalog
  - COLMAP
  - Point Cloud
  - Pose
visibility: public
---

# 输入、位姿与点云阶段

这一阶段负责把原始扫描视频变成后续所有模块共享的坐标系统：相机内外参、稠密点云、尺度约束和可追踪帧。它是 3DGS、mesh、语义回灌和 simulator asset bundle 的地基。

![输入位姿阶段](../assets/stage-input-pose.svg "从扫描视频到 COLMAP/SfM、稠密点云和坐标尺度合同")

## 主要项目和模型

| 项目 / 方法 | 简介 | 输入输出 | 对 Video2Mesh 的作用 | 风险 |
|---|---|---|---|---|
| COLMAP SfM/MVS | 经典摄影测量工具链，估计相机位姿、稀疏点云和稠密 workspace | 输入多帧图片，输出 cameras/images/points3D、dense fused point cloud | 当前最稳的 P0 位姿和 dense geometry 来源，能直接接 GraphDECO 3DGS、Delaunay mesher 和 Poisson baseline | 纹理弱、反光、重复图案时可能失败；需要较好帧覆盖 |
| COLMAP dense stereo | 基于已知相机做 patch-match stereo 和 fusion | 输入 COLMAP sparse model，输出 fused.ply / dense workspace | 场景级 mesh/collider 的主输入，比直接使用 Gaussian center 更可靠 | 稠密点云仍会有空洞、噪声和漂浮点 |
| MASt3R / DUSt3R | 学习式多视图几何，弱纹理/小基线下可作为传统 SfM 的补充 | 输入图像对或多视图，输出对应关系、深度/点云、相机关系 | 可作为 COLMAP 失败时的 pose/depth fallback，或为物体级 depth fusion 提供先验 | 输出坐标尺度和 COLMAP/3DGS 生态不完全一致，需要适配 |
| VGGT 类 feed-forward 模型 | 端到端估计相机、深度、点云等 3D 表征 | 输入图片集合，输出 camera/depth/point map | 可作为快速预处理或弱纹理场景 fallback | 工程稳定性、尺度一致性和大场景鲁棒性需实测 |
| [VGGT-Omega](vggt-omega.md) | 2026 年 VGGT 扩展版，加入 register attention、动态场景能力和 text-alignment checkpoint | 输入图片/视频帧，输出 camera、depth、depth confidence、register features | P1 learned geometry fallback、GraphDECO 初始化候选、动态视频 camera/depth prior | 权重需申请；输出不是标准 COLMAP workspace；scale/camera convention 必须审计 |
| Open3D / CloudCompare 点云处理 | 点云过滤、法线估计、下采样、可视检查 | 输入 PLY/PCD，输出 cleaned point cloud / normals | 用于 mesh 前处理、debug 和人工检查 | 清理规则容易影响真实薄结构 |

## 我们项目中的接入位置

```text
video frames
  -> COLMAP sparse/dense
  -> scene/cameras/camera_info.json
  -> scene/reconstruction/point_cloud.ply
  -> GraphDECO 3DGS / Delaunay mesh / Poisson baseline
```

当前建议：

- P0 仍以 COLMAP 为主，因为它的输出标准、生态成熟，而且和 GraphDECO / COLMAP Delaunay / CloudCompare 都能接起来。
- learned pose/depth 方法适合作为 fallback 或 object-level depth enhancement，不要一开始就替代主链路。
- 所有后续资产必须明确记录坐标系、scale、camera convention，否则 object mesh 和 collider 回填会错位。
