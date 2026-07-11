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

检查日期：2026-07-11；最新续跑：2026-07-12

当前执行状态：论文 PDF、项目页、GitHub README 和 mil8 部署探针已完成；官方源码已克隆到 mil8，VLM/decoder/TRELLIS 权重已放在 `/root/autodl-tmp` 并软链到 repo 的 `pretrain/`。官方原版四步仍未完整通过：官方 `1_vlm_demo.py` 硬编码 `attn_implementation="flash_attention_2"`，而当前环境没有 `flash_attn`；官方 `2_decoder.py` 期望导出 textured `sample.glb`，本轮 debug decoder 在 GLB texture/postprocess 后段卡住，未生成官方质量 `sample.glb`。bedroom_4 bedside crop 只留下了一条 **debug/proxy/smoke 证据链**：VLM debug wrapper 生成结构化物理描述和 part voxel；decoder debug 生成 geometry OBJ；该 OBJ 转成 geometry-only proxy GLB 后，官方 `3_split.py` 和 `4_simready_gen.py` 能继续产出 part OBJ、`basic.urdf` 和 `basic.xml`。这只能说明部分代码路径与文件格式转换链路可执行，不能证明 bedroom_4 物体跑通，也不能作为有效复现实验结果。

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

本轮在 mil8 做的是环境部署审计与 bedroom_4 debug/proxy 探针；下面记录的是排障证据，不是有效 bedroom_4 实验结论：

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
| Pipeline load re-probe | 2026-07-12 `TrellisImageTo3DPipeline.from_pretrained("./pretrain/decoder_abs_debug")` 用本地 DINOv2 cache 成功，`from_pretrained` 44.4 s，`.cuda()` 1.3 s |
| Decoder debug result | low-texture debug run 成功完成 `run_control(formats=["mesh", "gaussian"])`，mesh `343214` vertices / `686376` faces，并导出 `/root/autodl-tmp/physx-anything-outputs/bedroom_4_bedside_lamp_table_crop/sample_lowtex_geometry.obj`，size `27499041` bytes |
| Decoder GLB blocker | `postprocessing_utils.to_glb(..., texture_size=512)` 已完成 decimate、rasterizing、remove invisible faces，日志到 `After remove invisible faces: 148637 vertices, 297262 faces` 后长时间无输出；最终手动终止，没有生成 `sample_lowtex.glb` |
| Proxy GLB | 用 geometry OBJ 导出 geometry-only `/root/autodl-tmp/physx-anything-outputs/bedroom_4_bedside_lamp_table_crop/sample_geometry_proxy.glb`，size `12355984` bytes，并软链为 `test_demo/bedroom_4_bedside_lamp_table_crop/sample.glb` 供官方 split 脚本读取 |
| Split + simready proxy path | 官方 `3_split.py` 基于 proxy GLB 生成 `objs/0/0.obj`、`objs/1/1.obj`、`objs/2/2.obj`；官方 `4_simready_gen.py --voxel_define 32 --basepath ./test_demo --process 0 --fixed_base 0 --deformable 0` 生成 `basic_info.json`、`basic.urdf`、`basic.xml`。这只说明 proxy 输入能穿过这两个脚本，不说明 decoder 官方输出或仿真质量通过 |

实测失败日志的关键点：

```text
ImportError: cannot import name 'Qwen2_5_VLForConditionalGeneration' from 'transformers'
RuntimeError: register_pytree_node() got an unexpected keyword argument 'flatten_with_keys_fn'
1_vlm_demo.py: attn_implementation="flash_attention_2" but flash_attn is not installed
2_decoder.py official textured sample.glb: not verified
low-texture debug: to_glb reached "After remove invisible faces" but did not export GLB
geometry-only proxy GLB: used only to validate split and simready stages
```

结论边界：当前完成的是源码部署、环境审计、权重就位、bedroom_4 heuristic crop 准备、debug VLM 输出、debug geometry decoder、proxy split、proxy URDF/XML。尚未完成官方 `flash_attention_2` VLM、official `2_decoder.py` textured `sample.glb`、以及真实 simulator smoke test；因此不能写成“官方 textured decoder 跑通”、不能写成“bedroom_4 跑通”，也不能把 proxy URDF/XML 当作项目有效实验结果。

