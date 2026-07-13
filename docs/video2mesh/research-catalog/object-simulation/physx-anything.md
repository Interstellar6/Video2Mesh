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

检查日期：2026-07-11；最新续跑：2026-07-13

当前执行状态：论文 PDF、项目页、GitHub README、Hugging Face 权重页和 mil8 部署已复查；本轮没有下载完整 PhysX-Mobility 数据集，只下载并核验官方模型权重。官方 demo `demo/14.png` 在 mil8 的干净 checkout 中完成 VLM -> decoder -> split -> simready 链路：`test_demo/14/sample.glb`、part OBJ、`basic.urdf`、`basic.xml` 均已生成，MuJoCo 和 PyBullet 都能加载生成文件。证据边界必须写清楚：这不是“官方原版脚本无修改通过”，而是 **官方权重 + 官方 demo 输入 + 环境兼容 shim / 低显存兼容 decoder path**。旧的 bedroom_4 bedside crop 仍只算 debug/proxy 证据，不能写成 bedroom_4 跑通。

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

本轮在 mil8 做了两类事情：一是官方权重与官方 demo/14 的可复现性验证，二是保留旧 bedroom_4 debug/proxy 排障记录。下面的审计表要按阶段读，不能把 demo/14 的成功外推成 bedroom_4 成功。

| 项 | 结果 |
|---|---|
| Host | `mil8` |
| GPU | 8 x NVIDIA GeForce RTX 3090, each 24 GB；最近探针时 decoder 指定 `CUDA_VISIBLE_DEVICES=0` |
| Disk | `/data` 3.5 TB，已用约 3.3 TB，仅约 19 GB 可用，Use% 100%；`/` 440 GB，约 56 GB 可用 |
| Official repo | clean run: `/root/autodl-tmp/physx-anything-official-repro-20260713`；old bedroom_4 debug repo: `/data/zyx/workspace/PhysX-Anything` |
| Repo commit | `e221826` |
| Repo size | 55 MB |
| Shared Python | `/opt/envs/max/bin/python`, Python 3.10.0 |
| PyTorch | 2.2.2+cu121，CUDA 12.1，`torch.cuda.is_available=True`，8 GPUs visible |
| Existing required packages | `torch`, `torchvision`, `transformers`, `huggingface_hub`, `PIL`, `numpy`, `scipy`, `cv2` 等 |
| Initially missing packages | `qwen_vl_utils`, `trimesh`, `rembg`, `flash_attn`, `kaolin`, `nvdiffrast`, `spconv`, `mujoco`, `pybullet` |
| Isolated venv | `/root/autodl-tmp/physx-anything-venv`, created with `--system-site-packages` to reuse CUDA PyTorch |
| Packages added in isolated venv | `transformers==4.50.0`, `qwen-vl-utils==0.0.14`, `trimesh==4.12.2`, `rembg`, `accelerate`, `huggingface-hub`, `xformers`, `spconv-cu120`, `flash_attn==2.5.8`, `mujoco==3.10.0`, `pybullet==3.2.7` 等 |
| CUDA extensions | `nvdiffrast` 已从 `/root/autodl-tmp/nvdiffrast-src` 编译安装；`EasternJournalist/utils3d` 已按 TRELLIS 需要安装；`numpy==1.26.4`、`scipy==1.11.4` 已回退到可用版本 |
| Compatibility shims used for official demo/14 | PyTorch 2.2.2 需要 pytree shim；mil8 不能稳定访问 Hugging Face，所以 Qwen processor 被重定向到本地 processor 目录；官方 decoder `pipeline.json` 的相对路径改为绝对路径副本；系统 `diff-gaussian-rasterization` 不支持 `kernel_size` / `subpixel_offset`，运行时过滤这两个 kwargs |
| Weight size check | VLM `16G`、decoder `3.3G`、TRELLIS `3.1G`、Qwen processor 小文件 `11M`、flash-attn wheel `116M`；没有下载 PhysX-Mobility 数据集 |
| Weight placement | `pretrain/vlm -> /root/autodl-tmp/physx-anything-pretrain/vlm`；`pretrain/decoder -> /root/autodl-tmp/physx-anything-decoder-abs-debug`；`pretrain/trellis -> /root/autodl-tmp/physx-anything-trellis`；原始 decoder 权重保存在 `/root/autodl-tmp/physx-anything-pretrain/decoder` |
| VLM weights | four `model-00001..00004-of-00004.safetensors` present under `/root/autodl-tmp/physx-anything-pretrain/vlm` |
| Decoder weights | `/root/autodl-tmp/physx-anything-pretrain/decoder/ckpt_new/denoiser_step0350000.pt`, size 3.47 GB |
| TRELLIS weights | `ckpts/*.safetensors` present under `/root/autodl-tmp/physx-anything-trellis`; DINOv2 cached at `/root/.cache/torch/hub/checkpoints/dinov2_vitl14_reg4_pretrain.pth` |
| SSH note | `mil8` 曾短暂卡在 FRP/SSH banner exchange，后续恢复；当前官方 demo/14 已完成，剩余主要风险是未改源码路径、RF decode OOM 和 `/data` 满盘压力 |
| Official VLM blocker | `flash_attn` 已安装，但未改源码的 `1_vlm_demo.py` 在 PyTorch 2.2.2 / Transformers 4.50 的 pytree API 与在线 Qwen processor 访问上仍不稳定；本轮成功的是 runtime shim 路径 |
| Official demo/14 VLM result | 通过 pytree shim + 本地 Qwen processor redirect，`test_demo/14` 已生成 `basic_info.txt`、`coord_0..1.txt`、`ind_0..1.npy/.ply` 和 `allind.npy` |
| PyTorch 2.4 attempt | A clean Python 3.10 venv at `/root/autodl-tmp/physx-anything-torch24-venv` was repaired, but downloading `torch==2.4.0+cu121` from `download.pytorch.org` was too slow and did not complete; the environment still has no `torch`, so the practical route remains the existing venv plus Qwen shim. |
| Decoder config fix | 官方 decoder `pipeline.json` 的相对路径会触发 HFValidationError；compat copy `/root/autodl-tmp/physx-anything-decoder-abs-debug/pipeline.json` 已把子模型改成绝对路径 |
| Pipeline load re-probe | 2026-07-12 `TrellisImageTo3DPipeline.from_pretrained("./pretrain/decoder_abs_debug")` 用本地 DINOv2 cache 成功，`from_pretrained` 44.4 s，`.cuda()` 1.3 s |
| Decoder official-script blocker | 未改源码的 `2_decoder.py` 先被 decoder/TRELLIS 相对路径阻塞；修成绝对路径后默认 `run_control()` 含 RF decode，在 24GB RTX 3090 上 OOM |
| Official demo/14 decoder compat result | 使用官方 decoder/TRELLIS 权重和官方 `demo/14.png`，改走 `formats=["mesh", "gaussian"]`，释放 pipeline 后 `to_glb(texture_size=1024)` 成功导出 textured `sample.glb` |
| Official demo/14 split + simready | 官方 `3_split.py` 生成 2 个 part OBJ；官方 `4_simready_gen.py --voxel_define 32 --basepath ./test_demo --process 0 --fixed_base 0 --deformable 0` 生成 `basic_info.json`、`basic.urdf`、`basic.xml` |
| Engine load validation | 生成的 `basic.xml` 可被 MuJoCo `MjModel.from_xml_path` 加载并 step 20 次；`basic.urdf` 可被 PyBullet DIRECT 加载，包含 1 个 revolute joint 和 2 个 fixed joints |

