# Video2Mesh 远端环境配置状态

日期：2026-06-17  
远端项目路径：`/root/autodl-tmp/workspace/Video2Mesh`  
本地项目路径：`/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh`

## 1. 结论

当前已经在远端服务器上完成了一个可用的 Video2Mesh 基础环境：

- `SceneVersepp` 的数据处理入口、`SpatialLM` 推理入口、`PQ3D` 数据生成入口已经通过 smoke test。
- `image-blaster` 的 Bun/TypeScript 侧已经通过 `typecheck`。
- `MASt3R-SLAM` 已经安装到同一个 venv，官方三个 checkpoint 已下载，`main.py --no-viz` 已通过最小 PNG 序列 smoke test，并能被 Video2Mesh 自动导入。
- 远端 GPU 可用：`NVIDIA GeForce RTX 4080 SUPER`，`torch.cuda.is_available() == True`。
- 主要运行环境放在数据盘：`/root/autodl-tmp/venvs/v2m-svpp`，避免占满系统盘。

注意：用户提供的 conda `base` 环境里 PyTorch/CUDA 是好的，但 `scipy.stats`、`sklearn`、`open3d` 会触发 `RecursionError: maximum recursion depth exceeded`。我尝试重装 `numpy/scipy/scikit-learn` 后仍未解决，所以当前把 `base` 保留为备用 GPU torch 环境，把 SceneVersepp 主执行环境切到干净的 Python 3.11 venv。

## 2. 快速激活

在远端服务器上：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
```

`remote_env.sh` 会设置：

- `WORK=/root/autodl-tmp/workspace/Video2Mesh`
- `TMPDIR=/root/autodl-tmp/tmp`
- `PIP_CACHE_DIR=/root/autodl-tmp/pip-cache`
- `HF_HOME=/root/autodl-tmp/hf`
- `TORCH_HOME=/root/autodl-tmp/torch`
- `CUDA_HOME=/usr/local/cuda-12.4`
- `CPATH=$CUDA_HOME/targets/x86_64-linux/include:...`
- `LIBRARY_PATH` / `LD_LIBRARY_PATH` 指向 CUDA target lib，用于 `gsplat` 等 PyTorch CUDA extension 编译。
- Bun 路径：`/root/autodl-tmp/.bun/bin`
- Python venv：`/root/autodl-tmp/venvs/v2m-svpp`

下载 GitHub/HuggingFace 资源前可手动加速：

```bash
source /etc/network_turbo
```

不建议在普通 pip 镜像安装时长期打开该加速脚本，因为它主要面向 GitHub/HuggingFace。

如果要直接运行 MASt3R-SLAM，也可以使用：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_mast3r_env.sh
```

`remote_mast3r_env.sh` 会额外设置：

- `MAST3R_SLAM_ROOT=/root/autodl-tmp/workspace/MASt3R-SLAM`
- `PYTHONPATH` 指向 MASt3R-SLAM、vendored `mast3r` 和 `dust3r`
- `LD_LIBRARY_PATH` 指向当前 torch 的 shared library 目录

## 3. 已验证的 Python 环境

主环境：

```bash
source /root/autodl-tmp/venvs/v2m-svpp/bin/activate
```

已验证关键包：

- `python 3.11`
- `torch 2.5.1+cu124`
- `torchvision 0.20.1+cu124`
- `torchaudio 2.5.1+cu124`
- `numpy 1.26.4`
- `scipy 1.14.1`
- `scikit-learn 1.6.1`
- `open3d 0.18.0`
- `opencv-python 4.10.0`
- `transformers 4.46.1`
- `pandas 2.2.3`
- `hydra-core 1.3.2`
- `accelerate 1.2.1`
- `fvcore 0.1.5.post20221221`
- `wandb 0.19.1`
- `sentence-transformers 3.3.1`

CUDA 验证通过：

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
print(torch.ones(4, device="cuda").sum().item())
PY
```

输出确认 CUDA 可用，GPU 为 `NVIDIA GeForce RTX 4080 SUPER`。

## 4. SceneVersepp 验证结果

工作目录：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh/SceneVersepp
source /root/autodl-tmp/venvs/v2m-svpp/bin/activate
```

### 4.1 data_processing

以下入口均已通过 `--help`：

```bash
python data_processing/download_videos.py --help
python data_processing/extract_images.py --help
python data_processing/view_camera_poses.py --help
```

这些脚本对应 SceneVerse++ 原始数据形态：

- `data_info.json`
- `video.mp4`
- `camera_info.json`
- `mesh.ply`
- `metadata.json`
- `images/`
- `crop_images/`

用途：

- `download_videos.py`：根据 `data_info.json` 下载 YouTube 视频。
- `extract_images.py`：按 `data_info.json` 抽帧并生成裁剪图。
- `view_camera_poses.py`：用 Open3D 查看 `mesh.ply` 和相机位姿。

### 4.2 SpatialLM

工作目录：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh/SceneVersepp/SpatialLM
export TRANSFORMERS_NO_TF=1
export TRANSFORMERS_NO_FLAX=1
export USE_TF=0
export USE_FLAX=0
export PYTHONPATH=.
```

以下入口已通过：

```bash
python inference.py --help
python eval.py --help
python - <<'PY'
import torch, open3d, sklearn
from spatiallm import Layout
layout = Layout("bbox_0=Bbox(chair,0,0,0,0,1,1,1)")
print("spatiallm_import_ok", len(layout.bboxes), layout.bboxes[0].class_name, torch.cuda.is_available())
PY
```

`inference.py` 的接口说明：

- 输入：点云文件或点云文件夹，参数 `--data_file`
- 输出：layout txt 或输出文件夹，参数 `--output`
- 模型：`--model_path`
- 检测类型：`--detect_type all|arch|object`
- 类别过滤：`--category`

这部分适合后续作为 `3D scene understanding / 3D box layout` 模块。

### 4.3 PQ3D

工作目录：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh/SceneVersepp/PQ3D
export PYTHONPATH=.
```

已通过：

```bash
python data_process/generate_dataset.py --help
```

说明：

- `generate_dataset.py` 是 PQ3D 的数据生成入口。
- 配置文件是 `data_process/config.yaml`。
- 目标输出包括 segment、scan_data、segment_id 等训练中间数据。

`run.py --help` 当前未完全通过，原因不是普通 pip 依赖，而是当前仓库里的 PQ3D 训练代码引用了缺失的包：

```text
ModuleNotFoundError: No module named 'data'
```

具体位置：

```text
PQ3D/trainer/build.py
from data.build import build_dataloader
```

