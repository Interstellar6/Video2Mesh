from video2mesh.cli import aggregate_object_level_detections


def _aggregate(detections):
    return aggregate_object_level_detections(
        detections,
        width=1280,
        height=720,
        max_objects=20,
        min_area_ratio=0.001,
        max_area_ratio=0.8,
        min_width=8,
        min_height=8,
        nms_iou=0.65,
        containment_overlap=0.9,
        containment_area_ratio=1.8,
        granularity="object",
        min_parent_area_ratio=0.03,
        instance_iou=0.18,
        instance_center_distance=0.75,
        max_instances_per_label=4,
        merge_bed_parts=True,
        object_prefix="gdino_object",
    )


def test_bed_part_detections_merge_into_one_object_prompt():
    detections = [
        {"frame_id": "000010", "label": "bed", "bbox": [330, 150, 950, 620], "score": 0.70},
        {"frame_id": "000010", "label": "blanket", "bbox": [350, 275, 930, 500], "score": 0.82},
        {"frame_id": "000010", "label": "headboard", "bbox": [350, 145, 630, 360], "score": 0.77},
        {"frame_id": "000050", "label": "pillow", "bbox": [410, 220, 620, 355], "score": 0.76},
    ]

    prompts, skipped = _aggregate(detections)

    bed_prompts = [prompt for prompt in prompts if prompt["name"] == "bed"]
    assert len(bed_prompts) == 1
    assert bed_prompts[0]["detection_count"] == 4
    assert bed_prompts[0]["bbox"] == [350, 275, 930, 500]
    assert not skipped


def test_spatially_distinct_windows_remain_separate_instances():
    detections = [
        {"frame_id": "000010", "label": "window", "bbox": [675, 45, 890, 355], "score": 0.90},
        {"frame_id": "000010", "label": "window", "bbox": [990, 0, 1275, 365], "score": 0.88},
        {"frame_id": "000050", "label": "window", "bbox": [690, 30, 905, 350], "score": 0.82},
    ]

    prompts, _skipped = _aggregate(detections)

    window_prompts = [prompt for prompt in prompts if prompt["name"] == "window"]
    assert len(window_prompts) == 2
    counts = sorted(prompt["detection_count"] for prompt in window_prompts)
    assert counts == [1, 2]
