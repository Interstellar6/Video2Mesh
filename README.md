# Video2Mesh

Video2Mesh turns a scan video into layered 3D assets: 3DGS visual scene, semantic object masks, object meshes, collision proxies, physics metadata and simulator adapters.

The canonical documentation is now in [docs/](docs/README.md).

## Quick Start

```bash
cd /root/autodl-tmp/workspace/Video2Mesh
source /etc/network_turbo >/dev/null 2>&1 || true

bash tools/run_video2mesh_quick.sh dataset/<video>.mp4
```

Current default route:

```text
video
  -> COLMAP poses and full point cloud
  -> GraphDECO 3DGS
  -> SAM2 masks
  -> 2D-to-3D semantic fusion
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
