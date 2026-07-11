---
title: PhysX-Anything
id: video2mesh-object-simulation-physx-anything
category: 调研目录
visibility: public
summary: PhysX-Anything 是从单张图像生成仿真就绪物体资产的 VLM + decoder 管线，输出 part mesh、URDF/XML、关节和物理属性；对 Video2Mesh 更适合做单物体补全/物理 sidecar，而不是整房间重建替代。
tags:
  - 物体仿真
  - Research Catalog
  - PhysX-Anything
  - URDF
  - MuJoCo
---

# PhysX-Anything

检查日期：2026-07-11

当前执行状态：论文 PDF、项目页、GitHub README 和 mil8 部署探针已完成；官方源码已克隆到 mil8，VLM/decoder/TRELLIS 权重已放在 `/root/autodl-tmp` 并软链到 repo 的 `pretrain/`。官方原版四步 `1_vlm_demo.py -> 2_decoder.py -> 3_split.py -> 4_simready_gen.py` 仍未完整跑通：官方 `1_vlm_demo.py` 硬编码 `attn_implementation="flash_attention_2"`，而当前环境没有 `flash_attn`；debug wrapper 通过 PyTorch pytree shim 和 Qwen `sdpa` monkeypatch 已在 bedroom_4 bedside crop 上跑出 VLM 结构化物理描述和 part voxel。decoder 侧还没有产出可验证的 `sample.glb`、part mesh、URDF 或 XML；最新可核验证据是低纹理 debug run 停在 `TrellisImageTo3DPipeline.from_pretrained("./pretrain/decoder_abs_debug")`，分段加载 probe 也停在 `import torch`，mil8 负载升高且 `/data` 仍接近满盘。因此本页只把 VLM debug 结果记为通过，不把 bedroom_4 写成官方端到端跑通。

![PhysX-Anything teaser](../assets/physx-anything/physx-anything-teaser.jpg "PhysX-Anything 官方 teaser：单张真实图像输入，输出带物体几何、关节和物理属性的仿真资产")

## 链接

| 项 | 地址 |
|---|---|
| Project page | https://physx-anything.github.io/ |
| Paper | https://arxiv.org/abs/2511.13648 |
| Code | https://github.com/ziangcao0312/PhysX-Anything |
| Model | https://huggingface.co/Caoza/PhysX-Anything |
| Dataset | https://huggingface.co/datasets/Caoza/PhysX-Mobility |
| Related dataset / prior | https://huggingface.co/datasets/Caoza/PhysX-3D |
| Status on project page | CVPR 2026 accepted; inference and fine-tuning code released |

论文题目是 **PhysX-Anything: Simulation-Ready Physical 3D Assets from Single Image**。作者为 Ziang Cao、Fangzhou Hong、Zhaoxi Chen、Liang Pan、Ziwei Liu；机构为 NTU S-Lab 和 Shanghai AI Laboratory。arXiv PDF 标记为 `arXiv:2511.13648v1`，日期是 2025-11-17。

## 摘要要点

PhysX-Anything 要解决的问题不是“让 3D 看起来像”，而是从单张真实图像生成可以放进物理引擎的单物体资产。它同时预测几何、部件、关节、尺度、材质/密度/弹性等物理属性，并导出 URDF/XML 和 part-level mesh。

论文的核心贡献有四个：

| 贡献 | 论文含义 | 对 Video2Mesh 的意义 |
|---|---|---|
| VLM-based physical 3D generation | 用 Qwen2.5-VL 风格的 VLM 直接生成结构化物理描述和 part-level coarse geometry | 可以作为 object-level physics sidecar/URDF 生成器，而不是整场景 COLMAP/3DGS 替代 |
| 193x token compression | 先用 32^3 voxel grid 表示 coarse geometry，再只序列化 occupied voxel index，并把连续 index 合并成区间 | 说明它能把几何放进 VLM token budget，但输出尺度和局部几何仍需 decoder 修复 |
| Controllable flow transformer + structured latent decoder | 用 coarse voxel 条件控制 decoder，生成 mesh、radiance fields、3D Gaussians，再拆成 part-level meshes | 和 Video2Mesh 的 visual 3DGS/mesh 层不同，它偏单物体资产生成 |
| PhysX-Mobility | 基于 PartNet-Mobility 扩展到 47 类、2K+ 常见物体，并补充物理属性 | 对卧室内常见可动家具/器物有参考，但不是房间级语义重建数据集 |