本地已回传的调试产物放在 `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/physx_anything_bedroom4_proxy_20260712`。该目录仅用于复查日志、文件头、OBJ 规模和 XML 引用，不进入 Git，也不作为正式复现实验资产。

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

## bedroom_4 debug/proxy 记录

> 注意：本节只记录 debug/proxy/smoke evidence，不能作为 PhysX-Anything 在 bedroom_4 上的有效复现实验；它只证明部分代码路径和文件格式生成链路可执行。

这次实测只把 VLM debug wrapper 记为通过。该 wrapper 没有改官方 repo 源码，但绕开了两个环境问题：PyTorch 2.2.2 的 Qwen pytree 兼容问题，以及官方 `flash_attention_2` 依赖缺失问题。因此它是 debug path，不是官方原版 `1_vlm_demo.py`。

| 阶段 | 状态 | 证据 |
|---|---|---|
| `1_vlm_demo.py` official | Blocked | 官方代码第 146 行硬编码 `attn_implementation="flash_attention_2"`；当前 venv 没有 `flash_attn` |
| VLM debug wrapper | Debug evidence only | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/` 已生成 `basic_info.txt`、`coord_0..2.txt`、`ind_0..2.npy/.ply`、`allind.npy` |
| `2_decoder.py` official | Not passed | 官方脚本默认 textured `sample.glb` 尚未验证通过 |
| Decoder low-texture debug | Partial debug evidence | `run_control` 生成 mesh `343214` vertices / `686376` faces；geometry OBJ 已导出；textured GLB export 卡在后处理末段 |
| Geometry-only proxy GLB | Proxy artifact only | `sample_geometry_proxy.glb` 由 geometry OBJ 转出，12 MB，并软链为 `test_demo/.../sample.glb`；不是官方 decoder 输出 |
| `3_split.py` official on proxy GLB | Proxy path executed | 生成 3 个 part OBJ：board-like `0.obj`、tiny `1.obj`、vase-like `2.obj`；输入不是官方 textured `sample.glb` |
| `4_simready_gen.py` official on proxy split | Proxy path executed, not sim-validated | 生成 `basic_info.json`、`basic.urdf`、`basic.xml`；XML/URDF 已解析验证，OBJ 引用均存在，但没有仿真加载或动力学验证 |
| Simulator smoke test | Not tested | 尚未用 MuJoCo/PyBullet 实际加载或仿真 |

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

decoder / split / simready 脚本路径的 proxy 产物如下，只用于排障复查：

| 产物 | 路径 | 大小/规模 | 说明 |
|---|---|---|---|
| Geometry OBJ | `/root/autodl-tmp/physx-anything-outputs/bedroom_4_bedside_lamp_table_crop/sample_lowtex_geometry.obj` | `27499041` bytes；`343214` V / `686376` F；not watertight | debug decoder mesh 输出，未带官方 texture |
| Proxy GLB | `/root/autodl-tmp/physx-anything-outputs/bedroom_4_bedside_lamp_table_crop/sample_geometry_proxy.glb` | `12355984` bytes | geometry-only GLB，用于喂给官方 `3_split.py`；不是官方 textured `sample.glb` |
| Part 0 OBJ | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/objs/0/0.obj` | `336794` V / `673544` F；`27207161` bytes | 主体几何，吸收了绝大多数 faces |
| Part 1 OBJ | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/objs/1/1.obj` | `24` V / `27` F；`1231` bytes | 很小，说明 crop/VLM/proxy split 的 part 质量不稳定 |
| Part 2 OBJ | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/objs/2/2.obj` | `6415` V / `12805` F；`445593` bytes | vase-like 子部件 |
| URDF | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/basic.urdf` | `2233` bytes | XML parser 通过，引用 3 个 OBJ 均存在；未做 simulator smoke test |
| MJCF/XML | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/basic.xml` | `2847` bytes | root 为 `mujoco`，引用 3 个 OBJ 均存在；未做 simulator smoke test |
| Structured JSON | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/basic_info.json` | `1576` bytes | 由 `basic_info.txt` 转换出的结构化物理描述 |

这个记录只能说明 VLM debug wrapper 能把 bedroom_4 crop 转成 coarse physical representation，debug decoder 能产出一份可供脚本继续读取的几何，官方 split/simready 代码也能在 geometry-only proxy GLB 上走到 URDF/XML 文件生成。它没有证明 bedroom_4 物体被正确重建：复杂 crop 被理解成“桌子+花瓶”，没有恢复台灯/床头柜的真实语义；part 1 只有 24 个 vertices；mesh 非 watertight；官方 textured `sample.glb` 与真实 simulator smoke test 都缺失。因此这不是 bedroom_4 有效跑通，也不是可用于项目结论的 sim-ready 资产。

## 接入判断

短期建议是 **P1 research adapter，不进入主链路默认路径**：

| 层级 | 判断 | 原因 |
|---|---|---|
| P0 room reconstruction | 不进入 | 不是多视角房间重建器 |
| P1 object asset enrichment | 需要重新做干净单物体实验 | 理论上能输出 part mesh、URDF/XML、物理属性；当前 bedroom_4 proxy 记录不能作为该能力在本项目上的有效证据 |
| P1 simulator QA | 未通过 | 当前只有 proxy URDF/XML 文件生成，没有 MuJoCo/PyBullet 加载、碰撞和 joint smoke test |
| P2 articulated object library | 值得跟踪 | 对柜门、抽屉、笔记本、箱子、龙头等 articulated objects 很有价值 |
| P2 deformable object | 暂不做 | 官方 README 也建议 deformable flag 设为 0 以获得更可靠的 simulation |

下一步更稳的执行路线：

1. 若目标是官方原版复现，优先安装或编译 `flash-attn`，再重跑未改源码的 `1_vlm_demo.py`。
2. 继续定位 textured GLB export：降低 `texture_size`/`simplify`，或单独 profile `postprocessing_utils.to_glb` 在 `After remove invisible faces` 后的卡点；只有真实导出 `sample.glb` 后，才把 decoder 写成官方质量通过。
3. 如果继续保留当前 proxy 产物，只能把它作为排障输入，用 MuJoCo 或 PyBullet 做最小 simulator smoke test：文件可加载、mesh path 正确、质量/惯性不崩、关节/固定关系不报错；即便通过，也仍只是 proxy QA，不等于官方复现。
4. 换一个 mask-clean 单物体 crop，优先选真实 articulated object，例如柜门/抽屉/椅子，而不是这个混合了桌面、花瓶、床边背景的 heuristic crop。
5. 若要接入 Video2Mesh，当前记录最多只能作为 adapter 排障 trace；正式 baseline 应重新从 mask-clean 单物体输入开始，并保留 `source`、`official_step_status`、`qa_status`，避免把 debug/proxy 产物混入有效实验结果。

## 风险

- **磁盘风险**：`/data` 只剩约 25-27 GB 且 Use% 100%；权重已尽量放到 `/root/autodl-tmp`，但 decoder 中间 GLB/mesh/texture 仍可能因为 `/data` 满盘失败。
- **依赖风险**：官方 README 以 PyTorch 2.4.0 + CUDA 11.8 为默认，而 mil8 共享环境是 PyTorch 2.2.2 + CUDA 12.1；`xformers` 可用但 `flash_attn` 缺失，官方 VLM 原版仍不通过。
- **GLB export 风险**：pipeline load 和 sampling 已恢复，但 `to_glb` 在 texture/postprocess 后段仍会长时间卡住；当前可用的是 geometry-only proxy GLB，不是官方 textured output。
- **debug 标记风险**：pytree shim、Qwen `sdpa` monkeypatch、absolute-path decoder config 和 minimal `kaolin` stub 都是 debug workaround，不能写成官方复现。
- **输入风险**：PhysX-Anything 训练/推理假设单物体图像；`bedroom_4` full-room frame 会造成类别、尺度、部件和关节推理混乱。
- **坐标风险**：即使生成 URDF/XML，也还需要把单物体坐标、尺度和姿态对齐回 Video2Mesh 的 COLMAP/scene coordinate。
- **质量风险**：论文指标来自 PhysX-Mobility 和互联网单物体图像；不能直接外推到遮挡严重、背景复杂的室内扫描帧。
- **仿真风险**：自动物理属性必须经过 mass/friction/joint limit/penetration/support 的 simulator preflight，不可直接写进最终资产合同。
