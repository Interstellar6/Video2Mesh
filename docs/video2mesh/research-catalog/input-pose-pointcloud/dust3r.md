---
title: DUSt3R
id: video2mesh-input-pose-pointcloud-dust3r
category: 调研目录
research_stage: input-pose-pointcloud
visibility: public
summary: DUSt3R 直接从图像对预测 3D point maps，把深度、匹配和相机关系统一到同一个 learned geometry 表示里，适合作为 COLMAP 失败时的 point cloud / pose prior。
tags:
  - 输入、位姿与点云
  - DUSt3R
  - Point Map
  - Pose
  - Research Catalog
---

# DUSt3R

![输入位姿阶段](../assets/stage-input-pose.svg "DUSt3R 用 learned point map 为弱纹理输入提供相机、深度和点云先验")

## 链接

- GitHub: https://github.com/naver/dust3r
- Paper: https://openaccess.thecvf.com/content/CVPR2024/html/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.html
- 3D matching 扩展：[MASt3R](mast3r.md)
- 同阶段 feed-forward 几何模型：[VGGT](vggt.md)

## 一句话结论

DUSt3R 的核心是从图像对直接预测 3D point maps，让两张图之间的深度、对应关系、相机关系和点云几何可以从同一个 learned representation 里恢复。对 Video2Mesh 来说，它适合作为 COLMAP 的 **失败补救和几何先验**，尤其在传统 feature matching 不稳时，用它给后续相机估计、点云融合或局部 mesh 修复提供输入。

## 摘要要点

传统 SfM/MVS 往往先做特征提取和匹配，再做几何优化、三角化、bundle adjustment 和 dense stereo。DUSt3R 换了一个入口：它把图像对送入 transformer，直接预测每个像素对应的 3D point map。这个表示让深度、匹配和相机关系能够从点图中统一恢复。

它对 Video2Mesh 的意义是：当 COLMAP 因低纹理、少视角、反光、重复图案或小基线而注册失败时，DUSt3R 可以先给出一份 learned geometry prior，再由项目自己的 QA 和转换层决定是否接回主 pipeline。

边界也要明确：DUSt3R 输出的是点图/几何先验，不是经过 photometric optimization 的 3DGS，也不是可直接用于碰撞、导航或物理仿真的 watertight mesh。

## Pipeline

```text
image pair / selected multi-view pairs
  -> DUSt3R transformer
  -> 3D point maps + confidence
  -> pairwise geometry / camera relation recovery
  -> optional global alignment across selected frames
  -> Video2Mesh geometry prior + point cloud candidate
  -> QA, scale audit, fusion, meshing or GraphDECO initialization
```

| 阶段 | 作用 | 输出 |
|---|---|---|
| Pair inference | 对图像对预测 3D point maps | per-pixel point maps、confidence |
| Geometry recovery | 从点图恢复相对相机关系和对应点 | pose prior、dense correspondences |
| Global alignment | 多 pair 合成一个统一几何空间 | aligned point cloud / camera graph |
| Project conversion | 转成 Video2Mesh 的中间合同 | `geometry_prior.json`、候选 PLY、相机先验 |

## 输入与输出

输入：抽帧图像、图像对或经过 keyframe selection 的多视图集合。为了避免 N^2 pair 数量失控，实际接入时应优先使用相邻帧、关键帧和覆盖变化明显的 pair。

输出建议拆成三类保存：

| 输出 | 目的 |
|---|---|
| raw point maps | 保留模型原始几何输出，便于复查和重导出 |
| fused / aligned candidate point cloud | 用于 Open3D、CloudCompare、TSDF 或 Poisson 试验 |
| camera / scale audit report | 判断是否能接回 GraphDECO 或 dense mesh |

## 几何生成路径

DUSt3R 点云不是从 COLMAP sparse tracks 三角化出来的，而是模型从图像内容直接预测点图。接入 Video2Mesh 时要特别审计：

- 点图坐标是否已经全局对齐，还是仍是 pair/local 坐标。
- 不同 pair 之间是否有尺度漂移。
- 深度边界、遮挡、反光区域是否出现薄片或重影。
- 与 COLMAP 成功帧的相机/点云是否能粗配准。
- confidence 是否能用于过滤漂浮点，而不是只凭肉眼看截图。

## 在 Video2Mesh 中的位置

```text
video frames
  -> COLMAP SfM/MVS
  -> if failed or weak:
       DUSt3R point maps
       -> global alignment / fusion
       -> point cloud + camera prior
  -> GraphDECO / mesh reconstruction / semantic fusion
```

DUSt3R 更适合作为 P1 几何 prior，而不是 P0 主链路。当前主链路仍应该由 COLMAP 提供标准 sparse/dense workspace，因为 GraphDECO、Delaunay mesher、semantic transfer 和 simulator asset bundle 都已经围绕这个合同组织。

## 接入判断

| 用途 | 判断 |
|---|---|
| COLMAP fallback | 值得接入，尤其适合弱纹理或少视角片段 |
| Dense point cloud seed | 可做候选，但必须先做 confidence filtering、体素下采样和尺度审计 |
| Mesh reconstruction | 可作为 TSDF / Poisson / Delaunay 的候选输入，不应直接当最终 collider |
| 3DGS initialization | 可尝试转成 COLMAP-like cameras + points 后做短训 |
| Semantic / physics | 不能直接承担，仍需 sidecar、mesh/collider 和物理属性层 |

## 风险

- pairwise learned geometry 可能在全局合并时出现尺度和姿态漂移。
- 高密度 point map 看起来连续，但遮挡边界和薄结构可能不适合直接 meshing。
- 如果没有相机 convention 和 scale 记录，后续 object mesh、semantic transfer 和 collider 都可能错位。
- DUSt3R 与 MASt3R / VGGT 的边界要分清：它提供 point-map 几何基础；MASt3R 更偏 matching；VGGT 更偏多视图 feed-forward camera/depth/point tracks。
