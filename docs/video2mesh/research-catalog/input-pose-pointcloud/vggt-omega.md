---
title: VGGT-Omega
id: video2mesh-input-pose-pointcloud-vggt-omega
category: 调研目录
research_stage: input-pose-pointcloud
visibility: public
summary: VGGT-Omega 是 VGGT 的 2026 扩展版，面向静态和动态场景的 feed-forward 3D reconstruction，可输出相机、深度、点云和 register features。
tags:
  - 输入、位姿与点云
  - VGGT-Omega
  - Feed-forward 3D Reconstruction
  - Dynamic Reconstruction
  - Research Catalog
---

# VGGT-Omega

![VGGT-Omega 接入位置](../assets/vggt-omega-pipeline.svg "VGGT-Omega 更适合作为 Video2Mesh 的 camera/depth/point cloud prior，而不是直接生成 mesh 或 collider")

## 链接

- Project page: https://vggt-omega.github.io/
- arXiv: https://arxiv.org/abs/2605.15195
- GitHub: https://github.com/facebookresearch/vggt-omega
- Hugging Face model: https://huggingface.co/facebook/VGGT-Omega
- Hugging Face demo: https://huggingface.co/spaces/facebook/vggt-omega
- 原 VGGT project: https://vgg-t.github.io/

## 基本信息

| 项 | 内容 |
|---|---|
| 论文标题 | VGGT-Omega / VGGT-Ω |
| 日期与 venue | arXiv 2026-05-14；官方项目页标注 CVPR 2026 Best Paper Finalist，arXiv comments 标注 CVPR 2026 Oral |
| 作者 | Jianyuan Wang, Minghao Chen, Shangzhan Zhang, Nikita Karaev, Johannes Schoenberger, Patrick Labatut, Piotr Bojanowski, David Novotny, Andrea Vedaldi, Christian Rupprecht |
| 机构 | Visual Geometry Group, University of Oxford；Meta AI |
| 模型 | `VGGT-Omega-1B-512`、`VGGT-Omega-1B-256-Text-Alignment` |
| 权重状态 | Hugging Face 权重需要申请访问；官方 demo 对所有人开放 |

## 一句话结论

VGGT-Omega 是 VGGT 的大规模扩展版，重点不是输出 3DGS 或 mesh，而是更高效地从多帧图像/视频中恢复 camera、depth、point map / point cloud 和可用于空间理解的 register features。它适合放在 Video2Mesh 的 **输入、位姿与点云阶段**：作为 COLMAP 失败时的 fallback、GraphDECO 初始化 prior、动态视频的 camera/depth 估计和后续语义/语言对齐特征来源。

## 摘要要点

官方摘要把 VGGT-Omega 定位为 scaled-up feed-forward 3D reconstruction model，覆盖静态和动态场景。相比原 VGGT，它做了几处关键变化：

- 用单个 dense prediction head 做多任务监督，减少多个任务头的复杂度。
- 移除昂贵的 high-resolution convolutional layers。
- 使用 registers 聚合全局场景信息，并通过 register attention 限制帧间信息交换，部分替代全局 attention。
- 训练阶段 GPU memory 约为前代的 30%，因此能使用 15x 更多 supervised data，并利用大量 unlabeled video data。
- 官方摘要称其在 Sintel camera estimation 上比此前最好结果提升 77%，并展示 learned registers 对 VLA model 和 language alignment 的价值。

这意味着 VGGT-Omega 不只是“更准的 VGGT”。它把重建任务当作空间理解的 scalable proxy task：相机和深度是紧凑的几何目标，registers 则可能成为后续机器人、语言对齐、场景理解的共享 latent。

## Pipeline

| 阶段 | 作用 | 输出 |
|---|---|---|
| Image/video preprocessing | 将图片集合或视频抽帧 resize/normalize，官方 quick start 使用 `image_resolution=512` | tensor images |
| VGGT-Omega forward | 1B 模型对多帧做 feed-forward geometry inference | `pose_enc`、`depth`、`depth_conf`、`camera_and_register_tokens` |
| Camera decoding | 用 `encoding_to_camera` 将 `pose_enc` 转成外参和内参 | extrinsics、intrinsics |
| Depth unprojection | 使用相机和深度把像素反投影成 3D 点 | point cloud / point map |
| Register features | 从 `camera_and_register_tokens` 中分离 camera tokens 和 scene registers | scene-level geometry/spatial features |
| Optional text alignment | 256 text-aligned checkpoint 输出 `text_alignment_embedding` | 可与语言/语义任务对齐的 embedding |

