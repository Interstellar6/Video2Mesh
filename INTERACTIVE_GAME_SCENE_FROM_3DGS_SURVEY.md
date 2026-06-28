# 从 3DGS / 扫描点云到可交互游戏场景：业界工作流调研

调研日期：2026-06-28  
面向项目：Video2Mesh  
问题：游戏制作、虚拟制作和场景建模行业，如何把扫描得到的 3DGS / 点云变成可以交互的游戏场景。

## 0. 结论先行

业界通常不会把 3DGS 本体直接当作“游戏世界”。更常见、更可靠的做法是把扫描资产拆成多层：

```text
3DGS / scan / photogrammetry
  -> visual layer: 高保真外观，用 splat / Nanite mesh / textured mesh 展示
  -> collision layer: 低模碰撞代理，box / convex hull / simplified mesh
  -> navigation layer: navmesh / walkable surface / off-mesh links
  -> interaction layer: 可拾取、可推、可打开、可破坏的独立 actor/prefab
  -> semantic layer: object ids, labels, affordances, scene graph, gameplay metadata
  -> engine package: Unity / Unreal / Godot prefab、level、material、physics、scripts
```

一句话：  
**3DGS 负责“看起来像真实世界”，但游戏交互依赖 mesh、collider、navmesh、语义对象和引擎组件。**

对 Video2Mesh 的建议：

1. 保留 scene-level 3DGS 作为背景视觉层。
2. 把从 3DGS / 点云 / mask 得到的 object mesh 只当 visual mesh，不直接当 physics mesh。
3. 每个对象额外生成 collision proxy：box、convex hull、capsule、简化 mesh。
4. 从 floor / stairs / ramps / large planes 生成 navmesh source，而不是从全部 splat 生成导航。
5. 用 `scene_graph.json` 或 `simulator_asset_bundle.json` 记录 object category、static/dynamic、support relation、interactable type。
6. 导出 Unity/Unreal/Godot 时，不只是导出 `.ply/.obj/.glb`，而是导出 prefab/actor 级别的组件配置。

## 1. 行业共识：视觉和物理是两套资产

扫描场景进入游戏引擎后通常分成两条线：

| 层 | 目标 | 常见资产 | 典型工具 |
|---|---|---|---|
| 视觉层 | 让场景看起来真实 | 3DGS、Nanite high-poly mesh、textured mesh、light probes、pano/HDRI | SuperSplat、Unreal Nanite、RealityCapture、Luma/Polycam/Scaniverse |
| 几何层 | 让玩家/物体能碰撞 | simplified mesh、UCX collision、box/convex hull、heightfield | Blender、Houdini、Unreal Static Mesh collision、Unity MeshCollider |
| 导航层 | 让角色/NPC 能走 | navmesh、walkable floor polygons、stairs/ramps links | Recast/NavMesh、Unity AI Navigation、Unreal Navigation System |
| 交互层 | 让对象可操作 | prefabs/actors、rigidbody、trigger、socket、animation rig | Unity Prefab、Unreal Blueprint、Godot Scene |
| 语义层 | 让系统知道“是什么” | labels、object ids、scene graph、affordance、physics metadata | DCC tagging、level design metadata、LLM/VLM 辅助标注 |

这就是为什么 photogrammetry 和 3DGS demo 看起来很真实，但一进游戏项目就会被拆：

- 高模 mesh / splat 可能非常重，不适合直接碰撞。
- 扫描表面有洞、噪声、漂浮点和不闭合边界。
- 游戏需要明确的可行走面、墙体阻挡、门窗、可动物体。
- 交互对象需要 pivot、local frame、抓取点、质量、摩擦、脚本事件。
- 引擎 runtime 更关心稳定、可调、可 LOD、可打包，而不是只看离线重建质量。

## 2. 代表性工作流

### 2.1 PlayCanvas / SuperSplat：直接把 3DGS 做成小游戏

PlayCanvas 公开案例 “Turning a Gaussian Splat into a Videogame” 很接近这个问题：他们从 Polycam 扫描得到 Gaussian splat，再做成一个 FPS 风格可行走 demo。

关键步骤不是“直接在 splat 上碰撞”，而是：

