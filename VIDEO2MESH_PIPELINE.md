# Video2Mesh 原型流水线说明

这个工程层把两个参考项目连接成一个可以迭代的 Video2Mesh 原型：

- `SceneVersepp`：提供 SVPP 数据形态、相机/mesh/点云组织方式、SpatialLM/PQ3D 的场景理解入口。
- `image-blaster`：提供单物体图片到 mesh 的资产生成入口，以及 `worlds/<slug>/output/<object>/` 资产目录约定。

当前新增的 `video2mesh` 包不直接替代 3DGS、SAM、PQ3D 或 Hunyuan/Meshy，而是定义它们之间的工程协议，并实现已经能本地运行的部分：

1. 初始化项目目录。
2. 注册视频重建产物：相机、点云、3DGS 目录。
3. 读取帧级 2D object masks。
4. 将 2D masks 通过相机投影融合到点云，得到每个物体的 3D point mask。
5. 对每个物体自动选帧。
6. 导出 image-blaster 可消费的 object 目录。
7. 生成 mesh 调用命令，后续用 FAL/API key 执行。
8. 或者从物体级 3D mask point cloud 直接重建一个保尺度/保位姿的 object mesh baseline。

## 1. 快速 smoke test

在远端服务器上：

```bash
ssh -p 14225 root@connect.westd.seetacloud.com
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
```

创建合成样例：

```bash
python -m video2mesh.cli make-sample \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/synthetic_room \
  --scene-id synthetic_room
```

运行本地可执行闭环：

```bash
python -m video2mesh.cli run-local \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/synthetic_room \
  --image-blaster-root /root/autodl-tmp/workspace/Video2Mesh/image-blaster \
  --world synthetic_room
```

查看结果：

```bash
python -m video2mesh.cli status \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/synthetic_room
```

也可以用一条命令跑完整工程 smoke。下面的 3DGS 和 mesh 都是 placeholder/mock，只用于验证协议闭环：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/run_pipeline_smoke \
  --scene-id run_pipeline_smoke \
  --world run_pipeline_smoke \
  --make-sample \
  --g3dgs-command-template "python -c 'from pathlib import Path; import shutil; out=Path(\"{output_path}\")/\"point_cloud\"/\"iteration_1\"; out.mkdir(parents=True, exist_ok=True); shutil.copy2(Path(\"{project_root}\")/\"scene/reconstruction/point_cloud.ply\", out/\"point_cloud.ply\")'" \
  --image-blaster-root /root/autodl-tmp/workspace/Video2Mesh/image-blaster \
  --create-placeholder-meshes
```

也可以不用 placeholder mesh，而是从 fused 3D object mask cloud 直接重建 OBJ baseline：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/run_pipeline_mask_mesh_smoke \
  --scene-id run_pipeline_mask_mesh_smoke \
  --world run_pipeline_mask_mesh_smoke \
  --make-sample \
  --g3dgs-command-template "mkdir -p {output_path}/point_cloud/iteration_1 && cp {project_root}/scene/reconstruction/point_cloud.ply {output_path}/point_cloud/iteration_1/point_cloud.ply" \
  --reconstruct-mask-meshes \
  --mask-mesh-method auto \
  --mask-mesh-format obj \
  --simulator-format mujoco isaac unity
```

远端 `run_pipeline_mask_mesh_smoke` 已验证通过：不使用 `--create-placeholder-meshes`，两个物体的 mesh 来源均为 `object_mask_cloud_reconstruction`，Open3D 自动选择 ball-pivoting，分别生成 `382` 和 `375` 个三角面，`validate_ok == True`。

也可以用内置最小 `gsplat` trainer 替代 mock 3DGS，跑一个真实 differentiable rasterization/backward 的 3DGS baseline：

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/run_pipeline_gsplat_smoke \
  --scene-id run_pipeline_gsplat_smoke \
  --world run_pipeline_gsplat_smoke \
  --make-sample \
  --train-gsplat \
  --gsplat-iterations 8 \
  --gsplat-max-frames 2 \
  --gsplat-max-points 192 \
  --gsplat-width 160 \
  --gsplat-height 120 \
  --transfer-mode nearest \
  --max-transfer-distance 0.2 \
  --reconstruct-mask-meshes \
  --mask-mesh-method auto \
  --mask-mesh-format obj \
  --simulator-format mujoco isaac unity
```

远端 `run_pipeline_gsplat_smoke` 已验证通过：`train_gsplat` 真实调用 `gsplat.rasterization + loss.backward`，输出 `scene/reconstruction/3dgs/point_cloud/iteration_8/point_cloud.ply`，再继续生成 semantic splats、object mask clouds、selected frames、object crops、object meshes 和 MuJoCo/Isaac/Unity adapters，`validate_ok == True`。它是可微 3DGS 工程 baseline，不含 densification/pruning/SH 等高质量训练细节。该项目后续又用 `render-gsplat-preview` 渲染 2 个训练视角，生成 `simulator_assets/gsplat_preview/<frame_id>/{render,target,error}.png` 和 `preview_manifest.json`，`mean_l1=0.12295898050069809`，`mean_psnr=13.984593019374712`。

也可以从一个 synthetic scan `.mp4` 文件开始跑完整工程闭环，用来验证“视频文件入口 -> 抽帧 -> 3DGS -> 自动物体 prompts -> 3D masks -> mesh -> simulator assets”的编排：

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/run_pipeline_scan_video_full_smoke \
  --scene-id run_pipeline_scan_video_full_smoke \
  --world run_pipeline_scan_video_full_smoke \
  --make-scan-video-sample \
  --every 3 \
  --max-frames 4 \
  --overwrite-frames \
  --train-gsplat \
  --gsplat-iterations 4 \
  --gsplat-max-frames 2 \
  --gsplat-max-points 128 \
  --gsplat-width 160 \
  --gsplat-height 120 \
  --render-gsplat-preview \
  --preview-max-frames 2 \
  --preview-width 160 \
  --preview-height 120 \
  --auto-prompts \
  --auto-prompt-method opencv \
  --auto-prompt-max-objects 4 \
  --mask-backend opencv \
  --transfer-mode nearest \
  --max-transfer-distance 0.2 \
  --render-semantic-preview \
  --semantic-preview-max-frames 2 \
  --reconstruct-mask-meshes \
  --mask-mesh-method auto \
  --mask-mesh-format obj \
  --simulator-format mujoco isaac unity
```

