window.V2M_BLOG_DATA = {
  "generatedAt": "2026-07-04 02:43",
  "site": {
    "route": "video2mesh",
    "title": "Video2Mesh Field Notes",
    "brand": "Video2Mesh",
    "mark": "V2M",
    "subtitle": "Field Notes",
    "description": "Video2Mesh 项目文档、调研和运行手册的静态博客网站。",
    "space": "/video2mesh 项目空间",
    "researchRoot": "docs/video2mesh/research-catalog/",
    "catalogCategory": "调研目录",
    "catalogStages": [
      {
        "key": "input-pose-pointcloud",
        "title": "输入、位姿与点云",
        "summary": "视频抽帧、COLMAP/MVS、learned pose fallback、稠密点云和坐标尺度合同。",
        "image": "assets/uploaded/input-pose-pointcloud/stage-input-pose.svg",
        "tags": [
          "COLMAP",
          "Point Cloud",
          "Pose"
        ]
      },
      {
        "key": "visual-3dgs",
        "title": "视觉重建 / 3DGS",
        "summary": "GraphDECO 3DGS、Spark、SuperSplat 和 visual proxy 的工程边界。",
        "image": "assets/v2m-docs-mark.svg",
        "tags": [
          "3DGS",
          "Spark",
          "SuperSplat"
        ]
      },
      {
        "key": "mesh-reconstruction",
        "title": "Mesh 重建",
        "summary": "COLMAP Delaunay、Poisson、GS2Mesh、SuGaR、2DGS/GOF 的阶段定位。",
        "image": "assets/uploaded/mesh-reconstruction/stage-mesh.svg",
        "tags": [
          "Mesh",
          "GS2Mesh",
          "SuGaR"
        ]
      },
      {
        "key": "pointcloud-completion",
        "title": "点云/背景补全",
        "summary": "点云清理、背景 clean plate、inpainting 与场景结构补全。",
        "image": "assets/uploaded/pointcloud-completion/stage-completion.svg",
        "tags": [
          "Completion",
          "Inpainting"
        ]
      },
      {
        "key": "object-mesh-completion",
        "title": "物体 Mesh 补全",
        "summary": "Hunyuan3D、Meshy、TRELLIS、InstantMesh、image-blaster object jobs。",
        "image": "assets/uploaded/pointcloud-completion/stage-completion.svg",
        "tags": [
          "Object Mesh",
          "image-blaster"
        ]
      },
      {
        "key": "semantic-scene-graph",
        "title": "语义与 Scene Graph",
        "summary": "SAM/Grounded-SAM、semantic splats、mesh face sidecar 和交互查询。",
        "image": "assets/uploaded/semantic-scene-graph/stage-semantics.svg",
        "tags": [
          "Semantics",
          "Scene Graph"
        ]
      },
      {
        "key": "collider-physics-proxy",
        "title": "Collider 与物理代理",
        "summary": "static collider、primitive proxy、convex decomposition 和 runtime physics。",
        "image": "assets/uploaded/object-simulation/stage-simulation.svg",
        "tags": [
          "Collider",
          "Physics"
        ]
      },
      {
        "key": "object-simulation",
        "title": "物体仿真",
        "summary": "rigid body、soft body、PhysSplat/Sim Anything 和 dynamic Gaussian。",
        "image": "assets/uploaded/object-simulation/stage-simulation.svg",
        "tags": [
          "Simulation",
          "PhysSplat"
        ]
      },
      {
        "key": "industrial-pipelines",
        "title": "工业资产管线",
        "summary": "World Labs / Icare、image-blaster、Spark viewer 和 GLB runtime 约定。",
        "image": "assets/uploaded/research-catalog/pipeline-overview.svg",
        "tags": [
          "World Labs",
          "Spark"
        ]
      },
      {
        "key": "experiments",
        "title": "本项目实验",
        "summary": "GS2Mesh、Open3D Poisson、COLMAP Delaunay、语义投影和 Web demo。",
        "image": "assets/uploaded/experiments/04-visual-physics-proxy-demo.png",
        "tags": [
          "Experiments",
          "Video2Mesh"
        ]
      }
    ],
    "readingPaths": [
      {
        "title": "从视频到资产",
        "tags": [
          "Pipeline",
          "Simulation"
        ],
        "query": "pipeline"
      },
      {
        "title": "调研目录",
        "tags": [
          "调研目录",
          "Research Catalog"
        ],
        "query": "mesh"
      },
      {
        "title": "项目文档",
        "tags": [
          "项目文档",
          "Video2Mesh"
        ],
        "query": "pipeline"
      },
      {
        "title": "进度目录",
        "tags": [
          "进度目录",
          "Weekly",
          "P0"
        ],
        "query": "weekly"
      }
    ]
  },
  "docs": [
    {
      "id": "research-catalog",
      "title": "场景扫描与可交互资产调研目录",
      "category": "调研目录",
      "research_stage": "research-catalog",
      "research_stage_title": "调研目录总览",
      "research_doc_role": "root",
      "visibility": "public",
      "summary": "按 Video2Mesh 流程阶段整理学术、工业和本项目实验路线，作为 relumeow.top 的可浏览调研目录入口。",
      "source_path": "docs/video2mesh/research-catalog/README.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "3DGS",
        "Mesh",
        "Simulation",
        "调研目录"
      ],
      "body": "\n# 场景扫描与可交互资产调研目录\n\n这个目录把本周调研内容按 Video2Mesh 的流程阶段重新组织。目标不是堆论文名，而是回答一个更工程化的问题：**从扫描视频到可交互仿真/游戏资产，每个阶段有哪些可借用模型、项目和产业方案，它们应该接在我们 pipeline 的什么位置。**\n\n![Video2Mesh 调研目录总览](assets/uploaded/research-catalog/pipeline-overview.svg \"Video2Mesh 从扫描视频到视觉层、mesh、补全、语义、碰撞代理、物体仿真和引擎适配的调研目录\")\n\n## 阶段目录\n\n| 阶段 | 子目录 | 主要关注 |\n|---|---|---|\n| 输入、位姿与点云 | [input-pose-pointcloud](input-pose-pointcloud/overview.md) | COLMAP、MASt3R/DUSt3R/VGGT、MVS、稠密点云、尺度和坐标合同 |\n| 视觉重建 / 3DGS | [visual-3dgs](visual-3dgs/overview.md) | GraphDECO 3DGS、Spark、SuperSplat、3DGS 作为 visual proxy |\n| Mesh 重建 | [mesh-reconstruction](mesh-reconstruction/overview.md) | COLMAP Delaunay、Poisson/Open3D、GS2Mesh、SuGaR、2DGS/GOF |\n| 点云/背景补全 | [pointcloud-completion](pointcloud-completion/overview.md) | 点云清理、背景 clean plate、inpainting、场景结构补全 |\n| 物体 Mesh 补全 | [object-mesh-completion](object-mesh-completion/overview.md) | Hunyuan3D、Meshy、TRELLIS、InstantMesh、image-blaster object jobs |\n| 语义与 Scene Graph | [semantic-scene-graph](semantic-scene-graph/overview.md) | SAM/Grounded-SAM、2D-to-3D fusion、semantic splats、face sidecar |\n| Collider 与物理代理 | [collider-physics-proxy](collider-physics-proxy/overview.md) | static collider、primitive proxy、convex decomposition、Rapier/Unity collision |\n| 物体仿真 | [object-simulation](object-simulation/overview.md) | rigid body、soft body、PhysSplat/Sim Anything、动态 Gaussian |\n| 工业资产管线 | [industrial-pipelines](industrial-pipelines/overview.md) | World Labs / Icare、image-blaster、Spark viewer、GLB runtime asset convention |\n| 本项目实验 | [experiments](experiments/overview.md) | GS2Mesh、Open3D Poisson、COLMAP Delaunay、语义投影、Web visual/physics proxy demo |\n\n## 当前总判断\n\nVideo2Mesh 的目标产物应是分层资产包，而不是一个全能 mesh：\n\n```text\nscan video\n  -> camera / dense geometry\n  -> 3DGS visual proxy\n  -> scene collider mesh\n  -> object visual mesh / completion\n  -> semantic face and object sidecar\n  -> physics proxy and material metadata\n  -> Web / Unity / MuJoCo / Isaac adapters\n```\n\n核心原则：\n\n- 3DGS / Spark / Splat 负责视觉真实感。\n- mesh / collider 负责碰撞、导航、点击和交互。\n- 语义应保存在 sidecar，而不是绑死在会被简化或替换的 mesh 里。\n- 物体补全、背景 clean plate、物理代理补全要拆开。\n- Sim Anything / PhysSplat 这类动态 Gaussian 方法值得跟踪，但短期不替代 mesh/collider 主链路。\n",
      "headings": [
        {
          "level": "2",
          "text": "阶段目录",
          "slug": "阶段目录"
        },
        {
          "level": "2",
          "text": "当前总判断",
          "slug": "当前总判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-project-docs-overview",
      "title": "Video2Mesh 项目文档 Overview",
      "category": "项目文档",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "Video2Mesh 项目文档入口，串联项目简介、pipeline 和运行方式。",
      "source_path": "docs/video2mesh/project-docs/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Video2Mesh",
        "项目文档"
      ],
      "body": "\n# Video2Mesh 项目文档 Overview\n\n这个目录只放项目当前对外可读的稳定说明，不混入旧调研长文和实验草稿。\n\n## 文档结构\n\n| 文档 | 解决的问题 |\n|---|---|\n| [项目简介](project-intro.md) | Video2Mesh 要做什么、产物分几层、和外部项目的边界在哪里 |\n| [Pipeline](pipeline.md) | 从扫描视频到 3DGS、mesh、语义、collider、simulator bundle 的流程合同 |\n| [如何运行](how-to-run.md) | 本地/远端常用命令、输出目录、验证方式和注意事项 |\n\n## 当前一句话\n\nVideo2Mesh 的目标不是输出单一 mesh，而是从真实扫描视频生成一组可被浏览器、Unity、MuJoCo、Isaac 等 runtime 消费的分层 3D 场景资产。\n",
      "headings": [
        {
          "level": "2",
          "text": "文档结构",
          "slug": "文档结构"
        },
        {
          "level": "2",
          "text": "当前一句话",
          "slug": "当前一句话"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-project-intro",
      "title": "Video2Mesh 项目简介",
      "category": "项目文档",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "说明 Video2Mesh 的目标、资产分层、当前边界和对外部方案的承接关系。",
      "source_path": "docs/video2mesh/project-docs/project-intro.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Video2Mesh",
        "3DGS",
        "Simulator",
        "项目文档"
      ],
      "body": "\n# Video2Mesh 项目简介\n\nVideo2Mesh 关注的是真实扫描视频到可交互 3D 资产的工程闭环。它不把 3DGS、mesh、语义、物理都压进一个文件，而是拆成多个互相对齐的层。\n\n## 目标产物\n\n```text\nscan video\n  -> camera / point cloud\n  -> 3DGS visual proxy\n  -> scene mesh / collider proxy\n  -> object visual mesh / completion\n  -> semantic sidecar / scene graph\n  -> physics metadata\n  -> Web / Unity / MuJoCo / Isaac adapters\n```\n\n## 分层原则\n\n| 层 | 代表产物 | 主要职责 |\n|---|---|---|\n| Visual | GraphDECO 3DGS、Spark/SuperSplat 可视化资产 | 真实感显示 |\n| Geometry | COLMAP dense mesh、Poisson mesh、object mesh | 重建、定位、对齐 |\n| Collision | static collider、primitive/convex proxy | 点击、移动、碰撞、导航 |\n| Semantic | object id、face label、probability splat、scene graph | 查询与交互逻辑 |\n| Physics | mass、friction、restitution、body type | 仿真引擎消费 |\n| Adapter | simulator asset bundle、Unity/MuJoCo/Isaac 输出 | runtime 集成 |\n\n## 边界\n\nWorld Labs / Marble、image-blaster、Hunyuan3D、Meshy、SuGaR、GS2Mesh 等都可以成为某一阶段的后端或参考，但 Video2Mesh 自己要承接统一坐标、语义、物理属性、资产索引和引擎适配。\n",
      "headings": [
        {
          "level": "2",
          "text": "目标产物",
          "slug": "目标产物"
        },
        {
          "level": "2",
          "text": "分层原则",
          "slug": "分层原则"
        },
        {
          "level": "2",
          "text": "边界",
          "slug": "边界"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-pipeline",
      "title": "Video2Mesh Pipeline",
      "category": "项目文档",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "按流程说明 Video2Mesh 从视频输入到可交互仿真资产的主要阶段和输出合同。",
      "source_path": "docs/video2mesh/project-docs/pipeline.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Pipeline",
        "COLMAP",
        "3DGS",
        "Mesh",
        "项目文档"
      ],
      "body": "\n# Video2Mesh Pipeline\n\n## 总流程\n\n```text\ninput video\n  -> extract frames\n  -> COLMAP / pose fallback\n  -> dense point cloud\n  -> GraphDECO 3DGS visual layer\n  -> 2D masks and tracking\n  -> 2D-to-3D semantic fusion\n  -> mesh reconstruction\n  -> object mesh completion\n  -> collider / physics proxy\n  -> simulator asset bundle\n  -> Web / Unity / MuJoCo / Isaac adapters\n```\n\n## 阶段合同\n\n| 阶段 | 输入 | 输出 | 当前建议 |\n|---|---|---|---|\n| 输入与位姿 | scan video | frames、cameras、sparse/dense points | COLMAP 主线，MASt3R/DUSt3R/VGGT 作为 fallback 调研 |\n| 视觉层 | posed images | 3DGS / splat | GraphDECO 3DGS，Spark/SuperSplat 做浏览器查看 |\n| Mesh 重建 | dense workspace / 3DGS renders / point cloud | GLB/PLY mesh | P0 用 COLMAP Delaunay collider，P1 做 per-object visual mesh |\n| 语义 | 2D masks、3D points、mesh | object ids、face sidecar | 保持 sidecar，不和 mesh topology 绑定死 |\n| 补全 | crops、masks、bbox、clean plate | 完整 object mesh / background asset | image-blaster、Hunyuan3D、Meshy、TRELLIS 等作为后端 |\n| 物理代理 | mesh、bbox、semantic label | collider、mass、friction、body type | static mesh + primitive/convex proxy 先跑通 |\n\n## 当前 P0 主链路\n\nP0 的目标是展示和交互闭环，不是最佳画质：COLMAP dense + Delaunay mesh 做场景 collider，GraphDECO 3DGS 做 visual layer，语义与物理属性通过 sidecar 管理。\n",
      "headings": [
        {
          "level": "2",
          "text": "总流程",
          "slug": "总流程"
        },
        {
          "level": "2",
          "text": "阶段合同",
          "slug": "阶段合同"
        },
        {
          "level": "2",
          "text": "当前 P0 主链路",
          "slug": "当前-p0-主链路"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-how-to-run",
      "title": "Video2Mesh 如何运行",
      "category": "项目文档",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "记录 Video2Mesh 当前常用运行入口、远端路径、输出目录和验证方式。",
      "source_path": "docs/video2mesh/project-docs/how-to-run.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Runbook",
        "CLI",
        "QA",
        "项目文档"
      ],
      "body": "\n# Video2Mesh 如何运行\n\n## 远端常用入口\n\n```bash\ncd /root/autodl-tmp/workspace/Video2Mesh\nsource /etc/network_turbo >/dev/null 2>&1 || true\nbash tools/run_video2mesh_quick.sh dataset/<video>.mp4\n```\n\n## 本地文档站\n\n```bash\npython3 docs-blog/build_site.py\npython3 -m http.server 4173 -d docs-blog/_public\n```\n\n公开站入口：`http://127.0.0.1:4173/video2mesh/`。管理端入口：`http://127.0.0.1:4173/admin/`。\n\n## 输出位置\n\n```text\nexports/<run>/\n  scene/\n  masks/\n  simulator_assets/\n  mesh_recon_results/\n  review_pack/\n```\n\n## 验证重点\n\n- `simulator_asset_bundle.json` 是否能索引所有资产。\n- visual layer 和 collider 是否在同一坐标系。\n- mesh 是否能被 Web/Unity 读取。\n- 语义标签是否能投到 object/face sidecar。\n- 大型 3DGS/PLY 不直接进入 GitHub Pages artifact。\n",
      "headings": [
        {
          "level": "2",
          "text": "远端常用入口",
          "slug": "远端常用入口"
        },
        {
          "level": "2",
          "text": "本地文档站",
          "slug": "本地文档站"
        },
        {
          "level": "2",
          "text": "输出位置",
          "slug": "输出位置"
        },
        {
          "level": "2",
          "text": "验证重点",
          "slug": "验证重点"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-progress-overview",
      "title": "Video2Mesh 进度目录 Overview",
      "category": "进度目录",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "Video2Mesh 当前 P0/P1 进度、周报和实验结果入口。",
      "source_path": "docs/video2mesh/progress/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Progress",
        "Weekly",
        "P0",
        "P1",
        "进度目录"
      ],
      "body": "\n# Video2Mesh 进度目录 Overview\n\n这个目录记录当前项目推进状态，包括优先级、阶段完成度、实验结论和周报材料。\n\n## 文档\n\n| 文档 | 内容 |\n|---|---|\n| [P0/P1 模块优先级](p0-p1-priority.md) | 当前路线、下一步、风险和验收标准 |\n| [2026-07-03 周报](weekly-2026-07-03.md) | 本周调研、mesh 实验、语义 mesh 新结果和下周计划 |\n",
      "headings": [
        {
          "level": "2",
          "text": "文档",
          "slug": "文档"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-p0-p1-priority",
      "title": "P0/P1 模块优先级",
      "category": "进度目录",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "记录 Video2Mesh 当前 P0/P1/P2 模块优先级、状态和下一步实验。",
      "source_path": "docs/video2mesh/progress/p0-p1-priority.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "P0",
        "P1",
        "Roadmap",
        "进度目录"
      ],
      "body": "\n# P0/P1 模块优先级\n\n## 当前优先级\n\n| 优先级 | 模块 | 当前状态 | 下一步 |\n|---|---|---|---|\n| P0 | 场景级 visual/collider 分层 | 已有 Web demo 验证，3DGS visual + COLMAP Delaunay collider 可分离 | 保持稳定，减少大资产发布压力 |\n| P0 | 场景级 static collider | COLMAP dense + Delaunay 效果最稳 | 加入 simplify、尺度检查和 face sidecar |\n| P0 | 语义 mesh | 新结果 `bedroom4_formal_semantic_mesh_results_20260703` 明显优于前一版 debug 投影 | 统计 face/object 覆盖率，接入评论周报展示 |\n| P1 | per-object visual mesh | GS2Mesh/SuGaR/Open3D/Poisson 已有对比 | 针对床、窗帘、桌椅做 object-local 重建 |\n| P1 | 物体补全 | image-blaster / Hunyuan3D / Meshy / TRELLIS 适合作为候选后端 | 选择一两个遮挡物体做回填对齐 |\n| P1 | 物体交互 | 需要 collider、semantic sidecar、physics metadata | 先做 rigid body/primitive proxy，再看 dynamic Gaussian |\n| P2 | Sim Anything / PhysSplat | 思想有价值，但模型/代码可用性不足 | 跟踪论文和复现，作为物理信息注入方向 |\n\n## 验收指标\n\n- visual layer 和 collider 在同一视角下不明显错位。\n- 公开文档能解释每个模块为什么在 P0 或 P1。\n- 语义 mesh 能在导师汇报中直观看出床、窗帘、地毯等主要物体区域。\n- 每个外部模型都有明确输入、输出、接入阶段和限制。\n",
      "headings": [
        {
          "level": "2",
          "text": "当前优先级",
          "slug": "当前优先级"
        },
        {
          "level": "2",
          "text": "验收指标",
          "slug": "验收指标"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-weekly-2026-07-03",
      "title": "周报 2026-07-03：场景扫描调研与 Mesh 重建实验",
      "category": "进度目录",
      "research_stage": "",
      "research_stage_title": "",
      "research_doc_role": "",
      "visibility": "public",
      "summary": "本周完成场景扫描学术/工业路线调研，测试多种 mesh 重建方法，新增 semantic mesh 正式结果，并实现 visual/physics proxy demo。",
      "source_path": "docs/video2mesh/progress/weekly-2026-07-03.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Weekly",
        "Mesh",
        "Semantic Mesh",
        "3DGS",
        "进度目录"
      ],
      "body": "\n# 周报 2026-07-03：场景扫描调研与 Mesh 重建实验\n\n## 本周总体进展\n\n本周主要围绕“扫描场景如何进入可交互仿真/游戏环境”推进两条线：一是调研学术界和工业界的场景扫描、3DGS、Mesh 和交互资产方案；二是在 Video2Mesh 项目中实际测试多种 mesh 重建路线，并基于“视觉代理、碰撞代理、物体语义分层”的思路实现初步 demo。\n\n当前判断是：项目不应追求从视频直接生成一个完美统一 mesh，而应输出分层资产包。3DGS 负责高质量视觉层，mesh/collider 负责碰撞和交互，语义和物理属性通过 sidecar 或 scene graph 单独管理。\n\n## 调研进展\n\n- 学术路线：COLMAP/MVS、3DGS、SuGaR、GS2Mesh、2DGS/GOF、TSDF/Poisson 等从图像或 3DGS 到 mesh 的方法。结论是传统 COLMAP dense + Delaunay/Poisson 更适合作为场景级静态碰撞代理；GS2Mesh 和 SuGaR 更适合做高质量 visual mesh 对照或后续升级，不适合作为 P0 主链路直接替代 collider。\n- 工业路线：学长文档、World Labs / Icare、image-blaster 等方案都倾向于把 3DGS/Spark/Splat 作为视觉代理，把 GLB mesh 或简化 collider 作为交互代理。World Labs 更偏 static world/background 生成，image-blaster 更偏 object mesh generation 和浏览器查看约定，最终 simulator asset bundle、物理属性和引擎适配仍需要 Video2Mesh 自己承接。\n\n## Mesh 重建实验\n\n### GS2Mesh\n\n![GS2Mesh 输出效果](assets/uploaded/video2mesh-weekly-2026-07-03/01-gs2mesh.png \"GS2Mesh 输出保留床、窗帘和大结构，但墙面破碎、漂浮片和局部缺失仍明显\")\n\nGS2Mesh raw mesh 约 4.48M vertices / 8.09M triangles，原始文件约 333MB；减面后可以得到几 MB 级 GLB。结构比直接 Gaussian center Poisson 更合理，但墙面破碎和漂浮片仍明显。\n\n### Open3D Poisson / 3DGS 点云\n\n![Open3D Poisson 3DGS alpha005 sample500k](assets/uploaded/video2mesh-weekly-2026-07-03/02-open3d-poisson-3dgs-alpha005-sample500k.png \"Open3D Poisson 输出体量可控，但壳状伪影、粘连和漂浮面明显\")\n\n`alpha005_sample500k` 路线输入 50 万点，输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。适合快速 baseline 或 fallback，不应把 3DGS center 当成最终真实表面。\n\n### COLMAP Delaunay Dense\n\n![COLMAP Delaunay dense mesh](assets/uploaded/video2mesh-weekly-2026-07-03/03-colmap-delaunay-dense.png \"COLMAP Delaunay dense mesh 更适合场景级 static collision proxy\")\n\n输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB。视觉细节不如 3DGS，但作为 static collider 更稳定，是当前 P0 场景级碰撞代理推荐路线。\n\n### 语义投影融合 Debug\n\n![mesh 语义投影融合调试结果](assets/uploaded/video2mesh-weekly-2026-07-03/05-mesh-semantic-transfer-ray-projection.png \"P1 ray projection debug 覆盖更高，但床、墙、窗帘、地面之间存在明显串色\")\n\n早期 P1 ray projection 使用 projected semantic point label masks 做 debug，缺少真实 SAM/GDINO 2D masks，因此串色明显、置信度偏低。\n\n### 正式 Semantic Mesh 新结果\n\n![bedroom4 formal semantic mesh](assets/uploaded/video2mesh-weekly-2026-07-03/06-bedroom4-formal-semantic-mesh.png \"新训练输出 bedroom4_formal_semantic_mesh_results_20260703 的语义 mesh，床、窗帘、墙面挂画/窗帘、地毯等主要区域已经能较清楚区分\")\n\n新训练输出结果位于 `bedroom4_formal_semantic_mesh_results_20260703`。相比前一版 debug 投影，这版 semantic mesh 的主要物体区域明显更清楚，床、窗帘/绿色大面、蓝色物体、地毯和小物件能够被颜色区分，已经可以作为周报正向结果展示。\n\n## Demo 进展\n\n![视觉代理 3DGS + 碰撞代理 mesh Demo](assets/uploaded/video2mesh-weekly-2026-07-03/04-visual-physics-proxy-demo.png \"Web demo 验证了 3DGS visual layer 与 mesh collision layer 可以分离\")\n\n基于视觉代理、碰撞代理、物体语义分层的思想，实现了 `visual-physics-proxy` demo。3DGS 只负责视觉显示，COLMAP Delaunay GLB 作为隐藏 collider 承担 raycast、ground probe 和移动阻挡。\n\n## 下一步\n\n- 进一步探索 per-object mesh 重建，优先床、窗帘、桌椅等主要物体。\n- 研究残缺物体补全，重点比较 image-blaster、Hunyuan3D、Meshy、TRELLIS、InstantMesh。\n- 把 semantic mesh 的 face/object sidecar 接到 collider 和 Web 交互上。\n- 做物体交互 demo，先从刚体和 primitive/convex proxy 开始。\n- 跟踪 Sim Anything / PhysSplat 为 3DGS 注入物理仿真信息的方向，但短期不替代 mesh/collider 主链路。\n",
      "headings": [
        {
          "level": "2",
          "text": "本周总体进展",
          "slug": "本周总体进展"
        },
        {
          "level": "2",
          "text": "调研进展",
          "slug": "调研进展"
        },
        {
          "level": "2",
          "text": "Mesh 重建实验",
          "slug": "mesh-重建实验"
        },
        {
          "level": "3",
          "text": "GS2Mesh",
          "slug": "gs2mesh"
        },
        {
          "level": "3",
          "text": "Open3D Poisson / 3DGS 点云",
          "slug": "open3d-poisson-3dgs-点云"
        },
        {
          "level": "3",
          "text": "COLMAP Delaunay Dense",
          "slug": "colmap-delaunay-dense"
        },
        {
          "level": "3",
          "text": "语义投影融合 Debug",
          "slug": "语义投影融合-debug"
        },
        {
          "level": "3",
          "text": "正式 Semantic Mesh 新结果",
          "slug": "正式-semantic-mesh-新结果"
        },
        {
          "level": "2",
          "text": "Demo 进展",
          "slug": "demo-进展"
        },
        {
          "level": "2",
          "text": "下一步",
          "slug": "下一步"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-collider-physics-proxy-convex-decomposition",
      "title": "Convex Decomposition",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "V-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/convex-decomposition.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Convex Decomposition\n\n![Convex decomposition](../assets/stage-collider.svg \"Convex decomposition 把复杂物体拆成多个凸体，适合动态刚体和可抓取物体\")\n\n## 链接\n\n- V-HACD GitHub: https://github.com/kmammou/v-hacd\n- CoACD project: https://colin97.github.io/CoACD/\n- CoACD GitHub: https://github.com/SarahWeiii/CoACD\n- CoACD Rust wrapper: https://github.com/Jondolf/CoACD-rs\n\n## 摘要要点\n\nConvex decomposition 把复杂 mesh 拆成多个凸体，让物理引擎能稳定处理动态刚体。V-HACD 是常见工程方案；CoACD 更强调 collision-aware concavity，希望用更少凸部件保留碰撞条件，适合游戏和交互应用。\n\n对 Video2Mesh 来说，它不是场景级 static collider 的替代品，而是 object-level dynamic collider 的候选。床、柜子这种大型静态物体未必需要拆很多凸体；可移动椅子、盒子、杯子、小摆件更适合用 convex compound。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object mesh cleanup | 先去飞面、封孔、减面，避免分解结果过碎 |\n| convex decomposition | 用 V-HACD/CoACD 拆为多个 convex hull |\n| hull filtering | 去掉太小或重叠严重的 hull |\n| physics binding | 写入 compound collider、mass、friction、restitution |\n| runtime QA | 检查穿透、稳定性和帧率 |\n\n## 输入与输出\n\n输入：object mesh、object bbox、类别和是否可移动。输出：convex hull compound、collider sidecar、运行时可用的动态刚体代理。\n\n## 在 Video2Mesh 中的位置\n\nP1 动态物体 collider。它可以接在 object split 或 Hunyuan3D/image-blaster object mesh 回填之后，作为 visual mesh 的物理替代层。\n\n## 接入判断\n\n- P0：不进入，P0 static collider 不需要复杂分解。\n- P1：用于可移动物体和 object completion 输出。\n- 风险：输入 mesh 质量差会导致 hull 过多或形状异常，需要限制 hull 数量和最小体积。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-collider-physics-proxy-mujoco-isaac",
      "title": "MuJoCo / Isaac",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "MuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的 body、joint、mass、friction、scale 合同。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/mujoco-isaac.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# MuJoCo / Isaac\n\n![MuJoCo / Isaac](../assets/stage-collider.svg \"MuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的资产合同\")\n\n## 链接\n\n- MuJoCo modeling docs: https://mujoco.readthedocs.io/en/stable/modeling.html\n- MuJoCo XML reference: https://mujoco.readthedocs.io/en/stable/XMLreference.html\n- Isaac Sim physics docs: https://docs.isaacsim.omniverse.nvidia.com/latest/physics/index.html\n- Isaac Sim physics fundamentals: https://docs.isaacsim.omniverse.nvidia.com/4.5.0/physics/simulation_fundamentals.html\n\n## 简介\n\nMuJoCo 和 Isaac 更偏机器人、物理仿真和可控实验环境，比 Web viewer 更严格。它们需要明确的 body tree、joint、geom/collider、mass、inertia、friction、contact 参数、scale 和坐标约定。视觉 mesh 可以作为展示资产，但仿真是否稳定主要看 collider 和物理参数。\n\n这条线提醒 Video2Mesh：最终 simulator asset bundle 必须是结构化资产包，而不是简单的 mesh 文件集合。\n\n## Pipeline\n\n| 阶段 | MuJoCo | Isaac / USD |\n|---|---|---|\n| scene asset | MJCF worldbody / mesh assets | USD stage / prim hierarchy |\n| collision | geom / mesh / primitive | CollisionAPI / PhysX collision shapes |\n| dynamics | body mass, inertia, joint, contact | RigidBodyAPI, joints, material, solver params |\n| export adapter | XML / MJCF | USD / Python config |\n\n## 输入与输出\n\n输入：Video2Mesh simulator asset bundle、visual mesh、collider、body type、material、mass/friction metadata。输出：MJCF/XML、USD/Isaac adapter、仿真可加载的 body/collider/physics 配置。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2 仿真适配。当前阶段先把 `simulator_asset_bundle.json` 的结构做扎实：每个 object 必须知道 visual、collider、pose、scale、body type、material 和来源置信度。MuJoCo/Isaac adapter 之后再消费这份 bundle。\n\n## 接入判断\n\n- P0：不阻塞，P0 先保证 collider/semantic sidecar。\n- P1：生成基础 adapter，验证可加载。\n- P2：做机器人/物理任务级 QA。\n- 风险：VLM 自动推断物理参数只能做初稿，仿真稳定性必须实测。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "collider-physics-proxy",
      "title": "Collider 与物理代理阶段",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "整理 static collider、primitive proxy、convex decomposition、Rapier/Unity 交互代理在 Video2Mesh 中的职责。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Collider",
        "Physics",
        "Unity",
        "调研目录"
      ],
      "body": "\n# Collider 与物理代理阶段\n\n碰撞代理的目标不是“看起来最真实”，而是“交互稳定、体量可控、运行时可消费”。这也是学长文档、World Labs / Icare、image-blaster viewer 给出的共同工程信号。\n\n## 主要方法和项目\n\n| 方法 / 项目 | 简介 | 适合对象 | Video2Mesh 用法 |\n|---|---|---|---|\n| Static triangle mesh collider | 简化后的 GLB/mesh 作为静态环境碰撞 | 地面、墙体、大型静态家具、房间壳体 | COLMAP Delaunay / Poisson mesh -> simplified GLB |\n| Primitive fitting | box、capsule、sphere、cylinder 等基本形体 | 桌、柜、床、椅腿、花盆等 | 物体交互 P1 的首选 collider |\n| Convex hull / convex decomposition | 用凸包或多个 convex parts 近似复杂物体 | 可移动刚体、可抓取物体 | 后续可接 CoACD / V-HACD |\n| Rapier | Web 端物理引擎 | 浏览器 demo 和 image-blaster-style viewer | 可加载 GLB collider 或 primitive rigid body |\n| Unity MeshCollider / Rigidbody | Unity 运行时物理组件 | 项目引擎适配 | static 用 concave mesh，dynamic 优先 convex/compound |\n| MuJoCo / Isaac | 仿真环境 | 机器人和物理仿真 | 需要质量、摩擦、joint、body type 等 metadata |\n\n## 推荐策略\n\n| 资产 | 推荐 collider |\n|---|---|\n| 房间地面/墙体 | static simplified mesh |\n| 床/柜/桌等大型静态家具 | box / convex hull / compound primitive |\n| 可移动小物体 | primitive / convex decomposition |\n| 布料、枕头、植物叶片 | visual mesh + soft/dynamic side route，不直接用复杂 concave collider |\n\n## 和视觉层的关系\n\n```text\n3DGS visual layer\n  -> visible only\n\ncollider mesh / primitive proxy\n  -> raycast\n  -> ground probe\n  -> movement blocking\n  -> physics body\n```\n\n本项目 Web demo 已验证：3DGS 视觉层可以完全不参与 raycast，隐藏的 COLMAP Delaunay GLB collider 仍能承担点击、地面探测和移动阻挡。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要方法和项目",
          "slug": "主要方法和项目"
        },
        {
          "level": "2",
          "text": "推荐策略",
          "slug": "推荐策略"
        },
        {
          "level": "2",
          "text": "和视觉层的关系",
          "slug": "和视觉层的关系"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-collider-physics-proxy-primitive-fitting",
      "title": "Primitive Fitting",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/primitive-fitting.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Primitive Fitting\n\n![Primitive fitting](../assets/stage-collider.svg \"Primitive fitting 用 box、plane、sphere、capsule、cylinder 等形体给物体生成稳定交互代理\")\n\n## 链接\n\n- Unity collider types: https://docs.unity3d.com/6000.0/Documentation/Manual/collider-types-introduction.html\n- Rapier colliders: https://rapier.rs/docs/user_guides/javascript/colliders\n- Open3D bounding boxes: https://www.open3d.org/docs/latest/python_api/open3d.geometry.OrientedBoundingBox.html\n\n## 简介\n\nPrimitive fitting 是把床、桌、柜、墙、门、地面等对象拟合成 box、plane、sphere、capsule、cylinder 或少量组合体。它牺牲外观细节，但换来物理稳定、求解快、体量小、易编辑。\n\n这条路线尤其适合 Video2Mesh 的 P1 object interaction：很多室内物体不需要每个凹凸都参与碰撞。床可以用 box + support surface，桌子可以用 tabletop box + leg cylinders，墙面/地面可以用 planes 或 thin boxes，小物体可先用 bbox/convex hull。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| semantic object split | 从 face sidecar 或 point mask 得到物体局部几何 |\n| bbox / plane estimation | 估计 AABB/OBB、support plane、principal axes |\n| primitive selection | 根据类别和形状选择 box/cylinder/sphere/capsule/plane |\n| fit and validate | 对齐尺度、支撑面、交互范围 |\n| export sidecar | 写入 collider type、params、pose、material |\n\n## 输入与输出\n\n输入：语义点云、object mesh split、bbox、物体类别和支撑关系。输出：primitive collider、局部 pose、物理参数初稿。\n\n## 在 Video2Mesh 中的位置\n\nP1 object collider，适合刚体交互。正式 semantic mesh 已经可以拆出 bed、window、floor、wall、door、nightstand、curtain、lamp 等对象，下一步就是对 bed/nightstand/floor/wall 先做 primitive fitting，再把小物体留给 convex decomposition 或 object mesh completion。\n\n## 接入判断\n\n- P0：不阻塞 P0，但 floor/wall primitive 可以作为快速 fallback。\n- P1：进入 object interaction 主线。\n- 风险：自动类别判断可能错，需要可视化审核和人工纠错入口。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-collider-physics-proxy-rapier-unity",
      "title": "Rapier / Unity Physics",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Rapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/rapier-unity.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "Unity",
        "调研目录"
      ],
      "body": "\n# Rapier / Unity Physics\n\n![Rapier / Unity Physics](../assets/stage-collider.svg \"Rapier 用于 Web demo，Unity Physics/PhysX 用于引擎侧交互验证\")\n\n## 链接\n\n- Rapier JavaScript docs: https://rapier.rs/docs/user_guides/javascript/rigid_bodies/\n- React Three Rapier: https://github.com/pmndrs/react-three-rapier\n- Unity Mesh Collider manual: https://docs.unity3d.com/6000.2/Documentation/Manual/mesh-colliders-introduction.html\n- Unity Rigidbody collider rules: https://docs.unity3d.com/6000.0/Documentation/Manual/rigidbody-configure-colliders.html\n\n## 简介\n\nRapier 适合 Web demo 和 Three.js 场景中的实时碰撞；Unity Physics/PhysX 适合后续引擎集成和更完整的游戏交互。二者都强调同一个工程事实：rigid body 和 collider 是分离概念，动态刚体通常不能直接使用复杂 concave mesh。\n\n因此 Video2Mesh 的导出不能只给一个漂亮 GLB，而要同时给 visual mesh、collider、body type、mass、friction、restitution、pose、scale 和 material hints。\n\n## Pipeline\n\n| 阶段 | Web / Rapier | Unity |\n|---|---|---|\n| visual layer | Three.js / Spark / GLB | MeshRenderer / Splat renderer |\n| collider layer | trimesh/static、cuboid、ball、capsule、convex hull | MeshCollider static、Box/Capsule/Sphere、Convex MeshCollider |\n| physics metadata | rigid body type、friction、restitution | Rigidbody、PhysicMaterial、layer |\n| QA | raycast、ground probe、movement blocking | play mode collision、CharacterController、rigidbody stability |\n\n## 输入与输出\n\n输入：collider mesh/primitive、body type、material、object pose。输出：runtime collision、raycast result、movement blocking、rigid body response。\n\n## 在 Video2Mesh 中的位置\n\nP1 runtime 集成验证。本周 visual/physics proxy demo 已经验证浏览器里可以让 visual layer 和 collider layer 分开：可见的是 3DGS/visual mesh，交互查询和碰撞走隐藏 mesh 或 primitive。\n\n## 接入判断\n\n- P0：Web demo 可以先用 static collider + raycast 验证。\n- P1：进入 object interaction 和 Unity adapter。\n- 风险：同一个 mesh 在 Web/Unity/MuJoCo/Isaac 的坐标轴和 collider 限制不同，需要 adapter 层显式转换。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-collider-physics-proxy-static-mesh-collider",
      "title": "Static Mesh Collider",
      "category": "调研目录",
      "research_stage": "collider-physics-proxy",
      "research_stage_title": "Collider 与物理代理",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/static-mesh-collider.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Static Mesh Collider\n\n![Static mesh collider](../assets/stage-collider.svg \"Static mesh collider 用简化三角网格承担房间地面、墙面和大型静态结构的碰撞\")\n\n## 链接\n\n- Unity Mesh Collider manual: https://docs.unity3d.com/6000.2/Documentation/Manual/mesh-colliders-introduction.html\n- Rapier colliders: https://rapier.rs/docs/user_guides/javascript/colliders\n- OpenUSD rigid body physics proposal: https://openusd.org/release/wp_rigid_body_physics.html\n\n## 简介\n\n场景级 static mesh collider 用一个简化三角网格承担地面、墙体、点击、导航边界和粗碰撞。它的目标不是视觉精美，而是稳定、轻量、尺度正确、能被 Web/Unity/MuJoCo/Isaac 等运行时消费。\n\nStatic mesh collider 适合房间壳体、地面、墙面、大型固定家具等“不需要被刚体求解器推动”的对象。动态物体不应直接使用复杂 concave mesh，而应走 primitive、convex hull 或 convex decomposition。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| scene mesh source | COLMAP Delaunay / cleaned Poisson / simplified mesh |\n| cleanup | 移除飞面、孤立分量、过薄结构和远端噪声 |\n| simplification | decimate 到 Web/engine 可消费体量 |\n| export | GLB/OBJ/PLY + coordinate metadata |\n| runtime binding | 作为 hidden collider，visual layer 仍由 3DGS 或 visual mesh 显示 |\n\n## 输入与输出\n\n输入：COLMAP Delaunay、Poisson 或其他场景级 mesh。输出：简化后的 GLB collider、face/material sidecar、scale/axis metadata。\n\n## 在 Video2Mesh 中的位置\n\nP0 必需，优先稳定和轻量。本周 formal semantic mesh 结果里，COLMAP Delaunay local transfer 的 82,920 vertices / 167,082 faces 规模适中，语义覆盖 84.98%，比 GS2Mesh 和 Open3D Poisson 更适合作为 static collider 基线。\n\n## 接入判断\n\n- P0：必须进入，先服务地面探测、点击和移动阻挡。\n- P1：叠加 semantic face sidecar 和 object split。\n- 风险：不要把 visual mesh 的破碎表面直接作为物理真实几何，需要清理和简化。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-colmap-delaunay-experiment",
      "title": "COLMAP Delaunay Dense 实验",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "COLMAP dense + Delaunay mesher 生成场景级 mesh。",
      "source_path": "docs/video2mesh/research-catalog/experiments/colmap-delaunay-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP Delaunay Dense 实验\n\n![COLMAP Delaunay dense mesh](assets/uploaded/video2mesh-experiments-colmap-delaunay-experiment/03-colmap-delaunay-dense.png \"COLMAP Delaunay dense mesh 视觉细节不如 3DGS，但几何轻量稳定，更适合场景级 static collision proxy\")\n\n## 实验目的\n\nCOLMAP dense + Delaunay mesher 生成场景级 mesh，用来验证传统 MVS mesh 能否作为 Video2Mesh 的 P0 static collider。\n\n## 输入与输出\n\n| 项目 | 数值/说明 |\n|---|---|\n| 输入 | COLMAP dense fused point cloud |\n| 输出 | 82,920 vertices / 167,082 triangles |\n| GLB | 约 3.0MB |\n| formal semantic local transfer | 141,993 / 167,082 faces assigned |\n| semantic coverage | 84.98% |\n| object split | 16 个 object/local mesh |\n\n## 在 Video2Mesh 中的位置\n\n当前最适合 P0 static collider。它视觉上不如 3DGS/GS2Mesh，但作为碰撞代理有三个优势：轻量、拓扑更连续、可直接进入 GLB/physics runtime。formal semantic mesh 结果也说明它能承载 per-face semantic sidecar。\n\n在下一步交互 demo 里，它应当作为隐藏 collider；视觉层仍由 3DGS/Splat 或 visual mesh 承担。\n\n## 接入判断\n\n- P0：进入主链路，作为 static mesh collider。\n- P1：结合 semantic sidecar 支持点击查询、object split、可交互代理。\n- 风险：视觉细节不足，不能单独替代 3DGS visual layer。\n",
      "headings": [
        {
          "level": "2",
          "text": "实验目的",
          "slug": "实验目的"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-formal-semantic-mesh-20260703",
      "title": "正式 Semantic Mesh 结果 20260703",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。",
      "source_path": "docs/video2mesh/research-catalog/experiments/formal-semantic-mesh-20260703.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 正式 Semantic Mesh 结果 20260703\n\n![bedroom4 formal semantic mesh](assets/uploaded/video2mesh-experiments-formal-semantic-mesh-20260703/06-bedroom4-formal-semantic-mesh.png \"正式 bedroom4 semantic mesh：相较早期 ray projection debug，主要语义区域更清晰，适合作为周报展示结果\")\n\n## 结果路径\n\n- 本地 compact delivery: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`\n- 原远端 export root: `/root/autodl-tmp/workspace/Video2Mesh/exports/bedroom_4_cli_colmap_dense_graphdeco30k_47_56_20260702_024145`\n- 总结文件：`mesh_recon_results/semantic_bedroom4_formal_delivery/semantic_mesh_summary.json`\n- 物体拆分总结：`mesh_recon_results/object_mesh_splits/object_mesh_split_summary.json`\n\n## 输入与输出摘录\n\n这次不是 smoke/debug 版本，而是 bedroom_4 formal run。流程里包含 GroundingDINO object discovery、SAM/SAM2 tracking、3D object masks、semantic dense/3DGS manifest，以及多条 mesh semantic transfer 路线。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| COLMAP / GraphDECO base | 使用 bedroom_4 COLMAP dense 和 GraphDECO 30k 结果作为几何与视觉输入 |\n| object discovery / tracking | GroundingDINO 发现候选物体，SAM/SAM2 跨帧生成 object masks |\n| semantic 3D evidence | 生成 semantic dense/3DGS manifest、3D object masks 和 semantic splats |\n| mesh reconstruction routes | 对 COLMAP Delaunay、Open3D Poisson、GS2Mesh decim mesh 分别做语义 transfer |\n| face sidecar / object split | 输出 per-face semantics、coverage 统计和 object mesh splits |\n\n| 路线 | Mesh | Face | 已赋语义 face | 覆盖率 | object split |\n|---|---:|---:|---:|---:|---:|\n| COLMAP dense Delaunay + local semantic transfer | 82,920 vertices | 167,082 | 141,993 | 84.98% | 16 |\n| COLMAP dense Delaunay + projected splats | 82,920 vertices | 167,082 | 133,876 | 80.13% | 15 |\n| Open3D Poisson dense fused voxel10 | 100,705 vertices | 199,999 | 64,410 | 32.21% | 15 |\n| GS2Mesh decim100k | 43,734 vertices | 120,144 | 66,667 | 55.49% | 13 |\n\nCOLMAP dense Delaunay local transfer 是当前最适合 P0/P1 之间衔接的路线：几何足够轻，语义覆盖高，能导出 object mesh split。Top labels 里 bed 占 40.82% faces，window 占 13.80%，floor 占 12.57%，wall/door/nightstand/curtain 等也都有可见分配。\n\n## 在 Video2Mesh 中的位置\n\n这版结果说明“mesh + semantic sidecar”已经可作为下一步交互资产的基础：\n\n- scene collider：优先用 COLMAP Delaunay GLB/Ply，稳定且轻。\n- semantic sidecar：使用 `mesh_mesh_semantics_local.json` 存 per-face semantic/object id。\n- object mesh split：从 face semantics 拆出 bed、window、floor、wall、door、nightstand、curtain、lamp 等物体局部 mesh。\n- simulator asset bundle：下一步把 object mesh split 与 body_type、collider、mass、friction/restitution 合并。\n\n## 输出结果判断\n\n从图上看，床、窗户/窗帘、地面、墙面挂画、小桌/灯等主要区域已经比早期 ray projection debug 清楚，能够作为周报正向结果展示。问题仍然在于细小物体和薄结构的边界会抖动；Open3D Poisson 的 unknown/background 比例过高，不适合做主语义 mesh。\n\n## 下一步\n\n- 把 `mesh_mesh_semantics_local.json` 接入 Web viewer，点击 face 或 raycast 时返回 object/label。\n- 用 object split 生成 per-object bbox 和 collider candidates。\n- 给 object split 加质量统计：闭合性、连通分量、face area、bbox 尺寸。\n- 对 bed/nightstand/curtain 做 object completion 对照，测试 Hunyuan3D/image-blaster 回填。\n\n## 接入判断\n\n- P0：COLMAP Delaunay mesh 可以作为 static collider；semantic sidecar 可作为可选增强。\n- P1：object split 和 per-face semantics 应进入下一步交互 demo。\n- 风险：semantic transfer 的可信度依赖 2D masks 和空间距离阈值，仍需可视化审核和人工纠错入口。\n",
      "headings": [
        {
          "level": "2",
          "text": "结果路径",
          "slug": "结果路径"
        },
        {
          "level": "2",
          "text": "输入与输出摘录",
          "slug": "输入与输出摘录"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果判断",
          "slug": "输出结果判断"
        },
        {
          "level": "2",
          "text": "下一步",
          "slug": "下一步"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-gs2mesh-experiment",
      "title": "GS2Mesh 实验",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。",
      "source_path": "docs/video2mesh/research-catalog/experiments/gs2mesh-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GS2Mesh 实验\n\n![GS2Mesh 输出效果](assets/uploaded/video2mesh-experiments-gs2mesh-experiment/01-gs2mesh.png \"本项目 GS2Mesh 输出：床、窗帘和大结构保留较好，但墙面破碎、漂浮片和局部缺失仍明显\")\n\n## 实验目的\n\n本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。目标不是立刻替代 collider，而是验证：如果把 3DGS 渲染和 depth fusion 接起来，是否能得到比 Gaussian center Poisson 更像真实表面的 mesh。\n\n## 输入与输出\n\n| 项目 | 数值/说明 |\n|---|---|\n| 输入 | GraphDECO 3DGS 30k iteration 训练结果 |\n| 路线 | `gs2mesh_cli30k_voxel10_baseline0p5` |\n| raw mesh | 约 4.48M vertices / 8.09M triangles |\n| raw 文件 | 约 333MB |\n| formal decim mesh | `gs2mesh_decim100000.ply`，43,734 vertices / 120,144 faces |\n| semantic transfer | local transfer 覆盖 55.49%，13 个 object split |\n\n## 在 Video2Mesh 中的位置\n\n效果能保留床、窗帘和大结构，但仍有墙面破碎、漂浮片和局部缺失。它比 Open3D Poisson 更像 visual mesh，但当前仍不如 COLMAP Delaunay 稳定适合作为 P0 collider。\n\nformal semantic run 里，GS2Mesh decim100k 的语义 transfer 覆盖率为 55.49%，主要标签包括 window、bed、floor、wall、door、lamp、nightstand 等。它可以用于检查“高质量 visual mesh 路线能否承载语义 sidecar”，但还不能作为最终交互资产的唯一来源。\n\n## 接入判断\n\n- P0：不进入主 collider。\n- P1：保留为 visual mesh 对照和 object-level mesh 实验候选。\n- 下一步：尝试只对 foreground object 或 crop 区域运行，降低场景级噪声。\n",
      "headings": [
        {
          "level": "2",
          "text": "实验目的",
          "slug": "实验目的"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-open3d-poisson-experiment",
      "title": "Open3D Poisson 实验",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "使用过滤后的 3DGS center point cloud 做 Poisson baseline。",
      "source_path": "docs/video2mesh/research-catalog/experiments/open3d-poisson-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D Poisson 实验\n\n![Open3D Poisson 3DGS alpha005 sample500k](assets/uploaded/video2mesh-experiments-open3d-poisson-experiment/02-open3d-poisson-3dgs-alpha005-sample500k.png \"Open3D Poisson 输出体量可控，但壳状伪影、粘连和漂浮面明显\")\n\n## 实验目的\n\n使用过滤后的 3DGS center point cloud 做 Poisson baseline，验证“直接把 Gaussian center 当点云重建 mesh”是否足够作为 Video2Mesh fallback。\n\n## 输入与输出\n\n| 项目 | 数值/说明 |\n|---|---|\n| 输入 | `alpha005_sample500k`，50 万个 3DGS center samples |\n| 输出 | 约 100,965 vertices / 200,000 triangles |\n| GLB | 约 5.23MB |\n| formal semantic run | 100,705 vertices / 199,999 faces |\n| semantic coverage | 32.21%，unknown/background 67.79% |\n\n## 在 Video2Mesh 中的位置\n\n适合 fallback/debug，不适合最终 surface。它的问题不是文件大小，而是几何语义都不够稳定：3DGS center 并不等于真实表面，因此 Poisson 会产生壳状伪影、粘连、漂浮面和大量 unknown/background。\n\n## 接入判断\n\n- P0：不作为主 collider。\n- P1：保留 debug/fallback，帮助检查点云清理、bbox crop 和 postprocess 参数。\n- 风险：semantic transfer 覆盖低，不能用它代表正式 semantic mesh 质量。\n",
      "headings": [
        {
          "level": "2",
          "text": "实验目的",
          "slug": "实验目的"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "experiments",
      "title": "本项目实验目录",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "汇总 Video2Mesh 本周在 bedroom 场景上的 GS2Mesh、Open3D Poisson、COLMAP Delaunay、语义投影融合和 Web Demo 实验。",
      "source_path": "docs/video2mesh/research-catalog/experiments/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Experiments",
        "Video2Mesh",
        "Mesh",
        "调研目录"
      ],
      "body": "\n# 本项目实验目录\n\n本目录汇总本周在 Video2Mesh bedroom 场景上的真实实验结果。它和前面的调研目录对应：不是只看论文效果，而是看这些方法接到我们自己的 pipeline 后能不能形成可用资产。\n\n## 实验一：GS2Mesh\n\nGS2Mesh 路线从训练好的 3DGS 出发，通过渲染多视角/双目深度再做 TSDF 融合。实测 raw mesh 约 4.48M vertices / 8.09M triangles，原始文件约 333MB；减面后可以得到几 MB 级别 GLB。结构比直接 Gaussian center Poisson 更合理，但墙面破碎和漂浮片仍明显。\n\n![GS2Mesh 输出效果](assets/uploaded/experiments/01-gs2mesh.png \"GS2Mesh 输出保留了床、窗帘和大结构，但仍有墙面破碎、漂浮片和局部缺失\")\n\n结论：适合作为 P1/P2 object visual mesh 或 benchmark，不适合作为 P0 lightweight collider。\n\n## 实验二：Open3D Poisson / 3DGS 点云\n\nOpen3D Poisson 使用过滤后的 3DGS center point cloud。`alpha005_sample500k` 路线输入 50 万点，输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。\n\n![Open3D Poisson 3DGS alpha005 sample500k](assets/uploaded/experiments/02-open3d-poisson-3dgs-alpha005-sample500k.png \"Open3D Poisson 输出体量可控，但壳状伪影、粘连和漂浮面明显\")\n\n结论：适合快速 baseline 或 fallback；不应把 3DGS center 当作最终真实表面。\n\n## 实验三：COLMAP Delaunay Dense\n\nCOLMAP dense + Delaunay mesher 输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB。视觉细节不如 3DGS，但作为 static collider 更稳定。\n\n![COLMAP Delaunay dense mesh](assets/uploaded/experiments/03-colmap-delaunay-dense.png \"COLMAP Delaunay dense mesh 更适合场景级 static collision proxy\")\n\n结论：当前最适合作为 P0 场景级碰撞代理。\n\n## 实验四：语义投影融合\n\n本周尝试 P0 KDTree 语义回灌和 P1 ray projection 多视角投票。P1 当前使用 projected semantic point label masks 做 debug，缺少真实 SAM/GDINO 2D masks，因此串色明显、置信度偏低。\n\n![mesh 语义投影融合调试结果](assets/uploaded/experiments/05-mesh-semantic-transfer-ray-projection.png \"P1 ray projection debug 覆盖更高，但床、墙、窗帘、地面之间存在明显串色\")\n\n结论：P1 路线保留，但需要真实 2D mask、深度可见性过滤和 face graph smoothing。\n\n## 实验五：视觉代理 + 碰撞代理 Web Demo\n\n本周实现了 `visual-physics-proxy` demo：3DGS 只负责视觉显示，COLMAP Delaunay GLB 作为隐藏 collider 承担 raycast、ground probe 和移动阻挡。\n\n![视觉代理 3DGS + 碰撞代理 mesh Demo](assets/uploaded/experiments/04-visual-physics-proxy-demo.png \"Web demo 验证了 3DGS visual layer 与 mesh collision layer 可以分离\")\n\n结论：该 demo 已验证最小架构闭环，后续应拆成 object-level collider，并接入 face/object semantics 和物理材质。\n",
      "headings": [
        {
          "level": "2",
          "text": "实验一：GS2Mesh",
          "slug": "实验一gs2mesh"
        },
        {
          "level": "2",
          "text": "实验二：Open3D Poisson / 3DGS 点云",
          "slug": "实验二open3d-poisson-3dgs-点云"
        },
        {
          "level": "2",
          "text": "实验三：COLMAP Delaunay Dense",
          "slug": "实验三colmap-delaunay-dense"
        },
        {
          "level": "2",
          "text": "实验四：语义投影融合",
          "slug": "实验四语义投影融合"
        },
        {
          "level": "2",
          "text": "实验五：视觉代理 + 碰撞代理 Web Demo",
          "slug": "实验五视觉代理--碰撞代理-web-demo"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-semantic-transfer-experiment",
      "title": "语义投影融合实验",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。",
      "source_path": "docs/video2mesh/research-catalog/experiments/semantic-transfer-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 语义投影融合实验\n\n![mesh 语义投影融合调试结果](assets/uploaded/video2mesh-experiments-semantic-transfer-experiment/05-mesh-semantic-transfer-ray-projection.png \"早期 ray projection debug 覆盖更高，但床、墙、窗帘、地面之间存在明显串色\")\n\n## 实验位置\n\n- Early debug route: `tmp_remote_results/cli_dense_graphdeco30k_mesh_routes_20260702/mesh_semantic_transfer_P0_P1_delivery/p1_ray_projected_debug`\n- Formal replacement: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`\n- 相关文档：正式 Semantic Mesh 结果 20260703\n\n## 实验简介\n\n早期 P1 ray projection debug 尝试把语义投到 mesh face/点上，目标是支持点击 face 查询 object id、label 和后续交互属性。这个实验跑通了流程，但由于没有真实 2D masks，只能用 projected semantic point labels 调试，床、墙、窗帘、地面之间存在明显串色。\n\n后来 formal semantic mesh run 进一步补齐 GroundingDINO object discovery、SAM/SAM2 tracking、3D object masks 和多条 semantic transfer 路线，效果明显更适合汇报。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| mesh source | COLMAP Delaunay / Open3D Poisson / GS2Mesh |\n| semantic evidence | semantic point cloud、semantic splats、object masks |\n| face assignment | 投影、KDTree、local transfer 或 projected splats |\n| sidecar export | 写出 face -> label/object id/probability |\n| viewer QA | 用颜色渲染检查串色、unknown 和边界 |\n\n## 输入与输出\n\n输入：mesh、semantic points/splats、相机、object masks。输出：face semantics、colored semantic mesh、object split 和 coverage statistics。\n\n## 在 Video2Mesh 中的位置\n\n保留路线，但需要真实 2D mask、深度可见性过滤和 smoothing。\n\n## 输出结果摘录\n\n早期图五可以作为“问题案例”：覆盖更高但颜色串扰严重。新 formal run 中，COLMAP Delaunay local transfer 覆盖率 84.98%，projected splats 80.13%，Open3D Poisson 32.21%，GS2Mesh decim100k 55.49%。因此下一步应优先推进 COLMAP Delaunay local transfer + face sidecar。\n\n## 接入判断\n\n- P0：语义 sidecar 可作为增强，不阻塞 static collider。\n- P1：进入交互查询主线。\n- 风险：串色和 unknown 区域必须用可见性过滤、face graph smoothing 和人工审核控制。\n",
      "headings": [
        {
          "level": "2",
          "text": "实验位置",
          "slug": "实验位置"
        },
        {
          "level": "2",
          "text": "实验简介",
          "slug": "实验简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果摘录",
          "slug": "输出结果摘录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-experiments-visual-physics-proxy-demo",
      "title": "Visual / Physics Proxy Demo",
      "category": "调研目录",
      "research_stage": "experiments",
      "research_stage_title": "本项目实验",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。",
      "source_path": "docs/video2mesh/research-catalog/experiments/visual-physics-proxy-demo.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Visual / Physics Proxy Demo\n\n![视觉代理 3DGS + 碰撞代理 mesh Demo](assets/uploaded/video2mesh-experiments-visual-physics-proxy-demo/04-visual-physics-proxy-demo.png \"Web demo 验证了 3DGS visual layer 与 mesh collision layer 可以分离\")\n\n## Demo 链接\n\n- Local demo: http://127.0.0.1:4173/demos/visual-physics-proxy/\n- 相关调研：Icare / 学长文档路线、Spark Viewer、Static Mesh Collider\n\n## 实验简介\n\n这是根据视觉代理、碰撞代理、物体语义等分层思想实现的 Web demo。核心不是“做一个漂亮页面”，而是验证架构：3DGS/Splat/visual mesh 只负责显示，隐藏 mesh collider 或 primitive proxy 负责 raycast、地面探测、移动阻挡和交互命中。\n\n这个 demo 对导师汇报很有价值，因为它把调研结论落实成了一个可操作的最小系统：工业界的 visual proxy + collider proxy 思路在 Video2Mesh 中是可实现的。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| visual layer | 加载 3DGS / visual scene asset |\n| collider layer | 加载 hidden GLB mesh 或 primitive collider |\n| semantic layer | 命中 collider 后查询 object/label |\n| interaction | raycast、ground probe、movement blocking |\n| UI QA | 展示 visual/collider 分层开关和结果 |\n\n## 输入与输出\n\n输入：3DGS visual layer 和 mesh collider。输出：浏览器交互 demo。\n\n## 在 Video2Mesh 中的位置\n\n证明交互逻辑不需要依赖 3DGS 自身产生 collider。\n\n## 输出结果摘录\n\n图四显示 demo 已能表达分层代理思想：用户看到视觉场景，但实际交互可绑定到碰撞代理。下一步应把 formal semantic mesh 的 face sidecar 接进去，让点击 collider 后能返回 object id、label、material 和可交互属性。\n\n## 接入判断\n\n- P0：作为架构验证，不阻塞重建主线。\n- P1：继续接 semantic sidecar、object split 和 physics metadata。\n- 风险：demo 里的资产合同要和真实 export schema 对齐，避免只在演示数据里成立。\n",
      "headings": [
        {
          "level": "2",
          "text": "Demo 链接",
          "slug": "demo-链接"
        },
        {
          "level": "2",
          "text": "实验简介",
          "slug": "实验简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果摘录",
          "slug": "输出结果摘录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-industrial-pipelines-icare",
      "title": "Icare / 学长文档路线",
      "category": "调研目录",
      "research_stage": "industrial-pipelines",
      "research_stage_title": "工业资产管线",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/icare.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Icare / 学长文档路线\n\n![Icare / 学长文档路线](assets/uploaded/video2mesh-industrial-pipelines-icare/pipeline-overview.svg \"学长/工业路线共同强调 visual proxy、collider proxy 和 metadata sidecar 的分层\")\n\n## 链接\n\n- Local notes: 学长文档 / Icare 调研材料\n- Related industrial pattern: World Labs / Marble static world assets\n- Related implementation reference: image-blaster viewer and object job conventions\n\n## 简介\n\n学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部 metadata。这个分层和 Video2Mesh 当前方向高度一致：3DGS 负责看，COLMAP/Poisson/primitive/convex collider 负责碰撞，face/object sidecar 负责语义与物理属性。\n\n这类方案的重点不在单个算法，而在 asset bundle contract：viewer 能加载什么、engine 需要什么、哪些资产是 visual-only、哪些资产可参与 raycast/physics。\n\n## Pipeline 摘要\n\n| 阶段 | 作用 |\n|---|---|\n| visual proxy | 3DGS/Splat/Spark/SuperSplat 等承担高质量显示 |\n| interaction proxy | GLB mesh、simplified collider、primitive bodies 承担交互 |\n| semantic metadata | object id、label、face/material sidecar |\n| physics metadata | body type、mass、friction、restitution、constraints |\n| adapter | Web/Unity/MuJoCo/Isaac 运行时转换 |\n\n## 输入与输出\n\n输入：扫描/生成资产、3DGS、mesh、object metadata。输出：viewer 可消费的 visual + collider + metadata bundle。\n\n## 在 Video2Mesh 中的位置\n\n作为 Video2Mesh 架构参考，不能替代本项目导出合同。它帮助确认本周 demo 的方向：视觉代理与碰撞代理分开，最终由 Video2Mesh 自己承接语义、物理属性和引擎 adapter。\n\n## 接入判断\n\n- P0：借鉴分层合同。\n- P1：将 object sidecar、physics sidecar 和 adapter 做成项目自己的 bundle。\n- 风险：外部文档/演示不是可直接复用代码，需要 Video2Mesh 自己承接导出和 QA。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline 摘要",
          "slug": "pipeline-摘要"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-industrial-pipelines-image-blaster",
      "title": "image-blaster",
      "category": "调研目录",
      "research_stage": "industrial-pipelines",
      "research_stage_title": "工业资产管线",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/image-blaster.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# image-blaster\n\n## 链接\n\n- Local reference repo: `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/image-blaster`\n- 相关脚本：`scripts/generate-single-asset.mjs`、`scripts/generate-world.mjs`\n- Viewer 相关：`app/vite.config.ts`、`SceneObject.tsx`、`ObjectGrid.tsx`、`useSceneObjectVisual.ts`\n\n## 简介\n\nimage-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以为每个对象生成 object-local mesh，并以 `worlds/<world>/output/<object>/` 的目录组织资产；浏览器 viewer 侧稳定消费 `.glb`。但它本身不直接输出 MuJoCo/Isaac/Unity simulator bundle，物理属性、语义 ID、尺度/位姿归一化和引擎适配仍需要 Video2Mesh 承接。\n\n## Pipeline 摘要\n\n![image-blaster 在 Video2Mesh 中的位置](assets/uploaded/video2mesh-industrial-pipelines-image-blaster/pipeline-overview.svg \"image-blaster 更适合接在 object crop / reference image 之后，作为物体外观补全后端，再回填到 Video2Mesh simulator bundle\")\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| object crop/reference image | Video2Mesh 从 SAM/GDINO/semantic mesh 里准备物体裁剪图 |\n| object generation backend | 通过 Hunyuan3D 或 Meshy 等后端生成 `.glb/.obj` |\n| local object directory | 写入 `object.json`、mesh 文件和预览资产 |\n| React/Three.js viewer | 用 GLTFLoader 加载 GLB，并交给 Rapier/scene object 交互 |\n\n输入：object crop、prompt、world config。输出：object mesh、object.json、viewer 目录。对 Video2Mesh 来说，最关键的输出是可回填的 object-local mesh，而不是 viewer 本身。\n\n## 在 Video2Mesh 中的位置\n\nP1 物体补全后端和目录约定参考。推荐桥接方式是：\n\n1. `prepare-object-images` 从 mask/semantic sidecar 生成 object reference image。\n2. `export-image-blaster` 写出 image-blaster 可消费的 world/object job。\n3. image-blaster 生成 object mesh。\n4. `import-object-meshes` 将 GLB/OBJ 回填 Video2Mesh。\n5. `export-simulator-assets --fit-object-local-meshes-to-bbox` 统一尺度、姿态、物理属性和引擎 adapter。\n\n这能把 image-blaster 放在“物体视觉补全”位置，而不把它误认为完整 simulator exporter。\n\n## 接入判断\n\n- P0：不依赖它闭环；P0 先保证 scene collider 和 semantic sidecar。\n- P1：适合作为 object completion backend，重点接床、桌椅、小物体等缺损物体。\n- 风险：生成 mesh 的尺度和坐标系不可完全信任，需要 bbox fitting、object pose 和碰撞代理重新生成。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline 摘要",
          "slug": "pipeline-摘要"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "industrial-pipelines",
      "title": "工业资产管线阶段",
      "category": "调研目录",
      "research_stage": "industrial-pipelines",
      "research_stage_title": "工业资产管线",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "按 World Labs / Icare、image-blaster、Spark viewer 等工业方案整理 visual layer、collider 和 simulator asset bundle 的边界。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "World Labs",
        "image-blaster",
        "Spark",
        "调研目录"
      ],
      "body": "\n# 工业资产管线阶段\n\n工业界给出的最重要信号是：真实可交互 3D 场景通常不是一个单文件 mesh，而是由视觉资产、碰撞资产、语义/交互 metadata 和 runtime viewer 组成。\n\n## 主要项目和案例\n\n| 项目 / 案例 | 简介 | 可借鉴点 | 边界 |\n|---|---|---|---|\n| World Labs / Marble | 面向 static world/background 的生成和资产输出，通常包含 splat/SPZ、pano、collider mesh 等多层资产 | clean plate / world generation；视觉资产和 collider 分开交付 | 不直接负责 Video2Mesh 的物体级仿真 asset bundle |\n| Icare / World Labs game | 真实浏览器 3D 游戏案例，使用 Spark/Splat 类视觉层和独立碰撞/交互资产 | 证明 visual proxy + collision proxy 是产业级可落地架构 | 不是从任意扫描视频自动得到所有物理属性 |\n| image-blaster | 管理 world/object 目录、reference image、object mesh jobs、React/Three/Rapier viewer | object mesh generation convention、GLB viewer、Rapier 交互分层 | 不生成 MuJoCo/Isaac/Unity adapter，也不拥有 simulator_asset_bundle |\n| Spark / SuperSplat runtime | 浏览器端 splat 渲染和查看工具 | Web 视觉展示与调试 | 不能替代 collider / physics solver |\n\n## 对 Video2Mesh 的分层启发\n\n```text\nvisual layer:\n  3DGS / SPZ / SOG / Splat\n\ncollision layer:\n  GLB collider / primitive proxy / convex parts\n\nsemantic and physics sidecar:\n  object_id / label / affordance / material / mass / friction\n\nruntime adapter:\n  Web / Unity / MuJoCo / Isaac\n```\n\n## 与 image-blaster 的正确关系\n\nimage-blaster 可以成为 Video2Mesh 的 object mesh helper：\n\n```text\nVideo2Mesh selected object frames\n  -> image-blaster world/object folder\n  -> Hunyuan3D / Meshy mesh job\n  -> generated object-local mesh\n  -> Video2Mesh import and fit\n  -> simulator asset bundle\n```\n\n但最终 simulator bundle、坐标对齐、物理属性、引擎 adapter 仍应由 Video2Mesh 负责。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和案例",
          "slug": "主要项目和案例"
        },
        {
          "level": "2",
          "text": "对 Video2Mesh 的分层启发",
          "slug": "对-video2mesh-的分层启发"
        },
        {
          "level": "2",
          "text": "与 image-blaster 的正确关系",
          "slug": "与-image-blaster-的正确关系"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-industrial-pipelines-spark-viewer",
      "title": "Spark Viewer",
      "category": "调研目录",
      "research_stage": "industrial-pipelines",
      "research_stage_title": "工业资产管线",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/spark-viewer.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Spark Viewer\n\n![Spark Viewer](../assets/stage-visual-3dgs.svg \"Spark viewer 代表浏览器端 splat visual layer，物理仍需独立 collider\")\n\n## 链接\n\n- Spark docs: https://sparkjs.dev/\n- Spark 2.0 blog: https://www.worldlabs.ai/blog/spark-2.0\n- Three.js: https://threejs.org/\n- Rapier JS: https://rapier.rs/docs/user_guides/javascript/getting_started_js\n\n## 简介\n\nSpark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。它和 image-blaster/World Labs 类工具的共同点是：视觉层可以是 splat，交互层仍然要另有 mesh/collider/physics。\n\n这对 Video2Mesh 的 Web demo 很重要：用户看到的是高质量 splat 或 visual mesh，点击、导航、碰撞和物体选择则走隐藏 collider 或 semantic sidecar。\n\n## Pipeline 摘要\n\n| 阶段 | 作用 |\n|---|---|\n| splat asset | 载入 PLY/SPZ/SOG/SPLAT |\n| Web renderer | Three.js / Spark 渲染 visual proxy |\n| collider overlay | 同场景加载 hidden GLB/primitive collider |\n| interaction query | raycast 命中 collider，再查 semantic sidecar |\n| engine handoff | 将 visual/collider/metadata 打包给后续 adapter |\n\n## 输入与输出\n\n输入：splat/ply/spz/sog、相机、可选 mesh collider。输出：Web 视觉层、交互查询和 QA 截图。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 展示层，不承担 physics。本周 visual-physics-proxy demo 就是沿着这个方向做的最小验证。\n\n## 接入判断\n\n- P0：作为 viewer 参考和 visual QA。\n- P1：接 collider/semantic sidecar，形成交互 demo。\n- 风险：浏览器 viewer 很容易掩盖物理资产缺失，必须显示/检查 collider 和 metadata。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline 摘要",
          "slug": "pipeline-摘要"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-industrial-pipelines-world-labs-marble",
      "title": "World Labs / Marble",
      "category": "调研目录",
      "research_stage": "industrial-pipelines",
      "research_stage_title": "工业资产管线",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "World Labs Marble 更偏 static world/background 生成，可提供 splat、collider、pano 等世界资产。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/world-labs-marble.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# World Labs / Marble\n\n## 链接\n\n- World Labs: https://www.worldlabs.ai/\n- Marble API docs: https://docs.worldlabs.ai/\n- image-blaster local script: `image-blaster/scripts/generate-world.mjs`\n\n## 简介\n\nWorld Labs / Marble 更偏 static world/background 生成。它的价值不在于替 Video2Mesh 做每个物体的交互资产，而在于给一个 clean plate / static world 层：splat 负责视觉，collider mesh 负责基础空间约束，pano/thumbnail 用于 viewer 和预览。\n\n在 image-blaster 的使用方式里，World Labs 主要被当作 background/world generator：先从场景描述中去掉需要单独处理的 foreground objects，形成 clean plate prompt，再请求 Marble 生成世界资产。\n\n## Pipeline 摘要\n\n![World/background 与 object mesh 的分层](assets/uploaded/video2mesh-industrial-pipelines-world-labs-marble/pipeline-overview.svg \"World Labs 更靠近 static world/background 层；object mesh 和 simulator bundle 仍由 Video2Mesh/image-blaster 后续模块处理\")\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| scene description / clean plate | 描述去掉 foreground objects 后的背景世界 |\n| world generation | 调用 Marble world generation API |\n| asset download/cache | 下载 splat、collider mesh、panorama、thumbnail 等世界资产 |\n| local viewer loading | 运行时消费本地 `/worlds/` 路径，不直接依赖 provider URL |\n\n输入：场景描述、clean plate 或生成请求。输出：static world assets，包括视觉层 splat、基础 collider、pano/thumbnail 和 provenance/resume 信息。\n\n## 在 Video2Mesh 中的位置\n\n适合借鉴两个点：\n\n- 静态背景和前景物体分层。背景可以是 splat/world layer，物体由 object mesh/jobs 单独处理。\n- visual proxy 与 collider proxy 分开保存。即使视觉是 splat，交互也需要独立 collider/physics contract。\n\nVideo2Mesh 如果后续做背景补全，可以把 World Labs 类方法放在 background clean plate 方向，但仍要自己生成 simulator asset bundle、semantic IDs、physics sidecar 和 Unity/MuJoCo/Isaac adapter。\n\n## 接入判断\n\n- P0：不进入，当前 P0 依赖真实扫描视频和本项目可控输出。\n- P1：可借鉴 clean plate/background repair 的资产分层合同。\n- P2/P3：如果需要生成缺损背景或静态世界替换，可作为工业方案对照。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline 摘要",
          "slug": "pipeline-摘要"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-input-pose-pointcloud-colmap",
      "title": "COLMAP",
      "category": "调研目录",
      "research_stage": "input-pose-pointcloud",
      "research_stage_title": "输入、位姿与点云",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "COLMAP 是当前 Video2Mesh 的 P0 位姿、稠密重建和 Delaunay mesh 基线。它提供相机参数、稀疏点、dense workspace 和可作为 collider 的传统几何。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/colmap.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP\n\n![COLMAP input stage](assets/uploaded/video2mesh-input-pose-pointcloud-colmap/stage-input-pose.svg \"COLMAP 在 Video2Mesh 中负责从扫描视频抽帧得到相机、稠密点云和后续 mesh/collider 的基础坐标系\")\n\n## 链接\n\n- Official docs: https://colmap.github.io/\n- GitHub: https://github.com/colmap/colmap\n- Tutorial: https://colmap.github.io/tutorial.html\n\n## 摘要要点\n\nCOLMAP 是通用 Structure-from-Motion 和 Multi-View Stereo 工具链，提供图形界面和命令行接口。对 Video2Mesh 来说，它不是一个可替代的小工具，而是 P0 坐标合同的来源：相机内外参、稀疏点云、dense workspace、fused point cloud 和 Delaunay/Poisson mesher 都从这里出发。\n\n它的优点是输出格式成熟、和 GraphDECO 3DGS 生态天然兼容，也能直接作为传统 mesh/collider 的输入。缺点是弱纹理、反光、重复纹理和扫描覆盖不足时容易断链，因此后续可以引入 MASt3R/DUSt3R/VGGT 做 fallback，但当前主链路仍建议保留 COLMAP。\n\n## Pipeline\n\n| 阶段 | 作用 | Video2Mesh 消费方式 |\n|---|---|---|\n| feature extraction / matching | 从抽帧图像中建立跨视角匹配 | 产生 SfM 的观测基础 |\n| sparse reconstruction | 估计 cameras/images/points3D | 生成 `camera_info.json` 和 GraphDECO 输入 |\n| image undistortion | 生成 dense workspace | 接 PatchMatch stereo / Delaunay mesher |\n| patch-match stereo + fusion | 生成 dense depth / fused point cloud | 输入 Open3D、Poisson、Delaunay、语义投影 |\n| Delaunay / Poisson meshing | 传统 MVS mesh 输出 | P0 static collider baseline |\n\n## 输入与输出\n\n输入：扫描视频抽帧、多视角图片、可选相机先验。输出：COLMAP sparse model、dense workspace、`fused.ply`、Delaunay/Poisson mesh、相机位姿和尺度基准。\n\n## 在 Video2Mesh 中的位置\n\nP0 主链路。当前项目中的 GraphDECO 训练、COLMAP Delaunay dense mesh、semantic transfer 和 simulator asset bundle 都依赖这个坐标基准。它比 learned pose 方法更可控，也方便 debug 每一步产物。\n\n## 输出结果摘录\n\n本周 `colmap_delaunay_dense` 路线的结果视觉细节不如 3DGS，但几何更轻、更稳定，适合作为隐藏 static collision proxy。正式 semantic mesh run 中，COLMAP Delaunay local semantic transfer 得到 82,920 vertices / 167,082 faces，语义覆盖率 84.98%，优于 Open3D Poisson 和 GS2Mesh 的语义覆盖。\n\n## 接入判断\n\n- P0：保留为主链路，负责相机、dense geometry 和 static collider。\n- P1：接入 learned fallback、尺度检查和失败场景自动诊断。\n- 风险：扫描覆盖不足时要及时提示重拍，而不是让后续 3DGS/mesh 阶段背锅。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果摘录",
          "slug": "输出结果摘录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-input-pose-pointcloud-mast3r-dust3r-vggt",
      "title": "MASt3R / DUSt3R / VGGT",
      "category": "调研目录",
      "research_stage": "input-pose-pointcloud",
      "research_stage_title": "输入、位姿与点云",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/mast3r-dust3r-vggt.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "VGGT",
        "调研目录"
      ],
      "body": "\n# MASt3R / DUSt3R / VGGT\n\n![输入位姿阶段](assets/uploaded/video2mesh-input-pose-pointcloud-mast3r-dust3r-vggt/stage-input-pose.svg \"MASt3R、DUSt3R、VGGT 更适合作为 COLMAP 失败时的 learned geometry fallback，而不是直接替代 P0 主坐标合同\")\n\n## 链接\n\n- MASt3R GitHub: https://github.com/naver/mast3r\n- DUSt3R GitHub: https://github.com/naver/dust3r\n- DUSt3R paper: https://openaccess.thecvf.com/content/CVPR2024/html/Wang_DUSt3R_Geometric_3D_Vision_Made_Easy_CVPR_2024_paper.html\n- VGGT project: https://vgg-t.github.io/\n- VGGT GitHub: https://github.com/facebookresearch/vggt\n- VGGT paper: https://arxiv.org/abs/2503.11651\n\n## 摘要要点\n\nDUSt3R 的核心是直接从图像对预测 3D point map，让深度、匹配、相机和相对位姿可以从同一个表示中恢复。MASt3R 进一步强化了 3D grounding 和 matching，可服务更稳的图像匹配、SfM 或 SLAM。VGGT 则是 feed-forward 几何模型，试图从单张、少量或大量视图中一次性预测相机参数、深度、点图和 3D point tracks。\n\n这组方法的共同价值是降低 COLMAP 对纹理、匹配和足够重叠视角的依赖；共同风险是输出坐标系、尺度、置信度和工程接口不一定和 COLMAP/GraphDECO 完全对齐。\n\n## Pipeline\n\n| 方法 | Pipeline | 输出 |\n|---|---|---|\n| DUSt3R | image pair -> transformer point map -> global alignment | point maps、depth、relative/absolute camera 线索 |\n| MASt3R | image pair -> 3D grounded matching -> SfM/SLAM helper | dense matches、pose/track 辅助 |\n| VGGT | multi-view images -> feed-forward transformer -> geometry attributes | camera、depth、point maps、point tracks |\n\n## 输入与输出\n\n输入：图像对、图像序列或视频抽帧。输出：相对几何、点图、深度、匹配、相机/轨迹估计，必要时再转换到 Video2Mesh 的 `camera_info.json` 和 scene coordinate contract。\n\n## 在 Video2Mesh 中的位置\n\nP1 fallback 和质量增强，不建议当前直接替换 COLMAP 主链路。更合理的接入方式是：\n\n- COLMAP 失败时，用 learned geometry 生成初始 pose/depth，再尝试重建。\n- 对少纹理物体做 object-level depth fusion 辅助。\n- 给 mesh semantic transfer 增加深度可见性或稠密 correspondence。\n\n## 输出/接入记录\n\n项目当前主线仍使用 COLMAP。此前 MASt3R-SLAM 适合作为候选，但轨迹帧数、尺度和 COLMAP-compatible export 还需要适配，暂未作为正式 P0 路线进入周报结果。\n\n## 接入判断\n\n- P0：暂不替代 COLMAP。\n- P1：作为失败 fallback、弱纹理补强和 object-level depth 辅助。\n- 风险：必须显式记录 scale、axis convention、confidence，否则 object mesh 和 collider 会错位。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出/接入记录",
          "slug": "输出-接入记录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-input-pose-pointcloud-open3d-cloudcompare",
      "title": "Open3D / CloudCompare",
      "category": "调研目录",
      "research_stage": "input-pose-pointcloud",
      "research_stage_title": "输入、位姿与点云",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/open3d-cloudcompare.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D / CloudCompare\n\n![点云处理阶段](assets/uploaded/video2mesh-input-pose-pointcloud-open3d-cloudcompare/stage-input-pose.svg \"Open3D 更适合脚本化处理，CloudCompare 更适合人工检查和可视化诊断\")\n\n## 链接\n\n- Open3D docs: https://www.open3d.org/docs/latest/\n- Open3D surface reconstruction: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html\n- CloudCompare: https://www.cloudcompare.org/\n- CloudCompare PoissonRecon plugin: https://www.cloudcompare.org/doc/wiki/index.php/Poisson_Surface_Reconstruction_%28plugin%29\n\n## 简介\n\nOpen3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计、手动分割和可视化对比。两者在 Video2Mesh 里都应该定位为工程诊断与 baseline 工具，而不是最终产品形态。\n\nOpen3D 的优势是可以被 CLI 批量调用，便于统一下采样、法线估计、outlier removal、Poisson reconstruction 和 mesh decimation。CloudCompare 的优势是肉眼检查非常快，适合判断某条路线为什么漂浮、破碎、壳化或语义串色。\n\n## Pipeline\n\n| 工具 | Pipeline | 适合用途 |\n|---|---|---|\n| Open3D | PLY/point cloud -> downsample/filter -> normal estimation -> Poisson/BPA/alpha shape -> mesh cleanup | 批量 baseline、自动统计、可复现实验 |\n| CloudCompare | cloud/mesh -> manual crop -> normal/recon plugin -> visual inspection -> screenshots | 人工 QA、参数调试、汇报截图 |\n\n## 输入与输出\n\n输入：PLY/PCD/OBJ/GLB 等点云或 mesh。输出：cleaned point cloud、normals、Poisson/BPA mesh、diagnostic screenshot、density/connected component 等质量线索。\n\n## 在 Video2Mesh 中的位置\n\ndebug 和 baseline 工具。Open3D Poisson 已经用于本周 mesh 重建实验；CloudCompare + 3D recon + Poisson 用于手动对照。结果说明它们能快速出 mesh，但对 3DGS center 或不干净点云非常敏感，容易生成壳状面、粘连面和 unknown/background 过高的语义区域。\n\n## 接入判断\n\n- P0：只保留 Open3D 的轻量清理/统计脚本，不把 Poisson 作为唯一 collider 主链路。\n- P1：作为可复现实验 baseline 和失败诊断工具。\n- 风险：Poisson 会在低密度区域补面，必须配合 density filter、connected-component cleanup 和人工 QA。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "input-pose-pointcloud",
      "title": "输入、位姿与点云阶段",
      "category": "调研目录",
      "research_stage": "input-pose-pointcloud",
      "research_stage_title": "输入、位姿与点云",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "调研从扫描视频获得相机、稠密点云和统一坐标系的模型与项目，包括 COLMAP、MASt3R/DUSt3R/VGGT 和 MVS。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "COLMAP",
        "Point Cloud",
        "Pose",
        "调研目录"
      ],
      "body": "\n# 输入、位姿与点云阶段\n\n这一阶段负责把原始扫描视频变成后续所有模块共享的坐标系统：相机内外参、稠密点云、尺度约束和可追踪帧。它是 3DGS、mesh、语义回灌和 simulator asset bundle 的地基。\n\n![输入位姿阶段](assets/uploaded/input-pose-pointcloud/stage-input-pose.svg \"从扫描视频到 COLMAP/SfM、稠密点云和坐标尺度合同\")\n\n## 主要项目和模型\n\n| 项目 / 方法 | 简介 | 输入输出 | 对 Video2Mesh 的作用 | 风险 |\n|---|---|---|---|---|\n| COLMAP SfM/MVS | 经典摄影测量工具链，估计相机位姿、稀疏点云和稠密 workspace | 输入多帧图片，输出 cameras/images/points3D、dense fused point cloud | 当前最稳的 P0 位姿和 dense geometry 来源，能直接接 GraphDECO 3DGS、Delaunay mesher 和 Poisson baseline | 纹理弱、反光、重复图案时可能失败；需要较好帧覆盖 |\n| COLMAP dense stereo | 基于已知相机做 patch-match stereo 和 fusion | 输入 COLMAP sparse model，输出 fused.ply / dense workspace | 场景级 mesh/collider 的主输入，比直接使用 Gaussian center 更可靠 | 稠密点云仍会有空洞、噪声和漂浮点 |\n| MASt3R / DUSt3R | 学习式多视图几何，弱纹理/小基线下可作为传统 SfM 的补充 | 输入图像对或多视图，输出对应关系、深度/点云、相机关系 | 可作为 COLMAP 失败时的 pose/depth fallback，或为物体级 depth fusion 提供先验 | 输出坐标尺度和 COLMAP/3DGS 生态不完全一致，需要适配 |\n| VGGT 类 feed-forward 模型 | 端到端估计相机、深度、点云等 3D 表征 | 输入图片集合，输出 camera/depth/point map | 可作为快速预处理或弱纹理场景 fallback | 工程稳定性、尺度一致性和大场景鲁棒性需实测 |\n| Open3D / CloudCompare 点云处理 | 点云过滤、法线估计、下采样、可视检查 | 输入 PLY/PCD，输出 cleaned point cloud / normals | 用于 mesh 前处理、debug 和人工检查 | 清理规则容易影响真实薄结构 |\n\n## 我们项目中的接入位置\n\n```text\nvideo frames\n  -> COLMAP sparse/dense\n  -> scene/cameras/camera_info.json\n  -> scene/reconstruction/point_cloud.ply\n  -> GraphDECO 3DGS / Delaunay mesh / Poisson baseline\n```\n\n当前建议：\n\n- P0 仍以 COLMAP 为主，因为它的输出标准、生态成熟，而且和 GraphDECO / COLMAP Delaunay / CloudCompare 都能接起来。\n- learned pose/depth 方法适合作为 fallback 或 object-level depth enhancement，不要一开始就替代主链路。\n- 所有后续资产必须明确记录坐标系、scale、camera convention，否则 object mesh 和 collider 回填会错位。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和模型",
          "slug": "主要项目和模型"
        },
        {
          "level": "2",
          "text": "我们项目中的接入位置",
          "slug": "我们项目中的接入位置"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-2dgs-gof",
      "title": "2DGS / GOF",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/2dgs-gof.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 2DGS / GOF\n\n![2DGS surfel and meshing teaser](https://github.com/hbb1/2d-gaussian-splatting/raw/main/assets/teaser.jpg \"2DGS 将场景表示为 2D oriented Gaussian disks / surfels，并支持 surface normal 和 mesh extraction\")\n\n## 链接\n\n- 2DGS project/code: https://github.com/hbb1/2d-gaussian-splatting\n- 2DGS paper: https://arxiv.org/abs/2403.17888\n- GOF project page: https://niujinshuchong.github.io/gaussian-opacity-fields/\n- GOF code: https://github.com/autonomousvision/gaussian-opacity-fields\n- Venues: 2DGS 为 SIGGRAPH 2024；GOF 为 SIGGRAPH Asia 2024 / TOG\n\n## 摘要要点\n\n2DGS 和 GOF 都是在回应同一个问题：传统 3DGS 视觉质量强，但其 3D Gaussians 是显式、离散、视角相关的体元，不天然形成稳定 surface。2DGS 将体状 Gaussian 压成 2D oriented planar disks / surfels，让几何更接近表面；GOF 则把 3D Gaussians 组织成 opacity field，通过 level set 和 Marching Tetrahedra 做 adaptive mesh extraction。\n\n这两类方法比“从 Gaussian center 做 Poisson”更接近 surface-aware Gaussian 路线，适合未来做高质量 visual mesh 或对比论文结果。但它们通常需要按各自方法重新训练或改训练过程，不是简单接在现有 GraphDECO 3DGS 后面就能稳定产出 collider。\n\n## Pipeline 摘要\n\n## 输入与输出\n\n| 方法 | Pipeline | 输出 |\n|---|---|---|\n| 2DGS | multi-view images -> 2D oriented Gaussian disks -> perspective-correct splatting -> depth/normal regularization -> meshing | surfel-like Gaussian 表示、normal/depth、mesh |\n| GOF | 3DGS-like optimization -> opacity field / ray-Gaussian geometry -> normal regularization -> Gaussian-induced tetrahedral grid -> Marching Tetrahedra | adaptive compact mesh、unbounded scene reconstruction |\n\n![GOF teaser](https://niujinshuchong.github.io/gaussian-opacity-fields/resources/teaser_gof.png \"GOF 通过 Gaussian Opacity Field 和 adaptive extraction 得到更紧凑的 surface mesh\")\n\n## 在 Video2Mesh 中的位置\n\n它们适合作为 P2/P3 的研究升级路线，用于回答“如果从训练阶段就考虑几何一致性，是否能减少后续 mesh 清理压力”。短期 Video2Mesh 已经有 GraphDECO 3DGS 输出，所以这条线不能直接替代现有 P0；更适合新实验分支，和 GS2Mesh/SuGaR 比较 visual mesh 质量。\n\n## 接入判断\n\n- P0：不进入，当前 collider 仍以 COLMAP Delaunay / cleaned Poisson 为主。\n- P1：如果想系统评估 surface-aware Gaussian，需要新增训练配置和评估脚本。\n- P2/P3：适合作为论文调研和后续 visual mesh 升级方向，尤其关注 unbounded scene 和背景几何。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline 摘要",
          "slug": "pipeline-摘要"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-cloudcompare-poisson",
      "title": "CloudCompare / PoissonRecon",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/cloudcompare-poisson.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# CloudCompare / PoissonRecon\n\n## 链接\n\n- CloudCompare: https://www.cloudcompare.org/\n- PoissonRecon: https://github.com/mkazhdan/PoissonRecon\n- Open3D reconstruction docs: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html\n\n## 简介\n\nCloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。它更像“诊断台”和人工 baseline，而不是无人值守 pipeline：优点是可视化、裁剪、法线检查很直观；缺点是人工步骤多，难以稳定复现成项目主链路。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| load point cloud | 导入 COLMAP dense / 3DGS center / fused point cloud |\n| visual inspection | 人工检查漂浮点、空洞、尺度和噪声 |\n| crop/clean | 裁剪 bbox、删除离群点、保留主连通结构 |\n| normal estimation | 估计并定向 normals |\n| PoissonRecon | 生成三角网格 |\n| postprocess | 裁剪低 density、减面、导出 GLB/PLY |\n\n输入：点云。输出：可视化检查结果、Poisson mesh、参数判断。\n\n## 在 Video2Mesh 中的位置\n\n人工诊断和方法对照，不建议直接作为无人值守主链路。它适合用来回答“为什么 Open3D/Poisson 输出坏了”“点云是不是本身就有漂浮/空洞”“法线方向是否错误”等问题。\n\n在本周实验中，CloudCompare + PoissonRecon 的经验支持了一个判断：3DGS center point cloud 不能等同真实表面，直接建面会出现壳状伪影和粘连；更稳的 collider 应该回到 COLMAP dense/Delaunay 或经过严格清理的 MVS point cloud。\n\n## 接入判断\n\n- P0：不进入自动主链路。\n- P1：作为人工 QA/诊断工具保留。\n- P2：如果要把人工经验自动化，可把 CloudCompare 中有效步骤翻译成 Open3D/Trimesh 脚本。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-colmap-delaunay",
      "title": "COLMAP Delaunay Mesher",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/colmap-delaunay.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP Delaunay Mesher\n\n## 链接\n\n- COLMAP docs: https://colmap.github.io/\n- COLMAP dense reconstruction: https://colmap.github.io/tutorial.html\n- Poisson/Delaunay meshing commands: `colmap poisson_mesher` / `colmap delaunay_mesher`\n\n## 简介\n\nCOLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。它的视觉质量通常不如 3DGS，但几何上更适合作为 collision proxy：mesh 较轻、位置和尺度跟 SfM/MVS workspace 一致、可直接导出 GLB/PLY 给 runtime 使用。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| sparse reconstruction | 从视频抽帧估计相机位姿 |\n| image undistortion | 准备 dense stereo workspace |\n| patch match stereo | 得到多视角深度 |\n| stereo fusion | 融合为 dense point cloud |\n| Delaunay meshing | 从 dense workspace/点云建场景级 mesh |\n| GLB postprocess | double-sided/indexed/decimation，供 Web viewer 或 engine 使用 |\n\n输入：COLMAP dense workspace 或 dense fused point cloud。输出：scene-level mesh，适合 static collision proxy。\n\n## 在 Video2Mesh 中的位置\n\nP0 scene collider 主路线，适合轻量静态碰撞代理。当前 bedroom4 实验里，COLMAP Delaunay 输出 82,920 vertices / 167,082 triangles，GLB 约 3.0MB；formal semantic run 的 local transfer 覆盖率 84.98%，能拆出 16 个 object mesh split。\n\n![COLMAP Delaunay dense mesh](assets/uploaded/video2mesh-mesh-reconstruction-colmap-delaunay/03-colmap-delaunay-dense.png \"COLMAP Delaunay mesh 视觉细节有限，但轻量稳定，适合作为隐藏 collider\")\n\n## 接入判断\n\n- P0：进入主链路，作为 hidden static collider。\n- P1：结合 semantic sidecar，支持 raycast 后返回 object/label。\n- 风险：薄结构和细节会缺失，所以不能替代 3DGS visual layer。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-gs2mesh",
      "title": "GS2Mesh",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "GS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/gs2mesh.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GS2Mesh\n\n![GS2Mesh pipeline](https://gs2mesh.github.io/static/images/pipeline.jpeg \"GS2Mesh pipeline：场景拍摄与位姿估计 -> 3DGS 和双目 novel view 渲染 -> stereo depth estimation -> depth fusion 到三角网格\")\n\n## 链接\n\n- Project page: https://gs2mesh.github.io/\n- Code: https://github.com/yanivw12/gs2mesh\n- Paper: https://arxiv.org/abs/2404.01810\n- Venue: ECCV 2024\n\n## 摘要要点\n\nGS2Mesh 解决的问题是：3DGS 的视觉渲染很好，但 Gaussian 本身是按 photometric loss 优化出来的，直接从 Gaussian center 或属性抽 surface 容易得到噪声面。它的核心做法不是直接连 Gaussian，而是把训练好的 3DGS 当作 novel-view renderer，渲染 stereo-aligned image pairs，再用预训练 stereo matching model 得到深度，最后将多视角深度融合成单个 smooth mesh。\n\n这条路线的亮点是工程上比较模块化：只要有稳定的 3DGS 和相机位姿，就可以把 depth prior 插进来，不需要重新训练一个复杂 SDF。代价是会引入 stereo model、渲染视角选择、TSDF/depth fusion 和 mesh 清理等额外环节。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| scene capture + pose estimation | 用 COLMAP/SfM 得到相机位姿，并训练 3DGS |\n| stereo-calibrated novel view rendering | 从 3DGS 渲染匹配的双目视角 |\n| stereo depth estimation | 用预训练 stereo model 预测每个视角深度 |\n| depth fusion | 将多视角 depth profiles 融合为三角 mesh |\n\n输入：训练后的 3DGS、相机位姿、渲染视角参数。输出：场景级 visual mesh，通常还需要 decimation、component cleanup、double-side/indexed GLB 等后处理，才能放到 Web 或引擎里。\n\n## 在 Video2Mesh 中的位置\n\n适合作为 P1/P2 的 visual mesh benchmark 或 per-object visual mesh 升级路线。它不适合作为 P0 collider 主链路直接替代 COLMAP Delaunay，因为输出 mesh 的体量和局部破碎仍需要清理，且运行依赖比传统 MVS/Poisson 重。\n\n在当前项目实验中，GS2Mesh 的 raw mesh 大约 4.48M vertices / 8.09M triangles，原始文件约 333MB；减面后可以压到几 MB 级 GLB。结构上能保留床、窗帘、大型家具和房间轮廓，但墙面破碎、漂浮片和局部缺失仍明显。\n\n![本项目 GS2Mesh 输出](assets/uploaded/video2mesh-mesh-reconstruction-gs2mesh/01-gs2mesh.png \"Video2Mesh GS2Mesh 实验输出：保留了床和大结构，但墙面与局部表面仍不稳定\")\n\n## 接入判断\n\n- P0：不进入主 collider 链路，避免把视觉 mesh 的噪声带到物理层。\n- P1：可以保留为 visual mesh 对照，尤其用于比较 Open3D Poisson、COLMAP Delaunay 和 SuGaR/2DGS 的质量。\n- P2：如果后面做 per-object mesh，可尝试对单个物体或局部空间运行，降低场景级噪声和体量。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-neus-volsdf",
      "title": "NeuS / VolSDF",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Neural SDF 路线能做高质量隐式表面重建，但训练和集成成本高。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/neus-volsdf.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# NeuS / VolSDF\n\n![Neural SDF mesh reconstruction](assets/uploaded/video2mesh-mesh-reconstruction-neus-volsdf/stage-mesh.svg \"NeuS / VolSDF 代表 neural implicit surface reconstruction 路线，适合离线高质量表面重建\")\n\n## 链接\n\n- NeuS project: https://lingjie0206.github.io/papers/NeuS/\n- NeuS paper: https://arxiv.org/abs/2106.10689\n- NeuS code: https://github.com/Totoro97/NeuS\n- VolSDF project: https://lioryariv.github.io/volsdf/\n- VolSDF paper: https://arxiv.org/abs/2106.12052\n\n## 摘要要点\n\nNeuS 和 VolSDF 都属于 neural implicit surface reconstruction。它们不是直接从点云做 Poisson，而是学习一个连续 SDF 或 density/SDF 相关场，再通过体渲染约束多视角图像一致性，最后从隐式表面中抽取 mesh。\n\n这类方法通常能得到比传统点云建面更干净的表面，尤其适合离线高质量重建；但训练时间、环境依赖、尺度对齐、texture/material 和大场景效率都比 COLMAP Delaunay 或 Poisson 更重。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| posed images | 输入多视角图像和相机 |\n| implicit field training | 学习 SDF / density / radiance field |\n| surface extraction | 通过 marching cubes 等方式抽 mesh |\n| texture/material | 可选再做颜色、贴图或外观优化 |\n| cleanup/export | 减面、坐标对齐、导出 GLB/OBJ |\n\n## 输入与输出\n\n输入：多视角图像、相机位姿、mask 或 bbox。输出：SDF、surface mesh、可选 appearance/texture。\n\n## 在 Video2Mesh 中的位置\n\n离线高质量资产候选，不适合当前主链路快速闭环。它更像 P2/P3 的对照路线：当我们需要单个物体或局部区域的高质量 visual mesh，可以用 neural SDF 做实验；但 P0 static collider 仍优先使用 COLMAP Delaunay。\n\n## 接入作用\n\n如果尝试接入，最合理方式是 object/local reconstruction：\n\n- 对 bed、nightstand、lamp 等 object split 或 selected crop 单独训练，减少场景级复杂度。\n- 将输出 mesh 回填 Video2Mesh object coordinate，再生成独立 collider。\n- 用它和 GS2Mesh、SuGaR、Hunyuan3D 做 visual mesh 质量对照。\n\n## 接入判断\n\n- P0：不进入，训练成本和工程复杂度不适合当前闭环。\n- P1：可作为少量 object/local visual mesh 对照实验。\n- P2/P3：跟踪高质量 neural surface reconstruction 和 editable asset 方向。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入作用",
          "slug": "接入作用"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-open3d-poisson",
      "title": "Open3D Poisson",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/open3d-poisson.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D Poisson\n\n## 链接\n\n- Open3D surface reconstruction docs: https://www.open3d.org/docs/latest/tutorial/Advanced/surface_reconstruction.html\n- Open3D Poisson API: https://www.open3d.org/docs/latest/python_api/open3d.geometry.TriangleMesh.html\n- Kazhdan Poisson reconstruction reference implementation: https://github.com/mkazhdan/PoissonRecon\n\n## 简介\n\nOpen3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。它的优点是工程成本低、容易放进 CLI、输出 GLB/PLY 很方便；缺点是强依赖点云质量和法线方向，遇到 3DGS center cloud 时容易把“视觉采样点”错误当作真实 surface。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| point filtering | 去除低 alpha、尺度异常、拉长 Gaussian 或离群点 |\n| normal estimation/orientation | 用 Open3D 估计并朝向一致化法线 |\n| Poisson reconstruction | 从带法线点云重建 watertight-ish surface |\n| density/component cleanup | 按 density、连通分量、bbox 裁剪坏面 |\n| decimation/export | 减面并导出 PLY/GLB |\n\n输入：带法线点云，可以来自 COLMAP dense fused point cloud，也可以来自过滤后的 3DGS centers。输出：Poisson mesh、decimated mesh、预览图和 route report。\n\n## 在 Video2Mesh 中的位置\n\nbaseline/fallback。3DGS center point cloud 上容易生成壳状伪影，因此不适合被解释为真实表面；如果输入换成 COLMAP dense fused point cloud，会更接近传统 MVS mesh，但仍不如 Delaunay route 稳定。\n\n本项目 `alpha005_sample500k` 实验输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。formal semantic run 中 Open3D Poisson dense fused voxel10 的 semantic coverage 只有 32.21%，unknown/background 高达 67.79%，说明它不适合承载主 semantic sidecar。\n\n![Open3D Poisson 实验输出](assets/uploaded/video2mesh-mesh-reconstruction-open3d-poisson/02-open3d-poisson-3dgs-alpha005-sample500k.png \"3DGS center Poisson 输出体量可控，但有壳状伪影、粘连和漂浮面\")\n\n## 接入判断\n\n- P0：不作为主 collider，只保留 fallback。\n- P1：用于快速 debug 点云清理和 postprocess 参数。\n- 风险：如果输入是 3DGS centers，结果容易“看起来有面但语义和物理都不可靠”。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "mesh-reconstruction",
      "title": "Mesh 重建阶段",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "按场景级 collider 和物体级 visual mesh 两个目标，整理 COLMAP Delaunay、Poisson、GS2Mesh、SuGaR、2DGS/GOF 等路线。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Mesh",
        "GS2Mesh",
        "SuGaR",
        "Poisson",
        "调研目录"
      ],
      "body": "\n# Mesh 重建阶段\n\nMesh 重建不能只问“哪个方法画面最好”，还要区分目标：场景级 static collider 需要稳定、轻量、可碰撞；物体级 visual mesh 需要更好的外观、边界和补全能力。\n\n![Mesh 重建路线](assets/uploaded/mesh-reconstruction/stage-mesh.svg \"Delaunay/Poisson 适合 static collider；GS2Mesh/TSDF、SuGaR/2DGS 更适合 visual mesh 对照和升级\")\n\n## 主要项目和模型\n\n| 项目 / 方法 | 简介 | 当前定位 | 实测/判断 |\n|---|---|---|---|\n| COLMAP Delaunay mesher | 利用 COLMAP dense workspace 直接生成 mesh | P0 scene collider 主路线 | 本项目 bedroom 场景输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB，适合 Web/Unity 静态碰撞代理 |\n| Open3D Poisson / BPA | 点云 + normals 到 watertight-ish mesh 的自动化 baseline | baseline / fallback / debug | 对 3DGS center point cloud 容易生成壳状伪影和漂浮面 |\n| CloudCompare / PoissonRecon | 点云人工检查、法线估计、Poisson 建面工具链 | 人工检查和传统建面对照 | 快速可视化好用，但不应直接作为唯一生产路线 |\n| GS2Mesh | 从训练后 3DGS 渲染 stereo/multiview，再估深并 TSDF fusion | P1/P2 object visual mesh benchmark | 思路比直接 Gaussian center 连面更合理；raw mesh 很大，需减面和清理 |\n| SuGaR | surface-aligned Gaussians + mesh extraction + editable mesh | P2 高质量 visual mesh 对照 | 需要额外环境和优化，短期不放进 P0 主链路 |\n| 2DGS / GOF | 从 Gaussian 表面约束角度改训练或优化形式 | P2/P3 研究升级 | 有潜力减少后处理 mesh 问题，但工程替换成本高 |\n| Neural SDF / NeuS / VolSDF | 神经隐式表面重建 | P3 离线高质量资产 | 训练成本高，和当前 3DGS 主链路并行成本大 |\n\n## 推荐路线\n\n```text\nscene collider:\n  COLMAP dense workspace -> Delaunay mesh -> simplify -> GLB\n\nobject visual mesh:\n  3DGS rendered RGB/depth/mask -> masked TSDF -> cleanup -> GLB\n\nquality benchmark:\n  GS2Mesh / SuGaR / 2DGS on selected objects or small scenes\n```\n\n## 判断\n\n当前 P0 应把 COLMAP Delaunay 作为场景 collider 主链路；Open3D/CloudCompare Poisson 做 baseline 和人工检查；GS2Mesh/SuGaR 做后续 per-object visual mesh 对照。这样可以先完成交互闭环，再逐步提高物体 mesh 质量。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和模型",
          "slug": "主要项目和模型"
        },
        {
          "level": "2",
          "text": "推荐路线",
          "slug": "推荐路线"
        },
        {
          "level": "2",
          "text": "判断",
          "slug": "判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-mesh-reconstruction-sugar",
      "title": "SuGaR",
      "category": "调研目录",
      "research_stage": "mesh-reconstruction",
      "research_stage_title": "Mesh 重建",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "SuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/sugar.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# SuGaR\n\n![SuGaR hybrid mesh editing](https://github.com/Anttwo/SuGaR/raw/main/media/blender/blender_edit.png \"SuGaR 将 Gaussian 绑定到 mesh surface 后，可在 Blender 等传统工具中通过 mesh 操作编辑/动画化 Gaussian 场景\")\n\n## 链接\n\n- Project / Code: https://github.com/Anttwo/SuGaR\n- Project page: https://anttwo.github.io/sugar/\n- Paper: https://arxiv.org/abs/2311.12775\n- Venue: CVPR 2024\n\n## 摘要要点\n\nSuGaR 的目标是从 3D Gaussian Splatting 中快速抽取可编辑 mesh，并把 mesh 与 surface-aligned Gaussians 绑定成 hybrid representation。它先让 Gaussians 更好贴合真实表面，再从贴合后的 Gaussians 采样 surface points 并用 Poisson reconstruction 得到 mesh；后续还可以联合优化 mesh 和 Gaussians，让传统 mesh 编辑、rigging、animation、relighting 可以间接作用到 Gaussian 场景。\n\n这条路线的意义不是“给 P0 碰撞一个更快替代品”，而是把 3DGS 从纯视觉表示推进到可编辑资产表示。它对后续 Unity/Blender/Unreal 工作流更友好，但训练、环境和后处理成本比 Delaunay collider 更高。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| vanilla 3DGS warm-up | 先训练短程 3DGS，让 Gaussians 粗略覆盖场景 |\n| SuGaR optimization | 加 surface alignment regularization，使 Gaussians 更贴近 scene surface |\n| mesh extraction | 从 aligned Gaussians 采样 surface points，并通过 Poisson 抽 mesh |\n| SuGaR refinement | 联合优化 mesh 和 Gaussians，形成 Mesh + Gaussians hybrid 表示 |\n| optional textured mesh | 导出传统 textured mesh，便于 Blender/Unity/Unreal 检查和编辑 |\n\n输入：COLMAP 格式数据或已有 3DGS 训练结果。输出：coarse/refined mesh、surface-bound Gaussians、可选 textured mesh。\n\n## 在 Video2Mesh 中的位置\n\n适合作为 P2 高质量 visual mesh 路线。它可以帮助回答“如果我们后续需要可编辑场景资产，而不是只要 collider，应该往哪里走”。但是短期不应该进入 P0，因为 P0 的目标是稳定的 static collision proxy 和 simulator asset bundle，而不是最漂亮的 mesh。\n\n## 接入判断\n\n- P0：不进入，依赖和训练时间不适合当前闭环。\n- P1：可作为 high-quality visual mesh baseline，和 GS2Mesh、2DGS/GOF 放在同一组对照。\n- P2/P3：如果后面要把 mesh 编辑、物体动画、Blender/Unity 资产修改接入 Video2Mesh，可以重新评估 SuGaR hybrid representation。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-mesh-completion-hunyuan3d",
      "title": "Hunyuan3D",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Hunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/hunyuan3d.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Hunyuan3D\n\n![Hunyuan3D-2 examples](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/assets/images/teaser.jpg \"Hunyuan3D-2/2.1 面向高分辨率 textured 3D asset generation，可从文本/图像条件生成 object mesh\")\n\n## 链接\n\n- GitHub: https://github.com/Tencent-Hunyuan/Hunyuan3D-2\n- Model / demo: https://huggingface.co/tencent/Hunyuan3D-2\n- Project family: Hunyuan3D-2 / Hunyuan3D-2.1\n\n## 摘要要点\n\nHunyuan3D 面向 text/image conditioned 3D asset generation。对 Video2Mesh 来说，它不是场景级重建工具，而是 object completion backend：当扫描视频中的某个物体被遮挡、破碎或只需要单独生成更干净的 mesh 时，可以用 object crop/reference image 作为输入，生成 object-local mesh。\n\n它通常能给出比传统点云补洞更“像物体”的外观，但尺度、坐标、物理可用性和语义归属都不是天然正确的。因此输出不能直接进 simulator，需要回填 bbox、pose、semantic id、material 和 collider。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| object reference preparation | 从 SAM/GDINO/semantic mesh 中裁出物体参考图 |\n| 3D generation | 生成 object mesh/texture |\n| format normalization | 转为 GLB/OBJ 等可导入格式 |\n| Video2Mesh import | 按 object id 回填尺度、bbox、pose、semantic sidecar |\n| collider generation | 用 primitive/convex/static mesh 生成物理代理 |\n\n输入：物体 crop / reference image，也可以配合文字 prompt。输出：object-local mesh / GLB，以及可选 texture。\n\n## 在 Video2Mesh 中的位置\n\nP1 object visual completion。它可以接在 `prepare-object-images -> export-image-blaster -> mesh-commands` 后面，也可以作为 image-blaster 的默认 backend 之一。当前最适合优先测试床、椅子、柜子、小物体等 foreground objects。\n\n输出结果需要简单摘出来看：\n\n- 几何是否闭合、是否有薄片/飞面。\n- 纹理是否和原始视频一致。\n- 尺度是否可通过 bbox fitting 拉回场景坐标。\n- 是否需要另建 primitive/convex collider，而不是直接用 visual mesh 碰撞。\n\n## 接入判断\n\n- P0：不进入，P0 不应依赖 generative object mesh。\n- P1：进入 object completion 实验，优先跑 2-3 个物体并记录 GLB、bbox fit、collider 质量。\n- 风险：生成结果可能“好看但不物理”，所以必须拆成 visual mesh 和 collider proxy 两层。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-mesh-completion-image-blaster-object-jobs",
      "title": "image-blaster Object Jobs",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/image-blaster-object-jobs.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# image-blaster Object Jobs\n\n![image-blaster object jobs](assets/uploaded/video2mesh-object-mesh-completion-image-blaster-object-jobs/pipeline-overview.svg \"image-blaster 的 object job 目录约定可作为 Video2Mesh 物体补全后端的桥接层\")\n\n## 链接\n\n- Local reference repo: `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/image-blaster`\n- Object generation script: `image-blaster/scripts/generate-single-asset.mjs`\n- Video2Mesh bridge: `prepare-object-images -> export-image-blaster -> import-object-meshes`\n\n## 简介\n\nimage-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。这种目录约定很适合 Video2Mesh：每个 object 的输入图、prompt、输出 mesh、预览、失败日志和 provenance 都能集中保存。\n\n需要注意的是，image-blaster object job 解决的是“为物体生成 visual mesh”，不是“生成仿真资产包”。尺度、pose、semantic id、collider、mass/friction 和 Unity/MuJoCo/Isaac adapter 仍由 Video2Mesh 承接。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object crop/reference | Video2Mesh 从 mask/selected frame 准备输入图 |\n| job directory | 写入 `worlds/<world>/output/<object>/object.json` |\n| backend generation | 调用 Hunyuan3D/Meshy 等生成 GLB/OBJ |\n| viewer check | React/Three.js 查看 object mesh |\n| import back | Video2Mesh 回填 object-local mesh 并 bbox fitting |\n\n## 输入与输出\n\n输入：object crop、prompt、world object config、object id。输出：`object.json`、GLB/OBJ、reference image、viewer assets 和生成日志。\n\n## 在 Video2Mesh 中的位置\n\n可借用目录约定和 object job 思路，但 simulator bundle 仍由 Video2Mesh 导出。它适合接在正式 semantic mesh 的 object split 之后，优先补 bed、nightstand、lamp 等可解释对象。\n\n## 接入判断\n\n- P0：不进入。\n- P1：作为 object mesh generation bridge。\n- 风险：后端生成物体的尺度和朝向不可信，必须 `fit-object-local-meshes-to-bbox` 并另建 collider。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-mesh-completion-instantmesh",
      "title": "InstantMesh",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "InstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/instantmesh.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# InstantMesh\n\n![InstantMesh](assets/uploaded/video2mesh-object-mesh-completion-instantmesh/stage-completion.svg \"InstantMesh 代表快速 image-to-mesh 的 feed-forward 物体补全路线\")\n\n## 链接\n\n- Project page: https://jiahao.ai/instantmesh/\n- GitHub: https://github.com/TencentARC/InstantMesh\n- Paper: https://arxiv.org/abs/2404.07191\n\n## 摘要要点\n\nInstantMesh 是 feed-forward sparse-view 3D mesh reconstruction 路线，目标是从单图或少量视图快速生成带纹理的 3D mesh。相比逐物体优化，它的优势是速度和批量化；相比 Hunyuan3D/Meshy 等生成服务，它更适合作为本地可控 baseline。\n\n对 Video2Mesh 来说，InstantMesh 可以作为 object completion 的快速对照：同一批 object crops 同时跑 Hunyuan3D/image-blaster 和 InstantMesh，比较闭合性、尺度拟合、纹理一致性和 collider 生成难度。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object image preparation | 从 selected frame / mask 中取 object crop |\n| novel-view / reconstruction | feed-forward 生成多视角或 3D 表示 |\n| mesh extraction | 输出 textured mesh |\n| bbox fitting | 对齐回 Video2Mesh object bbox |\n| collider proxy | 生成 primitive/convex collider |\n\n## 输入与输出\n\n输入：单图或少量多视角物体图像。输出：object mesh、texture、预览图和可回填 Video2Mesh 的 object-local visual asset。\n\n## 在 Video2Mesh 中的位置\n\nP1 批量候选，可能需要更多纹理和尺度修正。它适合先跑 2-3 个清晰物体，作为 Hunyuan3D/Meshy 的开源 baseline。\n\n## 接入判断\n\n- P0：不进入。\n- P1：用于批量 object mesh baseline。\n- 风险：真实室内物体遮挡严重时，单图生成可能和原场景外观不一致。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-mesh-completion-meshy",
      "title": "Meshy",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Meshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/meshy.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Meshy\n\n![Meshy](assets/uploaded/video2mesh-object-mesh-completion-meshy/stage-completion.svg \"Meshy 是商业 image/text-to-3D 服务，适合快速得到展示级 object mesh\")\n\n## 链接\n\n- Meshy: https://www.meshy.ai/\n- Meshy API docs: https://docs.meshy.ai/\n- image-blaster backend reference: `image-blaster/scripts/generate-single-asset.mjs`\n\n## 简介\n\nMeshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。它的优势是工程接入成本低、生成结果适合汇报预览；缺点是外部服务依赖、结果可控性和 provenance/授权需要记录。\n\n在 image-blaster 里，Meshy 可以作为 Hunyuan3D 的 alternative backend。Video2Mesh 需要把它定位为 object visual completion provider，而不是仿真资产生成器。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| prompt/reference image | 从 object crop 或文字描述构造任务 |\n| Meshy generation | 调用 image/text-to-3D 服务 |\n| asset download | 获取 mesh、texture、thumbnail |\n| Video2Mesh import | 按 object id 回填并 bbox fitting |\n| collider rebuild | 生成 primitive/convex collider |\n\n## 输入与输出\n\n输入：图片或文本 prompt。输出：mesh、texture、thumbnail、服务端任务记录和下载链接。\n\n## 在 Video2Mesh 中的位置\n\nP1 快速补全候选，需记录 provenance 和人工 QA。适合在导师汇报里快速展示 object completion 的潜力，但最终主链路仍要可复现和可控。\n\n## 接入判断\n\n- P0：不进入。\n- P1：作为商业 baseline/快速 demo 后端。\n- 风险：外部 API、费用、服务端版本变化和生成尺度不确定。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "object-mesh-completion",
      "title": "物体 Mesh 补全阶段",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "梳理 Hunyuan3D、Meshy、TRELLIS、InstantMesh、image-blaster 等物体级生成和补全方案。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Object Mesh",
        "Hunyuan3D",
        "image-blaster",
        "调研目录"
      ],
      "body": "\n# 物体 Mesh 补全阶段\n\n物体级补全适合从 object crops、selected frames、mask 和粗 3D bbox 出发，生成 object-local visual mesh，再对齐回原始场景。\n\n## 主要项目和模型\n\n| 项目 / 方法 | 简介 | 输入输出 | 对 Video2Mesh 的作用 | 注意 |\n|---|---|---|---|---|\n| Hunyuan3D | 单图/少图到 3D asset 的生成式模型/服务生态 | 输入 reference image，输出 mesh/texture | 可作为 image-blaster object mesh backend，补全遮挡物体外观 | 尺度、朝向、支撑面必须由 Video2Mesh 校准 |\n| Meshy | 商业 3D asset 生成服务 | 文本/图片到 mesh | 可作为 object mesh alternative backend | 结果需要 provenance 和 QA |\n| TRELLIS | 3D asset generation 研究/开源路线 | 图片/文本到 3D asset | 可作为本地或远端 object completion 候选 | 环境、质量和授权需单独评估 |\n| InstantMesh | feed-forward image-to-3D mesh 方案 | 单图/多视图到 mesh | 快速生成 object-local mesh baseline | 复杂遮挡和真实尺度需要后处理 |\n| image-blaster | 管理 world/object 目录、reference image、Hunyuan/Meshy jobs 和 React/Three viewer 的工程项目 | `worlds/<world>/output/<object>/object.json`、GLB/OBJ | 可复用其 object mesh generation convention 和 viewer 思路 | 它不是 simulator bundle 生成器 |\n\n## 接入 Video2Mesh 的正确位置\n\n```text\nobject masks / selected frames\n  -> prepare-object-images\n  -> export-image-blaster\n  -> Hunyuan3D / Meshy / TRELLIS / InstantMesh\n  -> import-object-meshes\n  -> fit-object-local-meshes-to-bbox\n  -> export-simulator-assets\n```\n\n## 关键 QA\n\n- object-local mesh 是否对齐 observed 3D bbox。\n- 支撑面是否贴近 floor/table/chair seat。\n- scale 是否可信。\n- 是否需要拆分 visual mesh 和 collider proxy。\n- 补全来源和置信度是否写入 metadata，便于导师/用户知道哪些部分是生成的。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和模型",
          "slug": "主要项目和模型"
        },
        {
          "level": "2",
          "text": "接入 Video2Mesh 的正确位置",
          "slug": "接入-video2mesh-的正确位置"
        },
        {
          "level": "2",
          "text": "关键 QA",
          "slug": "关键-qa"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-mesh-completion-trellis",
      "title": "TRELLIS",
      "category": "调研目录",
      "research_stage": "object-mesh-completion",
      "research_stage_title": "物体 Mesh 补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "TRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/trellis.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# TRELLIS\n\n![TRELLIS](assets/uploaded/video2mesh-object-mesh-completion-trellis/stage-completion.svg \"TRELLIS 是较新的 3D asset generation 路线，可作为物体补全候选\")\n\n## 链接\n\n- Project page: https://microsoft.github.io/TRELLIS/\n- GitHub: https://github.com/microsoft/TRELLIS\n- Paper: https://arxiv.org/abs/2412.01506\n\n## 摘要要点\n\nTRELLIS 代表新一代 3D asset generation 路线，关注从图像或文本条件生成结构较完整的 3D assets。它对 Video2Mesh 的价值和 Hunyuan3D 类似：不是替代场景级重建，而是补全单个 object visual mesh。\n\n这类模型通常能生成更完整、更规整的物体外观，但物理尺度、真实场景对齐和碰撞代理仍需要 Video2Mesh 后处理。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object crop/prompt | 从语义物体准备图像或文字条件 |\n| asset generation | 生成 3D asset representation |\n| mesh/texture export | 导出 GLB/OBJ 或等价格式 |\n| scene alignment | bbox/pose 对齐回扫描场景 |\n| physics proxy | 重建 collider 和 material metadata |\n\n## 输入与输出\n\n输入：单图、多视图或文本/图像条件。输出：3D asset、visual mesh、texture 和预览。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2 物体补全候选，重点测试遮挡物体。可以作为 Hunyuan3D/Meshy/InstantMesh 的对照模型。\n\n## 接入判断\n\n- P0：不进入。\n- P1：用于 object mesh completion 对照。\n- P2：评估更复杂 object asset generation。\n- 风险：环境和显存需求、授权、尺度一致性都要单独确认。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "object-simulation",
      "title": "物体仿真阶段",
      "category": "调研目录",
      "research_stage": "object-simulation",
      "research_stage_title": "物体仿真",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "按刚体、软体、动态 Gaussian 三条线整理物体交互和 Sim Anything / PhysSplat 的关系。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Simulation",
        "PhysSplat",
        "SimAnything",
        "调研目录"
      ],
      "body": "\n# 物体仿真阶段\n\n物体仿真应分为刚体、软体和 dynamic Gaussian 三条线。它们消费的资产合同不同，不应强行合并成一个 mesh。\n\n![物体仿真](assets/uploaded/object-simulation/stage-simulation.svg \"刚体、软体和 dynamic Gaussian 三种物体仿真路径\")\n\n## 主要路线\n\n| 路线 | 简介 | 适合对象 | 对 Video2Mesh 的意义 |\n|---|---|---|---|\n| Rigid body simulation | 刚体 + collider + mass/friction/restitution | 桌椅、杯子、柜门、盒子 | P1 物体交互闭环，最容易进入 Unity/MuJoCo/Isaac |\n| Soft body / cloth | 布料、枕头、被子、植物叶片等形变对象 | pillow、blanket、curtain、plant | 需要比刚体更复杂的材质和 solver |\n| PhysSplat / Sim Anything | MLLM 估计物理属性，粒子/高斯动态模拟，动态 splat 渲染 | 非刚体、局部形变、动态视觉展示 | P2 研究旁线，可为物理属性估计和 dynamic Gaussian 提供启发 |\n| VLM physical property inference | 用 VLM/MLLM 估计材质、质量范围、摩擦、可移动性 | 所有 object metadata | 可作为 simulator_asset_bundle 的初稿，但必须 QA |\n\n## Sim Anything / PhysSplat 的定位\n\nPhysSplat 的目标不是把 3DGS 转成传统 mesh，而是把物理属性估计和动态模拟注入 semantic Gaussian/particle 表示中。它对我们后续做布料、枕头、植物等非刚体交互有启发，但短期不替代 mesh/collider 主链路。\n\n当前建议：\n\n- P0/P1：先做 rigid-body 资产合同，即 visual mesh + collider + physics sidecar。\n- P2：对特定对象探索 dynamic Gaussian 或 PhysSplat-style 物理属性估计。\n- 所有自动推理出的质量、摩擦、恢复系数都要标注来源和置信度。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要路线",
          "slug": "主要路线"
        },
        {
          "level": "2",
          "text": "Sim Anything / PhysSplat 的定位",
          "slug": "sim-anything-physsplat-的定位"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-simulation-physsplat-sim-anything",
      "title": "PhysSplat / Sim Anything",
      "category": "调研目录",
      "research_stage": "object-simulation",
      "research_stage_title": "物体仿真",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/physsplat-sim-anything.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# PhysSplat / Sim Anything\n\n![PhysSplat / Sim Anything pipeline](https://sim-gs.github.io/static/images/pipeline.jpg \"Sim Anything / PhysSplat pipeline：open-vocabulary 3D segmentation -> MLLM physical property perception -> PGAS particle sampling + MPM simulation -> render\")\n\n## 链接\n\n- Project page: https://sim-gs.github.io/\n- Paper: https://arxiv.org/abs/2411.12789\n- Code placeholder: https://github.com/CHNxindong/sim-anything\n- Venue: ICCV 2025\n\n## 摘要要点\n\nSim Anything / PhysSplat 的目标不是把 3DGS 转成传统 mesh collider，而是让静态 3DGS 场景里的物体获得可交互动态。它先做 open-vocabulary object segmentation，再用 MLLM 推断物体物理属性，接着用 Material Property Distribution Prediction 估计属性分布，最后通过 Physical-Geometric Adaptive Sampling 采样粒子并进行 MPM simulation。\n\n这条路线和 Video2Mesh 当前“视觉代理 + 碰撞代理 + 语义/物理 sidecar”的分层思路不同。它更像是把物理仿真注入 Gaussian/particle 表示里，适合 deformable object 或动态效果研究；但如果要接 Unity/MuJoCo/Isaac 的标准 asset bundle，仍然需要传统 collider、mass、friction、restitution、joint/constraint 等结构化资产。\n\n## Pipeline\n\n## 输入与输出\n\n| 阶段 | 作用 |\n|---|---|\n| 3D open-vocabulary segmentation | 从开放世界场景中定位需要仿真的目标物体 |\n| multi-view inpainting | 补齐目标移动/变形后可能暴露的背景 |\n| MLLM-P3 | 通过多模态大模型推断物体的平均物理属性 |\n| MPDP | 将平均物理属性扩展为分布，降低精确手工标注需求 |\n| PGAS + MPM | 按几何和物理属性采样粒子，执行 material point simulation |\n\n输入：3DGS 场景、物体分割、交互力或动作条件。输出：物体动态响应、模拟粒子/动态 Gaussian 表示、渲染视频或交互结果。\n\n## 在 Video2Mesh 中的位置\n\n适合作为 P2/P3 的研究方向，尤其在“物体交互”阶段提供参考：如何从语义物体推断物理属性，如何处理软体/可变形物体，如何把 3DGS 视觉和物理动态联系起来。\n\n短期不进入主链路。原因是当前可复现实验和工程接口仍不如传统 physics engine 稳定，而且它的输出不直接等价于 Video2Mesh 需要的 simulator asset bundle。\n\n## 接入判断\n\n- P0：不进入。\n- P1：可以借鉴 MLLM 物理属性推断，把 material、mass、friction/restitution 的默认值写入 Video2Mesh sidecar。\n- P2/P3：跟踪 dynamic Gaussian / MPM 方向，后面做 deformable object demo 时再尝试复现。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-simulation-rigid-body",
      "title": "Rigid Body Interaction",
      "category": "调研目录",
      "research_stage": "object-simulation",
      "research_stage_title": "物体仿真",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/rigid-body.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Rigid Body Interaction\n\n![Rigid body interaction](assets/uploaded/video2mesh-object-simulation-rigid-body/stage-simulation.svg \"刚体交互是 Video2Mesh 物体交互的第一步：visual mesh、collider 和 physics metadata 必须分离\")\n\n## 链接\n\n- Rapier rigid bodies: https://rapier.rs/docs/user_guides/javascript/rigid_bodies/\n- Unity Rigidbody manual: https://docs.unity3d.com/6000.0/Documentation/Manual/RigidbodiesOverview.html\n- MuJoCo modeling: https://mujoco.readthedocs.io/en/stable/modeling.html\n\n## 简介\n\n刚体是物体交互第一步，要求 visual mesh、collider、mass、friction、restitution 和 body type 分离。对于室内扫描场景，很多物体先不需要复杂软体仿真：床头柜、灯、盒子、杯子、椅子、门等都可以先用 rigid body 或 static body 建交互闭环。\n\n刚体交互的关键不是 mesh 好不好看，而是 collider 是否保守、重心是否合理、支撑关系是否正确、物理参数是否稳定。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object split | 从 semantic mesh 拆出物体候选 |\n| collider selection | primitive / convex hull / convex decomposition |\n| physics metadata | 估计 body_type、mass、friction、restitution |\n| engine binding | Rapier/Unity/MuJoCo/Isaac adapter |\n| QA | 推动、掉落、支撑、穿透、稳定性测试 |\n\n## 输入与输出\n\n输入：object mesh、collider、physics metadata、scene support relations。输出：可移动或可碰撞物体、rigid body config、engine adapter。\n\n## 在 Video2Mesh 中的位置\n\nP1 首选。当前 formal semantic mesh 已经能给出 object split，下一步可以从 bed/nightstand/lamp 这类对象开始：bed 大概率 static/support，nightstand 可 static 或 dynamic，lamp 可 dynamic/fragile。\n\n## 接入判断\n\n- P0：不阻塞，但 static collider 是刚体交互基础。\n- P1：进入 object interaction 主线。\n- 风险：物理参数不能只靠类别猜测，需要可视化 QA 和默认值表。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-simulation-soft-body-cloth",
      "title": "Soft Body / Cloth",
      "category": "调研目录",
      "research_stage": "object-simulation",
      "research_stage_title": "物体仿真",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/soft-body-cloth.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Soft Body / Cloth\n\n![Soft body / cloth](assets/uploaded/video2mesh-object-simulation-soft-body-cloth/stage-simulation.svg \"窗帘、被子、枕头等软体对象需要独立仿真路线，短期先用静态代理\")\n\n## 链接\n\n- NVIDIA Isaac Sim physics fundamentals: https://docs.isaacsim.omniverse.nvidia.com/4.5.0/physics/simulation_fundamentals.html\n- Unity cloth component: https://docs.unity3d.com/6000.0/Documentation/Manual/class-Cloth.html\n- Taichi cloth simulation reference: https://docs.taichi-lang.org/docs/cloth_simulation\n\n## 简介\n\n窗帘、床品、枕头、植物叶片等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。短期 Video2Mesh 不应该为了这些对象阻塞 P1 刚体闭环，可以先把它们标记为 soft/deformable candidate，并用 static proxy 或简化面片做保守交互。\n\n后续如果要做可拉动窗帘、可变形被子或枕头碰撞，需要 cloth mesh、constraints、material stiffness、damping、collision thickness 等更复杂数据。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| soft object detection | 从 label/shape 识别 curtain、blanket、pillow 等 |\n| proxy selection | 短期用 static mesh、thin box 或 support surface |\n| cloth/soft mesh prep | 清理拓扑、生成边约束、质量点 |\n| material estimation | 估计 stiffness、damping、mass density |\n| engine simulation | Unity cloth、Isaac deformable、MPM 等 |\n\n## 输入与输出\n\n输入：cloth mesh、constraints、material、collision proxy。输出：软体/布料仿真配置、动态 visual mesh 或 dynamic Gaussian candidate。\n\n## 在 Video2Mesh 中的位置\n\nP2，先用静态代理或简化面片。formal semantic mesh 中 curtain 和 bed/blanket 类区域可以先标注为 soft candidate，为后续 Sim Anything/PhysSplat 方向留接口。\n\n## 接入判断\n\n- P0：不进入。\n- P1：只保留 static/primitive proxy。\n- P2/P3：探索 cloth/MPM/dynamic Gaussian。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-object-simulation-vlm-physical-properties",
      "title": "VLM Physical Properties",
      "category": "调研目录",
      "research_stage": "object-simulation",
      "research_stage_title": "物体仿真",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "VLM 可估计物体类别、材质、可抓取性、是否可移动等属性，但数值物理参数仍需校准。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/vlm-physical-properties.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# VLM Physical Properties\n\n![VLM physical properties](assets/uploaded/video2mesh-object-simulation-vlm-physical-properties/stage-simulation.svg \"VLM 可为 simulator asset bundle 生成物体材质、可移动性和物理参数初稿\")\n\n## 链接\n\n- GPT-4o model docs: https://platform.openai.com/docs/models/gpt-4o\n- LLaVA project: https://llava-vl.github.io/\n- PhysSplat / Sim Anything: https://sim-gs.github.io/\n\n## 简介\n\nVLM 可估计物体类别、材质、可抓取性、是否可移动、是否支撑其他物体等属性，也可以为 mass、friction、restitution 给出初始范围。Sim Anything / PhysSplat 也使用 MLLM 推断物理属性，这说明视觉语言模型在物理 sidecar 里有价值。\n\n但 VLM 输出不应直接作为真值：数值物理参数仍需默认表、规则约束和运行时 QA。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| evidence packing | 收集 object crop、多视角截图、label、bbox |\n| VLM inference | 输出 material、movable、fragile、support 等 hints |\n| rule normalization | 映射到 mass/friction/restitution/body_type 默认表 |\n| confidence/provenance | 记录模型、prompt、证据图和置信度 |\n| QA loop | 运行物理引擎检查稳定性 |\n\n## 输入与输出\n\n输入：图像、object crop、语义标签、bbox、support relation。输出：material/body hints、physics defaults、affordance、可读描述。\n\n## 在 Video2Mesh 中的位置\n\nP1 辅助填写 simulator asset bundle。比如 bed -> static/support/cloth material，floor -> static/high friction，lamp -> dynamic/fragile/low mass 等，都可以先由 VLM 给初稿，再人工或规则校正。\n\n## 接入判断\n\n- P0：不进入必需链路。\n- P1：进入 metadata 生成和审核工作流。\n- 风险：VLM 幻觉和单位不一致，需要 schema、默认表和数值范围约束。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-pointcloud-completion-background-clean-plate",
      "title": "Background Clean Plate",
      "category": "调研目录",
      "research_stage": "pointcloud-completion",
      "research_stage_title": "点云/背景补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "clean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/background-clean-plate.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Background Clean Plate\n\n![Background clean plate](assets/uploaded/video2mesh-pointcloud-completion-background-clean-plate/stage-completion.svg \"Clean plate 把前景物体移除后暴露的背景补齐，是 World Labs / image-blaster 类工业路线的关键思想\")\n\n## 链接\n\n- World Labs: https://www.worldlabs.ai/\n- Marble API docs: https://docs.worldlabs.ai/\n- image-blaster world generation reference: `image-blaster/scripts/generate-world.mjs`\n\n## 简介\n\nClean plate 是把前景物体移除后，补齐被遮挡的地板、墙面、柜体或背景。World Labs / Marble 与 image-blaster 的工业路线都体现了这个思想：背景世界和前景物体分开处理，背景可以生成 static world/splat/collider，物体再单独生成或回填。\n\n对 Video2Mesh 来说，clean plate 和 object mesh completion 必须分开。补一个完整椅子 mesh 不等于恢复椅子后面的地板；修复背景图也不等于生成可碰撞物体。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| foreground masks | 识别要移除或单独处理的物体 |\n| scene description | 形成去掉 foreground 后的 clean background prompt |\n| background inpainting/generation | 修复图像、3DGS 或 static world |\n| geometry consistency | 与原 COLMAP/mesh 坐标对齐 |\n| collider update | 补地面/墙体等 static collider 缺口 |\n\n## 输入与输出\n\n输入：场景描述、移除物体 masks、背景参考图、相机和深度。输出：修复背景图、static world assets、补全地面/墙体 mesh 或 clean plate provenance。\n\n## 在 Video2Mesh 中的位置\n\nP1 背景补全，和 object mesh completion 分开。短期可以先从被床/柜遮挡的地面与墙面区域做实验，不直接依赖生成整套 world。\n\n## 接入判断\n\n- P0：不进入，P0 先基于真实扫描。\n- P1：用于物体移除后的背景/地面修复。\n- 风险：多视角一致性难，生成内容必须标注为 synthetic。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-pointcloud-completion-floater-cleaning",
      "title": "Floater Cleaning",
      "category": "调研目录",
      "research_stage": "pointcloud-completion",
      "research_stage_title": "点云/背景补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/floater-cleaning.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Floater Cleaning\n\n![Floater cleaning](assets/uploaded/video2mesh-pointcloud-completion-floater-cleaning/stage-completion.svg \"清理点云和 3DGS 漂浮点能显著改善后续 mesh 重建与相机 framing\")\n\n## 链接\n\n- Open3D statistical outlier removal: https://www.open3d.org/docs/latest/tutorial/Advanced/pointcloud_outlier_removal.html\n- SuperSplat editing: https://playcanvas.com/products/supersplat\n- 3DGS pruning reference: https://github.com/graphdeco-inria/gaussian-splatting\n\n## 简介\n\nFloater cleaning 指清理 3DGS/点云中的漂浮点、长尾离群点、低 opacity 结构和异常尺度高斯。它能改善截图、viewer framing、mesh reconstruction 和 semantic transfer。尤其是把 Gaussian center 当作点云做 Poisson 时，未清理的飞点会把 surface 拉成壳状或大面积粘连。\n\n清理不能过度：窗帘、椅腿、灯、床品边缘等真实薄结构也可能看起来像离群点，需要分类型阈值和人工 QA。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| statistics | 统计 bbox quantile、opacity、scale、distance、component |\n| outlier filtering | 移除远端点、低贡献高斯和孤立分量 |\n| optional manual edit | 用 SuperSplat/CloudCompare 人工检查 |\n| rebuild downstream | 重新导出 mesh、semantic splats 或 viewer assets |\n| QA | 对比截图、mesh face coverage 和 object labels |\n\n## 输入与输出\n\n输入：point cloud、Gaussian PLY、semantic splats。输出：cleaned point cloud / cleaned Gaussian、过滤报告、QA 截图。\n\n## 在 Video2Mesh 中的位置\n\nP0 预处理，应放在 semantic transfer 和 mesh 重建前。本周 Open3D Poisson 的壳状伪影说明，点云/高斯清理是直接影响 mesh 质量的上游步骤。\n\n## 接入判断\n\n- P0：进入，至少记录过滤前后统计。\n- P1：和 semantic/object-aware cleanup 结合，避免删真实物体。\n- 风险：阈值场景相关，需要可视化审核。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-pointcloud-completion-inpainting",
      "title": "2D/3D Inpainting",
      "category": "调研目录",
      "research_stage": "pointcloud-completion",
      "research_stage_title": "点云/背景补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/inpainting.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 2D/3D Inpainting\n\n![2D/3D inpainting](assets/uploaded/video2mesh-pointcloud-completion-inpainting/stage-completion.svg \"2D/3D inpainting 可以修复纹理或几何缺口，但不能直接替代物理可信 collider\")\n\n## 链接\n\n- LaMa image inpainting: https://github.com/advimman/lama\n- Stable Diffusion inpainting: https://huggingface.co/docs/diffusers/using-diffusers/inpaint\n- Instruct-NeRF2NeRF reference: https://instruct-nerf2nerf.github.io/\n\n## 简介\n\n2D inpainting 修复单帧图像纹理，3D inpainting 或 scene completion 尝试补点、补 surface 或补 radiance field。它们适合修复视觉缺口，但不能直接被当作物理真实 collider。对 Video2Mesh 来说，inpainting 最好服务 clean plate、纹理补全和 visual mesh；碰撞层仍要保守处理。\n\n多视角一致性是最大挑战：单帧看起来合理，不代表从其他相机角度也成立。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| mask selection | 定义缺损区域或要移除的物体 |\n| 2D inpainting | 修复单帧图像 |\n| multi-view consistency | 检查跨帧纹理/深度一致性 |\n| optional 3D update | 重建或更新 3DGS/mesh/texture |\n| metadata | 标注 synthetic region 和置信度 |\n\n## 输入与输出\n\n输入：masks、images、depth、point cloud 或 mesh。输出：修复图像、修复纹理、补点/补 surface 或 clean plate evidence。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2，不应直接伪造物理可信 collider。短期可以作为 object/background visual repair 的候选，而不是 simulator bundle 的物理来源。\n\n## 接入判断\n\n- P0：不进入。\n- P1：用于 clean plate 和纹理补全。\n- 风险：生成内容必须可追踪，不能和真实扫描混淆。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "pointcloud-completion",
      "title": "点云清理与背景补全阶段",
      "category": "调研目录",
      "research_stage": "pointcloud-completion",
      "research_stage_title": "点云/背景补全",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "整理点云去噪、背景 clean plate、2D/3D inpainting 和场景结构补全在 Video2Mesh 中的位置。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Completion",
        "Point Cloud",
        "Inpainting",
        "调研目录"
      ],
      "body": "\n# 点云清理与背景补全阶段\n\n补全不是一个单独按钮。对 Video2Mesh 来说，至少要拆成三件事：点云/高斯清理、背景 clean plate、场景结构补全。\n\n![点云与补全阶段](assets/uploaded/pointcloud-completion/stage-completion.svg \"物体外观补全、背景 clean plate 和物理代理补全需要拆开处理\")\n\n## 主要方向\n\n| 方向 | 简介 | 项目中的作用 | 风险 |\n|---|---|---|---|\n| 3DGS floater cleaning | 根据 opacity、scale、elongation、空间离群过滤高斯 | 让 3DGS 视觉层更干净，也避免后续点云建面被远端漂浮点拉坏 | 过度清理会删掉真实薄结构 |\n| Point cloud outlier removal | quantile bbox、statistical/radius outlier、voxel downsample | 给 Poisson、Delaunay preview、semantic projection 提供更稳输入 | 参数依赖场景 |\n| Background clean plate | 移除前景物体后补全地板/墙面/背景图像，再更新背景 3D 表征 | 当物体可移动时，恢复被遮挡的地面/墙面 | 需要真实 2D masks 和多视角一致性 |\n| 2D image/video inpainting | 对视频帧局部缺失区域补图 | clean plate 的前置工具 | 单帧好看不代表多视角一致 |\n| Scene layout / plane fitting | floor/wall/ceiling/door/window/cabinet 等结构化估计 | 给 collider、navmesh、support plane 提供稳定结构 | 自动识别门窗柜等细类仍需 VLM/scene graph 增强 |\n\n## 和物体补全的边界\n\n```text\nobject completion:\n  补全被遮挡物体本身\n\nbackground clean plate:\n  补全物体移开后露出的地板/墙面\n\nphysics proxy completion:\n  补全交互需要的保守碰撞形状\n```\n\n这三件事不能混在一起。一个完整椅子 mesh 不能自动恢复椅子背后的地板；一个好看的 inpainted 背景也不能直接提供椅子的碰撞体。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要方向",
          "slug": "主要方向"
        },
        {
          "level": "2",
          "text": "和物体补全的边界",
          "slug": "和物体补全的边界"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-pointcloud-completion-scene-layout",
      "title": "Scene Layout Completion",
      "category": "调研目录",
      "research_stage": "pointcloud-completion",
      "research_stage_title": "点云/背景补全",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/scene-layout.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Scene Layout Completion\n\n![Scene layout completion](assets/uploaded/video2mesh-pointcloud-completion-scene-layout/stage-completion.svg \"Scene layout completion 把墙、地、天花板、门窗和支撑面抽象成可交互结构\")\n\n## 链接\n\n- Open3D plane segmentation: https://www.open3d.org/docs/latest/python_api/open3d.geometry.PointCloud.html#open3d.geometry.PointCloud.segment_plane\n- PlaneRCNN reference: https://github.com/NVlabs/planercnn\n- Structured3D dataset reference: https://structured3d-dataset.org/\n\n## 简介\n\nScene layout completion 关注墙、地、天花板、门窗、柜体等大结构，用于 collider、导航边界、支撑关系和可编辑场景结构。它比单纯补纹理更接近交互需求：用户要走、点击、放置物体，首先需要稳定 floor/wall/support planes。\n\n对室内场景，布局补全可以从 plane fitting、semantic labels 和 VLM 关系推理开始，不一定要先跑复杂生成模型。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| semantic mesh / point cloud | 提供 floor/wall/window/door/cabinet 等候选 |\n| plane / primitive fitting | 拟合 floor、wall、ceiling、support plane |\n| topology repair | 补齐墙角、地面边界和被遮挡支撑面 |\n| collider export | 输出 layout primitives 或 simplified structure mesh |\n| scene graph binding | 标注 support/on/near/inside 等关系 |\n\n## 输入与输出\n\n输入：点云、mesh、语义、VLM/scene graph。输出：layout primitives、结构 mesh、support planes、navigation/collider boundaries。\n\n## 在 Video2Mesh 中的位置\n\nP1 物理代理补全，比视觉补纹理更重要。正式 semantic mesh 已经有 floor、wall、window、door 等标签，下一步可以先从 floor/wall plane fitting 做起。\n\n## 接入判断\n\n- P0：不作为首要阻塞，但 floor/wall primitive 可作为 collider fallback。\n- P1：进入支持放置、导航和物体关系推理。\n- 风险：自动补全可能改变真实空间尺度，必须和 COLMAP 坐标对齐。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-semantic-scene-graph-grounded-sam",
      "title": "Grounded-SAM / Open-vocabulary Detection",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Grounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/grounded-sam.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Grounded-SAM / Open-vocabulary Detection\n\n![Grounded-SAM](assets/uploaded/video2mesh-semantic-scene-graph-grounded-sam/stage-semantics.svg \"Grounded-SAM 类路线把文本检测框和 SAM mask 结合，得到带开放词汇标签的对象区域\")\n\n## 链接\n\n- Grounding DINO GitHub: https://github.com/IDEA-Research/GroundingDINO\n- Grounded-Segment-Anything GitHub: https://github.com/IDEA-Research/Grounded-Segment-Anything\n- Grounding DINO paper: https://arxiv.org/abs/2303.05499\n- Segment Anything: https://segment-anything.com/\n\n## 摘要要点\n\nGroundingDINO 做开放词汇目标检测：给定文本类别或自然语言短语，输出图像中的候选框；SAM 再把框转成精细 mask。Grounded-SAM 的实用价值在于把“开放词汇类别”和“高质量分割边界”连接起来。\n\n对 Video2Mesh 来说，它能从 bedroom scan 中发现 bed、window、curtain、floor、nightstand、lamp 等对象，为每个 object id 生成多帧 masks。后续再通过投影/投票把这些 2D masks 绑定到 3D 点、Gaussian 或 mesh face。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| text prompt / class list | 设定需要发现的物体类别 |\n| GroundingDINO detection | 输出开放词汇 boxes 和 scores |\n| SAM mask prediction | 用 boxes 提示 SAM 生成 masks |\n| tracking / multi-view fusion | 合并跨帧 object id |\n| 3D semantic transfer | 回灌到 point cloud / mesh face sidecar |\n\n## 输入与输出\n\n输入：图像、文本 prompt 或类别列表。输出：带 label/score 的 2D masks、object candidate 列表和后续 3D 语义融合证据。\n\n## 在 Video2Mesh 中的位置\n\nP1 提升 object label 和 affordance。正式 semantic mesh 结果中已经出现 GroundingDINO object discovery、SAM/SAM2 tracking 和 3D object masks 的产物，它是下一步 object split 和交互属性的入口。\n\n## 接入判断\n\n- P0：不阻塞几何闭环，但可作为可选 semantic path。\n- P1：进入 object split、物体补全和交互属性路线。\n- 风险：类别 prompt 需要针对室内场景维护，过宽会误检，过窄会漏物体。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-semantic-scene-graph-mesh-face-sidecar",
      "title": "Mesh Face Sidecar",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "mesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/mesh-face-sidecar.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Mesh Face Sidecar\n\n![Mesh face sidecar](assets/uploaded/video2mesh-semantic-scene-graph-mesh-face-sidecar/stage-semantics.svg \"Mesh face sidecar 将 triangle index 映射到 object id、label、material 和交互属性\")\n\n## 链接\n\n- glTF extensions registry: https://github.com/KhronosGroup/glTF/tree/main/extensions\n- Unity Mesh API: https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Mesh.html\n- Video2Mesh formal output: `tmp_remote_results/bedroom4_formal_semantic_mesh_results_20260703`\n\n## 简介\n\nMesh face sidecar 把 triangle face index 映射到 object id、label、material、affordance 和置信度，不把语义烘死在顶点色或贴图里。这样 collider raycast 命中某个 face 后，可以直接查“这是床、窗帘还是地板”，再决定交互、物理和 UI。\n\n它是 Video2Mesh 从“能看见 mesh”走向“能和物体交互”的关键合同。sidecar 还方便在 mesh 减面、替换、补全时记录版本和 provenance。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| mesh source | COLMAP Delaunay / Poisson / GS2Mesh / object split |\n| semantic evidence | 3D object masks、semantic splats、2D masks |\n| face assignment | KDTree / projection / voting / smoothing |\n| sidecar export | face -> object_id/label/prob/material |\n| runtime query | raycast face index -> object semantic and interaction rule |\n\n## 输入与输出\n\n输入：mesh、semantic points/masks、投票结果、object metadata。输出：`mesh_mesh_semantics_local.json`、`face_labels.json` 或等价 sidecar。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 交互查询关键合同。正式 semantic mesh 结果已经可以产出 per-face semantic transfer 和 object split，总体上比早期 ray projection debug 更适合接交互 demo。\n\n## 输出结果摘录\n\n`bedroom4_formal_semantic_mesh_results_20260703` 中 COLMAP Delaunay local transfer 覆盖 141,993 / 167,082 faces，覆盖率 84.98%，并能拆出 16 个 object split，是当前最值得推进的 mesh semantic sidecar 路线。\n\n## 接入判断\n\n- P0：进入，至少支持 click/raycast 查 label。\n- P1：接 material、affordance、body_type 和 object split。\n- 风险：mesh 简化后 face index 会变化，必须记录 source mesh hash 或重建映射。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果摘录",
          "slug": "输出结果摘录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "semantic-scene-graph",
      "title": "语义与 Scene Graph 阶段",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "整理 2D/3D 语义分割、semantic splats、mesh face sidecar 和 scene graph 在交互场景中的作用。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "Semantics",
        "Scene Graph",
        "SAM",
        "调研目录"
      ],
      "body": "\n# 语义与 Scene Graph 阶段\n\n语义层要服务交互查询：点击到哪个 face、属于哪个 object、是什么材质、能不能移动、能不能抓取、和其他物体有什么关系。\n\n![语义与 Scene Graph](assets/uploaded/semantic-scene-graph/stage-semantics.svg \"从 2D masks 到 3D labels，再到 mesh face sidecar 和交互查询\")\n\n## 主要项目和方法\n\n| 项目 / 方法 | 简介 | 对 Video2Mesh 的作用 | 风险 |\n|---|---|---|---|\n| Segment Anything / SAM | 通用 2D mask 生成/提示分割 | 生成 object masks，支持视频帧中的对象区域 | 无语义类别，需要 detector/VLM 命名 |\n| GroundingDINO / Grounded-SAM | 文本提示驱动检测 + mask | 开放词汇发现床、桌、椅、窗帘等对象 | 边界和类别稳定性需多帧融合 |\n| 2D-to-3D mask fusion | 将每帧 mask 投影/投票到 3D 点或 Gaussian | 生成 3D object masks、semantic/probability splats | 遮挡和深度误差会造成串色 |\n| Semantic splats | 给 3DGS/point cloud 携带 object probability | 支持可视化、hover、语义筛选和 mesh 回灌 | 不等同于 mesh face 语义 |\n| Mesh face sidecar | 按 triangle index 保存 label/probability/material/affordance | 点击 collider 后直接查 object_id 和交互属性 | mesh 简化/替换时需要重建索引或映射 |\n| Scene graph / VLM relation QA | 物体关系、支撑关系、可交互属性推理 | 给 simulator asset bundle 补 affordance、support、material | VLM 输出必须可复核 |\n\n## 推荐数据合同\n\n```json\n{\n  \"mesh\": \"colliders/scene_collision.glb\",\n  \"face_semantics\": [\n    {\n      \"face\": 1024,\n      \"object_id\": \"bed_01\",\n      \"label\": \"bed\",\n      \"probability\": 0.91,\n      \"material\": \"cloth\",\n      \"affordance\": [\"support\", \"sit_or_lie\"]\n    }\n  ]\n}\n```\n\n## 当前项目状态\n\n本周已验证 P0 KDTree 语义回灌和 P1 ray projection debug 路线。P1 当前没有真实 2D masks，只能用 projected semantic point label masks 调试，因此串色明显，暂时不能作为生产级语义融合结果。下一步应接入真实 2D mask、深度可见性过滤和 face graph smoothing。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和方法",
          "slug": "主要项目和方法"
        },
        {
          "level": "2",
          "text": "推荐数据合同",
          "slug": "推荐数据合同"
        },
        {
          "level": "2",
          "text": "当前项目状态",
          "slug": "当前项目状态"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-semantic-scene-graph-sam",
      "title": "Segment Anything / SAM",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "SAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/sam.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Segment Anything / SAM\n\n![SAM semantic masks](assets/uploaded/video2mesh-semantic-scene-graph-sam/stage-semantics.svg \"SAM 给 Video2Mesh 提供 2D masks，是后续 2D-to-3D 语义融合的基础\")\n\n## 链接\n\n- Project page: https://segment-anything.com/\n- GitHub: https://github.com/facebookresearch/segment-anything\n- Paper: https://arxiv.org/abs/2304.02643\n- Venue: ICCV 2023\n\n## 摘要要点\n\nSegment Anything 提出 promptable segmentation：给定点、框、文本外部提示或自动采样点，它可以在图像中生成候选 masks。论文强调大规模数据和模型的可迁移性，使 SAM 成为很多开放词汇分割、视频跟踪和 2D-to-3D 语义管线的基础模块。\n\nSAM 本身不负责“知道这是床还是窗帘”，它只给 mask。类别命名需要 GroundingDINO、YOLO-World、VLM 或人工标签；跨帧一致性需要 tracker；投到 3D 后还需要可见性过滤和多视角投票。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| prompt generation | 自动点、检测框或人工点框生成 SAM prompt |\n| mask prediction | 输出单帧候选 masks |\n| tracking / association | 跨帧保持 object id |\n| 2D-to-3D fusion | 将 masks 投票到点云、Gaussian 或 mesh faces |\n| semantic sidecar | 生成 object id / label / probability |\n\n## 输入与输出\n\n输入：图像、点/框/自动提示、可选文本检测结果。输出：2D masks、mask confidence、后续 tracking/fusion 所需的 per-frame object regions。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 语义输入，但要配合跟踪、投影和可见性过滤。当前 Video2Mesh 已有 SAM v1 相关路径，适合继续服务 object masks、semantic splats 和 mesh face sidecar。\n\n## 输出/接入记录\n\n本周 P1 ray projection debug 因没有真实 2D masks，只能用 projected semantic point label masks 调试，所以串色明显。正式 semantic mesh run 的结果说明：一旦 3D object masks 和 mesh transfer 更完整，COLMAP Delaunay local transfer 可以达到 84.98% face semantic coverage。\n\n## 接入判断\n\n- P0：作为 2D mask 输入保留。\n- P1：接 Grounded-SAM、tracking 和 face sidecar。\n- 风险：mask 边界错误会沿投影传播到 mesh，必须有可视化审核。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出/接入记录",
          "slug": "输出-接入记录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-semantic-scene-graph-scene-graph-vlm",
      "title": "Scene Graph / VLM",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "VLM 和 scene graph 用来描述物体关系、空间布局和可交互属性。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/scene-graph-vlm.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "Scene Graph",
        "调研目录"
      ],
      "body": "\n# Scene Graph / VLM\n\n![Scene Graph / VLM](assets/uploaded/video2mesh-semantic-scene-graph-scene-graph-vlm/stage-semantics.svg \"Scene graph 和 VLM 将几何物体扩展成可查询的关系、支撑和交互属性\")\n\n## 链接\n\n- ConceptGraphs project: https://concept-graphs.github.io/\n- OpenScene project: https://pengsongyou.github.io/openscene\n- LLaVA project: https://llava-vl.github.io/\n- GPT-4o / VLM APIs can provide object description and QA when local model is not fixed.\n\n## 简介\n\nScene graph / VLM 的任务是把“物体在哪里”扩展成“物体之间是什么关系、能不能移动、是不是支撑面、材质大概是什么、交互应该如何处理”。这对 simulator asset bundle 很重要，因为物理参数和交互规则不能只从三角网格自动得到。\n\nVLM 可以从 object crop、多视角截图和语义 mesh 中估计类别、材质、可抓取性、支撑关系和简短描述；scene graph 则把这些信息结构化为 nodes/edges，供 viewer 和引擎适配使用。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| object candidates | 来自 semantic sidecar 或 object split |\n| visual evidence | 多视角 crops、mesh screenshot、splat screenshot |\n| VLM inference | 估计 label、material、movable、support、affordance |\n| relation graph | 建立 on/inside/near/support/occluding 等关系 |\n| asset sidecar | 写入 simulator_asset_bundle metadata |\n\n## 输入与输出\n\n输入：图像、语义 mesh、object crops、bbox、support planes。输出：object relation、affordance、材质和物理属性 hints、可读描述。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2，让场景从“能看见”变成“能查询”。它可以为 bed/nightstand/lamp/curtain 等 object split 生成初始 metadata，再由人工或规则 QA。\n\n## 接入判断\n\n- P0：不阻塞几何闭环。\n- P1：用于 simulator asset bundle 的 material/body_type/affordance 初稿。\n- 风险：VLM 输出必须带 provenance 和 confidence，不能直接当真值物理参数。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-semantic-scene-graph-semantic-splats",
      "title": "Semantic Splats",
      "category": "调研目录",
      "research_stage": "semantic-scene-graph",
      "research_stage_title": "语义与 Scene Graph",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "semantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/semantic-splats.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Semantic Splats\n\n![Semantic splats](assets/uploaded/video2mesh-semantic-scene-graph-semantic-splats/stage-semantics.svg \"Semantic splats 把 3DGS visual proxy 与 object/label probability 绑定，用于可视化和查询\")\n\n## 链接\n\n- LangSplat: https://langsplat.github.io/\n- Feature 3DGS / semantic Gaussian survey reference: https://github.com/MrNeRF/awesome-3D-gaussian-splatting\n- Segment Anything: https://segment-anything.com/\n\n## 简介\n\nSemantic splats 是给 Gaussian 或点云附加 object id、label 或 probability 的路线。它可以让 3DGS visual layer 支持 hover、筛选、按类别渲染、点击查询和调试语义传播质量。\n\n它和 mesh face sidecar 的职责不同：semantic splats 适合看和查视觉层，mesh face sidecar 适合 collider raycast 后查 face/object/material。最终交互系统往往两个都要有。\n\n## Pipeline\n\n| 阶段 | 作用 |\n|---|---|\n| 2D masks / labels | SAM、Grounded-SAM 或 VLM 提供每帧语义证据 |\n| projection / voting | 将 2D mask 证据投到 3D points/Gaussians |\n| probability aggregation | 为每个 Gaussian/point 保存 label probabilities |\n| viewer export | 导出 semantic PLY / colored splats |\n| mesh transfer | 可选把 semantic splats 再映射到 mesh faces |\n\n## 输入与输出\n\n输入：3DGS/点云、相机、2D masks 和 labels。输出：semantic/probability PLY、colored splats、object mask clouds、后续 face transfer 证据。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 语义可视化，不替代 mesh face sidecar。本周 formal semantic mesh 结果中也包含 semantic dense/3DGS manifest，可以作为 mesh semantic transfer 的输入之一。\n\n## 输出/接入记录\n\n正式结果里，COLMAP Delaunay projected splats 路线达到了 80.13% face semantic coverage，低于 local transfer 的 84.98%，但仍说明 semantic splats 可以作为 mesh 语义回灌证据。\n\n## 接入判断\n\n- P0：作为语义可视化和 transfer evidence。\n- P1：与 face sidecar、object split 联动。\n- 风险：投影误差和遮挡会造成串色，需要深度可见性过滤和 face graph smoothing。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出/接入记录",
          "slug": "输出-接入记录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-visual-3dgs-graphdeco-3dgs",
      "title": "GraphDECO 3D Gaussian Splatting",
      "category": "调研目录",
      "research_stage": "visual-3dgs",
      "research_stage_title": "视觉重建 / 3DGS",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "GraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/graphdeco-3dgs.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GraphDECO 3D Gaussian Splatting\n\n![3DGS visual layer](../assets/stage-visual-3dgs.svg \"GraphDECO 3DGS 在 Video2Mesh 中承担 visual proxy，不直接承担 collider\")\n\n## 链接\n\n- Project page: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/\n- GitHub: https://github.com/graphdeco-inria/gaussian-splatting\n- Paper: https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/3d_gaussian_splatting_high.pdf\n- Venue: SIGGRAPH 2023\n\n## 摘要要点\n\n3D Gaussian Splatting 的核心是用 COLMAP sparse points 初始化一组 3D Gaussians，通过颜色、opacity、位置、尺度、旋转和各向异性协方差优化来拟合多视角图像。论文同时提出 density control 和 visibility-aware splatting renderer，使训练和实时渲染都比传统 NeRF 路线更适合交互展示。\n\n对 Video2Mesh 来说，3DGS 是最强 visual proxy：它让扫描房间看起来真实，也能渲染 novel view、截图和语义可视化。但 Gaussian 并不等价于真实 surface，直接拿 Gaussian center 做 Poisson 或 collider 会产生壳状伪影、飞面和语义串色。\n\n## Pipeline\n\n| 阶段 | 作用 | 输出 |\n|---|---|---|\n| COLMAP initialization | 用 sparse points 和 camera 初始化 Gaussian | 初始 3D Gaussians |\n| differentiable splatting | 将 Gaussians 渲染回训练视角 | RGB reconstruction loss |\n| densification / pruning | 补充细节并移除低贡献 Gaussian | 更密的 visual proxy |\n| export / viewer | 导出 PLY、Splat、SPZ/SOG 等 | Web/桌面 visual layer |\n\n## 输入与输出\n\n输入：COLMAP 相机、图像、稀疏点云。输出：Gaussian PLY / point_cloud.ply、viewer 可消费的 splat 资产、可选 semantic/probability splats。\n\n## 在 Video2Mesh 中的位置\n\nP0 visual layer。当前 bedroom_4 formal run 中，GraphDECO 30k 提供主要视觉资产，并作为语义投影、GS2Mesh、semantic splats 和 Web proxy demo 的输入。它不直接承担 mesh collider，但可以给 mesh 重建提供 novel-view RGB/depth/mask evidence。\n\n## 输出结果摘录\n\n本周实验说明：3DGS 视觉层对展示非常有价值，但由 Gaussian center 直接做 Poisson 的路线效果不稳定。`open3d_poisson_3dgs_alpha005_sample500k` 体量可控，却有壳状伪影和粘连；正式 semantic mesh 中 Open3D Poisson 语义覆盖率只有 32.21%，明显弱于 COLMAP Delaunay local transfer。\n\n## 接入判断\n\n- P0：继续作为 visual proxy 主线。\n- P1：接 semantic splats、face sidecar、object crop/ref image 生成。\n- 风险：严禁把 Gaussian center 直接解释成物理表面；碰撞层必须另走 mesh/collider proxy。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出结果摘录",
          "slug": "输出结果摘录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "visual-3dgs",
      "title": "视觉重建与 3DGS 阶段",
      "category": "调研目录",
      "research_stage": "visual-3dgs",
      "research_stage_title": "视觉重建 / 3DGS",
      "research_doc_role": "overview",
      "visibility": "public",
      "summary": "梳理 GraphDECO 3DGS、Spark、SuperSplat 等视觉代理方案，以及它们和 mesh/collider 的边界。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/overview.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Research Catalog",
        "3DGS",
        "Spark",
        "SuperSplat",
        "调研目录"
      ],
      "body": "\n# 视觉重建与 3DGS 阶段\n\n3DGS 在 Video2Mesh 中应该被定位为 **visual proxy**：它负责让扫描场景看起来真实，但不直接承担碰撞、导航、刚体交互和语义查询。\n\n## 主要项目和模型\n\n| 项目 / 方法 | 简介 | 适合承担 | 不适合承担 |\n|---|---|---|---|\n| GraphDECO 3D Gaussian Splatting | 经典 3DGS 训练实现，用 COLMAP 相机和点云初始化高斯场景 | 当前 P0/P1 真实场景视觉层，生成高质量 splat/PLY | 直接输出可靠 mesh topology 或 collider |\n| Spark / SparkJS | 浏览器端 3DGS/Splat 渲染 runtime，World Labs / Icare 生态中常见 | Web visual layer，加载 `.ply/.splat/.spz/.sog` 等视觉资产 | 物理碰撞和复杂交互本身 |\n| SuperSplat | 3DGS 浏览器查看、编辑和导出工具 | 本地/远端检查 splat 质量、清理 floaters、截图展示 | simulator asset bundle 生成 |\n| 2DGS / GOF / surface-aware GS | 让 Gaussian 更贴近表面、改善 mesh extraction 的研究路线 | P2 替换或增强训练端，提高后续 mesh 质量 | 短期 P0 工程主链路 |\n\n## 核心边界\n\n```text\nGraphDECO 3DGS\n  -> visual display\n  -> rendered RGB / depth / mask evidence\n  -> object visual mesh reconstruction helper\n\nnot:\n  -> collider\n  -> navigation mesh\n  -> final simulator physics body\n```\n\n## 对 Video2Mesh 的结论\n\n3DGS 应该继续作为视觉质量最强的场景层，同时为后续 mesh 重建提供 rendered RGB/depth/mask evidence。不要直接把 Gaussian center 当作真实表面点云去建最终 mesh，因为当前实验证明这会导致壳状伪影、漂浮片和语义串色。\n",
      "headings": [
        {
          "level": "2",
          "text": "主要项目和模型",
          "slug": "主要项目和模型"
        },
        {
          "level": "2",
          "text": "核心边界",
          "slug": "核心边界"
        },
        {
          "level": "2",
          "text": "对 Video2Mesh 的结论",
          "slug": "对-video2mesh-的结论"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-visual-3dgs-spark-supersplat",
      "title": "Spark / SuperSplat",
      "category": "调研目录",
      "research_stage": "visual-3dgs",
      "research_stage_title": "视觉重建 / 3DGS",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "Spark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/spark-supersplat.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Spark / SuperSplat\n\n![Spark / SuperSplat](../assets/stage-visual-3dgs.svg \"Spark 和 SuperSplat 代表工业界对 3DGS visual proxy 的浏览器查看、编辑和发布约定\")\n\n## 链接\n\n- Spark docs: https://sparkjs.dev/\n- Spark 2.0 / World Labs blog: https://www.worldlabs.ai/blog/spark-2.0\n- SuperSplat product: https://playcanvas.com/products/supersplat\n- SuperSplat GitHub: https://github.com/playcanvas/supersplat\n\n## 简介\n\nSpark 是浏览器端 3DGS renderer，面向 Three.js 集成，支持把 splats 与普通 meshes 一起放在 Web 场景里。SuperSplat 是 PlayCanvas 生态的浏览器编辑/优化/发布工具，适合检查、裁剪、优化和发布 3D Gaussian Splats。\n\n它们给 Video2Mesh 的启发不是“浏览器能自动做物理”，而是明确了工业界分层：splat 负责视觉，mesh/collider/primitive 才负责交互和物理。Web viewer 可以同时加载 visual proxy 与隐藏 collider proxy。\n\n## Pipeline\n\n| 工具 | Pipeline | 输出 |\n|---|---|---|\n| Spark | PLY/SPZ/SOG/SPLAT -> Three.js renderer -> Web visual layer | 可和 mesh/controls/physics scene 同屏 |\n| SuperSplat | splat import -> cleanup/edit/optimize -> export/publish | PLY、compressed PLY、SOG、截图和发布链接 |\n\n## 输入与输出\n\n输入：PLY/SPZ/SOG/SPLAT 等 splat 资产。输出：浏览器可视化、编辑结果、优化后的 splat、截图、发布资产。\n\n## 在 Video2Mesh 中的位置\n\nWeb 展示和 QA 工具，不负责 simulator bundle。当前项目可以借鉴 Spark/SuperSplat 的 viewer 约定：3DGS visual layer 独立加载，碰撞/点击/导航走 hidden GLB collider 或 primitive bodies。\n\n## 输出/接入记录\n\n本周完成的 visual/physics proxy demo 已验证类似分层：浏览器显示视觉层，同时用 mesh collision layer 做 raycast、地面探测和阻挡。这条路线比直接给 splat 加碰撞更稳。\n\n## 接入判断\n\n- P0：作为 Web visual layer/QA 参考。\n- P1：用于交互 viewer，和 collider proxy、semantic sidecar 同屏。\n- 风险：viewer 资产格式不能替代 simulator asset bundle；物理属性和引擎适配仍由 Video2Mesh 导出。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出/接入记录",
          "slug": "输出-接入记录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    },
    {
      "id": "video2mesh-visual-3dgs-surface-aware-gs",
      "title": "Surface-aware Gaussian 路线",
      "category": "调研目录",
      "research_stage": "visual-3dgs",
      "research_stage_title": "视觉重建 / 3DGS",
      "research_doc_role": "item",
      "visibility": "public",
      "summary": "SuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/surface-aware-gs.md",
      "source_kind": "builtin",
      "updated": "2026-07-04",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Surface-aware Gaussian 路线\n\n![Surface-aware GS](../assets/stage-visual-3dgs.svg \"Surface-aware Gaussian 路线把视觉高斯约束到更明确的表面，为后续 mesh extraction 降低噪声\")\n\n## 链接\n\n- SuGaR: https://anttwo.github.io/sugar/\n- 2DGS: https://github.com/hbb1/2d-gaussian-splatting\n- GOF: https://niujinshuchong.github.io/gaussian-opacity-fields/\n- GS2Mesh: https://gs2mesh.github.io/\n\n## 摘要要点\n\nSurface-aware Gaussian 是一个路线族，而不是单个模型。它们共同解决的问题是：传统 3DGS 对视觉渲染很强，但没有天然 surface topology。SuGaR 通过 surface alignment 和 Poisson extraction 得到 mesh + Gaussian hybrid；2DGS 把 Gaussian 改为更像 surfel 的二维 oriented disks；GOF 从 opacity field 和 tetrahedral extraction 方向得到更紧凑 surface；GS2Mesh 则用 3DGS novel-view 渲染 + stereo depth + fusion 避免直接连 Gaussian center。\n\n这些方法比“3DGS center -> Poisson”更合理，但通常需要新训练、新环境或额外深度/TSDF 流程。\n\n## Pipeline\n\n| 路线 | Pipeline | 输出 |\n|---|---|---|\n| SuGaR | 3DGS warm-up -> surface alignment -> Poisson mesh -> hybrid refinement | editable mesh + surface-bound Gaussians |\n| 2DGS | images -> 2D Gaussian disks -> normal/depth regularization -> meshing | surfel-like visual representation and mesh |\n| GOF | Gaussian opacity field -> geometry-aware optimization -> marching tetrahedra | adaptive surface mesh |\n| GS2Mesh | 3DGS render stereo views -> depth estimation -> TSDF/depth fusion | visual mesh |\n\n## 输入与输出\n\n输入：训练图像、COLMAP 相机、已有 3DGS 或方法专用训练结果。输出：更贴近表面的 Gaussian 表示、visual mesh、可编辑 hybrid asset。\n\n## 在 Video2Mesh 中的位置\n\nP2 研究升级线，短期不替代 GraphDECO P0。当前结论是：COLMAP Delaunay 更适合 P0 static collider；GS2Mesh/SuGaR/2DGS/GOF 更适合作为 high-quality visual mesh benchmark 或后续 per-object mesh 升级方向。\n\n## 输出/接入记录\n\n本周已尝试 GS2Mesh 和 SuGaR/GS2Mesh 类 mesh 重建对照。GS2Mesh 原始 mesh 体量较大，减面后可展示，但墙面破碎和漂浮片仍需要清理；因此它更适合做 visual mesh 对照，不适合直接替代 collider 主链路。\n\n## 接入判断\n\n- P0：不进入主 collider 链路。\n- P1：可作为 visual mesh benchmark。\n- P2/P3：探索 per-object mesh、editable asset 和 surface-aware training。\n",
      "headings": [
        {
          "level": "2",
          "text": "链接",
          "slug": "链接"
        },
        {
          "level": "2",
          "text": "摘要要点",
          "slug": "摘要要点"
        },
        {
          "level": "2",
          "text": "Pipeline",
          "slug": "pipeline"
        },
        {
          "level": "2",
          "text": "输入与输出",
          "slug": "输入与输出"
        },
        {
          "level": "2",
          "text": "在 Video2Mesh 中的位置",
          "slug": "在-video2mesh-中的位置"
        },
        {
          "level": "2",
          "text": "输出/接入记录",
          "slug": "输出-接入记录"
        },
        {
          "level": "2",
          "text": "接入判断",
          "slug": "接入判断"
        }
      ],
      "reading_minutes": 1
    }
  ],
  "categories": [
    "调研目录",
    "进度目录",
    "项目文档"
  ]
};
