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
  -> strict 3DGS floater cleanup: COLMAP dense bbox + DBSCAN cluster filter + background plane protection
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

For commands, QA and research decisions, start here:

- [Project Overview](docs/01-project-overview.md)
- [Pipeline And Commands](docs/02-pipeline-and-commands.md)
- [Research Roadmap](docs/03-research-roadmap.md)
- [Mesh, Interaction And Completion](docs/04-mesh-interaction-and-completion.md)
- [Operations And Showcase](docs/05-operations-and-showcase.md)
- [Site And Remote Control](docs/06-site-and-remote-control.md)

Generated data, exports, checkpoints, videos and model weights are intentionally ignored by Git.
