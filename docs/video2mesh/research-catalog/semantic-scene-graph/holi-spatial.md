---
title: Holi-Spatial 调研与 bedroom_4 实验报告
id: video2mesh-semantic-scene-graph-holi-spatial
category: 调研目录
visibility: public
summary: 调研 Holi-Spatial 的自动 3D 空间数据生成 pipeline、公开模型与数据集，并记录 Video2Mesh bedroom_4 的 Holi-Spatial 兼容 smoke run。
tags:
  - 语义与 Scene Graph
  - Holi-Spatial
  - Spatial QA
  - 3D Grounding
  - Research Catalog
---

# Holi-Spatial 调研与 bedroom_4 实验报告

这份报告记录 Holi-Spatial 论文、官方仓库、公开模型/数据集状态，以及 Video2Mesh `bedroom_4` 片段接入 Holi-Spatial 后处理和 spatial QA 的实际实验结果。这里的实验是 **Holi-Spatial-compatible smoke run**，不是完整官方 DA3/SAM3/PGSR 重跑。

![Holi-Spatial 官方 teaser](../assets/holi-spatial-teaser.jpg "官方 Holi-Spatial teaser：从视频流构建几何、语义、3D grounding 和 spatial QA 数据")

## 链接

- Paper: https://arxiv.org/abs/2603.07660
- Project page: https://visionary-laboratory.github.io/holi-spatial/
- Code: https://github.com/Visionary-Laboratory/Holi-Spatial
- Hugging Face org: https://huggingface.co/Holi-Spatial
- Local PDF: `/Users/zhangyuxiang/Desktop/worksplace/Holi-Spatial/2603.07660v1.pdf`
- Local official clone inspected: `/tmp/Holi-Spatial-official`

## 基本信息

| 项目 | 内容 |
|---|---|
| 论文标题 | Holi-Spatial: Evolving Video Streams into Holistic 3D Spatial Intelligence |
| arXiv | 2603.07660v1, submitted on 2026-03-08 |
| README 标注 | ICML 2026 Oral |
| 作者 | Yuanyuan Gao, Hao Li, Yifei Liu, Xinhao Ji, Yuning Gong, Yuanjun Liao, Fangfu Liu, Manyuan Zhang, Yuchen Yang, Dan Xu, Xue Yang, Huaxi Huang, Hongjie Zhang, Ziwei Liu, Xiao Sun, Dingwen Zhang, Zhihang Zhong |
| 目标 | 从 raw video 自动生成 3DGS、深度、2D mask、3D bbox、instance caption、3D grounding 和 spatial QA |
| 对 Video2Mesh 的定位 | 不是替代 COLMAP/3DGS/mesh 主链路，而是可以作为语义空间标注、空间 QA benchmark、VLM 训练数据生成层 |

## 核心结论

Holi-Spatial 最值得借鉴的是它把视频场景整理成 **可训练、可评测的空间监督数据**：每个场景不只是有重建结果，还带有 2D masks、3D bounding boxes、instance captions、3D grounding pairs 和 spatial QA。对 Video2Mesh 来说，它适合作为 P1/P2 的语义空间数据层，用来检验“我们的重建、mask、bbox、camera pose 是否足够支撑空间推理”。

它不应该被理解成一个轻量部署模型。完整 pipeline 依赖 DA3、PGSR/3DGS、SAM3、VLM/vLLM 服务、CUDA 扩展和大量数据存储。当前本地 Mac 不适合跑完整链路；`mil8` 有 8 张 RTX 3090 24GB，算力够做单场景实验，但 `/data` 在 2026-07-10 核验时只剩约 85GB 可用、98% 使用率，不适合直接下载大模型和批量数据。

## 论文方法

Holi-Spatial 的自动数据生成分三段：

| 阶段 | 论文/官方代码中的作用 | 关键产物 |
|---|---|---|
| Geometric Optimization | 用 Depth-Anything-V3 等 monocular prior 初始化，再优化 3D Gaussian Splatting/PGSR 场景，提高多视角几何和深度一致性 | optimized 3DGS, rendered depth, point cloud, mesh |
| Image-level Perception | 抽关键帧，用 VLM 发现开放词汇类别，再用 SAM3 生成每帧 instance masks | per-image class list, SAM3 masks, mask index |
| Scene-level Lift and Refinement | 用深度、相机内参和位姿把 2D mask 回投到 3D；跨视角合并、过滤、生成 3D bbox/caption/grounding/QA | 3D bbox, instance caption, 3D grounding, spatial QA |

