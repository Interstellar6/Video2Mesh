from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare = load_tool("prepare_trellis_bedroom4_instances")
review = load_tool("review_trellis_instances_with_qwen")
materialize = load_tool("materialize_trellis_vlm_splits")
prompted = load_tool("prepare_trellis_prompted_instances")
references = load_tool("materialize_trellis_prompted_references")
geometry = load_tool("trellis_geometry_contracts")
runner = load_tool("run_trellis_gaussian_batch")


def test_projected_instance_seed_discards_unrelated_disconnected_component(tmp_path: Path) -> None:
    image_path = tmp_path / "frame.png"
    mask_path = tmp_path / "mask.png"
    Image.new("RGB", (100, 80), (110, 120, 130)).save(image_path)
    mask = np.zeros((80, 100), dtype=np.uint8)
    mask[14:64, 8:34] = 255
    mask[14:64, 64:92] = 255
    Image.fromarray(mask, mode="L").save(mask_path)
    candidate = prepare.Candidate(
        frame_id="frame",
        image_path=str(image_path),
        mask_path=str(mask_path),
        bbox_xyxy=[0, 0, 100, 80],
        bbox_width=100,
        bbox_height=80,
        bbox_area=8000,
        visible_points=3,
        mask_support_points=3,
        support_ratio=1.0,
        score=1.0,
    )
    points = np.asarray([[14.0, 20.0, 1.0], [21.0, 34.0, 1.0], [29.0, 53.0, 1.0]], dtype=np.float32)
    _, rgba, support, report = prepare.mask_for_candidate(
        candidate,
        points,
        np.eye(4, dtype=np.float32),
        {"fx": 1.0, "fy": 1.0, "cx": 0.0, "cy": 0.0, "w": 100.0, "h": 80.0},
        probability_threshold=0.6,
        min_component_support=0.01,
        support_seed_radius=2,
    )
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)
    assert alpha[30, 20] == 255
    assert alpha[30, 75] == 0
    assert np.asarray(support, dtype=np.uint8).sum() > 0
    assert report["retained_by"] == "projected_instance_seed"
    assert report["retained_component_labels"] == [1]


def test_window_vlm_contract_requires_split_decision_for_multiple_panes() -> None:
    request = prepare.build_vlm_request(
        "sam3_window_01",
        "window",
        "window",
        480,
        610,
        {"projected_instance_seed": {"seed_pixels": 200}},
    )
    prompt = request["prompt"]
    assert "split_required" in prompt
    assert "adjacent window pane or sash" in prompt
    assert "central mullion" in prompt
    assert request["input_contract"]["asset_type"] == "architectural window unit"


def test_split_required_vlm_spec_blocks_trellis_generation() -> None:
    request = prepare.build_vlm_request(
        "sam3_window_01",
        "window",
        "window",
        480,
        610,
        {"projected_instance_seed": {"seed_pixels": 200}},
    )
    spec, errors = review.validate_spec(
        {
            "decision": "split_required",
            "reason": "Two separately framed panes are visible.",
            "observed_same_category_instance_count": 2,
            "asset_units": [
                {"unit_id": "left", "normalized_bbox_xyxy": [0, 0, 490, 1000]},
                {"unit_id": "right", "normalized_bbox_xyxy": [510, 0, 1000, 1000]},
            ],
            "generation_contract": {"one_asset_per_unit": True, "needs_new_instance_masks": True},
        },
        request,
    )
    assert not errors
    assert spec["decision"] == "split_required"
    assert spec["generation_allowed"] is False


def test_physx_voxel_sequence_is_not_treated_as_a_vlm_instance_review() -> None:
    output = " ".join(f"{index}-{index + 4}" for index in range(0, 160, 5))
    assert review.looks_like_voxel_sequence(output)
    assert review.extract_json(output)[0] is None


