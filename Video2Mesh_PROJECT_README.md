# Video2Mesh 项目说明

## 1. 项目目标

Video2Mesh 的目标是把一段真实空间扫描视频转换成可查看、可分解、可导入仿真器的 3D 场景资产。当前工程已经跑通一条 demo 级闭环：

```text
扫描视频
  -> 抽帧
  -> MASt3R-SLAM 相机位姿与点云
  -> 最小 3D Gaussian Splatting baseline
  -> SAM 自动物体候选与 2D mask tracking
  -> 2D mask 投影融合为物体级 3D mask
  -> floor / ceiling / wall 等背景结构 3D 语义 mask
  -> 语义 3DGS / SuperSplat 可视化文件
  -> 每物体相关帧选择
  -> 每物体粗 mesh 重建
  -> 多视角 mesh job / image-blaster 资产入口
  -> image-blaster 物体资产目录
  -> MuJoCo / Isaac / Unity 仿真资产包
  -> SceneVerse++ / SVPP-style 数据导出
```

这个仓库当前不是最终论文级系统，而是一个工程协议和可运行 baseline。它的价值在于把视频重建、3DGS、物体语义 mask、单物体 mesh、仿真导出这些模块用统一文件格式串起来。

## 2. 仓库结构

```text
Video2Mesh/
  video2mesh/
    cli.py                         # 主 CLI，所有流水线命令都在这里
  configs/
    mast3r_video_scan.yaml         # MASt3R-SLAM 视频扫描配置
  dataset/
    milscene.mp4                   # 示例扫描视频
    milscene2.mp4                  # 示例扫描视频
  exports/
    milscene_real_demo/            # 已跑通的真实视频 demo
    milscene2_real_demo/           # 已跑通的真实视频 demo，含最新 viewer PLY
  SceneVersepp/                    # 参考项目：3D 场景理解 / SVPP / SpatialLM / PQ3D
  image-blaster/                   # 参考项目：单图生成环境 / 物体 mesh / Three.js viewer
  Video2Mesh_technical_survey_draft.md
  Video2Mesh_real_demo_runbook.md
  VIDEO2MESH_PIPELINE.md
  REMOTE_SETUP_STATUS.md
```

几个文档的分工：

- `Video2Mesh_PROJECT_README.md`：当前这份总览文档。
- `Video2Mesh_technical_survey_draft.md`：偏论文调研，解释 SceneVerse++ 和 image-blaster 如何映射到目标系统。
- `VIDEO2MESH_PIPELINE.md`：偏 CLI / 数据协议 / 阶段说明。
- `Video2Mesh_real_demo_runbook.md`：真实 demo 的运行记录和命令。
- `REMOTE_SETUP_STATUS.md`：远端环境、依赖、smoke test 记录。

## 3. 参考项目的角色

### 3.1 SceneVersepp

`SceneVersepp` 不是直接的端到端视频转 3DGS 工具。它更像一个研究型 3D 场景理解数据引擎，重点在：

- `data_processing/`：视频下载、抽帧、相机位姿可视化。
- `SpatialLM/`：3D object/layout detection，输出 3D boxes / layout code。
- `PQ3D/`：3D instance segmentation，训练点云或 segment 级实例 mask。

对 Video2Mesh 来说，SceneVerse++ 最有用的是 SVPP-style 数据组织方式：

```text
mesh.ply
camera_info.json
metadata.json
data_info.json
```

Video2Mesh 已提供：

```bash
python -m video2mesh.cli export-svpp-metadata \
  --project-root exports/milscene2_real_demo \
  --scene-id milscene2-real-demo \
  --output-dir exports/milscene2_real_demo/simulator_assets/svpp/milscene2-real-demo \
  --default-category object \
  --min-points 1
```

输出示例：

```text
exports/milscene2_real_demo/simulator_assets/svpp/milscene2-real-demo/
  mesh.ply
  camera_info.json
  metadata.json
  data_info.json
  video2mesh_svpp_export.json
```