## Pipeline

![PhysX-Anything framework](../assets/physx-anything/physx-anything-framework.jpg "官方 framework：单图输入，经 VLM 多轮对话生成 overall information 与每个 part 的 geometry information，再由 decoder 输出 mesh/3DGS/RF/URDF/XML")

论文的流程可以按“全局结构 -> 局部部件 -> 几何解码 -> 仿真格式”理解：

```text
single real-world object image
  -> VLM multi-round dialogue
  -> overall physical information
       name/category
       absolute scale
       material / density / Young's modulus / Poisson ratio
       part descriptions
       group hierarchy and joint type
  -> per-part coarse geometry
       32^3 voxel indices
       occupied voxel serialization
       adjacent-index range compression
  -> controllable flow transformer
  -> structured latent diffusion decoder
  -> mesh / radiance field / 3D Gaussian
  -> nearest-neighbor part split
  -> physical-format decoder
  -> part-level meshes + URDF + XML
```

这里最关键的边界是：输入是一张物体图，而不是多视角房间视频；输出是物体级 sim-ready asset，而不是整场景 navigation mesh 或房间级 3DGS。

## 物理表示

![PhysX-Anything decoder](../assets/physx-anything/physx-anything-decoder.jpg "官方 decoder：coarse physical representation 控制 flow transformer 和 sparse decoder，最终合成 mesh、3DGS、radiance field、part mesh、URDF 与 XML")

论文把原始 mesh token 过长的问题拆成两层：

| 层 | 做法 | 目的 |
|---|---|---|
| coarse voxel | 把物体部件映射到 32^3 voxel grid | 保留显式空间结构，同时降低 VLM 输出难度 |
| index serialization | 将 occupied voxel 线性化为 0 到 32767 的 index | 避免输出三元坐标序列 |
| range compression | 将连续 index 写成 `start-end` | 把 token 量压到原始 mesh 级表示的约 1/193 |
| physical JSON-like representation | 保存 part、group、joint、scale、material 和描述 | 比直接 URDF 更适合 VLM 生成和推理 |
| voxel-space kinematics | 将 motion direction、axis location、range 等转成 voxel 坐标 | 保持关节参数和几何一致 |

这套表示的启发价值很明确：Video2Mesh 当前的 `simulator_asset_bundle.json`、`object_asset.json` 和 semantic sidecar 可以学习它的“物体结构 + 几何 + 物理属性 + 关节”的统一 schema；但 Video2Mesh 的场景坐标、COLMAP 尺度、mesh collider 和 3DGS visual layer 仍应保留为主链路资产。

## 代码与推理链路

官方 README 给出的推理入口是四步：

```bash
python 1_vlm_demo.py \
  --demo_path ./demo \
  --save_part_ply True \
  --remove_bg False \
  --ckpt ./pretrain/vlm

python 2_decoder.py
python 3_split.py

python 4_simready_gen.py \
  --voxel_define 32 \
  --basepath ./test_demo \
  --process 0 \
  --fixed_base 0 \
  --deformable 0
```

实际代码边界：

