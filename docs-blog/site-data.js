window.V2M_BLOG_DATA = {
  "generatedAt": "2026-07-01 16:59",
  "docs": [
    {
      "id": "readme",
      "title": "Video2Mesh",
      "category": "Pipeline",
      "summary": "Video2Mesh turns a scan video into layered 3D assets: 3DGS visual scene, semantic object masks, object meshes, collision proxies, physics metadata and simulator adapters.",
      "source_path": "README.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Pipeline"
      ],
      "body": "# Video2Mesh\n\nVideo2Mesh turns a scan video into layered 3D assets: 3DGS visual scene, semantic object masks, object meshes, collision proxies, physics metadata and simulator adapters.\n\nThe canonical documentation is now in [docs/](docs/README.md).\n\n## Quick Start\n\n```bash\ncd /root/autodl-tmp/workspace/Video2Mesh\nsource /etc/network_turbo >/dev/null 2>&1 || true\n\nbash tools/run_video2mesh_quick.sh dataset/<video>.mp4\n```\n\nCurrent default route:\n\n```text\nvideo\n  -> COLMAP poses and full point cloud\n  -> GraphDECO 3DGS\n  -> SAM2 masks\n  -> 2D-to-3D semantic fusion\n  -> object mesh / completion jobs\n  -> collider and physics proxies\n  -> MuJoCo / Unity / Isaac assets\n```\n\nFor commands, QA and research decisions, start here:\n\n- [Project Overview](docs/01-project-overview.md)\n- [Pipeline And Commands](docs/02-pipeline-and-commands.md)\n- [Research Roadmap](docs/03-research-roadmap.md)\n- [Mesh, Interaction And Completion](docs/04-mesh-interaction-and-completion.md)\n- [Operations And Showcase](docs/05-operations-and-showcase.md)\n- [Site And Remote Control](docs/06-site-and-remote-control.md)\n\nGenerated data, exports, checkpoints, videos and model weights are intentionally ignored by Git.\n",
      "headings": [
        {
          "level": "2",
          "text": "Quick Start",
          "slug": "quick-start"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "readme-2",
      "title": "Video2Mesh 文档中心",
      "category": "Overview",
      "summary": "Video2Mesh 精简后的唯一主文档入口，按项目总览、流水线、研究路线、交互仿真、运行展示和网站运维分类。",
      "source_path": "docs/README.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Video2Mesh",
        "Docs",
        "Overview"
      ],
      "body": "\n# Video2Mesh 文档中心\n\n这个目录是 Video2Mesh 的精简文档入口。旧的根目录长报告已经合并到这里，不再作为主文档维护。\n\n## 文档结构\n\n| 文档 | 读者问题 | 内容 |\n|---|---|---|\n| [01-project-overview.md](01-project-overview.md) | 这个项目到底做什么？ | 项目目标、资产分层、当前边界、参考项目角色 |\n| [02-pipeline-and-commands.md](02-pipeline-and-commands.md) | 怎么跑？产物在哪里？ | 端到端流水线、远端命令、关键输出、QA |\n| [03-research-roadmap.md](03-research-roadmap.md) | 学术和业界路线怎么选？ | 场景扫描、3DGS、mesh、Scene Graph、方法优先级 |\n| [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) | 怎么让场景可交互？遮挡怎么补？ | 3DGS-to-mesh、collider、补全、语义、SimAnything 动态线 |\n| [05-operations-and-showcase.md](05-operations-and-showcase.md) | 展示和排错怎么做？ | 远端环境、历史 run、展示清单、常见失败处理 |\n| [06-site-and-remote-control.md](06-site-and-remote-control.md) | relumeow.top 怎么更新？ | Markdown 网站、API、登录、远程控制边界 |\n\n## 当前结论\n\nVideo2Mesh 的核心路线不是“从视频直接生成一个完美 mesh”，而是把真实扫描视频拆成多层资产：\n\n```text\nvideo\n  -> COLMAP / learned pose fallback\n  -> GraphDECO 3DGS visual scene\n  -> 2D/3D object masks\n  -> semantic / probability splats\n  -> object visual mesh\n  -> collider / physics proxy\n  -> simulator adapters and review pack\n```\n\n最重要的工程判断：\n\n- 3DGS 负责高质量视觉层，不直接负责碰撞。\n- mesh/collider 是物理和交互代理，不要求和视觉 3DGS 一样精细。\n- semantic layer 独立保存，必要时投到 mesh face、collider 或 trigger。\n- 遮挡补全要分成 object visual completion、background clean plate、physics proxy completion 三件事。\n- SimAnything / PhysSplat 应作为 dynamic Gaussian 和物理属性增强线，不替代 mesh/collider 主链路。\n\n## 优先级\n\n| 优先级 | 目标 | 当前推荐 |\n|---|---|---|\n| P0 | 跑通可展示闭环 | COLMAP + GraphDECO + SAM2 + 3D masks + simulator bundle |\n| P0 | 场景级碰撞 | dense point cloud / Poisson / simplified static collider |\n| P1 | 物体 visual mesh | 3DGS rendered RGB/depth/normal/mask -> TSDF / Poisson |\n| P1 | 动态物体 collider | primitive compound / convex hull / CoACD or V-HACD |\n| P1 | 遮挡补全 | Hunyuan3D / Meshy / TRELLIS / image-blaster 生成完整视觉 mesh，再按 bbox 对齐 |\n| P2 | 高质量 3DGS-to-mesh | GS2Mesh-style stereo depth fusion、SuGaR、2DGS、GOF |\n| P2 | 动态 Gaussian | SimAnything / PhysSplat-style semantic Gaussian -> physics object |\n\n## 旧文档合并说明\n\n| 旧主题 | 新位置 |\n|---|---|\n| `Video2Mesh_PROJECT_README.md`、`README.md` | [01-project-overview.md](01-project-overview.md) |\n| `VIDEO2MESH_PIPELINE.md`、`SVLGaussian_frame_matching_notes.md` | [02-pipeline-and-commands.md](02-pipeline-and-commands.md) |\n| `SCENE_SCANNING_SOLUTIONS_SURVEY.md`、`FEED_FORWARD_GAUSSIAN_SCENE_GRAPH_SURVEY.md` | [03-research-roadmap.md](03-research-roadmap.md) |\n| `MESH_RECONSTRUCTION_METHODS_SURVEY.md`、`INTERACTIVE_GAME_SCENE_FROM_3DGS_SURVEY.md`、`SIM_ANYTHING_PHYS_SPLAT_SURVEY.md` | [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) |\n| `REMOTE_SETUP_STATUS.md`、`Video2Mesh_real_demo_runbook.md`、`Video2Mesh_milscene*.md` | [05-operations-and-showcase.md](05-operations-and-showcase.md) |\n| `docs-blog/content/*.md` | [06-site-and-remote-control.md](06-site-and-remote-control.md) |\n",
      "headings": [
        {
          "level": "2",
          "text": "文档结构",
          "slug": "文档结构"
        },
        {
          "level": "2",
          "text": "当前结论",
          "slug": "当前结论"
        },
        {
          "level": "2",
          "text": "优先级",
          "slug": "优先级"
        },
        {
          "level": "2",
          "text": "旧文档合并说明",
          "slug": "旧文档合并说明"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "01-project-overview",
      "title": "Video2Mesh 项目总览",
      "category": "Overview",
      "summary": "Video2Mesh 的目标、系统边界、资产分层、参考项目角色和当前工程状态。",
      "source_path": "docs/01-project-overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Video2Mesh",
        "3DGS",
        "Simulator",
        "Overview"
      ],
      "body": "\n# Video2Mesh 项目总览\n\n## 项目目标\n\nVideo2Mesh 的目标是把一段真实空间扫描视频转换成可展示、可拆分、可进入仿真器或游戏引擎的 3D 场景资产。\n\n它不是单图 3D 生成工具，也不是只输出一个好看 mesh 的 photogrammetry pipeline。它的目标产物是一组分层资产：\n\n```text\nscene visual representation\nobject and background semantic masks\nobject visual meshes\ncollision and physics proxies\nscene graph / semantic sidecars\nUnity / MuJoCo / Isaac adapters\nreview and QA reports\n```\n\n## 当前默认链路\n\n```text\nscan video\n  -> real-frame extraction\n  -> COLMAP poses and full point cloud\n  -> GraphDECO 3D Gaussian Splatting\n  -> SAM prompt discovery + SAM2 tracking\n  -> 2D mask to 3D mask fusion\n  -> semantic / probability Gaussian export\n  -> object frame selection\n  -> object mesh and completion jobs\n  -> simulator asset bundle\n  -> adapters and QA\n```\n\n默认 3DGS 后端是 GraphDECO。旧的 minimal gsplat 路线只作为 debug/smoke fallback，不作为真实实验默认结果。\n\n## 资产分层\n\n| 层 | 主要产物 | 作用 |\n|---|---|---|\n| Visual | 3DGS / semantic splat / visual mesh | 看起来像真实场景 |\n| Geometry | point cloud / object mesh / background planes | 支撑重建、对齐和导出 |\n| Collision | simplified mesh / box / convex hull / compound collider | 让角色、物体、射线和物理系统可交互 |\n| Semantic | object ids / labels / probabilities / scene graph | 查询“这是什么、能做什么、和谁相邻” |\n| Physics | body type / mass / friction / restitution / material | 进入 MuJoCo、Unity、Isaac 的仿真合同 |\n| Adapter | `unity_adapter.json`、MuJoCo XML、review HTML | 给不同 runtime 消费 |\n\n核心原则：3DGS 是视觉层；碰撞、导航、交互和语义必须有独立资产承接。\n\n## 项目边界\n\nVideo2Mesh 当前负责：\n\n- 从真实视频抽帧并建立相机/点云/3DGS。\n- 跟踪 2D masks 并融合成 3D object masks。\n- 生成 semantic splats / probability splats。\n- 选择 object frames 和 object crops。\n- 导出 object mesh baseline、3DGS-derived mesh jobs、external mesh jobs。\n- 生成 simulator asset bundle、adapter 和 QA 报告。\n\nVideo2Mesh 不应伪装负责：\n\n- 商业级 photogrammetry texture baking。\n- 完整神经 SDF 训练器。\n- 物理引擎内部 solver。\n- 所有遮挡区域的真实几何恢复。\n- 自动生成百分百可信的质量、摩擦、恢复系数。\n\n这些能力可以通过外部 backend 接入，但要保留输入/输出合同和 QA。\n\n## 参考项目角色\n\n| 项目 / 方法 | 角色 | 不能误解成 |\n|---|---|---|\n| SceneVerse++ | 结构化 3D scene understanding、PQ3D/SpatialLM 数据桥接 | 任意视频到 3DGS-to-mesh 的完整系统 |\n| image-blaster | 单物体图像到 mesh、world 目录、Three.js viewer 资产约定 | Video2Mesh 的 simulator bundle 生成器 |\n| World Labs / Marble | 静态 world/background 生成和 clean plate 思路 | 物体级仿真资产导出器 |\n| SuGaR | 从 3DGS 提取 editable visual mesh 的高级后端 | P0 collider 主路线 |\n| GS2Mesh | 用 3DGS 渲染 stereo views，再 depth fusion 成 mesh | 直接读取 Gaussian centers 连面 |\n| SimAnything / PhysSplat | semantic Gaussian 到 dynamic Gaussian / physical object | mesh 补全或 Unity collider 替代品 |\n\n## 当前系统状态\n\n已闭合：\n\n- 视频到相机/点云/3DGS 的工程链路。\n- SAM2 2D mask tracking 和 2D-to-3D mask fusion。\n- semantic/probability PLY 导出。\n- object frame selection 和 object crops。\n- simulator bundle、Unity/MuJoCo adapter、review pack。\n- QA/readiness/showcase 报告。\n\n仍是 baseline：\n\n- 物体 mesh 对遮挡和细结构还不够稳定。\n- object label 和 affordance 需要 open-vocabulary detector / VLM 增强。\n- 真实尺度、质量、摩擦、恢复系数仍需校准或人工复核。\n- 背景结构目前以 floor/wall/ceiling 等基础结构为主，door/window/cabinet 等需要更强 layout/scene graph。\n\n## 仓库主要目录\n\n```text\nvideo2mesh/                 # Python CLI and pipeline implementation\ntools/                      # shell helpers, remote run scripts, audit scripts\nconfigs/                    # reusable config\ndocs/                       # current canonical docs\ndocs-blog/                  # relumeow.top static docs site and admin API\nSceneVersepp/               # submodule / reference project\nimage-blaster/              # submodule / reference object generation project\nexports/                    # generated runs, ignored by Git\ndataset/                    # source videos, ignored by Git\ncheckpoints/                # model weights, ignored by Git\n```\n\nGenerated videos, exports, model weights and 3D assets are intentionally ignored by Git.\n",
      "headings": [
        {
          "level": "2",
          "text": "项目目标",
          "slug": "项目目标"
        },
        {
          "level": "2",
          "text": "当前默认链路",
          "slug": "当前默认链路"
        },
        {
          "level": "2",
          "text": "资产分层",
          "slug": "资产分层"
        },
        {
          "level": "2",
          "text": "项目边界",
          "slug": "项目边界"
        },
        {
          "level": "2",
          "text": "参考项目角色",
          "slug": "参考项目角色"
        },
        {
          "level": "2",
          "text": "当前系统状态",
          "slug": "当前系统状态"
        },
        {
          "level": "2",
          "text": "仓库主要目录",
          "slug": "仓库主要目录"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "02-pipeline-and-commands",
      "title": "Video2Mesh 流水线与命令",
      "category": "Pipeline",
      "summary": "当前端到端运行方式、关键阶段、产物路径、恢复命令和 QA 命令。",
      "source_path": "docs/02-pipeline-and-commands.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Pipeline",
        "COLMAP",
        "GraphDECO",
        "SAM2"
      ],
      "body": "\n# Video2Mesh 流水线与命令\n\n## 端到端流程\n\n```text\ninput video\n  -> extract-frames\n  -> run-colmap\n  -> train/import GraphDECO 3DGS\n  -> auto prompts\n  -> SAM2 mask tracking\n  -> fuse-masks\n  -> export semantic splats\n  -> select object frames\n  -> prepare object images\n  -> reconstruct or import object meshes\n  -> export simulator assets\n  -> QA / readiness / showcase reports\n```\n\n## 远端快速运行\n\n```bash\ncd /root/autodl-tmp/workspace/Video2Mesh\nsource /etc/network_turbo >/dev/null 2>&1 || true\n\nbash tools/run_video2mesh_quick.sh dataset/<video>.mp4\n```\n\n常用高质量覆盖：\n\n```bash\nMAX_FRAMES=200 \\\nEXTRACT_EVERY=1 \\\nGRAPHDECO_ITERATIONS=30000 \\\nGRAPHDECO_SAVE_ITERATIONS=\"7000 30000\" \\\nGRAPHDECO_TEST_ITERATIONS=\"7000 30000\" \\\nGRAPHDECO_RESOLUTION=1 \\\nbash tools/run_video2mesh_quick.sh dataset/<video>.mp4\n```\n\n指定真实视频时间窗：\n\n```bash\nSTART_SEC=47 \\\nEND_SEC=56 \\\nMAX_FRAMES=200 \\\nEXTRACT_EVERY=1 \\\nbash tools/run_video2mesh_quick.sh dataset/<video>.mp4\n```\n\n帧规则：只使用真实 decoded frames。如果候选帧数超过 `MAX_FRAMES`，就在真实帧中均匀采样，不插值。\n\n## COLMAP 与点云\n\n默认入口：\n\n```bash\npython -m video2mesh.cli run-colmap \\\n  --project-root exports/<run> \\\n  --frames-dir exports/<run>/scene/frames\n```\n\n关键产物：\n\n```text\nscene/cameras/camera_info.json\nscene/reconstruction/point_cloud.ply\n```\n\n`point_cloud.ply` 是默认全量点云，供 3DGS、mask fusion、semantic transfer、object mask cloud 使用。`point_cloud_10k.ply` 或其他轻量版本只用于预览和 debug。\n\n如果 COLMAP readiness 失败，通常应换真实时间窗重跑，而不是补插值帧。\n\n## GraphDECO 3DGS\n\n远端 GraphDECO 默认路径：\n\n```text\n/root/autodl-tmp/workspace/gaussian-splatting\n```\n\n对已有 run 单独补跑：\n\n```bash\nITERATIONS=30000 \\\nSAVE_ITERATIONS=\"7000 30000\" \\\nTEST_ITERATIONS=\"7000 30000\" \\\nRESOLUTION=1 \\\nbash tools/run_graphdeco_3dgs.sh exports/<run>\n```\n\n默认生产设置：\n\n```text\niterations: 30000\nsave/test: 7000, 30000\nSH degree: 3\ndensify from: 500\ndensify until: 15000\nopacity reset: 3000\n```\n\n低显存处理顺序：\n\n1. 保持 full `point_cloud.ply`。\n2. 降低 `GRAPHDECO_RESOLUTION`。\n3. 降低 `GRAPHDECO_ITERATIONS` 做诊断。\n4. 只有完全无法训练时才考虑点数限制。\n\n## 语义 mask 与 semantic splats\n\n核心输入：\n\n```text\nmasks/2d/<object_id>/<frame>.png\nscene/cameras/camera_info.json\nscene/reconstruction/point_cloud.ply\n```\n\n核心命令：\n\n```bash\npython -m video2mesh.cli fuse-masks \\\n  --project-root exports/<run> \\\n  --point-cloud exports/<run>/scene/reconstruction/point_cloud.ply \\\n  --fusion-mode probability \\\n  --min-votes 1\n\npython -m video2mesh.cli export-splat-masks \\\n  --project-root exports/<run> \\\n  --mask-source-ply exports/<run>/scene/reconstruction/point_cloud.ply \\\n  --transfer-mode nearest\n\npython -m video2mesh.cli backproject-gaussian-probabilities \\\n  --project-root exports/<run>\n```\n\n关键输出：\n\n```text\nmasks/3d/<object_id>/point_indices.json\nmasks/3d/<object_id>/point_probabilities.npz\nsimulator_assets/semantic_splats.ply\nsimulator_assets/semantic_gaussian_probabilities.ply\nsimulator_assets/viewer_plys/\n```\n\n大点云 run 可以先跳过最重的 Gaussian probability backprojection，等 object masks 和 simulator bundle 已经可用后再补。\n\n## 选帧与物体图像\n\n默认选帧策略来自 SVLGaussian-style protocol 的工程化版本：\n\n```text\nbest visible anchor\n  + frame offset 5\n  + frame offset 10\n  + random window 30\n  + masked crop diversity fallback\n```\n\n命令：\n\n```bash\npython -m video2mesh.cli select-frames \\\n  --project-root exports/<run> \\\n  --selection-method svlgaussian \\\n  --top-k 4\n\npython -m video2mesh.cli prepare-object-images \\\n  --project-root exports/<run> \\\n  --top-k 4 \\\n  --skip-missing\n```\n\n产物：\n\n```text\nobjects/<object_id>/selected_frames/\nobjects/<object_id>/object_images/\n```\n\n## 物体 mesh\n\n临时 baseline：\n\n```bash\npython -m video2mesh.cli reconstruct-object-meshes \\\n  --project-root exports/<run> \\\n  --method bbox \\\n  --skip-failed\n```\n\n这个 baseline 只用于尺度、位置和导出接口检查。它会有碎片、破洞、悬浮面片和非 watertight 问题，不作为最终物体模型。\n\n生产路线：\n\n```text\ntrained 3DGS + object masks + registered cameras\n  -> render object-centric RGB/depth/normal/mask\n  -> masked TSDF fusion\n  -> marching cubes / Poisson\n  -> optional NeuS-style SDF refinement\n  -> texture baking + simplification + collider generation\n```\n\n入口：\n\n```bash\npython -m video2mesh.cli export-3dgs-mesh-observations \\\n  --project-root exports/<run> \\\n  --max-frames-per-object 6 \\\n  --device cuda\n\npython -m video2mesh.cli reconstruct-3dgs-object-meshes \\\n  --project-root exports/<run> \\\n  --method auto \\\n  --format obj \\\n  --skip-failed\n\npython -m video2mesh.cli prepare-neus-surface-jobs \\\n  --project-root exports/<run> \\\n  --provider external_neus_sdf\n```\n\n外部补全/生成 mesh 入口：\n\n```bash\npython -m video2mesh.cli export-image-blaster \\\n  --project-root exports/<run> \\\n  --provider hunyuan\n\npython -m video2mesh.cli mesh-commands \\\n  --project-root exports/<run> \\\n  --provider hunyuan\n\npython -m video2mesh.cli import-object-meshes \\\n  --project-root exports/<run> \\\n  --provider external_mesh\n```\n\n如果生成的 object-local mesh 尺度不可信，导出 simulator assets 时用 bbox 对齐。\n\n## Simulator assets\n\n```bash\npython -m video2mesh.cli export-simulator-assets \\\n  --project-root exports/<run> \\\n  --simulator-format mujoco unity \\\n  --collision-proxy bbox \\\n  --use-collision-proxy \\\n  --collider box \\\n  --body-type dynamic\n```\n\n关键输出：\n\n```text\nsimulator_assets/simulator_asset_bundle.json\nsimulator_assets/adapters/mujoco/scene.xml\nsimulator_assets/adapters/unity/unity_adapter.json\nsimulator_assets/review/index.html\n```\n\n## QA\n\n推荐每个 run 结束后执行：\n\n```bash\npython -m video2mesh.cli evaluate \\\n  --project-root exports/<run> \\\n  --json \\\n  --output exports/<run>/simulator_assets/evaluation_report.json\n\npython -m video2mesh.cli validate \\\n  --project-root exports/<run>\n\npython -m video2mesh.cli production-readiness \\\n  --project-root exports/<run> \\\n  --no-require-scale-calibration\n\npython -m video2mesh.cli qa-simulator-assets \\\n  --project-root exports/<run> \\\n  --require-physics\n\npython -m video2mesh.cli simulator-physics-quality-report \\\n  --project-root exports/<run>\n```\n\n展示包检查：\n\n```bash\nbash tools/audit_showcase_artifacts.sh exports/<run>\n```\n\n## 恢复下游阶段\n\n如果 COLMAP/GraphDECO 已经完成，只恢复 mask、mesh、simulator 资产：\n\n```bash\nbash tools/run_video2mesh_downstream_light.sh \\\n  exports/<run> \\\n  dataset/<video>.mp4\n```\n\n默认会跳过最重的 Gaussian probability backprojection，并限制背景 RANSAC/Fit 采样，但 object mask fusion 仍使用 full scene point cloud。\n",
      "headings": [
        {
          "level": "2",
          "text": "端到端流程",
          "slug": "端到端流程"
        },
        {
          "level": "2",
          "text": "远端快速运行",
          "slug": "远端快速运行"
        },
        {
          "level": "2",
          "text": "COLMAP 与点云",
          "slug": "colmap-与点云"
        },
        {
          "level": "2",
          "text": "GraphDECO 3DGS",
          "slug": "graphdeco-3dgs"
        },
        {
          "level": "2",
          "text": "语义 mask 与 semantic splats",
          "slug": "语义-mask-与-semantic-splats"
        },
        {
          "level": "2",
          "text": "选帧与物体图像",
          "slug": "选帧与物体图像"
        },
        {
          "level": "2",
          "text": "物体 mesh",
          "slug": "物体-mesh"
        },
        {
          "level": "2",
          "text": "Simulator assets",
          "slug": "simulator-assets"
        },
        {
          "level": "2",
          "text": "QA",
          "slug": "qa"
        },
        {
          "level": "2",
          "text": "恢复下游阶段",
          "slug": "恢复下游阶段"
        }
      ],
      "reading_minutes": 2
    },
    {
      "id": "03-research-roadmap",
      "title": "技术调研与路线图",
      "category": "Research",
      "summary": "学术界、工业界和参考项目对 Video2Mesh 的启发，压缩为可执行路线图。",
      "source_path": "docs/03-research-roadmap.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Research",
        "Scene Graph",
        "Mesh",
        "3DGS"
      ],
      "body": "\n# 技术调研与路线图\n\n## 总结判断\n\nVideo2Mesh 不应该押注单一“3DGS 转 mesh”方法。更稳的路线是把问题拆成阶段：\n\n```text\npose and reconstruction\n  -> visual 3DGS\n  -> semantic object masks\n  -> mesh / collider / physics assets\n  -> scene graph and simulator adapters\n```\n\n学术方法和工业产品给出的共同启发是：视觉表达、物理碰撞、语义结构和交互逻辑要分层。\n\n## 方法横评\n\n| 方向 | 代表方法 | 对 Video2Mesh 的价值 | 优先级 |\n|---|---|---|---|\n| 经典 SfM/MVS | COLMAP、OpenMVS | 稳定 baseline，输出标准相机和点云 | P0 |\n| 学习式几何兜底 | DUSt3R、MASt3R、MegaSaM、VGGT | 当 COLMAP 失败时补 pose/depth/point map | P1 |\n| 3DGS visual | GraphDECO 3DGS、Spark/SuperSplat | 高质量场景视觉层 | P0 |\n| mask tracking | GroundingDINO、SAM、SAM2、DEVA/XMem | object masks 和语义入口 | P0/P1 |\n| 2D-to-3D semantic | projection voting、SVLGaussian-style backprojection | semantic splats / object masks | P0/P1 |\n| point-cloud meshing | Poisson、BPA、alpha shape | 快速 scene collider / baseline mesh | P0 |\n| depth fusion mesh | 3DGS rendered depth/mask + TSDF | object visual mesh 主路线 | P1 |\n| 3DGS-aware mesh | SuGaR、GS2Mesh、2DGS、GOF | 高质量 visual mesh 升级 | P2 |\n| scene graph | SpatialLM、PQ3D、open-vocabulary 3D scene graph | 结构化关系、support、affordance | P1/P2 |\n| generated completion | Hunyuan3D、Meshy、TRELLIS、InstantMesh | 遮挡物体 visual mesh 补全 | P1 |\n| dynamic Gaussian | SimAnything / PhysSplat | 软体/颗粒/动态视觉仿真 | P2 |\n\n## 学术路线\n\n### 位姿与重建\n\nCOLMAP 仍是最稳的工程 baseline：可复现、输出标准、能接 GraphDECO 3DGS。问题是它对视频质量、视差、纹理、运动模糊敏感。\n\n建议：\n\n- 默认 COLMAP。\n- readiness 失败时使用 learned pose/depth fallback。\n- 保留 scan QA：覆盖、视差、模糊、注册率、点数。\n\n### 3DGS\n\n3DGS 适合做 visual scene，不适合直接做 collider。原始 Gaussian 是离散椭球体集合，没有 mesh topology。\n\n建议：\n\n- 3DGS 作为视觉层和多视角证据生成器。\n- object mesh 从 rendered RGB/depth/normal/mask 融合得到。\n- semantic splats 作为语义主数据之一。\n\n### 语义与 scene graph\n\n只得到 object mask 还不够。交互场景需要知道：\n\n- object category。\n- support relation，例如 chair supported_by floor。\n- spatial relation，例如 cup on table。\n- affordance，例如 chair sit-able、table placeable。\n- background structure，例如 floor、wall、door、window、cabinet。\n\n第一版 scene graph 可以是 sidecar JSON，不要强行写入 mesh：\n\n```json\n{\n  \"objects\": [\n    {\n      \"object_id\": \"chair_01\",\n      \"category\": \"chair\",\n      \"bbox\": {},\n      \"support\": {\"type\": \"floor\"},\n      \"affordances\": [\"sit\"],\n      \"asset_refs\": {\n        \"visual_mesh\": \"...\",\n        \"collider\": \"...\",\n        \"semantic_splats\": \"...\"\n      }\n    }\n  ]\n}\n```\n\n## 业界路线\n\n| 产品 / 实践 | 启发 |\n|---|---|\n| Matterport | 标准化资产包、测量、mesh/点云/E57/MatterPak 分层 |\n| Apple RoomPlan | 参数化 room layout 比纯 mesh 更适合交互和编辑 |\n| Polycam / Scaniverse | Gaussian splat 和 mesh 分用途输出 |\n| RealityCapture / RealityScan | meshing 前做 quality heatmap 和 mask/align QA |\n| PlayCanvas / SuperSplat | 3DGS 可做实时视觉层，但碰撞需要传统代理 |\n| Unity / Unreal | 交互依赖 collider、prefab/component、navmesh 和 metadata |\n\n## SuGaR 与 GS2Mesh\n\nSuGaR 的思路是让 Gaussian 更贴近表面，再提取 editable mesh。它适合做 visual mesh 升级，但不是第一版 collider。\n\n![SuGaR pipeline and editing result](https://anttwo.github.io/sugar/results/full_teaser.png \"SuGaR 官方项目页图：从 3DGS 提取可编辑 mesh，并保持高质量 Gaussian rendering / compositing 效果\")\n\nGS2Mesh 的思路是把 3DGS 当渲染器，生成 stereo-aligned novel views，用 stereo depth 得深度，再 TSDF fusion 成 mesh。它和 Video2Mesh 当前 “render views -> TSDF” 方向更契合。\n\n推荐顺序：\n\n1. 先强化现有 `3DGS render depth/mask -> TSDF`。\n2. 加 GS2Mesh-style stereo depth 作为 depth quality enhancement。\n3. 用 SuGaR 对单物体/小场景做高级 visual mesh benchmark。\n\n## SceneVerse++ 的位置\n\nSceneVerse++ 不做 3DGS-to-mesh。它更像结构化 3D scene understanding / data generation 框架，使用已有 mesh/point cloud/metadata，服务 SpatialLM、PQ3D、VQA、VLN 等任务。\n\nVideo2Mesh 可借：\n\n- `mesh.ply`、`camera_info.json`、`metadata.json`、`data_info.json` 等数据组织。\n- PQ3D / SpatialLM 对 object/layout understanding 的评估思路。\n- scene graph、object relation、language supervision 的数据结构。\n\n不能指望它替代：\n\n- 从视频重建 3DGS。\n- 从 3DGS 自动生成 mesh。\n- simulator collider / physics bundle。\n\n## image-blaster 的位置\n\nimage-blaster 主要提供：\n\n- object crop / reference image 到 generated mesh 的资产约定。\n- `worlds/<world>/output/<object>/` 目录结构。\n- browser viewer 和 local asset loading 思路。\n- 可接 Hunyuan3D / Meshy / FAL / InstantMesh 等后端。\n\nVideo2Mesh 应把它当作 object visual mesh completion helper。simulator bundle、physics、collider 和 adapter 仍由 Video2Mesh 负责。\n\n## SimAnything / PhysSplat 的位置\n\nSimAnything / PhysSplat 关注的是：\n\n```text\nstatic 3DGS\n  -> movable object discovery\n  -> physics property inference\n  -> Gaussian / particle dynamics\n  -> dynamic splat rendering\n```\n\n它不是 mesh 补全方法，也不能替代 Unity/MuJoCo collider。最值得借的是：\n\n- MLLM/VLM 估计物理属性草稿。\n- semantic Gaussian 到 physical object 的转换层。\n- dynamic Gaussian object 与 static background collider 的分层。\n\n短期落地应该先做 `mllm_physics` provider，自动生成质量、材质、摩擦、刚体/软体候选，再进 `simulator-physics-quality-report`。\n\n## 路线图\n\n### P0：稳定可展示闭环\n\n- COLMAP + GraphDECO 3DGS。\n- SAM2 mask tracking。\n- full point cloud 2D-to-3D mask fusion。\n- semantic / viewer PLY。\n- simulator bundle + Unity/MuJoCo adapter。\n- review pack 和 QA。\n\n### P1：让资产可交互\n\n- scene-level static collider。\n- object visual mesh 从 3DGS rendered depth/mask 做 TSDF。\n- collider proxy：box、convex hull、compound primitive。\n- object label、support plane、affordance sidecar。\n- external object completion backend。\n\n### P2：高质量 mesh 和动态仿真\n\n- GS2Mesh-style stereo depth fusion。\n- SuGaR / 2DGS / GOF benchmark。\n- MLLM physics annotation。\n- dynamic Gaussian assets for deformable/particle objects。\n- scene graph integration with SpatialLM/PQ3D-style outputs。\n\n### P3：产品化\n\n- scan QA and capture guidance。\n- scale calibration workflow。\n- texture baking and material estimation。\n- game-scene bundle。\n- deterministic validation and regression demos。\n",
      "headings": [
        {
          "level": "2",
          "text": "总结判断",
          "slug": "总结判断"
        },
        {
          "level": "2",
          "text": "方法横评",
          "slug": "方法横评"
        },
        {
          "level": "2",
          "text": "学术路线",
          "slug": "学术路线"
        },
        {
          "level": "3",
          "text": "位姿与重建",
          "slug": "位姿与重建"
        },
        {
          "level": "3",
          "text": "3DGS",
          "slug": "3dgs"
        },
        {
          "level": "3",
          "text": "语义与 scene graph",
          "slug": "语义与-scene-graph"
        },
        {
          "level": "2",
          "text": "业界路线",
          "slug": "业界路线"
        },
        {
          "level": "2",
          "text": "SuGaR 与 GS2Mesh",
          "slug": "sugar-与-gs2mesh"
        },
        {
          "level": "2",
          "text": "SceneVerse++ 的位置",
          "slug": "sceneverse-的位置"
        },
        {
          "level": "2",
          "text": "image-blaster 的位置",
          "slug": "image-blaster-的位置"
        },
        {
          "level": "2",
          "text": "SimAnything / PhysSplat 的位置",
          "slug": "simanything-physsplat-的位置"
        },
        {
          "level": "2",
          "text": "路线图",
          "slug": "路线图"
        },
        {
          "level": "3",
          "text": "P0：稳定可展示闭环",
          "slug": "p0稳定可展示闭环"
        },
        {
          "level": "3",
          "text": "P1：让资产可交互",
          "slug": "p1让资产可交互"
        },
        {
          "level": "3",
          "text": "P2：高质量 mesh 和动态仿真",
          "slug": "p2高质量-mesh-和动态仿真"
        },
        {
          "level": "3",
          "text": "P3：产品化",
          "slug": "p3产品化"
        }
      ],
      "reading_minutes": 2
    },
    {
      "id": "04-mesh-interaction-and-completion",
      "title": "Mesh、交互与遮挡补全",
      "category": "Simulation",
      "summary": "从 3DGS 到可交互场景的资产分层、mesh 重建、collider、遮挡补全、语义和 SimAnything 动态线。",
      "source_path": "docs/04-mesh-interaction-and-completion.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Mesh",
        "Collider",
        "Completion",
        "SimAnything",
        "Simulation"
      ],
      "body": "\n# Mesh、交互与遮挡补全\n\n## 核心结论\n\n3DGS 不能直接承担碰撞和交互。3DGS 本质是离散高斯椭球体集合，没有 mesh topology，也不能直接生成可靠 collider。\n\n可交互场景应该这样分层：\n\n```text\n3DGS visual layer\n  + visual mesh / completed mesh\n  + simplified collision proxy\n  + semantic / scene graph sidecar\n  + physics material and body metadata\n  + engine adapter\n```\n\n视觉要“像”，物理要“稳”，语义要“可查询”。三者不要混成一个资产。\n\n## Scene collider\n\n静态场景的第一版 collider 可以用：\n\n```text\nCOLMAP dense / fused point cloud\n  -> Poisson reconstruction\n  -> simplification\n  -> scene_collision.glb\n```\n\n这和 Azureovo 报告中的 CloudCompare PoissonRecon 路线一致，适合快速补上 Web/Unity 的碰撞闭环。\n\n注意：\n\n- Poisson 会补洞，作为 collider 可以接受，作为 visual mesh 要谨慎。\n- scene-level static collider 可以是 concave mesh。\n- dynamic object 不应该直接用复杂 concave mesh collider。\n\n## Object visual mesh\n\n生产路线：\n\n```text\ntrained GraphDECO 3DGS\n  + object masks\n  + registered camera poses\n  -> render object-centric RGB/depth/normal/mask\n  -> masked TSDF fusion\n  -> marching cubes / Poisson\n  -> cleanup / hole fill / simplify\n  -> visual mesh\n```\n\n这比直接从 sparse object mask cloud 三角化稳定，因为 3DGS 可以提供多视角、可筛选的 rendered evidence。\n\n如果 depth 不稳定，可以接 GS2Mesh-style stereo depth：先渲染 stereo views，再用 stereo model 估深，最后 TSDF fusion。\n\n## SuGaR、GS2Mesh 和其他 mesh 路线\n\n| 方法 | 输入 | 输出 | 适合 |\n|---|---|---|---|\n| COLMAP/CloudCompare Poisson | dense point cloud | scene mesh | P0 scene collider |\n| Open3D Poisson/BPA/alpha | point cloud + normals | baseline mesh | debug / automated baseline |\n| TSDF fusion | posed depth maps / 3DGS rendered depth | smooth object mesh | P1 object visual mesh |\n| GS2Mesh | 3DGS rendered stereo views | TSDF fused mesh | in-the-wild 3DGS-to-mesh enhancement |\n| SuGaR | trained 3DGS | editable mesh + refined GS | P2 visual mesh backend |\n| 2DGS / GOF | surface-aware Gaussian optimization | high-quality surface | P2/P3 research backend |\n| NeuS / VolSDF | posed images | neural SDF mesh | high-quality offline asset |\n\n![SuGaR pipeline and editing result](https://anttwo.github.io/sugar/results/full_teaser.png \"SuGaR 官方项目页图：pipeline 与编辑/合成效果，说明 extracted mesh 可以承接编辑，最终仍可用 Gaussian splatting 渲染\")\n\n![Surface-aligned Gaussian arrangement](https://anttwo.github.io/sugar/results/gaussian_arrangement.png \"SuGaR 官方项目页图：surface-aligned regularization 让 Gaussians 沿真实表面排列，后续再做 mesh extraction\")\n\n推荐顺序：\n\n1. P0：scene collider 用 dense point cloud + Poisson。\n2. P1：object visual mesh 用 3DGS rendered depth/mask + TSDF。\n3. P1：dynamic object collider 用 primitive / convex decomposition。\n4. P2：GS2Mesh-style depth enhancement。\n5. P2：SuGaR 单物体 benchmark。\n\n## Collider 策略\n\n| 对象 | 推荐 collider |\n|---|---|\n| 地面/墙体/大场景 | simplified static MeshCollider |\n| 桌椅柜等静态家具 | box / convex hull / compound primitive |\n| 动态可移动物体 | primitive / convex decomposition |\n| 楼梯/斜坡 | ramp proxy + navmesh |\n| 视觉细节复杂物体 | visual mesh 和 physics mesh 分离 |\n\n物体 visual mesh 出来后：\n\n```text\nobject_mesh.glb\n  -> CoACD / V-HACD / primitive fitting\n  -> object_collider_compound.glb\n  -> export-simulator-assets\n```\n\nUnity 中 concave MeshCollider 通常更适合 static/kinematic 场景。动态刚体应优先使用 convex 或 compound colliders。\n\n## 遮挡补全\n\n桌子、椅子这类对象要交互时，遮挡补全要拆成三件事：\n\n```text\nobject visual completion\nbackground clean plate\nphysics proxy completion\n```\n\n### Object visual completion\n\n如果物体部分被挡住，但需要完整视觉 mesh，可以从 object crops / selected frames 生成完整模型：\n\n- Hunyuan3D。\n- Meshy。\n- TRELLIS。\n- InstantMesh。\n- image-blaster external mesh jobs。\n\n生成 mesh 后必须对齐回原场景：\n\n```text\ngenerated object-local mesh\n  -> fit to observed 3D bbox\n  -> align support plane\n  -> record completion source and confidence\n```\n\n### Background completion\n\n如果用户移动桌椅，原来被挡住的地面/墙面会露出来。这时需要 clean plate：\n\n```text\nvideo frames + object masks\n  -> remove object from frames\n  -> 2D image/video inpainting\n  -> rebuild / update background 3DGS or background mesh\n```\n\n背景补全和物体补全要分开。物体生成得再完整，也不能自动恢复它背后的地板。\n\n### Physics proxy completion\n\n交互不需要真实还原每个不可见三角面。它需要稳定、合理、保守的物理代理：\n\n- table：桌面 box + 桌腿 box/capsule。\n- chair：坐垫 box + 靠背 box + 椅腿 + 扶手可选。\n- cabinet：box / convex hull。\n- plant：粗略 pot collider + visual mesh。\n\n这比拿生成式 visual mesh 直接做碰撞更稳。\n\n## 语义兼容\n\n语义不要塞死在 collider 里。推荐 sidecar：\n\n```json\n{\n  \"mesh\": \"objects/chair_01.glb\",\n  \"face_semantics\": [\n    {\"face\": 1024, \"object_id\": \"chair_01\", \"label\": \"chair\", \"probability\": 0.91}\n  ],\n  \"support_surfaces\": [\n    {\"type\": \"seat\", \"normal\": [0, 1, 0], \"height\": 0.45}\n  ]\n}\n```\n\n常用策略：\n\n- semantic splats / point cloud 作为主语义数据。\n- mesh face center 用 KDTree 或 ray projection 回灌语义。\n- collider 或 trigger 只保存可交互需要的语义字段。\n\n## SimAnything / PhysSplat 动态线\n\nSimAnything / PhysSplat 的价值不是 mesh 补全，而是把语义 Gaussian 对象变成可动态仿真的对象：\n\n```text\nsemantic Gaussian object\n  -> physics property inference\n  -> particle / Gaussian state\n  -> simulation\n  -> dynamic splat rendering\n```\n\n适合：\n\n- cloth。\n- pillow。\n- blanket。\n- plant leaf。\n- liquid / granular / soft object。\n- 局部受力形变展示。\n\n不适合替代：\n\n- object visual mesh。\n- Unity/MuJoCo collider。\n- scale/physics QA。\n\n推荐新增旁路线：\n\n```text\nsimulator_assets/dynamic_gaussian_assets/\n  scene_dynamic_config.json\n  objects/<object_id>/gaussians.ply\n  objects/<object_id>/physics.json\n  objects/<object_id>/constraints.json\n  simulations/<sim_id>/trajectory.npz\n```\n\n短期最实用的是先接 MLLM/VLM 物理属性草稿：\n\n```text\nobject crop + mask + label + bbox + support plane\n  -> mllm_physics provider\n  -> mass / material / friction / restitution / rigid/deformable\n  -> import-simulator-physics\n  -> simulator-physics-quality-report\n```\n\n## 推荐落地方案\n\n第一版可交互：\n\n1. 3DGS 继续做 visual scene。\n2. scene collider 用 dense point cloud + Poisson + simplify。\n3. object mesh 用 3DGS rendered depth/mask + TSDF。\n4. 遮挡严重的常见家具用 generated visual mesh 补全。\n5. physics collider 用 bbox/primitive/convex decomposition。\n6. semantic / scene graph / physics 用 sidecar 记录。\n7. Unity/MuJoCo/Isaac 只消费稳定合同，不直接依赖 3DGS 高斯几何。\n\n这条路线和 Icare / World Labs / Azureovo 报告的共识一致：3DGS 做视觉层，传统 mesh/physics/controller 做交互层。\n",
      "headings": [
        {
          "level": "2",
          "text": "核心结论",
          "slug": "核心结论"
        },
        {
          "level": "2",
          "text": "Scene collider",
          "slug": "scene-collider"
        },
        {
          "level": "2",
          "text": "Object visual mesh",
          "slug": "object-visual-mesh"
        },
        {
          "level": "2",
          "text": "SuGaR、GS2Mesh 和其他 mesh 路线",
          "slug": "sugargs2mesh-和其他-mesh-路线"
        },
        {
          "level": "2",
          "text": "Collider 策略",
          "slug": "collider-策略"
        },
        {
          "level": "2",
          "text": "遮挡补全",
          "slug": "遮挡补全"
        },
        {
          "level": "3",
          "text": "Object visual completion",
          "slug": "object-visual-completion"
        },
        {
          "level": "3",
          "text": "Background completion",
          "slug": "background-completion"
        },
        {
          "level": "3",
          "text": "Physics proxy completion",
          "slug": "physics-proxy-completion"
        },
        {
          "level": "2",
          "text": "语义兼容",
          "slug": "语义兼容"
        },
        {
          "level": "2",
          "text": "SimAnything / PhysSplat 动态线",
          "slug": "simanything-physsplat-动态线"
        },
        {
          "level": "2",
          "text": "推荐落地方案",
          "slug": "推荐落地方案"
        }
      ],
      "reading_minutes": 2
    },
    {
      "id": "05-operations-and-showcase",
      "title": "运行、展示与排错",
      "category": "Operations",
      "summary": "远端环境、展示产物、历史 run、QA 命令和常见失败处理。",
      "source_path": "docs/05-operations-and-showcase.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Runbook",
        "Showcase",
        "QA",
        "Operations"
      ],
      "body": "\n# 运行、展示与排错\n\n## 远端环境\n\n常用路径：\n\n```text\nVideo2Mesh: /root/autodl-tmp/workspace/Video2Mesh\ndataset: /root/autodl-tmp/workspace/Video2Mesh/dataset\nexports: /root/autodl-tmp/workspace/Video2Mesh/exports\nGraphDECO: /root/autodl-tmp/workspace/gaussian-splatting\nSAM2: /root/autodl-tmp/workspace/sam2\nmain venv: /root/autodl-tmp/venvs/v2m-svpp\nSAM2 venv: /root/autodl-tmp/workspace/venvs/v2m-sam2-clean\n```\n\n登录后：\n\n```bash\ncd /root/autodl-tmp/workspace/Video2Mesh\nsource /etc/network_turbo >/dev/null 2>&1 || true\n```\n\n不推荐默认用 conda base 跑完整流程；历史上 base 的 OpenCV/NumPy/SciPy 组合出现过问题。\n\n## 权重和依赖\n\n常用权重：\n\n```text\n/root/autodl-tmp/checkpoints/sam/sam_vit_b_01ec64.pth\n/root/autodl-tmp/workspace/sam2/checkpoints/sam2.1_hiera_tiny.pt\n/root/autodl-tmp/workspace/MASt3R-SLAM/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth\n```\n\nGraphDECO 运行时需要 torch shared library 在 `LD_LIBRARY_PATH` 中。`tools/run_video2mesh_quick.sh` 和 `tools/run_graphdeco_3dgs.sh` 已处理。\n\n## 监控命令\n\n进程：\n\n```bash\nps -eo pid,ppid,pgid,etime,stat,pcpu,pmem,cmd | \\\n  grep -E \"run_video2mesh_quick|MASt3R-SLAM|mast3r|graphdeco|train.py\" | \\\n  grep -v grep\n```\n\nGPU：\n\n```bash\nnvidia-smi\n```\n\n关键输出：\n\n```bash\nfind exports/<run>/scene -maxdepth 4 \\\n  \\( -name camera_info.json -o -name point_cloud.ply \\) -ls\n```\n\n日志：\n\n```bash\ntail -80 exports/<run>/logs/mast3r_slam_run.log\ntail -80 exports/<run>/logs/graphdeco_train.log\n```\n\n## 展示产物\n\n| 展示目标 | 文件 |\n|---|---|\n| 总览网页 | `simulator_assets/review/index.html` |\n| 场景 SuperSplat | `simulator_assets/viewer_plys/scene_3dgs_supersplat.ply` |\n| 普通点云 | `simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply` |\n| 语义 SuperSplat | `simulator_assets/viewer_plys/semantic_3dgs_supersplat.ply` |\n| Gaussian probability | `simulator_assets/semantic_gaussian_probability_supersplat.ply` |\n| 3D object masks | `simulator_assets/object_masks_3d/*.ply` |\n| object selected frames | `objects/<object_id>/selected_frames/` |\n| object crops | `objects/<object_id>/object_images/` |\n| object meshes | `simulator_assets/reconstructed_meshes/` 或 `simulator_assets/3dgs_object_meshes/` |\n| simulator bundle | `simulator_assets/simulator_asset_bundle.json` |\n| MuJoCo adapter | `simulator_assets/adapters/mujoco/scene.xml` |\n| Unity adapter | `simulator_assets/adapters/unity/unity_adapter.json` |\n| evaluation | `simulator_assets/evaluation_report.json` |\n| showcase verification | `simulator_assets/showcase_pack_verification.json` |\n| production readiness | `simulator_assets/production_readiness_report.json` |\n\n刷新展示检查：\n\n```bash\nbash tools/audit_showcase_artifacts.sh exports/<run>\n```\n\n推荐展示顺序：\n\n1. 打开 `review/index.html` 讲完整链路。\n2. 用 SuperSplat 打开 `scene_3dgs_supersplat.ply`。\n3. 展示 semantic splat / probability splat。\n4. 展示 3D masks 和 object selected frames。\n5. 展示 object mesh 和 simulator bundle。\n6. 最后展示 QA，明确 demo-ready 和 production gap。\n\n## 历史 run 定位\n\n`milscene3_full_20260618_124804`：\n\n- 已完成端到端 baseline。\n- 证明 `video -> 3DGS -> 3D semantic masks -> object frames -> mesh -> simulator assets` 闭合。\n- active 3DGS 是历史 minimal gsplat full-cloud baseline，不是当前 GraphDECO 默认。\n\n`milscene2_hq_20260618_065920`：\n\n- 更早的真实视频 baseline。\n- 可展示系统闭环，但不代表当前最高质量。\n\n新实验默认应看 GraphDECO quick pipeline 输出。\n\n## 常见失败\n\n### 重建只有单 pose 或空点云\n\n症状：\n\n```text\nframes=1 poses=1 points=0\nNo points found in point cloud\n```\n\n处理：\n\n- 不进入 GraphDECO。\n- 换真实时间窗。\n- 裁剪更稳定、更有视差的 10 秒片段。\n- 不用插值帧填补。\n\nOpenCV 裁剪：\n\n```bash\npython tools/crop_best_video_window.py dataset/<video>.mp4 \\\n  --duration 10 \\\n  --output dataset/<video>_best10.mp4 \\\n  --force\n```\n\n### MASt3R 或重建耗时过长\n\n规则：\n\n- 长视频小于 1.5 小时且 GPU/CPU 有负载时继续观察。\n- 超过 1.5 小时无 `camera_info.json` 和有效 `point_cloud.ply`，中断。\n- 先裁剪前 60 秒。\n- 若 60 秒仍失败，再裁剪更稳定的 10 秒。\n\n### 物体 mesh 破碎\n\n这是 object mask cloud baseline 的预期问题，不是最终路线。处理：\n\n- 不把 baseline OBJ 当最终展示 mesh。\n- 使用 `export-3dgs-mesh-observations` + `reconstruct-3dgs-object-meshes`。\n- 遮挡严重时接 external generated mesh，再 fit to bbox。\n- collider 走 primitive / convex proxy。\n\n### 物理字段缺失\n\n处理：\n\n```bash\npython -m video2mesh.cli prepare-simulator-physics-jobs \\\n  --project-root exports/<run>\n\npython -m video2mesh.cli import-simulator-physics \\\n  --project-root exports/<run> \\\n  --physics exports/<run>/simulator_assets/physics_properties.json\n\npython -m video2mesh.cli simulator-physics-quality-report \\\n  --project-root exports/<run>\n```\n\nMLLM/VLM 可作为物理属性草稿来源，但必须进 QA。\n\n## 展示口径\n\n可以说：\n\n- 系统已经跑通从真实视频到 3DGS、语义 mask、object assets、simulator bundle 的闭环。\n- 当前 baseline mesh 用于验证尺度和接口，不是最终 visual mesh。\n- 生产 mesh 主线是 3DGS rendered depth/mask + TSDF/Poisson。\n- 交互层依赖 collider/proxy/physics sidecar，不依赖原始 3DGS 几何。\n\n不要说：\n\n- 已经能从任意视频稳定生成生产级 mesh。\n- 3DGS 本身可以直接碰撞。\n- SimAnything 可以替代 mesh/collider。\n- generated mesh 可以不经对齐和 QA 直接进仿真。\n",
      "headings": [
        {
          "level": "2",
          "text": "远端环境",
          "slug": "远端环境"
        },
        {
          "level": "2",
          "text": "权重和依赖",
          "slug": "权重和依赖"
        },
        {
          "level": "2",
          "text": "监控命令",
          "slug": "监控命令"
        },
        {
          "level": "2",
          "text": "展示产物",
          "slug": "展示产物"
        },
        {
          "level": "2",
          "text": "历史 run 定位",
          "slug": "历史-run-定位"
        },
        {
          "level": "2",
          "text": "常见失败",
          "slug": "常见失败"
        },
        {
          "level": "3",
          "text": "重建只有单 pose 或空点云",
          "slug": "重建只有单-pose-或空点云"
        },
        {
          "level": "3",
          "text": "MASt3R 或重建耗时过长",
          "slug": "mast3r-或重建耗时过长"
        },
        {
          "level": "3",
          "text": "物体 mesh 破碎",
          "slug": "物体-mesh-破碎"
        },
        {
          "level": "3",
          "text": "物理字段缺失",
          "slug": "物理字段缺失"
        },
        {
          "level": "2",
          "text": "展示口径",
          "slug": "展示口径"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "06-site-and-remote-control",
      "title": "relumeow.top 文档站与远程控制",
      "category": "Site",
      "summary": "Markdown 文档站的构建、内容收录、登录、API 和安全边界。",
      "source_path": "docs/06-site-and-remote-control.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "relumeow.top",
        "Docs Site",
        "API",
        "Site"
      ],
      "body": "\n# relumeow.top 文档站与远程控制\n\n## 文档站定位\n\n`docs-blog/` 是 relumeow.top 的静态文档站和本机 API 管理界面。当前项目主文档来自：\n\n```text\nREADME.md\ndocs/*.md\ndocs-blog/content/*.md\n```\n\n项目长期主文档应放在 `docs/`。`docs-blog/content/` 只保留网站或临时内容，不再放项目主报告。\n\n## 构建网站\n\n在仓库根目录运行：\n\n```bash\npython3 docs-blog/build_site.py\n```\n\n输出：\n\n```text\ndocs-blog/site-data.js\ndocs-blog/_public/\ndocs-blog/CNAME\n```\n\n`docs-blog/_public/` 是静态发布目录，已被 Git 忽略。\n\n## 新增文档\n\n1. 把项目主文档放到 `docs/`。\n2. 在文件顶部加 front matter：\n\n```markdown\n---\ntitle: 文档标题\ncategory: Research\nsummary: 一句话摘要。\ntags:\n  - 3DGS\n  - Mesh\n---\n```\n\n3. 运行：\n\n```bash\npython3 docs-blog/build_site.py\n```\n\n4. 打开 `docs-blog/index.html` 本地检查。\n\n## Markdown 支持\n\n文档站支持：\n\n- 标题。\n- 表格。\n- 代码块。\n- 本地图片。\n- 网络图片。\n- task list。\n- 折叠块。\n- Obsidian 风格内部链接。\n\n本地图片建议放在文档旁边或 `docs-blog/content/assets/`。构建脚本会复制可解析的本地图片。\n\n网络图片可以直接写在 Markdown 里：\n\n```markdown\n![SuGaR pipeline](https://anttwo.github.io/sugar/results/full_teaser.png \"图注文字\")\n```\n\n图片单独占一行时，页面会渲染成带图注和来源域名的 figure。外链图片会保留原图链接，点击可打开来源。\n\n## 本机 API\n\n默认 API URL：\n\n```text\nhttps://api.relumeow.top\n```\n\n本地开发时可运行：\n\n```bash\npython3 docs-blog/api_server.py\n```\n\n管理界面在：\n\n```text\ndocs-blog/admin/index.html\n```\n\nAPI 负责：\n\n- 用户登录和 session。\n- 管理员创建。\n- GitHub OAuth 登录。\n- 在线编辑和同步 Markdown。\n- 多项目记录。\n- Codex 任务队列。\n- 工作区文件浏览。\n- 管理员终端。\n\n## 安全边界\n\n远程控制功能必须保持以下边界：\n\n- 管理员功能需要登录。\n- workspace terminal 只能对可信用户开放。\n- runtime secrets 不进 Git。\n- `.env`、`docs-blog/runtime/`、密钥文件已被 `.gitignore` 排除。\n- 网站静态发布目录不应包含 runtime state。\n\n## Codex 同步文档\n\n推荐流程：\n\n```text\nedit docs/*.md\n  -> python3 docs-blog/build_site.py\n  -> inspect docs-blog/site-data.js / index.html\n  -> deploy static site\n```\n\n不要直接手写 `site-data.js`。它是构建产物。\n",
      "headings": [
        {
          "level": "2",
          "text": "文档站定位",
          "slug": "文档站定位"
        },
        {
          "level": "2",
          "text": "构建网站",
          "slug": "构建网站"
        },
        {
          "level": "2",
          "text": "新增文档",
          "slug": "新增文档"
        },
        {
          "level": "2",
          "text": "Markdown 支持",
          "slug": "markdown-支持"
        },
        {
          "level": "2",
          "text": "本机 API",
          "slug": "本机-api"
        },
        {
          "level": "2",
          "text": "安全边界",
          "slug": "安全边界"
        },
        {
          "level": "2",
          "text": "Codex 同步文档",
          "slug": "codex-同步文档"
        }
      ],
      "reading_minutes": 1
    }
  ],
  "categories": [
    "Operations",
    "Overview",
    "Pipeline",
    "Research",
    "Simulation",
    "Site"
  ]
};
