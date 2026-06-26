# Video2Mesh

Video2Mesh turns a spatial scan video into a scene-level 3DGS, object/background 3D semantic masks, object reference frames, 3DGS-derived object meshes, and simulator-ready assets.

Current default pipeline:

```text
video
  -> uniform dense real-frame extraction (<=200 frames)
  -> COLMAP poses + full sparse point cloud
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

bash run.sh --image_path dataset/<video>.mp4
```

Equivalent direct quick runner:

```bash
bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

Run a fixed real-video window without interpolation:

```bash
START_SEC=47 END_SEC=56 MAX_FRAMES=200 EXTRACT_EVERY=1 \
bash tools/run_video2mesh_quick.sh dataset/bedroom_4_CmEIg9gMI74/bedroom_4_Cm.mp4
```

The quick entrypoint defaults to:

- `RUN_COLMAP=1`
- `RUN_MAST3R=0`
- `MAX_FRAMES=200`
- `GS_BACKEND=graphdeco`
- `GRAPHDECO_ROOT=/root/autodl-tmp/workspace/gaussian-splatting`
- `GRAPHDECO_ITERATIONS=30000`
- `MASK_BACKEND=sam2`
- full COLMAP sparse `scene/reconstruction/point_cloud.ply` for 3DGS and semantic fusion
- simulator/export QA reports at the end

Frame extraction first computes how many real frames the requested video/window
would produce. If that exceeds `MAX_FRAMES`, it uniformly samples from those
decoded source frames instead of interpolating or using synthetic frames.

The GraphDECO default is now the full training preset: full COLMAP point-cloud
initialization, 30000 iterations, checkpoints at 7000 and 30000,
densification/pruning, opacity reset, and SH degree 3 appearance enabled. Use
smaller overrides only for explicit smoke tests or memory-constrained debugging.

## Object Mesh Route

`reconstruct-object-meshes` can still export quick OBJ baselines from fused
object mask point clouds so the simulator/export path has concrete geometry to
inspect. Those OBJ files are not the target 3DGS-to-mesh method.

Current mask-cloud OBJ output is expected to be fragmented: sparse/uneven point
support creates many disconnected triangle islands, holes, floating sheets, and
non-watertight surfaces. Treat these meshes as debug geometry only, useful for
checking object scale, rough placement, and export wiring. They should not be
shown as final object assets.

The default production direction is:

```text
trained 3DGS + object 2D/3D masks + registered cameras
  -> render multi-view RGB/depth/normal/mask observations
  -> fuse masked depth/normal evidence with TSDF fusion
  -> extract surfaces with marching cubes / Poisson reconstruction
  -> optionally refine with NeuS-style SDF optimization
  -> bake texture, simplify collider, export simulator mesh
```

This route treats 3DGS as the geometric scene representation and extracts a
surface from rendered multi-view evidence, rather than meshing raw sparse
points directly.

## Frame Window Rule

Frame extraction uses real decoded frames only. For a requested full video or
time window, the pipeline estimates the candidate frame count first. If the
candidate count exceeds `MAX_FRAMES`, it uniformly samples from those real
frames so total input stays within the cap.

```bash
START_SEC=47 END_SEC=56 MAX_FRAMES=200 EXTRACT_EVERY=1 \
bash tools/run_video2mesh_quick.sh dataset/bedroom_4_CmEIg9gMI74/bedroom_4_Cm.mp4
```

If COLMAP fails readiness because the segment has too little parallax or too
few registered poses, choose a different real time window and rerun. Do not
fill gaps with interpolated frames.

After a project already has valid COLMAP/GraphDECO outputs, resume a lighter
downstream pass with:

```bash
bash tools/run_video2mesh_downstream_light.sh exports/<run> dataset/<video>_best10.mp4
```

This resume script still fuses object masks against the full scene point cloud,
but caps background-plane RANSAC sampling by default so recovery runs remain
interactive on 16M+ point clouds.

Refresh demo/advisor reports and list showable files with:

```bash
bash tools/audit_showcase_artifacts.sh exports/<run>
```

When exporting semantic masks for large GraphDECO runs, avoid generating viewer
PLYs inside `export-splat-masks` if the semantic source PLY is already large:

```bash
python -m video2mesh.cli export-splat-masks \
  --project-root exports/<run> \
  --splat-ply exports/<run>/scene/reconstruction/point_cloud.ply \
  --mask-source-ply exports/<run>/scene/reconstruction/point_cloud.ply \
  --transfer-mode index \
  --no-export-viewer-plys \
  --output exports/<run>/simulator_assets/semantic_point_cloud_full.ply

python -m video2mesh.cli export-viewer-plys \
  --project-root exports/<run> \
  --splat-ply exports/<run>/simulator_assets/semantic_point_cloud_full.ply \
  --output-dir exports/<run>/simulator_assets/viewer_plys \
  --prefix semantic_3dgs \
  --include-labels
```

## Key Docs

- `Video2Mesh_PROJECT_README.md`: project overview.
- `VIDEO2MESH_PIPELINE.md`: current pipeline and commands.
- `Video2Mesh_real_demo_runbook.md`: remote experiment runbook.
- `REMOTE_SETUP_STATUS.md`: remote environment status.
- `Video2Mesh_milscene3_showcase.md`: showcase asset checklist.
- `SVLGaussian_frame_matching_notes.md`: frame selection algorithm notes.

Generated data, exports, checkpoints, videos, and model weights are intentionally ignored by Git.