官方 README 对应的代码入口也基本按这个边界组织：

| 官方入口 | 作用 |
|---|---|
| `run_da3.sh`, `inference_da3_scannetppv2.py` | DA3 depth / point cloud preprocessing |
| `3dgs_train.sh`, `PGSR/` | PGSR/3DGS 训练，输出 `point_cloud/iteration_30000/point_cloud.ply` |
| `mesh.sh` | 渲染 mesh 和 mesh-guided masks |
| `classic_vllm.py`, `classic_region.py` | VLM object / functional-region discovery |
| `sam3.py` | SAM3 text-prompted mask generation |
| `3d_bounding_instance_gs_rerun_da3.py` | object 2D-to-3D lifting/refinement |
| `postprocess_3d_bbox_aabb.py` | 基于 floor 的 AABB/OBB 对齐后处理 |
| `qa_generation/` | instance description、two-view spatial QA、LLaMA-Factory 格式转换 |

## 数据规模和论文结果

论文摘要给出的 Holi-Spatial-4M 规模是：

| 数据项 | 规模 |
|---|---:|
| optimized 3DGS scenes | 12K |
| 2D instance masks | 1.3M |
| 3D bounding boxes | 320K |
| instance captions | 320K |
| 3D grounding instances | 1.2M |
| spatial QA pairs | 1.2M |

论文正文另有一处写法是 12K scenes、1.2M 2D masks、1.3M spatial QA pairs；项目页顶部截至 2026-07-10 显示 13K+ scenes、1.3M+ QA pairs、300K+ 3D bboxes。报告里应以“论文版本与项目页口径略有差异”处理，不把这些数字混成一个唯一精确值。

论文报告的自动标注质量对比中，Holi-Spatial 是同时覆盖 depth、2D segmentation 和 3D detection 的方法。PDF 表格中可读到的主要结果：

| 数据集 | Depth F1 | 2D Seg IoU | 3D Det AP25 | 3D Det AP50 |
|---|---:|---:|---:|---:|
| ScanNet | 0.98 | 0.66 | 76.60 | 67.00 |
| ScanNet++ | 0.89 | 0.64 | 81.06 | 70.05 |
| DL3DV | 0.78 | 0.71 | 62.89 | 52.67 |

VLM fine-tuning 方面，论文用 Holi-Spatial-4M 的 QA/grounding 数据训练 Qwen3-VL 系列，并报告空间推理和 3D grounding 均有提升。PDF 中可读到：

| 任务 | Baseline | + Holi-Spatial data |
|---|---:|---:|
| Qwen3-VL-2B spatial QA 两列指标 | 26.1 / 33.5 | 27.6 / 44.0 |
| Qwen3-VL-8B spatial QA 两列指标 | 31.1 / 29.4 | 32.6 / 49.1 |
| Qwen3-VL-8B 3D grounding AP15/AP25/AP50 | 19.82 / 16.80 / 13.50 | 35.52 / 31.94 / 27.98 |

这里要注意：这些是论文原始 protocol 下的结果，不等于我们本地 `bedroom_4` smoke run 的指标。

## 公开模型与数据集状态

截至 2026-07-10 用 Hugging Face API 核验，`Holi-Spatial` 组织下有 1 个公开模型和 4 个公开数据集条目：

| 类型 | 名称 | 状态 |
|---|---|---|
| model | `Holi-Spatial/HoliSpatial-2M-QA-Qwen3-VL-8B` | public, safetensors, 4 个 model shard, lastModified 2026-03-29 |
| dataset | `Holi-Spatial/HoliSpatial-QA-2M` | public, webdataset/jsonl, lastModified 2026-03-22 |
| dataset | `Holi-Spatial/HoliSpatial-3D-Grounding` | public, tar shards, lastModified 2026-04-21 |
| dataset | `Holi-Spatial/ScanNetPP` | public |
| dataset | `Holi-Spatial/ScanNet_v2` | public |

