#!/usr/bin/env python3
"""Patch GraphDECO gaussian-splatting with Video2Mesh shape regularization.

The patch is intentionally idempotent. It adds optional training-time Gaussian
scale/elongation splitting without changing GraphDECO defaults.
"""

from __future__ import annotations

import argparse
from pathlib import Path


TRAIN_MARKER = "# BEGIN VIDEO2MESH_SHAPE_REGULARIZER_TRAIN"
MODEL_MARKER = "# BEGIN VIDEO2MESH_SHAPE_REGULARIZER_MODEL"
ARGS_MARKER = "# BEGIN VIDEO2MESH_SHAPE_REGULARIZER_ARGS"


TRAIN_HELPER = f'''
{TRAIN_MARKER}
def maybe_run_v2m_shape_regularizer(gaussians, opt, scene, iteration):
    if not bool(getattr(opt, "v2m_shape_regularizer", False)):
        return
    interval = int(getattr(opt, "v2m_shape_interval", 0) or 0)
    if interval <= 0 or iteration % interval != 0:
        return
    start_iter = int(getattr(opt, "v2m_shape_from_iter", -1))
    until_iter = int(getattr(opt, "v2m_shape_until_iter", -1))
    if start_iter < 0:
        start_iter = int(getattr(opt, "densify_from_iter", 0))
    if until_iter < 0:
        until_iter = int(getattr(opt, "densify_until_iter", getattr(opt, "iterations", iteration)))
    if iteration < start_iter or iteration > until_iter:
        return

    max_scale = float(getattr(opt, "v2m_shape_max_scale", 0.0) or 0.0)
    max_scale_ratio = float(getattr(opt, "v2m_shape_max_scale_ratio", 0.0) or 0.0)
    if max_scale_ratio > 0:
        max_scale = max(max_scale, max_scale_ratio * float(scene.cameras_extent))

    report = gaussians.v2m_shape_regularize_and_split(
        max_scale=max_scale,
        max_elongation=float(getattr(opt, "v2m_shape_max_elongation", 0.0) or 0.0),
        split_children=int(getattr(opt, "v2m_shape_split_children", 2) or 2),
        max_points=int(getattr(opt, "v2m_shape_max_points_per_interval", 20000) or 0),
        split_scale_divisor=float(getattr(opt, "v2m_shape_split_scale_divisor", 1.6) or 1.6),
    )
    if int(report.get("selected_count", 0) or 0) <= 0:
        return
    report["iteration"] = int(iteration)
    report["scene_extent"] = float(scene.cameras_extent)
    report_path = os.path.join(scene.model_path, "v2m_shape_regularizer_report.jsonl")
    with open(report_path, "a", encoding="utf-8") as report_file:
        report_file.write(json.dumps(report, sort_keys=True) + "\\n")
    print(
        "\\n[ITER {{}}] Video2Mesh shape regularizer split {{}} Gaussian(s), "
        "added {{}}, total {{}}. Report: {{}}".format(
            iteration,
            report.get("selected_count"),
            report.get("new_count"),
            report.get("final_count"),
            report_path,
        )
    )
{TRAIN_MARKER.replace("BEGIN", "END")}
'''