SVPP 导出时要靠 `object_id` 对齐 Video2Mesh 的 object record、semantic PLY、simulator bundle 和 SceneVerse++ metadata。`semantic_id` 是实例标签，`pred_class_id` 是类别标签，二者不能混用；`floor`、`ceiling`、`wall_*` 这类背景结构也会作为带独立 semantic id 的结构实例进入 metadata。

### 3.2 image-blaster

`image-blaster` 关注从单张图片生成资产。它的目录约定对 Video2Mesh 很有用：

```text
image-blaster/worlds/<world>/
  source/
  output/<object_id>/
    object.json
    source.png
    video2mesh_object_images/
```

Video2Mesh 会把每个物体选出的参考帧和裁剪图导出到 image-blaster world。后续可以用 image-blaster / FAL / Hunyuan / Meshy 生成更好的单物体 mesh。

当前 demo 中已经生成：

```text
image-blaster/worlds/milscene2-real-demo/
```

对应命令脚本：

```text
exports/milscene2_real_demo/simulator_assets/mesh_generation_commands.sh
exports/milscene2_real_demo/simulator_assets/multiview_mesh_jobs/run_mesh_jobs.sh
```

## 4. 核心流水线

### 4.1 视频与重建

输入视频放在：

```text
dataset/<video>.mp4
```

初始化项目并抽帧：

```bash
python -m video2mesh.cli init \
  --project-root exports/milscene2_real_demo \
  --scene-id milscene2_real_demo \
  --video dataset/milscene2.mp4

python -m video2mesh.cli extract-frames \
  --project-root exports/milscene2_real_demo \
  --every 4 \
  --overwrite \
  --renumber
```

运行 MASt3R-SLAM：

```bash
python -m video2mesh.cli run-mast3r-slam \
  --project-root exports/milscene2_real_demo \
  --dataset exports/milscene2_real_demo/scene/frames \
  --config config/video_scan.yaml \
  --save-as milscene2_real_demo_dense \
  --focal-scale 1.2
```

关键输出：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
scene/mast3r_keyframes/
```

### 4.2 原始点云与 10k 点云

`point_cloud.ply` 是 MASt3R-SLAM 原始点云，点数更多，几何更完整。

`point_cloud_10k.ply` 是从原始点云下采样得到的轻量工作点云，用于 3DGS baseline、mask fusion 和物体 mask cloud 导出。

```text
scene/reconstruction/point_cloud.ply      # 原始大点云
scene/reconstruction/point_cloud_10k.ply  # 10k 下采样点云
```

下采样命令：

```bash
python -m video2mesh.cli downsample-point-cloud \
  --project-root exports/milscene2_real_demo \
  --point-cloud exports/milscene2_real_demo/scene/reconstruction/point_cloud.ply \
  --output scene/reconstruction/point_cloud_10k.ply \
  --max-points 10000 \
  --seed 7
```

### 4.3 3DGS baseline

当前 `train-gsplat` 是最小 baseline：从点云初始化 Gaussians，用 `gsplat.rasterization` 做少量 L1 reconstruction 优化。它用于验证工程接口，不代表最终高质量 3DGS。

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli train-gsplat \
  --project-root exports/milscene2_real_demo \
  --frames-dir exports/milscene2_real_demo/scene/mast3r_keyframes \
  --point-cloud exports/milscene2_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --output-dir exports/milscene2_real_demo/scene/reconstruction/3dgs_trained \
  --iterations 10 \
  --max-frames 6 \
  --max-points 8000 \
  --device cuda \
  --width 288 \
  --height 512 \
  --log-every 2
```

关键输出：

```text
scene/reconstruction/3dgs/point_cloud/iteration_10/point_cloud.ply
scene/reconstruction/3dgs/point_cloud/iteration_10/point_cloud_point_cloud.ply
scene/reconstruction/3dgs/point_cloud/iteration_10/point_cloud_supersplat.ply
```

### 4.4 2D mask 与 3D mask

自动生成物体候选：