当前 `PQ3D/` 目录下没有 `data/` 包。也就是说，公开仓库里的 PQ3D 训练入口可能是裁剪版、缺子模块，或需要从上游 PQ3D 补齐数据加载代码。

训练阶段还可能需要更重的 CUDA/稀疏卷积扩展：

- `MinkowskiEngine`
- `torch_scatter`
- `pointnet2_utils`
- 可能还有 `spconv` / `flash-attn`

这些没有在当前阶段强行编译安装，因为无数据 smoke test 下收益不高，而且容易耗时很久。

## 5. image-blaster 验证结果

工作目录：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh/image-blaster
export PATH=/root/autodl-tmp/.bun/bin:$PATH
```

Bun 已安装：

```bash
bun --version
# 1.3.14
```

已通过：

```bash
bun install --frozen-lockfile --cache-dir /root/autodl-tmp/.cache/bun
bun run typecheck
bun run build
```

项目结构可用于后续资产对接：

- `worlds/<slug>/source/`
- `worlds/<slug>/output/world/`
- `worlds/<slug>/output/<object>/`
- `.claude/scripts/asset-pipeline/generate-single-asset.mjs`

这部分适合复用为单物体 mesh 生成、资产目录组织和 Three.js viewer。

## 6. MASt3R-SLAM 验证结果

工作目录：

```bash
cd /root/autodl-tmp/workspace/MASt3R-SLAM
source /root/autodl-tmp/workspace/Video2Mesh/remote_mast3r_env.sh
```

已完成：

- 主仓库克隆到 `/root/autodl-tmp/workspace/MASt3R-SLAM`。
- GitLab `thirdparty/eigen` 拉取失败后，已用 GitHub mirror 补齐。
- `thirdparty/in3d/thirdparty/pyimgui/imgui-cpp` 按 `pyimgui` 记录的 gitlink 固定到 Dear ImGui `35b1148`，避免最新 ImGui API 不兼容。
- 在 `/root/autodl-tmp/venvs/v2m-svpp` 里安装并验证：
  - `mast3r`
  - `dust3r`
  - `curope`
  - `asmk`
  - `in3d`
  - `lietorch`
  - `mast3r_slam`
  - `mast3r_slam_backends`
  - `imgui/moderngl/glfw` 可视化依赖
- MASt3R-SLAM 官方 checkpoint 已下载到：

```text
/root/autodl-tmp/workspace/MASt3R-SLAM/checkpoints/
  MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth
  MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_trainingfree.pth
  MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_codebook.pkl
```

已通过入口验证：

```bash
python main.py --help
```

已通过真实模型加载 smoke：

```bash
python main.py \
  --dataset /root/autodl-tmp/workspace/Video2Mesh/exports/mast3r_smoke_frames \
  --config config/eval_no_calib.yaml \
  --save-as v2m_smoke \
  --no-viz
```

该 smoke 成功加载主模型和 retrieval 模型，并写出：

```text
/root/autodl-tmp/workspace/MASt3R-SLAM/logs/v2m_smoke/mast3r_smoke_frames.txt
/root/autodl-tmp/workspace/MASt3R-SLAM/logs/v2m_smoke/mast3r_smoke_frames.ply
/root/autodl-tmp/workspace/MASt3R-SLAM/logs/v2m_smoke/keyframes/mast3r_smoke_frames/0.0.png
```

进一步验证了 Video2Mesh wrapper：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
python -m video2mesh.cli run-mast3r-slam \
  --project-root /root/autodl-tmp/workspace/Video2Mesh/exports/mast3r_wrapper_imported \
  --dataset /root/autodl-tmp/workspace/Video2Mesh/exports/mast3r_smoke_frames \
  --config config/eval_no_calib.yaml \
  --save-as v2m_wrapper_smoke \
  --width 640 --height 480 --fx 500 --fy 500 --cx 320 --cy 240
```

结果：

- 自动调用 MASt3R-SLAM。
- 自动导入 trajectory、PLY、keyframes。
- 写入 `scene/cameras/camera_info.json`。
- 写入 `scene/reconstruction/point_cloud.ply`。
- 写入 `scene/frames/000000.png`。
- `manifest.json` 中 `external_stages.video_to_3dgs.status == imported_mast3r_slam`。

注意：这个 smoke 使用合成短 PNG 序列，只证明环境和工程入口可运行，不代表真实扫描视频的重建质量已经评估完成。

## 7. 当前限制

### 7.1 base 环境限制

`base` 环境：

```bash
/root/miniconda3/bin/python
```

可用：

- `torch 2.5.1+cu124`
- CUDA 可用
- `transformers` 可 import

异常：

- `import scipy.stats` 失败
- `import sklearn` 失败
- `import open3d` 失败
- 错误为 `RecursionError: maximum recursion depth exceeded`

因此不要用 `base` 跑 SceneVersepp 的 Open3D/Sklearn/SpatialLM 全链路；当前建议用 `/root/autodl-tmp/venvs/v2m-svpp`。

### 7.2 数据限制

仓库本身没有内置完整样例数据。真正跑 SceneVersepp 需要准备符合 SVPP 格式的数据：

```text
<dataset_root>/<scene_name>/
  data_info.json
  mesh.ply
  metadata.json
  camera_info.json
  video.mp4
```

如果使用官方数据，需要按 README 从 HuggingFace 下载。

### 7.3 PQ3D 训练限制

PQ3D 的数据生成入口可用，但训练入口当前缺 `PQ3D/data/` 包。要继续训练或微调，需要：

1. 检查上游 PQ3D 是否有 `data/` 模块。
2. 补齐缺失训练代码或修正 import 路径。
3. 再安装/编译 `MinkowskiEngine`、`torch_scatter`、`pointnet2` 等重依赖。

## 8. 推荐下一步

### Phase A：拿一个最小 SVPP 风格样例

准备一个 scene：

```text
/root/autodl-tmp/data/svpp_miniset/<scene_name>/
  data_info.json
  mesh.ply
  metadata.json
  camera_info.json
  video.mp4
```

然后跑：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
cd SceneVersepp
python data_processing/extract_images.py /root/autodl-tmp/data/svpp_miniset --scene-name <scene_name> --overwrite
python data_processing/view_camera_poses.py /root/autodl-tmp/data/svpp_miniset --scene-name <scene_name> --max-cameras 50
```

### Phase B：跑 SpatialLM 点云/layout 推理

先把 scene mesh 或点云转成 SpatialLM 期望的 `.ply/.pcd` 输入，再跑：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh/SceneVersepp/SpatialLM
source /root/autodl-tmp/venvs/v2m-svpp/bin/activate
export PYTHONPATH=.
python inference.py \
  --data_file /path/to/input_point_cloud.ply \
  --output /root/autodl-tmp/outputs/spatiallm_layout.txt \
  --model_path /path/to/spatiallm_checkpoint
```