| 脚本 | 输入 | 输出/作用 | 关键依赖 |
|---|---|---|---|
| `1_vlm_demo.py` | `demo/*.png` 或 `demo/*.jpg`，`pretrain/vlm` | `test_demo/<name>/basic_info.txt`、`coord_<part>.txt`、`ind_<part>.npy/ply` | `transformers` 的 `Qwen2_5_VLForConditionalGeneration`、`qwen_vl_utils`、`flash_attention_2`、`rembg`、`trimesh` |
| `2_decoder.py` | `test_demo/<name>/allind.npy` 和原图，`pretrain/decoder` | `sample.glb` | TRELLIS `TrellisImageTo3DPipeline`、CUDA PyTorch、decoder 权重 |
| `3_split.py` | `sample.glb`、part voxels | part-level mesh | `trimesh`、`scipy.spatial.cKDTree` |
| `4_simready_gen.py` | part mesh、basic physical description | `basic.urdf`、XML/MJCF、物理参数和连接关系 | `trimesh`、`scipy`、XML/URDF 生成逻辑 |
| `render_urdf.py` | `basic.urdf` | PyBullet 渲染视频 | `pybullet`、`imageio` |

README 还明确建议 `deformable=0`，因为论文/代码可以生成 deformable 参数，但 deformable parts 在 MuJoCo 中不稳定。对 Video2Mesh 来说，这意味着短期只能把它当 rigid/articulated object asset generator，不能把软体结果算成稳定仿真资产。

## 实验结果

论文在 PhysX-Mobility 和 in-the-wild 图像上评测几何、尺度、材质、affordance、kinematic parameters 和 description。

| 评测 | 论文结果摘要 | 备注 |
|---|---|---|
| PhysX-Mobility quantitative | PhysX-Anything 达到 PSNR 20.35、Chamfer Distance 14.43、F-score 77.50；absolute scale error 0.30，优于 PhysXGen 的 43.44 | 物理属性提升比几何指标更明显 |
| In-the-wild human study | Geometry 0.98；absolute scale 0.95；material 0.84；affordance 0.94；kinematic 0.98；description 0.96 | 14 名志愿者，共 1,568 个有效评分 |
| In-the-wild VLM eval | Geometry 0.94；kinematic parameters 0.94 | 论文用 GPT-5 做 VLM-based evaluation |
| Ablation | full representation 比 voxel/index 变体更好，PSNR 20.35、F-score 77.50 | 支撑 193x token compression 设计 |
| MuJoCo-style simulation | 展示 faucet、cabinet、eyeglass、lighter、laptop、handle 等 manipulation | 更像可执行性 demo，没有给出 Video2Mesh 可直接复用的整场景 benchmark |

![PhysX-Anything policy page](../assets/physx-anything/physx-anything-policy-page8.jpg "PDF 第 8 页：representation ablation、robot manipulation examples 和 Table 5")

## 和 Video2Mesh 的边界

PhysX-Anything 可以补 Video2Mesh 的“单物体物理资产”短板，但不能替代当前房间级扫描重建：

| Video2Mesh 阶段 | PhysX-Anything 是否适合 | 判断 |
|---|---|---|
| 视频抽帧、相机位姿、COLMAP/MVS | 不适合 | 它不估计房间相机轨迹，也不做多视角 SfM/MVS |
| 3DGS visual layer | 局部可参考 | 它的 decoder 能产 3DGS/RF，但目标是单物体；Video2Mesh 仍应用 GraphDECO/Spark/SuperSplat 维护场景 visual layer |
| mesh/collider | 适合单物体补全 | 可对语义分割出的 chair/cabinet/laptop 等 object crop 生成 part mesh/URDF，再和场景 collider 对齐 |
| physics sidecar | 很适合 | material、density、Young's modulus、Poisson ratio、joint type、scale、affordance 可映射进 `object_asset.json` |
| dynamic readiness | 部分适合 | 对 articulated object 有帮助，但仍要做 support、penetration、scale、joint limit、sim smoke test |
| whole-room simulator bundle | 不能直接替代 | 房间级 bundle 仍由 Video2Mesh 汇总 visual mesh、semantic mesh、object assets、adapters |

推荐吸收方式：

```text
Video2Mesh semantic objects
  -> choose articulated / movable object candidates
  -> crop object image from registered frames
  -> PhysX-Anything single-object generation
  -> part mesh + URDF/XML + physical metadata
  -> align into Video2Mesh scene coordinates
  -> run simulator preflight QA
  -> write object_asset.json / simulator_asset_bundle.json
```

