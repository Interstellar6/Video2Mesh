# Video2Mesh 当前流水线

更新时间：2026-06-24

## 1. 总体流程

```text
输入视频
  -> extract-frames (uniform dense real frames, <=200)
  -> COLMAP
  -> GraphDECO 3DGS
  -> SAM prompt + SAM2 tracking
  -> 2D-to-3D mask fusion
  -> semantic/probability splat export
  -> object frame selection
  -> object images
  -> object mesh (3DGS rendered depth/normal/mask -> fusion/extraction)
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
MAX_FRAMES=200 \
EXTRACT_EVERY=1 \
GRAPHDECO_ITERATIONS=30000 \
GRAPHDECO_SAVE_ITERATIONS="7000 30000" \
GRAPHDECO_TEST_ITERATIONS="7000 30000" \
GRAPHDECO_RESOLUTION=1 \
bash tools/run_video2mesh_quick.sh /path/to/video.mp4
```

指定真实视频时间窗，例如 `bedroom_4` 的 47-56 秒：

```bash
START_SEC=47 \
END_SEC=56 \
MAX_FRAMES=200 \
EXTRACT_EVERY=1 \
bash tools/run_video2mesh_quick.sh dataset/bedroom_4_CmEIg9gMI74/bedroom_4_Cm.mp4
```

该脚本默认：

- 输出到 `exports/<scene>_quick_<timestamp>`。
- 使用 `/root/autodl-tmp/venvs/v2m-svpp/bin/python`。
- 对输入视频/时间窗均匀抽取真实帧，默认 `MAX_FRAMES=200`、`EXTRACT_EVERY=1`。如果预估帧数超过上限，会在真实候选帧中均匀取样，不插值。
- 用 COLMAP 生成 camera poses 和 full sparse `point_cloud.ply`。
- 用 GraphDECO `train.py` 训练满血 3DGS：full COLMAP point cloud 初始化，30000 iter，保存/测试 7000 和 30000，开启 densification/pruning、opacity reset 和 SH appearance。
- 用 SAM v1 自动生成 prompts。
- 用 SAM2.1 Hiera Tiny 传播视频 masks。
- 使用 full `point_cloud.ply` 做 mask fusion、semantic transfer 和 object mask clouds。
- 导出 review pack、viewer PLY、simulator bundle 和 QA reports。

## 3. COLMAP 默认重建

默认重建入口是：

```bash
python -m video2mesh.cli run-colmap \
  --project-root exports/<run> \
  --frames-dir exports/<run>/scene/frames
```

`run-pipeline --run-colmap` 会在抽帧后自动执行该阶段，并把 COLMAP text model 导入为：

```text
scene/cameras/camera_info.json
scene/reconstruction/point_cloud.ply
```

导入时只保留 COLMAP 成功注册位姿的真实帧，因此后续 3DGS、SAM2、mask fusion、preview 和 object frame selection 都使用同一个稠密帧目录，不使用 MASt3R keyframes。

如果需要回退旧 MASt3R-SLAM 路径，显式设置：

```bash
RUN_COLMAP=0 RUN_MAST3R=1 bash tools/run_video2mesh_quick.sh /path/to/video.mp4
```

如果 COLMAP readiness 显示注册 pose 太少、空点云或帧-相机覆盖率不足，选择另一个真实时间窗重跑；不要用插值帧补齐输入。

如果已有 project 已经完成 COLMAP/GraphDECO，只需要恢复下游 SAM2、3D mask、选帧、mesh 和 simulator 资产，使用轻量恢复入口：

```bash
bash tools/run_video2mesh_downstream_light.sh \
  exports/<run> \
  dataset/<video>.mp4
```

默认 `SEMANTIC_SPLATS=0`，即先产出 3D object masks、object meshes 和 simulator bundle，跳过最重的 Gaussian semantic backprojection。需要语义 splat 时再显式打开：

```bash
SEMANTIC_SPLATS=1 GAUSSIAN_BACKPROJECT=0 \
bash tools/run_video2mesh_downstream_light.sh exports/<run> dataset/<video>_best10.mp4
```

该脚本仍用 full scene point cloud 做 object mask fusion；为了避免背景结构 RANSAC 在千万级点云上压满机器，默认只对背景平面拟合采样：

```text
BACKGROUND_RANSAC_MAX_POINTS=200000
BACKGROUND_FIT_MAX_POINTS=80000
```

导师展示前刷新并检查可展示产物：

```bash
bash tools/audit_showcase_artifacts.sh exports/<run>
```

重点看这些文件是否存在：

```text
simulator_assets/review/index.html
simulator_assets/advisor_demo_summary.md
simulator_assets/showcase_pack_verification.json
simulator_assets/viewer_plys/scene_3dgs_supersplat.ply
simulator_assets/simulator_asset_bundle.json
simulator_assets/adapters/unity/unity_adapter.json
```

## 4. GraphDECO 3DGS

远端 GraphDECO 路径：

```text
/root/autodl-tmp/workspace/gaussian-splatting
```

单独对已有 run 补跑：