```bash
python -m video2mesh.cli auto-prompts \
  --project-root exports/milscene2_real_demo \
  --frames-dir exports/milscene2_real_demo/scene/mast3r_keyframes \
  --method sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b \
  --sam-device cuda \
  --frame-index 6 \
  --max-objects 6 \
  --min-area-ratio 0.003 \
  --max-area-ratio 0.35 \
  --overwrite
```

跨帧生成 2D masks：

```bash
python -m video2mesh.cli track-masks \
  --project-root exports/milscene2_real_demo \
  --frames-dir exports/milscene2_real_demo/scene/mast3r_keyframes \
  --prompts exports/milscene2_real_demo/masks/auto_prompts.json \
  --mask-backend sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b \
  --sam-device cuda \
  --max-frames 13 \
  --clear-output
```

融合到 3D 点云：

```bash
python -m video2mesh.cli fuse-masks \
  --project-root exports/milscene2_real_demo \
  --point-cloud exports/milscene2_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --min-votes 1 \
  --occlusion-filter \
  --depth-tolerance 0.05 \
  --relative-depth-tolerance 0.03
```

关键输出：

```text
masks/2d/
masks/3d/object_masks.json
objects/<object_id>/object.json
```

如果要把当前 demo 级 bbox/SAM tracking 替换成 SAM2 / DEVA / XMem / Grounded-SAM，可以先生成外部 video segmentation job，再把外部 masks 导回标准 `masks/2d`：

```bash
python -m video2mesh.cli prepare-video-segmentation-jobs \
  --project-root exports/milscene2_real_demo \
  --frames-dir exports/milscene2_real_demo/scene/mast3r_keyframes \
  --prompts exports/milscene2_real_demo/masks/auto_prompts.json \
  --provider sam2 \
  --command-template "python run_sam2.py --job {job_path} --output {mask_output_root}"

python -m video2mesh.cli import-video-segmentation-masks \
  --project-root exports/milscene2_real_demo \
  --source-root /path/to/external_masks \
  --provider sam2
```

导入后仍然走同一个 `fuse-masks -> semantic 3DGS -> object mesh -> simulator assets` 后半段。这一步是外部生产级视频分割的协议接口，不等于当前仓库已经内置 SAM2/DEVA/XMem。

如果后续用 VLM / 开放词汇检测器给 object_id 生成了更可靠的类别、名称和描述，可以把 JSON 标签导入回 Video2Mesh：

```bash
python -m video2mesh.cli import-object-labels \
  --project-root exports/milscene2_real_demo \
  --labels /path/to/object_labels.json
```

支持的最小格式可以是 map 或 list，例如：

```json
{
  "auto_object_blue_01": {
    "name": "blue chair",
    "category": "chair",
    "description": "blue chair near the desk"
  }
}
```

导入后会更新 `masks/object_labels.json` 和对应的 `objects/<object_id>/object.json`。这是给 VLM/open-vocabulary 语义命名预留的接口；当前 demo 的自动名称仍然只是颜色和候选编号，不应当视为可靠类别。

### 4.5 背景结构语义 mask

前景物体来自 2D mask tracking 和 2D-to-3D fusion；地面、天花板、墙面这类背景结构通常没有单物体 crop，也不应该进入 image-blaster mesh 生成。当前工程提供一个可运行的 axis-boundary baseline：

```bash
python -m video2mesh.cli infer-background-structure-masks \
  --project-root exports/milscene2_real_demo \
  --point-cloud exports/milscene2_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --up-axis y \
  --quantile 0.03 \
  --min-points 50
```

它会从点云边界启发式生成：

```text
objects/floor/object.json
objects/ceiling/object.json
objects/wall_x_min/object.json
objects/wall_x_max/object.json
objects/wall_z_min/object.json
objects/wall_z_max/object.json
masks/3d/<structure>/point_indices.json
simulator_assets/background_structures/background_structures.json
```

