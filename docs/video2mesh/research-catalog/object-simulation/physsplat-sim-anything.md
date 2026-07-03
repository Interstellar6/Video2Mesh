---
title: PhysSplat / Sim Anything
id: video2mesh-object-simulation-physsplat-sim-anything
category: 调研目录
visibility: public
summary: 这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。
tags:
  - 物体仿真
  - Research Catalog
---

# PhysSplat / Sim Anything

![PhysSplat / Sim Anything pipeline](https://sim-gs.github.io/static/images/pipeline.jpg "Sim Anything / PhysSplat pipeline：open-vocabulary 3D segmentation -> MLLM physical property perception -> PGAS particle sampling + MPM simulation -> render")

## 链接

- Project page: https://sim-gs.github.io/
- Paper: https://arxiv.org/abs/2411.12789
- Code placeholder: https://github.com/CHNxindong/sim-anything
- Venue: ICCV 2025

## 摘要要点

Sim Anything / PhysSplat 的目标不是把 3DGS 转成传统 mesh collider，而是让静态 3DGS 场景里的物体获得可交互动态。它先做 open-vocabulary object segmentation，再用 MLLM 推断物体物理属性，接着用 Material Property Distribution Prediction 估计属性分布，最后通过 Physical-Geometric Adaptive Sampling 采样粒子并进行 MPM simulation。

这条路线和 Video2Mesh 当前“视觉代理 + 碰撞代理 + 语义/物理 sidecar”的分层思路不同。它更像是把物理仿真注入 Gaussian/particle 表示里，适合 deformable object 或动态效果研究；但如果要接 Unity/MuJoCo/Isaac 的标准 asset bundle，仍然需要传统 collider、mass、friction、restitution、joint/constraint 等结构化资产。

## Pipeline

## 输入与输出

| 阶段 | 作用 |
|---|---|
| 3D open-vocabulary segmentation | 从开放世界场景中定位需要仿真的目标物体 |
| multi-view inpainting | 补齐目标移动/变形后可能暴露的背景 |
| MLLM-P3 | 通过多模态大模型推断物体的平均物理属性 |
| MPDP | 将平均物理属性扩展为分布，降低精确手工标注需求 |
| PGAS + MPM | 按几何和物理属性采样粒子，执行 material point simulation |

输入：3DGS 场景、物体分割、交互力或动作条件。输出：物体动态响应、模拟粒子/动态 Gaussian 表示、渲染视频或交互结果。

## 在 Video2Mesh 中的位置

适合作为 P2/P3 的研究方向，尤其在“物体交互”阶段提供参考：如何从语义物体推断物理属性，如何处理软体/可变形物体，如何把 3DGS 视觉和物理动态联系起来。

短期不进入主链路。原因是当前可复现实验和工程接口仍不如传统 physics engine 稳定，而且它的输出不直接等价于 Video2Mesh 需要的 simulator asset bundle。

## 接入判断

- P0：不进入。
- P1：可以借鉴 MLLM 物理属性推断，把 material、mass、friction/restitution 的默认值写入 Video2Mesh sidecar。
- P2/P3：跟踪 dynamic Gaussian / MPM 方向，后面做 deformable object demo 时再尝试复现。
