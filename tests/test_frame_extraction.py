from video2mesh.cli import compute_uniform_frame_extraction_plan


def test_uniform_frame_extraction_caps_dense_real_frames():
    plan = compute_uniform_frame_extraction_plan(
        source_frame_count=3600,
        fps=30.0,
        every=1,
        max_frames=200,
        start_sec=47.0,
        end_sec=56.0,
    )

    selected = plan["selected_source_indices"]
    assert plan["possible_frame_count"] == 270
    assert plan["planned_frame_count"] == 200
    assert plan["selection_strategy"] == "uniform_limited"
    assert selected[0] == 1410
    assert selected[-1] == 1679
    assert all(isinstance(frame_index, int) for frame_index in selected)
    assert selected == sorted(set(selected))


def test_uniform_frame_extraction_keeps_every_when_under_cap():
    plan = compute_uniform_frame_extraction_plan(
        source_frame_count=300,
        fps=30.0,
        every=2,
        max_frames=200,
        start_sec=1.0,
        duration_sec=3.0,
    )

    assert plan["possible_frame_count"] == 45
    assert plan["planned_frame_count"] == 45
    assert plan["selection_strategy"] == "interval"
    assert plan["selected_source_indices"][:3] == [30, 32, 34]
    assert plan["selected_source_indices"][-1] == 118