这些记录的 `asset_role` 是 `background_structure`：它们参与 semantic 3DGS、object mask cloud、SVPP metadata 和 simulator bundle，但会跳过 selected frames、object crops、object mesh 这些前景物体步骤。这个 baseline 只是协议验证，后续应替换为更稳的 layout segmentation / SpatialLM / PQ3D / open-vocabulary 3D segmentation。

### 4.6 Semantic 3DGS 与 viewer PLY

把 3D object mask 转移到 3DGS：

```bash
python -m video2mesh.cli export-splat-masks \
  --project-root exports/milscene2_real_demo \
  --mask-source-ply exports/milscene2_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --transfer-mode nearest \
  --max-transfer-distance 0.08
```

该命令会输出：

```text
simulator_assets/semantic_splats.ply
simulator_assets/semantic_splats_manifest.json
simulator_assets/semantic_point_cloud.ply
simulator_assets/semantic_supersplat.ply
```

也可以手动导出 viewer PLY：

```bash
python -m video2mesh.cli export-viewer-plys \
  --project-root exports/milscene2_real_demo \
  --kind all
```

输出：

```text
simulator_assets/viewer_plys/
  scene_3dgs_point_cloud.ply
  scene_3dgs_supersplat.ply
  semantic_3dgs_point_cloud.ply
  semantic_3dgs_supersplat.ply
  viewer_plys_manifest.json
```

PLY 查看约定：

| 文件 | 用途 |
| --- | --- |
| `*_point_cloud.ply` | 普通点云，字段是 `x/y/z/red/green/blue`，适合 Mac Preview、CloudCompare、MeshLab。 |
| `*_supersplat.ply` | SuperSplat / GraphDECO 兼容 PLY，字段包含 `f_dc_0/1/2`、`opacity`、`scale_0/1/2`、`rot_0/1/2/3`。 |
| `semantic_splats.ply` | Video2Mesh 内部语义 splat，包含 `object_id`，用于评估和投影。 |

## 5. 物体资产与仿真导出

导出每个物体的 3D mask cloud：

```bash
python -m video2mesh.cli export-object-mask-clouds \
  --project-root exports/milscene2_real_demo \
  --point-cloud exports/milscene2_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --skip-missing
```

选帧和裁剪参考图。注意：这些命令只处理 `asset_role=object` 的前景物体，会跳过 `asset_role=background_structure` 的 floor/wall/ceiling：

```bash
python -m video2mesh.cli select-frames \
  --project-root exports/milscene2_real_demo \
  --frames-dir exports/milscene2_real_demo/scene/mast3r_keyframes \
  --top-k 3

python -m video2mesh.cli prepare-object-images \
  --project-root exports/milscene2_real_demo \
  --top-k 3 \
  --skip-missing
```

从 3D mask cloud 生成粗 mesh：

```bash
python -m video2mesh.cli reconstruct-object-meshes \
  --project-root exports/milscene2_real_demo \
  --method auto \
  --format obj \
  --skip-missing \
  --skip-failed
```

如果要把每个物体交给外部单图或多视角 mesh 方法，可以先生成统一的 job JSON 和 shell 脚本：

```bash
python -m video2mesh.cli prepare-multiview-mesh-jobs \
  --project-root exports/milscene2_real_demo \
  --max-frames 2 \
  --command-template "python reconstruct_object.py --job {job_path} --output {mesh_output}" \
  --skip-missing
```

输出：

```text
simulator_assets/multiview_mesh_jobs/multiview_mesh_jobs.json
simulator_assets/multiview_mesh_jobs/jobs/<object_id>.json
simulator_assets/multiview_mesh_jobs/run_mesh_jobs.sh
```

这个命令不会真正解决 mesh 质量问题，它只是把 “object_id -> selected frames / crops / expected mesh output” 标准化，方便后续接 Hunyuan3D、Meshy、多视角重建或自研 object reconstruction。

导出 image-blaster world：

```bash
python -m video2mesh.cli export-image-blaster \
  --project-root exports/milscene2_real_demo \
  --world milscene2-real-demo \
  --image-blaster-root image-blaster \
  --provider hunyuan \
  --use-object-crop \
  --skip-missing
```

