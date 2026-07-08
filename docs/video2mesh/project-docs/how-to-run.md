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

## 本地文档站

```bash
python3 docs-blog/build_video2mesh_site_data.py
python3 -m http.server 4173 -d docs-blog/_public
```

公开站入口：`http://127.0.0.1:4173/video2mesh/`。管理端入口：`http://127.0.0.1:4173/admin/`。

## 输出位置

```text
exports/<run>/
  scene/
  masks/
  simulator_assets/
  mesh_recon_results/
  review_pack/
```

## SimFoundry 复刻分支当前证据

当前分支 `codex/simfoundry-replica` 的本轮验收收口到资产生成，不做 Blender / Isaac / MuJoCo 适配，也不做动态仿真。目标是能稳定产出六类资产：

| 资产 | 当前证据 |
|---|---|
| 高质量 3DGS 点云 | `tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/3dgs_point_cloud_clean_iteration30000.ply`，GraphDECO 30k clean，971,305 vertices |
| 语义分割 3DGS 点云 | `exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/semantic_3dgs_from_semantic_mesh_transfer.ply`，971,305 vertices，含 `object_id` / `object_probability` |
| 高质量 mesh 重建 | `tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_recon_results/colmap_delaunay_dense/mesh.ply`，82,920 vertices / 167,082 faces |
| 语义分割 mesh | `exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/semantic_object_meshes/semantic_object_meshes.json`，16 objects，73,970 vertices / 141,993 faces |
| 整个场景 GLB | `exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/scene_glb/scene.glb`，16 objects，约 2.9 MB |
| 单个物体 GLB | `exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/semantic_object_glbs/semantic_object_glbs.json`，`status=semantic_object_glbs_exported`，16/16 objects，error_count=0 |

语义 3DGS 当前是从已有 semantic mesh debug PLY 最近邻转移到 clean GraphDECO 30k 3DGS 的本地恢复 baseline，不是完整 SVLGaussian/SimFoundry 2D 概率反投影。单体 GLB 已补成可回放命令 `export-semantic-object-glbs`，不依赖仿真器 adapter 或动态 gate。

复验单体 GLB：

```bash
PYTHONPATH=. uv run --with numpy --with trimesh python -m video2mesh.cli export-semantic-object-glbs \
  --project-root exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534 \
  --semantic-meshes exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/semantic_object_meshes/semantic_object_meshes.json \
  --output-dir exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/semantic_object_glbs \
  --json \
  --fail-on-empty \
  --fail-on-failed
```

复验整场景 GLB：

```bash
PYTHONPATH=. uv run --with numpy --with trimesh python -m video2mesh.cli export-simfoundry-scene-glb \
  --project-root exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534 \
  --bundle exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/simulator_asset_bundle.json \
  --output-dir exports/simfoundry_bedroom4_static_object_scene_p1_20260708_161534/simulator_assets/scene_glb \
  --json \
  --fail-on-empty
```

## 验证重点

- `simulator_asset_bundle.json` 是否能索引所有资产。
- visual layer 和 collider 是否在同一坐标系。
- mesh 是否能被 Web/Unity 读取。
- 语义标签是否能投到 object/face sidecar。
- 当前阶段不验收 Blender / Isaac / MuJoCo 适配和动态仿真。
- 大型 3DGS/PLY 不直接进入 GitHub Pages artifact。
