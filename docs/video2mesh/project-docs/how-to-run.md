---
title: Video2Mesh 如何运行
id: video2mesh-how-to-run
category: 项目文档
visibility: public
summary: 记录 Video2Mesh 当前常用运行入口、远端路径、输出目录和验证方式。
tags:
  - Runbook
  - CLI
  - QA
---

# Video2Mesh 如何运行

## 远端常用入口

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true
bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

`bash run.sh` 和 `tools/run_video2mesh_quick.sh` 当前默认路线：

```text
video
  -> COLMAP sparse + dense fused.ply
  -> 清理 dense fused.ply 后作为 GraphDECO 3DGS 初始化点云
  -> GraphDECO 30k 训练
  -> point_cloud_clean_strict.ply
     - COLMAP dense 分位 bbox
     - DBSCAN detached cluster 过滤
     - 背景平面保护
     - 默认不启用 KNN/MAD 稀疏点删除或低透明细长 Gaussian 删除
  -> GroundingDINO bbox prompts
     - GroundingDINO 缺权重/环境时 fallback 到 auto-prompts
  -> SAM2/2D mask tracking
  -> 2D-to-3D semantic fusion
  -> 保守 object-fragment merge
  -> semantic splats / viewer PLY
  -> COLMAP dense Delaunay scene mesh
  -> mesh semantic transfer + object PLY split
  -> object PLY mesh reconstruction
  -> collider / physics proxy asset bundle
```

当前默认不导出 simulator adapters，不默认导出 OBJ object mesh。原因是这两步现在不是质量瓶颈，OBJ 路径在 bedroom_4 上出现过碎裂/质量劣化；默认保留 PLY mesh 和 simulator asset bundle。需要 adapter 时显式设置：

```bash
RUN_SIMULATOR_ADAPTERS=1 bash run.sh dataset/<video>.mp4
```

Gaussian probability backprojection 现在也不作为 quick run 默认阻塞项。默认路线直接用 `semantic_splats.ply` 对 scene mesh 做 local multi-sample semantic transfer；需要复现实验性的投影概率融合时再显式打开：

```bash
GAUSSIAN_BACKPROJECT=1 bash run.sh dataset/<video>.mp4
```

常用调参：

```bash
# 关闭 strict 3DGS cluster clean，仅用于对比
STRICT_3DGS_CLEAN=0 bash run.sh dataset/<video>.mp4

# 关闭 strict clean 中的背景平面保护，仅用于定位是否误保留了大平面噪声
STRICT_3DGS_PRESERVE_BACKGROUND_PLANES=0 bash run.sh dataset/<video>.mp4

# 重新启用 KNN/MAD 或细长 Gaussian 过滤，仅用于对比噪声清理；默认关闭以保护墙/地板
STRICT_3DGS_GEOMETRIC_OUTLIERS=1 bash run.sh dataset/<video>.mp4
STRICT_3DGS_ELONGATION_FILTER=1 bash run.sh dataset/<video>.mp4

# 背景墙面被 RANSAC 分到 other_structure 时，默认先导出；可关闭
BACKGROUND_PLANE_INCLUDE_OTHER_PLANES=0 bash run.sh dataset/<video>.mp4

# 只写 object merge 建议，不自动应用
OBJECT_MERGE_APPLY=0 bash run.sh dataset/<video>.mp4
```

## 多 GPU 运行

mil8 这类 8 卡机器上，单个 quick run 里最适合多卡加速的是 COLMAP dense stereo；GraphDECO 官方 trainer 在当前 pipeline 里仍按单场景单进程运行。推荐做法是不要在外层固定 `CUDA_VISIBLE_DEVICES=0`，而是分阶段指定：

```bash
COLMAP_USE_GPU=1 \
COLMAP_GPU_INDEX=0,1,2,3,4,5,6,7 \
COLMAP_DENSE_GPU_INDEX=0,1,2,3,4,5,6,7 \
GRAPHDECO_CUDA_VISIBLE_DEVICES=0 \
GROUNDINGDINO_DEVICE=cuda:1 \
SAM_DEVICE=cuda:1 \
SAM2_DEVICE=cuda:1 \
bash run.sh dataset/<video>.mp4
```

如果某张卡被占用，可以从 `COLMAP_DENSE_GPU_INDEX` 里删掉对应编号。后续做多场景或多参数训练时，可以启动多个独立 run，并用不同的 `GRAPHDECO_CUDA_VISIBLE_DEVICES` 分配到不同 GPU；这比临时把 GraphDECO 改成 DDP 更稳。

外部 object mesh / production-upgrade jobs 也按外层任务并行来吃多卡。生成的 `run_mesh_jobs.sh` 默认仍是串行；需要并行时显式打开：

```bash
RUN_PARALLEL=1 GPU_POOL=0,1,2,3 MAX_PARALLEL_JOBS=4 bash run_mesh_jobs.sh
```

## 本地文档站

```bash
python3 docs-blog/build_site.py
python3 -m http.server 4173 -d docs-blog/_public
```

公开站入口：`http://127.0.0.1:4173/video2mesh/`。管理端入口：`http://127.0.0.1:4173/admin/`。

线上文档入口：`https://relumeow.top/video2mesh/`。

## 输出位置

```text
exports/<run>/
  scene/
  masks/
  simulator_assets/
  mesh_recon_results/
  review_pack/
```

## 验证重点

- `simulator_asset_bundle.json` 是否能索引所有资产。
- visual layer 和 collider 是否在同一坐标系。
- mesh 是否能被 Web/Unity 读取。
- 语义标签是否能投到 object/face sidecar。
- 大型 3DGS/PLY 不直接进入 GitHub Pages artifact。

## 近期 bedroom_4 经验

- `scene_3dgs_supersplat.ply` 约 118 MB 不等于点数极少；这类 viewer PLY 是压成 SuperSplat 兼容字段后的可视化副本。质量差的主因更常见是 Gaussian scale/rotation 不健康、细长低透明光斑和 detached dense floater cluster，而不是单纯文件体积。
- 普通 KNN/MAD 只能删孤立散点；右下角那种“自己内部很密、但离主体很远”的小簇需要 strict cluster-level clean。当前默认的 strict clean 会用 COLMAP dense fused.ply 的分位 bbox + DBSCAN 删除 detached cluster，同时保护大平面背景；KNN/MAD 稀疏点删除和低透明细长 Gaussian 删除默认关闭，因为它们在 bedroom_4 上会误删墙面/地板。
- 在 `bedroom_4_mil8_cuda_gpu0_20260708_213645` 上复测，raw 3DGS 为 965,577 个 Gaussian。旧 strict clean 保留 746,464 个，其中 `elongated & weak` 删除 140,174 个；关闭细长过滤后保留 890,394 个；最终 scene-only clean 只保留 COLMAP bbox + DBSCAN detached cluster + 背景平面保护，保留 963,296 个，仅删除 2,281 个场景外/小簇点。
- 左墙缺失通常来自背景平面分类过严：RANSAC 找到了平面，但被标成 `other_structure` 后没有导出。quick run 现在默认打开 `BACKGROUND_PLANE_INCLUDE_OTHER_PLANES=1`，先把这些结构保留下来，再由语义/人工修正。
