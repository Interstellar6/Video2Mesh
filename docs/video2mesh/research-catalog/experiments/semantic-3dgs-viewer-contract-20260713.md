---
title: bedroom_4 语义 3DGS、SuperSplat 与双面 Mesh 修复
id: video2mesh-experiments-semantic-3dgs-viewer-contract-20260713
category: 调研目录
summary: 记录 bedroom_4 语义 3DGS 的文件膨胀、GraphDECO 几何合同、AnySplat 相机坐标错配、轻量 SuperSplat overlay 与 mesh 双面查看修复。
tags:
  - Video2Mesh
  - Experiment
  - Semantic 3DGS
  - GraphDECO
  - AnySplat
  - SuperSplat
visibility: public
---

# bedroom_4 语义 3DGS、SuperSplat 与双面 Mesh 修复

## 结论

`bedroom_4` 当前应该始终保持分层资产，而不是把所有用途塞进一个 PLY：

```text
GraphDECO / AnySplat scene 3DGS
  -> visual base layer
2D GroundingDINO + SAM2 masks
  -> SVLGaussian-style probability backprojection
binary semantic core PLY
  -> mesh semantic transfer / object split / sidecar
light semantic overlay PLY
  -> load together with the visual base in SuperSplat
COLMAP / AnySplat / SuGaR mesh
  -> collider or geometry proxy
double-sided display PLY
  -> human inspection only, never replaces collider topology
```

![GraphDECO clean visual 3DGS](../assets/semantic-viewer-20260713/01-graphdeco-visual.png "GraphDECO clean 3DGS：墙面和地板在保背景清理后仍保留完整")

GraphDECO clean 3DGS 的视觉底图仍是当前 P0 visual layer：墙面和地板没有被 aggressive clean 删除。语义不应重新生成另一份几何，也不应把 dense semantic point cloud 或 3D mask 最近邻贴回它；正确做法是用 2D mask probability 投影到这个已经训练完成并 clean 的 Gaussian 序列上。

## 发现的问题

![旧 GraphDECO semantic SuperSplat 预览](../assets/semantic-viewer-20260713/02-graphdeco-semantic-before.png "旧语义预览：分类色可见，但视觉表面与原始 3DGS 观感不一致，且文件过大")

旧版有三类相互叠加的问题：

| 问题 | 根因 | 修复 |
|---|---|---|
| `semantic_splats.ply` 约 1GB，打开会卡死 | binary GraphDECO PLY 被 ASCII 重写并追加属性 | 改为 binary little-endian vertex rewrite，原有 Gaussian 属性原样复制 |
| semantic SuperSplat 文件异常大 | DC-only 预览仍被补了 45 个全零 `f_rest` | DC-only PLY 不再写全零 SH；大标签数组移到 compressed NPZ sidecar |
| semantic 3DGS 看起来不像 visual 3DGS | viewer preview、viewer-safe 变体和 full semantic core 容易混用 | manifest 明确区分 `semantic_splats_ply`、`semantic_supersplat_full_ply`、`semantic_supersplat_overlay_ply`；几何指纹强制一致 |

每次 `backproject-gaussian-probabilities` 都会对 `means/opacities/scales/quats` 计算 SHA-256。若 semantic core 的几何指纹与指定 scene 3DGS 不同，命令直接失败，不会交付一个标签正确但空间已经变形的文件。

### 推荐的 SuperSplat 打开方式

不要把 `semantic_splats.ply` 直接拖进 SuperSplat。它是 full-resolution pipeline core，含 semantic property，服务 mesh transfer。

1. 打开 `scene_3dgs...ply` 作为原始视觉底图。
2. 再打开 `semantic_*_overlay_supersplat.ply` 作为分类颜色 overlay。
3. 需要人工检查完整标签时读取 overlay 的 `*_labels.npz` / `*_labels.json`，不要用超大 JSON 数组当渲染输入。

这种方式保留原始 SH visual appearance，同时让语义层只承载标签色，不重复存整份场景。

## GraphDECO V2/V3 实验

远端 run：`/data/zyx/workspace/Video2MeshWorkspace/video2mesh_runs/bedroom_4_fresh_full_cpu_seq30_8gpu_dense_20260711_0600`。

| 产物 | 实测状态 | 用途 |
|---|---:|---|
| `point_cloud_clean_strict.ply` | 954,394 Gaussians | GraphDECO visual base |
| `semantic_splats_v2.ply` | 234MB binary，geometry SHA verified | full semantic core，给 mesh transfer |
| `semantic_gaussian_probability_supersplat.ply` | 62MB DC-only semantic preview | 兼容性检查，不作为首选视觉层 |
| `semantic_gaussian_probability_semantic_overlay_supersplat.ply` | 27MB | 推荐与 scene base 一起在 SuperSplat 打开 |

![COLMAP dense Delaunay mesh](../assets/semantic-viewer-20260713/03-colmap-mesh.png "COLMAP Delaunay dense mesh：当前稳定的场景 collider/geometry proxy")

![COLMAP semantic mesh](../assets/semantic-viewer-20260713/04-colmap-semantic-mesh.png "当前质量较好的 semantic mesh；保留在默认 pipeline")

COLMAP Delaunay scene mesh 与 local multi-sample semantic mesh 是当前最可用的一组 geometry/semantic 代理，保留在 quick pipeline。新的 binary semantic reader 已接入 local mesh transfer，避免格式修复后断开 semantic mesh 路线。

## AnySplat 坐标合同修复