1. 用 SuperSplat 编辑清理 splat。
2. 基于 splat 生成碰撞 mesh。
3. 把 splat 放到 PlayCanvas 里作为视觉层。
4. 用碰撞 mesh 做物理阻挡。
5. 用 Blender 补光照探针和场景代理。
6. 添加角色控制器、拾取、射击、物体交互、NPC、NavMesh。

这说明 3DGS 可以进入游戏，但它在游戏里主要是 environment rendering layer。真正让游戏跑起来的是：

- collision mesh
- character controller
- navmesh
- interactive entity
- scripting
- light/probe setup

SuperSplat / SplatTransform 也已经往行业工具方向走：它们不只是看 splat，还在提供 collision generation、压缩格式、编辑和引擎集成能力。

对 Video2Mesh 的启发：

- `semantic_splats.ply` 可以成为视觉层。
- `object_masks_3d` / `bbox_3d` / background planes 可以生成 collision layer。
- `simulator_asset_bundle.json` 应扩展为 game-ready bundle，不只是 robotics simulator bundle。

### 2.2 Unreal / RealityCapture / Nanite：扫描到高保真关卡

Unreal 生态里，RealityCapture/RealityScan 常用于 photogrammetry asset pipeline。典型流程是：

```text
photos / video frames / lidar
  -> RealityCapture alignment
  -> dense reconstruction
  -> high-poly mesh
  -> simplify / retopology
  -> UV unwrap
  -> texture bake
  -> export FBX/OBJ/GLB/texture
  -> Unreal import
  -> Nanite for visual mesh
  -> simple/complex collision setup
  -> navmesh + gameplay actors
```

Unreal Nanite 可以让高面数静态视觉 mesh 进入实时场景，但它仍不等于游戏交互层。碰撞通常仍要单独处理：

- 简单碰撞：box、sphere、capsule、convex hull、UCX meshes。
- 复杂碰撞：使用 render mesh triangles，但昂贵，通常用于静态环境或查询，不适合所有动态物理。
- Gameplay object：用 Blueprint/Actor 包住 mesh、collider、interaction logic。

对扫描场景，Unreal 常见做法是：

- 背景大环境：Nanite high-poly mesh 或 3DGS plugin 做视觉。
- 地面/墙体：单独 simplified collision mesh。
- 可交互物：从扫描中切出来，重新做低模、UV、pivot、碰撞体。
- 导航：只用清理后的地面/楼梯/坡道生成 NavMesh。

### 2.3 Unity：mesh/prefab/component 化

Unity 工作流更强调 prefab 和 component：

```text
scan visual asset
  -> import as mesh / splat renderer
  -> create GameObject hierarchy
  -> add MeshRenderer / SplatRenderer
  -> add BoxCollider / MeshCollider / Convex Collider
  -> add Rigidbody / CharacterController / NavMeshSurface
  -> bake navmesh
  -> add interaction scripts
  -> package prefab / scene
```

Unity 里 MeshCollider 可以用 mesh，但动态刚体通常需要 convex collider；复杂扫描 mesh 直接作为动态碰撞会慢、不稳定，也经常不满足 convex 限制。所以行业做法仍然是：

- 静态环境可以用 simplified MeshCollider 或多个 primitive colliders。
- 动态物体尽量用 primitive / convex hull / compound colliders。
- 角色行走依赖 NavMeshSurface 或 CharacterController，不依赖 splat。
- 视觉 splat 和 physics collider 是两个 sibling objects 或 parent-child objects。

这和 Video2Mesh 当前 `export-simulator-assets --collision-proxy bbox --collider box` 的方向一致，只是还需要更游戏化：

- `interactable_type`
- `prefab_role`
- `navmesh_area`
- `occluder`
- `grab_points`
- `door_hinge` / `drawer_slide`
- `static_batching` / `lod_group`

### 2.4 DCC/外包建模：扫描只是参考，不是最终资产

在游戏/影视资产制作里，扫描常作为高保真参考或高模来源，最终还会经过 DCC：

```text
scan high-poly / splat
  -> cleanup
  -> retopology / decimation
  -> UV unwrap
  -> texture bake
  -> material authoring
  -> collision proxy
  -> LODs
  -> pivot/origin adjustment
  -> naming and hierarchy
  -> engine import
```

