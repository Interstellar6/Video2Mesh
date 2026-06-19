# Video2Mesh 真实实验运行手册

更新时间：2026-06-20

## 1. 远端环境

```bash
ssh -p 14225 root@connect.westd.seetacloud.com
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true
```

推荐 Python：

```text
/root/autodl-tmp/venvs/v2m-svpp/bin/python
```

SAM2 Python：

```text
/root/autodl-tmp/workspace/venvs/v2m-sam2-clean/bin/python
```

不要优先用 conda base 跑完整流程；base 的 PyTorch 可用，但历史上 OpenCV/NumPy/Scipy 组合出现过 ABI 和递归问题。

## 2. 一条视频跑完整流程

```bash
cd /root/autodl-tmp/workspace/Video2Mesh

bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

输出目录：

```text
exports/<video_slug>_quick_<timestamp>
```

当前默认：

- MASt3R-SLAM 抽取 keyframes、camera poses 和 full point cloud。
- GraphDECO 训练 3DGS。
- SAM v1 生成 prompts。
- SAM2.1 tiny 跟踪 masks。
- full `point_cloud.ply` 做 3D semantic fusion。
- 导出 viewer PLY、object images、baseline mesh、simulator bundle 和 QA。

## 3. bedroom_100 当前实验规则

输入：

```text
dataset/bedroom_100.mp4
```

如果 MASt3R-SLAM 运行超过 1.5 小时仍无：

```text
exports/<run>/scene/cameras/camera_info.json
exports/<run>/scene/reconstruction/point_cloud.ply
```

则停止该次 MASt3R，裁剪前 60 秒：

```bash
ffmpeg -y \
  -i dataset/bedroom_100.mp4 \
  -t 60 \
  -c copy \
  dataset/bedroom_100_first60.mp4
```

如 stream copy 失败：

```bash
ffmpeg -y \
  -i dataset/bedroom_100.mp4 \
  -t 60 \
  -c:v libx264 -crf 18 -preset veryfast \
  -c:a copy \
  dataset/bedroom_100_first60.mp4
```

然后把裁剪视频作为新数据集重跑：

```bash
bash tools/run_video2mesh_quick.sh dataset/bedroom_100_first60.mp4
```

## 4. 监控命令

查看进程：

```bash
ps -eo pid,ppid,pgid,etime,stat,pcpu,pmem,cmd | \
  grep -E "run_video2mesh_quick|MASt3R-SLAM|mast3r|graphdeco|train.py" | \
  grep -v grep
```

查看 GPU：

```bash
nvidia-smi
```

查看关键输出是否出现：

```bash
find exports/<run>/scene -maxdepth 4 \
  \( -name camera_info.json -o -name point_cloud.ply \) -ls
```

查看 MASt3R 日志：

```bash
tail -80 exports/<run>/logs/mast3r_slam_run.log
```

## 5. 单独补跑 GraphDECO

如果 run 已经有相机和 full cloud，但 active 3DGS 不是 GraphDECO：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh

ITERATIONS=7000 RESOLUTION=1 \
bash tools/run_graphdeco_3dgs.sh exports/<run>
```

低显存 fallback 顺序：

1. 保持 full `point_cloud.ply`。
2. 降低 `RESOLUTION`，例如 `RESOLUTION=2`。
3. 降低 `ITERATIONS`，例如 `ITERATIONS=3000`。
4. 只有完全无法训练时，才考虑实验性点数限制；这不是默认策略。

## 6. 展示产物

| 目标 | 文件 |
|---|---|
| 总览网页 | `simulator_assets/review/index.html` |
| 场景普通点云 | `simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` |
| 场景 SuperSplat | `simulator_assets/viewer_plys/scene_3dgs_supersplat.ply` |
| 语义 SuperSplat | `simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply` |
| 概率语义 3DGS | `simulator_assets/semantic_gaussian_probability_supersplat.ply` |
| 3D semantic masks | `simulator_assets/object_masks_3d/*.ply` |
| 物体相关帧 | `objects/<object_id>/selected_frames/` |
| 物体裁图 | `objects/<object_id>/object_images/` |
| 粗 mesh | `simulator_assets/reconstructed_meshes/<object_id>/` |
| 仿真资产 | `simulator_assets/simulator_asset_bundle.json` |
| MuJoCo | `simulator_assets/adapters/mujoco/scene.xml` |
| Unity | `simulator_assets/adapters/unity/unity_adapter.json` |
| QA | `simulator_assets/evaluation_report.json` |

## 7. 结束后检查

```bash
python -m video2mesh.cli evaluate \
  --project-root exports/<run> \
  --json \
  --output exports/<run>/simulator_assets/evaluation_report.json

python -m video2mesh.cli production-readiness \
  --project-root exports/<run> \
  --no-require-scale-calibration

python -m video2mesh.cli verify-showcase-pack \
  --project-root exports/<run> \
  --require-semantic-probability \
  --no-require-review-tar \
  --no-scan-common-remote-roots
```

如果 `production_ready=false` 但 `demo_ready=true`，当前阶段可以接受。主要原因通常是：语义标签仍弱、mesh 仍粗、scale/physics 未真实标定。