远端 `run_pipeline_scan_video_full_smoke` 已验证通过：从 `inputs/synthetic_scan.mp4` 抽出 `4` 帧，训练 `128` 个 Gaussian vertices 的最小 3DGS，回渲染预览 `2` 帧，`mean_l1=0.12248225882649422`、`mean_psnr=13.996128072430665`；`auto-prompts` 自动得到 `2` 个物体，两个物体各 `324` 个 3D mask 点，mesh 和 MuJoCo/Isaac/Unity adapters 均导出，`evaluate.ok == True`。这是视频入口和工程协议 smoke，不代表真实世界扫描质量已经完成。

远端 `run_pipeline_semantic_preview_gsplat_smoke` 已进一步验证 `--render-semantic-preview`：synthetic mp4 抽帧后训练真实最小 3DGS，导出 semantic splats，再生成 `simulator_assets/semantic_preview/semantic_splats_colored.ply` 和 `2` 张 `semantic_overlay.png`，`evaluate.ok == True`，review HTML 包含 `Semantic 3D Mask Projection` section。这个 QA 用于检查 object-level 3D semantic mask 是否能按相机位姿投回图像。

真实视频时，把 `--make-scan-video-sample` 换成 `--video/--dataset`、`--run-mast3r-slam`、真实 `--g3dgs-command-template` 或高质量 3DGS trainer，并检查 `auto_prompts_preview.png`、`gsplat_preview` 和 `semantic_preview`。mesh 阶段有两条路线：用 image-blaster/FAL 的生成结果跑 `import-object-meshes`，或者先用 `--reconstruct-mask-meshes` 从 3D object mask cloud 得到几何 baseline。

如果只想先验证扫描/帧序列能通过 MASt3R-SLAM 导入 Video2Mesh，可以跑 reconstruction-only pipeline：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scene-id <scene_id> \
  --dataset /path/to/frames_or_video \
  --run-mast3r-slam \
  --mast3r-config config/eval_no_calib.yaml \
  --width 640 --height 480 --fx 500 --fy 500 --cx 320 --cy 240 \
  --skip-fuse-masks \
  --skip-export-splat-masks \
  --skip-select-frames \
  --skip-object-images \
  --skip-export-image-blaster \
  --skip-import-meshes \
  --skip-simulator-assets \
  --allow-incomplete
```

这会验证 MASt3R-SLAM 是否能输出 trajectory/PLY/keyframes，并写入 `scene/cameras/camera_info.json`、`scene/reconstruction/point_cloud.ply`、`scene/frames/`。因为语义和 mesh 阶段被跳过，`validate` 失败是预期现象。

如果只想先把一个 `.mp4` 扫描视频抽帧进 Video2Mesh 项目，可以直接用 OpenCV 抽帧入口；远端不需要系统 `ffmpeg`：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scene-id <scene_id> \
  --dataset /path/to/scan_video.mp4 \
  --extract-frames \
  --every 10 \
  --max-frames 200 \
  --skip-fuse-masks \
  --skip-export-splat-masks \
  --skip-object-mask-clouds \
  --skip-select-frames \
  --skip-object-images \
  --skip-export-image-blaster \
  --skip-import-meshes \
  --skip-simulator-assets \
  --allow-incomplete
```

`--dataset` 是文件且没有显式传 `--video` 时，pipeline 会把它当作视频源。抽帧默认会把输出重编号为连续的 `000000.png`、`000001.png`，并在 `scene/frames_manifest.json` 记录原始视频帧号和时间戳，后面排查 MASt3R/3DGS/mask 对齐问题时用这个 manifest。

核心输出：

```text
exports/synthetic_room/
  manifest.json
  scene/
    frames/
    cameras/camera_info.json
    reconstruction/point_cloud.ply
  masks/
    2d/
    3d/object_masks.json
  objects/
    red_cube/object.json
    red_cube/selected_frames/
    blue_cube/object.json
    blue_cube/selected_frames/
  simulator_assets/
    asset_manifest.json
    selected_frames.json
```

同时会写入：

```text
image-blaster/worlds/synthetic_room/
  source/video2mesh_manifest.json
  output/red_cube/object.json
  output/red_cube/source.png
  output/blue_cube/object.json
  output/blue_cube/source.png
```

## 2. 真实视频任务的阶段协议

### Phase A：视频到 3DGS/相机/点云

这一阶段可以接入 COLMAP、Gaussian Splatting、MASt3R-SLAM 或其他 video-to-3DGS 工具。Video2Mesh 需要至少拿到：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
scene/reconstruction/3dgs/
scene/frames/<frame_id>.png
```

`camera_info.json` 采用 SceneVerse++ 风格：

```json
{
  "intrinsic": {
    "w": 640,
    "h": 480,
    "fx": 500.0,
    "fy": 500.0,
    "cx": 320.0,
    "cy": 240.0
  },
  "extrinsic": {
    "0": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
  }
}
```

默认外参解释为 `world_to_camera`。如果来自 COLMAP/MASt3R-SLAM 的导出是 `camera_to_world`，运行 `fuse-masks` 时传：

```bash
--extrinsic-type camera_to_world
```

注册重建产物：

```bash
python -m video2mesh.cli init \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scene-id <scene_id> \
  --video /path/to/scan_video.mp4

python -m video2mesh.cli register-reconstruction \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --point-cloud /path/to/point_cloud.ply \
  --camera-info /path/to/camera_info.json \
  --scene-3dgs /path/to/3dgs_output \
  --mode copy
```

如果只想先抽帧：

```bash
python -m video2mesh.cli extract-frames \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --video /path/to/scan_video.mp4 \
  --every 30 \
  --max-frames 200
