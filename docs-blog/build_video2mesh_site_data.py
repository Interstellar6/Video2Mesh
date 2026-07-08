#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path


DOC_ROOT = Path("/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh/docs/video2mesh")
PUBLIC_ROOT = Path(__file__).resolve().parent / "_public" / "video2mesh"
ASSET_ROOT = Path(__file__).resolve().parent / "assets" / "uploaded"

SITE = {
    "route": "video2mesh",
    "title": "Video2Mesh Field Notes",
    "brand": "Video2Mesh",
    "mark": "V2M",
    "subtitle": "Field Notes",
    "description": "Video2Mesh 项目文档、调研和运行手册的静态博客网站。",
    "space": "/video2mesh 项目空间",
    "researchRoot": "docs/video2mesh/research-catalog/",
    "catalogCategory": "调研目录",
    "catalogStages": [
        {
            "key": "input-pose-pointcloud",
            "title": "输入、位姿与点云",
            "directory": "research-catalog/input-pose-pointcloud/",
            "summary": "视频抽帧、COLMAP/MVS、learned pose fallback、稠密点云和坐标尺度合同。",
            "image": "assets/uploaded/input-pose-pointcloud/stage-input-pose.svg",
            "tags": ["COLMAP", "Point Cloud", "Pose"],
        },
        {
            "key": "visual-3dgs",
            "title": "视觉重建 / 3DGS",
            "directory": "research-catalog/visual-3dgs/",
            "summary": "GraphDECO 3DGS、Spark、SuperSplat 和 visual proxy 的工程边界。",
            "image": "assets/v2m-docs-mark.svg",
            "tags": ["3DGS", "Spark", "SuperSplat"],
        },
        {
            "key": "mesh-reconstruction",
            "title": "Mesh 重建",
            "directory": "research-catalog/mesh-reconstruction/",
            "summary": "COLMAP Delaunay、Poisson、GS2Mesh、SuGaR、2DGS/GOF 的阶段定位。",
            "image": "assets/uploaded/mesh-reconstruction/stage-mesh.svg",
            "tags": ["Mesh", "GS2Mesh", "SuGaR"],
        },
        {
            "key": "pointcloud-completion",
            "title": "点云/背景补全",
            "directory": "research-catalog/pointcloud-completion/",
            "summary": "点云清理、背景 clean plate、inpainting 与场景结构补全。",
            "image": "assets/uploaded/pointcloud-completion/stage-completion.svg",
            "tags": ["Completion", "Inpainting"],
        },
        {
            "key": "object-mesh-completion",
            "title": "物体 Mesh 补全",
            "directory": "research-catalog/object-mesh-completion/",
            "summary": "Hunyuan3D、Meshy、TRELLIS、InstantMesh、image-blaster object jobs。",
            "image": "assets/uploaded/pointcloud-completion/stage-completion.svg",
            "tags": ["Object Mesh", "image-blaster"],
        },
        {
            "key": "semantic-scene-graph",
            "title": "语义与 Scene Graph",
            "directory": "research-catalog/semantic-scene-graph/",
            "summary": "SAM/Grounded-SAM、semantic splats、mesh face sidecar 和交互查询。",
            "image": "assets/uploaded/semantic-scene-graph/stage-semantics.svg",
            "tags": ["Semantics", "Scene Graph"],
        },
        {
            "key": "collider-physics-proxy",
            "title": "Collider 与物理代理",
            "directory": "research-catalog/collider-physics-proxy/",
            "summary": "static collider、primitive proxy、convex decomposition 和 runtime physics。",
            "image": "assets/uploaded/research-catalog/stage-collider.svg",
            "tags": ["Collider", "Physics"],
        },
        {
            "key": "object-simulation",
            "title": "物体仿真",
            "directory": "research-catalog/object-simulation/",
            "summary": "rigid body、soft body、PhysSplat/Sim Anything 和 dynamic Gaussian。",
            "image": "assets/uploaded/object-simulation/stage-simulation.svg",
            "tags": ["Simulation", "PhysSplat"],
        },
        {
            "key": "industrial-pipelines",
            "title": "工业资产管线",
            "directory": "research-catalog/industrial-pipelines/",
            "summary": "World Labs / Icare、SimFoundry、image-blaster、Spark viewer 和 GLB runtime 约定。",
            "image": "assets/uploaded/research-catalog/pipeline-overview.svg",
            "tags": ["SimFoundry", "World Labs", "Spark"],
        },
        {
            "key": "experiments",
            "title": "本项目实验",
            "directory": "experiments/",
            "summary": "GS2Mesh、Open3D Poisson、COLMAP Delaunay、语义投影和 Web demo。",
            "image": "assets/uploaded/experiments/04-visual-physics-proxy-demo.png",
            "tags": ["Experiments", "Video2Mesh"],
        },
    ],
    "readingPaths": [
        {
            "title": "从视频到资产",
            "summary": "先看项目 pipeline，再看 P0/P1 如何落到 simulator-ready bundle。",
            "tags": ["Pipeline", "Simulator"],
            "query": "pipeline simulator",
        },
        {
            "title": "SimFoundry 复刻",
            "summary": "从调研报告进入复刻分支运行说明，确认当前只验收到 P0/P1 static scene。",
            "tags": ["SimFoundry", "Collider", "P1"],
            "query": "SimFoundry",
        },
        {
            "title": "调研目录",
            "summary": "按输入、3DGS、mesh、语义、collider、仿真和工业管线阶段阅读。",
            "tags": ["调研目录", "Research Catalog"],
            "query": "mesh",
        },
        {
            "title": "项目进度",
            "summary": "查看周报和优先级，理解当前路线为什么先保仿真资产合同。",
            "tags": ["进度目录", "P0", "P1"],
            "query": "weekly",
        },
    ],
}