特别是可交互对象，通常不会直接用扫描 mesh：

- 桌椅需要合理 pivot 和局部坐标。
- 门需要 hinge axis。
- 抽屉需要 slide axis。
- 瓶子/杯子需要抓取点和稳定碰撞。
- 可破坏物需要 fracture mesh 或替换 prefab。

因此如果 Video2Mesh 目标是“交互游戏场景”，仅做 3DGS-to-mesh 不够，还要做 asset authoring metadata。

## 3. 从 3DGS 到可交互场景的通用架构

推荐把 Video2Mesh 的输出从“一个场景 splat + 若干 object mesh”升级为多层 game scene package：

```text
exports/<run>/game_scene/
  visual/
    scene.splat or scene.spz
    scene_visual.glb
    materials/
    textures/
  collision/
    world_collision.glb
    objects/<object_id>_collider.glb
    navmesh_source.glb
  navigation/
    navmesh.json or engine-specific baked data
    walkable_surfaces.json
  objects/
    <object_id>/
      visual.glb
      collider.glb
      prefab.json
      interaction.json
  semantics/
    scene_graph.json
    labels.json
    affordances.json
  adapters/
    unity/
    unreal/
    godot/
```

### 3.1 Visual Layer

可选表达：

- scene-level 3DGS / SPZ / PLY for photorealistic background。
- high-poly static mesh for Nanite / static rendering。
- object visual GLB for editable objects。
- baked textures/materials。

Video2Mesh 对应：

- `simulator_assets/semantic_splats.ply`
- `simulator_assets/viewer_plys/*_supersplat.ply`
- `objects/<object_id>/mesh_asset`
- 未来的 `scene_visual.glb` / `scene.spz`

### 3.2 Collision Layer

碰撞层要比视觉层简单、闭合、稳定。

常用策略：

| 对象类型 | 推荐 collider | 原因 |
|---|---|---|
| 地面/墙/天花板 | simplified static mesh / boxes / planes | 静态、大、需要稳定阻挡 |
| 桌椅柜等家具 | box / convex hull / compound colliders | 性能好，足够游戏交互 |
| 小物体 | primitive colliders | 稳定、便宜 |
| 楼梯/坡道 | ramp proxy + navmesh | 角色控制更稳定 |
| 复杂不可动物体 | low-poly MeshCollider | 只做静态碰撞 |
| 动态物体 | convex hull / primitive compound | 避免非凸三角网格刚体 |

Video2Mesh 已有：

- `bbox_3d`
- `collision_proxy`
- `body_type`
- `collider`
- `mass_kg`
- `material.friction/restitution`

应增强：

- oriented bbox，而不是只有 axis-aligned bbox。
- convex decomposition。
- per-object compound collider。
- floor/wall/ceiling collision export。
- collision QA：闭合、面数、是否过大、是否偏离视觉 mesh。

### 3.3 Navigation Layer

导航层不是从全部点云或全部 splat 直接生成，而是从 walkable surface 生成：

- floor plane
- ramps
- stairs simplified proxy
- obstacle volumes
- no-walk zones

推荐流程：

```text
background masks + plane fitting + object bboxes
  -> classify floor / obstacle / wall
  -> generate navmesh_source.glb
  -> export Unity NavMeshSurface / Unreal Recast settings
  -> engine bake navmesh
```

第一版可以先输出：

```json
{
  "walkable_surfaces": [
    {"id": "floor_main", "source": "background_structure:floor", "slope": 0.0}
  ],
  "obstacles": [
    {"object_id": "bed", "bbox": "..."},
    {"object_id": "table", "bbox": "..."}
  ]
}
```

### 3.4 Interaction Layer

可交互性来自 object-level prefab/actor，而不是来自 splat：

| 交互类型 | 需要的额外信息 |
|---|---|
| 拾取 | mass、grabbable、grab point、collider、local origin |
| 推动 | rigidbody、friction、mass、stable collider |
| 打开门 | hinge axis、closed/open angle、door frame relation |
| 拉抽屉 | slide axis、limits、handle position |
| 坐下 | seat surface、approach direction、height |
| 遮挡/阻挡 | occluder mesh、static collider |
| 触发区域 | trigger volume、event name |