def test_vlm_boxes_materialize_disjoint_window_inputs(tmp_path: Path) -> None:
    rgb_path = tmp_path / "window_rgb.png"
    rgba_path = tmp_path / "window_rgba.png"
    support_path = tmp_path / "window_support.png"
    rgb = Image.new("RGB", (100, 60), (150, 160, 170))
    alpha = np.zeros((60, 100), dtype=np.uint8)
    alpha[8:54, 5:43] = 255
    alpha[8:54, 57:95] = 255
    rgba = rgb.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha, mode="L"))
    rgb.save(rgb_path)
    rgba.save(rgba_path)
    Image.fromarray(alpha, mode="L").save(support_path)
    parent = {
        "object_id": "sam3_window_01",
        "category": "window",
        "rgb_path": str(rgb_path),
        "rgba_path": str(rgba_path),
        "projected_support_path": str(support_path),
    }
    spec = {
        "input_contract": prepare.instance_contract("window"),
        "reason": "Two framed panes.",
        "asset_units": [
            {"unit_id": "left_pane", "normalized_bbox_xyxy": [0, 0, 480, 1000]},
            {"unit_id": "right_pane", "normalized_bbox_xyxy": [520, 0, 1000, 1000]},
        ],
    }
    children, child_specs = materialize.materialize_split(
        parent,
        spec,
        tmp_path / "input",
        tmp_path / "specs",
        padding_pixels=2,
        min_alpha_pixels=50,
    )
    assert len(children) == 2
    assert len(child_specs) == 2
    child_alpha = [np.asarray(Image.open(item["rgba_path"]).getchannel("A"), dtype=np.uint8) for item in children]
    assert sum(int((item > 0).sum()) for item in child_alpha) == int((alpha > 0).sum())
    assert all(item["bbox_width"] > 0 and item["bbox_height"] > 0 for item in children)


def test_prompted_masks_resolve_shared_mullion_without_duplicate_alpha() -> None:
    left = np.zeros((40, 80), dtype=bool)
    right = np.zeros((40, 80), dtype=bool)
    left[5:35, 8:46] = True
    right[5:35, 34:72] = True
    resolved, overlap_pixels = prompted.resolve_mask_overlaps(
        [left.copy(), right.copy()],
        [(6, 3, 48, 37), (32, 3, 74, 37)],
    )
    assert overlap_pixels == 360
    assert not np.any(resolved[0] & resolved[1])
    assert int((resolved[0] | resolved[1]).sum()) == int((left | right).sum())


def test_prompted_reference_is_recorded_and_selected(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    reference = tmp_path / "reference.png"
    Image.new("RGBA", (40, 60), (120, 130, 140, 255)).save(source)
    edited = Image.new("RGBA", (80, 100), (255, 0, 255, 0))
    edited.paste(Image.new("RGBA", (30, 70), (220, 225, 230, 255)), (25, 15))
    edited.save(reference)
    item = {"object_id": "window_01", "category": "window", "rgba_path": str(source)}
    config = {
        "provider": "test-editor",
        "geometry_contract": {"kind": "planar", "max_thickness_to_short_side_ratio": 0.1},
        "objects": {"window_01": {"prompt": "Create one thin planar window."}},
    }
    materialized = references.materialize_reference(
        item,
        config,
        reference,
        tmp_path / "output",
        None,
        min_alpha_pixels=100,
        max_alpha_ratio=0.9,
    )
    selected, provenance, error = runner.generation_input(materialized, True, True)
    assert error is None
    assert selected and selected.is_file()
    assert provenance and provenance["provider"] == "test-editor"
    assert materialized["geometry_contract"]["kind"] == "planar"


def test_prompted_reference_contract_blocks_missing_reference() -> None:
    selected, provenance, error = runner.generation_input(
        {"object_id": "window_01", "rgba_path": "original.png"},
        use_prompted_reference=True,
        require_prompted_reference=True,
    )
    assert selected is None
    assert provenance is None
    assert error == "missing_prompted_reference"


def test_planar_geometry_gate_accepts_thin_plane_and_rejects_box() -> None:
    yy, xx = np.meshgrid(np.linspace(-1.0, 1.0, 50), np.linspace(-0.6, 0.6, 40), indexing="ij")
    thin_points = np.column_stack([xx.ravel(), yy.ravel(), np.zeros(xx.size)])
    thick_points = np.concatenate(
        [
            thin_points + np.asarray([0.0, 0.0, -0.35]),
            thin_points + np.asarray([0.0, 0.0, 0.35]),
        ],
        axis=0,
    )
    opacity = np.ones(len(thin_points), dtype=np.float32)
    contract = {
        "kind": "planar",
        "max_thickness_to_short_side_ratio": 0.1,
        "opacity_threshold": 0.5,
        "quantile_low": 0.01,
        "quantile_high": 0.99,
    }
    thin = geometry.evaluate_geometry_contract(thin_points, opacity, contract)
    thick = geometry.evaluate_geometry_contract(thick_points, np.ones(len(thick_points), dtype=np.float32), contract)
    assert thin["status"] == "passed"
    assert thin["thickness_to_short_side_ratio"] < 0.01
    assert thick["status"] == "failed"
    assert thick["thickness_to_short_side_ratio"] > 0.1
