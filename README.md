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
  -> GraphDECO 3DGS
  -> GroundingDINO bbox prompts, with SAM/OpenCV auto prompts as fallback
  -> SAM2 masks
  -> 2D-to-3D semantic fusion
  -> COLMAP dense Delaunay scene collider mesh
  -> mesh semantic transfer and semantic object mesh splitting
  -> object mesh / completion jobs
  -> collider and physics proxies
  -> MuJoCo / Unity / Isaac assets
```

For commands, QA and research decisions, start here:

- [Project Overview](docs/01-project-overview.md)
- [Pipeline And Commands](docs/02-pipeline-and-commands.md)
- [Research Roadmap](docs/03-research-roadmap.md)
- [Mesh, Interaction And Completion](docs/04-mesh-interaction-and-completion.md)
- [Operations And Showcase](docs/05-operations-and-showcase.md)
- [Site And Remote Control](docs/06-site-and-remote-control.md)

Generated data, exports, checkpoints, videos and model weights are intentionally ignored by Git.
