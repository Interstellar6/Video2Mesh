---
title: image-blaster
id: video2mesh-industrial-pipelines-image-blaster
category: 调研目录
visibility: public
summary: image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以生成 object mesh，但不直接输出 MuJoCo/Isaac/Unity simulator bundle。
tags:
  - 工业资产管线
  - Research Catalog
---

# image-blaster

## 链接

- Local reference repo: `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/image-blaster`
- 相关脚本：`scripts/generate-single-asset.mjs`、`scripts/generate-world.mjs`
- Viewer 相关：`app/vite.config.ts`、`SceneObject.tsx`、`ObjectGrid.tsx`、`useSceneObjectVisual.ts`

## 简介

image-blaster 更偏 object mesh generation 和 Three.js/Rapier 浏览器查看约定。它可以为每个对象生成 object-local mesh，并以 `worlds/<world>/output/<object>/` 的目录组织资产；浏览器 viewer 侧稳定消费 `.glb`。但它本身不直接输出 MuJoCo/Isaac/Unity simulator bundle，物理属性、语义 ID、尺度/位姿归一化和引擎适配仍需要 Video2Mesh 承接。

## Pipeline 摘要

![image-blaster 在 Video2Mesh 中的位置](../assets/pipeline-overview.svg "image-blaster 更适合接在 object crop / reference image 之后，作为物体外观补全后端，再回填到 Video2Mesh simulator bundle")

## 输入与输出

| 阶段 | 作用 |
|---|---|
| object crop/reference image | Video2Mesh 从 SAM/GDINO/semantic mesh 里准备物体裁剪图 |
| object generation backend | 通过 Hunyuan3D 或 Meshy 等后端生成 `.glb/.obj` |
| local object directory | 写入 `object.json`、mesh 文件和预览资产 |
| React/Three.js viewer | 用 GLTFLoader 加载 GLB，并交给 Rapier/scene object 交互 |

输入：object crop、prompt、world config。输出：object mesh、object.json、viewer 目录。对 Video2Mesh 来说，最关键的输出是可回填的 object-local mesh，而不是 viewer 本身。

## 在 Video2Mesh 中的位置

P1 物体补全后端和目录约定参考。推荐桥接方式是：

1. `prepare-object-images` 从 mask/semantic sidecar 生成 object reference image。
2. `export-image-blaster` 写出 image-blaster 可消费的 world/object job。
3. image-blaster 生成 object mesh。
4. `import-object-meshes` 将 GLB/OBJ 回填 Video2Mesh。
5. `export-simulator-assets --fit-object-local-meshes-to-bbox` 统一尺度、姿态、物理属性和引擎 adapter。

这能把 image-blaster 放在“物体视觉补全”位置，而不把它误认为完整 simulator exporter。

## 接入判断

- P0：不依赖它闭环；P0 先保证 scene collider 和 semantic sidecar。
- P1：适合作为 object completion backend，重点接床、桌椅、小物体等缺损物体。
- 风险：生成 mesh 的尺度和坐标系不可完全信任，需要 bbox fitting、object pose 和碰撞代理重新生成。