## 几何生成路径

VGGT-Omega 的几何路径是 learned feed-forward，而不是 COLMAP 的 SfM/MVS：

```text
image sequence
  -> VGGT-Omega transformer + registers
  -> pose encoding + depth + confidence
  -> camera intrinsics/extrinsics
  -> depth-unprojected point cloud
  -> optional GLB visualization or COLMAP-like prior
```

如果要接入 Video2Mesh，必须把输出转成我们自己的坐标合同：

- `camera_info.json`：保存 frame id、intrinsics、extrinsics、camera convention、source resolution、confidence。
- `point_cloud.ply` 或 intermediate point maps：由 depth + camera 反投影生成，带深度置信度或 mask。
- `geometry_prior.json`：记录模型版本、checkpoint、输入帧、resize 策略、scale normalization、是否 text-aligned。
- `quality_report.json`：检查重投影误差、深度空洞、漂浮点、尺度漂移和与 COLMAP 的姿态差异。

## Mesh / 3DGS 接入方式

VGGT-Omega 不直接输出 triangle mesh，也不直接输出 Gaussian PLY。后接路线应分清：

| 后接模块 | 可用方式 | 不应做的事 |
|---|---|---|
| GraphDECO 3DGS | 用 predicted cameras + point cloud 作为 COLMAP-like 初始化，做短训或 fallback | 直接把 VGGT-Omega 输出当作已经优化过的 3DGS visual layer |
| Mesh reconstruction | 把 depth/point cloud 融合后做 TSDF、Poisson、Delaunay 或 Marching Cubes | 直接把单帧 depth 点云当最终 collider |
| Semantic sidecar | text-aligned registers 可作为未来语义/语言对齐线索 | 把 register embedding 直接当 object ID 或物理属性 |
| Dynamic scene | 用动态场景 camera/depth 估计作为 D4RT 类 4D tracks 的辅助 | 把动态物体强行融合进静态 mesh |

## 工程和部署要求

官方 README 给出的直接依赖很轻：`torch>=2.3`、`torchvision>=0.18`、`numpy<2`、`Pillow`、`einops`、`safetensors`、`opencv-python`。demo 另有 `requirements_demo.txt`。

官方 quick start 的核心输出如下：

```python
predictions = model(images)
extrinsics, intrinsics = encoding_to_camera(
    predictions["pose_enc"],
    predictions["images"].shape[-2:],
)
depth = predictions["depth"]
depth_conf = predictions["depth_conf"]
camera_and_register_tokens = predictions["camera_and_register_tokens"]
```

官方 A100 推理显存表：

| 输入帧数 | 1 | 10 | 25 | 50 | 100 | 200 | 300 | 400 | 500 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Peak memory GB | 6.02 | 6.67 | 7.80 | 9.66 | 13.37 | 20.82 | 28.26 | 35.71 | 43.15 |

该表使用 `VGGT-Omega-1B-512`、单张 A100、624x416 输入，并覆盖从加载权重到 forward pass 的端到端 peak memory。对 Video2Mesh 的 bedroom 级视频来说，RTX 3090/4090 理论上能跑几十到上百帧级别的测试，但真实吞吐、CUDA memory fragmentation、长视频分块和输出转换都要等本地/远端实测。

## Video2Mesh bedroom_4 实测：点云和 mesh 重建

这轮实测使用 `bedroom_4` clean31 片段，在远端 `mil8` 上跑通 VGGT-Omega 推理，并把输出的 depth、intrinsics、extrinsics 转成点云和 mesh。VGGT-Omega 官方代码里的 extrinsics 是 **camera-from-world OpenCV 坐标**，因此反投影时使用：

```text
X_cam = K^-1 [u, v, 1]^T * depth
X_world = R.T @ (X_cam - t)
```

本次 VGGT-Omega 输出形状为：`extrinsics [1,31,3,4]`、`intrinsics [1,31,3,3]`、`depth [1,31,384,688,1]`、`depth_conf [1,31,384,688]`。这些是真实推理结果，不是手工伪造相机或合成位姿。

### 主要产物

本地产物目录：`tmp_remote_results/vggt_omega_bedroom_4_clean31_omega512_pointcloud_mesh_20260711_054752/`

