# Video2Mesh 当前流水线

更新时间：2026-06-20

## 1. 总体流程

```text
输入视频
  -> extract-frames
  -> MASt3R-SLAM
  -> GraphDECO 3DGS
  -> SAM prompt + SAM2 tracking
  -> 2D-to-3D mask fusion
  -> semantic/probability splat export
  -> object frame selection
  -> object images
  -> object mesh
  -> simulator assets
  -> QA / readiness / showcase reports
```

## 2. 推荐一键命令

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh /path/to/video.mp4
```

常用覆盖：

```bash
MAX_FRAMES=72 \
EXTRACT_EVERY=2 \
GRAPHDECO_ITERATIONS=7000 \
GRAPHDECO_RESOLUTION=1 \
GRAPHDECO_DENSIFY_UNTIL_ITER=0 \
bash tools/run_video2mesh_quick.sh /path/to/video.mp4
```

该脚本默认：

- 输出到 `exports/<scene>_quick_<timestamp>`。
- 使用 `/root/autodl-tmp/venvs/v2m-svpp/bin/python`。
- 用 MASt3R-SLAM 生成 camera poses、keyframes、full point cloud。
- 用 GraphDECO `train.py` 训练 3DGS，默认保留 full cloud 初始化并关闭 densification。
- 用 SAM v1 自动生成 prompts。
- 用 SAM2.1 Hiera Tiny 传播视频 masks。
- 使用 full `point_cloud.ply` 做 mask fusion、semantic transfer 和 object mask clouds。
- 导出 review pack、viewer PLY、simulator bundle 和 QA reports。

## 3. MASt3R 超时裁剪策略

如果 MASt3R-SLAM 对长视频运行超过 1.5 小时还没有输出：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

则中断当前 MASt3R，裁剪视频前 60 秒作为新数据集：

```bash
ffmpeg -y \
  -i dataset/bedroom_100.mp4 \
  -t 60 \
  -c copy \
  dataset/bedroom_100_first60.mp4
```

如果 stream copy 失败，用重编码 fallback：

```bash
ffmpeg -y \
  -i dataset/bedroom_100.mp4 \
  -t 60 \
  -c:v libx264 -crf 18 -preset veryfast \
  -c:a copy \
  dataset/bedroom_100_first60.mp4
```

然后重新运行：

```bash
bash tools/run_video2mesh_quick.sh dataset/bedroom_100_first60.mp4
```

这个裁剪文件要保存在 `dataset/` 中，作为独立数据集记录，而不是临时文件。

对 `*_first60.mp4` 二次实验使用 30 分钟 MASt3R 预算。如果 30 分钟内仍没有有效 `camera_info.json` / `point_cloud.ply`，或者虽然结束但 `reconstruction-readiness` 显示单 pose、空点云、`ready_for_gsplat_training=false`，则不再继续用该片段训练，改裁一个运动和视差更稳定的 10 秒片段，保存为 `dataset/<name>_best10.mp4` 后继续。

无 `ffmpeg` 的远端环境使用 OpenCV 裁剪工具：

```bash
python tools/crop_best_video_window.py dataset/bedroom_100_first60.mp4 \
  --duration 10 \
  --output dataset/bedroom_100_first60_best10.mp4 \
  --force
```

如果只需要固定裁剪前 60 秒，也可以显式指定起点：

```bash
python tools/crop_best_video_window.py dataset/bedroom_100.mp4 \
  --start 0 \
  --duration 60 \
  --output dataset/bedroom_100_first60.mp4 \
  --force
```

如果已有 project 已经完成 MASt3R/GraphDECO，只需要恢复下游 SAM2、3D mask、选帧、mesh 和 simulator 资产，使用轻量恢复入口：

```bash
bash tools/run_video2mesh_downstream_light.sh \
  exports/<run> \
  dataset/bedroom_100_first60_best10.mp4
