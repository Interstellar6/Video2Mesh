#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import mimetypes
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs-blog"
ASSETS = SITE / "assets"
CONTENT = SITE / "content"
PUBLIC_BUILD = SITE / "_public"

PINNED_DOCS = [
    "docs/video2mesh/research-catalog/README.md",
    "docs/video2mesh/project-docs/overview.md",
    "docs/video2mesh/project-docs/project-intro.md",
    "docs/video2mesh/project-docs/pipeline.md",
    "docs/video2mesh/project-docs/how-to-run.md",
    "docs/video2mesh/progress/overview.md",
    "docs/video2mesh/progress/p0-p1-priority.md",
    "docs/video2mesh/progress/weekly-2026-07-03.md",
]

ROOT_DOC_EXCLUDE = {"README.md"}

CATEGORY_RULES = [
    ("Game Scenes", ["game", "interactive", "游戏", "交互"]),
    ("Surveys", ["survey", "调研", "方案"]),
    ("Pipeline", ["pipeline", "readme", "流水线", "项目说明"]),
    ("Simulation", ["simulator", "unity", "mujoco", "isaac", "仿真"]),
    ("Runs", ["runbook", "showcase", "remote", "milscene", "运行", "展示", "远端"]),
    ("Notes", ["notes", "frame", "匹配", "说明"]),
]

RESEARCH_STAGE_DEFS = [
    ("input-pose-pointcloud", "输入、位姿与点云"),
    ("visual-3dgs", "视觉重建 / 3DGS"),
    ("mesh-reconstruction", "Mesh 重建"),
    ("pointcloud-completion", "点云/背景补全"),
    ("object-mesh-completion", "物体 Mesh 补全"),
    ("semantic-scene-graph", "语义与 Scene Graph"),
    ("collider-physics-proxy", "Collider 与物理代理"),
    ("object-simulation", "物体仿真"),
    ("industrial-pipelines", "工业资产管线"),
    ("experiments", "本项目实验"),
]

RESEARCH_STAGE_TITLES = dict(RESEARCH_STAGE_DEFS)


@dataclass
class Doc:
    id: str
    title: str
    category: str
    research_stage: str
    research_stage_title: str
    research_doc_role: str
    visibility: str
    summary: str
    source_path: str
    source_kind: str
    updated: str
    tags: list[str]
    body: str
    headings: list[dict[str, str]]
    reading_minutes: int


def slugify(value: str, fallback: str = "doc") -> str:
    text = value.strip().lower()
    text = re.sub(r"[\s_/\\]+", "-", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff.-]+", "", text)
    text = text.strip(".-")
    return text or fallback


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(raw) or {}
    return (data if isinstance(data, dict) else {}), body


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return strip_markdown(match.group(1)).strip()
    return fallback


def strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    return value


def infer_category(path: Path, title: str, meta: dict[str, Any]) -> str:
    if meta.get("category"):
        return str(meta["category"])
    haystack = f"{path.name} {title}".lower()
    for category, needles in CATEGORY_RULES:
        if any(needle.lower() in haystack for needle in needles):
            return category
    return "Notes"


def infer_research_stage(path: Path) -> tuple[str, str, str]:
    relative = str(path.relative_to(ROOT)).replace("\\", "/")
    prefix = "docs/video2mesh/research-catalog/"
    if not relative.startswith(prefix):
        return "", "", ""
    tail = relative[len(prefix):]
    if tail == "README.md":
        return "research-catalog", "调研目录总览", "root"
    stage_key = tail.split("/", 1)[0]
    stage_title = RESEARCH_STAGE_TITLES.get(stage_key, "")
    if not stage_title:
        return "", "", ""
    role = "overview" if tail.endswith("/overview.md") else "item"
    return stage_key, stage_title, role


def extract_summary(body: str, meta: dict[str, Any]) -> str:
    if meta.get("summary"):
        return str(meta["summary"]).strip()
    lines: list[str] = []
    in_code = False
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line or line.startswith("#") or line.startswith("|") or line.startswith("!") or line.startswith("---"):
            continue
        clean = strip_markdown(line)
        if clean:
            lines.append(clean)
        if len(" ".join(lines)) > 150:
            break
    summary = " ".join(lines).strip()
    return summary[:220] + ("..." if len(summary) > 220 else "")