不要这样用：

```text
bedroom_4 full room frame
  -> PhysX-Anything
  -> claim room-level sim-ready scene
```

这会把单物体生成器误用为整场景重建器。整房间帧可以作为 smoke test 输入，不能作为有效实验结论。

## mil8 部署审计

本轮在 mil8 做了真实部署与 bedroom_4 探针：

| 项 | 结果 |
|---|---|
| Host | `mil8` |
| GPU | 8 x NVIDIA GeForce RTX 3090, each 24 GB；最近探针时 decoder 指定 `CUDA_VISIBLE_DEVICES=0` |
| Disk | `/data` 3.5 TB，已用约 3.3 TB，仅约 25-27 GB 可用，Use% 100%；`/` 440 GB，约 57 GB 可用 |
| Official repo | `/data/zyx/workspace/PhysX-Anything` |
| Repo commit | `e221826` |
| Repo size | 55 MB |
| Shared Python | `/opt/envs/max/bin/python`, Python 3.10.0 |
| PyTorch | 2.2.2+cu121，CUDA 12.1，`torch.cuda.is_available=True`，8 GPUs visible |
| Existing required packages | `torch`, `torchvision`, `transformers`, `huggingface_hub`, `PIL`, `numpy`, `scipy`, `cv2` 等 |
| Initially missing packages | `qwen_vl_utils`, `trimesh`, `rembg`, `flash_attn`, `kaolin`, `nvdiffrast`, `spconv`, `mujoco`, `pybullet` |
| Isolated venv | `/root/autodl-tmp/physx-anything-venv`, created with `--system-site-packages` to reuse CUDA PyTorch |
| Packages added in isolated venv | `transformers==4.50.0`, `qwen-vl-utils==0.0.14`, `trimesh`, `rembg`, `accelerate`, `huggingface-hub`, `xformers`, `spconv-cu120` 等 |
| CUDA extensions | `nvdiffrast` 已从 `/root/autodl-tmp/nvdiffrast-src` 编译安装；`EasternJournalist/utils3d` 已按 TRELLIS 需要安装；`numpy==1.26.4`、`scipy==1.11.4` 已回退到可用版本 |
| Debug-only compatibility | PyTorch 2.2.2 需要 pytree shim 才能导入 Qwen2.5-VL；缺少官方 `kaolin`，当前只有极小 debug stub 满足 `kaolin.utils.testing.check_tensor` |
| Weight size check | Hugging Face API reports `Caoza/PhysX-Anything` `usedStorage=39938791487` and `microsoft/TRELLIS-image-large` `usedStorage=3300497168`, so weights alone are about 43.24 GB before pip wheels, build cache, intermediate GLB/mesh outputs, and HF snapshot metadata |
| Weight placement | `pretrain/vlm -> /root/autodl-tmp/physx-anything-pretrain/vlm`；`pretrain/decoder -> /root/autodl-tmp/physx-anything-pretrain/decoder`；`pretrain/trellis -> /root/autodl-tmp/physx-anything-trellis`；`pretrain/decoder_abs_debug -> /root/autodl-tmp/physx-anything-decoder-abs-debug` |
| VLM weights | four `model-00001..00004-of-00004.safetensors` present under `/root/autodl-tmp/physx-anything-pretrain/vlm` |
| Decoder weights | `/root/autodl-tmp/physx-anything-pretrain/decoder/ckpt_new/denoiser_step0350000.pt`, size 3.47 GB |
| TRELLIS weights | `ckpts/*.safetensors` present under `/root/autodl-tmp/physx-anything-trellis`; DINOv2 cached at `/root/.cache/torch/hub/checkpoints/dinov2_vitl14_reg4_pretrain.pth` |
| SSH note | `mil8` 曾短暂卡在 FRP/SSH banner exchange，后续恢复；当前 blocker 不是登录，而是 Python/CUDA/TRELLIS 加载稳定性与 `/data` 满盘压力 |
| Official VLM blocker | `1_vlm_demo.py` line 146 hardcodes `attn_implementation="flash_attention_2"`；当前没有 `flash_attn`，所以官方原版 VLM 尚未通过 |
| Debug VLM result | 通过 pytree shim + Qwen `sdpa` monkeypatch，`bedroom_4_bedside_lamp_table_crop` 已生成 `basic_info.txt`、`coord_*.txt`、`ind_*.npy/.ply` 和 `allind.npy` |
| PyTorch 2.4 attempt | A clean Python 3.10 venv at `/root/autodl-tmp/physx-anything-torch24-venv` was repaired, but downloading `torch==2.4.0+cu121` from `download.pytorch.org` was too slow and did not complete; the environment still has no `torch`, so the practical route remains the existing venv plus Qwen shim. |
| Decoder config fix | 官方 decoder `pipeline.json` 的相对路径会触发 HFValidationError；debug copy `/root/autodl-tmp/physx-anything-decoder-abs-debug/pipeline.json` 已把子模型改成绝对路径 |
| Decoder latest blocker | `decoder_lowtex_debug_run.log` 停在 `loading pipeline ./pretrain/decoder_abs_debug`；同一时段分段加载 probe `probe_pipeline_load.log` 停在 `import torch`，机器 load average 升至约 60；没有生成 `sample_lowtex.glb`、geometry OBJ 或官方 `sample.glb` |

