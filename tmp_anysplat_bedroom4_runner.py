#!/usr/bin/env python3
import argparse
import json
import os
import platform
import shutil
import socket
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageDraw


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _file_record(path: Path, root: Path | None = None) -> dict:
    path = Path(path)
    try:
        rel = str(path.relative_to(root)) if root else str(path)
    except ValueError:
        rel = str(path)
    return {
        "path": str(path),
        "relative_path": rel,
        "size_bytes": path.stat().st_size if path.exists() else None,
    }


def _extract_video_frames(video_path: Path, image_dir: Path, fps: float) -> list[Path]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / source_fps if source_fps > 0 else None
    interval = max(1, int(round(source_fps / fps))) if source_fps > 0 and fps > 0 else 1

    written: list[Path] = []
    frame_index = 0
    output_index = 0
    while True:
        ok, frame_bgr = capture.read()
        if not ok:
            break
        if frame_index % interval == 0:
            out = image_dir / f"{output_index:06d}.png"
            if not cv2.imwrite(str(out), frame_bgr):
                raise RuntimeError(f"Could not write extracted frame: {out}")
            written.append(out)
            output_index += 1
        frame_index += 1
    capture.release()

    return written, {
        "source_fps": source_fps,
        "source_frame_count": frame_count,
        "source_duration_seconds": duration,
        "sample_fps": fps,
        "frame_interval": interval,
    }