MODEL_METHOD = f'''
    {MODEL_MARKER}
    def v2m_shape_regularize_and_split(
        self,
        max_scale: float = 0.0,
        max_elongation: float = 0.0,
        split_children: int = 2,
        max_points: int = 20000,
        split_scale_divisor: float = 1.6,
    ):
        n_init_points = int(self.get_xyz.shape[0])
        report = {{
            "enabled": True,
            "initial_count": n_init_points,
            "selected_count": 0,
            "new_count": 0,
            "final_count": n_init_points,
            "max_scale": float(max_scale),
            "max_elongation": float(max_elongation),
            "split_children": int(split_children),
            "max_points": int(max_points),
            "split_scale_divisor": float(split_scale_divisor),
        }}
        if n_init_points <= 0 or (float(max_scale) <= 0 and float(max_elongation) <= 0):
            report["reason"] = "disabled_or_empty"
            return report

        scales = self.get_scaling
        max_axis = torch.max(scales, dim=1).values
        min_axis = torch.clamp(torch.min(scales, dim=1).values, min=1e-12)
        elongation = max_axis / min_axis
        oversized = torch.zeros_like(max_axis, dtype=torch.bool)
        elongated = torch.zeros_like(max_axis, dtype=torch.bool)
        score = torch.zeros_like(max_axis)
        if float(max_scale) > 0:
            oversized = max_axis > float(max_scale)
            score = torch.maximum(score, max_axis / float(max_scale))
        if float(max_elongation) > 0:
            elongated = elongation > float(max_elongation)
            score = torch.maximum(score, elongation / float(max_elongation))
        selected_pts_mask = torch.logical_or(oversized, elongated)
        selected_count = int(selected_pts_mask.sum().item())
        report.update(
            {{
                "candidate_count": selected_count,
                "oversized_count": int(oversized.sum().item()),
                "elongated_count": int(elongated.sum().item()),
                "max_scale_observed": float(max_axis.max().item()) if n_init_points else 0.0,
                "max_elongation_observed": float(elongation.max().item()) if n_init_points else 0.0,
            }}
        )
        if selected_count <= 0:
            report["reason"] = "no_gaussians_over_threshold"
            return report

        if int(max_points) > 0 and selected_count > int(max_points):
            selected_indices = torch.nonzero(selected_pts_mask, as_tuple=False).squeeze(1)
            topk = torch.topk(score[selected_indices], k=int(max_points), largest=True).indices
            limited_mask = torch.zeros_like(selected_pts_mask)
            limited_mask[selected_indices[topk]] = True
            selected_pts_mask = limited_mask
            selected_count = int(selected_pts_mask.sum().item())
            report["limited_by_max_points"] = True
        else:
            report["limited_by_max_points"] = False

        split_children = max(2, int(split_children))
        split_scale_divisor = max(float(split_scale_divisor), 1e-6)
        selected_scales = scales[selected_pts_mask]
        selected_xyz = self.get_xyz[selected_pts_mask]
        selected_rotation = self._rotation[selected_pts_mask]
        selected_count = int(selected_scales.shape[0])
        longest_axis = torch.argmax(selected_scales, dim=1)

        steps = torch.linspace(-0.5, 0.5, split_children, device=selected_scales.device, dtype=selected_scales.dtype)
        local_offsets = torch.zeros((selected_count, split_children, 3), device=selected_scales.device, dtype=selected_scales.dtype)
        rows = torch.arange(selected_count, device=selected_scales.device)[:, None]
        cols = torch.arange(split_children, device=selected_scales.device)[None, :]
        local_offsets[rows, cols, longest_axis[:, None]] = selected_scales.gather(1, longest_axis[:, None]) * steps[None, :]
        local_offsets = local_offsets.reshape(selected_count * split_children, 3)

        rots = build_rotation(selected_rotation).repeat_interleave(split_children, dim=0)
        new_xyz = torch.bmm(rots, local_offsets.unsqueeze(-1)).squeeze(-1) + selected_xyz.repeat_interleave(split_children, dim=0)

        target_scales = selected_scales.clone()
        if float(max_scale) > 0:
            target_scales = torch.minimum(target_scales, torch.full_like(target_scales, float(max_scale)))
        if float(max_elongation) > 0:
            target_min = torch.clamp(torch.min(target_scales, dim=1).values, min=1e-12)
            target_scales = torch.minimum(target_scales, (target_min * float(max_elongation)).unsqueeze(1))
        long_axis_target = torch.minimum(
            target_scales.gather(1, longest_axis[:, None]),
            selected_scales.gather(1, longest_axis[:, None]) / split_scale_divisor,
        )
        target_scales = target_scales.scatter(1, longest_axis[:, None], long_axis_target)
        target_scales = torch.clamp(target_scales, min=1e-8)
        new_scaling = self.scaling_inverse_activation(target_scales).repeat_interleave(split_children, dim=0)
        new_rotation = selected_rotation.repeat_interleave(split_children, dim=0)
        new_features_dc = self._features_dc[selected_pts_mask].repeat_interleave(split_children, dim=0)
        new_features_rest = self._features_rest[selected_pts_mask].repeat_interleave(split_children, dim=0)
        new_opacity = self._opacity[selected_pts_mask].repeat_interleave(split_children, dim=0)

        old_tmp_radii = getattr(self, "tmp_radii", None)
        if old_tmp_radii is None or old_tmp_radii.shape[0] != n_init_points:
            self.tmp_radii = torch.zeros((n_init_points), device="cuda")
        new_tmp_radii = self.tmp_radii[selected_pts_mask].repeat_interleave(split_children)

        self.densification_postfix(new_xyz, new_features_dc, new_features_rest, new_opacity, new_scaling, new_rotation, new_tmp_radii)
        prune_filter = torch.cat(
            (
                selected_pts_mask,
                torch.zeros(selected_count * split_children, device="cuda", dtype=torch.bool),
            )
        )
        self.prune_points(prune_filter)
        self.tmp_radii = None
        torch.cuda.empty_cache()

        report["selected_count"] = selected_count
        report["new_count"] = int(selected_count * split_children)
        report["final_count"] = int(self.get_xyz.shape[0])
        return report
    {MODEL_MARKER.replace("BEGIN", "END")}
'''