需要先下载或放置 SpatialLM checkpoint。

### Phase C：桥接 image-blaster

建议新增一个中间目录：

```text
/root/autodl-tmp/workspace/Video2Mesh/exports/<scene_slug>/
  scene_3dgs/
  object_masks/
  selected_frames/
  object_meshes/
  simulator_assets/
```

后续桥接逻辑：

1. 视频重建得到 3DGS、相机位姿、稀疏/稠密点云。
2. 2D segmentation/tracking 得到帧级物体 mask。
3. 用位姿把 2D mask 融合到 3DGS/点云，得到 object-level 3D mask。
4. 每个 object 根据可见面积、清晰度、遮挡程度选帧。
5. 把选中的单图或多视角帧送入 image-blaster/Hunyuan/Meshy/FAL 生成 mesh。
6. 导出 mesh、材质、pose、scale、semantic_id、collider，作为仿真器资产包。

## 9. 常用命令速查

连接服务器：

```bash
ssh -p 14225 root@connect.westd.seetacloud.com
```

激活环境：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
```

验证 SceneVersepp：

```bash
cd $WORK/SceneVersepp
python data_processing/download_videos.py --help
python data_processing/extract_images.py --help
python data_processing/view_camera_poses.py --help

cd $WORK/SceneVersepp/SpatialLM
PYTHONPATH=. python inference.py --help
PYTHONPATH=. python eval.py --help

cd $WORK/SceneVersepp/PQ3D
PYTHONPATH=. python data_process/generate_dataset.py --help
```

验证 image-blaster：

```bash
cd $WORK/image-blaster
bun run typecheck
bun run build
```

查看磁盘：

```bash
df -h / /root/autodl-tmp
du -sh /root/autodl-tmp/venvs/v2m-svpp /root/autodl-tmp/pip-cache /root/autodl-tmp/.bun
```

## 10. Video2Mesh 原型层新增能力

根目录现在新增了 `video2mesh` Python CLI，用来把真实重建工具和两个参考项目接起来：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source remote_env.sh
python -m video2mesh.cli --help
```

已在远端验证通过的命令：

