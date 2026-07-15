from __future__ import annotations

import importlib.util
import json
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
auto_plan = load_tool("plan_trellis_auto_completion")
assembler = load_tool("assemble_trellis_auto_completion_bundle")
sanitizer = load_tool("sanitize_trellis_gaussians")
planar_enforcer = load_tool("enforce_trellis_planar_contracts")


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


def test_auto_completion_evidence_tiers_and_prompt_are_fail_closed() -> None:
    thresholds = {
        "high_min_short_side": 144,
        "high_min_alpha_pixels": 8000,
        "high_min_support_ratio": 0.75,
        "medium_min_short_side": 80,
        "medium_min_alpha_pixels": 2000,
        "medium_min_support_ratio": 0.45,
    }
    high, high_report = auto_plan.evidence_tier(
        {"bbox_width": 220, "bbox_height": 180, "alpha_pixels": 12000, "support_ratio": 0.9},
        thresholds,
    )
    low, low_report = auto_plan.evidence_tier(
        {"bbox_width": 43, "bbox_height": 43, "alpha_pixels": 500, "support_ratio": 0.8},
        thresholds,
    )
    forced_low, forced_low_report = auto_plan.evidence_tier(
        {
            "bbox_width": 300,
            "bbox_height": 300,
            "alpha_pixels": 30000,
            "support_ratio": 0.95,
            "low_detail_input": True,
        },
        thresholds,
    )
    prompt = auto_plan.completion_prompt(
        {
            "subject": "potted plant",
            "view": "Show the full object.",
            "completion": "Complete one pot and its stems.",
            "avoid": "wall, furniture, second plant",
        },
        "#ff00ff",
    )
    assert high == "high"
    assert high_report["short_side"] == 180
    assert low == "low"
    assert low_report["alpha_pixels"] == 500
    assert forced_low == "low"
    assert forced_low_report["low_detail_input"] is True
    assert auto_plan.completion_fidelity("prompt_complete", low) == "category_proxy_from_low_detail_evidence"
    assert "exactly one complete independent potted plant" in prompt
    assert "Do not redesign visible evidence" in prompt
    assert "#ff00ff" in prompt