ROOT_ORDER = [
    "README.md",
    "overview.md",
    "project-docs/overview.md",
    "project-docs/project-intro.md",
    "project-docs/pipeline.md",
    "project-docs/how-to-run.md",
    "project-docs/simfoundry-replica.md",
    "research-catalog/README.md",
    "research-catalog/overview.md",
    "research-catalog/industrial-pipelines/simfoundry.md",
    "progress/overview.md",
]

CATEGORY_ORDER = ["总目录", "项目文档", "调研目录", "进度目录", "实验记录", "Legacy"]
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
        href_path, suffix = split_href(href)
        target_path = (source_path.parent / href_path).resolve()
        if target_path.suffix.lower() not in {".md", ".markdown"}:
            return match.group(0)
        target_id = path_to_doc_id.get(target_path)
        if not target_id:
            return match.group(0)
        return f"[{label}](#/doc/{target_id}{suffix}{title})"

    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(\s+\"[^\"]+\")?\)", repl, markdown)


def source_rel(path: Path) -> str:
    return f"docs/video2mesh/{path.relative_to(DOC_ROOT).as_posix()}"


def infer_category(path: Path) -> str:
    rel = path.relative_to(DOC_ROOT).as_posix()
    if rel in {"README.md", "overview.md"}:
        return "总目录"
    if rel.startswith("project-docs/"):
        return "项目文档"
    if rel.startswith("research-catalog/"):
        return "调研目录"
    if rel.startswith("progress/"):
        return "进度目录"
    if rel.startswith("experiments/"):
        return "实验记录"
    if rel.startswith("legacy/"):
        return "Legacy"
    return "项目文档"


def infer_research_stage(path: Path) -> str:
    rel = path.relative_to(DOC_ROOT).as_posix()
    if rel.startswith("experiments/"):
        return "experiments"
    prefix = "research-catalog/"
    if not rel.startswith(prefix):
        return ""
    parts = rel.split("/")
    if len(parts) < 3:
        return "research-catalog"
    stage = parts[1]
    return stage if stage in STAGE_BY_KEY else ""


def infer_research_doc_role(path: Path, stage: str) -> str:
    rel = path.relative_to(DOC_ROOT).as_posix()
    if rel == "research-catalog/README.md":
        return "root"
    if stage and path.name in {"README.md", "overview.md"}:
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
    doc_id = str(meta.get("id") or f"video2mesh-{slugify(path.relative_to(DOC_ROOT).with_suffix('').as_posix())}")
    category = str(meta.get("category") or infer_category(path))
    research_stage = str(meta.get("research_stage") or infer_research_stage(path))
    research_stage_title = str(
        meta.get("research_stage_title")
        or STAGE_BY_KEY.get(research_stage, {}).get("title", "")
        or ("调研目录总览" if research_stage == "research-catalog" else "")
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


def copy_uploaded_assets() -> None:
    public_assets = PUBLIC_ROOT / "assets" / "uploaded"
    public_assets.mkdir(parents=True, exist_ok=True)
    if not ASSET_ROOT.exists():
        return
    for item in ASSET_ROOT.iterdir():
        if not item.is_dir() or item.name.startswith("challengecup-"):
            continue
        target = public_assets / item.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(item, target)


def main() -> None:
    md_paths = sorted(DOC_ROOT.rglob("*.md"), key=doc_sort_key)
    path_to_doc_id: dict[Path, str] = {}
    for path in md_paths:
        raw = path.read_text(encoding="utf-8")
        meta, _body = parse_frontmatter(raw)
        path_to_doc_id[path.resolve()] = str(
            meta.get("id") or f"video2mesh-{slugify(path.relative_to(DOC_ROOT).with_suffix('').as_posix())}"
        )
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
    copy_uploaded_assets()
    print(f"wrote {site_data}")
    print(f"docs={len(unique_docs)} categories={len(categories)}")


if __name__ == "__main__":
    main()