```bash
python -m video2mesh.cli make-sample --project-root exports/synthetic_room_v3 --scene-id synthetic_room_v3
python -m video2mesh.cli run-local --project-root exports/synthetic_room_v3 --image-blaster-root image-blaster --world synthetic_room_v3
python -m video2mesh.cli export-splat-masks --project-root exports/synthetic_room_v3
python -m video2mesh.cli make-colmap-sample --output-dir tmp_colmap_sample
python -m video2mesh.cli import-colmap --project-root exports/colmap_import_sample --sparse-dir tmp_colmap_sample --images-dir tmp_colmap_sample/images
python -m video2mesh.cli track-masks --project-root exports/track_masks_smoke --prompts exports/track_masks_smoke/masks/prompts.json --no-grabcut
python -m video2mesh.cli import-object-meshes --project-root exports/sim_asset_smoke_tail --image-blaster-root image-blaster --world sim_asset_smoke_tail
python -m video2mesh.cli export-simulator-assets --project-root exports/sim_asset_smoke_tail
python -m video2mesh.cli export-splat-masks --project-root exports/semantic_transfer_smoke --splat-ply exports/semantic_transfer_smoke/scene/reconstruction/mismatched_splats.ply --transfer-mode auto --max-transfer-distance 0.05
python -m video2mesh.cli export-colmap --project-root exports/export_colmap_smoke --output-dir exports/export_colmap_smoke/exports/colmap_text
python -m video2mesh.cli run-3dgs --project-root exports/run_3dgs_smoke --command-template "<external 3DGS trainer command using {source_path} and {output_path}>"
python -m video2mesh.cli prepare-object-images --project-root exports/object_crop_smoke --top-k 3 --transparent
python -m video2mesh.cli validate --project-root exports/end_to_end_smoke --output exports/end_to_end_smoke/simulator_assets/validation_report.json
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_smoke --scene-id run_pipeline_smoke --world run_pipeline_smoke --make-sample --g3dgs-command-template "<mock or real 3DGS command using {source_path}/{output_path}>" --create-placeholder-meshes
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_mast3r_smoke --scene-id run_pipeline_mast3r_smoke --dataset exports/mast3r_smoke_frames --run-mast3r-slam --mast3r-config config/eval_no_calib.yaml --width 640 --height 480 --fx 500 --fy 500 --cx 320 --cy 240 --skip-fuse-masks --skip-export-splat-masks --skip-select-frames --skip-object-images --skip-export-image-blaster --skip-import-meshes --skip-simulator-assets --allow-incomplete
python -m video2mesh.cli fuse-masks --project-root exports/occlusion_fusion_smoke --occlusion-filter --depth-tolerance 0.01 --relative-depth-tolerance 0.0
python -m video2mesh.cli export-object-mask-clouds --project-root exports/end_to_end_smoke
python -m video2mesh.cli evaluate --project-root exports/end_to_end_smoke
python -m video2mesh.cli export-svpp-metadata --project-root exports/end_to_end_smoke --default-category table
python -m video2mesh.cli export-review-pack --project-root exports/end_to_end_smoke --max-frames 2
python -m video2mesh.cli export-review-pack --project-root exports/run_pipeline_scan_video_full_smoke --max-frames 2 --max-scene-frames 2
python -m video2mesh.cli export-simulator-adapter --project-root exports/end_to_end_smoke --format mujoco isaac unity
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_adapter_smoke --scene-id run_pipeline_adapter_smoke --world run_pipeline_adapter_smoke --make-sample --g3dgs-command-template "<mock or real 3DGS command using {source_path}/{output_path}>" --create-placeholder-meshes --simulator-format mujoco isaac unity
python -m video2mesh.cli track-masks --project-root exports/track_masks_auto_smoke --prompts exports/track_masks_auto_smoke/masks/prompts.json --mask-backend auto --no-grabcut
python -m video2mesh.cli track-masks --project-root exports/track_masks_sam_smoke --prompts exports/track_masks_sam_smoke/masks/prompts.json --mask-backend sam --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth --sam-model-type vit_b --no-sam-multimask
python -m video2mesh.cli auto-prompts --project-root exports/auto_prompts_preview_smoke --method opencv --max-objects 4 --overwrite
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli auto-prompts --project-root exports/auto_prompts_sam_preview_smoke --method sam --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth --sam-model-type vit_b --sam-device cuda --max-objects 4 --max-area-ratio 0.2 --overwrite
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_auto_prompts_preview_smoke --scene-id run_pipeline_auto_prompts_preview_smoke --world run_pipeline_auto_prompts_preview_smoke --make-sample --g3dgs-command-template "<mock or real 3DGS command using {source_path}/{output_path}>" --auto-prompts --auto-prompt-method opencv --auto-prompt-max-objects 4 --mask-backend opencv --transfer-mode nearest --max-transfer-distance 0.2 --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
python -m video2mesh.cli fuse-masks --project-root exports/track_masks_sam_smoke
python -m video2mesh.cli validate --project-root exports/track_masks_sam_smoke --output exports/track_masks_sam_smoke/simulator_assets/validation_report.json
python -m video2mesh.cli reconstruct-object-meshes --project-root exports/mask_mesh_reconstruction_smoke --method auto --format obj
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_mask_mesh_smoke --scene-id run_pipeline_mask_mesh_smoke --world run_pipeline_mask_mesh_smoke --make-sample --g3dgs-command-template "<mock or real 3DGS command using {source_path}/{output_path}>" --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
python -m video2mesh.cli make-scan-video-sample --project-root exports/scan_video_sample_smoke --scene-id scan_video_sample_smoke --frame-count 10 --extract-every 3
python -m video2mesh.cli extract-frames --project-root exports/extract_video_smoke --every 3 --max-frames 4
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_extract_video_smoke --scene-id run_pipeline_extract_video_smoke --dataset exports/test_scan_video.mp4 --extract-frames --every 4 --max-frames 3 --skip-fuse-masks --skip-export-splat-masks --skip-object-mask-clouds --skip-select-frames --skip-object-images --skip-export-image-blaster --skip-import-meshes --skip-simulator-assets --allow-incomplete
python -m video2mesh.cli render-reconstruction-preview --project-root exports/run_pipeline_scan_video_full_smoke --max-frames 2 --max-points-per-frame 1000 --point-radius 2 --alpha 0.9
python -m video2mesh.cli render-semantic-preview --project-root exports/run_pipeline_scan_video_full_smoke --max-frames 2 --max-points-per-frame 1000 --point-radius 2 --alpha 0.9
python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_reconstruction_preview_smoke --scene-id run_pipeline_reconstruction_preview_smoke --world run_pipeline_reconstruction_preview_smoke --make-scan-video-sample --every 3 --max-frames 4 --overwrite-frames --render-reconstruction-preview --reconstruction-preview-max-frames 2 --reconstruction-preview-max-points 1000 --g3dgs-command-template "<mock or real 3DGS command using {source_path}/{output_path}>" --auto-prompts --auto-prompt-method opencv --auto-prompt-max-objects 4 --mask-backend opencv --transfer-mode nearest --max-transfer-distance 0.2 --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli train-gsplat --project-root exports/train_gsplat_smoke --iterations 6 --max-frames 2 --max-points 128 --width 160 --height 120 --log-every 1
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_gsplat_smoke --scene-id run_pipeline_gsplat_smoke --world run_pipeline_gsplat_smoke --make-sample --train-gsplat --gsplat-iterations 8 --gsplat-max-frames 2 --gsplat-max-points 192 --gsplat-width 160 --gsplat-height 120 --gsplat-log-every 2 --transfer-mode nearest --max-transfer-distance 0.2 --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli render-gsplat-preview --project-root exports/run_pipeline_gsplat_smoke --max-frames 2 --width 160 --height 120
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_gsplat_preview_smoke --scene-id run_pipeline_gsplat_preview_smoke --world run_pipeline_gsplat_preview_smoke --make-sample --train-gsplat --gsplat-iterations 3 --gsplat-max-frames 1 --gsplat-max-points 96 --gsplat-width 160 --gsplat-height 120 --gsplat-log-every 1 --render-gsplat-preview --preview-max-frames 1 --preview-width 160 --preview-height 120 --transfer-mode nearest --max-transfer-distance 0.2 --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_scan_video_full_smoke --scene-id run_pipeline_scan_video_full_smoke --world run_pipeline_scan_video_full_smoke --make-scan-video-sample --every 3 --max-frames 4 --overwrite-frames --train-gsplat --gsplat-iterations 4 --gsplat-max-frames 2 --gsplat-max-points 128 --gsplat-width 160 --gsplat-height 120 --gsplat-log-every 1 --render-gsplat-preview --preview-max-frames 2 --preview-width 160 --preview-height 120 --auto-prompts --auto-prompt-method opencv --auto-prompt-max-objects 4 --mask-backend opencv --transfer-mode nearest --max-transfer-distance 0.2 --reconstruct-mask-meshes --mask-mesh-method auto --mask-mesh-format obj --simulator-format mujoco isaac unity
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_semantic_preview_gsplat_smoke --scene-id run_pipeline_semantic_preview_gsplat_smoke --make-scan-video-sample --every 3 --max-frames 4 --train-gsplat --gsplat-iterations 3 --gsplat-max-frames 2 --gsplat-max-points 128 --gsplat-device cuda --render-gsplat-preview --preview-max-frames 1 --auto-prompts --auto-prompt-method opencv --auto-prompt-max-objects 2 --auto-prompt-min-area-ratio 0.01 --auto-prompt-max-area-ratio 0.4 --track-max-frames 4 --render-semantic-preview --semantic-preview-max-frames 2 --semantic-preview-max-points 1000 --reconstruct-mask-meshes --skip-export-image-blaster
MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9 python -m video2mesh.cli run-pipeline --project-root exports/run_pipeline_localized_mesh_smoke --scene-id run_pipeline_localized_mesh_smoke --make-scan-video-sample --every 3 --max-frames 4 --train-gsplat --gsplat-iterations 2 --gsplat-max-frames 1 --gsplat-max-points 96 --gsplat-device cuda --auto-prompts --auto-prompt-method opencv --auto-prompt-max-objects 2 --auto-prompt-min-area-ratio 0.01 --auto-prompt-max-area-ratio 0.4 --track-max-frames 4 --render-semantic-preview --semantic-preview-max-frames 1 --semantic-preview-max-points 1000 --reconstruct-mask-meshes --skip-export-image-blaster --simulator-ascii-meshes
```

验证结果：