远端源目录：`/data/zyx/workspace/vggt_omega_runs/bedroom_4_clean31_omega512_full31_20260711_050958/`

| 产物 | 文件 | 生成方法 | 规模 | 观察结论 |
|---|---|---|---:|---|
| 原始 RGB 点云 | `pointcloud_mesh_from_depth_light_20260711_054752/vggt_omega_depth_unproject_rgb_points.ply` | depth + camera 反投影，confidence 过滤，robust bbox 裁剪，导出 120 万点 | 1,200,000 points / 18.0 MB | 图五。渲染和重建质量最高，床、窗、墙、地板、床头柜等主体最完整，细节保留也最好。 |
| voxel clean 点云 | `mesh_from_vggt_pointcloud_open3d_20260711_055739/vggt_omega_depth_pointcloud_voxel0012_clean.ply` | 120 万点 PLY 经 Open3D voxel downsample + statistical outlier removal | 38,104 points / 1.9 MB | 图二。结构仍清楚，但为了后续 BPA/Poisson 重建做了明显下采样，视觉细节低于原始 120 万点。 |
| depth-grid mesh | `mesh_from_vggt_depth_grid_20260711_055635/vggt_omega_depth_grid_mesh_stride4.ply` | 每帧 depth 图按 stride=4 反投影，相邻有效像素连三角形 | 297,885 vertices / 539,272 faces / 11.5 MB | 图一。保留每帧局部表面，房间大结构完整，但多视角重叠和深度边缘会形成薄片、接缝和洞。 |
| BPA mesh | `mesh_from_vggt_pointcloud_open3d_20260711_055739/vggt_omega_pointcloud_bpa_mesh_voxel0012.ply` | voxel clean 点云估计法线后 Ball Pivoting，radii=[0.018,0.03,0.048] | 38,104 vertices / 49,668 faces / 2.6 MB | 图三。局部表面更连续，形状比 depth-grid 更规整，但仍有孔洞和少量三角碎片。 |
| Poisson mesh | `mesh_from_vggt_pointcloud_open3d_20260711_055739/vggt_omega_pointcloud_poisson_depth7_trim08_mesh.ply` | voxel clean 点云估计法线后 Poisson depth=7，并按 density 去掉最低 8% 顶点 | 26,747 vertices / 52,594 faces / 2.0 MB | 图四。mesh 版本里空洞最少、表面最干净，适合作为这轮 mesh baseline；但它比原始点云更平滑，局部细节被抹掉。 |

![VGGT-Omega depth-grid mesh](../assets/vggt-omega-bedroom4-depth-mesh/depth-grid-mesh-stride4.jpg "图一：vggt_omega_depth_grid_mesh_stride4.ply。保留局部 depth surface，但多视角薄片和接缝更多。")

![VGGT-Omega voxel clean point cloud](../assets/vggt-omega-bedroom4-depth-mesh/voxel-pointcloud-clean.jpg "图二：vggt_omega_depth_pointcloud_voxel0012_clean.ply。下采样点云适合 Open3D meshing，但视觉细节少于 120 万点原始点云。")

![VGGT-Omega BPA mesh](../assets/vggt-omega-bedroom4-depth-mesh/bpa-mesh-voxel0012.jpg "图三：vggt_omega_pointcloud_bpa_mesh_voxel0012.ply。BPA 保留可见局部表面，但仍有孔洞和三角碎片。")

![VGGT-Omega Poisson mesh](../assets/vggt-omega-bedroom4-depth-mesh/poisson-depth7-trim08-mesh.jpg "图四：vggt_omega_pointcloud_poisson_depth7_trim08_mesh.ply。mesh 版本里空洞最少、最干净。")

![VGGT-Omega depth-unproject point cloud](../assets/vggt-omega-bedroom4-depth-mesh/depth-unproject-rgb-points.jpg "图五：vggt_omega_depth_unproject_rgb_points.ply。120 万点 RGB 点云的渲染和整体重建质量最高。")

### 效果判断

这次结果比预期干净：VGGT-Omega 的 camera/depth 合同在 `bedroom_4` clean31 上足以恢复卧室主体结构，床、床头板、床品褶皱、窗框、两侧墙面、地板和床头柜都能被点云或 mesh 表达出来。图五的 `vggt_omega_depth_unproject_rgb_points.ply` 是这一轮**渲染和整体重建质量最高**的产物，因为它保留了 120 万点原始几何和颜色；如果目标是展示、人工 QA 或给后续几何融合提供高密度输入，应优先看它。