导出仿真器资产：

```bash
python -m video2mesh.cli export-simulator-assets \
  --project-root exports/milscene2_real_demo \
  --ascii-meshes
```

写入尺度、上方向和估算物理字段：

```bash
python -m video2mesh.cli calibrate-simulator-assets \
  --project-root exports/milscene2_real_demo \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --estimate-physics \
  --overwrite-physics
```

没有真实标尺时，`--scale-to-meters 1.0 --no-scale-calibrated` 只代表工程假设，不能当作真实物理尺度。后续如果知道某个物体的真实长度，可以用 `--reference-object <object_id> --reference-axis longest --reference-length-m <meters>` 自动反推 scale。

导出仿真器 adapter：

```bash
python -m video2mesh.cli export-simulator-adapter \
  --project-root exports/milscene2_real_demo \
  --format mujoco isaac unity
```

仿真资产 QA：

```bash
python -m video2mesh.cli qa-simulator-assets \
  --project-root exports/milscene2_real_demo \
  --max-issues 20
```

QA 会检查 mesh 是否可读、bbox/pose 是否大致对齐、是否缺少尺度标定、碰撞体和物理字段。背景结构允许没有 object mesh，并默认作为 static scene structure 进入 simulator bundle。

关键输出：

```text
simulator_assets/simulator_asset_bundle.json
simulator_assets/simulator_calibration.json
simulator_assets/simulator_asset_qa.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/objects/<object_id>/
```

## 6. 当前已跑通的真实 demo

### 6.1 milscene2_real_demo

路径：

```text
exports/milscene2_real_demo
```

输入：

```text
dataset/milscene2.mp4
```

当前评估：

```text
ok=true
frames=36
camera_poses=13
point_cloud_vertices=1,869,714
gsplat_vertices=8,000
2D_masks=78
semantic_records=12
foreground_objects=6
background_structures=6
objects_total=12
objects_with_reference_images=6
objects_with_3d_mask_clouds=12
objects_with_meshes=6
svpp_instances=12
simulator_bundle_objects=12
simulator_missing_meshes=[]
required_failed=[]
recommended_failed=[]
```

关键文件：

```text
exports/milscene2_real_demo/simulator_assets/review/index.html
exports/milscene2_real_demo/simulator_assets/evaluation_report.json
exports/milscene2_real_demo/simulator_assets/viewer_plys/scene_3dgs_supersplat.ply
exports/milscene2_real_demo/simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply
exports/milscene2_real_demo/simulator_assets/simulator_asset_bundle.json
exports/milscene2_real_demo/simulator_assets/simulator_calibration.json
exports/milscene2_real_demo/simulator_assets/simulator_asset_qa.json
exports/milscene2_real_demo/simulator_assets/background_structures/background_structures.json
exports/milscene2_real_demo/simulator_assets/svpp/milscene2-real-demo/metadata.json
image-blaster/worlds/milscene2-real-demo
```

### 6.2 milscene_real_demo

路径：

```text
exports/milscene_real_demo
```

输入：

```text
dataset/milscene.mp4
```

当前评估：

```text
ok=true
frames=46
camera_poses=45
point_cloud_vertices=5,083,870
gsplat_vertices=8,000
2D_masks=108
semantic_ids=6
objects=6
objects_with_reference_images=6
objects_with_3d_mask_clouds=6
objects_with_meshes=6
required_failed=[]
recommended_failed=[]
```

## 7. 远端环境

主要运行环境在远端：

```bash
ssh -p 14225 root@connect.westd.seetacloud.com
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo || true
source remote_env.sh
```

关键路径：

```text
/root/autodl-tmp/workspace/Video2Mesh
/root/autodl-tmp/workspace/MASt3R-SLAM
/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth
```

当前远端环境已验证：

