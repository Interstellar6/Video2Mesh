#!/usr/bin/env python3
"""Snapshot public browser-delivered code for a set of web entrypoints."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ASSET_RE = re.compile(
    r"""(?:
        (?:src|href)=["']([^"']+)["']|
        import\(["']([^"']+)["']\)|
        ["']([^"']+\.(?:js|mjs|css|wasm|json|map|svg|png|jpg|jpeg|webp|gif|mp4|ogg|mp3|ttf|woff2?|glb|gltf|spz|sog|splat|ply|gz|rad))(?:\?[^"']*)?["']
    )""",
    re.IGNORECASE | re.VERBOSE,
)


TEXT_TYPES = (
    "text/",
    "application/javascript",
    "application/x-javascript",
    "application/json",
    "application/manifest+json",
    "application/wasm",
)


def is_probably_text(content_type: str, path: Path) -> bool:
    lower = content_type.lower()
    if lower.startswith(TEXT_TYPES):
        return True
    return path.suffix.lower() in {".html", ".js", ".mjs", ".css", ".json", ".svg", ".txt", ".map"}


def safe_local_path(root: Path, url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc.replace(":", "_") or "local"
    raw_path = parsed.path
    if raw_path.endswith("/"):
        raw_path += "index.html"
    if not raw_path or raw_path == "/":
        raw_path = "/index.html"
    if parsed.query:
        suffix = "_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", parsed.query)[:80]
        raw_path += suffix
    parts = [part for part in raw_path.split("/") if part not in {"", ".", ".."}]
    return root / host / Path(*parts)


def fetch(url: str, timeout: int) -> tuple[bytes, str, str]:
    req = Request(url, headers={"User-Agent": "Video2Mesh-public-code-snapshot/1.0"})
    with urlopen(req, timeout=timeout) as response:
        data = response.read()
        content_type = response.headers.get("content-type", "")
        final_url = response.geturl()
    return data, content_type, final_url


def asset_candidates(text: str, base_url: str) -> Iterable[str]:
    for match in ASSET_RE.finditer(text):
        raw = next((group for group in match.groups() if group), "")
        if not raw or raw.startswith(("data:", "blob:", "mailto:", "tel:", "#")):
            continue
        yield urljoin(base_url, raw)


def same_site_or_allowed(url: str, allowed_hosts: set[str]) -> bool:
    host = urlparse(url).netloc
    return host in allowed_hosts


def snapshot(entrypoints: list[str], output: Path, max_depth: int, timeout: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    allowed_hosts = {urlparse(url).netloc for url in entrypoints}
    queue: deque[tuple[str, int]] = deque((url, 0) for url in entrypoints)
    seen: set[str] = set()
    records: list[dict] = []

    while queue:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        record = {"url": url, "depth": depth, "status": "pending"}
        try:
            data, content_type, final_url = fetch(url, timeout)
            local = safe_local_path(output, final_url)
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
            record.update(
                {
                    "status": "ok",
                    "final_url": final_url,
                    "content_type": content_type,
                    "bytes": len(data),
                    "local_path": str(local.relative_to(output)),
                }
            )

            if depth < max_depth and is_probably_text(content_type, local):
                try:
                    text = data.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""
                for candidate in asset_candidates(text, final_url):
                    if same_site_or_allowed(candidate, allowed_hosts) and candidate not in seen:
                        queue.append((candidate, depth + 1))
        except Exception as exc:
            record.update({"status": "error", "error": str(exc)})
        records.append(record)
        print(f"{record['status']:>5} depth={depth} {url}", flush=True)

    manifest = {
        "entrypoints": entrypoints,
        "allowed_hosts": sorted(allowed_hosts),
        "max_depth": max_depth,
        "records": records,
    }
    (output / "snapshot_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("entrypoints", nargs="+")
    args = parser.parse_args(argv)
    snapshot(args.entrypoints, args.output, args.max_depth, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
