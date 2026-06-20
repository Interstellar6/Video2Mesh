# Video2Mesh 项目说明

更新时间：2026-06-20

## 1. 项目目标

Video2Mesh 的目标是把一段真实空间扫描视频转换为可展示、可分解、可进入仿真器的 3D 场景资产。

当前工程目标不是“单图生成一个好看的 mesh”，而是：

```text
扫描视频
  -> 相机位姿与场景点云
  -> 场景级 3D Gaussian Splatting
  -> 物体/背景结构级 3D semantic masks
  -> 每个物体的相关帧与裁图
  -> 每个物体 mesh
  -> MuJoCo / Unity / Isaac 可消费的资产包
```

## 2. 当前默认路线

真实视频实验默认使用：

- MASt3R-SLAM：从视频估计相机位姿、keyframes 和原始场景点云。
- GraphDECO Gaussian Splatting：默认 3DGS trainer。
- SAM v1 ViT-B：生成初始 object prompts。
- SAM2.1 Hiera Tiny：做 video mask propagation。
- Video2Mesh fusion：把 2D masks 通过相机投影融合成 3D masks，并回写到 Gaussian / viewer PLY。
- SVLGaussian-style frame selection：采用 SVLGaussian 论文的 view-selection protocol（DOI `10.1049/cit2.70148`），为每个物体选择 anchor、5/10 frame offset、30-frame random-window 补充帧；这不是完整复现其 Flash3D/Qwen/SAM 单图 pipeline。
- baseline mesh exporter：先从 3D mask cloud 得到粗 mesh；后续可替换为 Hunyuan/Meshy/多视角 mesh。
- simulator exporter：导出 object pose、mesh、collider、physics stub、语义 ID 和仿真器 adapter。

内置 minimal `train-gsplat` 只作为 smoke/debug fallback；真实实验默认使用 GraphDECO。

## 3. 一键入口

远端运行：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh /root/autodl-tmp/workspace/Video2Mesh/dataset/<video>.mp4
```

默认参数：

```text
GS_BACKEND=graphdeco
GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting
GRAPHDECO_ITERATIONS=7000
GRAPHDECO_RESOLUTION=1
GRAPHDECO_DENSIFY_UNTIL_ITER=0
MASK_BACKEND=sam2
MAX_FRAMES=72
EXTRACT_EVERY=2
```

GraphDECO 默认使用 MASt3R full point cloud 初始化，但关闭 densification。这个设置是为了避免千万级初始化点云在 32GB 显存上继续扩点导致 OOM；它不是降采样策略。

如果 MASt3R-SLAM 对长视频运行超过 1.5 小时仍未产出 `camera_info.json` 和 `point_cloud.ply`，当前实验策略是中断该次 MASt3R，把视频前 60 秒裁剪成新的 dataset 文件，例如：

```text
dataset/bedroom_100_first60.mp4
```

然后对该新数据集重新运行一键流程。

如果 `*_first60.mp4` 的 MASt3R 仍超过 30 分钟，或 30 分钟内结束但 readiness 显示单 pose / 空点云，则继续裁剪更稳定的 10 秒片段作为新 dataset，例如 `dataset/bedroom_100_first60_best10.mp4`。这条规则用于避免把不可重建片段送入 GraphDECO 或语义融合。

推荐使用仓库内的 OpenCV 裁剪工具生成该 fallback 数据集：

```bash
python tools/crop_best_video_window.py dataset/bedroom_100_first60.mp4 \
  --duration 10 \
  --output dataset/bedroom_100_first60_best10.mp4 \
  --force
```

当 MASt3R/GraphDECO 已经完成、只需要恢复下游资产阶段时，使用：

```bash
bash tools/run_video2mesh_downstream_light.sh \
  exports/<run> \
  dataset/bedroom_100_first60_best10.mp4
```

## 4. 不降采样约定

高质量实验默认使用 MASt3R-SLAM 原始点云：

```text
scene/reconstruction/point_cloud.ply
```

它同时作为：

- GraphDECO COLMAP `points3D.txt` 的来源。
- 2D-to-3D mask fusion 的点索引源。
- semantic splat transfer 的点索引源。
- object mask cloud 和背景结构 mask 的点索引源。

`point_cloud_10k.ply`、`point_cloud_30000.ply` 只用于轻量预览、人工检查或低资源 debug，不作为默认训练/分割输入。

检查命令：

```bash
python -m video2mesh.cli audit-3dgs-init-point-cloud \
  --project-root exports/<run>
```

## 5. 关键输出

每个 run 默认在：

```text
exports/<scene>_quick_<timestamp>/
```

核心产物：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
scene/reconstruction/3dgs_graphdeco/
masks/2d*/
masks/3d/object_masks.json
objects/<object_id>/selected_frames/
objects/<object_id>/object_images/
simulator_assets/viewer_plys/
simulator_assets/semantic_splats.ply
simulator_assets/simulator_asset_bundle.json
simulator_assets/adapters/
simulator_assets/review/index.html
```

Viewer PLY 约定：

| 文件 | 用途 |
|---|---|
| `*_point_cloud.ply` | 普通 XYZ/RGB 点云，Mac Preview、MeshLab、CloudCompare 可看。 |
| `*_supersplat.ply` | GraphDECO/SuperSplat 字段 PLY，可上传到 SuperSplat。 |
| `semantic_*` | 语义颜色或 `object_id/object_probability` 已写入的版本。 |

## 6. 两个参考项目的角色

`SceneVersepp`：

- 不是任意扫描视频到 3DGS 的完整推理系统。
- 主要提供 SVPP-style 数据格式、SpatialLM/PQ3D 的场景理解训练/评估接口。
- Video2Mesh 复用它的数据组织方式：`mesh.ply`、`camera_info.json`、`metadata.json`、`data_info.json`。

`image-blaster`：

- 不是视频重建系统。
- 主要提供单图/物体图到 mesh、world 目录和 Three.js viewer 的资产生成思路。
- Video2Mesh 复用其 `worlds/<world>/output/<object>/` 资产约定，后续可接 Hunyuan/Meshy/FAL。

## 7. 当前局限

- GraphDECO 已接入为默认 trainer，但长视频重建质量仍受 MASt3R 位姿、帧选择、显存和训练时间影响。
- SAM2.1 tiny 比 SAM v1 bbox tracking 更稳定，但对折叠椅、植物、透明/反光/细结构仍会过分割或漂移。
- 物体语义名还需要开放词汇检测或 VLM 回流。
- 当前物体 mesh 多为 object mask cloud baseline，适合验证尺度和接口，不是最终仿真质量。
- 背景结构仍以 floor/wall/ceiling 等 baseline 为主，door/window/cabinet 等需要更强 scene structure segmentation。
- 仿真器资产仍需要真实尺度标定、碰撞体质量检查和物理属性测量。

## 8. 文档入口

- `README.md`：GitHub 首页。
- `VIDEO2MESH_PIPELINE.md`：完整流程、命令和数据协议。
- `Video2Mesh_real_demo_runbook.md`：远端实验运行手册。
- `REMOTE_SETUP_STATUS.md`：远端环境、依赖、权重和 GraphDECO 状态。
- `Video2Mesh_milscene3_showcase.md`：当前可展示产物清单。
- `SVLGaussian_frame_matching_notes.md`：帧匹配/选帧算法说明。