```bash
cd /root/autodl-tmp/workspace/Video2Mesh

ITERATIONS=30000 SAVE_ITERATIONS="7000 30000" TEST_ITERATIONS="7000 30000" RESOLUTION=1 \
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
--iterations 30000
--save_iterations 7000 30000
--test_iterations 7000 30000
--sh_degree 3
--densify_from_iter 500
--densify_until_iter 15000
--densification_interval 100
--opacity_reset_interval 3000
```

这是默认生产训练档：不使用 `point_cloud_10k.ply` / `point_cloud_30000.ply`
初始化，保留 full COLMAP/重建 point cloud，并启用 GraphDECO 的
densification/pruning、opacity reset 和 SH appearance。只有显式做 smoke
test 或显存调试时，才用环境变量覆盖为短训练或关闭 densification。

GraphDECO 输出默认在：

```text
scene/reconstruction/3dgs_graphdeco/
```

进入 GraphDECO 或语义 mask fusion 前，`run-pipeline` 会写入：

```text
simulator_assets/reconstruction_readiness_report.json
```

这个报告检查帧数、相机 pose、帧-相机覆盖率和 `scene/reconstruction/point_cloud.ply` 点数。默认门槛是至少 3 帧、2 个 pose、100 个点、80% camera coverage。若 COLMAP/重建阶段只得到单 pose 或空点云，pipeline 会在 3DGS 训练前失败，避免继续消耗训练时间。

## 5. 点云和 PLY 约定

| 文件 | 含义 |
|---|---|
| `scene/reconstruction/point_cloud.ply` | COLMAP/重建阶段原始全量点云，默认训练和语义源。 |
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

临时 baseline mesh：

```bash
python -m video2mesh.cli reconstruct-object-meshes \
  --project-root exports/<run> \
  --method bbox \
  --skip-failed
```

这一步只把 fused 3D mask cloud 先转成可查看的 OBJ，方便检查物体尺度、
位置和 simulator 导出接口；它不是最终的 3DGS-to-mesh 技术路线。
当前这类 mesh 明显会太碎：会出现大量 disconnected triangle islands、
holes、floating sheets，很多对象不是 watertight。原因是直接从稀疏/不均匀
mask cloud 做 surface reconstruction 时，点支持不足且噪声点会被连成片。
因此它只能作为 debug/baseline，不能作为最终物体模型展示。

生产 mesh 默认路线改为：

```text
trained GraphDECO 3DGS
  + object masks
  + registered camera poses
  -> render object-centric multi-view RGB/depth/normal/mask
  -> TSDF fusion over masked depth/normal observations
  -> marching cubes / Poisson surface extraction
  -> optional NeuS-style SDF refinement
  -> texture baking + mesh simplification + collider generation
  -> simulator-ready OBJ/GLB
```

实现要求：

- depth、normal、mask 来自真实相机位姿下的 3DGS 多视角渲染，不用插值帧。
- TSDF fusion 是默认几何融合路径，Poisson 可作为 normal-oriented surface extraction fallback。
- NeuS-style refinement 作为高质量后处理，用同一组真实视角和 mask 约束优化 SDF surface。
- surface extraction 后需要做 connected-component filtering、hole filling、mesh simplification 和 watertight/fragment QA，避免再次输出碎片化 mesh。
- 旧的 object-mask-cloud meshing 只保留为 debug/baseline，不作为生产质量结果。

当前实现入口：

```bash
python -m video2mesh.cli export-3dgs-mesh-observations \
  --project-root exports/<run> \
  --max-frames-per-object 6 \
  --device cuda

python -m video2mesh.cli reconstruct-3dgs-object-meshes \
  --project-root exports/<run> \
  --method auto \
  --format obj \
  --skip-failed

python -m video2mesh.cli prepare-neus-surface-jobs \
  --project-root exports/<run> \
  --provider external_neus_sdf
```

第一步从 active 3DGS 和真实注册相机位姿渲染每个 object 的
`rgb.png`、`depth.npy/png`、`normal.npy/png`、`mask.png`。第二步默认先尝试
TSDF fusion；如果 TSDF 没有足够 masked depth，会回退到从这些 3DGS-rendered
depth observations 反投影点云，再用 Poisson surface extraction 出 mesh。
第三步把同一批观测打包成 NeuS-style SDF optimization 的外部 backend 作业；
仓库内不伪装实现神经 SDF 训练器，但会固定输入/输出合同，后续可接 NeuS/VolSDF/NeuS2
等后端。

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
4. 3DGS-to-mesh：从 3DGS 多视角渲染 depth/normal/mask，再做 TSDF fusion / Poisson / NeuS-style surface extraction，替换 bbox/object-mask-cloud baseline mesh。
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
  -> GraphDECO 真实训练应使用默认满血档：30000 iter，保存 7000/30000，开启 densification/pruning、opacity reset、SH appearance
```

该失败说明：裁剪前 60 秒并不保证可重建；如果视频开头缺乏足够视差、纹理或稳定运动，MASt3R 仍可能只输出单 pose/空点云。本次已按该诊断改用更合适的 10 秒片段继续 GraphDECO/SAM2 后半段。

该 run 已可用 `reconstruction-readiness` 明确诊断：

```text
frames=1 poses=1 points=0
ok=False colmap=False 3dgs=False mask_fusion=False
```