实测失败日志的关键点：

```text
ImportError: cannot import name 'Qwen2_5_VLForConditionalGeneration' from 'transformers'
RuntimeError: register_pytree_node() got an unexpected keyword argument 'flatten_with_keys_fn'
1_vlm_demo.py: attn_implementation="flash_attention_2" but flash_attn is not installed
2_decoder.py / debug wrapper: loading pipeline ./pretrain/decoder_abs_debug
probe_pipeline_load.py: [load-probe] import torch
```

我没有把这个状态写成“官方跑通”。当前完成的是源码部署、环境审计、权重就位、bedroom_4 单物体 crop 准备、debug VLM 输出验证；尚未完成 decoder GLB、part split、URDF/XML 和仿真 smoke test。

## bedroom_4 smoke input

为了验证和 Video2Mesh 数据的连接，本轮从已有 `bedroom_4` 数据集中抽取了一张真实帧作为单图 smoke input：

![bedroom_4 smoke input](../assets/physx-anything/bedroom4-physx-smoke-input.jpg "bedroom_4 真实帧 003069.png：当前仅作为 PhysX-Anything 单图 smoke input，不代表单物体 crop")

| 项 | 路径/结果 |
|---|---|
| Source dataset | `/data/zyx/workspace/Video2MeshWorkspace/Video2Mesh/dataset/bedroom_4_CmEIg9gMI74` |
| Image folder | `/data/zyx/workspace/Video2MeshWorkspace/Video2Mesh/dataset/bedroom_4_CmEIg9gMI74/bedroom_4_images` |
| Image count / size | 35 PNG images, about 113 MB |
| Selected frame | `003069.png` |
| Prepared input | `/data/zyx/workspace/physx_anything_bedroom4_20260711/input/demo/bedroom_4_center_frame.png` |
| Manifest | `/data/zyx/workspace/physx_anything_bedroom4_20260711/input/physx_anything_bedroom4_input_manifest.json` |
| Local doc copy | `docs/video2mesh/research-catalog/assets/physx-anything/bedroom4-physx-smoke-input.jpg` |

这个输入是 full-room frame，所以只能用于环境 smoke test。要做有效 PhysX-Anything 实验，下一步应该从 Video2Mesh 语义结果里挑一个清楚的单物体 crop，例如 cabinet、chair、laptop 或 door-like articulated object；最好带 mask/alpha 或干净背景，再设置 `--remove_bg True`。

为了继续靠近单物体假设，本轮又从同一帧裁了一个右侧床头柜/台灯区域：

