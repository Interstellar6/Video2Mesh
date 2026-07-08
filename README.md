# Video2Mesh

Video2Mesh turns a scan video into layered 3D assets: 3DGS visual scene, semantic object masks, object meshes, collision proxies, physics metadata and simulator adapters.

Read the published docs at [relumeow.top/video2mesh/](https://relumeow.top/video2mesh/).
The source Markdown remains in [docs/](docs/README.md).

## Quick Start

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash run.sh dataset/<video>.mp4
```

`bash run.sh` wraps `tools/run_video2mesh_quick.sh`; if no argument is passed it
uses `VIDEO=/path/to/video.mp4` or the first video found under `dataset/` or
`inputs/`.

Current default route:

```text
video
  -> COLMAP poses and full point cloud
  -> COLMAP dense fused.ply cleaned as GraphDECO init
  -> GraphDECO 3DGS
  -> scene-only 3DGS cleanup: COLMAP dense bbox + DBSCAN detached-cluster filter + background plane protection
  -> GroundingDINO bbox prompts, with SAM/OpenCV auto prompts as fallback
  -> SAM2 masks
  -> 2D-to-3D semantic fusion
  -> semantic 3DGS / SuperSplat export
  -> conservative object-fragment merge suggestions/applied small components
  -> COLMAP dense Delaunay scene collider mesh
  -> mesh semantic transfer and semantic object mesh splitting
  -> per-object PLY mesh reconstruction / completion jobs
  -> collider and physics proxies
  -> simulator asset bundle
```

Simulator adapters are skipped by default in the quick pipeline while mesh and
collider quality is still being tuned. Re-enable them explicitly with
`RUN_SIMULATOR_ADAPTERS=1`.

The slower Gaussian probability backprojection route is also optional now; the
default route uses semantic splats directly for mesh semantic transfer. Re-enable
the projected probability experiment with `GAUSSIAN_BACKPROJECT=1`.

If the GraphDECO 3DGS run is available but the lightweight gsplat preview
dependencies are not installed, keep the visual/mesh pipeline moving with
`RENDER_GSPLAT_PREVIEW=0`. This only skips the preview render, not the
GraphDECO training output or viewer PLY exports.

The default 3DGS cleanup is intentionally conservative for room-scale scenes:
it does not remove KNN/MAD sparse points or low-opacity elongated Gaussians by
default, because those rules removed real walls and floors in bedroom scans.
Use `STRICT_3DGS_GEOMETRIC_OUTLIERS=1` or `STRICT_3DGS_ELONGATION_FILTER=1`
only for debugging a noisy visual layer.

On multi-GPU servers, keep `CUDA_VISIBLE_DEVICES` unset for the full quick
pipeline unless you are intentionally pinning the whole process. Prefer explicit
stage assignment:

```bash
COLMAP_USE_GPU=1 \
COLMAP_GPU_INDEX=0,1,2,3,4,5,6,7 \
COLMAP_DENSE_GPU_INDEX=0,1,2,3,4,5,6,7 \
GRAPHDECO_CUDA_VISIBLE_DEVICES=0 \
GROUNDINGDINO_DEVICE=cuda:1 \
SAM_DEVICE=cuda:1 \
SAM2_DEVICE=cuda:1 \
bash run.sh dataset/<video>.mp4
```

COLMAP dense stereo is the main single-run multi-GPU acceleration point.
GraphDECO's reference trainer is still single-scene/single-process in this
pipeline, so use `GRAPHDECO_CUDA_VISIBLE_DEVICES=<gpu>` for one run, or launch
multiple independent scenes/parameter sweeps on different GPUs.

Some servers ship a COLMAP binary that can run sparse/dense MVS but was built
without CGAL-backed Delaunay meshing. In that case keep `COLMAP_BINARY` for
SfM/MVS and point only the scene mesh stage at a CGAL-capable binary or wrapper:

```bash
SCENE_MESH_COLMAP_BINARY=tools/colmap_with_libstdcxx.sh \
COLMAP_REAL_BINARY=/data/zyx/workspace/Video2MeshWorkspace/colmap_cuda/bin/colmap \
COLMAP_LIBSTDCXX_DIR=/data/zyx/workspace/Video2MeshWorkspace/third_party/runtime_libs/libstdcxx_compat \
RENDER_GSPLAT_PREVIEW=0 \
bash run.sh dataset/<video>.mp4
```

Prepared production-upgrade jobs and external per-object mesh jobs also support
outer-loop GPU assignment. For generated `run_mesh_jobs.sh` scripts, use:

```bash
RUN_PARALLEL=1 GPU_POOL=0,1,2,3 MAX_PARALLEL_JOBS=4 bash run_mesh_jobs.sh
```

For future multi-object or multi-configuration training/reconstruction stages,
prefer this outer-loop GPU pool style by default. Single-scene stages that are
CPU-bound or single-process by design should stay single-task until their own
backend supports robust distributed execution.

For commands, QA and research decisions, start here:

- [Project Overview](docs/01-project-overview.md)
- [Pipeline And Commands](docs/02-pipeline-and-commands.md)
- [Research Roadmap](docs/03-research-roadmap.md)
- [Mesh, Interaction And Completion](docs/04-mesh-interaction-and-completion.md)
- [Operations And Showcase](docs/05-operations-and-showcase.md)
- [Site And Remote Control](docs/06-site-and-remote-control.md)

Generated data, exports, checkpoints, videos and model weights are intentionally ignored by Git.
