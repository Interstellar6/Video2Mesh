---
title: MASt3R / DUSt3R / VGGT
id: video2mesh-input-pose-pointcloud-mast3r-dust3r-vggt
category: 调研目录
visibility: public
summary: 这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。
tags:
  - 输入、位姿与点云
  - Research Catalog
---

# MASt3R / DUSt3R / VGGT

![输入位姿阶段](../assets/stage-input-pose.svg "MASt3R、DUSt3R、VGGT 更适合作为 COLMAP 失败时的 learned geometry fallback，而不是直接替代 P0 主坐标合同")

## 链接

- MASt3R GitHub: https://github.com/naver/mast3r
- DUSt3R GitHub: https://github.com/naver/dust3r
- DUSt3R paper: https://openaccess.thecvf.com/content/CVPR2024/html/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.html
- VGGT project: https://vgg-t.github.io/
- VGGT GitHub: https://github.com/facebookresearch/vggt
- VGGT paper: https://arxiv.org/abs/2503.11651

## 摘要要点

DUSt3R 的核心是直接从图像对预测 3D point map，让深度、匹配、相机和相对位姿可以从同一个表示中恢复。MASt3R 进一步强化了 3D grounding 和 matching，可服务更稳的图像匹配、SfM 或 SLAM。VGGT 则是 feed-forward 几何模型，试图从单张、少量或大量视图中一次性预测相机参数、深度、点图和 3D point tracks。

这组方法的共同价值是降低 COLMAP 对纹理、匹配和足够重叠视角的依赖；共同风险是输出坐标系、尺度、置信度和工程接口不一定和 COLMAP/GraphDECO 完全对齐。

## Pipeline

| 方法 | Pipeline | 输出 |
|---|---|---|
| DUSt3R | image pair -> transformer point map -> global alignment | point maps、depth、relative/absolute camera 线索 |
| MASt3R | image pair -> 3D grounded matching -> SfM/SLAM helper | dense matches、pose/track 辅助 |
| VGGT | multi-view images -> feed-forward transformer -> geometry attributes | camera、depth、point maps、point tracks |

## 输入与输出

输入：图像对、图像序列或视频抽帧。输出：相对几何、点图、深度、匹配、相机/轨迹估计，必要时再转换到 Video2Mesh 的 `camera_info.json` 和 scene coordinate contract。

## 在 Video2Mesh 中的位置

P1 fallback 和质量增强，不建议当前直接替换 COLMAP 主链路。更合理的接入方式是：

- COLMAP 失败时，用 learned geometry 生成初始 pose/depth，再尝试重建。
- 对少纹理物体做 object-level depth fusion 辅助。
- 给 mesh semantic transfer 增加深度可见性或稠密 correspondence。

## 输出/接入记录

项目当前主线仍使用 COLMAP。此前 MASt3R-SLAM 适合作为候选，但轨迹帧数、尺度和 COLMAP-compatible export 还需要适配，暂未作为正式 P0 路线进入周报结果。

## 接入判断

- P0：暂不替代 COLMAP。
- P1：作为失败 fallback、弱纹理补强和 object-level depth 辅助。
- 风险：必须显式记录 scale、axis convention、confidence，否则 object mesh 和 collider 会错位。
