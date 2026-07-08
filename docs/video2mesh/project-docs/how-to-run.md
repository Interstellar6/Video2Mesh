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

## 验证重点

- `simulator_asset_bundle.json` 是否能索引所有资产。
- visual layer 和 collider 是否在同一坐标系。
- mesh 是否能被 Web/Unity 读取。
- 语义标签是否能投到 object/face sidecar。
- 大型 3DGS/PLY 不直接进入 GitHub Pages artifact。