def extract_headings(body: str) -> list[dict[str, str]]:
    headings: list[dict[str, str]] = []
    for line in body.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if not match:
            continue
        text = strip_markdown(match.group(2)).strip()
        headings.append({"level": str(len(match.group(1))), "text": text, "slug": slugify(text)})
    return headings[:24]


def normalize_tags(meta: dict[str, Any], title: str, category: str) -> list[str]:
    tags: list[str] = []
    raw = meta.get("tags")
    if isinstance(raw, list):
        tags.extend(str(item) for item in raw)
    elif isinstance(raw, str):
        tags.extend(part.strip() for part in raw.split(","))
    for key in ["3DGS", "Scene Graph", "Unity", "Game", "COLMAP", "SAM2", "VGGT"]:
        if key.lower() in title.lower():
            tags.append(key)
    tags.append(category)
    unique: list[str] = []
    seen = set()
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean.lower() not in seen:
            unique.append(clean)
            seen.add(clean.lower())
    return unique[:8]


def normalize_visibility(meta: dict[str, Any], path: Path) -> str:
    raw = str(meta.get("visibility") or "").strip().lower()
    if raw in {"public", "private"}:
        return raw
    relative = str(path.relative_to(ROOT)).replace("\\", "/")
    if "/research-catalog/" in relative or relative.endswith("/research-catalog/README.md"):
        return "public"
    if "/project-docs/" in relative or "/progress/" in relative:
        return "public"
    return "private"


def copy_local_assets(doc_path: Path, doc_id: str, body: str) -> str:
    def split_image_target(raw_url: str) -> tuple[str, str]:
        match = re.match(r'^(\S+)(\s+"[^"]*")\s*$', raw_url.strip())
        if match:
            return match.group(1), match.group(2)
        return raw_url.strip(), ""

    def copy_one(raw_url: str) -> str | None:
        url, _title = split_image_target(raw_url)
        if re.match(r"^(https?:|data:|#)", url):
            return None
        url_path = url.split("#", 1)[0].split("?", 1)[0]
        src = (doc_path.parent / url_path).resolve()
        if not src.exists() or not src.is_file():
            return None
        dst_dir = ASSETS / "uploaded" / doc_id
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
        return f"assets/uploaded/{doc_id}/{src.name}"

    def replace(match: re.Match[str]) -> str:
        alt, raw_url = match.group(1), match.group(2).strip()
        _url, title = split_image_target(raw_url)
        copied = copy_one(raw_url)
        return f"![{alt}]({copied}{title})" if copied else match.group(0)

    def replace_obsidian(match: re.Match[str]) -> str:
        raw = match.group(1).strip()
        if not re.search(r"\.(png|jpe?g|gif|webp|svg)$", raw, re.IGNORECASE):
            return match.group(0)
        copied = copy_one(raw)
        return f"![{Path(raw).stem}]({copied})" if copied else match.group(0)

    body = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, body)
    body = re.sub(r"!\[\[([^\]]+)\]\]", replace_obsidian, body)
    return body


def load_doc(path: Path, source_kind: str, used_ids: set[str], copy_assets: bool = True) -> Doc:
    raw = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(raw)
    title = str(meta.get("title") or extract_title(body, path.stem.replace("_", " "))).strip()
    doc_id = slugify(str(meta.get("id") or path.stem), "doc")
    base_id = doc_id
    index = 2
    while doc_id in used_ids:
        doc_id = f"{base_id}-{index}"
        index += 1
    used_ids.add(doc_id)
    category = infer_category(path, title, meta)
    research_stage, research_stage_title, research_doc_role = infer_research_stage(path)
    visibility = normalize_visibility(meta, path)
    if copy_assets and visibility == "public":
        body = copy_local_assets(path, doc_id, body)
    words = re.findall(r"[\w\u4e00-\u9fff]+", strip_markdown(body))
    updated = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    return Doc(
        id=doc_id,
        title=title,
        category=category,
        research_stage=research_stage,
        research_stage_title=research_stage_title,
        research_doc_role=research_doc_role,
        visibility=visibility,
        summary=extract_summary(body, meta),
        source_path=str(path.relative_to(ROOT)),
        source_kind=source_kind,
        updated=updated,
        tags=normalize_tags(meta, title, category),
        body=body,
        headings=extract_headings(body),
        reading_minutes=max(1, round(len(words) / 420)),
    )


