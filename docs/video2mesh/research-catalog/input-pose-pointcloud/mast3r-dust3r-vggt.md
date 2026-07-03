---
title: MASt3R / DUSt3R / VGGT
id: video2mesh-input-pose-pointcloud-mast3r-dust3r-vggt
category: 调研目录
visibility: public
summary: 这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。
tags:
  - 输入、位姿与点云
  - Research Catalog
---

# MASt3R / DUSt3R / VGGT

## 简介

这一组 learned geometry 方法适合作为 COLMAP 失败时的 pose/point cloud fallback，也适合处理纹理弱、视角少、匹配困难的输入。

## 输入与输出

输入：图像对或图像序列。输出：相对几何、点图、相机或轨迹估计。

## 在 Video2Mesh 中的位置

P1 fallback。需要和 Video2Mesh 的 camera_info.json、尺度、坐标约定对齐。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
