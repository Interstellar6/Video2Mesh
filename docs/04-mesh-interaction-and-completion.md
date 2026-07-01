---
title: Mesh、交互与遮挡补全
category: Simulation
summary: 从 3DGS 到可交互场景的资产分层、mesh 重建、collider、遮挡补全、语义和 SimAnything 动态线。
tags:
  - Mesh
  - Collider
  - Completion
  - SimAnything
---

# Mesh、交互与遮挡补全

## 核心结论

3DGS 不能直接承担碰撞和交互。3DGS 本质是离散高斯椭球体集合，没有 mesh topology，也不能直接生成可靠 collider。

可交互场景应该这样分层：

```text
3DGS visual layer
  + visual mesh / completed mesh
  + simplified collision proxy
  + semantic / scene graph sidecar
  + physics material and body metadata
  + engine adapter
```

视觉要“像”，物理要“稳”，语义要“可查询”。三者不要混成一个资产。

## Scene collider

静态场景的第一版 collider 可以用：

```text
COLMAP dense / fused point cloud
  -> Poisson reconstruction
  -> simplification
  -> scene_collision.glb
```

这和 Azureovo 报告中的 CloudCompare PoissonRecon 路线一致，适合快速补上 Web/Unity 的碰撞闭环。

注意：

- Poisson 会补洞，作为 collider 可以接受，作为 visual mesh 要谨慎。
- scene-level static collider 可以是 concave mesh。
- dynamic object 不应该直接用复杂 concave mesh collider。

## Object visual mesh

生产路线：

```text
trained GraphDECO 3DGS
  + object masks
  + registered camera poses
  -> render object-centric RGB/depth/normal/mask
  -> masked TSDF fusion
  -> marching cubes / Poisson
  -> cleanup / hole fill / simplify
  -> visual mesh
```

这比直接从 sparse object mask cloud 三角化稳定，因为 3DGS 可以提供多视角、可筛选的 rendered evidence。

如果 depth 不稳定，可以接 GS2Mesh-style stereo depth：先渲染 stereo views，再用 stereo model 估深，最后 TSDF fusion。

## SuGaR、GS2Mesh 和其他 mesh 路线

| 方法 | 输入 | 输出 | 适合 |
|---|---|---|---|
| COLMAP/CloudCompare Poisson | dense point cloud | scene mesh | P0 scene collider |
| Open3D Poisson/BPA/alpha | point cloud + normals | baseline mesh | debug / automated baseline |
| TSDF fusion | posed depth maps / 3DGS rendered depth | smooth object mesh | P1 object visual mesh |
| GS2Mesh | 3DGS rendered stereo views | TSDF fused mesh | in-the-wild 3DGS-to-mesh enhancement |
| SuGaR | trained 3DGS | editable mesh + refined GS | P2 visual mesh backend |
| 2DGS / GOF | surface-aware Gaussian optimization | high-quality surface | P2/P3 research backend |
| NeuS / VolSDF | posed images | neural SDF mesh | high-quality offline asset |