```

输出：

```text
scene/frames/*.png
scene/frames_manifest.json
```

如果需要一个可复现的视频入口 smoke，可以先生成 synthetic scan `.mp4`，同时写入与推荐抽帧步长匹配的 `camera_info.json` 和 `point_cloud.ply`：

```bash
python -m video2mesh.cli make-scan-video-sample \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scene-id <scene_id> \
  --frame-count 10 \
  --extract-every 3
```

输出：

```text
inputs/synthetic_scan.mp4
source_frames/*.png
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

随后可用 `extract-frames --every 3` 或 `run-pipeline --make-scan-video-sample --every 3` 从该视频文件入口继续跑后续阶段。

`frames_manifest.json` 包含 `source_video`、`source_fps`、`source_frame_count`、`written_frame_count`，以及每张输出帧对应的 `source_frame_index` 和 `source_time_sec`。

如果已有 COLMAP sparse text model，可以直接导入：

```bash
python -m video2mesh.cli import-colmap \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --sparse-dir /path/to/colmap/sparse/0 \
  --images-dir /path/to/images \
  --mode copy
```

要求 `--sparse-dir` 下有：

```text
cameras.txt
images.txt
points3D.txt
```

如果当前是 COLMAP `.bin`，先用 COLMAP 转文本：

```bash
colmap model_converter \
  --input_path /path/to/sparse/0 \
  --output_path /path/to/sparse_text/0 \
  --output_type TXT
```

如果相机和点云来自 MASt3R-SLAM、SceneVerse++ 或其他工具，但后续 3DGS 训练脚本要求 COLMAP-style 数据，也可以反向导出：

```bash
python -m video2mesh.cli export-colmap \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --output-dir /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>/exports/colmap_text
```

输出：

```text
exports/colmap_text/
  images/
  sparse/0/cameras.txt
  sparse/0/images.txt
  sparse/0/points3D.txt
  video2mesh_colmap_export.json
```

这个目录可以作为很多 Gaussian Splatting 实现的 `source_path`/COLMAP 输入；如果某个实现只接受 binary COLMAP model，再用 `colmap model_converter --input_path sparse/0 --output_path sparse_bin/0 --output_type BIN` 转换。

在把 2D mask 投影融合到 3D 之前，建议先检查相机和点云是否对齐。可以把 `point_cloud.ply` 投影回输入帧，生成 overlay 图和 coverage 指标：

```bash
python -m video2mesh.cli render-reconstruction-preview \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-frames 5
```

输出：

```text
simulator_assets/reconstruction_preview/reconstruction_preview.json
simulator_assets/reconstruction_preview/<frame_id>/projection_overlay.png
```

`reconstruction_preview.json` 会记录每帧 `projected_points`、`visible_points`、`projected_pixel_ratio`、`visible_pixel_ratio` 等指标。这个 QA 看的是 camera/point-cloud alignment，不是 3DGS 画质；如果 overlay 明显错位，应先修相机位姿、尺度、坐标系或内参，再继续做 `fuse-masks`。

也可以用 `run-3dgs` 作为统一入口：它会先导出 COLMAP-style source，然后按模板运行外部 3DGS trainer，成功后自动注册输出目录。

```bash
python -m video2mesh.cli run-3dgs \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --command-template "python /path/to/gaussian-splatting/train.py -s {source_path} -m {output_path}"
```

模板可用变量：

```text
{source_path}   # run-3dgs 导出的 COLMAP-style source
{output_path}   # 3DGS trainer 输出目录，默认 scene/reconstruction/3dgs
{project_root}
{work_dir}
{scene_id}
```

如果只想准备 source 和命令，不启动训练：

```bash
python -m video2mesh.cli run-3dgs \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --command-template "python /path/to/gaussian-splatting/train.py -s {source_path} -m {output_path}" \
  --prepare-only
```

注意：`run-3dgs` 是外部 trainer 适配器，不内置完整 3DGS 训练算法。远端现在已经安装并验证 `gsplat==1.5.3` 的 CUDA rasterization/backward，说明底层 splat 渲染/梯度 runtime 可用；但真实训练仍需要基于 `gsplat` 写一个训练循环，或接入现成 gsplat/nerfstudio/gaussian-splatting trainer，然后通过 `--command-template` 调用。

`gsplat` 远端 smoke 信息：

```text
python package: gsplat==1.5.3
cuda smoke: gsplat.rasterization + loss.backward passed
render_shape: [1, 64, 64, 3]
compile note: first JIT build of gsplat_cuda took about 634s, then uses cache
required env: CUDA_HOME=/usr/local/cuda-12.4, CPATH includes $CUDA_HOME/targets/x86_64-linux/include
```

内置最小 trainer：

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli train-gsplat \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --iterations 200 \
  --max-frames 20 \
  --max-points 50000
```

输出会注册到：

```text
scene/reconstruction/3dgs/point_cloud/iteration_<N>/point_cloud.ply
scene/reconstruction/3dgs/video2mesh_gsplat_train.json
```

当前 `train-gsplat` 从点云初始化 Gaussian 的 position/color/scale/opacity，用 L1 image reconstruction loss 优化。它主要用于验证真实 3DGS 训练接口和 semantic transfer 链路；要达到生产质量，还需要增加 densification、pruning、multi-scale schedule、SH appearance、曝光/白平衡处理和更完整的相机模型支持。

训练或注册 3DGS 后，可以把 splat 按项目相机回渲染到原始帧，生成快速 QA 图和数值指标：

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli render-gsplat-preview \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-frames 3
```

输出位置：

```text
simulator_assets/gsplat_preview/preview_manifest.json
simulator_assets/gsplat_preview/<frame_id>/render.png
simulator_assets/gsplat_preview/<frame_id>/target.png
simulator_assets/gsplat_preview/<frame_id>/error.png
```

也可以在一键 pipeline 中加 `--render-gsplat-preview`，让训练或注册 3DGS 后自动生成预览。远端 `run_pipeline_gsplat_preview_smoke` 已验证该开关：`train_gsplat -> render_gsplat_preview -> fuse_masks -> ... -> validate` 完整跑通，预览 1 帧，`mean_l1=0.122959`，`mean_psnr=13.985`。

如果已有 3DGS 训练输出目录，注册到 Video2Mesh：

```bash
python -m video2mesh.cli register-3dgs \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --path /path/to/gaussian_splatting/output \
  --mode copy
```

该命令会尝试寻找 `point_cloud.ply` 或任意 `.ply`，并记录到 `manifest.json` 的 `scene_3dgs_ply`。

如果使用 MASt3R-SLAM，可以先运行：

```bash
cd /root/autodl-tmp/workspace/MASt3R-SLAM
source /root/autodl-tmp/workspace/Video2Mesh/remote_mast3r_env.sh
python main.py \
  --dataset /path/to/video.mp4 \
  --config config/base.yaml \
  --save-as <scene_id> \
  --no-viz
```

MASt3R-SLAM 默认会保存：

```text
logs/<scene_id>/<sequence_name>.txt
logs/<scene_id>/<sequence_name>.ply
logs/<scene_id>/keyframes/<sequence_name>/*.png
```

其中 `.txt` 每行是：

```text
timestamp x y z qx qy qz qw
```

这是 MASt3R-SLAM 的 `T_WC` camera-to-world 位姿。导入 Video2Mesh：

```bash
python -m video2mesh.cli import-mast3r-slam \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --trajectory /root/autodl-tmp/workspace/MASt3R-SLAM/logs/<scene_id>/<sequence_name>.txt \
  --reconstruction-ply /root/autodl-tmp/workspace/MASt3R-SLAM/logs/<scene_id>/<sequence_name>.ply \
  --frames-dir /root/autodl-tmp/workspace/MASt3R-SLAM/logs/<scene_id>/keyframes/<sequence_name> \
  --width 640 \
  --height 480
```

如果有真实标定，建议传：

```bash
--fx <fx> --fy <fy> --cx <cx> --cy <cy>
```

否则 CLI 会按图像大小估计内参，仅适合先跑通工程链路，mask 投影精度会受影响。

也可以直接让 Video2Mesh 调用 MASt3R-SLAM 并自动导入结果：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
python -m video2mesh.cli init \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scene-id <scene_id> \
  --video /path/to/video.mp4

python -m video2mesh.cli run-mast3r-slam \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --video /path/to/video.mp4 \
  --config config/base.yaml \
  --width 640 \
  --height 480
```

`run-mast3r-slam` 会：

1. 在 `/root/autodl-tmp/workspace/MASt3R-SLAM` 下运行 `main.py --no-viz`。
2. 保存 MASt3R-SLAM 日志到 `exports/<scene_id>/logs/mast3r_slam_run.log`。
3. 自动定位 `logs/<scene_id>/<sequence_name>.txt`、`.ply`、`keyframes/`。
4. 调用 `import-mast3r-slam` 写入 `scene/cameras/camera_info.json`、`scene/reconstruction/point_cloud.ply`、`scene/frames/`。

当前远端已用合成 PNG 序列 smoke 验证通过：MASt3R-SLAM 权重加载、CUDA 扩展、输出保存和 Video2Mesh 自动导入都能执行。该 smoke 不是完整真实扫描质量评估，只证明工程入口可运行。

### Phase B：帧级 2D segmentation/tracking

这一阶段可以接 SAM2、Grounded-SAM、DEVA、XMem 或手工标注。输出放到：

```text
masks/2d/<object_id>/<frame_id>.png
```

也支持：

```text
masks/2d/<frame_id>_<object_id>.png
```

可选写入物体标签：

```json
{
  "chair_01": {
    "name": "chair",
    "category": "chair",
    "description": "wooden chair beside the table"
  }
}
```

文件路径：

```text
masks/object_labels.json
```

当前原型里已经提供两个可替换的半自动适配器：

- `auto-prompts`：从一张代表帧自动生成 bbox prompt。可用 OpenCV 前景轮廓，也可用 SAM Automatic Mask Generator；会输出 prompt JSON 和带框预览图。
- `track-masks`：给每个物体在一帧上的 bbox prompt 后，用 OpenCV template matching 做跨帧位置传播；mask 生成可以选择 OpenCV GrabCut/矩形 fallback，也可以在安装 `segment-anything` 并提供 checkpoint 后，用 SAM bbox prompt 精修每帧 mask。

这两个适配器不是最终生产质量的 SAM2/DEVA/Grounded-SAM，但可以把工程链路从“手工放 mask”推进到“自动生成候选 prompt，再形成标准 mask 目录”。真实扫描视频里仍应检查 `auto_prompts_preview.png`，必要时手工删改 prompt 或调阈值。

自动生成 prompts：

```bash
python -m video2mesh.cli auto-prompts \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --method opencv \
  --max-objects 12 \
  --overwrite
```

如果使用 SAM Automatic Mask Generator：

```bash
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli auto-prompts \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --method sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b \
  --sam-device cuda \
  --max-objects 12 \
  --max-area-ratio 0.2 \
  --overwrite
```

`auto-prompts` 输出：

```text
masks/auto_prompts.json
masks/auto_prompts_preview.png
masks/object_labels.json
```

`--max-area-ratio`、`--min-area-ratio`、`--nms-iou` 和 `--containment-*` 用于过滤背景大块区域、重复框和包住多个小物体的大合并框。`auto_prompts.json` 里的 `objects` 字段兼容 `track-masks --prompts`。

在一键 pipeline 中可以让它自动接到 `track-masks`：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --auto-prompts \
  --auto-prompt-method opencv \
  --mask-backend opencv
```

prompt 示例：

```json
{
  "objects": [
    {
      "id": "chair_01",
      "name": "chair",
      "category": "chair",
      "description": "wooden chair beside the table",
      "frame_id": "000000",
      "bbox": [120, 160, 260, 360]
    }
  ]
}
```

运行：

```bash
python -m video2mesh.cli track-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --prompts /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>/masks/prompts.json
```

如果只想用矩形 bbox mask，不跑 GrabCut：

```bash
python -m video2mesh.cli track-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --prompts /path/to/prompts.json \
  --no-grabcut
```

如果已经安装 Segment Anything 并下载 checkpoint，可以用 SAM 做 bbox prompt mask refinement：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
python -m pip install segment-anything==1.0
mkdir -p /root/autodl-tmp/checkpoints/sam
cd /root/autodl-tmp/checkpoints/sam
wget -c https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth -O sam_vit_b_01ec64.pth
```

远端环境已经完成这一步：`segment-anything==1.0` 已安装，SAM ViT-B checkpoint 已完整下载到 `/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth`。`track_masks_sam_smoke` 已验证真实 SAM bbox refinement 能在 CUDA 上生成帧级 mask，并可继续接 `fuse-masks -> export-splat-masks -> export-object-mask-clouds -> select-frames -> prepare-object-images`。

ViT-B checkpoint 下载完成后运行：

```bash
python -m video2mesh.cli track-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --prompts /path/to/prompts.json \
  --mask-backend sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b \
  --no-sam-multimask
```

真实 SAM smoke 的结果是：`backend == sam`，`model_type == vit_b`，`device == cuda`，两个样例物体各生成 `3` 张 mask，SAM score 约 `0.98-0.996`；融合后 `blue_cube=324`、`red_cube=324` 个 3D mask 点。完整协议闭环也已通过 `validate/evaluate`，但该闭环仍使用 mock 3DGS 和 placeholder object meshes，不代表真实视频 3DGS 训练和真实 mesh 生成质量已经完成。

如果希望有 checkpoint 时用 SAM、没有 checkpoint 时自动回退 OpenCV：

```bash
--mask-backend auto --sam-checkpoint /path/to/sam_checkpoint.pth
```

显式 `--mask-backend sam` 时必须传 `--sam-checkpoint`；这样可以避免误以为已经用了 SAM。

输出：

```text
masks/2d/<object_id>/<frame_id>.png
masks/2d/tracking_manifest.json
masks/object_labels.json
```

如果 object label 来自外部开放词汇检测器或 VLM，可以把结果导入到统一标签文件和 object record：

```bash
python -m video2mesh.cli import-object-labels \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --labels /path/to/object_labels.json
```

`object_labels.json` 可以是 `{object_id: label}` 的 map，也可以是 `{"objects": [...]}` 或 list。每条 label 支持 `name`、`category`、`description`、`aliases`、`open_vocab_labels`、`confidence`、`source`、`vlm` 等字段。这个接口的目标是把当前颜色/编号式自动命名替换成 VLM 可解释语义，同时保持后续 `fuse-masks`、SVPP export 和 simulator bundle 的文件协议不变。

后续可以把 `track-masks` 内部替换为 SAM2/DEVA/XMem 的视频级 mask propagation，但保持上述输出协议不变。

### Phase C：2D mask 融合成 3D object mask

```bash
python -m video2mesh.cli fuse-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --min-votes 2
```

输出：

```text
masks/3d/object_masks.json
masks/3d/<object_id>/point_indices.npy
masks/3d/<object_id>/point_indices.json
objects/<object_id>/object.json
objects/<object_id>/frame_scores.json
```

当前融合方法是 MVP：把点云投影到每一帧，在 2D mask 中命中的可见点给该 object 投票。默认启用基于点云投影的 z-buffer 可见性过滤，避免同一像素后方墙面/背景点误吃到前景物体 mask：

```bash
python -m video2mesh.cli fuse-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --min-votes 2 \
  --occlusion-filter \
  --depth-tolerance 0.03 \
  --relative-depth-tolerance 0.01
```

如果需要回退旧逻辑：

```bash
--no-occlusion-filter
```

这仍不是严格的真实深度/渲染深度遮挡判断，但已经把“帧级语义 mask -> 可见表面 3D object mask”的工程接口跑通了。

为了让每个物体的 3D mask 更容易检查、可视化和给下游使用，可以导出每物体独立 PLY：

```bash
python -m video2mesh.cli export-object-mask-clouds \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>
```

输出：

```text
simulator_assets/object_masks_3d/<object_id>.ply
simulator_assets/object_masks_3d/object_mask_clouds.json
objects/<object_id>/object.json  # 写入 mask_3d_cloud
```

背景结构可以作为另一类 semantic record 加入同一套 3D mask 协议。当前可运行 baseline 会从点云边界启发式推断 floor / ceiling / walls：

```bash
python -m video2mesh.cli infer-background-structure-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --point-cloud /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>/scene/reconstruction/point_cloud_10k.ply \
  --up-axis y \
  --quantile 0.03 \
  --min-points 50
```

输出：

```text
objects/floor/object.json
objects/ceiling/object.json
objects/wall_x_min/object.json
objects/wall_x_max/object.json
objects/wall_z_min/object.json
objects/wall_z_max/object.json
masks/3d/<structure_id>/point_indices.npy
masks/3d/<structure_id>/point_indices.json
simulator_assets/background_structures/background_structures.json
```

这些 object record 的 `asset_role` 是 `background_structure`。它们不是 PLY 里 `object_id=0` 的 unlabeled background，而是有正常 semantic id 的场景结构实例，会进入 semantic splats、object mask clouds、SVPP metadata 和 simulator bundle。与此同时，它们会跳过 `select-frames`、`prepare-object-images`、`reconstruct-object-meshes`、`export-image-blaster` 和 `prepare-multiview-mesh-jobs`，因为 floor/wall/ceiling 不是要送进单物体 mesh API 的可搬动物体。

当前 `infer-background-structure-masks` 只是 axis-boundary heuristic，适合验证协议；真正系统应换成 layout segmentation、SpatialLM/PQ3D、open-vocabulary 3D segmentation 或从 3DGS/mesh 中提取稳定建筑结构。

如果想把 object mask 写入 splat/点云 PLY，运行：

```bash
python -m video2mesh.cli export-splat-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>
```

输出：

```text
simulator_assets/semantic_splats.ply
simulator_assets/semantic_splats_manifest.json
```

`semantic_splats.ply` 会在 vertex 上新增：

```text
property int object_id
```

其中 `0` 是 background，`1..N` 对应每个 object。导出器既支持按点/vertex index 写标签，也支持在 3DGS PLY 的 vertex 顺序和融合点云不一致时，用 nearest-neighbor 做标签转移。

默认 `--transfer-mode auto` 会自动判断：

- `index`：目标 PLY 和 `fuse-masks` 使用的源点云相同，并且 vertex 数一致，直接按点索引写 `object_id`。
- `nearest`：目标 PLY 是另一个 3DGS/splat/点云文件，vertex 数或顺序不一致，则按 XYZ 最近邻把源点云上的 object labels 转移到目标 vertex。

可以显式指定：

```bash
python -m video2mesh.cli export-splat-masks \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --splat-ply /path/to/3dgs/point_cloud.ply \
  --mask-source-ply /path/to/fusion/source_point_cloud.ply \
  --transfer-mode nearest \
  --max-transfer-distance 0.05
```

`--max-transfer-distance` 会把离任何源点都太远的 splat/vertex 标为 background，避免远处漂浮点继承错误物体标签。

导出器支持两种 PLY 路径：

- ASCII PLY：保留原始 vertex 字段并追加 `object_id`。
- Open3D 可读的 binary PLY：读取 XYZ/RGB 后重写为 ASCII PLY，并追加 `object_id`。这已经用 MASt3R-SLAM 生成的 binary `.ply` 做过 smoke test。

导出 semantic splats 后，可以把每个 `object_id` 映射成固定颜色，并按相机位姿投影回原始帧做 QA：

```bash
python -m video2mesh.cli render-semantic-preview \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-frames 3 \
  --max-points-per-frame 5000
```

输出：

```text
simulator_assets/semantic_preview/semantic_splats_colored.ply
simulator_assets/semantic_preview/semantic_preview.json
simulator_assets/semantic_preview/<frame_id>/semantic_overlay.png
```

`semantic_preview.json` 会记录 legend、每帧 projected/visible/drawn label counts、foreground projection ratio 等指标。这个检查回答的是：“3D semantic mask 是否真的落回到视频中的对应物体上”。如果 overlay 明显错位，通常应该先回头检查相机位姿、坐标系、内参、mask tracking 或 3DGS/点云的 label transfer。

后续升级方向：

- 用真实深度图或 splat 渲染深度替换点云 z-buffer，进一步提升 occlusion-aware voting。
- 对 3DGS 的每个 Gaussian 保存更丰富的 instance logits，而不仅是离散 `object_id`。
- 用 CRF/graph smoothing/segment voting 清理噪声。
- 使用 PQ3D 或类似模型生成点云/segment-level instance masks 作为先验。

### Phase D：为每个物体自动选帧

```bash
python -m video2mesh.cli select-frames \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --top-k 5
```

评分因子：

- `hit_points`：该帧中投票命中的 3D 点数量。
- `mask_area`：2D mask 面积。
- `sharpness`：图像 Laplacian 方差。

输出：

```text
objects/<object_id>/selected_frames/
objects/<object_id>/object.json
simulator_assets/selected_frames.json
```

`select-frames` 只处理 `asset_role=object` 的前景物体。`asset_role=background_structure` 的 floor/wall/ceiling 会保留 3D mask 和 semantic id，但不会要求 selected frames。

为了让单物体 mesh 生成更干净，建议再把 selected frames 按 2D mask 裁剪成单物体参考图：

```bash
python -m video2mesh.cli prepare-object-images \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --top-k 3 \
  --transparent
```

输出：

```text
objects/<object_id>/object_images/
objects/<object_id>/reference.png
simulator_assets/object_images.json
```

默认会使用 2D mask 的 foreground bbox，加 padding 后裁成方形 PNG；`--transparent` 会保留 alpha 背景。`objects/<object_id>/reference.png` 会作为 image-blaster 的主输入，top-k object crops 会作为 evidence 一起写入。

### Phase E：导出 image-blaster 资产目录

```bash
python -m video2mesh.cli export-image-blaster \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --image-blaster-root /root/autodl-tmp/workspace/Video2Mesh/image-blaster \
  --world <scene_id>
```

输出：

```text
image-blaster/worlds/<scene_id>/source/video2mesh_manifest.json
image-blaster/worlds/<scene_id>/output/<object_id>/object.json
image-blaster/worlds/<scene_id>/output/<object_id>/source.png
image-blaster/worlds/<scene_id>/output/<object_id>/video2mesh_object_images/*.png
```

`export-image-blaster` 默认会自动运行 `prepare-object-images`，并优先使用 masked object crop，而不是整张 selected frame。需要回退整帧时可以传 `--no-use-object-crop`。

生成 mesh 命令：

```bash
python -m video2mesh.cli mesh-commands \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --image-blaster-root /root/autodl-tmp/workspace/Video2Mesh/image-blaster \
  --provider hunyuan
```

这会写入：

```text
simulator_assets/mesh_generation_commands.sh
```

确认 FAL/API key 配好后，可以加 `--run` 执行。默认不自动调用外部生成 API，避免没有 key 时中断整个 pipeline。

image-blaster 生成成功后，模型通常会落在：

```text
image-blaster/worlds/<scene_id>/output/<object_id>/<N>-<object_id>.glb
image-blaster/worlds/<scene_id>/output/<object_id>/<N>-<object_id>.obj
image-blaster/worlds/<scene_id>/output/<object_id>/.<N>-<object_id>__model-request.json
```

其中隐藏的 `__model-request.json` 保存 provider、request id、输出文件等元数据。

如果不想绑定 image-blaster/FAL，也可以只把每个前景物体的 selected frames、object crops、3D mask bbox 和预期输出位置整理成外部 mesh job：

```bash
python -m video2mesh.cli prepare-multiview-mesh-jobs \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-frames 3 \
  --command-template "python reconstruct_object.py --job {job_path} --output {mesh_output}" \
  --skip-missing
```

输出：

```text
simulator_assets/multiview_mesh_jobs/multiview_mesh_jobs.json
simulator_assets/multiview_mesh_jobs/jobs/<object_id>.json
simulator_assets/multiview_mesh_jobs/run_mesh_jobs.sh
simulator_assets/multiview_mesh_jobs/meshes/<object_id>.<mesh_format>
```

`--command-template` 支持 `{job_path}`、`{object_id}`、`{output_dir}`、`{mesh_output}`、`{primary_frame}`、`{primary_crop}`、`{image_paths}`、`{crop_paths}`、`{project_root}`。默认只写 job 和脚本，不会执行外部模型；传 `--run` 才会真正调用命令。外部 mesh 生成结束后，可以用：

```bash
python -m video2mesh.cli import-object-meshes \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --mesh-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>/simulator_assets/multiview_mesh_jobs/meshes \
  --skip-missing
```

把 mesh 回流到 `simulator_assets/object_meshes.json`。该路线会跳过 `background_structure`，只为可作为独立资产的前景物体准备 mesh job。

### Phase F：导入 object mesh 并导出仿真器资产包

Phase F 有两条互补路线。

第一条是生成式资产路线：将 image-blaster/FAL/Hunyuan/Meshy 生成的单物体 mesh 回流到 Video2Mesh：

```bash
python -m video2mesh.cli import-object-meshes \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --image-blaster-root /root/autodl-tmp/workspace/Video2Mesh/image-blaster \
  --world <scene_id>
```

该命令会为每个 `objects/<object_id>/object.json` 写入 `mesh_asset` 字段，并默认把 mesh 拷贝到：

```text
simulator_assets/objects/<object_id>/<mesh_file>
simulator_assets/object_meshes.json
```

如果 mesh 来自别的目录，也可以用：

```bash
python -m video2mesh.cli import-object-meshes \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --mesh-root /path/to/object_meshes
```

第二条是几何 baseline 路线：如果已经有 `export-object-mask-clouds` 生成的物体级 3D mask point cloud，可以直接从点云重建每个物体的 mesh：

```bash
python -m video2mesh.cli reconstruct-object-meshes \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --method auto \
  --format obj
```

该命令会读取：

```text
simulator_assets/object_masks_3d/<object_id>.ply
```

并输出：

```text
simulator_assets/reconstructed_meshes/<object_id>/<object_id>.obj
simulator_assets/reconstructed_meshes/<object_id>/reconstruction.json
simulator_assets/objects/<object_id>/<object_id>.obj
simulator_assets/object_meshes.json
```

`--method auto` 会依次尝试 `alpha_shape`、`ball_pivoting`、`convex_hull`，必要时退到 `bbox`。它的优点是保持重建场景里的尺度和物体位置，适合作为仿真资产的几何 baseline；缺点是质量受 3D mask 点云密度、遮挡和表面完整性影响，稀疏/单面点云可能只得到粗糙表面或 bbox。

注意这里有一个坐标语义差异：

- `import-object-meshes` 导入的 image-blaster/FAL/Hunyuan/Meshy mesh 默认视为 `object_local`，也就是模型自身围绕局部原点，后续由 `pose.position` 放到场景里。
- `reconstruct-object-meshes` 从 3D mask cloud 直接生成的 mesh 默认视为 `video2mesh_scene`，顶点本身已经在场景坐标中。

因此，后续 `export-simulator-assets` 会对 `object_mask_cloud_reconstruction` 来源的 mesh 自动生成一个 `*_local.obj`/`*_local.<ext>` 副本：用 3D mask bbox center 把顶点平移到物体局部坐标，再把 `pose.position` 设置为该 bbox center。这样可避免仿真器 adapter 里出现“mesh 顶点已经在世界坐标，同时 body 又放到 bbox center”的双重位移问题。

最后导出仿真器资产包：

```bash
python -m video2mesh.cli export-simulator-assets \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --ascii-meshes
```

输出：

```text
simulator_assets/simulator_asset_bundle.json
simulator_assets/objects/<object_id>/object_asset.json
simulator_assets/objects/<object_id>/<mesh_file>
simulator_assets/objects/<object_id>/<mesh_stem>_local.<ext>  # 对 scene-coordinate mask mesh 自动生成
```

`simulator_asset_bundle.json` 会包含：

- 场景级资产：frames、camera_info、point_cloud、scene_3dgs、semantic_splats。
- 每个物体的 `object_id`、`semantic_id`、类别、描述。
- mesh 路径、mesh 格式、mesh/source coordinate frame、3D mask、selected frames、primary frame。
- 由 3D mask bbox 估计的初始 pose、bbox size 和 scale。
- mesh QA：source/exported mesh 的 vertex/triangle 数、bbox、surface area、manifold/watertight 标记、source mesh 与 mask bbox 的 center/size 对齐摘要、是否做了 object-local localization。
- 仿真器占位字段：body type、collider、mass、material。

注意：当前 pose/scale 来自重建坐标和 3D mask bbox，是工程初值；真实仿真还需要校准尺度、上方向、坐标系、碰撞体和物理参数。若 mesh 已在 `export-simulator-assets` 阶段被 localize，bundle 中该物体的 `pose.scale` 会写成 `[1, 1, 1]`，避免把 `scene_scale` 重复乘到已经 bake 过尺度的 mesh 上。

导出 bundle 后，可以先写入尺度、上方向和估算物理字段：

```bash
python -m video2mesh.cli calibrate-simulator-assets \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --scale-to-meters 1.0 \
  --no-scale-calibrated \
  --up-axis y \
  --estimate-physics \
  --overwrite-physics
```

输出：

```text
simulator_assets/simulator_calibration.json
simulator_assets/simulator_asset_bundle.json  # 更新 coordinate_system / pose / physics
```

如果没有真实标尺，`--scale-to-meters 1.0 --no-scale-calibrated` 只是协议层假设，QA 仍会提示 scale 未校准。若知道某个物体或背景结构的真实长度，可以用 reference object 自动反推真实比例：

```bash
python -m video2mesh.cli calibrate-simulator-assets \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --reference-object chair_01 \
  --reference-axis longest \
  --reference-length-m 0.82 \
  --up-axis y \
  --estimate-physics \
  --overwrite-physics
```

这会把 `coordinate_system.scale_calibrated` 标为 true，并按 bbox 体积和默认密度估算前景物体 `mass_kg`、`material.friction`、`restitution` 等字段。背景结构会保持 static，通常只写 box collider 和 surface material。所有这些物理字段仍然是工程初值，不等于最终仿真任务的真实质量、摩擦和碰撞体。

导出后建议跑一次 simulator-readiness QA：

```bash
python -m video2mesh.cli qa-simulator-assets \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-issues 20
```

输出：

```text
simulator_assets/simulator_asset_qa.json
```

QA 会检查 mesh 是否存在且可读、vertex/triangle 数是否太少、mesh 是否 watertight/manifold、mesh bbox 与 3D mask bbox 的 center/size 是否大致对齐、是否缺少 scale calibration、up axis、mass、collider、body_type。背景结构允许没有 object mesh，并以 static scene structure / box collider 的占位方式进入 simulator bundle。

CI 或批处理可以把更严格的要求打开：

```bash
python -m video2mesh.cli qa-simulator-assets \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --require-physics \
  --require-scale-calibration \
  --fail-on-required
```

如果要生成目标仿真器的导入骨架，可以继续导出 adapter：

```bash
python -m video2mesh.cli export-simulator-adapter \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --format mujoco isaac unity
```

输出：

```text
simulator_assets/adapters/simulator_adapters.json
simulator_assets/adapters/assets/<object_id>/<mesh_file>
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/isaac/isaac_adapter.json
simulator_assets/adapters/unity/unity_adapter.json
```

`export-simulator-adapter` 会默认把 mesh 复制到 `simulator_assets/adapters/assets/`，并在 MuJoCo XML / Isaac JSON / Unity JSON 中使用相对路径。它只是仿真器导入 skeleton：真实使用时仍要校准 meters、up-axis、碰撞体、质量、摩擦和材质。

### Phase G：验证工程产物完整性

完整链路跑完后，用 `validate` 做项目审计：

```bash
python -m video2mesh.cli validate \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --output /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>/simulator_assets/validation_report.json
```

它会检查：

- frames、camera_info、point_cloud。
- scene 3DGS / splat PLY。
- objects 和 object-level 3D masks。
- per-object 3D mask PLY clouds。
- semantic splats PLY / manifest。
- object semantic labels（recommended）。
- background structures（recommended）。
- selected frames 和 masked object reference images。
- image-blaster world、object meshes。
- SVPP-style scene export（recommended）。
- simulator asset bundle。
- simulator adapters（recommended）。
- simulator asset QA（recommended）。
- simulator calibration（recommended）。

`validate` 只证明工程产物是否齐全；真实质量还要继续评估重建清晰度、mask 一致性、mesh 几何质量、尺度/pose 和仿真器导入效果。

如果希望看到更细的阶段 readiness 和物体级质量摘要，运行：

```bash
python -m video2mesh.cli evaluate \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>
```

默认输出：

```text
simulator_assets/evaluation_report.json
```

`evaluate` 会聚合：

- 场景帧数、相机外参数量、点云/3DGS PLY vertex 数。
- `render-reconstruction-preview` 生成的 camera/point-cloud 对齐 QA：有效帧数、点投影比例、可见点比例、投影像素覆盖率和输出目录。
- `render-gsplat-preview` 生成的回渲染 QA：preview frame 数、mean L1、mean PSNR 和输出目录。
- 2D mask 数量、3D mask fusion 配置和 skipped mask 数量。
- semantic splats 的 label transfer 信息，以及 `render-semantic-preview` 生成的彩色语义 PLY、object-level 3D mask 投影 summary 和输出目录。
- 每个物体的 point count、bbox、selected frame 数、object crop 数、mask cloud 是否存在、mesh 是否存在、simulator mesh 是否存在、simulator mesh coordinate frame 和 mesh QA/localization 摘要。
- semantic labeling 的标签文件数量和非 `unknown` 类别数量。
- mesh generation 的 object mesh index、缺失列表和 `prepare-multiview-mesh-jobs` 的 job 数量。
- SceneVerse++ / SVPP 导出目录和 `metadata.json` instance 数量。
- simulator asset bundle 是否存在、mesh 缺失列表、coordinate system、calibration report、simulator QA summary、validation 缺口。

这个命令默认即使发现问题也返回成功，适合批量生成报告；如果要在 CI/脚本里把缺口当失败，可以加：

```bash
--fail-on-issues
```

如果要在调用 image-blaster/FAL 之前做人工质检，可以导出 review pack：

```bash
python -m video2mesh.cli export-review-pack \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --max-scene-frames 3 \
  --max-frames 3
```

输出：

```text
simulator_assets/review/index.html
simulator_assets/review/review_pack.json
```

HTML 顶部会展示场景级 QA，包括 `auto_prompts_preview.png`、点云投影 overlay、semantic 3D mask projection overlay、3DGS render preview 和 error preview；下面再按物体展示 primary object crop、selected frame thumbnails、3D mask 点数、mask cloud 点数、原始 mesh 状态、simulator mesh 坐标系、是否 localize 和当前 issues。真实视频中建议先打开这个页面检查相机/点云对齐、3DGS 回渲染、3D semantic mask 投影、mask/crop/mesh pose 是否靠谱，再批量调用付费 mesh API。

如果希望由 Video2Mesh 统一编排各阶段，使用 `run-pipeline`。它会写出：

```text
logs/pipeline_report.json
simulator_assets/validation_report.json
```

`run-pipeline` 默认不会调用 MASt3R-SLAM、外部 3DGS trainer 或外部 mesh API，除非显式传 `--run-mast3r-slam`、`--g3dgs-command-template`、`--run-mesh-commands`。这是为了避免误耗 GPU/API 资源。若已导出 simulator asset bundle，`run-pipeline` 会默认生成 MuJoCo adapter；也可以传 `--simulator-format mujoco isaac unity` 或 `--skip-simulator-adapters`。

## 3. 与两个参考项目的关系

### SceneVersepp

当前复用点：

- `camera_info.json` / `mesh.ply` / `metadata.json` / `data_info.json` 风格。
- `data_processing` 的抽帧和相机可视化入口。
- `SpatialLM` 的点云/layout 推理入口。
- `PQ3D` 的数据生成和 3D instance segmentation 思路。

Video2Mesh 可以把已经融合出的 3D object masks 导出成 SVPP-style scene folder：

```bash
python -m video2mesh.cli export-svpp-metadata \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id>
```

输出：

```text
simulator_assets/svpp/<scene_id>/
  mesh.ply
  camera_info.json
  data_info.json
  metadata.json
  video2mesh_svpp_export.json
```

其中 `metadata.json` 每个实例包含 `point_ids`、`pred_class_name`、`pred_class_id`、bbox、selected frames、mask cloud 和 mesh metadata。`SpatialLM/data_generation/svpp/generate_layout.py` 主要读取 `point_ids + pred_class_name` 来生成 3D boxes；`PQ3D/data_process/generate_dataset.py` 主要读取 `point_ids + pred_class_id` 来生成 point-level instance labels。

SVPP 导出有几条一致性约束需要特别注意：

- `mesh.ply` 当前通常复制的是 Video2Mesh 的 scene point cloud，而不是封闭三角 mesh；`metadata.json[*].point_ids` 必须索引到这个 `mesh.ply` 的 vertex 顺序。
- `object_id` 是 Video2Mesh 内部跨文件 join key，会连接 `objects/<id>/object.json`、semantic PLY manifest、simulator bundle、SVPP metadata 和 image-blaster world。
- semantic PLY / SuperSplat 中的 `semantic_id` 是实例标签，用于区分 object/structure；SVPP 里的 `pred_class_id` 是类别 id，例如 ScanNet20 的 wall/floor/chair，不是实例 id。
- `object_id=0` 或 semantic label `0` 表示 unlabeled background；`floor`、`ceiling`、`wall_*` 这类 `background_structure` 是有独立 `object_id` 和 semantic id 的结构实例。
- 如果要让 SVPP metadata 使用 VLM/open-vocabulary 的新类别，或包含 floor/wall/ceiling 背景结构，应先运行 `import-object-labels` / `infer-background-structure-masks`，再运行 `export-svpp-metadata`。

如果 Video2Mesh 的类别不是 SceneVerse++/ScanNet20 类别，例如 `box`，可以显式映射：

```bash
python -m video2mesh.cli export-svpp-metadata \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/<scene_id> \
  --default-category table
```

也可以传 JSON category map：

```bash
--category-map /path/to/category_map.json
```

当前不假设 SceneVersepp 已经能直接完成：

```text
任意扫描视频 -> 3DGS -> object-level 3D semantic mask
```

这是 Video2Mesh 要补的中间桥接层。

### image-blaster

当前复用点：

- `worlds/<world>/output/<object>/object.json`
- `generate-single-asset.mjs`
- Hunyuan/Meshy via FAL 的单物体 mesh 生成能力。
- React/Three.js viewer 的资产查看能力。

当前 image-blaster 原始输入是单图，不负责视频位姿、跨帧跟踪、3D mask 融合。Video2Mesh 负责给它喂“每个 object 最合适的 selected frame”。

生成后的 `.glb/.obj/.fbx/.stl/.usdz` 会通过 `import-object-meshes` 回流到 Video2Mesh，再由 `export-simulator-assets` 和 3D mask / semantic id / bbox pose 合并成最终仿真资产包。

## 4. 后续真正要攻克的问题

1. 把 MASt3R-SLAM/COLMAP/3DGS 的输出稳定转换成 `camera_info.json + point_cloud.ply + scene_3dgs/`。
2. 让 2D segmentation/tracking 跨帧一致，避免同一个物体 ID 漂移。
3. 用深度一致性改进 2D-to-3D mask fusion。
4. 将点云 object masks 映射到 Gaussian splats，而不是只保存 point indices。
5. 对每个物体用单图、多视角或 masked 3DGS extraction 比较 mesh 质量。
6. 导出仿真器所需的尺度、坐标系、碰撞体、物理属性和 semantic ID。