![AnySplat visual scene](../assets/semantic-viewer-20260713/05-anysplat-visual.png "AnySplat 原生 visual scene：主体和背景相对完整、干净")

AnySplat 的 visual 结果整体完整干净，但新视角仍有空中丝状带。它是前馈 Gaussian/depth/pose 的一致性问题，后续可以研究 opacity/scale-aware trimming、multi-view reprojection consistency 和墙/地板平面保护；本轮没有把它伪装成已经解决。

![AnySplat new-view stripes](../assets/semantic-viewer-20260713/06-anysplat-stripes.png "AnySplat 新视角的丝状条带：尚未作为 collider 或真实 surface 使用")

旧 AnySplat semantic run 的真正错误不是“墙体遮挡算法不够强”，而是把 AnySplat **19 张输入图、预测 camera、预测坐标尺度**，拿去配 Video2Mesh COLMAP 的 **80 帧 camera_info 和原始画幅 mask**。这会把 mask 投到错误的射线上，造成标签落到墙面。

新工具 `tools/prepare_anysplat_semantic_projection.py` 完成：

- 19/19 AnySplat input image 与 project frame 匹配；最大 thumbnail MSE 为 `0.00421`。
- 380 张 mask 按 AnySplat `process_image` 的 448x448 center crop 规则重采样。
- `predicted_cameras.npz` 转为 AnySplat world-to-camera `camera_info_anysplat.json`。
- AnySplat V2 semantic core 以该相机合同重投，2,079,470 Gaussian 的 geometry SHA 与原始 `gaussians.ply` 完全一致。
- V2 full semantic core 为 151MB binary；推荐 viewer overlay 为 11MB。

![旧 AnySplat semantic 结果](../assets/semantic-viewer-20260713/09-anysplat-semantic-before.png "旧 AnySplat semantic cloud：因相机/裁切错配，标签被错误投到墙面")

## Mesh 的 backface culling 修复

![AnySplat mesh 一面](../assets/semantic-viewer-20260713/07-anysplat-mesh-back.png "AnySplat Poisson mesh：单面查看时一侧更完整")

![AnySplat mesh 另一面](../assets/semantic-viewer-20260713/08-anysplat-mesh-front.png "同一 mesh 翻到另一侧时面片消失或破碎，属于 winding/material 可见性问题")

PLY 本身没有 `doubleSided` material 开关。为避免查看器默认 backface culling 导致“房间正反面质量不同”的误判，pipeline 现在：

- collider/source mesh 仍保留原始单面三角拓扑；
- 输出 `*_double_sided.ply` display companion，包含反向 winding；
- semantic debug PLY 和 object semantic PLY 默认写正反两套 face；
- GLB/exporter 应使用 `doubleSided: true`，不以单面 viewer 判断 mesh 是否存在。

![旧 AnySplat semantic mesh](../assets/semantic-viewer-20260713/10-anysplat-semantic-mesh-before.png "旧 AnySplat semantic mesh 也受单面查看影响；新的 display companion 会保留双面可见性")

这不会把 double faces 当作新的 collider 真值，也不会解决 AnySplat mesh 自身的孔洞、条带或尺度不一致；它只解决查看器的面剔除误判。

## SuGaR 边界

![SuGaR observed view](../assets/semantic-viewer-20260713/11-sugar-visual.png "SuGaR 在已观测视角里墙、窗和地板贴合较好")

![SuGaR new view](../assets/semantic-viewer-20260713/12-sugar-new-view.png "SuGaR 切换新视角后暴露墙面 Gaussian 没有被规范到平面上的碎裂")

SuGaR 的背景在已观测视角里比 GraphDECO 更贴合墙、窗和地板，但换到新视角会暴露墙面未被约束到平面的碎裂。当前结论是保留它作为 visual mesh / surface-aligned Gaussian 对照，不把它升级为 P0 collider truth。SuGaR refined mesh 同样输出双面 display PLY；其 semantic full core 也将沿用 binary core + overlay contract，不再输出 ASCII 大文件供 viewer 直接打开。

![SuGaR single-sided mesh symptom](../assets/semantic-viewer-20260713/13-sugar-mesh-before.png "SuGaR coarse mesh 在单面查看下会因 winding/backface culling 显得像缺失")

![SuGaR semantic mesh symptom](../assets/semantic-viewer-20260713/14-sugar-semantic-mesh-before.png "SuGaR semantic mesh 同样需要双面 display companion 才能正确审阅")

## 默认路线

`tools/run_video2mesh_quick.sh` 现在默认开启 `GAUSSIAN_BACKPROJECT=1`：

```text
clean GraphDECO 3DGS
  -> 2D mask probability backprojection (binary semantic core)
  -> local multi-sample semantic mesh transfer
  -> double-sided display mesh companion
```

默认仍关闭 adapter 和 OBJ object reconstruction。3DGS 负责视觉，COLMAP Delaunay / mesh 负责 collider，语义点云与 semantic mesh 是 sidecar/inspection 资产，不替代物理几何。

## 未解决项

1. AnySplat 新视角丝状条带仍需单独的 geometry-aware trimming/regularization 实验。
2. AnySplat 和 GraphDECO 的 absolute scale 仍不应混用；它们各自使用自己的 camera contract。
3. 语义的 object-level accuracy 还依赖 GroundingDINO prompt、SAM2 track 质量和多视角覆盖；本次修复保证投影坐标与几何不再错配，不把当前类别识别误差写成已经解决。