官方 GitHub README 在本地 clone 的最新核验版本 `d988b16` 中写明：已发布 subset dataset、HoliSpatial-QA-2M、全部 model checkpoints，并已发布 pipeline code。项目页页面上仍有部分 “Data coming soon / Benchmark coming soon” 入口文案，因此以 GitHub README 和 Hugging Face API 核验为准。

## 硬件和环境需求

完整 pipeline 不是纯 Python 后处理。官方依赖包括：

| 层 | 需求 |
|---|---|
| Python deps | numpy, scipy, pillow, opencv, scikit-image, trimesh, open3d, pycocotools, openai, huggingface_hub, lpips, rerun-sdk, einops, timm, hydra-core, omegaconf |
| CUDA/PyTorch | PGSR README 要求安装 CUDA 版 PyTorch；官方示例用 cu118 |
| CUDA extensions | `PGSR/submodules/diff-plane-rasterization`, `PGSR/submodules/simple-knn` |
| Depth | `depth_anything_3.api.DepthAnything3`, 官方脚本会加载 `depth-anything/DA3NESTED-GIANT-LARGE` |
| Segmentation | SAM3 checkpoint/assets，`sam3.py` 可从 `facebook/sam3` 拉默认 checkpoint 和 BPE asset |
| VLM | OpenAI-compatible vLLM endpoint，默认 `http://localhost:8000/v1` 或 `/v1/chat/completions` |
| 数据 | ScanNet v2、ScanNet++ 或 DL3DV 格式的图像、相机、covisibility、训练输出目录 |

本机 Mac 更适合读论文、整理数据、写脚本和查看小输出，不适合完整 DA3/SAM3/PGSR/VLM 重跑。`mil8` 当前硬件核验结果：

| 项 | 状态 |
|---|---|
| GPU | 8 x NVIDIA GeForce RTX 3090, 24GB VRAM |
| `/data` | 3.5T total, 3.2T used, 85G available, 98% used |
| 结论 | 单场景轻量后处理和已有资产 smoke run 可以；完整官方单场景重跑需要先清空间/准备模型；批量数据生成不适合在当前磁盘状态直接开始 |

## Video2Mesh 接入判断

Holi-Spatial 和 Video2Mesh 的关系应该是“语义空间标注与 QA 层”，不是“替换几何主链路”。

```text
Video2Mesh:
  video frames
  -> COLMAP / GraphDECO 3DGS / scene mesh / object masks
  -> simulator asset bundle

Holi-Spatial-style extension:
  existing frames + cameras + masks + 3D bbox
  -> floor-aligned bbox postprocess
  -> instance descriptions
  -> two-view spatial QA
  -> LLaMA-Factory / VLM evaluation data
```

可吸收部分：

- 用 Holi-Spatial 的 bbox schema 和 QA schema 作为 Video2Mesh 语义空间 sidecar 的候选格式。
- 用 two-view QA 检查相机位姿、bbox、object label 是否自洽。
- 用 `HoliSpatial-2M-QA-Qwen3-VL-8B` 作为空间 QA/推理模型候选，而不是几何重建模型。
- 后续如果要做正式 benchmark，可以把每个 Video2Mesh run 自动转成 Holi-Spatial-style QA，再喂给多个 VLM 做横向比较。

暂不吸收部分：

- 不把 Holi-Spatial 的 PGSR/DA3/SAM3 全量 pipeline 直接塞入 Video2Mesh 主线。
- 不把 QA 输出当作 simulator-ready physics 属性。
- 不用 proxy floor/covisibility 产物训练正式模型。

## 本次实验：bedroom_4 Holi-Spatial-compatible smoke run

### 实验目标

目标不是完整复现论文，而是回答两个工程问题：

1. Video2Mesh 的 `bedroom_4` 现有输出能否整理成 Holi-Spatial 期望的目录和 JSON schema。
2. 在不下载完整 DA3/SAM3/PGSR 权重、不重训场景的前提下，能否跑通官方 AABB 后处理和 object-only two-view QA。

### 输入来源

