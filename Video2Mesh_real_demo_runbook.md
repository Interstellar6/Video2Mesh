# Video2Mesh 真实扫描视频 Demo 运行记录

## 样例输入

- 本地视频：`dataset/milscene.mp4`
- 远端工作目录：`/root/autodl-tmp/workspace/Video2Mesh`
- 项目输出：`exports/milscene_real_demo`
- 远端环境：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo || true
source remote_env.sh
```

## 已跑通的链路

这次 demo 已经从真实空间扫描视频跑到仿真资产导出：

1. 视频抽帧：从 227 帧视频中抽出 46 张原始帧。
2. MASt3R-SLAM：得到 45 个相机位姿和约 508 万点场景点云。
3. 场景 3DGS：用 10k 点云下采样训练最小 gsplat，注册 8000 个 Gaussian。
4. 2D segmentation/tracking：SAM 自动候选 + bbox/SAM tracking，得到 6 个对象、108 张 2D mask。
5. 2D-to-3D mask fusion：融合到 10k 点云，生成 6 个物体级 3D masks。
6. Semantic splats：把物体语义 ID transfer 到训练后的 3DGS PLY。
7. Object frame selection：每个物体选 top-3 相关帧。
8. Object mesh：从每个 object mask cloud 重建粗 mesh。
9. Simulator export：导出 object-local mesh、asset bundle、MuJoCo/Isaac/Unity adapter。

## 关键结果

- Evaluation report：`exports/milscene_real_demo/simulator_assets/evaluation_report.json`
- Review HTML：`exports/milscene_real_demo/simulator_assets/review/index.html`
- 训练后的 3DGS：`exports/milscene_real_demo/scene/reconstruction/3dgs/point_cloud/iteration_10/point_cloud.ply`
- Semantic splats：`exports/milscene_real_demo/simulator_assets/semantic_splats.ply`
- Simulator bundle：`exports/milscene_real_demo/simulator_assets/simulator_asset_bundle.json`
- MuJoCo adapter：`exports/milscene_real_demo/simulator_assets/adapters/mujoco/scene.xml`
- image-blaster world：`image-blaster/worlds/milscene-real-demo`
- image-blaster mesh commands：`exports/milscene_real_demo/simulator_assets/mesh_generation_commands.sh`

当前评估摘要：

- `video_to_3dgs.status = gsplat_trained_registered`
- 原始帧数：46
- 相机位姿数：45
- 原始 MASt3R 点云：5,083,870 points
- 训练 3DGS：8,000 vertices/Gaussians
- 2D masks：108
- 语义对象数：6
- 有 reference images 的对象数：6
- 有 3D mask clouds 的对象数：6
- 有 mesh 的对象数：6
- 必需项失败数：0
- 推荐项失败数：0

## 主要命令

```bash
python -m video2mesh.cli init \
  --project-root exports/milscene_real_demo \
  --scene-id milscene_real_demo \
  --video dataset/milscene.mp4

python -m video2mesh.cli extract-frames \
  --project-root exports/milscene_real_demo \
  --every 5 --max-frames 0 --overwrite --renumber

python -m video2mesh.cli run-mast3r-slam \
  --project-root exports/milscene_real_demo \
  --dataset exports/milscene_real_demo/scene/frames \
  --config config/video_scan.yaml \
  --save-as milscene_real_demo_dense \
  --focal-scale 1.2

python -m video2mesh.cli downsample-point-cloud \
  --project-root exports/milscene_real_demo \
  --point-cloud scene/reconstruction/point_cloud.ply \
  --output scene/reconstruction/point_cloud_10k.ply \
  --max-points 10000 --seed 7

python -m video2mesh.cli train-gsplat \
  --project-root exports/milscene_real_demo \
  --frames-dir exports/milscene_real_demo/scene/mast3r_keyframes \
  --point-cloud exports/milscene_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --output-dir exports/milscene_real_demo/scene/reconstruction/3dgs_trained \
  --iterations 10 --max-frames 6 --max-points 8000 \
  --device cuda --width 288 --height 512 --log-every 2

python -m video2mesh.cli auto-prompts \
  --project-root exports/milscene_real_demo \
  --frames-dir exports/milscene_real_demo/scene/mast3r_keyframes \
  --method sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b --sam-device cuda \
  --frame-index 10 --max-objects 6 \
  --min-area-ratio 0.003 --max-area-ratio 0.35 --overwrite

python -m video2mesh.cli track-masks \
  --project-root exports/milscene_real_demo \
  --frames-dir exports/milscene_real_demo/scene/mast3r_keyframes \
  --prompts exports/milscene_real_demo/masks/auto_prompts.json \
  --mask-backend sam \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b --sam-device cuda \
  --max-frames 18 --clear-output

