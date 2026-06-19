# Video2Mesh 展示清单：milscene2

更新时间：2026-06-20

## 1. 定位

`milscene2` 是早期真实视频 baseline，用于验证：

- MASt3R-SLAM 导入。
- 3DGS viewer PLY 导出。
- 2D mask 到 3D semantic mask。
- object frame selection。
- baseline mesh 和 simulator bundle。

它保留为历史对照；新实验默认使用 GraphDECO 3DGS 和 SAM2。

## 2. 推荐查看路径

```text
exports/milscene2_hq_20260618_065920
```

关键文件：

| 展示目标 | 文件 |
|---|---|
| Review HTML | `simulator_assets/review/index.html` |
| 普通 3DGS 点云 | `simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` |
| SuperSplat 3DGS | `simulator_assets/viewer_plys/scene_3dgs_supersplat.ply` |
| 语义 SuperSplat | `simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply` |
| semantic splats | `simulator_assets/semantic_splats.ply` |
| 3D masks | `simulator_assets/object_masks_3d/*.ply` |
| simulator bundle | `simulator_assets/simulator_asset_bundle.json` |
| MuJoCo | `simulator_assets/adapters/mujoco/scene.xml` |
| QA | `simulator_assets/evaluation_report.json` |

## 3. 和当前默认流程的差异

| 项 | milscene2 历史 run | 当前默认 |
|---|---|---|
| 3DGS | minimal gsplat baseline | GraphDECO |
| masks | SAM/SAM bbox tracking 为主 | SAM prompts + SAM2 video tracking |
| 点云 | 已逐步改为 full cloud | full `point_cloud.ply` 默认 |
| mesh | object mask cloud baseline | baseline，后续接 Hunyuan/Meshy/多视角 |
| 目标 | 工程闭环验证 | 高质量真实实验 |

## 4. 结论

`milscene2` 可用于展示“系统已经闭环”，但不应作为当前最高质量默认结果。当前新实验应优先看 GraphDECO quick pipeline 输出。
