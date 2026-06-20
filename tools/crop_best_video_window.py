#!/usr/bin/env python3
"""Crop a stable, textured scan-video window without requiring ffmpeg.

The default mode scores candidate windows by sharpness, contrast, exposure, and
moderate frame-to-frame motion. It is intended for the Video2Mesh fallback path:
when a first-60-second retry reconstructs as a single pose or empty point cloud,
crop a better 10-second segment and rerun the quick pipeline.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Input scan video.")
    parser.add_argument("--duration", type=float, default=10.0, help="Window duration in seconds.")
    parser.add_argument("--start", type=float, help="Explicit start time in seconds. If omitted, score windows.")
    parser.add_argument("--output", type=Path, help="Output mp4 path. Defaults beside input with a best-duration suffix.")
    parser.add_argument("--report", type=Path, help="JSON report path. Defaults to output path with .json suffix.")
    parser.add_argument("--sample-fps", type=float, default=2.0, help="Sampling rate used for scoring.")
    parser.add_argument("--window-step", type=float, default=1.0, help="Candidate-window stride in seconds.")
    parser.add_argument("--resize-width", type=int, default=320, help="Scoring resize width; keeps aspect ratio.")
    parser.add_argument("--max-scan-seconds", type=float, default=0.0, help="Limit scoring scan duration; 0 scans all.")
    parser.add_argument("--codec", default="mp4v", help="OpenCV VideoWriter fourcc, default mp4v.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output/report.")
    parser.add_argument("--dry-run", action="store_true", help="Only score and write the JSON report.")
    return parser.parse_args()


def import_cv2():
    try:
        import cv2  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime image
        raise RuntimeError("OpenCV is required. Install opencv-python or use the Video2Mesh venv.") from exc
    return cv2


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def default_output_path(video: Path, duration: float) -> Path:
    seconds = int(round(duration))
    suffix = f"best{seconds}" if seconds == duration else f"best{str(duration).replace('.', 'p')}"
    return video.with_name(f"{video.stem}_{suffix}{video.suffix or '.mp4'}")


def read_video_meta(video: Path) -> dict[str, Any]:
    cv2 = import_cv2()
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if not math.isfinite(fps) or fps <= 0:
        fps = 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    duration = frame_count / fps if frame_count > 0 else 0.0
    return {"fps": fps, "frame_count": frame_count, "width": width, "height": height, "duration": duration}


def resized_gray(frame: Any, resize_width: int) -> Any:
    cv2 = import_cv2()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if resize_width > 0 and gray.shape[1] > resize_width:
        scale = resize_width / float(gray.shape[1])
        gray = cv2.resize(gray, (resize_width, max(1, int(round(gray.shape[0] * scale)))))
    return gray


def collect_samples(video: Path, sample_fps: float, resize_width: int, max_scan_seconds: float) -> list[dict[str, float]]:
    cv2 = import_cv2()
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if not math.isfinite(fps) or fps <= 0:
        fps = 30.0

    sample_step = max(1, int(round(fps / max(0.1, sample_fps))))
    samples: list[dict[str, float]] = []
    previous_gray = None
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = frame_idx / fps
        if max_scan_seconds > 0 and t > max_scan_seconds:
            break
        if frame_idx % sample_step == 0:
            gray = resized_gray(frame, resize_width)
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            brightness = float(gray.mean())
            contrast = float(gray.std())
            diff = 0.0
            if previous_gray is not None:
                diff = float(cv2.absdiff(gray, previous_gray).mean())
            samples.append(
                {
                    "time": t,
                    "sharpness": sharpness,
                    "brightness": brightness,
                    "contrast": contrast,
                    "diff": diff,
                }
            )
            previous_gray = gray
        frame_idx += 1
    cap.release()
    return samples


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return 0.5 * (values[mid - 1] + values[mid])


def score_motion(value: float) -> float:
    if value <= 0:
        return 0.0
    low, target, high = 3.0, 18.0, 45.0
    if value < low:
        return 0.5 * value / low
    if value <= target:
        return 0.5 + 0.5 * (value - low) / (target - low)
    if value <= high:
        return 1.0 - 0.35 * (value - target) / (high - target)
    return clamp(0.65 - (value - high) / 80.0)


def score_window(samples: list[dict[str, float]], start: float, duration: float) -> dict[str, Any]:
    end = start + duration
    window = [item for item in samples if start <= item["time"] < end]
    if len(window) < 2:
        return {"start": start, "end": end, "score": -1.0, "sample_count": len(window)}

    sharpness = [item["sharpness"] for item in window]
    brightness = [item["brightness"] for item in window]
    contrast = [item["contrast"] for item in window]
    diffs = [item["diff"] for item in window[1:]]

    sharp_median = median(sharpness)
    brightness_mean = sum(brightness) / len(brightness)
    contrast_median = median(contrast)
    motion_median = median(diffs)
    coverage = abs(window[-1]["brightness"] - window[0]["brightness"]) + median(diffs) * 0.5

    sharp_score = clamp(sharp_median / 150.0)
    brightness_score = clamp(1.0 - abs(brightness_mean - 128.0) / 128.0)
    contrast_score = clamp(contrast_median / 55.0)
    motion_score = score_motion(motion_median)
    coverage_score = clamp(coverage / 35.0)

    blur_bad = sum(1 for value in sharpness if value < 12.0) / len(sharpness)
    exposure_bad = sum(1 for value in brightness if value < 25.0 or value > 235.0) / len(brightness)
    jump_bad = sum(1 for value in diffs if value > 70.0) / max(1, len(diffs))
    penalty = 0.30 * blur_bad + 0.25 * exposure_bad + 0.25 * jump_bad

    score = (
        0.30 * sharp_score
        + 0.20 * brightness_score
        + 0.20 * contrast_score
        + 0.20 * motion_score
        + 0.10 * coverage_score
        - penalty
    )
    return {
        "start": round(start, 3),
        "end": round(end, 3),
        "score": round(float(score), 6),
        "sample_count": len(window),
        "sharpness_median": round(sharp_median, 3),
        "brightness_mean": round(brightness_mean, 3),
        "contrast_median": round(contrast_median, 3),
        "motion_median": round(motion_median, 3),
        "coverage_proxy": round(coverage, 3),
        "blur_bad_fraction": round(blur_bad, 3),
        "exposure_bad_fraction": round(exposure_bad, 3),
        "jump_bad_fraction": round(jump_bad, 3),
    }


def choose_window(samples: list[dict[str, float]], video_duration: float, duration: float, step: float) -> dict[str, Any]:
    if video_duration <= duration:
        result = score_window(samples, 0.0, max(video_duration, 0.001))
        result["start"] = 0.0
        result["end"] = round(video_duration, 3)
        return result
    max_start = max(0.0, video_duration - duration)
    starts = []
    current = 0.0
    while current <= max_start + 1e-6:
        starts.append(round(current, 3))
        current += max(0.1, step)
    if starts[-1] < max_start:
        starts.append(round(max_start, 3))
    candidates = [score_window(samples, start, duration) for start in starts]
    return max(candidates, key=lambda item: (item["score"], item["sample_count"]))


def crop_video(video: Path, output: Path, start: float, duration: float, codec: str, force: bool) -> dict[str, Any]:
    cv2 = import_cv2()
    if output.exists() and not force:
        raise FileExistsError(f"Output exists; pass --force to overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if not math.isfinite(fps) or fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    start_frame = max(0, int(round(start * fps)))
    frame_limit = max(1, int(round(duration * fps)))
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    fourcc = cv2.VideoWriter_fourcc(*codec[:4])
    writer = cv2.VideoWriter(str(output), fourcc, fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Unable to open output video for writing: {output}")
    written = 0
    while written < frame_limit:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(frame)
        written += 1
    writer.release()
    cap.release()
    return {
        "start_frame": start_frame,
        "frames_written": written,
        "fps": fps,
        "width": width,
        "height": height,
        "actual_duration": written / fps if fps > 0 else 0.0,
    }


def main() -> int:
    args = parse_args()
    video = args.video.expanduser().resolve()
    if not video.exists():
        raise FileNotFoundError(video)
    if args.duration <= 0:
        raise ValueError("--duration must be positive")
    output = (args.output or default_output_path(video, args.duration)).expanduser().resolve()
    report_path = (args.report or output.with_suffix(".json")).expanduser().resolve()
    if report_path.exists() and not args.force:
        raise FileExistsError(f"Report exists; pass --force to overwrite: {report_path}")

    meta = read_video_meta(video)
    scoring_duration = float(meta["duration"])
    if args.max_scan_seconds > 0:
        scoring_duration = min(scoring_duration, args.max_scan_seconds)

    samples = collect_samples(video, args.sample_fps, args.resize_width, args.max_scan_seconds)
    if args.start is not None:
        selected = score_window(samples, max(0.0, args.start), args.duration)
        selected["start"] = round(max(0.0, args.start), 3)
        selected["end"] = round(max(0.0, args.start) + args.duration, 3)
    else:
        selected = choose_window(samples, scoring_duration, args.duration, args.window_step)

    top_candidates = []
    if args.start is None and scoring_duration > args.duration:
        starts = [round(i * max(0.1, args.window_step), 3) for i in range(int(scoring_duration // max(0.1, args.window_step)) + 1)]
        candidates = [score_window(samples, start, args.duration) for start in starts if start + args.duration <= scoring_duration + 1e-6]
        top_candidates = sorted(candidates, key=lambda item: item["score"], reverse=True)[:8]

    crop_info = None
    if not args.dry_run:
        crop_info = crop_video(video, output, float(selected["start"]), args.duration, args.codec, args.force)

    report = {
        "input": str(video),
        "output": str(output),
        "video": meta,
        "scoring": {
            "sample_fps": args.sample_fps,
            "sample_count": len(samples),
            "window_duration": args.duration,
            "window_step": args.window_step,
            "resize_width": args.resize_width,
            "max_scan_seconds": args.max_scan_seconds,
        },
        "selected": selected,
        "top_candidates": top_candidates,
        "crop": crop_info,
        "dry_run": bool(args.dry_run),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Selected window: {selected['start']}s -> {selected['end']}s score={selected.get('score')}")
    if crop_info:
        print(f"Wrote video: {output} ({crop_info['frames_written']} frames)")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