ARGS_SNIPPET = f'''        {ARGS_MARKER}
        self.v2m_shape_regularizer = False
        self.v2m_shape_interval = 300
        self.v2m_shape_from_iter = -1
        self.v2m_shape_until_iter = -1
        self.v2m_shape_max_scale = 0.0
        self.v2m_shape_max_scale_ratio = 0.0
        self.v2m_shape_max_elongation = 0.0
        self.v2m_shape_split_children = 2
        self.v2m_shape_max_points_per_interval = 20000
        self.v2m_shape_split_scale_divisor = 1.6
        {ARGS_MARKER.replace("BEGIN", "END")}
'''


def patch_file(path: Path, transform) -> bool:
    text = path.read_text(encoding="utf-8")
    patched = transform(text)
    if patched == text:
        return False
    path.write_text(patched, encoding="utf-8")
    return True


def replace_marked_block(text: str, begin_marker: str, block: str) -> tuple[str, bool]:
    start = text.find(begin_marker)
    if start < 0:
        return text, False
    end_marker = begin_marker.replace("BEGIN", "END")
    end = text.find(end_marker, start)
    if end < 0:
        return text, False
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end < 0 else line_end + 1
    replacement = block.strip("\n") + "\n"
    return text[:line_start] + replacement + text[line_end:], True


def patch_train(text: str) -> str:
    if "import json" not in text:
        text = text.replace("import os\n", "import os\nimport json\n", 1)
    text, replaced = replace_marked_block(text, TRAIN_MARKER, TRAIN_HELPER)
    if not replaced:
        text = text.replace("\ndef training(dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from):\n", TRAIN_HELPER + "\ndef training(dataset, opt, pipe, testing_iterations, saving_iterations, checkpoint_iterations, checkpoint, debug_from):\n", 1)
    call_line = "            maybe_run_v2m_shape_regularizer(gaussians, opt, scene, iteration)\n"
    if call_line not in text:
        text = text.replace("            # Optimizer step\n", call_line + "\n            # Optimizer step\n", 1)
    return text


def patch_model(text: str) -> str:
    text, replaced = replace_marked_block(text, MODEL_MARKER, MODEL_METHOD)
    if replaced:
        return text
    return text.replace("    def add_densification_stats(self, viewspace_point_tensor, update_filter):\n", MODEL_METHOD + "\n    def add_densification_stats(self, viewspace_point_tensor, update_filter):\n", 1)


def patch_arguments(text: str) -> str:
    text, replaced = replace_marked_block(text, ARGS_MARKER, ARGS_SNIPPET)
    if replaced:
        return text
    return text.replace("        self.depth_l1_weight_init = 1.0\n", ARGS_SNIPPET + "        self.depth_l1_weight_init = 1.0\n", 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graphdeco_root", type=Path)
    args = parser.parse_args()
    root = args.graphdeco_root.resolve()
    files = {
        "train.py": root / "train.py",
        "scene/gaussian_model.py": root / "scene" / "gaussian_model.py",
        "arguments/__init__.py": root / "arguments" / "__init__.py",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing GraphDECO files: " + ", ".join(missing))
    changed = {
        "train.py": patch_file(files["train.py"], patch_train),
        "scene/gaussian_model.py": patch_file(files["scene/gaussian_model.py"], patch_model),
        "arguments/__init__.py": patch_file(files["arguments/__init__.py"], patch_arguments),
    }
    for name, did_change in changed.items():
        print(f"{name}: {'patched' if did_change else 'already up to date'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
