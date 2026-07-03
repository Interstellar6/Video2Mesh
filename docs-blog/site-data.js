window.V2M_BLOG_DATA = {
  "generatedAt": "2026-07-03 20:34",
  "docs": [
    {
      "id": "research-catalog",
      "title": "场景扫描与可交互资产调研目录",
      "category": "调研目录",
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
      "visibility": "public",
      "summary": "V-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/convex-decomposition.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Convex Decomposition\n\n## 简介\n\nV-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。\n\n## 输入与输出\n\n输入：object mesh。输出：convex hull compound。\n\n## 在 Video2Mesh 中的位置\n\nP1 动态物体 collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "MuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的 body、joint、mass、friction、scale 合同。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/mujoco-isaac.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# MuJoCo / Isaac\n\n## 简介\n\nMuJoCo 和 Isaac 更偏机器人/仿真，需要更严格的 body、joint、mass、friction、scale 合同。\n\n## 输入与输出\n\n输入：simulator asset bundle 和 mesh/collider。输出：XML/USD/adapter。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2 仿真适配，需 QA 物理参数。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/primitive-fitting.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Primitive Fitting\n\n## 简介\n\n对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。\n\n## 输入与输出\n\n输入：语义点云、bbox、mesh。输出：primitive collider。\n\n## 在 Video2Mesh 中的位置\n\nP1 object collider，适合刚体交互。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Rapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/rapier-unity.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "Unity",
        "调研目录"
      ],
      "body": "\n# Rapier / Unity Physics\n\n## 简介\n\nRapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。\n\n## 输入与输出\n\n输入：collider、body type、material。输出：runtime collision。\n\n## 在 Video2Mesh 中的位置\n\nP1 runtime 集成验证。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。",
      "source_path": "docs/video2mesh/research-catalog/collider-physics-proxy/static-mesh-collider.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Collider 与物理代理",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Static Mesh Collider\n\n## 简介\n\n场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。\n\n## 输入与输出\n\n输入：COLMAP Delaunay/Poisson mesh。输出：GLB collider。\n\n## 在 Video2Mesh 中的位置\n\nP0 必需，优先稳定和轻量。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "COLMAP dense + Delaunay mesher 生成场景级 mesh。",
      "source_path": "docs/video2mesh/research-catalog/experiments/colmap-delaunay-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP Delaunay Dense 实验\n\n## 简介\n\nCOLMAP dense + Delaunay mesher 生成场景级 mesh。\n\n## 输入与输出\n\n输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB。\n\n## 在 Video2Mesh 中的位置\n\n当前最适合 P0 static collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。",
      "source_path": "docs/video2mesh/research-catalog/experiments/formal-semantic-mesh-20260703.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 正式 Semantic Mesh 结果 20260703\n\n## 简介\n\n新训练输出位于 bedroom4_formal_semantic_mesh_results_20260703，相比早期 debug 投影更适合汇报展示。\n\n## 输入与输出\n\n主要区域如床、窗帘/绿色大面、蓝色物体、地毯和小物件颜色区分更清楚。\n\n## 在 Video2Mesh 中的位置\n\n下一步统计 face/object 覆盖率，并接入 object/collider sidecar。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-experiments-gs2mesh-experiment",
      "title": "GS2Mesh 实验",
      "category": "调研目录",
      "visibility": "public",
      "summary": "本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。",
      "source_path": "docs/video2mesh/research-catalog/experiments/gs2mesh-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GS2Mesh 实验\n\n## 简介\n\n本项目使用 GS2Mesh 路线测试从 3DGS 到 visual mesh 的可行性。\n\n## 输入与输出\n\nraw mesh 约 4.48M vertices / 8.09M triangles，原始文件约 333MB。\n\n## 在 Video2Mesh 中的位置\n\n效果能保留床、窗帘和大结构，但仍有墙面破碎、漂浮片和局部缺失。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "使用过滤后的 3DGS center point cloud 做 Poisson baseline。",
      "source_path": "docs/video2mesh/research-catalog/experiments/open3d-poisson-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D Poisson 实验\n\n## 简介\n\n使用过滤后的 3DGS center point cloud 做 Poisson baseline。\n\n## 输入与输出\n\nalpha005_sample500k 输入 50 万点，输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。\n\n## 在 Video2Mesh 中的位置\n\n适合 fallback/debug，不适合最终 surface。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。",
      "source_path": "docs/video2mesh/research-catalog/experiments/semantic-transfer-experiment.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 语义投影融合实验\n\n## 简介\n\n早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。\n\n## 输入与输出\n\ndebug 图显示覆盖更高，但床、墙、窗帘、地面之间存在明显串色。\n\n## 在 Video2Mesh 中的位置\n\n保留路线，但需要真实 2D mask、深度可见性过滤和 smoothing。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-experiments-visual-physics-proxy-demo",
      "title": "Visual / Physics Proxy Demo",
      "category": "调研目录",
      "visibility": "public",
      "summary": "本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。",
      "source_path": "docs/video2mesh/research-catalog/experiments/visual-physics-proxy-demo.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "本项目实验",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Visual / Physics Proxy Demo\n\n## 简介\n\n本地 demo 验证 3DGS visual layer 与 GLB collider layer 可以完全分离。\n\n## 输入与输出\n\n入口曾为 http://127.0.0.1:4173/demos/visual-physics-proxy/。\n\n## 在 Video2Mesh 中的位置\n\n证明交互逻辑不需要依赖 3DGS 自身产生 collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-industrial-pipelines-icare",
      "title": "Icare / 学长文档路线",
      "category": "调研目录",
      "visibility": "public",
      "summary": "学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/icare.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Icare / 学长文档路线\n\n## 简介\n\n学长/工业演示通常把 Splat 作为视觉代理，把 mesh/collider 作为交互代理，把语义和物理保存在外部元数据。\n\n## 输入与输出\n\n输入：扫描/生成资产。输出：viewer 可消费的 visual + collider + metadata。\n\n## 在 Video2Mesh 中的位置\n\n作为 Video2Mesh 架构参考，不能替代本项目导出合同。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/image-blaster.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# image-blaster\n\n## 简介\n\nimage-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。\n\n## 输入与输出\n\n输入：object crop、prompt、world config。输出：object mesh、object.json、viewer 目录。\n\n## 在 Video2Mesh 中的位置\n\nP1 物体补全后端和目录约定参考。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Spark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/spark-viewer.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Spark Viewer\n\n## 简介\n\nSpark viewer 代表浏览器端高质量 splat 渲染路线，适合把 3DGS 当 visual proxy。\n\n## 输入与输出\n\n输入：splat/ply/spz/sog。输出：Web 视觉层。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 展示层，不承担 physics。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "World Labs Marble 更偏 static world/background 生成，可提供 splat、collider、pano 等世界资产。",
      "source_path": "docs/video2mesh/research-catalog/industrial-pipelines/world-labs-marble.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "工业资产管线",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# World Labs / Marble\n\n## 简介\n\nWorld Labs Marble 更偏 static world/background 生成，可提供 splat、collider、pano 等世界资产。\n\n## 输入与输出\n\n输入：场景描述、clean plate 或生成请求。输出：static world assets。\n\n## 在 Video2Mesh 中的位置\n\n可借鉴 visual/collider 分层和 clean plate 思路，不负责 Video2Mesh simulator bundle。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "COLMAP 是当前 Video2Mesh 的 P0 位姿、稠密重建和 Delaunay mesh 基线。它提供相机参数、稀疏点、dense workspace 和可作为 collider 的传统几何。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/colmap.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP\n\n## 简介\n\nCOLMAP 是当前 Video2Mesh 的 P0 位姿、稠密重建和 Delaunay mesh 基线。它提供相机参数、稀疏点、dense workspace 和可作为 collider 的传统几何。\n\n## 输入与输出\n\n输入：多视角图像或视频抽帧。输出：相机、稠密点云、Delaunay/Poisson mesh。\n\n## 在 Video2Mesh 中的位置\n\nP0 主链路。它比 learned pose 方法更可控，也能直接接 mesh 和尺度检查。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-input-pose-pointcloud-mast3r-dust3r-vggt",
      "title": "MASt3R / DUSt3R / VGGT",
      "category": "调研目录",
      "visibility": "public",
      "summary": "这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/mast3r-dust3r-vggt.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "VGGT",
        "调研目录"
      ],
      "body": "\n# MASt3R / DUSt3R / VGGT\n\n## 简介\n\n这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。\n\n## 输入与输出\n\n输入：图像对或图像序列。输出：相对几何、点图、相机或轨迹估计。\n\n## 在 Video2Mesh 中的位置\n\nP1 fallback。需要和 Video2Mesh 的 camera_info.json、尺度、坐标约定对齐。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-input-pose-pointcloud-open3d-cloudcompare",
      "title": "Open3D / CloudCompare",
      "category": "调研目录",
      "visibility": "public",
      "summary": "Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。",
      "source_path": "docs/video2mesh/research-catalog/input-pose-pointcloud/open3d-cloudcompare.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "输入、位姿与点云",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D / CloudCompare\n\n## 简介\n\nOpen3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。\n\n## 输入与输出\n\n输入：PLY/PCD/OBJ 等点云或 mesh。输出：清理点云、重建 mesh、诊断截图。\n\n## 在 Video2Mesh 中的位置\n\ndebug 和 baseline 工具，不作为唯一生产算法。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/2dgs-gof.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 2DGS / GOF\n\n## 简介\n\n2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。\n\n## 输入与输出\n\n输入：训练图像或 Gaussian。输出：更适合 surface reconstruction 的表示和 mesh。\n\n## 在 Video2Mesh 中的位置\n\nP2/P3 研究升级，不直接进入 P0 collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/cloudcompare-poisson.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# CloudCompare / PoissonRecon\n\n## 简介\n\nCloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。\n\n## 输入与输出\n\n输入：点云。输出：可视化检查结果和 Poisson mesh。\n\n## 在 Video2Mesh 中的位置\n\n人工诊断和方法对照，不建议直接作为无人值守主链路。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/colmap-delaunay.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "COLMAP",
        "调研目录"
      ],
      "body": "\n# COLMAP Delaunay Mesher\n\n## 简介\n\nCOLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。\n\n## 输入与输出\n\n输入：COLMAP dense workspace。输出：scene-level mesh。\n\n## 在 Video2Mesh 中的位置\n\nP0 scene collider 主路线，适合轻量静态碰撞代理。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "GS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/gs2mesh.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GS2Mesh\n\n## 简介\n\nGS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。\n\n## 输入与输出\n\n输入：训练后 3DGS 和渲染视角。输出：visual mesh。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2 object visual mesh benchmark；raw mesh 较大，需要减面和清理。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Neural SDF 路线能做高质量隐式表面重建，但训练和集成成本高。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/neus-volsdf.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# NeuS / VolSDF\n\n## 简介\n\nNeural SDF 路线能做高质量隐式表面重建，但训练和集成成本高。\n\n## 输入与输出\n\n输入：多视角图像和相机。输出：SDF / mesh。\n\n## 在 Video2Mesh 中的位置\n\n离线高质量资产候选，不适合当前主链路快速闭环。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-mesh-reconstruction-open3d-poisson",
      "title": "Open3D Poisson",
      "category": "调研目录",
      "visibility": "public",
      "summary": "Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/open3d-poisson.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Open3D Poisson\n\n## 简介\n\nOpen3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。\n\n## 输入与输出\n\n输入：带法线点云。输出：Poisson mesh。\n\n## 在 Video2Mesh 中的位置\n\nbaseline/fallback。3DGS center point cloud 上容易生成壳状伪影。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "SuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。",
      "source_path": "docs/video2mesh/research-catalog/mesh-reconstruction/sugar.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "Mesh 重建",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# SuGaR\n\n## 简介\n\nSuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。\n\n## 输入与输出\n\n输入：3DGS 或训练数据。输出：surface-aligned Gaussians 和 mesh。\n\n## 在 Video2Mesh 中的位置\n\nP2 高质量 visual mesh 路线，环境和优化成本高。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Hunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/hunyuan3d.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Hunyuan3D\n\n## 简介\n\nHunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。\n\n## 输入与输出\n\n输入：物体 crop / reference image。输出：object-local mesh / GLB。\n\n## 在 Video2Mesh 中的位置\n\nP1 object visual completion，需要回填尺度和姿态。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/image-blaster-object-jobs.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# image-blaster Object Jobs\n\n## 简介\n\nimage-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。\n\n## 输入与输出\n\n输入：object crop / prompt / world object config。输出：object.json、GLB/OBJ、viewer 资产。\n\n## 在 Video2Mesh 中的位置\n\n可借用目录约定和 object job 思路，但 simulator bundle 仍由 Video2Mesh 导出。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "InstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/instantmesh.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# InstantMesh\n\n## 简介\n\nInstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。\n\n## 输入与输出\n\n输入：单图/多视角图像。输出：mesh。\n\n## 在 Video2Mesh 中的位置\n\nP1 批量候选，可能需要更多纹理和尺度修正。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Meshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/meshy.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Meshy\n\n## 简介\n\nMeshy 是商业 image/text-to-3D 服务，适合快速生成可展示物体 mesh。\n\n## 输入与输出\n\n输入：图片或文本 prompt。输出：mesh / texture。\n\n## 在 Video2Mesh 中的位置\n\nP1 快速补全候选，需记录 provenance 和人工 QA。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "TRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。",
      "source_path": "docs/video2mesh/research-catalog/object-mesh-completion/trellis.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体 Mesh 补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# TRELLIS\n\n## 简介\n\nTRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。\n\n## 输入与输出\n\n输入：单图或多模态条件。输出：3D asset。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2 物体补全候选，重点测试遮挡物体。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/physsplat-sim-anything.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# PhysSplat / Sim Anything\n\n## 简介\n\n这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。\n\n## 输入与输出\n\n输入：3DGS、语义、物理属性或交互条件。输出：带动态/物理含义的 Gaussian 表示。\n\n## 在 Video2Mesh 中的位置\n\nP2/P3 跟踪方向；模型未完全开源时不能作为主链路依赖。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/rigid-body.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Rigid Body Interaction\n\n## 简介\n\n刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。\n\n## 输入与输出\n\n输入：object mesh/collider/physics metadata。输出：可移动或可碰撞物体。\n\n## 在 Video2Mesh 中的位置\n\nP1 首选。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/soft-body-cloth.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Soft Body / Cloth\n\n## 简介\n\n窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。\n\n## 输入与输出\n\n输入：cloth mesh、constraints、material。输出：软体/布料仿真。\n\n## 在 Video2Mesh 中的位置\n\nP2，先用静态代理或简化面片。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "VLM 可估计物体类别、材质、可抓取性、是否可移动等属性，但数值物理参数仍需校准。",
      "source_path": "docs/video2mesh/research-catalog/object-simulation/vlm-physical-properties.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "物体仿真",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# VLM Physical Properties\n\n## 简介\n\nVLM 可估计物体类别、材质、可抓取性、是否可移动等属性，但数值物理参数仍需校准。\n\n## 输入与输出\n\n输入：图像、object crop、语义标签。输出：material/body hints。\n\n## 在 Video2Mesh 中的位置\n\nP1 辅助填写 simulator asset bundle。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "clean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/background-clean-plate.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Background Clean Plate\n\n## 简介\n\nclean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。\n\n## 输入与输出\n\n输入：场景描述、移除物体 masks、背景参考。输出：修复背景或 static world。\n\n## 在 Video2Mesh 中的位置\n\nP1 背景补全，和 object mesh completion 分开。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/floater-cleaning.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Floater Cleaning\n\n## 简介\n\n先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。\n\n## 输入与输出\n\n输入：point cloud 或 Gaussian PLY。输出：cleaned point cloud / cleaned Gaussian。\n\n## 在 Video2Mesh 中的位置\n\nP0 预处理，应放在 semantic transfer 和 mesh 重建前。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/inpainting.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# 2D/3D Inpainting\n\n## 简介\n\n2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。\n\n## 输入与输出\n\n输入：masks、images、depth/point cloud。输出：修复图像、修复点云或补面。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2，不应直接伪造物理可信 collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。",
      "source_path": "docs/video2mesh/research-catalog/pointcloud-completion/scene-layout.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "点云清理与背景补全",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Scene Layout Completion\n\n## 简介\n\n场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。\n\n## 输入与输出\n\n输入：点云、语义、VLM/scene graph。输出：layout primitives 或结构 mesh。\n\n## 在 Video2Mesh 中的位置\n\nP1 物理代理补全，比视觉补纹理更重要。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "Grounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/grounded-sam.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Grounded-SAM / Open-vocabulary Detection\n\n## 简介\n\nGrounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。\n\n## 输入与输出\n\n输入：图像和文本类别。输出：带标签的 masks。\n\n## 在 Video2Mesh 中的位置\n\nP1 提升 object label 和 affordance。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "mesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/mesh-face-sidecar.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Mesh Face Sidecar\n\n## 简介\n\nmesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。\n\n## 输入与输出\n\n输入：mesh、semantic points/masks、投票结果。输出：face_labels.json 或等价 sidecar。\n\n## 在 Video2Mesh 中的位置\n\nP0 交互查询关键合同。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "semantic-scene-graph",
      "title": "语义与 Scene Graph 阶段",
      "category": "调研目录",
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
      "visibility": "public",
      "summary": "SAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/sam.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Segment Anything / SAM\n\n## 简介\n\nSAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。\n\n## 输入与输出\n\n输入：图像和点/框/自动提示。输出：2D masks。\n\n## 在 Video2Mesh 中的位置\n\nP0 语义输入，但要配合跟踪、投影和可见性过滤。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-semantic-scene-graph-scene-graph-vlm",
      "title": "Scene Graph / VLM",
      "category": "调研目录",
      "visibility": "public",
      "summary": "VLM 和 scene graph 用来描述物体关系、空间布局和可交互属性。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/scene-graph-vlm.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "Scene Graph",
        "调研目录"
      ],
      "body": "\n# Scene Graph / VLM\n\n## 简介\n\nVLM 和 scene graph 用来描述物体关系、空间布局和可交互属性。\n\n## 输入与输出\n\n输入：图像、语义 mesh、object crops。输出：object relation、affordance、描述。\n\n## 在 Video2Mesh 中的位置\n\nP1/P2，让场景从“能看见”变成“能查询”。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "visibility": "public",
      "summary": "semantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。",
      "source_path": "docs/video2mesh/research-catalog/semantic-scene-graph/semantic-splats.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "语义与 Scene Graph",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Semantic Splats\n\n## 简介\n\nsemantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。\n\n## 输入与输出\n\n输入：3DGS/点云 + 2D masks。输出：semantic/probability PLY。\n\n## 在 Video2Mesh 中的位置\n\nP0/P1 语义可视化，不替代 mesh face sidecar。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-visual-3dgs-graphdeco-3dgs",
      "title": "GraphDECO 3D Gaussian Splatting",
      "category": "调研目录",
      "visibility": "public",
      "summary": "GraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/graphdeco-3dgs.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# GraphDECO 3D Gaussian Splatting\n\n## 简介\n\nGraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。\n\n## 输入与输出\n\n输入：COLMAP 相机和图像。输出：Gaussian PLY / point_cloud.ply 等 visual proxy。\n\n## 在 Video2Mesh 中的位置\n\nP0 visual layer。不要直接拿 Gaussian center 当 collider。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "visual-3dgs",
      "title": "视觉重建与 3DGS 阶段",
      "category": "调研目录",
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
      "visibility": "public",
      "summary": "Spark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/spark-supersplat.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Spark / SuperSplat\n\n## 简介\n\nSpark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。\n\n## 输入与输出\n\n输入：PLY/SPZ/SOG/SPLAT 等 splat 资产。输出：Web 可视化、检查、截图。\n\n## 在 Video2Mesh 中的位置\n\nWeb 展示和 QA 工具，不负责 simulator bundle。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
      "id": "video2mesh-visual-3dgs-surface-aware-gs",
      "title": "Surface-aware Gaussian 路线",
      "category": "调研目录",
      "visibility": "public",
      "summary": "SuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。",
      "source_path": "docs/video2mesh/research-catalog/visual-3dgs/surface-aware-gs.md",
      "source_kind": "builtin",
      "updated": "2026-07-03",
      "tags": [
        "视觉重建与 3DGS",
        "Research Catalog",
        "调研目录"
      ],
      "body": "\n# Surface-aware Gaussian 路线\n\n## 简介\n\nSuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。\n\n## 输入与输出\n\n输入：训练图像或已有 3DGS。输出：更贴近表面的 Gaussian / mesh。\n\n## 在 Video2Mesh 中的位置\n\nP2 研究升级线，短期不替代 GraphDECO P0。\n\n## 接入判断\n\n- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。\n- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。\n- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。\n",
      "headings": [
        {
          "level": "2",
          "text": "简介",
          "slug": "简介"
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
    }
  ],
  "categories": [
    "调研目录",
    "进度目录",
    "项目文档"
  ]
};