def collect_docs(copy_assets: bool = True) -> list[Doc]:
    used_ids: set[str] = set()
    docs: list[Doc] = []
    seen_docs: set[Path] = set()
    for name in PINNED_DOCS:
        path = ROOT / name
        if path.exists():
            seen_docs.add(path.resolve())
            docs.append(load_doc(path, "builtin", used_ids, copy_assets=copy_assets))
    for path in sorted(ROOT.glob("*.md")):
        if path.name in ROOT_DOC_EXCLUDE or path.resolve() in seen_docs:
            continue
        docs.append(load_doc(path, "builtin", used_ids, copy_assets=copy_assets))
    docs_root = ROOT / "docs" / "video2mesh"
    for path in sorted(docs_root.rglob("*.md")):
        if path.resolve() in seen_docs:
            continue
        docs.append(load_doc(path, "builtin", used_ids, copy_assets=copy_assets))
    for path in sorted(CONTENT.rglob("*.md")):
        docs.append(load_doc(path, "content", used_ids, copy_assets=copy_assets))
    return docs


def write_site_data(docs: list[Doc]) -> None:
    public_docs = [doc for doc in docs if doc.visibility == "public"]
    payload = {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "docs": [doc.__dict__ for doc in public_docs],
        "categories": sorted({doc.category for doc in public_docs}),
    }
    text = "window.V2M_BLOG_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    (SITE / "site-data.js").write_text(text, encoding="utf-8")


def write_placeholder_asset() -> None:
    img = ASSETS / "v2m-docs-mark.svg"
    if img.exists():
        return
    img.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420">
  <rect width="800" height="420" fill="#f5f7f4"/>
  <path d="M70 314 C190 160 270 248 360 122 C440 14 560 120 722 56 L722 420 L70 420 Z" fill="#d7ebe6"/>
  <path d="M98 286 L252 210 L358 250 L516 142 L704 208" fill="none" stroke="#0d6b65" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="252" cy="210" r="18" fill="#ffb84d"/>
  <circle cx="516" cy="142" r="18" fill="#ffb84d"/>
  <g fill="#203230" font-family="Arial, sans-serif">
    <text x="86" y="86" font-size="42" font-weight="700">Video2Mesh</text>
    <text x="88" y="128" font-size="24">Field Notes</text>
  </g>
</svg>
""",
        encoding="utf-8",
    )


def write_custom_domain() -> None:
    (SITE / "CNAME").write_text("relumeow.top\n", encoding="utf-8")


def build_public_site() -> None:
    if PUBLIC_BUILD.exists():
        shutil.rmtree(PUBLIC_BUILD)
    PUBLIC_BUILD.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(
        ".env",
        ".env.*",
        "_public",
        "admin",
        "admin-domain-worker.js",
        "api_server.py",
        "build_site.py",
        "codex_queue.py",
        "demos",
        "run_api.sh",
        "runtime",
        "wrangler.admin.toml",
        "bedroom_4_cli30k_graphdeco_clean_iteration30000.ply",
        "bedroom_4_scene_3dgs_repaired_supersplat.ply",
        "chunks",
    )
    video2mesh_build = PUBLIC_BUILD / "video2mesh"
    shutil.copytree(SITE, video2mesh_build, ignore=ignore)
    admin_src = SITE / "admin"
    admin_dst = PUBLIC_BUILD / "admin"
    if admin_src.exists():
        shutil.copytree(admin_src, admin_dst)
        for name in ("styles.css", "theme.js"):
            src = SITE / name
            if src.exists():
                shutil.copy2(src, PUBLIC_BUILD / name)
    (PUBLIC_BUILD / "index.html").write_text(
        """<!doctype html>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=/video2mesh/">
<title>Video2Mesh</title>
<a href="/video2mesh/">进入 Video2Mesh 文档站</a>
""",
        encoding="utf-8",
    )
    (PUBLIC_BUILD / "CNAME").write_text("relumeow.top\n", encoding="utf-8")


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    CONTENT.mkdir(parents=True, exist_ok=True)
    generated_uploads = ASSETS / "uploaded"
    if generated_uploads.exists():
        shutil.rmtree(generated_uploads)
    docs = collect_docs()
    write_site_data(docs)
    write_placeholder_asset()
    write_custom_domain()
    build_public_site()
    public_count = sum(1 for doc in docs if doc.visibility == "public")
    private_count = len(docs) - public_count
    print(f"Built docs-blog with {public_count} public document(s), {private_count} private document(s).")
    for doc in docs:
        print(f"- [{doc.visibility}] [{doc.category}] {doc.title} ({doc.source_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