实测失败日志的关键点：

```text
ImportError: cannot import name 'Qwen2_5_VLForConditionalGeneration' from 'transformers'
RuntimeError: register_pytree_node() got an unexpected keyword argument 'flatten_with_keys_fn'
1_vlm_demo.py unmodified: PyTorch 2.2.2 pytree / Qwen processor online access still requires runtime compatibility handling
2_decoder.py unmodified: decoder/TRELLIS relative path failure, then default RF decode OOM on 24GB GPU
compat decoder: mesh+gaussian output succeeded; RF output not tested in this low-VRAM path
bedroom_4 old proxy: geometry-only proxy GLB was used only for historical debugging, not official evidence
```

结论边界：当前已经完成的是官方权重下载/核验、官方 demo/14 在兼容路径下的 VLM、textured `sample.glb`、官方 split、官方 simready 文件生成，以及 MuJoCo/PyBullet 加载验证。尚未完成的是未改源码的 official `1_vlm_demo.py` / `2_decoder.py` 端到端原版通过、默认 RF decode、以及 bedroom_4 干净单物体 crop 的有效实验；因此不能写成“官方原版四步无修改通过”，也不能写成“bedroom_4 跑通”。

本地已回传的官方 demo/14 产物放在 `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/physx_official_repro_20260713`，包含 `sample.glb`、part OBJ、URDF/XML、运行日志和验证用依赖缓存。旧 bedroom_4 proxy 调试产物放在 `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/physx_anything_bedroom4_proxy_20260712`，仅用于复查历史排障，不进入正式复现实验结论。

## 官方 demo/14 实测

![PhysX-Anything official demo14 run](../assets/physx-anything/physx-anything-official-demo14-run.png "官方 demo/14 输入、VLM coarse voxels 和 split 后 part mesh 预览")

