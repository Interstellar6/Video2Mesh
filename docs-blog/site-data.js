window.V2M_BLOG_DATA = {
  "generatedAt": "2026-07-03 17:43",
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
      "updated": "2026-07-02",
      "tags": [
        "Video2Mesh",
        "Docs",
        "Overview"
      ],
      "body": "\n# Video2Mesh 文档中心\n\n这个目录是 Video2Mesh 的精简文档入口。旧的根目录长报告已经合并到这里，不再作为主文档维护。\n\n## 文档结构\n\n| 文档 | 读者问题 | 内容 |\n|---|---|---|\n| [01-project-overview.md](01-project-overview.md) | 这个项目到底做什么？ | 项目目标、资产分层、当前边界、参考项目角色 |\n| [02-pipeline-and-commands.md](02-pipeline-and-commands.md) | 怎么跑？产物在哪里？ | 端到端流水线、远端命令、关键输出、QA |\n| [07-pipeline-route-matrix.md](07-pipeline-route-matrix.md) | 每个流程阶段该选哪条路线？ | 当前选型、备选方法、适用场景和风险对比 |\n| [03-research-roadmap.md](03-research-roadmap.md) | 学术和业界路线怎么选？ | 场景扫描、3DGS、mesh、Scene Graph、方法优先级 |\n| [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) | 怎么让场景可交互？遮挡怎么补？ | 3DGS-to-mesh、collider、补全、语义、SimAnything 动态线 |\n| [08-web-visual-physics-demo.md](08-web-visual-physics-demo.md) | Web 端能不能先演示视逻分离？ | 视觉代理 3DGS + 碰撞代理 mesh 的静态 Web demo |\n| [05-operations-and-showcase.md](05-operations-and-showcase.md) | 展示和排错怎么做？ | 远端环境、历史 run、展示清单、常见失败处理 |\n| [06-site-and-remote-control.md](06-site-and-remote-control.md) | relumeow.top 怎么更新？ | Markdown 网站、API、登录、远程控制边界 |\n\n## 当前结论\n\nVideo2Mesh 的核心路线不是“从视频直接生成一个完美 mesh”，而是把真实扫描视频拆成多层资产：\n\n```text\nvideo\n  -> COLMAP / learned pose fallback\n  -> GraphDECO 3DGS visual scene\n  -> 2D/3D object masks\n  -> semantic / probability splats\n  -> object visual mesh\n  -> collider / physics proxy\n  -> simulator adapters and review pack\n```\n\n最重要的工程判断：\n\n- 3DGS 负责高质量视觉层，不直接负责碰撞。\n- mesh/collider 是物理和交互代理，不要求和视觉 3DGS 一样精细。\n- semantic layer 独立保存，必要时投到 mesh face、collider 或 trigger。\n- 遮挡补全要分成 object visual completion、background clean plate、physics proxy completion 三件事。\n- SimAnything / PhysSplat 应作为 dynamic Gaussian 和物理属性增强线，不替代 mesh/collider 主链路。\n\n## 优先级\n\n| 优先级 | 目标 | 当前推荐 |\n|---|---|---|\n| P0 | 跑通可展示闭环 | COLMAP + GraphDECO + SAM2 + 3D masks + simulator bundle |\n| P0 | 场景级碰撞 | dense point cloud / Poisson / simplified static collider |\n| P1 | 物体 visual mesh | 3DGS rendered RGB/depth/normal/mask -> TSDF / Poisson |\n| P1 | 动态物体 collider | primitive compound / convex hull / CoACD or V-HACD |\n| P1 | 遮挡补全 | Hunyuan3D / Meshy / TRELLIS / image-blaster 生成完整视觉 mesh，再按 bbox 对齐 |\n| P2 | 高质量 3DGS-to-mesh | GS2Mesh-style stereo depth fusion、SuGaR、2DGS、GOF |\n| P2 | 动态 Gaussian | SimAnything / PhysSplat-style semantic Gaussian -> physics object |\n\n## 旧文档合并说明\n\n| 旧主题 | 新位置 |\n|---|---|\n| `Video2Mesh_PROJECT_README.md`、`README.md` | [01-project-overview.md](01-project-overview.md) |\n| `VIDEO2MESH_PIPELINE.md`、`SVLGaussian_frame_matching_notes.md` | [02-pipeline-and-commands.md](02-pipeline-and-commands.md) |\n| `SCENE_SCANNING_SOLUTIONS_SURVEY.md`、`FEED_FORWARD_GAUSSIAN_SCENE_GRAPH_SURVEY.md` | [03-research-roadmap.md](03-research-roadmap.md) |\n| `MESH_RECONSTRUCTION_METHODS_SURVEY.md`、`INTERACTIVE_GAME_SCENE_FROM_3DGS_SURVEY.md`、`SIM_ANYTHING_PHYS_SPLAT_SURVEY.md` | [04-mesh-interaction-and-completion.md](04-mesh-interaction-and-completion.md) |\n| `REMOTE_SETUP_STATUS.md`、`Video2Mesh_real_demo_runbook.md`、`Video2Mesh_milscene*.md` | [05-operations-and-showcase.md](05-operations-and-showcase.md) |\n| `docs-blog/content/*.md` | [06-site-and-remote-control.md](06-site-and-remote-control.md) |\n",
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
      "id": "07-pipeline-route-matrix",
      "title": "流水线阶段路线矩阵",
      "category": "Pipeline",
      "summary": "按 Video2Mesh 流程逐阶段说明当前采用路线、备选路线、适用条件和风险，便于开会讨论和后续替换模块。",
      "source_path": "docs/07-pipeline-route-matrix.md",
      "source_kind": "builtin",
      "updated": "2026-07-01",
      "tags": [
        "Pipeline",
        "Route Matrix",
        "Segmentation",
        "Mesh"
      ],
      "body": "\n# 流水线阶段路线矩阵\n\n这篇文档按流程组织，每一阶段都回答四个问题：\n\n- 当前选定路线是什么。\n- 为什么先选它。\n- 还有哪些可替代路线。\n- 什么时候应该切换或并行评估。\n\n## 总览\n\n```text\nvideo\n  -> frame selection / scan QA\n  -> camera pose and point cloud\n  -> 3DGS visual scene\n  -> object discovery and semantic segmentation\n  -> 2D-to-3D semantic fusion\n  -> object mesh and completion\n  -> collider / physics / scene graph\n  -> simulator adapters and QA\n```\n\n| 阶段 | 当前主路线 | 近期备选 | 判断标准 |\n|---|---|---|---|\n| 视频抽帧 | 真实帧均匀采样 + 时间窗 | smart keyframing / coverage QA | COLMAP 注册率、模糊、视差 |\n| 位姿/点云 | COLMAP | MASt3R / DUSt3R / VGGT / MegaSaM | COLMAP 失败或弱纹理场景 |\n| 视觉场景 | GraphDECO 3DGS | 2DGS / SuGaR refined GS / Spark runtime | 画质、训练时间、几何可用性 |\n| 语义分割 | SAM prompt + SAM2 tracking | Grounded-SAM2、YOLO-World+SAM、DEVA/XMem | mask 稳定性、类别覆盖、跨帧一致性 |\n| 3D 语义融合 | 点云投影投票 + probability | SVLGaussian-style ray-to-Gaussian、graph refinement | object mask 干净度、可解释性 |\n| object mesh | 3DGS rendered depth/mask + TSDF | GS2Mesh-style、SuGaR、generated mesh | 可见覆盖、遮挡程度、是否要编辑 |\n| collider | static mesh + object proxy | CoACD / V-HACD / primitive fitting | 是否动态、是否进 Unity/MuJoCo |\n| 物理属性 | 模板 + QA + 人工/外部导入 | MLLM physics draft / SimAnything-style | 是否需要可交互仿真 |\n| scene graph | sidecar JSON | SpatialLM / PQ3D / VLM relation extraction | 是否需要任务、导航、交互逻辑 |\n\n## 1. 视频抽帧与扫描质量\n\n### 当前路线\n\n真实 decoded frames + `MAX_FRAMES` 上限内均匀采样。指定时间窗时也只从真实帧中抽，不插值。\n\n### 为什么先选\n\n- 简单、稳定、可复现。\n- 不引入合成帧造成的相机/几何假信号。\n- 与 COLMAP / 3DGS 训练输入一致。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| smart keyframing | 提升视差覆盖，减少冗余帧 | 需要质量评分和调参 | 长视频、移动轨迹复杂 |\n| blur / exposure QA | 提前过滤坏帧 | 可能丢掉少数关键视角 | 手机扫描、运动模糊明显 |\n| coverage heatmap | 能提示补拍区域 | 需要已估 pose 或粗重建 | 产品化采集指导 |\n\n## 2. 位姿与点云\n\n### 当前路线\n\nCOLMAP 作为默认 SfM/MVS baseline，输出 `camera_info.json` 和 full `point_cloud.ply`。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| MASt3R / DUSt3R | 弱纹理或 COLMAP 失败时可兜底 | 尺度、全局一致性和工程依赖更复杂 | 短视频、低纹理、注册失败 |\n| VGGT / VGGT-Omega | 前馈几何能力强，适合未来统一底座 | 方法和代码成熟度需评估 | 中长期替换或辅助 COLMAP |\n| MegaSaM / learned depth | 提供 dense depth prior | 需要额外模型和标定处理 | TSDF mesh 或 GS2Mesh-style enhancement |\n\n### 切换条件\n\n当 readiness 出现注册帧过少、单 pose、空点云、覆盖率低时，优先换真实时间窗；仍失败再启用 learned fallback。\n\n## 3. 3DGS 视觉场景\n\n### 当前路线\n\nGraphDECO 3DGS 是默认训练路线，用 full COLMAP point cloud 初始化。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| 2DGS | surface 更稳，mesh 友好 | 替换训练后端成本高 | mesh 质量优先 |\n| SuGaR refined GS | 便于 editable mesh | 需要额外优化 | 单物体或小场景 benchmark |\n| Spark / SuperSplat runtime | Web 端运行成熟 | 主要是渲染 runtime，不解决重建 | 展示和交互 viewer |\n\n## 4. 语义分割与跟踪\n\n### 当前选定路线\n\n当前主线是：\n\n```text\nobject prompt discovery\n  -> SAM / SAM2 masks\n  -> SAM2 video tracking\n  -> mask QA\n```\n\n当前阶段更重视跨帧一致性和可投影性，而不是一次性得到完美类别名。类别和 affordance 可以后续用 VLM / open-vocabulary detector 补。\n\n### 为什么先选\n\n- SAM2 对视频 mask propagation 更适合我们的多帧融合。\n- 和 2D-to-3D projection voting 直接兼容。\n- mask 可以保留为可审计中间产物。\n- 出错时容易人工检查和替换。\n\n### 备选路线对比\n\n| 路线 | 做法 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|---|\n| SAM2 + 自动 prompts | 先发现候选框/点，再跟踪 | 当前最贴合 pipeline，跨帧一致性好 | 类别名弱，复杂家具会过分割 | 默认路线 |\n| Grounded-SAM2 | 文本检测框 + SAM2 mask | open-vocabulary 类别更清楚 | prompt 质量影响大，漏检小物体 | 需要“椅子/桌子/柜子”等明确类别 |\n| YOLO-World + SAM | open-vocabulary detector 给框，SAM 出 mask | 工程快，类别更稳定 | 框级误检会传给 SAM | 室内常见物体 |\n| OWL-ViT / OWLv2 + SAM | 文本-图像检测 + mask refinement | 类别灵活 | 速度和置信度需评估 | 自定义类别集合 |\n| DEVA / XMem | video object segmentation / tracking | 长视频跟踪强 | 初始化 mask 仍依赖上游 | SAM2 跟踪漂移时 |\n| Mask2Former / OneFormer | panoptic segmentation | 稳定类别和 stuff 区域 | 类别集合固定，开放性弱 | floor/wall/ceiling 背景结构 |\n| VLM 逐帧审查 | 用 GPT-4o/MLLM 过滤候选 | 可解释，能输出描述 | 成本高，不适合作每帧主干 | label / affordance / QA |\n\n### 推荐组合\n\n第一版保持：\n\n```text\nSAM2 tracking\n  + object mask QA\n  + VLM label refinement\n```\n\nP1 增强：\n\n```text\nGroundingDINO or YOLO-World\n  -> SAM2\n  -> track QA\n  -> VLM merge/split suggestions\n```\n\n背景结构单独处理：\n\n```text\nfloor / wall / ceiling\n  -> plane fitting + panoptic/stuff segmentation\n  -> layout sidecar\n```\n\n## 5. 2D 到 3D 语义融合\n\n### 当前路线\n\n把 3D 点投影到每个带 mask 的帧，使用可见性和 mask 命中统计做投票或 probability fusion。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| visibility-weighted vote | 可解释、易调试 | 对 pose/depth 敏感 | 默认 object masks |\n| SVLGaussian-style Gaussian probability | 直接把语义写到 Gaussian | 计算重，需过滤漂浮高斯 | semantic splats / viewer |\n| graph refinement | 用相邻点/高斯平滑语义 | 可能过度平滑边界 | mask 噪声较大 |\n| mesh face backprojection | 给 collider / mesh face 贴语义 | 依赖 mesh 质量 | trigger、navmesh、Unity 交互 |\n\n## 6. Object Mesh 与遮挡补全\n\n### 当前路线\n\n```text\n3DGS rendered RGB/depth/normal/mask\n  -> masked TSDF fusion\n  -> Poisson / marching cubes\n  -> cleanup and simplify\n```\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| GS2Mesh-style stereo depth | 不直接相信 Gaussian geometry | 需要 stereo model 和视角采样 | in-the-wild 3DGS mesh |\n| SuGaR | 3DGS-aware editable mesh | 额外优化，不适合 P0 collider | 高质量 visual mesh |\n| Hunyuan3D / Meshy / TRELLIS | 能补全遮挡物体 | 尺度和真实形状需对齐 QA | 桌椅柜等常见物体补全 |\n| OpenMVS / RealityCapture | 工业 mesh/texturing 强 | 依赖重或闭源 | 对照 benchmark |\n\n## 7. Collider 与物理代理\n\n### 当前路线\n\n- 场景级 static collider：dense point cloud / Poisson / simplified mesh。\n- 物体 collider：bbox、convex hull、compound primitive。\n- 动态物体：优先 primitive / convex decomposition。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| CloudCompare PoissonRecon | 快速稳定 | 自动化需封装 | scene collider baseline |\n| CoACD / V-HACD | 物理引擎友好 | 需要已有 mesh | dynamic rigid body |\n| 手工 primitive fitting | 稳定、轻量 | 视觉不精确 | 桌椅柜、箱体、平面 |\n| mesh collider | 几何贴合 | dynamic 限制多 | static environment |\n\n## 8. 物理属性与动态对象\n\n### 当前路线\n\n先用 template/manual/external import 补 `body_type`、`mass_kg`、`friction`、`restitution`，再跑 QA。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| MLLM physics draft | 自动给材料和质量初值 | 不能无 QA 直接相信 | 大量 object 初筛 |\n| SimAnything / PhysSplat | semantic Gaussian 动态仿真 | 不替代 mesh/collider | 软体、颗粒、局部动态展示 |\n| 真实测量 / 标定 | 最可信 | 成本高 | 关键 demo 或实验 |\n\n## 9. Scene Graph 与交互逻辑\n\n### 当前路线\n\n使用 sidecar JSON 记录 object id、类别、bbox、support、affordance、asset refs。\n\n### 备选路线\n\n| 路线 | 优点 | 风险 | 适用场景 |\n|---|---|---|---|\n| SpatialLM / PQ3D style | 结构化 3D 理解成熟 | 依赖数据格式和模型 | layout / object relation |\n| VLM relation extraction | 可解释、灵活 | 需要多视角证据 | support、on/near/inside |\n| rule-based geometry | 稳定、便宜 | 语义表达有限 | floor support、bbox relation |\n\n## 10. 推荐迭代顺序\n\n1. 保持 COLMAP + GraphDECO + SAM2 + projection fusion 主线稳定。\n2. 给语义分割加 GroundingDINO / YOLO-World 候选路线，但不要立刻替换 SAM2 tracking。\n3. object mesh 先加强 TSDF，再评估 GS2Mesh-style depth。\n4. 遮挡补全接 generated mesh，但必须 fit to bbox + support plane。\n5. collider 和 physics sidecar 独立于 visual mesh。\n6. 长期再加 SimAnything / PhysSplat dynamic Gaussian 旁路线。\n",
      "headings": [
        {
          "level": "2",
          "text": "总览",
          "slug": "总览"
        },
        {
          "level": "2",
          "text": "1. 视频抽帧与扫描质量",
          "slug": "1.-视频抽帧与扫描质量"
        },
        {
          "level": "3",
          "text": "当前路线",
          "slug": "当前路线"
        },
        {
          "level": "3",
          "text": "为什么先选",
          "slug": "为什么先选"
        },
        {
          "level": "3",
          "text": "备选路线",
          "slug": "备选路线"
        },
        {
          "level": "2",
          "text": "2. 位姿与点云",
          "slug": "2.-位姿与点云"
        },
        {
          "level": "3",
          "text": "当前路线",
          "slug": "当前路线"
        },
        {
          "level": "3",
          "text": "备选路线",
          "slug": "备选路线"
        },
        {
          "level": "3",
          "text": "切换条件",
          "slug": "切换条件"
        },
        {
          "level": "2",
          "text": "3. 3DGS 视觉场景",
          "slug": "3.-3dgs-视觉场景"
        },
        {
          "level": "3",
          "text": "当前路线",
          "slug": "当前路线"
        },
        {
          "level": "3",
          "text": "备选路线",
          "slug": "备选路线"
        },
        {
          "level": "2",
          "text": "4. 语义分割与跟踪",
          "slug": "4.-语义分割与跟踪"
        },
        {
          "level": "3",
          "text": "当前选定路线",
          "slug": "当前选定路线"
        },
        {
          "level": "3",
          "text": "为什么先选",
          "slug": "为什么先选"
        },
        {
          "level": "3",
          "text": "备选路线对比",
          "slug": "备选路线对比"
        },
        {
          "level": "3",
          "text": "推荐组合",
          "slug": "推荐组合"
        },
        {
          "level": "2",
          "text": "5. 2D 到 3D 语义融合",
          "slug": "5.-2d-到-3d-语义融合"
        },
        {
          "level": "3",
          "text": "当前路线",
          "slug": "当前路线"
        },
        {
          "level": "3",
          "text": "备选路线",
          "slug": "备选路线"
        },
        {
          "level": "2",
          "text": "6. Object Mesh 与遮挡补全",
          "slug": "6.-object-mesh-与遮挡补全"
        },
        {
          "level": "3",
          "text": "当前路线",
          "slug": "当前路线"
        },
        {
          "level": "3",
          "text": "备选路线",
          "slug": "备选路线"
        },
        {
          "level": "2",
          "text": "7. Collider 与物理代理",
          "slug": "7.-collider-与物理代理"
        }
      ],
      "reading_minutes": 2
    },
    {
      "id": "03-research-roadmap",
      "title": "技术调研与选型报告",
      "category": "Research",
      "summary": "汇总 World Labs、Azureovo 网站、image-blaster、3DGS-to-mesh、SimAnything/PhysSplat 等路线，落到 Video2Mesh 的可执行技术选型。",
      "source_path": "docs/03-research-roadmap.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research",
        "Scene Graph",
        "Mesh",
        "3DGS",
        "World Labs",
        "SimAnything"
      ],
      "body": "\n# 技术调研与选型报告\n\n## 总结判断\n\nVideo2Mesh 不应该追求“从视频一步生成一个完美 mesh”。更稳的产品形态是分层资产包：\n\n```text\nscan video\n  -> pose / dense geometry\n  -> 3DGS visual proxy\n  -> semantic masks / semantic splats\n  -> visual mesh / repaired object mesh\n  -> collider mesh / primitive proxy\n  -> scene graph / physics metadata\n  -> Web / Unity / MuJoCo / Isaac adapters\n```\n\n本次调研后，推荐的主线是：\n\n| 层 | 当前选型 | 为什么 |\n|---|---|---|\n| 位姿和稠密几何 | COLMAP dense workspace；失败时 MASt3R/DUSt3R/VGGT 兜底 | COLMAP 输出标准，能直接接 GraphDECO、Delaunay mesher、CloudCompare/Open3D |\n| 视觉代理 | GraphDECO 3DGS，Web 端用 Spark/SuperSplat 类 runtime | 画质和实时展示最好，适合做扫描场景的 photoreal visual layer |\n| 场景级碰撞代理 | COLMAP dense workspace + `delaunay_mesher`；辅以 Poisson/voxel mesh | 我们实测 Delaunay dense mesh 最接近 3MB collider 目标，碎片少于直接 raw fused Poisson |\n| 物体 visual mesh | 3DGS rendered RGB/depth/mask + TSDF；GS2Mesh-style stereo depth 作为增强 | 不直接相信 Gaussian center / scale，而是把 3DGS 当多视角渲染器提取 depth evidence |\n| 高质量 3DGS-to-mesh benchmark | GS2Mesh、SuGaR、2DGS/GOF、3DGS-to-PC | 用于对照和局部升级，不作为 P0 collider 主链路 |\n| 遮挡补全 | image-blaster/Hunyuan3D/Meshy/TRELLIS 生成 object-local mesh，再 fit 回场景 | 生成式 mesh 擅长补全物体外观，但尺度、朝向、支撑面必须由 Video2Mesh 校准 |\n| 语义和交互 | semantic splats/point labels + mesh face semantic sidecar + scene graph | 不把语义硬塞进视觉或碰撞资产，按 face/object/affordance 独立查询 |\n| 动态仿真 | SimAnything/PhysSplat-style dynamic Gaussian 作为 P2 旁路线 | 它们解决动态 Gaussian/物理属性估计，不替代 mesh collider |\n\n核心原则一句话：**3DGS 做视觉代理，mesh/collider 做碰撞代理，semantic sidecar 做语义查询，physics sidecar 做仿真合同。**\n\n## 参考项目与边界\n\n| 项目 / 来源 | 它真正提供什么 | Video2Mesh 应该怎么借 | 不应该误解成 |\n|---|---|---|---|\n| Azureovo 学长 3D Scene Research | 3DGS 视觉层 + CloudCompare/Poisson/Unity Collider 的可交互场景路线；网页 demo 中 `.splat/.sog` 视觉资产和 `.glb` collision mesh 分离 | 借它的“视觉代理 + 碰撞代理”架构、3MB 级 collider 目标、Web/Unity 对齐思路 | 直接从 3DGS PLY 点中心稳定得到高质量 mesh |\n| World Labs / Marble | 静态 world/background 生成，资产中包含 splat/SPZ、pano、collider mesh 等多层输出 | 借 clean plate/background repair 思路，以及环境视觉资产和 collider 资产分开交付的产品形态 | 物体级仿真资产生成器或 Video2Mesh 替代品 |\n| Spark / SuperSplat 类 Web runtime | 高斯场景实时渲染、压缩格式和浏览器展示 | 作为 Web visual proxy runtime；raycast/collision 仍交给 mesh | 3DGS 本身提供物理碰撞 |\n| image-blaster | 从单图/裁剪图生成 object mesh；按 `worlds/<world>/output/<object>/` 管理资产；React/Three/Rapier viewer | 作为 object completion helper，接在 `prepare-object-images -> export-image-blaster -> import-object-meshes` 后 | `simulator_asset_bundle.json`、Unity/MuJoCo/Isaac adapter 的拥有者 |\n| COLMAP / CloudCompare / PoissonRecon | 经典 SfM/MVS 和点云建面工具链 | P0 scene collider、对照 mesh、手工/半自动检查 | 遮挡物体补全或语义理解 |\n| SuGaR | 让 Gaussians surface-aligned，再提取可编辑 mesh，并可把 Gaussians 绑定到 mesh | P2 visual mesh benchmark，适合单物体/小场景高质量对照 | P0 collider 主路线 |\n| GS2Mesh | 从 3DGS 渲染 stereo novel views，用 stereo depth + TSDF 得 mesh | P1/P2 object mesh 质量增强，和我们的 rendered depth/mask 路线最契合 | 直接读取 Gaussian center 连面 |\n| SimAnything / PhysSplat | MLLM 估计物理属性，semantic Gaussian/particle dynamics，动态 splat 渲染 | P2 动态对象和物理属性草稿路线 | mesh 补全、Unity collider 或 MuJoCo rigid body 替代品 |\n\n## World Labs、Spark 与网页架构\n\nWorld Labs / Marble 和学长网页给出的工程信号很一致：交付的不是“一个万能 3D 文件”，而是一组分层资产。\n\n```text\nworld visual splat / SPZ / SOG\n  + pano / environment map\n  + collider mesh GLB\n  + semantic / scale / ground metadata\n  + viewer/controller/runtime code\n```\n\n本地 `image-blaster` 的 world 路径也印证了这一点：\n\n- `image-blaster/.claude/scripts/world/generate-world.mjs` 调 World Labs Marble `worlds:generate`，下载 `collider_mesh_url` 为 `*-world.glb`，下载 `pano_url`，并保存 `spz_urls`。\n- `image-blaster/app/src/utils/worldLoader.ts` 和 `WorldViewer.tsx` 只接受 `/worlds/...` 本地资产 URL，不在 viewer 里直接读 provider URL。\n- `SplatRenderer.tsx` 用 Spark `SparkRenderer` / `SplatMesh` 渲染 splat，并显式禁用 raycast。\n- `WorldCollider.tsx` 把 GLB 放进 Rapier fixed trimesh rigid body；object 侧 `SceneObject.tsx` 则用 GLB visual + box collider/rigid body 处理交互。\n\n这和我们现在的 Web demo 方向一致：\n\n```text\nGraphDECO 3DGS PLY / SPZ / SOG\n  -> Spark visual layer\n\nCOLMAP Delaunay / Poisson / simplified GLB\n  -> raycast\n  -> ground probe\n  -> forward block\n  -> Unity MeshCollider / Web physics proxy\n```\n\n因此 Video2Mesh 的目标不是把 3DGS 变成物理引擎，而是产出一个“视觉、碰撞、语义、物理”分层的 asset bundle。\n\n## image-blaster 技术定位\n\nimage-blaster 更像 object mesh generation + viewer asset convention，而不是扫描重建 pipeline。\n\n它的可借点：\n\n- 目录约定：`worlds/<world>/output/<object>/object.json`、编号参考图、编号 mesh。\n- 生成链路：先得到干净 reference image，再调用 Hunyuan3D/Meshy/FAL 类后端生成 mesh。\n- Viewer 约定：GLB 是最稳的交互模型格式；Three.js 加载 visual，Rapier 包裹 collider。\n- World 链路：World Labs 负责 static world/background，object mesh 单独生成和摆放。\n\n接入 Video2Mesh 的正确位置：\n\n```text\nVideo2Mesh object masks / selected frames\n  -> prepare-object-images\n  -> export-image-blaster\n  -> image-blaster / Hunyuan / Meshy jobs\n  -> import-object-meshes\n  -> fit-object-local-meshes-to-bbox\n  -> export-simulator-assets\n```\n\n注意边界：\n\n- image-blaster 生成的是 object-local visual mesh；它不知道我们场景的真实尺度、相机坐标、support plane 和 object_id 置信度。\n- `simulator_asset_bundle.json`、physics defaults、Unity/MuJoCo/Isaac adapter 仍应该由 Video2Mesh 生成。\n- 遮挡补全要拆成 object completion 和 background clean plate，不能用物体 mesh 自动修复背后的地板/墙面。\n\n## 3DGS 到 Mesh 路线横评\n\n我们已经验证过：直接从 3DGS PLY 里的 Gaussian center 当点云去 Poisson，容易得到碎片、大薄片、漂浮物和错位面。原因是 3DGS 优化目标主要是照片一致性，不保证 Gaussian center 采样在真实表面上，也不保证 `scale/rot/opacity` 可以直接解释成 watertight surface。\n\n更合理的路线如下：\n\n| 方法 | 输入 | 产物 | 优点 | 风险 | 当前优先级 |\n|---|---|---|---|---|---|\n| COLMAP dense + Delaunay | dense workspace / fused geometry | scene mesh / GLB collider | 与 COLMAP 原生数据一致，我们实测体量和效果最接近 collider 目标 | 适合场景级 static collider，不适合物体补全 | P0 |\n| CloudCompare/Open3D Poisson | 点云 + normals | watertight-ish mesh | 快速、传统、好自动化；voxel/downsample 后可得到较平滑场景 mesh | 会补洞，可能生成悬浮物/薄片；语义边界差 | P0/P1 |\n| Voxel / TSDF fusion | posed depth maps / rendered depth | smooth mesh | 抗噪，适合 object visual mesh 和场景代理 | 依赖 depth 和 mask 质量 | P1 |\n| GS2Mesh-style | trained 3DGS -> stereo rendered views -> stereo depth -> TSDF | geometrically consistent mesh | 不直接相信 Gaussian geometry，借 3DGS novel view + stereo prior | 需要视角采样、stereo 模型、TSDF 参数 | P1/P2 |\n| SuGaR | 3DGS checkpoint + surface alignment optimization | editable mesh + refined Gaussian | 适合可编辑 visual mesh 和高质量 benchmark | 额外训练/优化，P0 成本高 | P2 |\n| 2DGS / GOF / surface-aware GS | 替换或增强 Gaussian 表面约束 | 更 surface-friendly 的 GS/mesh | 从训练端解决几何不贴面问题 | 替换后端成本较高 | P2 |\n| 3DGS-to-PC / sampled surface Gaussians | 3DGS -> sampled point cloud -> Poisson | point cloud / mesh | 可作为无重训转换工具 | 仍需处理 floaters、normal、采样策略 | P2 |\n| Neural SDF / NeuS / VolSDF | posed images / masks | high-quality mesh | 表面质量强 | 训练慢，和 3DGS 主链路并行成本高 | P3 |\n\n当前最实用的落地策略：\n\n```text\nscene collider:\n  COLMAP dense workspace -> delaunay_mesher -> simplify -> GLB\n\nobject visual mesh:\n  3DGS render RGB/depth/mask -> masked TSDF -> cleanup -> GLB\n\nhigh-quality benchmark:\n  GS2Mesh and SuGaR on selected objects / small scenes\n```\n\n## COLMAP、CloudCompare 与 PoissonRecon 选型\n\nCloudCompare 是点云/三角网格处理软件，PoissonRecon 是其常用建面插件/功能。它适合人工检查和半自动对照：\n\n```text\npoint cloud\n  -> normal estimation\n  -> Poisson Surface Reconstruction\n  -> trim / clean / simplify\n  -> PLY/OBJ/GLB\n```\n\n但对我们当前 bedroom 类场景，经验结论是：\n\n- 直接对 `fused.ply` 或 3DGS center PLY 跑 Poisson，容易得到大薄片和悬浮壳。\n- dense point cloud 先做 voxel/downsample/outlier cleanup，再 Poisson，能得到较平滑 scene mesh，但仍要清理悬浮物。\n- COLMAP 原生 `delaunay_mesher` 从 dense workspace 建面更稳，适合做 3MB 级 static collider。\n- Poisson/voxel mesh 可以作为 visual inspection 或 fallback collider，不应该作为唯一生产路线。\n\n因此选型是：\n\n| 用途 | 推荐 |\n|---|---|\n| Web/Unity static scene collider | COLMAP dense + Delaunay mesh |\n| 快速人工检查 | CloudCompare PoissonRecon / MeshLab / Blender |\n| 自动化 fallback | Open3D Poisson with voxel/downsample/outlier cleanup |\n| object visual mesh | 3DGS rendered depth/mask + TSDF，而不是 raw point Poisson |\n\n## 语义回灌与 Mesh 分类\n\nMesh 分类不能只靠三角面最近的一个 semantic point。床面、墙面、桌面和薄片很容易串语义。更稳的做法是分层回灌：\n\n```text\nP0: semantic splats / semantic point cloud -> mesh face KDTree vote\nP1: mesh face center -> project to multi-view masks -> visibility weighted vote\nP2: face graph smoothing + object support constraints + VLM relation QA\n```\n\n推荐的 semantic sidecar 结构：\n\n```json\n{\n  \"mesh\": \"colliders/scene_collision.glb\",\n  \"face_semantics\": [\n    {\n      \"face\": 1024,\n      \"object_id\": \"bed_01\",\n      \"label\": \"bed\",\n      \"probability\": 0.91,\n      \"source\": \"semantic_splats+multiview_masks\"\n    }\n  ]\n}\n```\n\n交互时：\n\n```text\nraycast hit\n  -> triangleIndex\n  -> face_semantics[triangleIndex]\n  -> object_id / label / affordance / physics material\n```\n\n这比把语义直接烘进 GLB 顶点色更可靠，因为 collider 可以简化、替换、双面化，但 sidecar 仍能保留 face/object 级语义合同。\n\n## SimAnything / PhysSplat 选型\n\nSimAnything / PhysSplat 的目标不是把 3DGS 转成 mesh，而是让 static 3D scene 获得可交互动态：\n\n```text\nstatic 3DGS / scene reconstruction\n  -> object-level open-vocabulary segmentation\n  -> MLLM physical property estimation\n  -> particle / Gaussian dynamics\n  -> dynamic splat rendering\n```\n\n对 Video2Mesh 的价值：\n\n- 用 MLLM/VLM 给每个 object 生成物理属性草稿：材质、质量范围、摩擦、恢复系数、刚体/软体候选。\n- 对 pillow、blanket、cloth、plant、liquid、granular 等对象探索 dynamic Gaussian assets。\n- 作为展示层显示“物体受力后的视觉变形”，而不是只输出传统 rigid-body mesh。\n\n不适合：\n\n- 替代 COLMAP/3DGS 重建。\n- 替代 object visual mesh。\n- 替代 Unity/MuJoCo/Isaac collider。\n- 直接生成可相信的工程物理参数。\n\nVideo2Mesh 的接入点应该是：\n\n```text\nprepare-simulator-physics-jobs\n  -> mllm_physics provider\n  -> import-simulator-physics\n  -> simulator-physics-quality-report\n\nsimulator_assets/dynamic_gaussian_assets/\n  objects/<object_id>/gaussians.ply\n  objects/<object_id>/physics.json\n  simulations/<sim_id>/trajectory.npz\n```\n\n也就是说，SimAnything/PhysSplat 是 P2 动态旁路线，不动 P0/P1 的 visual 3DGS + collider mesh 主合同。\n\n## 当前阶段技术选型\n\n### P0：可展示、可交互、可传回本地\n\n- COLMAP dense + GraphDECO 30k 3DGS。\n- 3DGS PLY 清理 floaters 后做 visual proxy。\n- COLMAP dense workspace + Delaunay mesh 做 scene collider。\n- Web demo / Unity 用 collider mesh 做 raycast、ground probe、obstacle blocking。\n- semantic sidecar 先用 point/splat -> face KDTree voting。\n\n验收标准：\n\n- 3DGS 视觉层和 collider mesh 对齐。\n- collider 体量在几 MB 到几十 MB 可控范围。\n- raycast 命中的是 mesh，不是 splat。\n- semantic face debug PLY 至少能看出大类区域，低置信度可标 unknown。\n\n### P1：物体级资产和补全\n\n- 对床、桌、椅、柜等 foreground object 做 3DGS rendered depth/mask + TSDF。\n- 对遮挡严重物体，用 image-blaster/Hunyuan/Meshy/TRELLIS 生成完整 visual mesh。\n- 生成式 mesh 必须经过 bbox fit、support plane align、scale QA。\n- collider 用 primitive/convex/compound proxy，不直接拿复杂 visual mesh 当 dynamic collider。\n- mesh semantic 回灌升级到 multi-view projection voting。\n\n验收标准：\n\n- 物体 visual mesh 不再是碎点云连面。\n- dynamic object collider 稳定，不穿地、不爆炸。\n- `simulator_asset_bundle.json` 能明确记录 visual/collider/semantic/physics 的资产引用。\n\n### P2：高质量 Mesh 与动态 Gaussian\n\n- GS2Mesh-style stereo depth 对 selected objects / small scenes 做 benchmark。\n- SuGaR / 2DGS / GOF 对比训练端 surface-aware 方法。\n- SimAnything/PhysSplat-style MLLM physics draft 和 dynamic Gaussian demo。\n- Scene graph 引入 support/on/inside/near/affordance 关系。\n\n验收标准：\n\n- 能证明 GS2Mesh/SuGaR 相比 TSDF 或 Delaunay 的质量收益。\n- dynamic Gaussian 只作为视觉动态层接入，不破坏传统 simulator adapter。\n- 语义、物理、交互逻辑可以在 Web/Unity 中按 object_id 查询。\n\n## 实现建议\n\n近期最值得做的不是再盲跑更多 raw Poisson，而是把已经验证有效的几条路线固化成稳定命令和报告：\n\n1. 固化 `COLMAP dense -> delaunay_mesher -> simplify -> GLB collider`。\n2. 固化 `3DGS clean PLY -> Spark visual layer`。\n3. 固化 `collider GLB + semantic face sidecar -> Web/Unity raycast label`。\n4. 把 `3DGS rendered depth/mask -> TSDF object mesh` 作为 P1 主开发。\n5. 把 image-blaster/Hunyuan/Meshy 作为 object completion provider，而不是主重建器。\n6. 把 GS2Mesh/SuGaR 作为 benchmark 后端，选 1-2 个物体或小场景做对照即可。\n7. SimAnything/PhysSplat 先落到 physics draft 和 dynamic Gaussian 目录合同，不进入 P0 collider。\n\n## 参考资料\n\n| 主题 | 链接 |\n|---|---|\n| Azureovo  3D scene research | [https://azureovo.github.io/3dscene/research/](https://azureovo.github.io/3dscene/research/) |\n| World Labs | [https://www.worldlabs.ai/](https://www.worldlabs.ai/) |\n| World Labs Platform | [https://platform.worldlabs.ai/](https://platform.worldlabs.ai/) |\n| Spark | [https://sparkjs.dev/](https://sparkjs.dev/) |\n| image-blaster | [https://github.com/neilsonnn/image-blaster](https://github.com/neilsonnn/image-blaster) |\n| COLMAP | [https://colmap.github.io/](https://colmap.github.io/) |\n| CloudCompare | [https://www.cloudcompare.org/](https://www.cloudcompare.org/) |\n| GS2Mesh | [https://gs2mesh.github.io/](https://gs2mesh.github.io/) |\n| SuGaR | [https://anttwo.github.io/sugar/](https://anttwo.github.io/sugar/) |\n| PhysSplat / SimAnything paper | [https://arxiv.org/abs/2411.12789](https://arxiv.org/abs/2411.12789) |\n",
      "headings": [
        {
          "level": "2",
          "text": "总结判断",
          "slug": "总结判断"
        },
        {
          "level": "2",
          "text": "参考项目与边界",
          "slug": "参考项目与边界"
        },
        {
          "level": "2",
          "text": "World Labs、Spark 与网页架构",
          "slug": "world-labsspark-与网页架构"
        },
        {
          "level": "2",
          "text": "image-blaster 技术定位",
          "slug": "image-blaster-技术定位"
        },
        {
          "level": "2",
          "text": "3DGS 到 Mesh 路线横评",
          "slug": "3dgs-到-mesh-路线横评"
        },
        {
          "level": "2",
          "text": "COLMAP、CloudCompare 与 PoissonRecon 选型",
          "slug": "colmapcloudcompare-与-poissonrecon-选型"
        },
        {
          "level": "2",
          "text": "语义回灌与 Mesh 分类",
          "slug": "语义回灌与-mesh-分类"
        },
        {
          "level": "2",
          "text": "SimAnything / PhysSplat 选型",
          "slug": "simanything-physsplat-选型"
        },
        {
          "level": "2",
          "text": "当前阶段技术选型",
          "slug": "当前阶段技术选型"
        },
        {
          "level": "3",
          "text": "P0：可展示、可交互、可传回本地",
          "slug": "p0可展示可交互可传回本地"
        },
        {
          "level": "3",
          "text": "P1：物体级资产和补全",
          "slug": "p1物体级资产和补全"
        },
        {
          "level": "3",
          "text": "P2：高质量 Mesh 与动态 Gaussian",
          "slug": "p2高质量-mesh-与动态-gaussian"
        },
        {
          "level": "2",
          "text": "实现建议",
          "slug": "实现建议"
        },
        {
          "level": "2",
          "text": "参考资料",
          "slug": "参考资料"
        }
      ],
      "reading_minutes": 4
    },
    {
      "id": "04-mesh-interaction-and-completion",
      "title": "Mesh、交互与遮挡补全",
      "category": "Simulation",
      "summary": "从 3DGS 到可交互场景的资产分层、mesh 重建、collider、遮挡补全、语义和 SimAnything 动态线。",
      "source_path": "docs/04-mesh-interaction-and-completion.md",
      "source_kind": "builtin",
      "updated": "2026-07-02",
      "tags": [
        "Mesh",
        "Collider",
        "Completion",
        "SimAnything",
        "Simulation"
      ],
      "body": "\n# Mesh、交互与遮挡补全\n\n## 核心结论\n\n3DGS 不能直接承担碰撞和交互。3DGS 本质是离散高斯椭球体集合，没有 mesh topology，也不能直接生成可靠 collider。\n\n可交互场景应该这样分层：\n\n```text\n3DGS visual layer\n  + visual mesh / completed mesh\n  + simplified collision proxy\n  + semantic / scene graph sidecar\n  + physics material and body metadata\n  + engine adapter\n```\n\n视觉要“像”，物理要“稳”，语义要“可查询”。三者不要混成一个资产。\n\n## Scene collider\n\n静态场景的第一版 collider 可以用：\n\n```text\nCOLMAP dense / fused point cloud\n  -> Poisson reconstruction\n  -> simplification\n  -> scene_collision.glb\n```\n\n这和 Azureovo 报告中的 CloudCompare PoissonRecon 路线一致，适合快速补上 Web/Unity 的碰撞闭环。\n\n注意：\n\n- Poisson 会补洞，作为 collider 可以接受，作为 visual mesh 要谨慎。\n- scene-level static collider 可以是 concave mesh。\n- dynamic object 不应该直接用复杂 concave mesh collider。\n\n## Object visual mesh\n\n生产路线：\n\n```text\ntrained GraphDECO 3DGS\n  + object masks\n  + registered camera poses\n  -> render object-centric RGB/depth/normal/mask\n  -> masked TSDF fusion\n  -> marching cubes / Poisson\n  -> cleanup / hole fill / simplify\n  -> visual mesh\n```\n\n这比直接从 sparse object mask cloud 三角化稳定，因为 3DGS 可以提供多视角、可筛选的 rendered evidence。\n\n如果 depth 不稳定，可以接 GS2Mesh-style stereo depth：先渲染 stereo views，再用 stereo model 估深，最后 TSDF fusion。\n\n## SuGaR、GS2Mesh 和其他 mesh 路线\n\n| 方法 | 输入 | 输出 | 适合 |\n|---|---|---|---|\n| COLMAP/CloudCompare Poisson | dense point cloud | scene mesh | P0 scene collider |\n| Open3D Poisson/BPA/alpha | point cloud + normals | baseline mesh | debug / automated baseline |\n| TSDF fusion | posed depth maps / 3DGS rendered depth | smooth object mesh | P1 object visual mesh |\n| GS2Mesh | 3DGS rendered stereo views | TSDF fused mesh | in-the-wild 3DGS-to-mesh enhancement |\n| SuGaR | trained 3DGS | editable mesh + refined GS | P2 visual mesh backend |\n| 2DGS / GOF | surface-aware Gaussian optimization | high-quality surface | P2/P3 research backend |\n| NeuS / VolSDF | posed images | neural SDF mesh | high-quality offline asset |\n\n![SuGaR pipeline and editing result](https://anttwo.github.io/sugar/results/full_teaser.png \"SuGaR 官方项目页图：pipeline 与编辑/合成效果，说明 extracted mesh 可以承接编辑，最终仍可用 Gaussian splatting 渲染\")\n\n![Surface-aligned Gaussian arrangement](https://anttwo.github.io/sugar/results/gaussian_arrangement.png \"SuGaR 官方项目页图：surface-aligned regularization 让 Gaussians 沿真实表面排列，后续再做 mesh extraction\")\n\n推荐顺序：\n\n1. P0：scene collider 用 dense point cloud + Poisson。\n2. P1：object visual mesh 用 3DGS rendered depth/mask + TSDF。\n3. P1：dynamic object collider 用 primitive / convex decomposition。\n4. P2：GS2Mesh-style depth enhancement。\n5. P2：SuGaR 单物体 benchmark。\n\n## Collider 策略\n\n| 对象 | 推荐 collider |\n|---|---|\n| 地面/墙体/大场景 | simplified static MeshCollider |\n| 桌椅柜等静态家具 | box / convex hull / compound primitive |\n| 动态可移动物体 | primitive / convex decomposition |\n| 楼梯/斜坡 | ramp proxy + navmesh |\n| 视觉细节复杂物体 | visual mesh 和 physics mesh 分离 |\n\n物体 visual mesh 出来后：\n\n```text\nobject_mesh.glb\n  -> CoACD / V-HACD / primitive fitting\n  -> object_collider_compound.glb\n  -> export-simulator-assets\n```\n\nUnity 中 concave MeshCollider 通常更适合 static/kinematic 场景。动态刚体应优先使用 convex 或 compound colliders。\n\n## 遮挡补全\n\n桌子、椅子这类对象要交互时，遮挡补全要拆成三件事：\n\n```text\nobject visual completion\nbackground clean plate\nphysics proxy completion\n```\n\n### Object visual completion\n\n如果物体部分被挡住，但需要完整视觉 mesh，可以从 object crops / selected frames 生成完整模型：\n\n- Hunyuan3D。\n- Meshy。\n- TRELLIS。\n- InstantMesh。\n- image-blaster external mesh jobs。\n\n生成 mesh 后必须对齐回原场景：\n\n```text\ngenerated object-local mesh\n  -> fit to observed 3D bbox\n  -> align support plane\n  -> record completion source and confidence\n```\n\n### Background completion\n\n如果用户移动桌椅，原来被挡住的地面/墙面会露出来。这时需要 clean plate：\n\n```text\nvideo frames + object masks\n  -> remove object from frames\n  -> 2D image/video inpainting\n  -> rebuild / update background 3DGS or background mesh\n```\n\n背景补全和物体补全要分开。物体生成得再完整，也不能自动恢复它背后的地板。\n\n### Physics proxy completion\n\n交互不需要真实还原每个不可见三角面。它需要稳定、合理、保守的物理代理：\n\n- table：桌面 box + 桌腿 box/capsule。\n- chair：坐垫 box + 靠背 box + 椅腿 + 扶手可选。\n- cabinet：box / convex hull。\n- plant：粗略 pot collider + visual mesh。\n\n这比拿生成式 visual mesh 直接做碰撞更稳。\n\n## 语义兼容\n\n语义不要塞死在 collider 里。3DGS 继续做视觉代理，mesh 只做碰撞代理，语义用 sidecar 回灌到 mesh face：\n\n```json\n{\n  \"mesh\": \"colliders/scene_collision.glb\",\n  \"face_semantics\": [\n    {\"face\": 1024, \"object_id\": \"gdino_object_bed\", \"label\": \"bed\", \"probability\": 0.91}\n  ]\n}\n```\n\nP0 用 KDTree / nearest semantic transfer：\n\n```text\nsemantic_splats / semantic point cloud\n  -> KDTree / radius grid\nmesh faces\n  -> face center\n  -> nearest K semantic points\n  -> distance + probability weighted vote\n  -> face object_id\n```\n\n可复现命令：\n\n```bash\npython -m video2mesh.cli transfer-mesh-semantics \\\n  --project-root exports/bedroom_4_shape_regularized_v2_dense100_47_56_20260628_key_results \\\n  --semantic-splats-ply exports/bedroom_4_shape_regularized_v2_dense100_47_56_20260628_key_results/semantic_gaussian_probabilities.ply \\\n  --semantic-manifest exports/bedroom_4_shape_regularized_v2_dense100_47_56_20260628_key_results/semantic_splats_manifest.json \\\n  --mesh tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_recon_results/postprocessed_keep_candidates/colmap_delaunay_mesh_double_sided_indexed.glb \\\n  --output tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_recon_results/mesh_semantic_backfill_colmap_delaunay_glb/mesh_semantics.json \\\n  --debug-ply tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_recon_results/mesh_semantic_backfill_colmap_delaunay_glb/colored_debug_mesh.ply \\\n  --k 8 \\\n  --max-distance-ratio 0.015 \\\n  --min-face-probability 0.35 \\\n  --min-vote-confidence 0.45 \\\n  --smooth-iterations 1 \\\n  --min-region-faces 8\n```\n\n输出合同：\n\n- `mesh_semantics.json`：`face_semantics` 按 triangle index 排列。\n- `colored_debug_mesh.ply`：复制每个三角形顶点并按 face 语义染色，用来检查串语义和 unknown 区域。\n- Unity/Web 点击或射线命中 collider 后，用 `RaycastHit.triangleIndex` / hit face index 直接查 `face_semantics[triangleIndex]`。\n\n这个方法快、稳定、自动化，适合 COLMAP Delaunay collider、Open3D Poisson collider、GS2Mesh visual mesh。薄墙、床面、桌面等贴近区域可能串语义，所以必须保留 `max_distance` / `max-distance-ratio`、低置信度 unknown、小区域清理和平滑。\n\nP1 再做 ray projection / 多视角投票：\n\n```text\nmesh face center\n  -> project back to video frames\n  -> query 2D mask / semantic mask\n  -> multi-view visibility and vote\n  -> face object_id\n```\n\n多视角投票更适合边界和遮挡，但实现成本更高。当前 collider 闭环先用 P0 KDTree 回灌。\n\n## SimAnything / PhysSplat 动态线\n\nSimAnything / PhysSplat 的价值不是 mesh 补全，而是把语义 Gaussian 对象变成可动态仿真的对象：\n\n```text\nsemantic Gaussian object\n  -> physics property inference\n  -> particle / Gaussian state\n  -> simulation\n  -> dynamic splat rendering\n```\n\n适合：\n\n- cloth。\n- pillow。\n- blanket。\n- plant leaf。\n- liquid / granular / soft object。\n- 局部受力形变展示。\n\n不适合替代：\n\n- object visual mesh。\n- Unity/MuJoCo collider。\n- scale/physics QA。\n\n推荐新增旁路线：\n\n```text\nsimulator_assets/dynamic_gaussian_assets/\n  scene_dynamic_config.json\n  objects/<object_id>/gaussians.ply\n  objects/<object_id>/physics.json\n  objects/<object_id>/constraints.json\n  simulations/<sim_id>/trajectory.npz\n```\n\n短期最实用的是先接 MLLM/VLM 物理属性草稿：\n\n```text\nobject crop + mask + label + bbox + support plane\n  -> mllm_physics provider\n  -> mass / material / friction / restitution / rigid/deformable\n  -> import-simulator-physics\n  -> simulator-physics-quality-report\n```\n\n## 推荐落地方案\n\n第一版可交互：\n\n1. 3DGS 继续做 visual scene。\n2. scene collider 用 dense point cloud + Poisson + simplify。\n3. object mesh 用 3DGS rendered depth/mask + TSDF。\n4. 遮挡严重的常见家具用 generated visual mesh 补全。\n5. physics collider 用 bbox/primitive/convex decomposition。\n6. semantic / scene graph / physics 用 sidecar 记录。\n7. Unity/MuJoCo/Isaac 只消费稳定合同，不直接依赖 3DGS 高斯几何。\n\n这条路线和 Icare / World Labs / Azureovo 报告的共识一致：3DGS 做视觉层，传统 mesh/physics/controller 做交互层。\n",
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
      "id": "08-web-visual-physics-demo",
      "title": "Web 视觉代理与碰撞代理演示",
      "category": "Simulation",
      "summary": "一个参考 World Labs、image-blaster 和学长 TriSplat 演示结构的 Web demo：Spark 真实 3DGS 视觉层与 GLB collider mesh 分层交互。",
      "source_path": "docs/08-web-visual-physics-demo.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Web Demo",
        "3DGS",
        "Mesh Collider",
        "World Labs",
        "Simulation"
      ],
      "body": "\n# Web 视觉代理与碰撞代理演示\n\n在线演示入口：[Visual Proxy Demo](/demos/visual-physics-proxy/)\n\n## 目标\n\n这个 demo 验证的是架构，而不是最终画质：\n\n```text\nreal Spark 3DGS visual layer (.ply / .sog / .spz / .splat)\n  -> only for rendering\n\nreal lightweight GLB collider mesh\n  -> movement\n  -> raycast hit test\n  -> floor probing / obstacle blocking\n  -> future Unity / Web physics proxy\n```\n\n它对应我们项目里的核心判断：3DGS 负责视觉真实感，mesh/collider 负责物理、导航、点击、交互和 runtime 逻辑。\n\n## 参考对象\n\n| 来源 | 借鉴点 | demo 中的实现 |\n|---|---|---|\n| World Labs / Marble | 环境视觉资产和 collider 资产分开输出 | Spark 3DGS 视觉资产和 collider mesh 分成两个 layer |\n| image-blaster | `SparkRenderer` / `SplatMesh` + Rapier/mesh collider + object layer | Spark 负责 3DGS 视觉，Three.js mesh 负责射线和碰撞 |\n| 学长 TriSplat 网页 | `Outdoor.splat` / `outdoor4.sog` + `outdoor4.collision.glb`，以及 `3DGS.sog` + `3dgsCollider.glb` player controller | 保留真实 `.splat/.sog` 视觉资产和同源 GLB collider 作为兜底 |\n| Icare / SparkJS | splat 视觉资源与 walkable / characterCollision mesh 分离 | Splat 禁用 raycast，GLB mesh 独立承担交互 |\n\n## 当前能力\n\n- 视觉层：默认用 Spark `SplatMesh` 加载 bedroom_4 CLI30K 真实生成的 clean GraphDECO Gaussian PLY `bedroom_4_cli30k_graphdeco_clean_iteration30000.ply`，971,305 个高斯；若失败再退回 repaired GraphDECO PLY、cleaned XYZRGB PLY、Spark `azureovo_outdoor.splat` / `azureovo_3dgs.sog` 和旧 PLY debug visual。视觉层只负责显示，默认不参与 raycast。\n- 碰撞层：主路径加载同一 CLI30K run 的 `bedroom_4_cli30k_colmap_delaunay_dense_collider.glb`，来自 `mesh_recon_results/colmap_delaunay_dense/mesh.glb`，作为静态 mesh collider proxy；若失败再走旧 bedroom_4 collider、Spark 同源 GLB collider 与旧 Poisson GLB fallback。\n- Actor：WASD / 方向键 / 屏幕按钮移动；Real Assets 模式下用 GLB mesh 做向下地面探测和前向阻挡探测。\n- Raycast：单击画面只命中 collider mesh，并显示红色命中点、法线、face index、surface type 和 surface role；单击还会把 Orbit 相机焦点移到命中点，方便像 SuperSplat 一样快速检查局部表面。\n- Debug：默认同时显示 Visual 3DGS 和 Collider Mesh overlay；可切换 Real Assets / Procedural fallback、Visual 3DGS、Collider render mode、Orbit/Fly Camera、Spark quality、Semantic Tint。\n- Collider render mode：`wire` 显示线框 + 透明实体，`solid` 显示半透明 mesh，`hidden` 隐藏可视化但继续参与 ground probe、forward block 和 raycast。这个模式对应 image-blaster / Icare 中“碰撞代理是逻辑资产，不必总是可见”的做法。\n- Camera：Orbit 模式用于总览和点击聚焦；Fly 模式用于进入房间内部，鼠标拖拽看向，WASD 平移，Q/E 下/上。\n- Spark quality：`Balanced` 保持默认，`Crisp` 收紧 splat 半径便于检查边界，`Fast` 降低像素半径和 alpha 负担便于本地交互。\n\n## 当前资产\n\n| 层 | 文件 | 体积 | 用途 |\n|---|---:|---:|---|\n| 主视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_cli30k_graphdeco_clean_iteration30000.ply` | 230MB | CLI dense GraphDECO 30k clean Gaussian PLY，971,305 splats，带 `f_dc_*` / `opacity` / `scale_*` / `rot_*`，由 Spark `SplatMesh` 渲染，禁用 raycast |\n| 主碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_cli30k_colmap_delaunay_dense_collider.glb` | 2.9MB | 同一 CLI30K run 的 `colmap_delaunay_dense/mesh.glb`，82,920 vertices / 167,082 triangles，负责 raycast / ground probe |\n| GraphDECO fallback | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_supersplat.ply` | 207MB | bedroom_4 dense100/repaired GraphDECO Gaussian PLY，874,472 splats，Spark 主路径失败时兜底 |\n| 点云视觉 fallback | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.ply` | 37MB | bedroom_4 dense100/repaired viewer PLY 的 cleaned XYZRGB 版本，872,374 points，移除 2,098 个长尾离群点，Spark 主路径失败时用 `THREE.Points` 显示 |\n| 主视觉清理报告 | `docs-blog/demos/visual-physics-proxy/assets/bedroom_4_scene_3dgs_repaired_point_cloud_clean.outlier_clean_report.json` | 2KB | 记录 cleaned PLY 的 quantile bbox 参数、输入/输出 bbox 和移除数量 |\n| 兜底视觉代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor.splat` | 37MB | Spark `SplatMesh` 加载真实 `.splat` 3DGS，禁用 raycast |\n| 兜底碰撞代理 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_outdoor_collider.glb` | 1.1MB | Three.js `GLTFLoader` + `DRACOLoader` 加载 outdoor collider，负责 raycast / ground probe |\n| 二级兜底视觉 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs.sog` | 11MB | Spark `SplatMesh` 加载 PC-SOGS 3DGS，禁用 raycast |\n| 二级兜底碰撞 | `docs-blog/demos/visual-physics-proxy/assets/azureovo_3dgs_collider.glb` | 3.4MB | `.sog` 路径失败前的同源 GLB collider |\n| fallback 视觉 | `docs-blog/demos/visual-physics-proxy/assets/3dgs_iter30000_clean_filtered_xyzrgb.ply` | 7.4MB | Spark 失败时加载为 `THREE.Points` debug visual |\n| fallback 碰撞 | `docs-blog/demos/visual-physics-proxy/assets/true_3dgs_cloudcompare_poisson_depth8_trim8_mesh_faces40000.glb` | 1.8MB | 我们自己的 CloudCompare/Poisson collider fallback |\n\n## 线上发布形态\n\n`relumeow.top` 的公开站仍由 GitHub Pages 构建 `docs-blog/_public/`。为了避开 GitHub 普通仓库和 Pages 对 100MB 以上单文件的限制，两个 GraphDECO 大 PLY 在线上不直接发布 raw 文件：\n\n```text\nassets/large-asset-manifest.json\nassets/chunks/bedroom_4_cli30k_graphdeco_clean_iteration30000.ply.part00..04\nassets/chunks/bedroom_4_scene_3dgs_repaired_supersplat.ply.part00..04\n```\n\n每个分片约 48MB。前端先读取 `large-asset-manifest.json`，再按 manifest 拉取分片、合并成 `Uint8Array`，通过 `SplatMesh({ fileBytes, fileName, fileType: \"ply\" })` 初始化 Spark。这样线上 URL 仍展示同一套 3DGS 内容，但发布产物不会包含 230MB / 207MB 的 raw PLY 单文件。\n\n页面中的资产计数默认显示为 `3DGS / mesh`：bedroom_4 CLI30K Spark 主路径预期为 `971.3K / 167.1K`。页面会把当前 `visualAssetId`、`visualFormat`、`visualUrl`、`visualUsesSpark`、`visualRawCount`、`visualRemovedOutliers`、`visualCleanupReportUrl`、`colliderUrl`、`sparkRendererVisible`、`visibleColliderMeshes`、`visibleColliderWires`、`colliderRenderMode`、`cameraMode`、`splatQuality`、`lastHitInfo` 写入 `document.documentElement.dataset.visualPhysicsState`，方便确认线上实际命中的资产、显示状态和射线命中的 collider face。`Collider` 按钮只控制可视化，mesh 即使隐藏仍参与交互。\n\n当前 collider mesh 会标记这些 runtime roles：\n\n```json\n{\n  \"surfaceType\": \"scene-collider\",\n  \"walkable\": true,\n  \"characterCollision\": true,\n  \"cameraCollision\": true\n}\n```\n\n这参考了 Icare 的角色拆分：后续可以把同一个 GLB 或拆分后的 object colliders 分成 `walkable`、`characterCollision`、`cameraCollision`、`trigger` 等集合，再接入语义 face sidecar。\n\n本地 demo 额外放宽了 OrbitControls：相机可以绕完整球面旋转，并提供 `Reset View` 按钮按当前 3DGS/collider 包围盒自动重新构图。bedroom_4 的视觉层和碰撞层会作为同一组资产应用 SuperSplat 验证过的 Z 轴 180° 旋转、缩放和落地 offset，避免视觉层正了但 collider 错位。\n\n## 点云清理插入点\n\n当前 demo 主资产来自 `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/3dgs_point_cloud_clean_iteration30000.ply`，manifest 中记录原始输入 1,348,957 个高斯、清理后保留 971,305 个、移除 377,652 个。前端仍使用 per-axis 0.1% / 99.9% quantile bbox 加 2% padding 做相机和对齐用的稳健边界，避免少量远端高斯把视角拉远。项目流水线里可以用同样入口在语义投影融合和 mesh 重建前清理 plain XYZ/RGB 点云：\n\n```bash\npython -m video2mesh.cli clean-point-cloud-outliers \\\n  --project-root exports/<run> \\\n  --input exports/<run>/simulator_assets/viewer_plys/scene_3dgs_point_cloud.ply \\\n  --output exports/<run>/simulator_assets/viewer_plys/scene_3dgs_point_cloud_clean.ply \\\n  --quantile-min 0.001 \\\n  --quantile-max 0.999 \\\n  --padding-ratio 0.02 \\\n  --register-as scene_3dgs_point_cloud_ply\n```\n\n如果输入是带 opacity / scale / rotation 的 GraphDECO/SuperSplat PLY，仍优先使用已有的 `clean-3dgs-floaters`，它会额外过滤低透明度、细长和孤立高斯。\n\n## 后续替换方向\n\n这个 demo 的接口可以逐步替换：\n\n| 当前 demo | 后续增强 |\n|---|---|\n| Spark GraphDECO `.ply` visual layer | 当前线上使用 48MB 分片 + manifest；后续可转 `.spz` / `.sog` 或走 CDN/LFS 进一步减小体积 |\n| 真实 Poisson GLB collider | object-level mesh / convex hull / V-HACD / CoACD |\n| 轻量 kinematic collision | Rapier / Unity CharacterController / robot controller |\n| mock semantic tint | Video2Mesh semantic/probability splats 或 semantic sidecar |\n\n## 和 Video2Mesh 的接入位置\n\n```text\nexports/<run>/\n  semantic_supersplat.ply          # visual / semantic layer\n  simulator_assets/\n    background/collider_mesh.glb   # static collider proxy\n    objects/*/visual_mesh.glb      # object visual mesh\n    objects/*/collider.glb         # object collider proxy\n    simulator_asset_bundle.json    # pose / scale / semantic / physics sidecar\n```\n\n最终 Web viewer 可以从 `simulator_asset_bundle.json` 加载每个资产：\n\n- visual assets 放在可见层。\n- collider assets 放进 physics/raycast 层。\n- semantic sidecar 决定 hover label、可抓取性、affordance、材质参数。\n\n## 当前限制\n\n- 当前默认 bedroom_4 3DGS 和 collider 已来自 Video2Mesh 自己的 CLI dense GraphDECO 30k 本地导出；学长 `.splat/.sog` 资产只作为 Spark 路径兜底。\n- 230MB / 207MB GraphDECO raw PLY 不直接进入线上发布目录；当前通过 48MB 分片在浏览器端合并加载。长期仍建议转 `.spz` / `.sog` 或外链模型文件，减少首屏下载和内存压力。\n- 没有接入 Rapier rigid body，只做了轻量 kinematic collision 与 mesh raycast。\n- 真实碰撞 mesh 是场景级 collider proxy，还没有拆成桌子、椅子等 object-level collider。\n- 没有加载真实 World Labs Marble `.spz` 或 `collider_mesh_url`，但运行结构与 image-blaster / Icare 的 Spark visual + mesh proxy 边界一致。\n\n但它已经验证了我们要的最小闭环：真实视觉代理和真实碰撞代理可以完全分层，交互逻辑不依赖 3DGS 本身产生 collider。\n",
      "headings": [
        {
          "level": "2",
          "text": "目标",
          "slug": "目标"
        },
        {
          "level": "2",
          "text": "参考对象",
          "slug": "参考对象"
        },
        {
          "level": "2",
          "text": "当前能力",
          "slug": "当前能力"
        },
        {
          "level": "2",
          "text": "当前资产",
          "slug": "当前资产"
        },
        {
          "level": "2",
          "text": "线上发布形态",
          "slug": "线上发布形态"
        },
        {
          "level": "2",
          "text": "点云清理插入点",
          "slug": "点云清理插入点"
        },
        {
          "level": "2",
          "text": "后续替换方向",
          "slug": "后续替换方向"
        },
        {
          "level": "2",
          "text": "和 Video2Mesh 的接入位置",
          "slug": "和-video2mesh-的接入位置"
        },
        {
          "level": "2",
          "text": "当前限制",
          "slug": "当前限制"
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
      "updated": "2026-07-03",
      "tags": [
        "relumeow.top",
        "Docs Site",
        "API",
        "Site"
      ],
      "body": "\n# relumeow.top 文档站与远程控制\n\n## 文档站定位\n\n`docs-blog/` 是 relumeow.top 的静态文档站和本机 API 管理界面。当前项目主文档来自：\n\n```text\nREADME.md\ndocs/*.md\ndocs-blog/content/*.md\n```\n\n项目长期主文档应放在 `docs/`。`docs-blog/content/` 只保留网站或临时内容，不再放项目主报告。\n\n## 构建网站\n\n在仓库根目录运行：\n\n```bash\npython3 docs-blog/build_site.py\n```\n\n输出：\n\n```text\ndocs-blog/site-data.js\ndocs-blog/_public/\ndocs-blog/CNAME\n```\n\n`docs-blog/_public/` 是静态发布目录，已被 Git 忽略。\n\n`docs-blog/demos/visual-physics-proxy/` 里有超过 100MB 的本地 raw PLY 时，不要把 raw PLY 直接放进 Pages 发布产物。当前构建脚本会排除：\n\n```text\nbedroom_4_cli30k_graphdeco_clean_iteration30000.ply\nbedroom_4_scene_3dgs_repaired_supersplat.ply\n```\n\n线上使用 `assets/large-asset-manifest.json` 和 `assets/chunks/*.partNN` 分片发布。更新这些大资产时，先重新生成分片和 manifest，再运行 `python3 docs-blog/build_site.py` 检查 `_public`。\n\n## 新增文档\n\n1. 把项目主文档放到 `docs/`。\n2. 在文件顶部加 front matter：\n\n```markdown\n---\ntitle: 文档标题\ncategory: Research\nsummary: 一句话摘要。\ntags:\n  - 3DGS\n  - Mesh\n---\n```\n\n3. 运行：\n\n```bash\npython3 docs-blog/build_site.py\n```\n\n4. 打开 `docs-blog/index.html` 本地检查。\n\n## Markdown 支持\n\n文档站支持：\n\n- 标题。\n- 表格。\n- 代码块。\n- 本地图片。\n- 网络图片。\n- task list。\n- 折叠块。\n- Obsidian 风格内部链接。\n\n本地图片建议放在文档旁边或 `docs-blog/content/assets/`。构建脚本会复制可解析的本地图片。\n\n网络图片可以直接写在 Markdown 里：\n\n```markdown\n![SuGaR pipeline](https://anttwo.github.io/sugar/results/full_teaser.png \"图注文字\")\n```\n\n图片单独占一行时，页面会渲染成带图注和来源域名的 figure。外链图片会保留原图链接，点击可打开来源。\n\n## 本机 API\n\n默认 API URL：\n\n```text\nhttps://api.relumeow.top\n```\n\n本地开发时可运行：\n\n```bash\npython3 docs-blog/api_server.py\n```\n\n管理界面在：\n\n```text\ndocs-blog/admin/index.html\n```\n\nAPI 负责：\n\n- 用户登录和 session。\n- 管理员创建。\n- GitHub OAuth 登录。\n- 在线编辑和同步 Markdown。\n- 多项目记录。\n- Codex 任务队列。\n- 工作区文件浏览。\n- 管理员终端。\n\n## 安全边界\n\n远程控制功能必须保持以下边界：\n\n- 管理员功能需要登录。\n- workspace terminal 只能对可信用户开放。\n- runtime secrets 不进 Git。\n- `.env`、`docs-blog/runtime/`、密钥文件已被 `.gitignore` 排除。\n- 网站静态发布目录不应包含 runtime state。\n\n## Codex 同步文档\n\n推荐流程：\n\n```text\nedit docs/*.md\n  -> python3 docs-blog/build_site.py\n  -> inspect docs-blog/site-data.js / index.html\n  -> deploy static site\n```\n\n不要直接手写 `site-data.js`。它是构建产物。\n",
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