- 合成样例：`6` 张 2D mask 融合到 `648` 个点。
- `blue_cube` 和 `red_cube` 各得到 `324` 个 3D mask 点。
- 导出 `simulator_assets/semantic_splats.ply`，PLY 顶点新增 `property int object_id`。
- COLMAP text 样例成功导入 `2` 帧相机和 `points3D.txt` 点云。
- `track-masks` 已用 bbox prompts 在远端生成 `6` 张 2D mask，并接通 `fuse-masks -> select-frames -> export-image-blaster`。
- `track_masks_smoke` 验证里，`blue_cube` 得到 `306` 个 3D mask 点，`red_cube` 得到 `216` 个 3D mask 点，并导出 image-blaster world `image-blaster/worlds/track_masks_smoke`。
- `export-splat-masks` 已支持 ASCII PLY 和 Open3D 可读 binary PLY。已用 MASt3R-SLAM 的 `195953` 点 binary PLY 验证可重写为带 `property int object_id` 的 semantic ASCII PLY。
- `sim_asset_smoke_tail` 已完整验证 `make-sample -> run-local -> export-splat-masks -> import-object-meshes -> export-simulator-assets`。
- `sim_asset_smoke_tail` 使用两个占位 `.obj` 模型模拟 image-blaster/FAL 的 mesh 输出，最终写出 `simulator_assets/simulator_asset_bundle.json`，`blue_cube` 和 `red_cube` 均为 `ready`，缺失 mesh 数为 `0`。
- `semantic_transfer_smoke` 已验证 `export-splat-masks --transfer-mode auto` 的 nearest-neighbor 语义转移：目标 PLY 为 `1301` 个 vertex，源 mask 点云为 `648` 个点，自动选择 `nearest/scipy_ckdtree`，`blue_cube=648`、`red_cube=648`，并用 `--max-transfer-distance 0.05` 将 `5` 个远处点标为 background。
- `export_colmap_smoke` 已验证 `export-colmap`：从 Video2Mesh 样例导出 `images/` 和 `sparse/0/{cameras.txt,images.txt,points3D.txt}`，包含 `3` 张图、`1` 个 PINHOLE 相机、`648` 个点；再用 `import-colmap` 导回 `export_colmap_roundtrip`，确认得到 `3` 个外参和 `3` 帧图片。
- `run_3dgs_smoke` 已验证 `run-3dgs` 外部 trainer 适配器：先导出 COLMAP source，再执行 mock trainer，把 `point_cloud.ply` 写入默认 `scene/reconstruction/3dgs/point_cloud/iteration_1/point_cloud.ply`，最后自动 `register-3dgs`。`manifest.json` 中 `external_stages.video_to_3dgs.status == 3dgs_trained_registered`。这是 runner/注册协议验证，不代表真实 3DGS 训练质量评估。
- `object_crop_smoke` 已验证 `prepare-object-images` 和 `export-image-blaster` 的裁剪输入：`blue_cube` 生成 `219x219x4` 透明 PNG，`red_cube` 生成 `212x212x4` 透明 PNG；image-blaster world 中每个物体的 `source.png` 都是 masked object crop，并额外写入 `video2mesh_object_images/` 下的 top-3 object crops 作为 evidence。
- `end_to_end_smoke` 已把 mock 3DGS、2D/3D masks、semantic splats、selected frames、masked object crops、image-blaster world、placeholder object meshes 和 simulator asset bundle 放在同一个项目中，并通过 `python -m video2mesh.cli validate --project-root exports/end_to_end_smoke`。验证报告在 `exports/end_to_end_smoke/simulator_assets/validation_report.json`，`required_failed=[]`，`recommended_failed=[]`。这是工程协议完整性 smoke，不代表真实视频/真实 3DGS/真实 mesh 质量已经完成。
- `run_pipeline_smoke` 已验证 `run-pipeline` 一键编排器：同一命令完成 `make_sample -> run_3dgs(mock) -> fuse_masks -> export_splat_masks -> select_frames -> prepare_object_images -> export_image_blaster -> mesh_commands -> create_placeholder_meshes -> import_object_meshes -> export_simulator_assets -> validate`，`logs/pipeline_report.json` 中 `validate_ok == True`。
- `run_pipeline_mast3r_smoke` 已验证 `run-pipeline --run-mast3r-slam` 的真实 MASt3R-SLAM 调用和自动导入：使用 `exports/mast3r_smoke_frames`，输出 `mast3r_slam_pose_count=1`、`frames_imported=1`，并写入 `scene/cameras/camera_info.json` 和 `scene/reconstruction/point_cloud.ply`。该 smoke 刻意跳过 masks/mesh，`validate_ok == False` 是预期现象。
- `run_pipeline_report_smoke` 已验证 `run-pipeline` 对 skipped 阶段的 report 记录：`fuse_masks/export_splat_masks/select_frames/prepare_object_images/export_image_blaster/mesh_commands/import_object_meshes/export_simulator_assets` 均会显式写入 `logs/pipeline_report.json`。
- `occlusion_fusion_smoke` 已验证 `fuse-masks` 的 z-buffer 可见性过滤：两个点投到同一 mask 像素时，近点 index `0` 和远点 index `1` 都会被旧逻辑命中；开启 `--occlusion-filter --depth-tolerance 0.01 --relative-depth-tolerance 0.0` 后只保留近点 `[0]`，关闭过滤则得到 `[0, 1]`。
- `export-object-mask-clouds` 已在 `end_to_end_smoke` 验证：导出 `simulator_assets/object_masks_3d/blue_cube.ply` 和 `red_cube.ply`，各 `324` 点，并在 `objects/<object_id>/object.json` 写入 `mask_3d_cloud`；`validate` 现在会检查 `object_mask_clouds`，更新后的 `end_to_end_smoke` 仍 PASS。
- `run_pipeline_mask_cloud_smoke` 已验证新版 `run-pipeline` 会自动执行 `export_object_mask_clouds`，并生成 `simulator_assets/object_masks_3d/object_mask_clouds.json`；`validate_ok == True`。
- `evaluate` 已在 `end_to_end_smoke` 验证：生成 `simulator_assets/evaluation_report.json`，汇总 frame/camera/point cloud/3DGS、2D/3D masks、semantic splats、per-object mask clouds、selected frames、object crops、meshes 和 simulator bundle 的 readiness；该报告用于阶段化质检，不代表真实 3DGS/mesh 质量评估已完成。
- `export-svpp-metadata` 已在 `end_to_end_smoke` 验证：生成 `simulator_assets/svpp/end_to_end_smoke/{mesh.ply,camera_info.json,data_info.json,metadata.json,video2mesh_svpp_export.json}`。`metadata.json` 含 `point_ids/pred_class_name/pred_class_id`，用 `--default-category table` 可把 smoke 的 `box` 类别映射成 SceneVerse++/ScanNet20 识别的 `table`，两个实例各 `324` 个 point ids。
- `export-review-pack` 已在 `end_to_end_smoke` 验证：生成 `simulator_assets/review/index.html` 和 `review_pack.json`，汇总每个物体的 primary object crop、selected frames、3D mask 点数、mask cloud、mesh 状态和 issues；完整 smoke 为 `2` 个对象、`0` 个 issues。
- 增强版 `export-review-pack` 已在 `run_pipeline_scan_video_full_smoke` 验证：HTML 顶部现在包含场景级 QA sections：`Auto Prompts`、`Point Cloud Projection`、`Semantic 3D Mask Projection`、`3DGS Render Preview`、`3DGS Error Preview`；`review_pack.json.scene_review` 记录 auto prompt preview、reconstruction preview frames、semantic projection frames、gsplat render/error frames。该 smoke 中 index.html 存在，自动 prompt preview 存在，reconstruction overlay `2` 张存在，semantic overlay `2` 张存在，3DGS render/error 各 `2` 张，HTML section 检查通过。
- `export-simulator-adapter` 已在 `end_to_end_smoke` 验证：生成 `simulator_assets/adapters/simulator_adapters.json`、`mujoco/scene.xml`、`isaac/isaac_adapter.json`、`unity/unity_adapter.json`，并把 mesh 复制到 `simulator_assets/adapters/assets/<object_id>/`；MuJoCo XML 和 Isaac/Unity JSON 使用相对路径。
- `run_pipeline_adapter_smoke` 已验证新版 `run-pipeline` 会在 `export_simulator_assets` 后自动执行 `export_simulator_adapters`。该 smoke 使用 mock 3DGS 和 placeholder meshes，`validate_ok == True`，adapter formats 为 `mujoco/isaac/unity`。
- `track_masks_auto_smoke` 已验证 `track-masks --mask-backend auto`：没有完整 SAM checkpoint 时，命令会明确回退到 `opencv_template_tracking_bbox`，两个对象各写出 `3` 张 mask；显式 `--mask-backend sam` 但不传 `--sam-checkpoint` 会失败并提示 `--mask-backend sam requires --sam-checkpoint`，避免假装使用 SAM。
- 远端 `/root/autodl-tmp/venvs/v2m-svpp` 已安装 `segment-anything==1.0`。SAM ViT-B checkpoint 已完整下载到 `/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth`，文件大小 `375042383` bytes。
- `track_masks_sam_smoke` 已验证真实 SAM bbox refinement：`backend == sam`、`model_type == vit_b`、`device == cuda`、`multimask == False`；`red_cube` 和 `blue_cube` 各生成 `3` 张 mask，SAM score 约 `0.98-0.996`，`fuse-masks` 后 `blue_cube=324`、`red_cube=324` 个 3D mask 点。
- `track_masks_sam_smoke` 已进一步用 mock 3DGS 和 placeholder object meshes 完成协议闭环，`validate == True`、`evaluate == True`，并导出 `mujoco/isaac/unity` 三类 simulator adapter。该结果证明 SAM mask 分支已经接入工程协议，但仍不代表真实视频 3DGS 训练和真实 object mesh 生成质量已经完成。
- `auto-prompts` 已实现并验证：从代表帧生成 `masks/auto_prompts.json`、`masks/auto_prompts_preview.png` 和 `masks/object_labels.json`，输出格式可直接作为 `track-masks --prompts` 输入。OpenCV smoke `auto_prompts_preview_smoke` 找到 `2` 个候选物体并生成 preview 图；SAM AMG smoke `auto_prompts_sam_preview_smoke` 使用 ViT-B CUDA checkpoint，`candidate_count=5`，通过 `--max-area-ratio 0.2` 和 containment/NMS 过滤后保留 `2` 个物体候选，并生成 preview 图。
- `run_pipeline_auto_prompts_preview_smoke` 已验证无手写 prompt 的完整协议闭环：`make_sample -> run_3dgs(mock) -> auto_prompts(opencv) -> track_masks -> fuse_masks -> export_splat_masks -> export_object_mask_clouds -> select_frames -> prepare_object_images -> export_image_blaster -> reconstruct_object_meshes -> export_simulator_assets -> export_simulator_adapters -> validate/evaluate` 全部跑通。`evaluate.ok == True`，自动 prompt 数 `2`，preview 图存在，两个自动物体各 `324` 个 3D mask 点且 mesh 存在。
- `reconstruct-object-meshes` 已验证可从 `simulator_assets/object_masks_3d/<object_id>.ply` 直接重建 OBJ，并写入 `mesh_asset.source == object_mask_cloud_reconstruction`。`mask_mesh_reconstruction_smoke` 中两个物体均生成 OBJ，后续 `export-simulator-assets` 缺失 mesh 数为 `0`。
- `run_pipeline_mask_mesh_smoke` 已验证不使用 `--create-placeholder-meshes` 的完整协议闭环：mock 3DGS、2D/3D masks、semantic splats、object mask clouds、selected frames、object crops、image-blaster world、3D mask cloud 重建 mesh、simulator bundle 和 `mujoco/isaac/unity` adapters 全部生成，`validate_ok == True`。两个物体 mesh 来源均为 `object_mask_cloud_reconstruction`，Open3D 自动选择 `ball_pivoting`，`blue_cube=382` 个三角面，`red_cube=375` 个三角面。
- `export-simulator-assets` 已增强 object mesh 坐标语义：`object_mask_cloud_reconstruction` 来源的 mesh 会被识别为 `video2mesh_scene` 坐标，并在导出仿真资产时自动生成 `*_local.<ext>` object-local 副本；bundle 中记录 source/exported mesh bbox、vertex/triangle 数、surface area、manifold/watertight 标记、source mesh 与 3D mask bbox 的 center/size 对齐摘要，以及 localization 是否应用。已在 `run_pipeline_semantic_preview_gsplat_smoke` 上手动重导出验证：两个物体的 simulator mesh `coordinate_frame == object_local`，`localization.applied == True`，`pose.scale == [1.0, 1.0, 1.0]`，`evaluate.ok == True`，review HTML 显示 `sim mesh/localized` 信息。
- `run_pipeline_localized_mesh_smoke` 已验证该 localize 逻辑在一键 pipeline 中生效：synthetic mp4 -> `train_gsplat` -> auto prompts -> 2D/3D masks -> semantic preview -> mask-cloud mesh reconstruction -> simulator assets/adapters 全部跑通，`validate_ok == True`、`evaluate.ok == True`；两个自动物体的 simulator mesh 都是 `object_local`，`localization.applied == True`，`pose.scale == [1.0, 1.0, 1.0]`，mesh 文件存在。
- `make-scan-video-sample` 已实现并验证：生成 `inputs/synthetic_scan.mp4`、`source_frames/*.png`、匹配推荐抽帧步长的 `scene/cameras/camera_info.json` 和 `scene/reconstruction/point_cloud.ply`。`scan_video_sample_smoke` 用 `frame_count=10`、`extract_every=3` 生成视频后，再 `extract-frames --every 3 --max-frames 4`，得到 source frame indices `[0, 3, 6, 9]`，相机外参数量 `4`，点云存在。
- `extract_video_smoke` 已验证 OpenCV 视频抽帧入口：从 `exports/test_scan_video.mp4` 每 `3` 帧抽一帧，写出 `4` 张连续编号 PNG，`scene/frames_manifest.json` 记录原始 source frame indices `[0, 3, 6, 9]`。
- `run_pipeline_extract_video_smoke` 已验证 `run-pipeline --dataset <mp4> --extract-frames` 会在未显式传 `--video` 时把 dataset 文件当作视频源；该 smoke 写出 `3` 张连续编号帧和 `scene/frames_manifest.json`。后续语义/mesh 阶段刻意跳过，所以 `validate` 失败是预期现象。
- `render-reconstruction-preview` 已实现并在 `run_pipeline_scan_video_full_smoke` 上验证：读取 `scene/reconstruction/point_cloud.ply`、`scene/cameras/camera_info.json` 和 `scene/frames`，把点云投影回相机帧，输出 `simulator_assets/reconstruction_preview/<frame_id>/projection_overlay.png` 和 `reconstruction_preview.json`。该 smoke 渲染 `2` 帧，overlay 图都存在，`mean_projected_point_ratio=1.0`，`mean_visible_point_ratio=1.0`，`mean_projected_pixel_ratio=0.002109375`，`mean_visible_pixel_ratio=0.002109375`；`evaluate` 现在会把 `scene.reconstruction_preview.summary` 写入报告。
- `run_pipeline_reconstruction_preview_smoke` 已验证 `run-pipeline --render-reconstruction-preview` 新开关：从 synthetic mp4 生成/抽帧后，先输出 reconstruction projection QA，再继续 mock 3DGS、auto prompts、2D/3D masks、object meshes 和 simulator adapters，`evaluate.ok == True`。该 QA 用于发现 camera/point-cloud 对齐问题，应在真实视频的 `fuse-masks` 前检查。
- `render-semantic-preview` 已实现并在 `run_pipeline_scan_video_full_smoke` 上验证：读取 `simulator_assets/semantic_splats.ply` 和 `semantic_splats_manifest.json`，按 `object_id` 生成固定颜色的 `simulator_assets/semantic_preview/semantic_splats_colored.ply`，并把 semantic splats 投影回帧，输出 `simulator_assets/semantic_preview/<frame_id>/semantic_overlay.png` 和 `semantic_preview.json`。该 smoke 渲染 `2` 帧，colored PLY 存在，legend keys 为 `0/1/2`，`semantic_vertex_count=128`，`foreground_vertex_count=128`，`mean_projected_foreground_ratio=1.0`，`mean_visible_foreground_ratio=1.0`；`evaluate` 现在会把 `masks.semantic_splats.preview` 写入报告。
- `gsplat==1.5.3` 和 `ninja==1.13.0` 已安装到 `/root/autodl-tmp/venvs/v2m-svpp`。首次调用 `gsplat.rasterization` 会 JIT 编译 `gsplat_cuda`，远端已用 `MAX_JOBS=1 TORCH_CUDA_ARCH_LIST=8.9` 完成编译和 CUDA smoke：`render_shape=[1,64,64,3]`，`loss.backward()` 成功，`means.grad.norm()=0.08368656`。首次编译耗时约 `634s`，后续会使用 PyTorch extension cache。
- `train-gsplat` 已实现并验证最小 3DGS baseline：从 `scene/frames`、`scene/cameras/camera_info.json`、`scene/reconstruction/point_cloud.ply` 初始化 Gaussians，真实调用 `gsplat.rasterization + loss.backward` 优化 position/color/scale/opacity，输出 `scene/reconstruction/3dgs/point_cloud/iteration_<N>/point_cloud.ply` 和 `video2mesh_gsplat_train.json`，并自动注册为 `scene_3dgs_ply`。`train_gsplat_smoke` 用 `128` 个点、`2` 帧、`6` 步训练通过，semantic transfer 到 trained splat PLY 也通过。
- `run_pipeline_gsplat_smoke` 已验证不再使用 mock 3DGS：`make_sample -> train_gsplat -> fuse_masks -> export_splat_masks(nearest transfer) -> export_object_mask_clouds -> select_frames -> prepare_object_images -> export_image_blaster -> reconstruct_object_meshes -> export_simulator_assets -> export_simulator_adapters -> validate` 全部跑通，`validate_ok == True`，`evaluate_ok == True`。训练输出 `192` 个 Gaussian vertices，semantic splats `192` vertices，两个物体 mesh 均来自 `object_mask_cloud_reconstruction`，adapters 为 `mujoco/isaac/unity`。
- `render-gsplat-preview` 已实现并在 `run_pipeline_gsplat_smoke` 上验证：读取注册的 `scene_3dgs_ply` 和项目相机，把 splat 回渲染到输入帧，输出 `simulator_assets/gsplat_preview/<frame_id>/{render,target,error}.png` 和 `preview_manifest.json`。该 smoke 渲染 `2` 帧，`mean_l1=0.12295898050069809`，`mean_psnr=13.984593019374712`；`evaluate` 现在会把 `gsplat_preview.frame_count/mean_l1/mean_psnr/output_dir` 写入报告。
- `run_pipeline_gsplat_preview_smoke` 已验证 `run-pipeline --render-gsplat-preview` 新开关：`train_gsplat -> render_gsplat_preview -> fuse_masks -> export_splat_masks -> export_object_mask_clouds -> select_frames -> prepare_object_images -> export_image_blaster -> reconstruct_object_meshes -> export_simulator_assets -> export_simulator_adapters -> validate` 一条命令跑通，预览 `1` 帧，`mean_l1=0.122959`，`mean_psnr=13.985`。
- `run_pipeline_scan_video_full_smoke` 已验证从视频文件入口开始的完整工程闭环：`make_scan_video_sample -> extract_frames(mp4) -> train_gsplat -> render_gsplat_preview -> auto_prompts -> track_masks -> fuse_masks -> export_splat_masks -> export_object_mask_clouds -> select_frames -> prepare_object_images -> export_image_blaster -> reconstruct_object_meshes -> export_simulator_assets -> export_simulator_adapters -> evaluate`。结果：抽帧 `4` 张，source indices `[0, 3, 6, 9]`；3DGS PLY `128` vertices；预览 `2` 帧，`mean_l1=0.12248225882649422`，`mean_psnr=13.996128072430665`；自动 prompt 数 `2` 且 preview 图存在；两个自动物体各 `324` 个 3D mask 点，mesh 均存在，`evaluate.ok == True`。这是 synthetic mp4 视频入口和协议闭环验证，不代表真实扫描视频质量已经完成。
- `run_pipeline_semantic_preview_gsplat_smoke` 已验证 `run-pipeline --render-semantic-preview` 与真实最小 `train-gsplat` 可一起编排：`make_scan_video_sample -> extract_frames -> train_gsplat -> render_gsplat_preview -> auto_prompts -> track_masks -> fuse_masks -> export_splat_masks -> render_semantic_preview -> export_object_mask_clouds -> select_frames -> prepare_object_images -> reconstruct_object_meshes -> export_simulator_assets -> export_simulator_adapters -> validate/evaluate`。结果：`pipeline_render_semantic_preview == completed`，`pipeline_train_gsplat == completed`，`validate_ok == True`，`evaluate.ok == True`，scene 3DGS PLY `128` vertices，semantic overlay `2` 张，colored semantic PLY 存在，`2` 个对象均有 mesh，review HTML 包含 `Semantic 3D Mask Projection`。

