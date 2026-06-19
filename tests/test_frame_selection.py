from video2mesh.cli import (
    SVLGAUSSIAN_DEFAULT_OFFSETS,
    SVLGAUSSIAN_DEFAULT_RANDOM_WINDOW,
    SVLGAUSSIAN_DEFAULT_TOP_K,
    SVLGAUSSIAN_DEFAULT_VISIBILITY_WINDOW,
    select_svlgaussian_style_frames,
    svlgaussian_expected_frame_count,
    svlgaussian_offset_coverage,
)


def candidate(frame_id: int, score: float) -> dict:
    return {
        "frame_id": f"{frame_id:06d}",
        "frame_numeric_id": frame_id,
        "score": score,
        "quality_score": score,
        "matching_feature_available": False,
    }


def test_svlgaussian_default_protocol_selects_anchor_offsets_and_random_window():
    ranked = [
        candidate(100, 100.0),
        candidate(105, 90.0),
        candidate(110, 80.0),
        candidate(112, 70.0),
        candidate(130, 60.0),
    ]

    selected = select_svlgaussian_style_frames(
        ranked,
        SVLGAUSSIAN_DEFAULT_TOP_K,
        SVLGAUSSIAN_DEFAULT_OFFSETS,
        SVLGAUSSIAN_DEFAULT_RANDOM_WINDOW,
        SVLGAUSSIAN_DEFAULT_VISIBILITY_WINDOW,
        seed=7,
        similarity_penalty=250.0,
        temporal_bonus=2.0,
        min_frame_gap=3,
    )

    reasons = [item["selection_reason"] for item in selected]
    coverage = svlgaussian_offset_coverage(
        selected,
        SVLGAUSSIAN_DEFAULT_OFFSETS,
        SVLGAUSSIAN_DEFAULT_VISIBILITY_WINDOW,
    )

    assert svlgaussian_expected_frame_count(SVLGAUSSIAN_DEFAULT_OFFSETS, SVLGAUSSIAN_DEFAULT_RANDOM_WINDOW) == 4
    assert len(selected) == 4
    assert reasons[0] == "svlgaussian_anchor_offset_coverage"
    assert "svlgaussian_offset_5" in reasons
    assert "svlgaussian_offset_10" in reasons
    assert f"svlgaussian_random_window_{SVLGAUSSIAN_DEFAULT_RANDOM_WINDOW}" in reasons
    assert coverage["missing_offsets"] == []