本轮选择官方 repo 自带的 `demo/14.png`，因为它是干净的 wall switch 单物体样例，符合论文的单图物体输入假设。没有下载完整官方数据集。

| 项 | 结果 |
|---|---|
| Remote clean repo | `/root/autodl-tmp/physx-anything-official-repro-20260713` |
| Upstream commit | `e221826e6176d940905126d1894f9c1c933b70a8` |
| Input | `demo/14.png`，本地副本 `tmp_remote_results/physx_official_repro_20260713/demo_14.png` |
| Local result copy | `tmp_remote_results/physx_official_repro_20260713/test_demo_14/` |
| VLM structured object | `Wall Switch`，category `Electrical Control Device`，dimension `8*8*3` |
| Parts | `l_0: Switch`，`l_1: Base Body` |
| Joint | group 1 relative to group 0，type `C` revolute，axis `[1, 0, 0]`，range `[0, 12]` degrees |
| Voxel outputs | `ind_0.npy` shape `(488, 3)`；`ind_1.npy` shape `(2085, 3)`；`allind.npy` shape `(2573, 3)` |
| Decoder output | `sample.glb`，`7,748,388` bytes，GLB header `glTF v2` |
| GLB mesh check | 1 textured geometry，`159,870` vertices / `277,428` faces，visual type `TextureVisuals` |
| Split output | `objs/0/0.obj`：`20,402` vertices / `29,196` faces；`objs/1/1.obj`：`140,287` vertices / `248,232` faces |
| Simready output | `basic_info.json`、`basic.urdf`、`basic.xml`、part textures and `desert.png` |
| File-reference check | URDF references `./objs/1/1.obj` and `./objs/0/0.obj`，all present；MJCF references OBJ/texture/skybox，all present |
| Engine load check | MuJoCo loads `basic.xml` and steps 20 frames；PyBullet loads `basic.urdf` with 3 joints: fixed, revolute, fixed |
| Logs | `tmp_remote_results/physx_official_repro_20260713/logs/official_demo14_*.log` |

这次可以写成：**官方权重已完整核验；官方 demo/14 在兼容路径下生成了 textured GLB、part OBJ、URDF/XML，并通过 MuJoCo/PyBullet 加载验证。** 不能写成：**未改源码官方四步原版通过**，因为 VLM 和 decoder 都用了运行时兼容处理；也不能写成：**bedroom_4 跑通**，因为这次有效样例是官方 `demo/14.png`。

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

这段是 2026-07-12 的旧 bedroom_4 排障记录。它只把 VLM debug wrapper 记为通过；该 wrapper 没有改官方 repo 源码，但绕开了 PyTorch 2.2.2 的 Qwen pytree 兼容问题，并且当时还没有完成 `flash_attn` wheel 安装。因此它是 debug path，不是官方原版 `1_vlm_demo.py`，也不是本轮官方 demo/14 的有效复现证据。

| 阶段 | 状态 | 证据 |
|---|---|---|
| `1_vlm_demo.py` official on bedroom_4 | Not tested after env fix | 旧记录发生在 `flash_attn` 安装前；后续没有把 bedroom_4 heuristic crop 作为正式输入重跑官方 VLM |
| VLM debug wrapper | Debug evidence only | `/data/zyx/workspace/PhysX-Anything/test_demo/bedroom_4_bedside_lamp_table_crop/` 已生成 `basic_info.txt`、`coord_0..2.txt`、`ind_0..2.npy/.ply`、`allind.npy` |
| `2_decoder.py` official on bedroom_4 | Not passed | bedroom_4 只跑过 debug decoder 和 geometry proxy；没有生成官方 textured `sample.glb` |
| Decoder low-texture debug | Partial debug evidence | `run_control` 生成 mesh `343214` vertices / `686376` faces；geometry OBJ 已导出；textured GLB export 卡在后处理末段 |
| Geometry-only proxy GLB | Proxy artifact only | `sample_geometry_proxy.glb` 由 geometry OBJ 转出，12 MB，并软链为 `test_demo/.../sample.glb`；不是官方 decoder 输出 |
| `3_split.py` official on proxy GLB | Proxy path executed | 生成 3 个 part OBJ：board-like `0.obj`、tiny `1.obj`、vase-like `2.obj`；输入不是官方 textured `sample.glb` |
| `4_simready_gen.py` official on proxy split | Proxy path executed, not sim-validated | 生成 `basic_info.json`、`basic.urdf`、`basic.xml`；XML/URDF 已解析验证，OBJ 引用均存在，但没有对 bedroom_4 proxy 做仿真加载或动力学验证 |
| Simulator smoke test for bedroom_4 proxy | Not tested | 本轮 MuJoCo/PyBullet 加载验证只针对官方 `demo/14`，不是 bedroom_4 proxy |

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