![bedroom_4 bedside heuristic crop](../assets/physx-anything/bedroom4-physx-bedside-crop.png "bedroom_4 右床头柜/台灯 heuristic crop：比整房间帧更接近单物体输入，但仍包含床边、窗户、植物和桌面，不是 mask-clean 官方质量 crop")

| 项 | 路径/结果 |
|---|---|
| Remote crop | `/data/zyx/workspace/physx_anything_bedroom4_20260711/object_crop_demo/demo/bedroom_4_bedside_lamp_table_crop.png` |
| Remote manifest | `/data/zyx/workspace/physx_anything_bedroom4_20260711/object_crop_demo/crop_manifest.json` |
| Crop box | `(614, 216, 947, 525)` in the original 1280 x 720 frame |
| Local doc copy | `docs/video2mesh/research-catalog/assets/physx-anything/bedroom4-physx-bedside-crop.png` |
| Caveat | Heuristic crop only; it should not be reported as an official object-level experiment result until a mask-clean crop or semantic object crop is used. |

## bedroom_4 实测结果

这次实测只把 VLM debug wrapper 记为通过。该 wrapper 没有改官方 repo 源码，但绕开了两个环境问题：PyTorch 2.2.2 的 Qwen pytree 兼容问题，以及官方 `flash_attention_2` 依赖缺失问题。因此它是 debug path，不是官方原版 `1_vlm_demo.py`。

