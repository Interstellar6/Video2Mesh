---
title: image-blaster Object Jobs
id: video2mesh-object-mesh-completion-image-blaster-object-jobs
category: 调研目录
visibility: public
summary: image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# image-blaster Object Jobs

![image-blaster object jobs](../assets/pipeline-overview.svg "image-blaster 的 object job 目录约定可作为 Video2Mesh 物体补全后端的桥接层")

## 链接

- Local reference repo: `/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/image-blaster`
- Object generation script: `image-blaster/scripts/generate-single-asset.mjs`
- Video2Mesh bridge: `prepare-object-images -> export-image-blaster -> import-object-meshes`

## 简介

image-blaster 把每个 object 放进独立输出目录，生成 reference image，再调用 Hunyuan3D/Meshy 等后端。这种目录约定很适合 Video2Mesh：每个 object 的输入图、prompt、输出 mesh、预览、失败日志和 provenance 都能集中保存。

需要注意的是，image-blaster object job 解决的是“为物体生成 visual mesh”，不是“生成仿真资产包”。尺度、pose、semantic id、collider、mass/friction 和 Unity/MuJoCo/Isaac adapter 仍由 Video2Mesh 承接。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object crop/reference | Video2Mesh 从 mask/selected frame 准备输入图 |
| job directory | 写入 `worlds/<world>/output/<object>/object.json` |
| backend generation | 调用 Hunyuan3D/Meshy 等生成 GLB/OBJ |
| viewer check | React/Three.js 查看 object mesh |
| import back | Video2Mesh 回填 object-local mesh 并 bbox fitting |

## 输入与输出

输入：object crop、prompt、world object config、object id。输出：`object.json`、GLB/OBJ、reference image、viewer assets 和生成日志。

## 在 Video2Mesh 中的位置

可借用目录约定和 object job 思路，但 simulator bundle 仍由 Video2Mesh 导出。它适合接在正式 semantic mesh 的 object split 之后，优先补 bed、nightstand、lamp 等可解释对象。

## 接入判断

- P0：不进入。
- P1：作为 object mesh generation bridge。
- 风险：后端生成物体的尺度和朝向不可信，必须 `fit-object-local-meshes-to-bbox` 并另建 collider。