真实扫描视频接入建议：

1. 先用 MASt3R-SLAM、COLMAP 或 3DGS 工具产出相机、点云和 3DGS。
2. 如果是 COLMAP sparse text model，运行 `import-colmap` 生成 `camera_info.json` 和 `point_cloud.ply`。
3. 如果是 MASt3R-SLAM 输出，运行 `import-mast3r-slam` 导入 `logs/<scene>/<seq>.txt` 和 `<seq>.ply`。
4. 如果下游 3DGS 训练需要 COLMAP-style 输入，可运行 `export-colmap` 生成 `images/` 和 `sparse/0/*.txt`。
5. 在 `fuse-masks` 前运行 `render-reconstruction-preview` 或在 `run-pipeline` 加 `--render-reconstruction-preview`，检查点云投影 overlay 是否和图像对齐。
6. 如果要先跑内置最小 3DGS baseline，可运行 `train-gsplat` 或 `run-pipeline --train-gsplat`；如果要接外部 3DGS trainer，可运行 `run-3dgs --command-template "... {source_path} ... {output_path} ..."`。
7. 如果已有 Gaussian Splatting 输出，运行 `register-3dgs` 注册 3DGS 目录或 PLY。
8. 训练或注册 3DGS 后，可运行 `render-gsplat-preview` 或在 `run-pipeline` 加 `--render-gsplat-preview`，生成 render/target/error 图和 mean L1/PSNR，作为 3DGS 质量闸门。
9. 当前可先用 `auto-prompts` 从代表帧生成 bbox candidates 和 `auto_prompts_preview.png`，再用 `track-masks` 生成 `masks/2d/<object_id>/<frame_id>.png`；远端已经验证 OpenCV proposal、SAM AMG proposal 和 SAM bbox prompt 精修都可用。真实视频里必须检查 preview 图，生产质量仍建议后续接 GroundingDINO/SAM2/DEVA/SAM2 tracking。
10. 运行 `fuse-masks -> export-splat-masks` 后，运行 `render-semantic-preview` 或在 `run-pipeline` 加 `--render-semantic-preview`，检查 object-level 3D semantic mask 投影回视频帧是否贴合物体。
11. 继续运行 `export-object-mask-clouds -> select-frames -> prepare-object-images -> export-image-blaster -> mesh-commands`。
12. mesh 阶段有两条路线：image-blaster/FAL 生成 mesh 后运行 `import-object-meshes -> export-simulator-assets`；或先运行 `reconstruct-object-meshes -> export-simulator-assets`，直接从 3D object mask cloud 得到保尺度/保位姿的几何 baseline。后者会在 `export-simulator-assets` 中被自动 localize 成 object-local mesh，避免仿真器里重复叠加世界坐标和 pose。
13. 运行 `validate` 生成 `validation_report.json`，确认完整目标所需工程产物是否齐全。
14. 若要统一编排，可用 `run-pipeline` 串联上述阶段；真实项目中去掉 `--create-placeholder-meshes`，改用 image-blaster/FAL 生成的 mesh。