def test_auto_completion_prompt_split_materializes_child_jobs(tmp_path: Path, monkeypatch) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    Image.new("RGBA", (80, 120), (220, 225, 230, 255)).save(source_dir / "window_02_rgba.png")
    input_manifest = tmp_path / "input.json"
    input_manifest.write_text(
        '{"prepared":[{"object_id":"window_02","name":"window 2","category":"window",'
        '"bbox_width":200,"bbox_height":300,"alpha_pixels":20000,"support_ratio":0.9,'
        '"rgba_path":"remote.png"}]}',
        encoding="utf-8",
    )
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "provider": {"name": "test-editor", "quality": "medium", "background": "#ff00ff"},
                "categories": {
                    "window": {
                        "strategy": "prompt_complete",
                        "subject": "window sash",
                        "completion": "Complete one sash.",
                        "geometry_contract": {"kind": "planar", "max_thickness_to_short_side_ratio": 0.1},
                    }
                },
                "objects": {
                    "window_02": {
                        "strategy": "prompt_split",
                        "units": [
                            {"unit_id": "left", "subject": "left window sash"},
                            {"unit_id": "right", "subject": "right window sash"},
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    output_root = tmp_path / "output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "plan_trellis_auto_completion.py",
            "--input-manifest",
            str(input_manifest),
            "--policy-config",
            str(policy),
            "--source-image-dir",
            str(source_dir),
            "--output-root",
            str(output_root),
        ],
    )
    assert auto_plan.main() == 0
    jobs = json.loads((output_root / "plan" / "image_edit_jobs.json").read_text(encoding="utf-8"))
    generation = json.loads((output_root / "plan" / "prompt_input_manifest.json").read_text(encoding="utf-8"))
    plan = json.loads((output_root / "plan" / "completion_plan.json").read_text(encoding="utf-8"))
    assert [job["object_id"] for job in jobs["jobs"]] == ["window_02_left", "window_02_right"]
    assert [item["object_id"] for item in generation["prepared"]] == ["window_02_left", "window_02_right"]
    assert plan["items"][0]["replacement_ids"] == ["window_02_left", "window_02_right"]


def test_bounded_volume_gate_rejects_collapsed_furniture() -> None:
    grid = np.linspace(-0.5, 0.5, 12)
    xx, yy, zz = np.meshgrid(grid, grid, grid, indexing="ij")
    volume = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    collapsed = volume.copy()
    collapsed[:, 2] *= 0.03
    contract = {
        "kind": "bounded_volume",
        "min_thickness_to_short_side_ratio": 0.2,
        "max_long_side_to_short_side_ratio": 4.5,
    }
    passed = geometry.evaluate_geometry_contract(volume, np.ones(len(volume)), contract)
    failed = geometry.evaluate_geometry_contract(collapsed, np.ones(len(collapsed)), contract)
    assert passed["status"] == "passed"
    assert failed["status"] == "failed"
    assert failed["reason"] == "collapsed_volume"


def test_upright_volume_gate_requires_depth_and_supported_end() -> None:
    rng = np.random.default_rng(20260714)
    pot = np.column_stack(
        [
            rng.uniform(-0.3, 0.3, 900),
            rng.uniform(-1.0, -0.55, 900),
            rng.uniform(-0.25, 0.25, 900),
        ]
    )
    foliage = np.column_stack(
        [
            rng.normal(0.0, 0.42, 1800),
            rng.uniform(-0.55, 1.0, 1800),
            rng.normal(0.0, 0.35, 1800),
        ]
    )
    upright = np.concatenate([pot, foliage], axis=0)
    collapsed = upright.copy()
    collapsed[:, 2] *= 0.02
    contract = {
        "kind": "upright_volume",
        "vertical_axis": "y",
        "min_height_to_max_horizontal_ratio": 0.55,
        "max_height_to_max_horizontal_ratio": 4.5,
        "min_horizontal_depth_ratio": 0.16,
        "end_band_fraction": 0.18,
        "min_supported_end_point_fraction": 0.025,
        "min_supported_end_span_ratio": 0.12,
    }
    passed = geometry.evaluate_geometry_contract(upright, np.ones(len(upright)), contract)
    failed = geometry.evaluate_geometry_contract(collapsed, np.ones(len(collapsed)), contract)
    assert passed["status"] == "passed"
    assert passed["end_support"]["selected"] == "lower"
    assert failed["status"] == "failed"
    assert failed["reason"] == "collapsed_horizontal_depth"


def test_bundle_assembler_copies_only_qa_passed_asset(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    final_dir = tmp_path / "final"
    source_dir.mkdir()
    source = source_dir / "nightstand_01_trellis_gaussian.ply"
    source.write_bytes(b"ply\nmock\n")
    qa = {
        "nightstand_01": {
            "status": "passed",
            "file_status": "passed",
            "vertex_count": 1234,
            "geometry": {"status": "passed", "kind": "bounded_volume"},
        }
    }
    result = assembler.accepted_asset(
        "nightstand_01",
        "nightstand_01",
        "nightstand",
        "prompt_completed_reference",
        "prompt_completed_from_partial_evidence",
        source_dir,
        qa,
        final_dir,
    )
    assert result["status"] == "accepted"
    assert Path(result["final_ply"]).read_bytes() == source.read_bytes()
    blocked = assembler.accepted_asset(
        "missing",
        "missing",
        "nightstand",
        "prompt_completed_reference",
        "prompt_completed_from_partial_evidence",
        source_dir,
        qa,
        final_dir,
    )
    assert blocked["status"] == "blocked"


def test_gaussian_sanitizer_drops_rare_nonfinite_vertices() -> None:
    vertices = np.zeros(
        100,
        dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"), ("opacity", "f4")],
    )
    vertices[17]["opacity"] = np.inf
    finite, fields = sanitizer.finite_vertex_mask(vertices)
    assert int(finite.sum()) == 99
    assert fields == {"opacity": 1}


def test_planar_covariance_transform_preserves_valid_quaternions() -> None:
    scales = np.asarray([[0.0, -0.3, -0.7], [-0.2, -0.4, -0.8]], dtype=np.float64)
    quaternions = np.asarray([[1.0, 0.0, 0.0, 0.0], [0.9238795, 0.0, 0.3826834, 0.0]])
    transform = np.diag([1.0, 1.0, 0.25])
    output_scales, output_quaternions = planar_enforcer.transform_gaussian_covariances(
        scales, quaternions, transform, chunk_size=1
    )
    assert np.isfinite(output_scales).all()
    assert np.isfinite(output_quaternions).all()
    assert np.allclose(np.linalg.norm(output_quaternions, axis=1), 1.0, atol=1e-6)
    assert (output_scales.min(axis=1) < scales.min(axis=1)).all()
    source_rotations = planar_enforcer.quaternion_to_matrix(quaternions)
    source_covariances = np.einsum(
        "nij,nj,nkj->nik", source_rotations, np.exp(2.0 * scales), source_rotations
    )
    expected_covariances = np.einsum(
        "ij,njk,lk->nil", transform, source_covariances, transform
    )
    output_rotations = planar_enforcer.quaternion_to_matrix(output_quaternions)
    reconstructed_covariances = np.einsum(
        "nij,nj,nkj->nik", output_rotations, np.exp(2.0 * output_scales), output_rotations
    )
    assert np.allclose(reconstructed_covariances, expected_covariances, atol=1e-6)
