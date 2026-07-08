---
title: 3DGS Inpainting 与背景 Clean Plate
id: video2mesh-pointcloud-completion-gs-inpainting-clean-plate
category: 调研目录
visibility: public
summary: Inpaint360GS、SplatFill、3DGIC 等方法面向 3DGS object removal 和缺失区域补全，可为 Video2Mesh 的背景 clean plate 和平面洞修补提供 P1/P2 候选路线。
tags:
  - 点云清理与背景补全
  - Research Catalog
  - 3DGS Inpainting
  - Clean Plate
---

# 3DGS Inpainting 与背景 Clean Plate

![3DGS inpainting 与 clean plate](../assets/gs-inpainting-clean-plate.svg "移除前景物体后，先识别背景缺口，再用 copy-fill 或多视角 inpainting 生成可追踪的 clean plate")

## 链接

- Inpaint360GS: Efficient Object-Aware 3D Inpainting via Gaussian Splatting for 360 Scenes: https://arxiv.org/abs/2511.06457
- SplatFill: 3D Scene Inpainting via Depth-Guided Gaussian Splatting: https://arxiv.org/abs/2509.07809
- 3DGIC: 3D Gaussian Inpainting with Depth-Guided Cross-View Consistency: https://arxiv.org/abs/2502.11801
- InFusion: Inpainting 3D Gaussians via Learning Depth Completion from Diffusion Prior: https://arxiv.org/abs/2404.11613
- LaMa image inpainting: https://github.com/advimman/lama
- Stable Diffusion inpainting with Diffusers: https://huggingface.co/docs/diffusers/using-diffusers/inpaint

## 摘要要点

背景 clean plate 的目标是：当我们把床、椅子、柜子这类前景物体单独处理或移除时，能补齐它背后的地板、墙面、柜体侧面等背景。它和 Restore3D 的物体补全相反：Restore3D 补的是被遮挡/破损物体本身，clean plate 补的是物体移开后暴露出来的场景背景。

Inpaint360GS、SplatFill、3DGIC 这类方法共同关注一个问题：只在 2D 单帧补图不够，因为 3DGS 需要多视角一致、深度合理、可重新渲染的表示。它们通常会结合 object mask、深度/几何约束、图像 inpainting 和 3D 表示更新，最后得到可从新视角查看的补全背景。

不过对 Video2Mesh 来说，第一版不应该直接上自由生成。更稳的 P1 是平面 copy-fill：只在 floor/wall/ceiling/cabinet side 这种近似平面上，从洞周围同平面 donor Gaussian 复制颜色、opacity、scale、rotation 统计，再做多视角 QA。生成式 3DGS inpainting 可以放到 P2。

## Pipeline

| 阶段 | 作用 | Video2Mesh 策略 |
|---|---|---|
| object/background 分离 | 找到要移除的前景和应保留的背景 | SAM/语义 mask + Gaussian RoI sidecar |
| 缺口检测 | 渲染 alpha、depth、normal 或平面 mask 找洞 | 先聚焦地面、墙面、天花板、柜体侧面 |
| 局部补全 | copy-fill、2D inpainting、多视角扩散或 3DGS 更新 | P1 copy-fill，P2 生成式 inpainting |
| 几何约束 | 保证新点贴合目标平面或深度 | plane equation、depth residual、scale clamp |
| QA 与 provenance | 标注哪些区域是 synthetic | `inserted_gaussians.json`、hole masks、before/after renders |

## 输入与输出

| 类型 | 内容 |
|---|---|
| 输入 | clean 3DGS、foreground mask、background plane mask、camera poses、可选 depth |
| 输出 | filled PLY、hole masks、inserted Gaussian sidecar、synthetic region provenance、QA renders |

## 在 Video2Mesh 中的位置

它应位于 object completion 和 visual repair 之间：

```text
object RoI / foreground mask
  -> remove or isolate foreground
  -> detect background hole
  -> plane copy-fill or 3DGS inpainting
  -> clean plate visual layer
  -> collider still uses conservative plane / mesh proxy
```

这一步生成的是视觉 clean plate，不是物理真值。地板/墙体 collider 可以用 plane fitting 或 conservative mesh 补齐，但不能直接相信生成纹理里的几何细节。

## 接入判断

- P0：暂不进主链路，避免生成内容污染真实扫描。
- P1：做平面 copy-fill，记录 donor splats、平面方程、插入数量和回滚条件。
- P2：评估 Inpaint360GS / SplatFill / 3DGIC，用同一批 hole masks 做横向比较。

## 风险

- 单视角好看不代表新视角稳定，必须多视角 QA。
- 新增 Gaussian 的 scale/opacity 如果不受约束，很容易变成新的光斑。
- 生成背景必须在文档和 sidecar 中标注 synthetic，不能和真实观测混在一起。