python -m video2mesh.cli fuse-masks \
  --project-root exports/milscene_real_demo \
  --point-cloud exports/milscene_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --min-votes 1 --occlusion-filter \
  --depth-tolerance 0.05 --relative-depth-tolerance 0.03

python -m video2mesh.cli export-splat-masks \
  --project-root exports/milscene_real_demo \
  --mask-source-ply exports/milscene_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --transfer-mode nearest --max-transfer-distance 0.08

python -m video2mesh.cli render-semantic-preview \
  --project-root exports/milscene_real_demo \
  --frames-dir exports/milscene_real_demo/scene/mast3r_keyframes \
  --max-frames 4 --max-points-per-frame 12000

python -m video2mesh.cli export-object-mask-clouds \
  --project-root exports/milscene_real_demo \
  --point-cloud exports/milscene_real_demo/scene/reconstruction/point_cloud_10k.ply \
  --skip-missing

python -m video2mesh.cli select-frames \
  --project-root exports/milscene_real_demo --top-k 3

python -m video2mesh.cli prepare-object-images \
  --project-root exports/milscene_real_demo --top-k 3 --skip-missing

python -m video2mesh.cli reconstruct-object-meshes \
  --project-root exports/milscene_real_demo \
  --method auto --format obj --skip-missing --skip-failed

python -m video2mesh.cli export-image-blaster \
  --project-root exports/milscene_real_demo \
  --world milscene-real-demo \
  --image-blaster-root image-blaster \
  --provider hunyuan \
  --use-object-crop \
  --skip-missing

python -m video2mesh.cli mesh-commands \
  --project-root exports/milscene_real_demo \
  --image-blaster-root image-blaster \
  --provider hunyuan \
  --reference-only

python -m video2mesh.cli export-simulator-assets \
  --project-root exports/milscene_real_demo --ascii-meshes

python -m video2mesh.cli export-simulator-adapter \
  --project-root exports/milscene_real_demo --format mujoco isaac unity

python -m video2mesh.cli evaluate \
  --project-root exports/milscene_real_demo \
  --json --output exports/milscene_real_demo/simulator_assets/evaluation_report.json

python -m video2mesh.cli export-review-pack \
  --project-root exports/milscene_real_demo \
  --max-scene-frames 4 --max-frames 3
```

## 编排版命令

如果已经有 MASt3R-SLAM 的位姿、点云和 keyframes，也可以用 `run-pipeline` 自动完成下采样、最小 3DGS、预览、语义 splat、粗 mesh 和仿真导出。下面是与本 demo 接近的后半段编排命令：

```bash
python -m video2mesh.cli run-pipeline \
  --project-root exports/milscene_real_demo \
  --scene-id milscene_real_demo \
  --use-mast3r-keyframes \
  --downsample-point-cloud \
  --downsample-output scene/reconstruction/point_cloud_10k.ply \
  --downsample-max-points 10000 \
  --train-gsplat \
  --g3dgs-output-path scene/reconstruction/3dgs_trained \
  --gsplat-iterations 10 \
  --gsplat-max-frames 6 \
  --gsplat-max-points 8000 \
  --gsplat-device cuda \
  --gsplat-width 288 \
  --gsplat-height 512 \
  --render-gsplat-preview \
  --preview-max-frames 4 \
  --preview-width 288 \
  --preview-height 512 \
  --auto-prompts \
  --auto-prompt-method sam \
  --auto-prompt-frame-index 10 \
  --auto-prompt-max-objects 6 \
  --sam-checkpoint /root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth \
  --sam-model-type vit_b \
  --sam-device cuda \
  --mask-backend sam \
  --track-max-frames 18 \
  --min-votes 1 \
  --depth-tolerance 0.05 \
  --relative-depth-tolerance 0.03 \
  --transfer-mode nearest \
  --max-transfer-distance 0.08 \
  --render-semantic-preview \
  --semantic-preview-max-frames 4 \
  --reconstruct-mask-meshes \
  --skip-failed-mask-meshes \
  --world milscene-real-demo \
  --simulator-format mujoco isaac unity \
  --simulator-ascii-meshes \
  --allow-incomplete