| 项 | 路径 |
|---|---|
| Video2Mesh 源结果 | `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/bedroom_4_full_pipeline_valid_1280_20260708_160328` |
| 本地 Holi-Spatial run package | `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/holi_spatial_runs/bedroom_4_smoke_20260709` |
| 远端执行路径 | `mil8:/data/zyx/workspace/holi_spatial_runs/bedroom_4_smoke_20260709` |
| 准备脚本 | `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tools/prepare_holi_spatial_bedroom4.py` |

准备脚本完成的转换：

| Holi-Spatial 期望项 | 本次来源 |
|---|---|
| `scannetppv2/data/bedroom_4/dslr/resized_undistorted_images` | Video2Mesh GraphDECO COLMAP source images |
| `transforms_undistorted.json` | Video2Mesh `scene/reconstruction/3dgs/cameras.json` 转换 |
| `Qwen3VL-32B-Scannetppv2/bedroom_4.json` | Video2Mesh object labels 适配 |
| `sam3_masks_scannetppv2_new/bedroom_4/mask_index.json` | Video2Mesh `masks/2d` 转换，包含 RLE |
| `pgsr_scannetppv2_all/.../point_cloud.ply` | 复用 Video2Mesh GraphDECO 3DGS PLY |
| `pgsr_scannetppv2_all/.../mesh/tsdf_fusion_post.ply` | 复用 Video2Mesh COLMAP Delaunay scene mesh |
| `output_scannetppv2_new/bedroom_4.json` | Video2Mesh `masks/3d/object_masks.json` 的 bbox_3d 转成 Holi-Spatial bbox schema |
| `scannetppv2_wai/.../covisibility.npy` | 用相机中心距离生成的 proxy covisibility |

### 实际执行命令

在 `mil8` 上使用 `/data/anaconda3/bin/python` 执行：

```bash
cd /data/zyx/workspace/holi_spatial_runs/bedroom_4_smoke_20260709

/data/anaconda3/bin/python postprocess_3d_bbox_aabb.py \
  --input_dir output_scannetppv2_new \
  --output_dir output_scannetppv2_new_aabb \
  --floor_label floor \
  --axis_method largest_face \
  --extent_mode keep

/data/anaconda3/bin/python qa_generation/generate_two_view_qa.py \
  --scene-id bedroom_4 \
  --data-root scannetppv2/data \
  --wai-root scannetppv2_wai \
  --bbox-json-folder output_scannetppv2_new_aabb \
  --output output_QA_new_lang \
  --num 2 \
  --covis-threshold 0.05 \
  --marker-types language_description
```

这两步是官方后处理和 QA 生成脚本。它们没有训练模型，也没有调用大 VLM 生成答案；QA 答案由相机位姿、共视矩阵、3D bbox 中心/边长和方向规则计算得到。

### 产物统计

| 产物 | 大小/数量 | 说明 |
|---|---:|---|
| run package | 192MB, 1025 files | 本地与远端均已同步 |
| images / frames | 50 / 50 | 来自 `bedroom_4` 片段 |
| categories | 13 | object labels + wall/floor/ceiling |
| `mask_index.json` | 4,792,104 bytes, 1000 items | 每个 object 最多取 50 帧 mask |
| reused 3DGS PLY | 149,987,219 bytes | 复用 Video2Mesh GraphDECO 输出 |
| reused scene mesh | 2,695,503 bytes | 复用 Video2Mesh scene mesh |
| proxy covisibility | 10,128 bytes | 50 x 50 matrix |
| raw bbox JSON | 166,091 bytes, 21 instances | 包含 proxy floor |
| AABB bbox JSON | 167,799 bytes, 21 instances | 官方 AABB 后处理输出 |
| QA JSON | 70,463 bytes, 24 records | object-only two-view QA |

21 个 bbox 实例包括 1 个 proxy floor 和 20 个 Video2Mesh object mask 实例：bed、cabinet、curtain、desk、door x2、lamp x4、nightstand x4、plant x4、table、window。

QA 类型分布：

| question_type | 数量 |
|---|---:|
| `cam_translation` | 8 |
| `cam_rotation` | 4 |
| `object_distance` | 4 |
| `object_height_or_length` | 4 |
| `object_cross_direction` | 4 |

### QA 示例