- Python / PyTorch / CUDA 可用。
- MASt3R-SLAM 可以从 frame sequence 输出 trajectory、point cloud、keyframes。
- `gsplat` CUDA extension 已编译缓存，后续 3DGS baseline 训练会比第一次快。
- SAM vit_b checkpoint 可用于 auto prompts 和 bbox mask backend。

## 8. 验证和 Review

项目级验证：

```bash
python -m video2mesh.cli validate \
  --project-root exports/milscene2_real_demo
```

评估报告：

```bash
python -m video2mesh.cli evaluate \
  --project-root exports/milscene2_real_demo \
  --output exports/milscene2_real_demo/simulator_assets/evaluation_report.json
```

仿真资产 QA：

```bash
python -m video2mesh.cli qa-simulator-assets \
  --project-root exports/milscene2_real_demo \
  --max-issues 20
```

Review HTML：

```bash
python -m video2mesh.cli export-review-pack \
  --project-root exports/milscene2_real_demo \
  --max-scene-frames 4 \
  --max-frames 3
```

Review HTML 中会包含：

- 自动 prompt 预览。
- 点云投影 QA。
- semantic mask 投影 QA。
- 3DGS render / target / error。
- 每个物体的 reference image、selected frames、mesh 路径、simulator mesh 状态。

## 9. 局限和下一步

当前系统已经完成工程闭环，但还有明显局限：

- 3DGS 是最小 baseline，只有少量迭代，没有 densification、pruning、SH appearance、曝光处理。
- 物体语义名仍来自自动候选颜色名，不是可靠开放词汇类别。
- 2D tracking 是 bbox/SAM demo 级别，后续应换 SAM2 / DEVA / XMem 一类跨帧一致性更强的 video segmentation。
- 3D mask fusion 依赖 MASt3R-SLAM 位姿和点云质量，遮挡、反光、透明物体会明显影响结果。
- 当前 mesh 是从 3D mask cloud 粗重建，适合接口验证，不适合最终仿真质量。
- 目前只有工程假设/参考物体式尺度接口和 bbox 体积物理估计，仍缺少真实测量尺度、可靠质量/摩擦和稳定碰撞体。
- 背景结构目前只是点云边界启发式 floor/ceiling/wall mask，不会识别门、窗、柜体、桌面等语义结构，也不是可靠 layout reconstruction。

建议下一步：

1. 接入更高质量 3DGS trainer，例如完整 gsplat / nerfstudio / gaussian-splatting 流水线。
2. 用 SAM2 或 DEVA 替换当前 bbox/SAM tracking。
3. 引入开放词汇检测或 VLM，为每个 object_id 自动生成类别和描述。
4. 用多视角物体重建替换当前粗 mask-cloud mesh。
5. 给仿真资产增加尺度标定、质量、摩擦、碰撞体简化和坐标系 QA。
6. 将 SVPP-style export 接到 SceneVerse++ 的 SpatialLM / PQ3D 数据生成脚本中做进一步训练或评估。
7. 用 layout / semantic scene parsing 替换当前背景结构启发式，覆盖地面、墙、天花板、门窗、固定柜体等不可移动或半固定结构。

## 10. 快速入口

查看已跑通 demo：

```text
exports/milscene2_real_demo/simulator_assets/review/index.html
```

上传到 SuperSplat：

```text
exports/milscene2_real_demo/simulator_assets/viewer_plys/scene_3dgs_supersplat.ply
exports/milscene2_real_demo/simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply
```

用 Mac Preview 看普通点云：

```text
exports/milscene2_real_demo/simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply
exports/milscene2_real_demo/simulator_assets/viewer_plys/semantic_3dgs_point_cloud.ply
```

查看仿真器导出：

```text
exports/milscene2_real_demo/simulator_assets/adapters/mujoco/scene.xml
exports/milscene2_real_demo/simulator_assets/adapters/isaac/isaac_adapter.json
exports/milscene2_real_demo/simulator_assets/adapters/unity/unity_adapter.json
exports/milscene2_real_demo/simulator_assets/simulator_asset_qa.json
```