当前服务器探测结果：

- 未发现可直接调用的 `colmap` 命令。
- 未发现可直接调用的系统 `ffmpeg` 命令；但 `extract-frames` 已用 OpenCV `VideoCapture` 验证可从 `.mp4` 抽帧，并写出 `scene/frames_manifest.json`。
- 已安装并验证 `gsplat==1.5.3` CUDA rasterization/backward；未安装 `nerfstudio`。当前 `run-3dgs` 仍是外部 trainer 适配器，下一步可以基于 `gsplat` 写/接真实 3DGS 训练循环，或接现成 gsplat/nerfstudio trainer。
- 已安装 `segment_anything`，未安装 `sam2`；真实 SAM bbox refinement 已用完整 ViT-B checkpoint 验证通过。
- `/root/miniconda3/envs/mast3r-slam` 是 Python 3.11 环境，但未继续使用；当前统一使用 `/root/autodl-tmp/venvs/v2m-svpp`。
- MASt3R-SLAM 主仓库在 `/root/autodl-tmp/workspace/MASt3R-SLAM`，之前 GitLab `thirdparty/eigen` 失败的问题已绕过。
- MASt3R-SLAM README 的运行入口是 `python main.py --dataset <video>.mp4 --config config/base.yaml --save-as <scene_id> --no-viz`。
- MASt3R-SLAM 结束后会保存 `logs/<scene_id>/<sequence>.txt` 轨迹、`logs/<scene_id>/<sequence>.ply` 重建点云和 keyframes。
- Video2Mesh 已新增 `import-mast3r-slam` 和 `run-mast3r-slam`，后者可以一条命令运行 MASt3R-SLAM 并自动导入结果。