```

`--use-mast3r-keyframes` 会让 3DGS 训练、mask tracking、preview 和选帧使用 `scene/mast3r_keyframes`，避免 MASt3R 内部 288x512 keyframes 与原始 1080x1920 抽帧混用。`--downsample-point-cloud` 会先生成轻量点云，供 3DGS baseline 和 2D-to-3D mask fusion 使用。

## 注意事项和下一步

- `gsplat` 首次调用会编译 CUDA extension，第一次可能等待数分钟；编译完成后训练可以正常输出 step loss。
- 当前 3DGS 是最小训练 baseline，只有 10 iter / 8000 Gaussians，质量不是最终论文级结果。
- 当前物体名称来自 SAM 候选颜色提示，如 `auto_object_orange_03`，还不是可靠语义类别。
- 当前 tracking 是 bbox/SAM demo 级方案，生产路线应接 SAM2/DEVA/XMem 这类跨帧一致性更强的方法。
- 当前 mesh 来自 object mask cloud 的粗几何重建，可以用于接口验证；最终可替换为 image-blaster/Hunyuan/Meshy 或多视角 mesh 方法。
- `export-image-blaster` 已把每个物体的 cropped reference images 写入 `image-blaster/worlds/milscene-real-demo/output/<object_id>/`，`mesh_generation_commands.sh` 可用于后续调用 image-blaster/FAL 生成替代 mesh。
- 后续高质量版建议：更多帧、更长 gsplat 训练、尺度标定、人工/开放词汇语义标签、SAM2 video masks、mesh 物理属性和碰撞体 QA。

## 第二个真实视频示例：milscene2_real_demo

本地 `dataset/milscene2.mp4` 已同步到远端并跑通同一条流程，输出项目为 `exports/milscene2_real_demo`，image-blaster world 为 `image-blaster/worlds/milscene2-real-demo`。

关键结果：

- 输入视频：1080x1920，30 fps，143 帧，约 4.77 秒。
- 抽帧：`scene/frames` 共 36 张，抽帧间隔 `every=4`。
- MASt3R-SLAM：导入 13 个 keyframe poses，原始点云 1,869,714 points。
- 下采样点云：`scene/reconstruction/point_cloud_10k.ply`，10,000 points。
- 3DGS baseline：`scene/reconstruction/3dgs/point_cloud/iteration_10/point_cloud.ply`，8,000 Gaussians。
- 3DGS preview：4 帧，mean L1 约 0.1703，mean PSNR 约 12.55。
- SAM 自动物体：6 个 prompt，2D masks 共 78 个。
- Semantic splats：`simulator_assets/semantic_splats.ply`，6 个 semantic IDs，3,024 foreground vertices。
- Viewer PLYs：`simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` 和 `semantic_3dgs_point_cloud.ply` 可用 Mac Preview/CloudCompare 查看普通点云；`scene_3dgs_supersplat.ply` 和 `semantic_3dgs_supersplat.ply` 可上传到 SuperSplat。
- Object mask clouds：6 个 `.ply`。
- Object meshes：6 个 `.obj`，并导出 object-local simulator mesh。
- Simulator adapters：MuJoCo、Isaac、Unity 均已导出。
- SceneVerse++/SVPP-style export：`simulator_assets/svpp/milscene2-real-demo/{mesh.ply,camera_info.json,metadata.json,data_info.json}`，6 个 instances。
- Evaluation：`simulator_assets/evaluation_report.json`，`ok=true`，required/recommended failures 均为空。
- Review HTML：`simulator_assets/review/index.html`。

本地最终 sanity check：

```text
frame_count=36
camera_count=13
point_cloud_vertices=1869714
gsplat_vertices=8000
mask_count_2d=78
semantic_ids=6
object_count=6
objects_with_meshes=6
required_failed=[]
recommended_failed=[]
```

注意：远端运行时 `scene/frames/.ipynb_checkpoints` 曾出现 4 张 checkpoint PNG，已修复评估计数逻辑，隐藏目录不再被统计到 `frame_count`。

## PLY 查看约定

现在每次导出 splat 后会同时保留两类查看文件：

- 普通点云 PLY：`*_point_cloud.ply`，字段为 `x/y/z/red/green/blue`，适合 Mac Preview、CloudCompare、MeshLab。
- SuperSplat/GraphDECO PLY：`*_supersplat.ply`，字段为 `x/y/z/f_dc_0/f_dc_1/f_dc_2/opacity/scale_0/scale_1/scale_2/rot_0/rot_1/rot_2/rot_3`，适合 `https://superspl.at/editor`。

可以用下面命令给已有项目补导出：

```bash
python -m video2mesh.cli export-viewer-plys \
  --project-root exports/milscene2_real_demo \
  --kind all
```

`export-splat-masks` 和 `run-pipeline` 后续会自动生成这些 viewer PLY；`train-gsplat` 也会在 `scene/reconstruction/3dgs/.../iteration_<N>/` 下生成训练场景的普通点云版和 SuperSplat 版。
