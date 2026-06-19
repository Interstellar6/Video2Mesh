# Video2Mesh

Video2Mesh turns a spatial scan video into a scene-level 3DGS, object/background 3D semantic masks, object reference frames, coarse object meshes, and simulator-ready assets.

Current default pipeline:

```text
video
  -> MASt3R-SLAM poses + full point cloud
  -> GraphDECO 3D Gaussian Splatting
  -> SAM prompts + SAM2 video masks
  -> 2D-to-3D semantic mask fusion
  -> semantic/probability Gaussian export
  -> object frame selection
  -> object meshes
  -> MuJoCo / Unity / Isaac asset export
```

## Quick Start

Remote server:

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

The quick entrypoint defaults to:

- `GS_BACKEND=graphdeco`
- `GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting`
- `MASK_BACKEND=sam2`
- full MASt3R point cloud for 3DGS and semantic fusion
- simulator/export QA reports at the end

## Long Video Rule

If MASt3R-SLAM runs longer than 1.5 hours without producing `camera_info.json` and `point_cloud.ply`, stop that run and crop the first 60 seconds into a new dataset file:

```bash
ffmpeg -y -i dataset/bedroom_100.mp4 -t 60 -c copy dataset/bedroom_100_first60.mp4
bash tools/run_video2mesh_quick.sh dataset/bedroom_100_first60.mp4
```

## Key Docs

- `Video2Mesh_PROJECT_README.md`: project overview.
- `VIDEO2MESH_PIPELINE.md`: current pipeline and commands.
- `Video2Mesh_real_demo_runbook.md`: remote experiment runbook.
- `REMOTE_SETUP_STATUS.md`: remote environment status.
- `Video2Mesh_milscene3_showcase.md`: showcase asset checklist.
- `SVLGaussian_frame_matching_notes.md`: frame selection algorithm notes.

Generated data, exports, checkpoints, videos, and model weights are intentionally ignored by Git.