![SuGaR pipeline and editing result](https://anttwo.github.io/sugar/results/full_teaser.png "SuGaR 官方项目页图：pipeline 与编辑/合成效果，说明 extracted mesh 可以承接编辑，最终仍可用 Gaussian splatting 渲染")

![Surface-aligned Gaussian arrangement](https://anttwo.github.io/sugar/results/gaussian_arrangement.png "SuGaR 官方项目页图：surface-aligned regularization 让 Gaussians 沿真实表面排列，后续再做 mesh extraction")

推荐顺序：

1. P0：scene collider 用 dense point cloud + Poisson。
2. P1：object visual mesh 用 3DGS rendered depth/mask + TSDF。
3. P1：dynamic object collider 用 primitive / convex decomposition。
4. P2：GS2Mesh-style depth enhancement。
5. P2：SuGaR 单物体 benchmark。

## Collider 策略

| 对象 | 推荐 collider |
|---|---|
| 地面/墙体/大场景 | simplified static MeshCollider |
| 桌椅柜等静态家具 | box / convex hull / compound primitive |
| 动态可移动物体 | primitive / convex decomposition |
| 楼梯/斜坡 | ramp proxy + navmesh |
| 视觉细节复杂物体 | visual mesh 和 physics mesh 分离 |

物体 visual mesh 出来后：

```text
object_mesh.glb
  -> CoACD / V-HACD / primitive fitting
  -> object_collider_compound.glb
  -> export-simulator-assets
```

Unity 中 concave MeshCollider 通常更适合 static/kinematic 场景。动态刚体应优先使用 convex 或 compound colliders。

## 遮挡补全

桌子、椅子这类对象要交互时，遮挡补全要拆成三件事：

```text
object visual completion
background clean plate
physics proxy completion
```

### Object visual completion

如果物体部分被挡住，但需要完整视觉 mesh，可以从 object crops / selected frames 生成完整模型：

- Hunyuan3D。
- Meshy。
- TRELLIS。
- InstantMesh。
- image-blaster external mesh jobs。

生成 mesh 后必须对齐回原场景：

```text
generated object-local mesh
  -> fit to observed 3D bbox
  -> align support plane
  -> record completion source and confidence
```

### Background completion

如果用户移动桌椅，原来被挡住的地面/墙面会露出来。这时需要 clean plate：

```text
video frames + object masks
  -> remove object from frames
  -> 2D image/video inpainting
  -> rebuild / update background 3DGS or background mesh
```

背景补全和物体补全要分开。物体生成得再完整，也不能自动恢复它背后的地板。

### Physics proxy completion

交互不需要真实还原每个不可见三角面。它需要稳定、合理、保守的物理代理：

- table：桌面 box + 桌腿 box/capsule。
- chair：坐垫 box + 靠背 box + 椅腿 + 扶手可选。
- cabinet：box / convex hull。
- plant：粗略 pot collider + visual mesh。

这比拿生成式 visual mesh 直接做碰撞更稳。

## 语义兼容

语义不要塞死在 collider 里。推荐 sidecar：

```json
{
  "mesh": "objects/chair_01.glb",
  "face_semantics": [
    {"face": 1024, "object_id": "chair_01", "label": "chair", "probability": 0.91}
  ],
  "support_surfaces": [
    {"type": "seat", "normal": [0, 1, 0], "height": 0.45}
  ]
}
```

常用策略：

- semantic splats / point cloud 作为主语义数据。
- mesh face center 用 KDTree 或 ray projection 回灌语义。
- collider 或 trigger 只保存可交互需要的语义字段。

## SimAnything / PhysSplat 动态线

SimAnything / PhysSplat 的价值不是 mesh 补全，而是把语义 Gaussian 对象变成可动态仿真的对象：

```text
semantic Gaussian object
  -> physics property inference
  -> particle / Gaussian state
  -> simulation
  -> dynamic splat rendering
```

适合：

- cloth。
- pillow。
- blanket。
- plant leaf。
- liquid / granular / soft object。
- 局部受力形变展示。

不适合替代：

- object visual mesh。
- Unity/MuJoCo collider。
- scale/physics QA。

推荐新增旁路线：

```text
simulator_assets/dynamic_gaussian_assets/
  scene_dynamic_config.json
  objects/<object_id>/gaussians.ply
  objects/<object_id>/physics.json
  objects/<object_id>/constraints.json
  simulations/<sim_id>/trajectory.npz
```

短期最实用的是先接 MLLM/VLM 物理属性草稿：

```text
object crop + mask + label + bbox + support plane
  -> mllm_physics provider
  -> mass / material / friction / restitution / rigid/deformable
  -> import-simulator-physics
  -> simulator-physics-quality-report
```

## 推荐落地方案

第一版可交互：

1. 3DGS 继续做 visual scene。
2. scene collider 用 dense point cloud + Poisson + simplify。
3. object mesh 用 3DGS rendered depth/mask + TSDF。
4. 遮挡严重的常见家具用 generated visual mesh 补全。
5. physics collider 用 bbox/primitive/convex decomposition。
6. semantic / scene graph / physics 用 sidecar 记录。
7. Unity/MuJoCo/Isaac 只消费稳定合同，不直接依赖 3DGS 高斯几何。

这条路线和 Icare / World Labs / Azureovo 报告的共识一致：3DGS 做视觉层，传统 mesh/physics/controller 做交互层。