这就是 scene graph 和 affordance metadata 的价值。

推荐 Video2Mesh 先做规则版：

- category in `chair/sofa/bed`: add `sit_surface_candidate`
- category in `door/cabinet`: add `hinge_candidate`
- small movable object: add `grabbable_candidate`
- large background structure: `static_environment`
- floor: `walkable`

### 3.5 Semantic / Scene Graph Layer

游戏场景需要知道：

- 哪些对象是静态背景。
- 哪些对象可以移动。
- 哪些对象在地面上。
- 哪些对象依附于墙。
- 哪些对象互相支撑。
- 哪些对象可以被脚本引用。

建议输出：

```text
game_scene/semantics/scene_graph.json
```

核心节点：

- scene
- room
- floor/wall/ceiling
- object
- interaction volume
- nav area

核心边：

- contains
- supported_by
- attached_to
- blocks
- walkable_on
- near
- interactable_as

## 4. 对 Video2Mesh 的落地改造建议

### 4.1 新增 game-scene bundle

在现有 `simulator_asset_bundle.json` 旁边新增：

```text
simulator_assets/game_scene_bundle.json
```

最小字段：

```json
{
  "scene_id": "bedroom_4",
  "visual_layer": {
    "splat": "simulator_assets/semantic_splats.ply",
    "preview": "simulator_assets/review/index.html"
  },
  "collision_layer": {
    "world_collision": "simulator_assets/game/collision/world_collision.glb",
    "object_colliders": {}
  },
  "navigation_layer": {
    "navmesh_source": "simulator_assets/game/navigation/navmesh_source.glb",
    "walkable_surfaces": []
  },
  "interaction_layer": {
    "objects": {}
  },
  "semantic_layer": {
    "scene_graph": "simulator_assets/game/semantics/scene_graph.json"
  },
  "adapters": {
    "unity": "...",
    "unreal": "...",
    "godot": "..."
  }
}
```

### 4.2 新增命令建议

建议加 4 个命令：

```bash
python -m video2mesh.cli export-game-collision \
  --project-root exports/<run> \
  --output simulator_assets/game/collision

python -m video2mesh.cli export-game-navigation \
  --project-root exports/<run> \
  --output simulator_assets/game/navigation

python -m video2mesh.cli export-game-scene-graph \
  --project-root exports/<run> \
  --output simulator_assets/game/semantics/scene_graph.json

python -m video2mesh.cli export-game-engine-adapter \
  --project-root exports/<run> \
  --format unity unreal godot
```

第一版实现可以很轻：

- collision：用已有 bbox / background plane 生成 box colliders。
- navigation：用 floor plane + object bbox obstacles 生成 navmesh source manifest。
- scene graph：用 object labels + bbox + support relation 生成 JSON。
- adapters：输出 Unity/Unreal/Godot import manifest，不急着生成完整项目。

### 4.3 Unity adapter 应该输出什么

Unity 方向建议输出：

```text
game_scene/adapters/unity/
  unity_game_scene_adapter.json
  Assets/Video2MeshScene/
    Visual/
    Colliders/
    Prefabs/
    Materials/
```

每个对象：

```json
{
  "object_id": "chair_01",
  "visual": "objects/chair_01/visual.glb",
  "collider": {
    "type": "compound_box",
    "parts": []
  },
  "components": [
    "MeshRenderer",
    "BoxCollider",
    "Rigidbody",
    "V2MInteractable"
  ],
  "physics": {
    "body_type": "dynamic",
    "mass_kg": 4.0,
    "friction": 0.6
  },
  "interaction": {
    "grabbable": true,
    "sit_surface": false
  }
}
```

### 4.4 Unreal adapter 应该输出什么

Unreal 方向建议输出：

```text
game_scene/adapters/unreal/
  unreal_game_scene_adapter.json
  Content/Video2Mesh/
```

关键字段：

- visual asset path
- Nanite recommended true/false
- simple collision mesh path
- complex collision allowed true/false
- actor class
- mobility static/movable
- tags
- gameplay interface metadata

对象策略：