| 阶段 | 状态 | 证据 |
|---|---|---|
| `1_vlm_demo.py` official | Blocked | 官方代码第 146 行硬编码 `attn_implementation="flash_attention_2"`；当前 venv 没有 `flash_attn` |
| VLM debug wrapper | Passed | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/` 已生成 `basic_info.txt`、`coord_0..2.txt`、`ind_0..2.npy/.ply`、`allind.npy` |
| `2_decoder.py` official | Not passed | 默认 decoder 会导出 `sample.glb`，但当前目录没有 `sample.glb` |
| Decoder low-texture debug | Blocked | `/root/autodl-tmp/physx-anything-outputs/decoder_lowtex_debug_run.log` 停在 `loading pipeline ./pretrain/decoder_abs_debug`；未生成 `sample_lowtex.glb` 或 `sample_lowtex_geometry.obj` |
| `3_split.py` | Not run | 需要 `sample.glb`，目前没有可验证 GLB |
| `4_simready_gen.py` | Not run | 需要 part mesh `objs/`，目前没有可验证 part mesh |

VLM 对 bedside crop 的结构化理解如下：

| 项 | 值 |
|---|---|
| Name | Decorative Table with Vase |
| Category | Furniture |
| Dimension | `90*90*75` |
| Part 0 | `board`, Wood, density `0.65 g/cm^3`, Young's modulus `10.0`, Poisson ratio `0.3` |
| Part 1 | `table_base`, Wood, density `0.65 g/cm^3`, Young's modulus `10.0`, Poisson ratio `0.3` |
| Part 2 | `vase`, Ceramic, density `2.4 g/cm^3`, Young's modulus `300.0`, Poisson ratio `0.24` |
| Group 0 | `['l_0', 'l_1']`, equivalent/fixed group |
| Group 1 | `['l_2']`, attached relative to `group_0` |

对应 voxel 输出：

| 文件 | shape | dtype | min xyz | max xyz |
|---|---:|---|---|---|
| `allind.npy` | `(2693, 3)` | `int64` | `[0, 0, 1]` | `[31, 31, 26]` |
| `ind_0.npy` / board | `(2166, 3)` | `int64` | `[0, 0, 24]` | `[31, 31, 26]` |
| `ind_1.npy` / table_base | `(435, 3)` | `int64` | `[2, 17, 1]` | `[30, 31, 1]` |
| `ind_2.npy` / vase | `(92, 3)` | `int64` | `[14, 14, 15]` | `[19, 20, 18]` |

这个结果说明 VLM 已能把 bedroom_4 crop 转成可被 decoder 使用的 coarse physical representation；但它把复杂 crop 理解成“桌子+花瓶”，没有恢复台灯/床头柜的真实语义，也没有经过 decoder、split 和 simulator QA。因此它只能算 **bedroom_4 crop 的 VLM smoke pass**，不能算 sim-ready asset pass。

## 接入判断

短期建议是 **P1 research adapter，不进入主链路默认路径**：

| 层级 | 判断 | 原因 |
|---|---|---|
| P0 room reconstruction | 不进入 | 不是多视角房间重建器 |
| P1 object asset enrichment | 可以小规模试 | 能输出 part mesh、URDF/XML、物理属性，正好补 Video2Mesh object sidecar |
| P1 simulator QA | 需要真实跑通后再接 | 当前未有本地/mil8 输出 URDF；不能提前承诺 |
| P2 articulated object library | 值得跟踪 | 对柜门、抽屉、笔记本、箱子、龙头等 articulated objects 很有价值 |
| P2 deformable object | 暂不做 | 官方 README 也建议 deformable flag 设为 0 以获得更可靠的 simulation |

下一步更稳的执行路线：

1. 先稳定 Python/CUDA 初始化：清掉本轮 probe 残留进程后，单独跑 `/root/autodl-tmp/probe_physx_pipeline_load.py`，逐个加载 `sparse_structure_decoder`、`sparse_structure_flow_model`、`slat_decoder_mesh/gs/rf` 和 DINOv2，定位卡在 torch import、denoiser `.pt`、DINO cache 还是某个 TRELLIS safetensors。
2. 如果目标是“官方原版”，优先安装或编译 `flash-attn`，再重跑 `1_vlm_demo.py`；如果继续用 `sdpa` wrapper，需要在报告和产物名里保留 `debug` 标记。
3. decoder 重试时继续把大输出放在 `/root/autodl-tmp/physx-anything-outputs/`，只在 `sample_lowtex.glb` 小于 `/data` 可承受范围时复制到 `test_demo/<name>/sample.glb` 以运行 `3_split.py`。
4. 如果 GLB export 再次失败，先保底导出 mesh-only OBJ/PLY，并把它标为 decoder geometry debug artifact；不要跳过 GLB/part split 直接生成 URDF。
5. 只在真实生成并验证 `basic_info.txt`、`sample.glb`、`objs/<part>/<part>.obj`、`basic.urdf` 和 `basic.xml` 后，才把它写成“bedroom_4 物体跑通”。

## 风险

- **磁盘风险**：`/data` 只剩约 25-27 GB 且 Use% 100%；权重已尽量放到 `/root/autodl-tmp`，但 decoder 中间 GLB/mesh/texture 仍可能因为 `/data` 满盘失败。
- **依赖风险**：官方 README 以 PyTorch 2.4.0 + CUDA 11.8 为默认，而 mil8 共享环境是 PyTorch 2.2.2 + CUDA 12.1；`xformers` 可用但 `flash_attn` 缺失，官方 VLM 原版仍不通过。
- **运行时风险**：本轮 `TrellisImageTo3DPipeline.from_pretrained` 长时间卡在 pipeline load；分段 probe 也停在 `import torch`，说明当前远端 Python/CUDA 初始化状态不稳定。
- **debug 标记风险**：pytree shim、Qwen `sdpa` monkeypatch、absolute-path decoder config 和 minimal `kaolin` stub 都是 debug workaround，不能写成官方复现。
- **输入风险**：PhysX-Anything 训练/推理假设单物体图像；`bedroom_4` full-room frame 会造成类别、尺度、部件和关节推理混乱。
- **坐标风险**：即使生成 URDF/XML，也还需要把单物体坐标、尺度和姿态对齐回 Video2Mesh 的 COLMAP/scene coordinate。
- **质量风险**：论文指标来自 PhysX-Mobility 和互联网单物体图像；不能直接外推到遮挡严重、背景复杂的室内扫描帧。
- **仿真风险**：自动物理属性必须经过 mass/friction/joint limit/penetration/support 的 simulator preflight，不可直接写进最终资产合同。
