#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path


DOC_ROOT = Path("/Users/zhangyuxiang/Desktop/worksplace/ChallengeCup/docs/challengecup-agent-system")
PUBLIC_ROOT = Path(__file__).resolve().parent / "_public" / "challengecup-agent-system"
ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "uploaded"

SITE = {
    "route": "challengecup-agent-system",
    "title": "ChallengeCup Agent System",
    "brand": "ChallengeCup",
    "mark": "CC",
    "subtitle": "Agent System",
    "description": "ChallengeCup 多模态模型协同自主智能体系统的赛题分析、技术调研、进度和项目使用文档。",
    "space": "/challengecup-agent-system 项目空间",
    "researchRoot": "docs/challengecup-agent-system/research-catalog/",
    "catalogCategory": "调研目录",
    "catalogStages": [
        {
            "key": "target-detection",
            "title": "目标检测",
            "directory": "research-catalog/target-detection/",
            "summary": "YOLOv8、FPN、多尺度输入、SAHI 和 tiny soldier 检测瓶颈。",
            "image": "assets/uploaded/challengecup-yolov8/yolov8-pipeline.svg",
            "tags": ["YOLOv8", "FPN", "SAHI"],
        },
        {
            "key": "scene-cognition",
            "title": "场景认知",
            "directory": "research-catalog/scene-cognition/",
            "summary": "Places365、EfficientNet、MobileCLIP 和 air/sea/urban/forest 场景标签。",
            "image": "assets/uploaded/challengecup-places365-resnet50/scene-cognition-pipeline.svg",
            "tags": ["Places365", "EfficientNet", "MobileCLIP"],
        },
        {
            "key": "task-decision-postprocess",
            "title": "任务决策与后处理",
            "directory": "research-catalog/task-decision-postprocess/",
            "summary": "场景先验、precision policy、WBF、Model Soups、candidate gate。",
            "image": "assets/uploaded/challengecup-model-soups/model-soups-pipeline.svg",
            "tags": ["Policy", "WBF", "Model Soups"],
        },
        {
            "key": "data-engine-semisupervised",
            "title": "数据闭环与半监督",
            "directory": "research-catalog/data-engine-semisupervised/",
            "summary": "Teacher-Student、Grounding DINO、Copy-Paste、错例审计和数据回流。",
            "image": "assets/uploaded/challengecup-soft-teacher/teacher-student-pipeline.svg",
            "tags": ["Teacher", "Pseudo Label", "Copy-Paste"],
        },
        {
            "key": "deployment",
            "title": "端侧部署",
            "directory": "research-catalog/deployment/",
            "summary": "YOLO 权重导出 ONNX，经 CANN/ATC 转换为 Ascend 310B 可运行 OM。",
            "image": "assets/uploaded/challengecup-ascend-cann-atc/ascend-deploy-pipeline.svg",
            "tags": ["Ascend", "CANN", "ATC"],
        },
    ],
    "readingPaths": [
        {
            "title": "先理解比赛",
            "summary": "从任务和数据集约束入手，确认为什么当前路线以 R1 小目标检测和端侧部署为核心。",
            "tags": ["赛题分析目录", "R1", "数据集分析"],
            "query": "赛题",
        },
        {
            "title": "按环节看调研",
            "summary": "调研目录先进入目标检测、场景认知等子目录，再阅读每个模型/项目单项文档。",
            "tags": ["调研目录", "目标检测", "场景认知"],
            "query": "YOLOv8",
        },
        {
            "title": "复现实验结果",
            "summary": "查看当前进度、最强候选、被拒绝路线和本地复验命令。",
            "tags": ["进度目录", "mAP50-95", "uv"],
            "query": "current",
        },
    ],
}

ROOT_ORDER = [
    "README.md",
    "contest-analysis/README.md",
    "research-catalog/README.md",
    "progress/README.md",
    "project-docs/README.md",
]

CATEGORY_ORDER = ["总目录", "赛题分析目录", "调研目录", "进度目录", "项目使用文档目录"]
ASSET_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"}
STAGE_BY_KEY = {str(stage["key"]): stage for stage in SITE["catalogStages"]}


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, object] = {}
    current_key = ""
    for raw in parts[1].splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            meta.setdefault(current_key, [])
            assert isinstance(meta[current_key], list)
            meta[current_key].append(line[4:].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            meta[current_key] = value if value else []
    return meta, parts[2]


def slugify(value: str) -> str:
    slug = re.sub(r"\s+", "-", value.strip().lower())
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "", slug)
    return slug or "section"


