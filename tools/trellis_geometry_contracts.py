#!/usr/bin/env python3
"""Geometry metrics and acceptance contracts for generated TRELLIS assets."""

from __future__ import annotations

from typing import Any

import numpy as np


def planar_geometry_report(
    points: np.ndarray,
    opacity: np.ndarray,
    contract: dict[str, Any],
) -> dict[str, Any]:
    points = np.asarray(points, dtype=np.float64)
    opacity = np.asarray(opacity, dtype=np.float64).reshape(-1)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) != len(opacity):
        raise ValueError("points must be Nx3 and opacity must have N values")
    opacity_threshold = float(contract.get("opacity_threshold", 0.5))
    quantile_low = float(contract.get("quantile_low", 0.01))
    quantile_high = float(contract.get("quantile_high", 0.99))
    max_ratio = float(contract.get("max_thickness_to_short_side_ratio", 0.1))
    if not (0.0 <= opacity_threshold <= 1.0):
        raise ValueError("opacity_threshold must be in [0, 1]")
    if not (0.0 <= quantile_low < quantile_high <= 1.0):
        raise ValueError("geometry quantiles must satisfy 0 <= low < high <= 1")
    if max_ratio <= 0.0:
        raise ValueError("max_thickness_to_short_side_ratio must be positive")
    finite = np.isfinite(points).all(axis=1) & np.isfinite(opacity)
    selected = finite & (opacity >= opacity_threshold)
    selected_points = points[selected]
    if len(selected_points) < 8:
        return {
            "kind": "planar",
            "status": "failed",
            "reason": "insufficient_high_opacity_points",
            "selected_point_count": int(len(selected_points)),
            "opacity_threshold": opacity_threshold,
            "max_thickness_to_short_side_ratio": max_ratio,
        }
    center = np.median(selected_points, axis=0)
    centered = selected_points - center
    covariance = centered.T @ centered / max(len(centered) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    projected = centered @ eigenvectors[:, order]
    lower = np.quantile(projected, quantile_low, axis=0)
    upper = np.quantile(projected, quantile_high, axis=0)
    extents = np.sort(upper - lower)[::-1]
    short_side = float(extents[1])
    thickness = float(extents[2])
    ratio = thickness / max(short_side, 1e-12)
    passed = bool(np.isfinite(ratio) and ratio <= max_ratio)
    return {
        "kind": "planar",
        "status": "passed" if passed else "failed",
        "reason": "within_planar_thickness_limit" if passed else "excessive_planar_thickness",
        "selected_point_count": int(len(selected_points)),
        "opacity_threshold": opacity_threshold,
        "quantile_low": quantile_low,
        "quantile_high": quantile_high,
        "pca_extents": [float(value) for value in extents],
        "thickness": thickness,
        "short_side": short_side,
        "thickness_to_short_side_ratio": ratio,
        "max_thickness_to_short_side_ratio": max_ratio,
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
    return {"kind": kind, "status": "failed", "reason": "unsupported_geometry_contract"}