```

默认 `SEMANTIC_SPLATS=0`，即先产出 3D object masks、object meshes 和 simulator bundle，跳过最重的 Gaussian semantic backprojection。需要语义 splat 时再显式打开：

```bash
SEMANTIC_SPLATS=1 GAUSSIAN_BACKPROJECT=0 \
bash tools/run_video2mesh_downstream_light.sh exports/<run> dataset/<video>_best10.mp4
```

## 4. GraphDECO 3DGS

远端 GraphDECO 路径：

```text
/root/autodl-tmp/workspace/gaussian-splatting
```

单独对已有 run 补跑：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh

ITERATIONS=7000 RESOLUTION=1 \
bash tools/run_graphdeco_3dgs.sh /root/autodl-tmp/workspace/Video2Mesh/exports/<run>
```

脚本会：

1. 检查 `camera_info.json` 和 full `point_cloud.ply`。
2. 拒绝 `point_cloud_10k.ply`、`point_cloud_30000.ply` 等下采样输入。
3. 生成 COLMAP-style source。
4. 调用 GraphDECO `train.py --disable_viewer`。
5. 用 `import-3dgs-result` 注册结果并导出 viewer PLY / semantic preview。

默认 GraphDECO 参数：

```text
--densify_until_iter 0
--densify_from_iter 100000000
```

原因是 MASt3R-SLAM 对短扫描片段可能给出千万级初始化点云。默认 GraphDECO densification 会继续扩点，在 32GB 显存上容易 OOM。当前约定是不降采样初始化点云，而是关闭 densification；如果后续使用更小点云或更大显存，可以通过 `GRAPHDECO_DENSIFY_UNTIL_ITER`、`GRAPHDECO_DENSIFY_FROM_ITER` 和 `GRAPHDECO_EXTRA_ARGS` 覆盖。

GraphDECO 输出默认在：

```text
scene/reconstruction/3dgs_graphdeco/
```

进入 GraphDECO 或语义 mask fusion 前，`run-pipeline` 会写入：

```text
simulator_assets/reconstruction_readiness_report.json
```

这个报告检查帧数、相机 pose、帧-相机覆盖率和 `scene/reconstruction/point_cloud.ply` 点数。默认门槛是至少 3 帧、2 个 pose、100 个点、80% camera coverage。若 MASt3R 只得到单 pose 或空点云，pipeline 会在 3DGS 训练前失败，避免继续消耗训练时间。

## 5. 点云和 PLY 约定

| 文件 | 含义 |
|---|---|
| `scene/reconstruction/point_cloud.ply` | MASt3R 原始全量点云，默认训练和语义源。 |
| `scene/reconstruction/point_cloud_10k.ply` | 轻量预览点云，不作为默认训练/分割输入。 |
| `simulator_assets/viewer_plys/*_point_cloud.ply` | 普通点云查看器友好版本。 |
| `simulator_assets/viewer_plys/*_supersplat.ply` | SuperSplat/GraphDECO 字段版本。 |

SuperSplat 需要 `f_dc_*`、`opacity`、`scale_*`、`rot_*` 等 Gaussian 字段。只有普通 XYZ/RGB 的 PLY 能被 Mac Preview 打开，但不能被 SuperSplat 当作 3DGS 加载。

## 6. 2D 到 3D 语义 mask

输入：

```text
masks/2d/<object_id>/<frame>.png
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

核心步骤：

```bash
python -m video2mesh.cli fuse-masks \
  --project-root exports/<run> \
  --point-cloud exports/<run>/scene/reconstruction/point_cloud.ply \
  --fusion-mode probability \
  --min-votes 1

python -m video2mesh.cli export-splat-masks \
  --project-root exports/<run> \
  --mask-source-ply exports/<run>/scene/reconstruction/point_cloud.ply \
  --transfer-mode nearest

python -m video2mesh.cli backproject-gaussian-probabilities \
  --project-root exports/<run>
```

输出：

```text
masks/3d/<object_id>/point_indices.json
masks/3d/<object_id>/point_probabilities.npz
simulator_assets/semantic_splats.ply
simulator_assets/semantic_gaussian_probabilities.ply
```

## 7. 选帧和物体 mesh

默认选帧策略：

```text
anchor best visible frame
  + frame offset 5
  + frame offset 10
  + random window 30
  + masked crop diversity fallback
