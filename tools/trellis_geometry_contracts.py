#!/usr/bin/env python3
"""Geometry metrics and acceptance contracts for generated TRELLIS assets."""

from __future__ import annotations

from typing import Any

import numpy as np


AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def robust_geometry_stats(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any],
) -> tuple[np.ndarray | None, dict[str, Any]]:
    points = np.asarray(points, dtype=np.float64)
    opacity = np.asarray(opacity, dtype=np.float64).reshape(-1)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) != len(opacity):
        raise ValueError("points must be Nx3 and opacity must have N values")
    opacity_threshold = float(contract.get("opacity_threshold", 0.5))
    quantile_low = float(contract.get("quantile_low", 0.01))
    quantile_high = float(contract.get("quantile_high", 0.99))
    minimum_points = int(contract.get("minimum_selected_points", 8))
    if not (0.0 <= opacity_threshold <= 1.0):
        raise ValueError("opacity_threshold must be in [0, 1]")
    if not (0.0 <= quantile_low < quantile_high <= 1.0):
        raise ValueError("geometry quantiles must satisfy 0 <= low < high <= 1")
    if minimum_points < 3:
        raise ValueError("minimum_selected_points must be at least 3")
    finite = np.isfinite(points).all(axis=1) & np.isfinite(opacity)
    selected_points = points[finite & (opacity >= opacity_threshold)]
    common: dict[str, Any] = {
        "selected_point_count": int(len(selected_points)),
        "opacity_threshold": opacity_threshold,
        "quantile_low": quantile_low,
        "quantile_high": quantile_high,
    }
    if len(selected_points) < minimum_points:
        common["minimum_selected_points"] = minimum_points
        return None, common
    center = np.median(selected_points, axis=0)
    centered = selected_points - center
    covariance = centered.T @ centered / max(len(centered) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    projected = centered @ eigenvectors[:, order]
    pca_lower = np.quantile(projected, quantile_low, axis=0)
    pca_upper = np.quantile(projected, quantile_high, axis=0)
    pca_extents = np.sort(pca_upper - pca_lower)[::-1]
    axis_lower = np.quantile(selected_points, quantile_low, axis=0)
    axis_upper = np.quantile(selected_points, quantile_high, axis=0)
    axis_extents = axis_upper - axis_lower
    common.update({
        "pca_extents": [float(value) for value in pca_extents],
        "axis_extents": {
            axis: float(axis_extents[index])
            for axis, index in AXIS_INDEX.items()
        },
        "_axis_lower": axis_lower,
        "_axis_upper": axis_upper,
        "_axis_extents_array": axis_extents,
    })
    return selected_points, common


def public_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in stats.items() if not key.startswith("_")}


def planar_geometry_report(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any],
) -> dict[str, Any]:
    max_ratio = float(contract.get("max_thickness_to_short_side_ratio", 0.1))
    if max_ratio <= 0.0:
        raise ValueError("max_thickness_to_short_side_ratio must be positive")
    selected_points, stats = robust_geometry_stats(points, opacity, contract)
    if selected_points is None:
        return {
            "kind": "planar",
            "status": "failed",
            "reason": "insufficient_high_opacity_points",
            **public_stats(stats),
            "max_thickness_to_short_side_ratio": max_ratio,
        }
    extents = np.asarray(stats["pca_extents"], dtype=np.float64)
    short_side = float(extents[1])
    thickness = float(extents[2])
    ratio = thickness / max(short_side, 1e-12)
    passed = bool(np.isfinite(ratio) and ratio <= max_ratio)
    return {
        "kind": "planar",
        "status": "passed" if passed else "failed",
        "reason": "within_planar_thickness_limit" if passed else "excessive_planar_thickness",
        **public_stats(stats),
        "thickness": thickness,
        "short_side": short_side,
        "thickness_to_short_side_ratio": ratio,
        "max_thickness_to_short_side_ratio": max_ratio,
    }