- 背景视觉层：Splat plugin actor 或 Nanite mesh actor。
- 地面墙体：StaticMeshActor + simple collision。
- 动态物体：Blueprint Actor + StaticMeshComponent + simple/convex collision + physics。
- 语义对象：Actor tags / DataAsset。

## 5. 推荐路线图

### 5.1 短期

目标：让扫描结果能进一个 game viewer 并且可走、可撞。

1. 输出 `game_scene_bundle.json`。
2. 从 floor/background planes 生成 world collision proxy。
3. 从 object bbox 生成 object colliders。
4. 从 floor plane 和 obstacle bbox 生成 navmesh source manifest。
5. 在 image-blaster viewer 或 Unity adapter 里加载：
   - splat visual
   - collider mesh
   - object visual meshes
   - simple physics settings。

### 5.2 中期

目标：让物体可交互，而不是只有静态碰撞。

1. 生成 oriented bbox 和 convex hull。
2. 做 collision QA。
3. 生成 scene graph + affordances。
4. 给常见类别生成默认 interaction profile：
   - chair/sofa/bed: sit target
   - door/cabinet: hinge candidate
   - bottle/cup/book: grabbable
   - table/shelf: support surface
5. Unity/Unreal adapter 生成 prefab/actor skeleton。

### 5.3 长期

目标：接近游戏资产生产线。

1. 3DGS-to-mesh 生产质量：
   - TSDF fusion
   - Poisson / SDF refinement
   - texture baking
   - retopology
   - LODs
2. 自动生成 collision compound：
   - convex decomposition
   - stairs/ramp proxies
   - occluder meshes
3. 自动材质和光照：
   - texture atlas
   - PBR material estimation
   - light probes / reflection probes
4. 可编辑关卡：
   - object hierarchy
   - pivot/origin cleanup
   - prefab variants
   - gameplay tags
5. 增量扫描：
   - 新扫描更新 scene graph
   - 保留手工编辑过的 collision/interaction metadata。

## 6. 对我们项目的关键判断

Video2Mesh 当前方向是对的：它已经有 `semantic_splats`、object mask、object mesh、collision proxy、physics metadata、Unity/MuJoCo/Isaac adapter。缺的是把这些从“仿真资产导出”升级为“游戏场景生产包”：

| 已有能力 | 还缺什么 |
|---|---|
| scene-level 3DGS / semantic splat | game visual layer packaging, SPZ/SOGS 等 runtime 格式 |
| object masks / bbox | oriented bbox, support surface, relation graph |
| object mesh baseline | production mesh, texture bake, LOD, pivot cleanup |
| collision proxy bbox | convex/compound/static world collision |
| physics metadata | interaction profiles, gameplay tags |
| Unity adapter skeleton | prefab/actor/component-level adapter |
| review HTML | interactive game viewer with collision/nav/debug overlays |

最重要的改造不是“把 3DGS 转成一个大 mesh”，而是：

```text
把 3DGS 场景拆成 visual、collision、navigation、interaction、semantic 五层，
然后按游戏引擎的 prefab / actor / component 模型导出。
```

这也是游戏行业真正把扫描场景变成可玩空间的方式。

## 参考资料

- [PlayCanvas: Turning a Gaussian Splat into a Videogame](https://blog.playcanvas.com/turning-a-gaussian-splat-into-a-videogame/)
- [PlayCanvas SplatTransform Collision](https://developer.playcanvas.com/user-manual/splat-transform/collision/)
- [SuperSplat](https://superspl.at/)
- [Unreal Engine: Simple versus Complex Collision](https://dev.epicgames.com/documentation/unreal-engine/simple-versus-complex-collision-in-unreal-engine)
- [Unreal Engine: Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- [RealityCapture export documentation](https://rshelp.capturingreality.com/en-US/tools/export.htm)
- [Unity AI Navigation: NavMesh Surface](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavMeshSurface.html)
- [Unity Mesh Collider documentation](https://docs.unity3d.com/Manual/class-MeshCollider.html)
- [Scaniverse SPZ format](https://scaniverse.com/news/spz-gaussian-splat-open-source-file-format)
- [Niantic Labs spz GitHub](https://github.com/nianticlabs/spz)
