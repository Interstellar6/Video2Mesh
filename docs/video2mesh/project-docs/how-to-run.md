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
     - KNN/MAD 普通离群点
     - 低透明细长 Gaussian
     - COLMAP dense 分位 bbox
     - DBSCAN detached cluster 过滤
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

常用调参：

```bash
# 关闭 strict 3DGS cluster clean，仅用于对比
STRICT_3DGS_CLEAN=0 bash run.sh dataset/<video>.mp4

# 背景墙面被 RANSAC 分到 other_structure 时，默认先导出；可关闭
BACKGROUND_PLANE_INCLUDE_OTHER_PLANES=0 bash run.sh dataset/<video>.mp4

# 只写 object merge 建议，不自动应用
OBJECT_MERGE_APPLY=0 bash run.sh dataset/<video>.mp4
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
- 普通 KNN/MAD 只能删孤立散点；右下角那种“自己内部很密、但离主体很远”的小簇需要 strict cluster-level clean。
- 左墙缺失通常来自背景平面分类过严：RANSAC 找到了平面，但被标成 `other_structure` 后没有导出。quick run 现在默认打开 `BACKGROUND_PLANE_INCLUDE_OTHER_PLANES=1`，先把这些结构保留下来，再由语义/人工修正。