def headings(markdown: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if not match:
            continue
        text = re.sub(r"[#`*_]", "", match.group(2)).strip()
        result.append({"level": str(len(match.group(1))), "text": text, "slug": slugify(text)})
    return result


def reading_minutes(markdown: str) -> int:
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", markdown))
    latin_words = len(re.findall(r"[A-Za-z0-9_+-]+", markdown))
    return max(1, round((chinese_chars + latin_words) / 450))


def upload_dir(doc_id: str) -> Path:
    return ASSET_ROOT / doc_id


def rewrite_asset_links(markdown: str, source_path: Path, doc_id: str) -> str:
    def repl(match: re.Match[str]) -> str:
        alt, href, title = match.group(1), match.group(2).strip(), match.group(3) or ""
        if re.match(r"^[a-z]+://", href) or href.startswith("#") or href.startswith("data:"):
            return match.group(0)
        src = (source_path.parent / href).resolve()
        if not src.exists() or src.suffix.lower() not in ASSET_EXTS:
            return match.group(0)
        target_dir = upload_dir(doc_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / src.name
        shutil.copy2(src, target)
        public_href = f"assets/uploaded/{doc_id}/{src.name}"
        return f"![{alt}]({public_href}{title})"

    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(\s+\"[^\"]+\")?\)", repl, markdown)


def split_href(href: str) -> tuple[str, str]:
    for marker in ("#", "?"):
        if marker in href:
            index = href.index(marker)
            return href[:index], href[index:]
    return href, ""


def rewrite_doc_links(markdown: str, source_path: Path, path_to_doc_id: dict[Path, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        label, href, title = match.group(1), match.group(2).strip(), match.group(3) or ""
        if re.match(r"^[a-z]+:", href) or href.startswith("#") or href.startswith("/"):
            return match.group(0)
        href_path, _suffix = split_href(href)
        target_path = (source_path.parent / href_path).resolve()
        if target_path.suffix.lower() not in {".md", ".markdown"}:
            return match.group(0)
        target_id = path_to_doc_id.get(target_path)
        if not target_id:
            return match.group(0)
        return f"[{label}](#/doc/{target_id}{title})"

    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(\s+\"[^\"]+\")?\)", repl, markdown)


def source_rel(path: Path) -> str:
    return f"docs/challengecup-agent-system/{path.relative_to(DOC_ROOT).as_posix()}"


def infer_research_stage(path: Path) -> str:
    rel = path.relative_to(DOC_ROOT).as_posix()
    prefix = "research-catalog/"
    if not rel.startswith(prefix):
        return ""
    parts = rel.split("/")
    if len(parts) < 3:
        return ""
    stage = parts[1]
    return stage if stage in STAGE_BY_KEY else ""


def infer_research_doc_role(path: Path, stage: str) -> str:
    rel = path.relative_to(DOC_ROOT).as_posix()
    if rel == "research-catalog/README.md":
        return "root"
    if stage and path.name == "README.md":
        return "overview"
    if stage:
        return "item"
    return ""


def normalize_tags(tags: object, category: str) -> list[str]:
    result = [str(tag).strip() for tag in tags if str(tag).strip()] if isinstance(tags, list) else []
    if category and category not in result:
        result.append(category)
    return result


def build_doc(path: Path, path_to_doc_id: dict[Path, str]) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    doc_id = str(meta.get("id") or slugify(path.stem))
    category = str(meta.get("category") or "Drafts")
    research_stage = str(meta.get("research_stage") or infer_research_stage(path))
    research_stage_title = str(
        meta.get("research_stage_title")
        or STAGE_BY_KEY.get(research_stage, {}).get("title", "")
    )
    research_doc_role = str(meta.get("research_doc_role") or infer_research_doc_role(path, research_stage))
    body = rewrite_asset_links(body, path, doc_id)
    body = rewrite_doc_links(body, path, path_to_doc_id)
    return {
        "id": doc_id,
        "title": str(meta.get("title") or path.stem),
        "category": category,
        "research_stage": research_stage,
        "research_stage_title": research_stage_title,
        "research_doc_role": research_doc_role,
        "visibility": str(meta.get("visibility") or "public"),
        "summary": str(meta.get("summary") or ""),
        "source_path": source_rel(path),
        "source_kind": "builtin",
        "updated": dt.date.today().isoformat(),
        "tags": normalize_tags(meta.get("tags", []), category),
        "headings": headings(body),
        "reading_minutes": reading_minutes(body),
        "body": body,
    }


def doc_sort_key(path: Path) -> tuple[int, str]:
    rel = path.relative_to(DOC_ROOT).as_posix()
    if rel in ROOT_ORDER:
        return (ROOT_ORDER.index(rel), rel)
    return (len(ROOT_ORDER), rel)


def main() -> None:
    md_paths = sorted(DOC_ROOT.rglob("*.md"), key=doc_sort_key)
    path_to_doc_id: dict[Path, str] = {}
    for path in md_paths:
        raw = path.read_text(encoding="utf-8")
        meta, _body = parse_frontmatter(raw)
        path_to_doc_id[path.resolve()] = str(meta.get("id") or slugify(path.stem))
    docs = [build_doc(path, path_to_doc_id) for path in md_paths]
    seen: set[str] = set()
    unique_docs = []
    for doc in docs:
        doc_id = str(doc["id"])
        if doc_id in seen:
            continue
        seen.add(doc_id)
        unique_docs.append(doc)
    categories = [
        {"name": name, "count": sum(1 for doc in unique_docs if doc["category"] == name)}
        for name in CATEGORY_ORDER
        if any(doc["category"] == name for doc in unique_docs)
    ]
    data = {
        "generatedAt": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "site": SITE,
        "docs": unique_docs,
        "categories": categories,
    }
    PUBLIC_ROOT.mkdir(parents=True, exist_ok=True)
    site_data = PUBLIC_ROOT / "site-data.js"
    site_data.write_text(
        "window.V2M_BLOG_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )

    public_assets = PUBLIC_ROOT / "assets" / "uploaded"
    public_assets.mkdir(parents=True, exist_ok=True)
    for item in ASSET_ROOT.glob("challengecup-*"):
        target = public_assets / item.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(item, target)
    print(f"wrote {site_data}")
    print(f"docs={len(unique_docs)} categories={len(categories)}")


if __name__ == "__main__":
    main()