在 mesh 产物里，图四的 `vggt_omega_pointcloud_poisson_depth7_trim08_mesh.ply` 主观效果最好：空洞最少，表面最干净，床、墙和窗的连续性优于 depth-grid 和 BPA。但 Poisson 的平滑和补洞也意味着它会把部分细节平均掉，并可能在遮挡/缺数据处生成并非真实观测的封闭表面。因此它可以作为 **mesh baseline / visual proxy**，还不能直接声明为 simulator collider 或 physics-ready mesh。

图一的 depth-grid mesh 更忠实于原始 depth 图，适合分析深度边界、相机对齐和多视角重叠问题；图三的 BPA mesh 更保守，倾向保留可见局部表面，少做全局补洞；图二是 Open3D 重建前的轻量点云中间产物。

### 与 3DGS / collider 的边界

这些 PLY 都不是 GraphDECO / 3DGS Gaussian PLY。它们没有 trained Gaussian 的 `scale`、`rotation`、`opacity`、SH features，也没有经过 3DGS photometric optimization。更准确的定位是：

- `vggt_omega_depth_unproject_rgb_points.ply`：VGGT-Omega depth/camera prior 反投影得到的 RGB 点云，可做 QA、可视化、TSDF/Poisson/Delaunay/GraphDECO 初始化候选。
- `vggt_omega_pointcloud_poisson_depth7_trim08_mesh.ply`：从上述点云下采样后重建的干净 mesh baseline，可做视觉 proxy 或后续 collider 清理的输入。
- 若要变成 Video2Mesh 主链路资产，还需要 scale/camera audit、坐标合同固化、mesh cleanup/decimation、语义 sidecar transfer，以及碰撞/导航/物理用途的单独验证。

## 和已有 VGGT / AnySplat 的关系

已有 [VGGT](vggt.md) 页把 VGGT 归为 learned pose/depth fallback，并记录了 bedroom_4 clean31 上 no-cap 点云实测。VGGT-Omega 应作为这个方向的升级版单独跟踪，因为它加入了动态场景、register attention、text alignment checkpoint 和更明确的 runtime memory 数据。

AnySplat 页面里提到使用 pretrained VGGT 作为 pseudo-geometry prior。VGGT-Omega 未来也可能扮演类似角色：先给 video frames 估相机和深度，再把这些几何线索交给前馈 3DGS 或 GraphDECO refinement。但这仍然属于 prior / initialization，不是最终 visual/collider asset。

## 在 Video2Mesh 中的位置

```text
video frames
  -> VGGT-Omega camera/depth/point cloud prior
  -> quality and scale audit
  -> COLMAP-compatible export or fallback camera_info
  -> GraphDECO / Delaunay / semantic fusion
```

推荐先做三类小实验：

1. **COLMAP fallback audit**：选 COLMAP 不稳或弱纹理片段，比较 VGGT-Omega predicted cameras 与 COLMAP sparse cameras 的相对姿态、尺度和重投影质量。
2. **GraphDECO initialization**：把 VGGT-Omega point cloud + cameras 转成 COLMAP-like source，跑 3k/7k GraphDECO 短训，和 AnySplat->GraphDECO 路线并排比较。
3. **Dynamic/static split**：对有移动物体的视频，用 VGGT-Omega 的 depth/camera 作为基础，再接 D4RT / tracking 方法估计动态 object trajectory。

## 接入判断

- P0：暂不替代 COLMAP 主链路，因为虽然 `bedroom_4` 点云和 Poisson mesh 已经很干净，但还没有完成 scale/camera audit、碰撞网格清理和 simulator collider 验证。
- P1：作为 learned geometry fallback 和 GraphDECO 初始化候选，尤其适合 COLMAP 失败、输入视角少或纹理弱的片段；本次 120 万点 depth-unproject 点云说明它可以提供质量很高的 dense geometry prior。
- P1：作为动态视频 camera/depth prior，和 D4RT 这类 4D tracking 方法配合。
- P2：探索 text-aligned registers 是否能辅助 semantic sidecar 或自然语言场景查询。
- 风险：权重访问需要申请；输出不是标准 COLMAP workspace；点云/mesh/collider 的坐标、尺度、confidence 必须额外记录；Poisson mesh 虽然空洞少，但会平滑和补全未观测区域，不能直接等同物理碰撞体。