def bounded_volume_geometry_report(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any],
) -> dict[str, Any]:
    min_thickness_ratio = float(contract.get("min_thickness_to_short_side_ratio", 0.15))
    max_aspect_ratio = float(contract.get("max_long_side_to_short_side_ratio", 6.0))
    if not (0.0 < min_thickness_ratio <= 1.0):
        raise ValueError("min_thickness_to_short_side_ratio must be in (0, 1]")
    if max_aspect_ratio < 1.0:
        raise ValueError("max_long_side_to_short_side_ratio must be at least 1")
    selected_points, stats = robust_geometry_stats(points, opacity, contract)
    if selected_points is None:
        return {
            "kind": "bounded_volume",
            "status": "failed",
            "reason": "insufficient_high_opacity_points",
            **public_stats(stats),
        }
    extents = np.asarray(stats["pca_extents"], dtype=np.float64)
    thickness_ratio = float(extents[2] / max(extents[1], 1e-12))
    long_to_shortest_ratio = float(extents[0] / max(extents[2], 1e-12))
    thick_enough = np.isfinite(thickness_ratio) and thickness_ratio >= min_thickness_ratio
    bounded_aspect = np.isfinite(long_to_shortest_ratio) and long_to_shortest_ratio <= max_aspect_ratio
    passed = bool(thick_enough and bounded_aspect)
    if not thick_enough:
        reason = "collapsed_volume"
    elif not bounded_aspect:
        reason = "excessive_volume_aspect_ratio"
    else:
        reason = "within_bounded_volume_limits"
    return {
        "kind": "bounded_volume",
        "status": "passed" if passed else "failed",
        "reason": reason,
        **public_stats(stats),
        "thickness_to_short_side_ratio": thickness_ratio,
        "min_thickness_to_short_side_ratio": min_thickness_ratio,
        "long_side_to_shortest_side_ratio": long_to_shortest_ratio,
        "max_long_side_to_short_side_ratio": max_aspect_ratio,
    }


def end_support_report(
    selected_points: np.ndarray,
    vertical_index: int,
    horizontal_indices: list[int],
    lower: np.ndarray,
    upper: np.ndarray,
    extents: np.ndarray,
    band_fraction: float,
    end: str,
) -> dict[str, Any]:
    vertical_extent = max(float(extents[vertical_index]), 1e-12)
    if end == "lower":
        mask = selected_points[:, vertical_index] <= lower[vertical_index] + band_fraction * vertical_extent
    else:
        mask = selected_points[:, vertical_index] >= upper[vertical_index] - band_fraction * vertical_extent
    end_points = selected_points[mask]
    fraction = float(len(end_points) / max(len(selected_points), 1))
    span_ratios: list[float] = []
    if len(end_points) >= 3:
        for index in horizontal_indices:
            end_low, end_high = np.quantile(end_points[:, index], (0.05, 0.95))
            span_ratios.append(float((end_high - end_low) / max(extents[index], 1e-12)))
    else:
        span_ratios = [0.0, 0.0]
    return {
        "end": end,
        "point_count": int(len(end_points)),
        "point_fraction": fraction,
        "horizontal_span_ratios": span_ratios,
        "minimum_horizontal_span_ratio": float(min(span_ratios)),
        "support_score": float(fraction * min(span_ratios)),
    }


