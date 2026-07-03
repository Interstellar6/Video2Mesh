---
title: Hunyuan3D
id: video2mesh-object-mesh-completion-hunyuan3d
category: 调研目录
visibility: public
summary: Hunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# Hunyuan3D

![Hunyuan3D-2 examples](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/assets/images/teaser.jpg "Hunyuan3D-2/2.1 面向高分辨率 textured 3D asset generation，可从文本/图像条件生成 object mesh")

## 链接

- GitHub: https://github.com/Tencent-Hunyuan/Hunyuan3D-2
- Model / demo: https://huggingface.co/tencent/Hunyuan3D-2
- Project family: Hunyuan3D-2 / Hunyuan3D-2.1

## 摘要要点

Hunyuan3D 面向 text/image conditioned 3D asset generation。对 Video2Mesh 来说，它不是场景级重建工具，而是 object completion backend：当扫描视频中的某个物体被遮挡、破碎或只需要单独生成更干净的 mesh 时，可以用 object crop/reference image 作为输入，生成 object-local mesh。

它通常能给出比传统点云补洞更“像物体”的外观，但尺度、坐标、物理可用性和语义归属都不是天然正确的。因此输出不能直接进 simulator，需要回填 bbox、pose、semantic id、material 和 collider。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| object reference preparation | 从 SAM/GDINO/semantic mesh 中裁出物体参考图 |
| 3D generation | 生成 object mesh/texture |
| format normalization | 转为 GLB/OBJ 等可导入格式 |
| Video2Mesh import | 按 object id 回填尺度、bbox、pose、semantic sidecar |
| collider generation | 用 primitive/convex/static mesh 生成物理代理 |

输入：物体 crop / reference image，也可以配合文字 prompt。输出：object-local mesh / GLB，以及可选 texture。

## 在 Video2Mesh 中的位置

P1 object visual completion。它可以接在 `prepare-object-images -> export-image-blaster -> mesh-commands` 后面，也可以作为 image-blaster 的默认 backend 之一。当前最适合优先测试床、椅子、柜子、小物体等 foreground objects。

输出结果需要简单摘出来看：

- 几何是否闭合、是否有薄片/飞面。
- 纹理是否和原始视频一致。
- 尺度是否可通过 bbox fitting 拉回场景坐标。
- 是否需要另建 primitive/convex collider，而不是直接用 visual mesh 碰撞。

## 接入判断

- P0：不进入，P0 不应依赖 generative object mesh。
- P1：进入 object completion 实验，优先跑 2-3 个物体并记录 GLB、bbox fit、collider 质量。
- 风险：生成结果可能“好看但不物理”，所以必须拆成 visual mesh 和 collider proxy 两层。