def _copy_sampled_images(source_dir: Path, image_dir: Path, max_images: int | None) -> list[Path]:
    candidates = sorted(
        p
        for p in source_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if not candidates:
        raise RuntimeError(f"No input images found in {source_dir}")
    if max_images and len(candidates) > max_images:
        if max_images == 1:
            selected = [candidates[len(candidates) // 2]]
        else:
            selected = [
                candidates[round(i * (len(candidates) - 1) / (max_images - 1))]
                for i in range(max_images)
            ]
    else:
        selected = candidates

    written = []
    for idx, src in enumerate(selected):
        dst = image_dir / f"{idx:06d}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        written.append(dst)
    return written


def _make_contact_sheet(image_paths: list[Path], out_path: Path, max_tiles: int = 12) -> None:
    if not image_paths:
        return
    selected = image_paths[:max_tiles]
    thumbs = []
    for path in selected:
        im = Image.open(path).convert("RGB")
        im.thumbnail((192, 108))
        tile = Image.new("RGB", (192, 128), "white")
        x = (192 - im.width) // 2
        tile.paste(im, (x, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((6, 110), path.name, fill=(0, 0, 0))
        thumbs.append(tile)

    cols = min(4, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 192, rows * 128), "white")
    for i, tile in enumerate(thumbs):
        sheet.paste(tile, ((i % cols) * 192, (i // cols) * 128))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=92)


def _save_video_preview(video_path: Path, out_path: Path) -> None:
    capture = cv2.VideoCapture(str(video_path))
    ok, frame = capture.read()
    capture.release()
    if ok:
        cv2.imwrite(str(out_path), frame)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--source-video", type=Path)
    parser.add_argument("--source-images", type=Path)
    parser.add_argument("--sample-fps", default=1.0, type=float)
    parser.add_argument("--max-images", default=None, type=int)
    parser.add_argument("--model-id", default="lhjiang/anysplat")
    parser.add_argument("--vggt-model-id", default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if not args.source_video and not args.source_images:
        raise SystemExit("Provide --source-video or --source-images")

    start = time.time()
    outdir = args.outdir.resolve()
    image_dir = outdir / "images"
    preview_dir = outdir / "previews"
    logs_dir = outdir / "logs"
    image_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    repo_root = _repo_root()
    sys.path.append(str(repo_root))

    metadata = {
        "status": "running",
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "repo_root": str(repo_root),
        "outdir": str(outdir),
        "model_id": args.model_id,
        "vggt_model_id": args.vggt_model_id,
        "device_arg": args.device,
        "source_video": str(args.source_video) if args.source_video else None,
        "source_images": str(args.source_images) if args.source_images else None,
        "sample_fps": args.sample_fps,
        "max_images": args.max_images,
        "python": sys.version,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "outputs": {},
    }

    try:
        if args.source_video:
            image_paths, extraction = _extract_video_frames(args.source_video, image_dir, args.sample_fps)
            metadata["video_extraction"] = extraction
        else:
            image_paths = _copy_sampled_images(args.source_images, image_dir, args.max_images)
            metadata["image_sampling"] = {
                "source_count": len(list(args.source_images.glob("*"))),
                "selected_count": len(image_paths),
            }

        if not image_paths:
            raise RuntimeError("No frames were prepared for AnySplat")

        _make_contact_sheet(image_paths, preview_dir / "input_contact_sheet.jpg")
        metadata["input_images"] = [_file_record(p, outdir) for p in image_paths]
        metadata["input_image_count"] = len(image_paths)

        if args.vggt_model_id:
            from src.model.encoder.vggt.models.vggt import VGGT

            original_vggt_from_pretrained = VGGT.from_pretrained

            def patched_vggt_from_pretrained(model_id, *model_args, **model_kwargs):
                if model_id == "facebook/VGGT-1B":
                    print(
                        f"[AnySplat] redirecting VGGT model to {args.vggt_model_id}",
                        flush=True,
                    )
                    return original_vggt_from_pretrained(
                        args.vggt_model_id, *model_args, **model_kwargs
                    )
                return original_vggt_from_pretrained(
                    model_id, *model_args, **model_kwargs
                )

            VGGT.from_pretrained = patched_vggt_from_pretrained

        from src.misc.image_io import save_interpolated_video
        from src.model.model.anysplat import AnySplat
        from src.model.ply_export import export_ply
        from src.utils.image import process_image

        device = torch.device(args.device if torch.cuda.is_available() else "cpu")
        metadata["resolved_device"] = str(device)
        if device.type == "cuda":
            metadata["gpu_name"] = torch.cuda.get_device_name(0)

        print(f"[AnySplat] loading model {args.model_id}", flush=True)
        model_load_start = time.time()
        model = AnySplat.from_pretrained(args.model_id)
        model = model.to(device)
        model.eval()
        for param in model.parameters():
            param.requires_grad = False
        metadata["model_load_seconds"] = round(time.time() - model_load_start, 3)

        print(f"[AnySplat] processing {len(image_paths)} images", flush=True)
        processed = [process_image(str(p)) for p in image_paths]
        images = torch.stack(processed, dim=0).unsqueeze(0).to(device)
        metadata["model_input_shape"] = list(images.shape)

        print("[AnySplat] running inference", flush=True)
        infer_start = time.time()
        with torch.inference_mode():
            gaussians, pred_context_pose = model.inference((images + 1) * 0.5)
        if device.type == "cuda":
            torch.cuda.synchronize()
            metadata["cuda_max_memory_allocated_bytes"] = torch.cuda.max_memory_allocated()
        metadata["inference_seconds"] = round(time.time() - infer_start, 3)
        metadata["gaussian_count"] = int(gaussians.means.shape[1])
        metadata["pred_extrinsic_shape"] = list(pred_context_pose["extrinsic"].shape)
        metadata["pred_intrinsic_shape"] = list(pred_context_pose["intrinsic"].shape)

        print("[AnySplat] exporting gaussians.ply", flush=True)
        ply_path = outdir / "gaussians.ply"
        export_ply(
            gaussians.means[0],
            gaussians.scales[0],
            gaussians.rotations[0],
            gaussians.harmonics[0],
            gaussians.opacities[0],
            ply_path,
            save_sh_dc_only=True,
        )

        cameras_path = outdir / "predicted_cameras.npz"
        np.savez(
            cameras_path,
            extrinsic=pred_context_pose["extrinsic"].detach().cpu().numpy(),
            intrinsic=pred_context_pose["intrinsic"].detach().cpu().numpy(),
        )
        metadata["outputs"] = {
            "gaussians_ply": _file_record(ply_path, outdir),
            "predicted_cameras": _file_record(cameras_path, outdir),
            "input_contact_sheet": _file_record(preview_dir / "input_contact_sheet.jpg", outdir),
        }

        print("[AnySplat] saving rgb/depth videos", flush=True)
        b, v, c, h, w = images.shape
        try:
            video_path, depth_path = save_interpolated_video(
                pred_context_pose["extrinsic"],
                pred_context_pose["intrinsic"],
                b,
                h,
                w,
                gaussians,
                str(outdir),
                model.decoder,
            )

            _save_video_preview(Path(video_path), preview_dir / "rgb_first_frame.jpg")
            _save_video_preview(Path(depth_path), preview_dir / "depth_first_frame.jpg")
            metadata["outputs"].update(
                {
                    "rgb_video": _file_record(Path(video_path), outdir),
                    "depth_video": _file_record(Path(depth_path), outdir),
                    "rgb_first_frame": _file_record(preview_dir / "rgb_first_frame.jpg", outdir),
                    "depth_first_frame": _file_record(preview_dir / "depth_first_frame.jpg", outdir),
                }
            )
            metadata["status"] = "success"
        except Exception as video_exc:
            metadata["status"] = "partial_success_video_failed"
            metadata["video_error"] = repr(video_exc)
            metadata["video_traceback"] = traceback.format_exc()
            print(metadata["video_traceback"], file=sys.stderr, flush=True)
        return 0
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = repr(exc)
        metadata["traceback"] = traceback.format_exc()
        print(metadata["traceback"], file=sys.stderr, flush=True)
        return 1
    finally:
        metadata["finished_at"] = datetime.now().isoformat(timespec="seconds")
        metadata["elapsed_seconds"] = round(time.time() - start, 3)
        metadata_path = outdir / "run_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[AnySplat] metadata written to {metadata_path}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