这个记录只能说明 VLM debug wrapper 能把 bedroom_4 crop 转成 coarse physical representation，debug decoder 能产出一份可供脚本继续读取的几何，官方 split/simready 代码也能在 geometry-only proxy GLB 上走到 URDF/XML 文件生成。它没有证明 bedroom_4 物体被正确重建：复杂 crop 被理解成“桌子+花瓶”，没有恢复台灯/床头柜的真实语义；part 1 只有 24 个 vertices；mesh 非 watertight；官方 textured `sample.glb` 与 bedroom_4 的真实 simulator smoke test 都缺失。因此这不是 bedroom_4 有效跑通，也不是可用于项目结论的 sim-ready 资产。

## 接入判断

短期建议是 **P1 research adapter，不进入主链路默认路径**：

| 层级 | 判断 | 原因 |
|---|---|---|
| P0 room reconstruction | 不进入 | 不是多视角房间重建器 |
| P1 object asset enrichment | 官方 demo 已验证，Video2Mesh 仍需干净单物体 crop | 官方 `demo/14.png` 已生成 part mesh、URDF/XML、物理属性；但 bedroom_4 proxy 记录不能作为本项目有效证据 |
| P1 simulator QA | demo/14 加载通过，项目接入未通过 | 官方 demo/14 的 MJCF/URDF 可被 MuJoCo/PyBullet 加载；Video2Mesh 还没做真实 crop 的 scale、pose、support、penetration 和 joint QA |
| P2 articulated object library | 值得跟踪 | 对柜门、抽屉、笔记本、箱子、龙头等 articulated objects 很有价值 |
| P2 deformable object | 暂不做 | 官方 README 也建议 deformable flag 设为 0 以获得更可靠的 simulation |

下一步更稳的执行路线：

1. 若目标是官方原版复现，继续修未改源码路径：PyTorch/Transformers/Qwen processor 兼容、官方 decoder/TRELLIS 相对路径，以及默认 RF decode 在 24GB GPU 上的 OOM。
2. 若目标是 Video2Mesh 接入，下一步应从 mask-clean 单物体 crop 开始，优先选柜门、抽屉、开关、椅子这类真实 articulated object，而不是混合桌面、花瓶、床边背景的 heuristic crop。
3. 把官方 demo/14 作为“环境和权重可用”的基线，把 bedroom_4 proxy 仅作为历史排障 trace；正式 baseline 需要保留 `source`、`official_step_status`、`compatibility_shims`、`qa_status`。
4. 对接 Video2Mesh 时必须新增 alignment/preflight：把单物体坐标、尺度和姿态对齐回 COLMAP/scene coordinate，再检查 support、penetration、mass、joint limit 和 simulator loading。
5. 不下载完整 PhysX-Mobility 数据集；除非要做论文 benchmark，当前只需要官方权重、官方 demo 和本项目自己的干净 crop。

## 风险

- **磁盘风险**：`/data` 只剩约 19 GB 且 Use% 100%；权重和输出已尽量放到 `/root/autodl-tmp`，但 decoder 中间 GLB/mesh/texture 仍可能因为误写 `/data` 失败。
- **依赖风险**：官方 README 以 PyTorch 2.4.0 + CUDA 11.8 为默认，而 mil8 共享环境是 PyTorch 2.2.2 + CUDA 12.1；`flash_attn` 已安装，但官方原版 VLM 仍受 pytree/Qwen processor 兼容影响。
- **GLB export 风险**：官方 demo/14 的 textured `sample.glb` 已在 mesh+gaussian 兼容路径下导出；默认 RF decode 在 24GB GPU 上 OOM，不能写成完整 decoder 默认输出通过。
- **debug 标记风险**：pytree shim、Qwen processor redirect、absolute-path decoder config、diff-gaussian raster kwargs filter、mesh+gaussian-only decoder path 都是 compatibility workaround，不能写成官方原版复现。
- **输入风险**：PhysX-Anything 训练/推理假设单物体图像；`bedroom_4` full-room frame 会造成类别、尺度、部件和关节推理混乱。
- **坐标风险**：即使生成 URDF/XML，也还需要把单物体坐标、尺度和姿态对齐回 Video2Mesh 的 COLMAP/scene coordinate。
- **质量风险**：论文指标来自 PhysX-Mobility 和互联网单物体图像；不能直接外推到遮挡严重、背景复杂的室内扫描帧。
- **仿真风险**：自动物理属性必须经过 mass/friction/joint limit/penetration/support 的 simulator preflight，不可直接写进最终资产合同。