```

命令：

```bash
python -m video2mesh.cli select-frames \
  --project-root exports/<run> \
  --selection-method svlgaussian \
  --top-k 4

python -m video2mesh.cli prepare-object-images \
  --project-root exports/<run> \
  --top-k 4 \
  --skip-missing
```

baseline mesh：

```bash
python -m video2mesh.cli reconstruct-object-meshes \
  --project-root exports/<run> \
  --method bbox \
  --skip-failed
```

生产 mesh 后续应替换为：

- Hunyuan 3D / Meshy / image-blaster 单物体生成。
- 多视角物体重建。
- 从 3D mask cloud 做更稳定的 surface reconstruction。

## 8. 仿真器导出

```bash
python -m video2mesh.cli export-simulator-assets \
  --project-root exports/<run> \
  --simulator-format mujoco unity \
  --collision-proxy bbox \
  --use-collision-proxy \
  --collider box \
  --body-type dynamic
```

输出：

```text
simulator_assets/simulator_asset_bundle.json
simulator_assets/adapters/mujoco/scene.xml
simulator_assets/adapters/unity/unity_adapter.json
simulator_assets/review/index.html
```

## 9. QA

推荐每个 run 最后执行：

```bash
python -m video2mesh.cli evaluate \
  --project-root exports/<run> \
  --json \
  --output exports/<run>/simulator_assets/evaluation_report.json

python -m video2mesh.cli validate \
  --project-root exports/<run>

python -m video2mesh.cli production-readiness \
  --project-root exports/<run> \
  --no-require-scale-calibration

python -m video2mesh.cli verify-showcase-pack \
  --project-root exports/<run> \
  --require-semantic-probability \
  --no-require-review-tar \
  --no-scan-common-remote-roots
```

关键检查：

- `evaluate.ok == true`
- `validate.ok == true`
- `showcase_pack_verification.required_failed == []`
- `3dgs_init_point_cloud_audit.full_point_cloud_contract_ready`
- `production_ready == false` 仍可接受，因为当前系统是 demo-ready baseline，不是生产级系统。

## 10. 生产升级方向

下一步按优先级：

1. GraphDECO 高质量训练稳定化：长迭代、合适分辨率、preview 指标、导入验证。
2. SAM2 base/large 或 DEVA/XMem：减少椅子、花草等物体过分割。
3. GroundingDINO / YOLO-World / OWL-ViT + VLM：给 object_id 生成可靠类别和描述。
4. 多视角物体 mesh：替换 bbox/object-mask-cloud baseline mesh。
5. 背景结构语义：floor、wall、ceiling、door、window、cabinet。
6. 真实尺度标定、碰撞体简化、质量/摩擦/恢复系数估计。
7. SceneVerse++ / PQ3D 数据桥接和评估。

## 11. 实验检查点记录

`bedroom_100` 当前结果：

```text
dataset/bedroom_100.mp4
  -> MASt3R > 1.5h 无有效相机/点云
  -> 中断
  -> dataset/bedroom_100_first60.mp4
  -> MASt3R 只得到 1 pose 和空 point_cloud.ply
  -> GraphDECO 未开始训练
  -> 裁剪最佳 10 秒片段 dataset/bedroom_100_first60_best10.mp4
  -> MASt3R 恢复 161 poses 和 full point_cloud.ply
  -> GraphDECO 真实训练 7000 iter 完成，默认关闭 densification
```

该失败说明：裁剪前 60 秒并不保证可重建；如果视频开头缺乏足够视差、纹理或稳定运动，MASt3R 仍可能只输出单 pose/空点云。本次已按该诊断改用更合适的 10 秒片段继续 GraphDECO/SAM2 后半段。

该 run 已可用 `reconstruction-readiness` 明确诊断：

```text
frames=1 poses=1 points=0
ok=False colmap=False 3dgs=False mask_fusion=False
```
