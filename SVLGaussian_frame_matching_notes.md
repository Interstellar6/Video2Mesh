# Video2Mesh 帧匹配算法说明

更新时间：2026-06-20

## 1. 算法目的

帧匹配模块解决的问题是：

给定一个已经有 2D masks 和 3D mask 的物体，自动找出若干相关帧，用于后续物体裁图、单物体 mesh 或多视角 mesh 重建。

它不是传统图像检索，也不是完整复现 SVLGaussian 论文。当前实现采用的是论文里的 view-selection protocol 工程化适配：RE10K 的 5/10 frame offset、30-frame random interval，以及 lerf_ovs 的 ±3 frame visibility window，并结合 Video2Mesh 已有的 object mask 可见性和 crop 多样性。

## 2. 输入

每个 object 有：

```text
masks/2d/<object_id>/<frame>.png
masks/3d/<object_id>/point_indices.json
scene/frames 或 scene/mast3r_keyframes
camera_info.json
```

每个候选帧会计算：

- mask area：物体在图像里是否足够大。
- hit points：该帧 mask 能解释多少 3D 点。
- sharpness：裁图是否模糊。
- masked crop feature：用于去重和视角多样性。

## 3. 选择步骤

### Step 1：选 anchor

选择质量最高、可见性最好的帧：

```text
reason = svlgaussian_anchor_best_visible
```

当前策略优先选择能覆盖更多 offset 的 anchor，再按 object 可见性分数排序：

```text
reason = svlgaussian_anchor_offset_coverage
```

### Step 2：补 5/10 frame offset

围绕 anchor 查找：

```text
anchor +/- 5
anchor +/- 10
```

允许 visibility window：

```text
±3 frames
```

输出 reason：

```text
svlgaussian_offset_5
svlgaussian_offset_10
```

### Step 3：补随机窗口

在 anchor 附近：

```text
±30 frames
```

用固定 seed 选择一个可复现的补充视角：

```text
svlgaussian_random_window_30
```

### Step 4：masked crop diversity fallback

默认 `top_k=4`，对应：

```text
anchor + offset_5 + offset_10 + random_window
```

如果候选帧不足或无法满足 offset/random slot，才对候选 crop 计算简化视觉特征：

```text
mask bbox crop -> grayscale -> resize 32x32 -> normalize -> dot-product similarity
```

然后按：

```text
quality_score - similarity_penalty * max_similarity + temporal_bonus
```

补足剩余帧。

## 4. 输出

```text
objects/<object_id>/selected_frames/
simulator_assets/selected_frames.json
simulator_assets/frame_selection_matching/frame_selection_matching_report.json
simulator_assets/frame_selection_quality_report.json
```

每条记录会保存：

- frame id
- score
- selection reason
- mask/crop path
- offset coverage
- protocol_slots.expected_top_k
- per-object offset match details

其中 `frame_selection_matching_report.json` 会记录官方 DOI：

```text
10.1049/cit2.70148
```

并显式说明采用的是 SVLGaussian 的 view-selection protocol，而不是完整单图 SVLGaussian pipeline。

## 5. 当前局限

- 如果 SAM2 masks 本身过分割，选帧会为“碎片 object”选帧，而不是完整真实物体。
- 如果物体只在少数 keyframes 可见，5/10 offset 可能无法满足。
- 当前 crop feature 是轻量灰度特征，不是 CLIP/DINOv2 级别的语义匹配。
- 对花草、折叠椅、杆状物等复杂结构，需要先提升 segmentation 和 object merge，再谈高质量 mesh。

## 6. 推荐升级

1. 用 DINOv2/CLIP crop feature 替代 32x32 灰度特征。
2. 结合 camera baseline 和 viewing angle 选择真正多视角帧。
3. 将 object merge 结果反馈到 frame selection，避免为碎片单独重建 mesh。
4. 对每个 selected frame 增加可视化 QA：原图、mask、crop、命中 3D 点。
