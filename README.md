# Video2Mesh

Video2Mesh turns a scan video into layered 3D assets: 3DGS visual scene, semantic object masks, object meshes, collision proxies, physics metadata and simulator adapters.

Read the published docs at [relumeow.top/video2mesh/](https://relumeow.top/video2mesh/).
The source Markdown lives in [docs/video2mesh/](docs/video2mesh/README.md).

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
  -> GraphDECO 3DGS
  -> SAM2 masks
  -> 2D-to-3D semantic fusion
  -> COLMAP dense Delaunay scene collider mesh
  -> mesh semantic transfer and semantic object mesh splitting
  -> object mesh / completion jobs
  -> collider and physics proxies
  -> MuJoCo / Unity / Isaac assets
```

## Current Status

As of 2026-07-08, the repo default favors a layered runtime asset stack rather
than a single all-purpose mesh. GraphDECO 3DGS remains the visual proxy, while
COLMAP dense Delaunay is the most reliable scene-level collider baseline for
the bedroom_4 experiments. Open3D Poisson and GS2Mesh are kept as comparison
routes, especially for voxelized dense point-cloud outputs and 3DGS-derived
geometry.

Semantic mesh transfer and per-object mesh splitting are now part of the quick
pipeline path, so `bash run.sh` can produce semantic sidecars and object mesh
artifacts alongside the scene collider. GenRecon and Restore3D are tracked as
experimental reconstruction/completion options: the latest bed-focused
GenRecon test improved the bed outline when run on semantic bed points, but it
still pulled wall/window/nightstand context into the mesh, so it is not the
default collider path yet.

For commands, QA and research decisions, start here:

- [Video2Mesh Home](docs/video2mesh/README.md)
- [Research Catalog](docs/video2mesh/research-catalog/overview.md)
- [Experiments](docs/video2mesh/experiments/overview.md)
- [Progress](docs/video2mesh/progress/overview.md)
- [Project Docs](docs/video2mesh/project-docs/overview.md)
- [Legacy Notes](docs/video2mesh/legacy/README.md)

Generated data, exports, checkpoints, videos and model weights are intentionally ignored by Git.
