# Video2Mesh 展示清单：milscene3 与当前默认流程

更新时间：2026-06-20

## 1. 当前展示定位

`milscene3_full_20260618_124804` 是已完成的端到端 baseline 展示包，证明工程链路已经闭合：

```text
扫描视频 -> 3DGS -> 3D semantic masks -> object frames -> mesh -> simulator assets
```

它不是最终生产质量结果。新实验默认切到 GraphDECO 3DGS；该历史 run 中的 active 3DGS 仍是 minimal gsplat full-cloud baseline。

远端路径：

```text
/root/autodl-tmp/workspace/Video2Mesh/exports/milscene3_full_20260618_124804
```

本地路径：

```text
/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/exports/milscene3_full_20260618_124804
```

## 2. 展示产物表

| 展示目标 | 文件 |
|---|---|
| 总览网页 | `simulator_assets/review/index.html` |
| 场景级 3DGS | `simulator_assets/viewer_plys/scene_3dgs_supersplat.ply` |
| 普通场景点云 | `simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` |
| 语义 3DGS | `simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply` |
| 语义普通点云 | `simulator_assets/viewer_plys/semantic_3dgs_point_cloud.ply` |
| Gaussian probability | `simulator_assets/semantic_gaussian_probability_supersplat.ply` |
| 3D mask clouds | `simulator_assets/object_masks_3d/*.ply` |
| 物体选帧 | `objects/<object_id>/selected_frames/` |
| 物体裁图 | `objects/<object_id>/object_images/` |
| baseline mesh | `simulator_assets/reconstructed_meshes/<object_id>/` |
| simulator bundle | `simulator_assets/simulator_asset_bundle.json` |
| MuJoCo adapter | `simulator_assets/adapters/mujoco/scene.xml` |
| Unity adapter | `simulator_assets/adapters/unity/unity_adapter.json` |
| evaluation | `simulator_assets/evaluation_report.json` |
| showcase verification | `simulator_assets/showcase_pack_verification.json` |
| production readiness | `simulator_assets/production_readiness_report.json` |

## 3. 推荐展示顺序

1. 打开 `review/index.html`，先讲完整链路。
2. 用 SuperSplat 打开 `scene_3dgs_supersplat.ply`，展示场景级 3DGS。
3. 打开 `semantic_3dgs_supersplat.ply` 或 `semantic_gaussian_probability_supersplat.ply`，展示语义已经写入 Gaussian/point representation。
4. 打开 `object_masks_3d/*.ply`，展示每个 object/background structure 的 3D mask。
5. 展示 selected frames 和 object crops，说明后续 mesh 是从相关帧或 mask cloud 生成。
6. 展示 reconstructed meshes 和 simulator asset bundle。
7. 最后展示 readiness/QA，明确 baseline 和 production gap。

## 4. 当前系统能力

已完成：

- 视频到相机/点云。
- 场景级 3DGS 表达。
- SAM2 video masks 接口。
- 2D masks 到 3D semantic masks。
- semantic/probability PLY 导出。
- object frame selection。
- coarse object mesh。
- simulator bundle 和 MuJoCo/Unity adapter。
- SceneVerse++/SVPP-style export contract。

仍是 baseline：

- 3DGS 画质依赖当前 trainer 和位姿质量。
- object labels 仍需要 open-vocabulary/VLM。
- SAM2 tiny 仍会把折叠椅、植物、细杆等复杂结构切碎。
- baseline mesh 还不能直接当最终仿真 mesh。
- scale、physics、collider 仍需真实标定和 QA。

## 5. 新实验默认

以后新实验不再默认用 minimal gsplat；默认使用：

```bash
bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

其中：

- `GS_BACKEND=graphdeco`
- `MASK_BACKEND=sam2`
- 使用 full `scene/reconstruction/point_cloud.ply`
- 超过 1.5 小时无 MASt3R 输出时裁剪前 60 秒为新 dataset