| 类型 | 图像对 | 问题摘要 | 答案 |
|---|---|---|---|
| camera translation | `000027.png` -> `000026.png` | 从 view A 到 view B 的主相机运动方向是什么 | A, up |
| camera rotation | `000040.png` -> `000019.png` | view B 相对 view A 的 dominant rotation direction | B, turn left |
| object distance | `000040.png` -> `000042.png` | table 与 desk 的 3D 中心距离 | 1.83 m |
| object size | `000040.png` -> `000042.png` | lamp 与 desk 哪个最长 | D, desk |
| object direction | `000040.png` -> `000042.png` | desk 相对 image B 的方向 | C, North |

### 已完成和未完成

| 状态 | 内容 |
|---|---|
| Passed | 官方 `postprocess_3d_bbox_aabb.py` 跑通，生成 21 个 AABB bbox |
| Passed | 官方 `qa_generation/generate_two_view_qa.py` 跑通，生成 24 条 QA |
| Passed | 本地与 `mil8` 产物数量一致，`run_manifest.json` 状态为 `smoke_run_completed_on_mil8` |
| Not tested | DA3 depth inference |
| Not tested | PGSR/3DGS official retraining |
| Not tested | SAM3 mask inference |
| Not tested | Qwen/VLM object discovery 和 instance description |
| Not tested | region QA、repeat-description filtering、LLaMA-Factory conversion |

### 重要限制

这次实验不能写成“完整复现 Holi-Spatial”。具体原因：

- `bedroom_4` 源包没有官方 DA3 `depth_da3/*.npy`，本次没有跑 DA3。
- 没有重跑 PGSR/3DGS；3DGS PLY 和 mesh 都复用 Video2Mesh 现有输出。
- 没有跑 SAM3；mask 来自 Video2Mesh 的 GroundingDINO/SAM2 路线，再转换成 Holi-Spatial `mask_index.json`。
- 没有启动 vLLM/Qwen 做 object discovery 或 instance caption；class JSON 来自已有 object labels 适配。
- floor 是从场景 extent 插入的 proxy floor，用于让 AABB 后处理有 up axis。
- covisibility 是用相机中心距离生成的 proxy matrix，不是官方 WAI/covisibility 产物。

因此这批 QA 适合做 **管线验证样本** 和 schema smoke test，不适合作为正式 benchmark 或训练数据。

## 下一步建议

| 优先级 | 动作 | 目的 |
|---|---|---|
| P0 | 保留当前 `tools/prepare_holi_spatial_bedroom4.py`，把它作为 Video2Mesh -> Holi-Spatial schema adapter | 后续每个 run 都能生成可对比 QA |
| P0 | 为 `output_QA_new_lang/bedroom_4.json` 写一个轻量 verifier，检查问题类型、答案字段、图像路径、bbox 引用 | 防止 QA 生成静默退化 |
| P1 | 在空间允许时，单独选 1 个小场景补跑 SAM3 或 DA3 中的一步，和当前 adapter 输出比较 | 判断全官方链路收益 |
| P1 | 接入一个 VLM evaluation script，把这 24 条 QA 喂给 Qwen/GPT/Gemini，记录模型答题准确率 | 把 QA 从产物变成评测 |
| P2 | 生成 instance descriptions 和 LLaMA-Factory JSONL，但必须等真实 caption/VLM 服务跑通 | 训练数据化 |

短期最务实的路线不是追完整 Holi-Spatial 批量数据生成，而是把它的 **spatial QA schema + bbox postprocess + LLaMA-Factory conversion** 拆出来，成为 Video2Mesh 的语义空间评测层。

## 2026-07-11 当前状态

本周 Holi-Spatial 仍处在部署与适配阶段。已经确认 Video2Mesh 的 `bedroom_4` 现有 frames、cameras、object masks 和 3D bbox 可以被整理成 Holi-Spatial 风格 run package，并跑通官方 AABB postprocess 与 object-only two-view QA；但 DA3 depth、PGSR official retraining、SAM3 mask inference、Qwen/VLM object discovery 和 instance caption 都还没有跑。

因此当前适合写成“schema smoke run / 空间 QA 适配成功”，不适合写成“完整复现 Holi-Spatial”。后续优先级是加 QA verifier 和 VLM evaluation，把这 24 条 QA 从静态产物变成可比较的空间推理评测样本。