def upright_volume_geometry_report(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any],
) -> dict[str, Any]:
    vertical_axis = str(contract.get("vertical_axis") or "y")
    if vertical_axis not in AXIS_INDEX:
        raise ValueError(f"Unsupported vertical_axis: {vertical_axis}")
    min_height_ratio = float(contract.get("min_height_to_max_horizontal_ratio", 0.5))
    max_height_ratio = float(contract.get("max_height_to_max_horizontal_ratio", 5.0))
    min_depth_ratio = float(contract.get("min_horizontal_depth_ratio", 0.12))
    band_fraction = float(contract.get("end_band_fraction", 0.18))
    min_end_fraction = float(contract.get("min_supported_end_point_fraction", 0.02))
    min_end_span = float(contract.get("min_supported_end_span_ratio", 0.1))
    required_supported_end = str(contract.get("supported_end") or "lower")
    if not (0.0 < min_height_ratio <= max_height_ratio):
        raise ValueError("upright height ratio bounds are invalid")
    if not (0.0 < min_depth_ratio <= 1.0):
        raise ValueError("min_horizontal_depth_ratio must be in (0, 1]")
    if not (0.0 < band_fraction < 0.5):
        raise ValueError("end_band_fraction must be in (0, 0.5)")
    if required_supported_end not in {"lower", "upper", "either"}:
        raise ValueError("supported_end must be lower, upper, or either")
    selected_points, stats = robust_geometry_stats(points, opacity, contract)
    if selected_points is None:
        return {
            "kind": "upright_volume",
            "status": "failed",
            "reason": "insufficient_high_opacity_points",
            **public_stats(stats),
        }
    vertical_index = AXIS_INDEX[vertical_axis]
    horizontal_indices = [index for index in range(3) if index != vertical_index]
    extents = np.asarray(stats["_axis_extents_array"], dtype=np.float64)
    lower = np.asarray(stats["_axis_lower"], dtype=np.float64)
    upper = np.asarray(stats["_axis_upper"], dtype=np.float64)
    height = float(extents[vertical_index])
    horizontal = np.asarray([extents[index] for index in horizontal_indices], dtype=np.float64)
    max_horizontal = float(horizontal.max())
    min_horizontal = float(horizontal.min())
    height_ratio = height / max(max_horizontal, 1e-12)
    depth_ratio = min_horizontal / max(max_horizontal, 1e-12)
    lower_support = end_support_report(
        selected_points, vertical_index, horizontal_indices, lower, upper, extents, band_fraction, "lower"
    )
    upper_support = end_support_report(
        selected_points, vertical_index, horizontal_indices, lower, upper, extents, band_fraction, "upper"
    )
    if required_supported_end == "either":
        supported_end = max((lower_support, upper_support), key=lambda value: value["support_score"])
    else:
        supported_end = lower_support if required_supported_end == "lower" else upper_support
    height_ok = np.isfinite(height_ratio) and min_height_ratio <= height_ratio <= max_height_ratio
    depth_ok = np.isfinite(depth_ratio) and depth_ratio >= min_depth_ratio
    support_ok = (
        supported_end["point_fraction"] >= min_end_fraction
        and supported_end["minimum_horizontal_span_ratio"] >= min_end_span
    )
    passed = bool(height_ok and depth_ok and support_ok)
    if not height_ok:
        reason = "implausible_upright_height_ratio"
    elif not depth_ok:
        reason = "collapsed_horizontal_depth"
    elif not support_ok:
        reason = "insufficient_supported_end"
    else:
        reason = "within_upright_volume_limits"
    return {
        "kind": "upright_volume",
        "status": "passed" if passed else "failed",
        "reason": reason,
        **public_stats(stats),
        "vertical_axis": vertical_axis,
        "height_to_max_horizontal_ratio": float(height_ratio),
        "min_height_to_max_horizontal_ratio": min_height_ratio,
        "max_height_to_max_horizontal_ratio": max_height_ratio,
        "horizontal_depth_ratio": float(depth_ratio),
        "min_horizontal_depth_ratio": min_depth_ratio,
        "end_band_fraction": band_fraction,
        "end_support": {
            "lower": lower_support,
            "upper": upper_support,
            "required": required_supported_end,
            "selected": supported_end["end"],
        },
        "min_supported_end_point_fraction": min_end_fraction,
        "min_supported_end_span_ratio": min_end_span,
    }


def evaluate_geometry_contract(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any] | None,
) -> dict[str, Any]:
    if contract is None:
        return {"kind": None, "status": "not_applicable", "reason": "no_geometry_contract"}
    kind = str(contract.get("kind") or "")
    if kind == "planar":
        return planar_geometry_report(points, opacity, contract)
    if kind == "bounded_volume":
        return bounded_volume_geometry_report(points, opacity, contract)
    if kind == "upright_volume":
        return upright_volume_geometry_report(points, opacity, contract)
    return {"kind": kind, "status": "failed", "reason": "unsupported_geometry_contract"}
