#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import mimetypes
import os
import re
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import parse_qs, unquote, urlencode, urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs-blog"
CONTENT = SITE / "content"
REMOTE_CONTENT = CONTENT / "remote"
RUNTIME = SITE / "runtime"
PROJECTS_FILE = RUNTIME / "projects.json"
TASKS_FILE = RUNTIME / "codex_tasks.json"
USERS_FILE = RUNTIME / "users.json"
SESSIONS_FILE = RUNTIME / "sessions.json"
GITHUB_STATES_FILE = RUNTIME / "github_oauth_states.json"
BUILD_SCRIPT = SITE / "build_site.py"
CODEX_WORKSPACE = Path(os.environ.get("V2M_CODEX_WORKSPACE", ROOT / "CodexCloudWorkspace")).expanduser()
TERMINAL_SHELL = os.environ.get("V2M_TERMINAL_SHELL", "/bin/zsh")
TERMINAL_MAX_TIMEOUT_SECONDS = int(os.environ.get("V2M_TERMINAL_MAX_TIMEOUT_SECONDS", "30"))
TERMINAL_OUTPUT_LIMIT = int(os.environ.get("V2M_TERMINAL_OUTPUT_LIMIT", "80000"))


def load_env_file() -> None:
    for path in (ROOT / ".env", SITE / ".env"):
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


BOOTSTRAP_TOKEN = os.environ.get("V2M_API_TOKEN", "")
HOST = os.environ.get("V2M_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("V2M_API_PORT", "8787"))
SESSION_TTL_SECONDS = int(os.environ.get("V2M_SESSION_TTL_SECONDS", str(60 * 60 * 24 * 7)))
GITHUB_CLIENT_ID = os.environ.get("V2M_GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("V2M_GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.environ.get("V2M_GITHUB_REDIRECT_URI", "")
GITHUB_ALLOWED_LOGINS = [item.strip().lower() for item in os.environ.get("V2M_GITHUB_ALLOWED_LOGINS", "Interstellar6").split(",") if item.strip()]
GITHUB_SCOPE = os.environ.get("V2M_GITHUB_OAUTH_SCOPE", "read:user")
ALLOWED_WEB_ORIGINS = [item.strip() for item in os.environ.get(
    "V2M_ALLOWED_WEB_ORIGINS",
    "https://relumeow.top,http://relumeow.top,https://admin.relumeow.top",
).split(",") if item.strip()]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_iso(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromtimestamp(0, timezone.utc)


def slugify(value: str, fallback: str = "note") -> str:
    text = value.strip().lower()
    text = re.sub(r"[\s_/\\]+", "-", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff.-]+", "", text)
    text = text.strip(".-")
    return text or fallback


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback


def safe_workspace_id(value: str, fallback: str = "project") -> str:
    if "\x00" in value:
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid workspace id")
    text = slugify(value, fallback)
    if text in {".", ".."}:
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid workspace id")
    return text


def decode_url_part(value: str) -> str:
    return unquote(value)


def safe_workspace_path(root: Path, relative: str) -> Path:
    text = str(relative or "").strip().replace("\\", "/")
    if not text:
        raise ApiError(HTTPStatus.BAD_REQUEST, "path is required")
    if text.startswith("/") or "\x00" in text:
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid path")
    parts = [part for part in text.split("/") if part and part != "."]
    if not parts or any(part == ".." for part in parts):
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid path")
    target = root.joinpath(*parts).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ApiError(HTTPStatus.BAD_REQUEST, "path escapes workspace")
    return target


def safe_workspace_optional_path(root: Path, relative: str = "") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    root_resolved = root.resolve()
    text = str(relative or "").strip().replace("\\", "/")
    if text in {"", "."}:
        return root_resolved
    if text.startswith("/") or "\x00" in text:
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid path")
    parts = [part for part in text.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid path")
    target = root_resolved.joinpath(*parts).resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ApiError(HTTPStatus.BAD_REQUEST, "path escapes workspace")
    return target


def workspace_relative_path(path: Path) -> str:
    root = CODEX_WORKSPACE.resolve()
    target = path.resolve()
    if target == root:
        return ""
    return str(target.relative_to(root)).replace(os.sep, "/")


def workspace_item_meta(path: Path) -> dict[str, Any]:
    root = CODEX_WORKSPACE.resolve()
    target = path.resolve()
    relative = "" if target == root else str(target.relative_to(root)).replace(os.sep, "/")
    stat_result = path.lstat()
    mime, _encoding = mimetypes.guess_type(path.name)
    if path.is_symlink():
        item_type = "symlink"
    elif path.is_dir():
        item_type = "directory"
    elif path.is_file():
        item_type = "file"
    else:
        item_type = "other"
    return {
        "path": relative,
        "name": path.name or "CodexCloudWorkspace",
        "type": item_type,
        "mime": mime or "",
        "size": stat_result.st_size,
        "updated_at": datetime.fromtimestamp(stat_result.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
    }


def read_workspace_preview(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ApiError(HTTPStatus.BAD_REQUEST, "path is not a file")
    size = path.stat().st_size
    if size > 1_000_000:
        return {"preview": "", "preview_error": "file is larger than 1 MB", "truncated": False}
    raw = path.read_bytes()
    if b"\x00" in raw[:4096]:
        return {"preview": "", "preview_error": "binary file preview is not supported", "truncated": False}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    return {"preview": text, "preview_error": "", "truncated": False}


def list_workspace_path(relative: str = "", include_preview: bool = False) -> dict[str, Any]:
    target = safe_workspace_optional_path(CODEX_WORKSPACE, relative)
    if not target.exists():
        raise ApiError(HTTPStatus.NOT_FOUND, "workspace path not found")
    item = workspace_item_meta(target)
    payload: dict[str, Any] = {
        "ok": True,
        "root": str(CODEX_WORKSPACE.resolve()),
        "item": item,
        "children": [],
    }
    if target.is_dir():
        children = []
        for child in target.iterdir():
            try:
                resolved = child.resolve()
                root = CODEX_WORKSPACE.resolve()
                if resolved != root and root not in resolved.parents:
                    continue
                children.append(workspace_item_meta(child))
            except OSError:
                continue
        children.sort(key=lambda entry: (entry["type"] != "directory", entry["name"].lower()))
        payload["children"] = children[:500]
        payload["limited"] = len(children) > 500
        return payload
    if include_preview:
        payload.update(read_workspace_preview(target))
    return payload


def truncate_text(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[-limit:], True


def subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def read_codex_json(path: Path, default: Any) -> Any:
    return read_json(path, default)


def write_codex_json(path: Path, data: Any) -> None:
    write_json(path, data)


def codex_project_dir(project_id: str) -> Path:
    return CODEX_WORKSPACE / safe_workspace_id(project_id, "project")


def codex_session_dir(project_id: str, session_id: str) -> Path:
    return codex_project_dir(project_id) / "sessions" / safe_workspace_id(session_id, "session")


def codex_files_dir(project_id: str, session_id: str) -> Path:
    return codex_session_dir(project_id, session_id) / "files"


def codex_project_meta(project_id: str) -> dict[str, Any]:
    project_id = safe_workspace_id(project_id, "project")
    project_dir = codex_project_dir(project_id)
    meta = read_codex_json(project_dir / "project.json", {})
    if not isinstance(meta, dict):
        meta = {}
    sessions = read_codex_sessions(project_id)
    meta.setdefault("id", project_id)
    meta.setdefault("name", project_id)
    meta.setdefault("summary", "")
    meta.setdefault("status", "active")
    meta.setdefault("created_at", now_iso())
    meta["session_count"] = len(sessions)
    meta["updated_at"] = str(meta.get("updated_at") or meta.get("created_at") or "")
    return meta


def read_codex_projects() -> list[dict[str, Any]]:
    CODEX_WORKSPACE.mkdir(parents=True, exist_ok=True)
    projects = []
    for path in CODEX_WORKSPACE.iterdir():
        if path.is_dir() and not path.name.startswith("."):
            projects.append(codex_project_meta(path.name))
    projects.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
    return projects


def read_codex_sessions(project_id: str) -> list[dict[str, Any]]:
    sessions_root = codex_project_dir(project_id) / "sessions"
    if not sessions_root.exists():
        return []
    sessions = []
    for path in sessions_root.iterdir():
        if not path.is_dir() or path.name.startswith("."):
            continue
        meta = read_codex_json(path / "session.json", {})
        if not isinstance(meta, dict):
            meta = {}
        messages = read_codex_json(path / "messages.json", [])
        files = read_codex_json(path / "files.json", [])
        meta.setdefault("id", path.name)
        meta.setdefault("project_id", safe_workspace_id(project_id, "project"))
        meta.setdefault("title", path.name)
        meta.setdefault("status", "open")
        meta.setdefault("created_at", "")
        meta["message_count"] = len(messages) if isinstance(messages, list) else 0
        meta["file_count"] = len(files) if isinstance(files, list) else 0
        sessions.append(meta)
    sessions.sort(key=lambda item: str(item.get("updated_at", "") or item.get("created_at", "")), reverse=True)
    return sessions


def codex_session_detail(project_id: str, session_id: str) -> dict[str, Any]:
    session_dir = codex_session_dir(project_id, session_id)
    if not session_dir.exists():
        raise ApiError(HTTPStatus.NOT_FOUND, "Codex session not found")
    meta = read_codex_json(session_dir / "session.json", {})
    messages = read_codex_json(session_dir / "messages.json", [])
    files = read_codex_json(session_dir / "files.json", [])
    if not isinstance(meta, dict):
        meta = {}
    return {
        "session": meta,
        "messages": messages if isinstance(messages, list) else [],
        "files": files if isinstance(files, list) else [],
    }


def touch_codex_project(project_id: str) -> None:
    project_path = codex_project_dir(project_id) / "project.json"
    meta = read_codex_json(project_path, {})
    if isinstance(meta, dict):
        meta["updated_at"] = now_iso()
        write_codex_json(project_path, meta)


def enqueue_codex_cloud_task(project_id: str, session_id: str, prompt: str) -> dict[str, Any]:
    tasks = read_json(TASKS_FILE, [])
    task = {
        "id": unique_id("cloud-" + datetime.now().strftime("%Y%m%d%H%M%S"), tasks),
        "project": project_id,
        "prompt": prompt,
        "status": "queued",
        "priority": "normal",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "notes": "Created from Codex Cloud Workspace conversation.",
        "workspace_project": project_id,
        "workspace_session": session_id,
    }
    tasks.insert(0, task)
    write_json(TASKS_FILE, tasks)
    return task


def file_meta_for(path: Path, files_root: Path, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    relative = str(path.relative_to(files_root)).replace(os.sep, "/")
    mime, _encoding = mimetypes.guess_type(path.name)
    stat_result = path.stat()
    meta = {
        "id": slugify(relative, "file"),
        "path": relative,
        "name": path.name,
        "mime": mime or "application/octet-stream",
        "size": stat_result.st_size,
        "updated_at": datetime.fromtimestamp(stat_result.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
    }
    if extra:
        meta.update(extra)
    return meta


def ensure_bootstrap_token() -> str:
    global BOOTSTRAP_TOKEN
    if BOOTSTRAP_TOKEN:
        return BOOTSTRAP_TOKEN
    RUNTIME.mkdir(parents=True, exist_ok=True)
    token_file = RUNTIME / "api_token.txt"
    if token_file.exists():
        BOOTSTRAP_TOKEN = token_file.read_text(encoding="utf-8").strip()
    else:
        BOOTSTRAP_TOKEN = secrets.token_urlsafe(32)
        token_file.write_text(BOOTSTRAP_TOKEN + "\n", encoding="utf-8")
    return BOOTSTRAP_TOKEN


def hash_password(password: str, salt: str | None = None) -> dict[str, str | int]:
    if not salt:
        salt = secrets.token_hex(16)
    iterations = 260_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return {"algorithm": "pbkdf2_sha256", "iterations": iterations, "salt": salt, "hash": digest.hex()}


def verify_password(password: str, stored: dict[str, Any]) -> bool:
    try:
        salt = str(stored["salt"])
        iterations = int(stored["iterations"])
        expected = str(stored["hash"])
    except (KeyError, TypeError, ValueError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations).hex()
    return secrets.compare_digest(digest, expected)


def public_user(user: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(user.get("id", "")),
        "username": str(user.get("username", "")),
        "role": str(user.get("role", "admin")),
        "created_at": str(user.get("created_at", "")),
    }


def users_exist() -> bool:
    return bool(read_json(USERS_FILE, []))


def create_session(user_id: str) -> dict[str, str]:
    sessions = prune_sessions(read_json(SESSIONS_FILE, []), persist=False)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS)).replace(microsecond=0).isoformat()
    session = {
        "token": token,
        "token_hash": token_hash,
        "user_id": user_id,
        "created_at": now_iso(),
        "expires_at": expires_at,
    }
    stored_session = {key: value for key, value in session.items() if key != "token"}
    sessions.insert(0, stored_session)
    write_json(SESSIONS_FILE, sessions)
    return session


def prune_sessions(sessions: list[dict[str, Any]], persist: bool = True) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    active = [session for session in sessions if parse_iso(str(session.get("expires_at", ""))) > now]
    if persist and len(active) != len(sessions):
        write_json(SESSIONS_FILE, active)
    return active


def prune_github_states(states: list[dict[str, Any]], persist: bool = True) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    active = [state for state in states if parse_iso(str(state.get("expires_at", ""))) > now]
    if persist and len(active) != len(states):
        write_json(GITHUB_STATES_FILE, active)
    return active


def remove_session(token: str) -> None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    sessions = read_json(SESSIONS_FILE, [])
    write_json(SESSIONS_FILE, [session for session in sessions if not secrets.compare_digest(str(session.get("token_hash", "")), token_hash)])


def github_redirect_uri() -> str:
    if GITHUB_REDIRECT_URI:
        return GITHUB_REDIRECT_URI
    host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
    return f"http://{host}:{PORT}/api/auth/github/callback"


def safe_return_url(value: str) -> str:
    if not value:
        return "http://127.0.0.1:8000/docs-blog/admin/"
    parsed = urlparse(value)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
    if origin in ALLOWED_WEB_ORIGINS:
        return value
    return "http://127.0.0.1:8000/docs-blog/"


def origin_from_url(value: str) -> str:
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "*"


def request_json(url: str, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers=headers or {})
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ApiError(HTTPStatus.BAD_GATEWAY, f"GitHub request failed: {exc.code} {detail[:200]}") from exc
    data = json.loads(raw) if raw else {}
    if not isinstance(data, dict):
        raise ApiError(HTTPStatus.BAD_GATEWAY, "GitHub returned an unexpected response")
    return data


def request_form_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = urlencode(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers=headers or {})
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ApiError(HTTPStatus.BAD_GATEWAY, f"GitHub request failed: {exc.code} {detail[:200]}") from exc
    data = json.loads(raw) if raw else {}
    if not isinstance(data, dict):
        raise ApiError(HTTPStatus.BAD_GATEWAY, "GitHub returned an unexpected response")
    return data


def find_or_create_github_user(login: str) -> dict[str, Any]:
    users = read_json(USERS_FILE, [])
    login_lower = login.lower()
    for user in users:
        if str(user.get("github_login", "")).lower() == login_lower or str(user.get("username", "")).lower() == login_lower:
            user["github_login"] = login
            write_json(USERS_FILE, users)
            return user
    user = {
        "id": slugify(f"github-{login}", "github-user"),
        "username": login,
        "github_login": login,
        "role": "admin",
        "password": None,
        "created_at": now_iso(),
    }
    users.insert(0, user)
    write_json(USERS_FILE, users)
    return user


def login_callback_html(return_url: str, session: dict[str, str], user: dict[str, Any]) -> bytes:
    origin = origin_from_url(return_url)
    hash_params = urlencode({
        "v2m_session_token": session["token"],
        "v2m_expires_at": session["expires_at"],
        "v2m_username": str(user.get("username", "")),
    })
    fallback_url = return_url.split("#", 1)[0] + "#" + hash_params
    payload = json.dumps({
        "type": "v2m-github-login",
        "sessionToken": session["token"],
        "expiresAt": session["expires_at"],
        "user": public_user(user),
    }, ensure_ascii=False)
    html = f"""<!doctype html>
<meta charset="utf-8">
<title>Video2Mesh GitHub Login</title>
<p>GitHub 授权成功，可以关闭这个窗口。</p>
<script>
const payload = {payload};
if (window.opener) {{
  window.opener.postMessage(payload, {json.dumps(origin)});
  window.close();
}} else {{
  location.replace({json.dumps(fallback_url)});
}}
</script>
"""
    return html.encode("utf-8")


def build_site() -> None:
    subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=ROOT, check=True)


class ApiError(Exception):
    def __init__(self, status: HTTPStatus, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class Handler(BaseHTTPRequestHandler):
    server_version = "Video2MeshDocsAPI/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.add_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        self.handle_request("GET")

    def do_POST(self) -> None:
        self.handle_request("POST")

    def do_PATCH(self) -> None:
        self.handle_request("PATCH")

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def handle_request(self, method: str) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/health" and method == "GET":
                self.reply({"ok": True, "time": now_iso(), "users_configured": users_exist()})
                return
            if parsed.path == "/api/auth/setup" and method == "POST":
                self.require_bootstrap_auth()
                self.setup_user(self.read_body())
                return
            if parsed.path == "/api/auth/login" and method == "POST":
                self.login(self.read_body())
                return
            if parsed.path == "/api/auth/github/start" and method == "GET":
                self.github_start(parse_qs(parsed.query))
                return
            if parsed.path == "/api/auth/github/callback" and method == "GET":
                self.github_callback(parse_qs(parsed.query))
                return
            if parsed.path == "/api/auth/me" and method == "GET":
                self.reply({"ok": True, "user": public_user(self.require_auth())})
                return
            if parsed.path == "/api/auth/logout" and method == "POST":
                token = self.session_token()
                if token:
                    remove_session(token)
                self.reply({"ok": True})
                return
            if parsed.path == "/api/docs" and method == "POST":
                self.require_auth()
                self.create_doc(self.read_body())
                return
            if parsed.path == "/api/projects":
                self.require_auth()
                if method == "GET":
                    self.reply({"projects": read_json(PROJECTS_FILE, [])})
                    return
                if method == "POST":
                    self.create_project(self.read_body())
                    return
            if parsed.path == "/api/codex-tasks":
                self.require_auth()
                if method == "GET":
                    self.reply({"tasks": self.filtered_tasks(parse_qs(parsed.query))})
                    return
                if method == "POST":
                    self.create_task(self.read_body())
                    return
            if parsed.path == "/api/codex-cloud/projects":
                self.require_admin()
                if method == "GET":
                    self.reply({"projects": read_codex_projects(), "workspace": str(CODEX_WORKSPACE)})
                    return
                if method == "POST":
                    self.create_codex_project(self.read_body())
                    return
            if parsed.path == "/api/codex-cloud/fs" and method == "GET":
                self.require_admin()
                self.get_workspace_fs(parse_qs(parsed.query))
                return
            if parsed.path == "/api/codex-cloud/terminal" and method == "POST":
                self.require_admin()
                self.run_workspace_terminal(self.read_body())
                return
            codex_session_collection = re.fullmatch(r"/api/codex-cloud/projects/([^/]+)/sessions", parsed.path)
            if codex_session_collection:
                self.require_admin()
                project_id = decode_url_part(codex_session_collection.group(1))
                if method == "GET":
                    self.reply({"sessions": read_codex_sessions(project_id)})
                    return
                if method == "POST":
                    self.create_codex_session(project_id, self.read_body())
                    return
            codex_session_item = re.fullmatch(r"/api/codex-cloud/projects/([^/]+)/sessions/([^/]+)", parsed.path)
            if codex_session_item and method == "GET":
                self.require_admin()
                self.reply(codex_session_detail(decode_url_part(codex_session_item.group(1)), decode_url_part(codex_session_item.group(2))))
                return
            codex_messages = re.fullmatch(r"/api/codex-cloud/projects/([^/]+)/sessions/([^/]+)/messages", parsed.path)
            if codex_messages and method == "POST":
                self.require_admin()
                self.add_codex_message(decode_url_part(codex_messages.group(1)), decode_url_part(codex_messages.group(2)), self.read_body())
                return
            codex_files = re.fullmatch(r"/api/codex-cloud/projects/([^/]+)/sessions/([^/]+)/files", parsed.path)
            if codex_files and method == "POST":
                self.require_admin()
                self.add_codex_file(decode_url_part(codex_files.group(1)), decode_url_part(codex_files.group(2)), self.read_body())
                return
            codex_file_item = re.fullmatch(r"/api/codex-cloud/projects/([^/]+)/sessions/([^/]+)/files/(.+)", parsed.path)
            if codex_file_item and method == "GET":
                self.require_admin()
                self.get_codex_file(decode_url_part(codex_file_item.group(1)), decode_url_part(codex_file_item.group(2)), decode_url_part(codex_file_item.group(3)))
                return
            task_match = re.fullmatch(r"/api/codex-tasks/([^/]+)", parsed.path)
            if task_match and method == "PATCH":
                self.require_auth()
                self.update_task(task_match.group(1), self.read_body())
                return
            raise ApiError(HTTPStatus.NOT_FOUND, "Endpoint not found")
        except ApiError as error:
            self.reply({"ok": False, "error": error.message}, error.status)
        except subprocess.CalledProcessError as error:
            self.reply({"ok": False, "error": f"Build failed with exit code {error.returncode}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
        except Exception as error:
            self.reply({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def add_common_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_WEB_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "authorization, content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Cache-Control", "no-store")

    def reply(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.add_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def reply_html(self, data: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.add_common_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, url: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.add_common_headers()
        self.send_header("Location", url)
        self.end_headers()

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 5_000_000:
            raise ApiError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Request body too large")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"Invalid JSON: {error}") from error
        if not isinstance(data, dict):
            raise ApiError(HTTPStatus.BAD_REQUEST, "JSON body must be an object")
        return data

    def bearer_token(self) -> str:
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Missing Bearer token")
        return header.removeprefix("Bearer ").strip()

    def session_token(self) -> str:
        header = self.headers.get("Authorization", "")
        return header.removeprefix("Bearer ").strip() if header.startswith("Bearer ") else ""

    def require_bootstrap_auth(self) -> None:
        expected = ensure_bootstrap_token()
        provided = self.bearer_token()
        if not secrets.compare_digest(provided, expected):
            raise ApiError(HTTPStatus.FORBIDDEN, "Invalid token")

    def require_auth(self) -> dict[str, Any]:
        token = self.bearer_token()
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        sessions = prune_sessions(read_json(SESSIONS_FILE, []))
        session = next((item for item in sessions if secrets.compare_digest(str(item.get("token_hash", "")), token_hash)), None)
        if not session:
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Login required")
        users = read_json(USERS_FILE, [])
        user = next((item for item in users if str(item.get("id", "")) == str(session.get("user_id", ""))), None)
        if not user:
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Session user not found")
        return user

    def require_admin(self) -> dict[str, Any]:
        user = self.require_auth()
        if str(user.get("role", "admin")).lower() != "admin":
            raise ApiError(HTTPStatus.FORBIDDEN, "Admin role required")
        return user

    def setup_user(self, data: dict[str, Any]) -> None:
        if users_exist():
            raise ApiError(HTTPStatus.CONFLICT, "Admin user already exists")
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        if not re.fullmatch(r"[A-Za-z0-9_.@-]{3,64}", username):
            raise ApiError(HTTPStatus.BAD_REQUEST, "username must be 3-64 letters, numbers, dots, underscores, @, or hyphens")
        if len(password) < 10:
            raise ApiError(HTTPStatus.BAD_REQUEST, "password must be at least 10 characters")
        user = {
            "id": slugify(username, "user"),
            "username": username,
            "role": "admin",
            "password": hash_password(password),
            "created_at": now_iso(),
        }
        write_json(USERS_FILE, [user])
        session = create_session(str(user["id"]))
        self.reply({"ok": True, "user": public_user(user), "session_token": session["token"], "expires_at": session["expires_at"]}, HTTPStatus.CREATED)

    def login(self, data: dict[str, Any]) -> None:
        username = str(data.get("username") or "").strip()
        password = str(data.get("password") or "")
        users = read_json(USERS_FILE, [])
        user = next((item for item in users if str(item.get("username", "")) == username), None)
        if not user or not verify_password(password, user.get("password", {})):
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Invalid username or password")
        session = create_session(str(user["id"]))
        self.reply({"ok": True, "user": public_user(user), "session_token": session["token"], "expires_at": session["expires_at"]})

    def github_start(self, query: dict[str, list[str]]) -> None:
        if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
            raise ApiError(HTTPStatus.NOT_IMPLEMENTED, "GitHub OAuth is not configured")
        return_url = safe_return_url((query.get("return_url") or [""])[0])
        state = secrets.token_urlsafe(24)
        states = prune_github_states(read_json(GITHUB_STATES_FILE, []), persist=False)
        states.insert(0, {
            "state_hash": hashlib.sha256(state.encode("utf-8")).hexdigest(),
            "return_url": return_url,
            "created_at": now_iso(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).replace(microsecond=0).isoformat(),
        })
        write_json(GITHUB_STATES_FILE, states[:50])
        params = urlencode({
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": github_redirect_uri(),
            "scope": GITHUB_SCOPE,
            "state": state,
        })
        self.redirect(f"https://github.com/login/oauth/authorize?{params}")

    def github_callback(self, query: dict[str, list[str]]) -> None:
        code = (query.get("code") or [""])[0]
        state = (query.get("state") or [""])[0]
        if not code or not state:
            raise ApiError(HTTPStatus.BAD_REQUEST, "Missing GitHub OAuth code or state")
        state_hash = hashlib.sha256(state.encode("utf-8")).hexdigest()
        states = prune_github_states(read_json(GITHUB_STATES_FILE, []), persist=False)
        matched = next((item for item in states if secrets.compare_digest(str(item.get("state_hash", "")), state_hash)), None)
        write_json(GITHUB_STATES_FILE, [item for item in states if not secrets.compare_digest(str(item.get("state_hash", "")), state_hash)])
        if not matched:
            raise ApiError(HTTPStatus.UNAUTHORIZED, "Invalid or expired GitHub OAuth state")
        token_data = request_form_json(
            "https://github.com/login/oauth/access_token",
            {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": github_redirect_uri(),
                "state": state,
            },
            {"Accept": "application/json"},
        )
        access_token = str(token_data.get("access_token") or "")
        if not access_token:
            raise ApiError(HTTPStatus.UNAUTHORIZED, str(token_data.get("error_description") or "GitHub OAuth token exchange failed"))
        profile = request_json(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "Video2MeshDocsAPI",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        login = str(profile.get("login") or "")
        if not login:
            raise ApiError(HTTPStatus.BAD_GATEWAY, "GitHub profile did not include a login")
        if GITHUB_ALLOWED_LOGINS and login.lower() not in GITHUB_ALLOWED_LOGINS:
            raise ApiError(HTTPStatus.FORBIDDEN, f"GitHub login {login} is not allowed")
        user = find_or_create_github_user(login)
        session = create_session(str(user["id"]))
        self.reply_html(login_callback_html(str(matched.get("return_url", "")), session, user))

    def create_doc(self, data: dict[str, Any]) -> None:
        markdown = str(data.get("markdown") or data.get("body") or "").strip()
        if not markdown:
            raise ApiError(HTTPStatus.BAD_REQUEST, "markdown is required")
        title = str(data.get("title") or extract_title(markdown, "Remote Note")).strip()
        category = str(data.get("category") or "Remote").strip()
        summary = str(data.get("summary") or "").strip()
        tags = data.get("tags") if isinstance(data.get("tags"), list) else ["Remote"]
        slug = slugify(str(data.get("slug") or title))
        path = unique_path(REMOTE_CONTENT / f"{slug}.md")
        front_matter = {
            "title": title,
            "category": category,
            "summary": summary,
            "tags": [str(tag) for tag in tags if str(tag).strip()],
        }
        body = "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in front_matter.items() if value) + "\n---\n\n" + markdown + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        build_site()
        self.reply({"ok": True, "path": str(path.relative_to(ROOT)), "title": title, "rebuilt": True}, HTTPStatus.CREATED)

    def create_project(self, data: dict[str, Any]) -> None:
        name = str(data.get("name") or "").strip()
        if not name:
            raise ApiError(HTTPStatus.BAD_REQUEST, "name is required")
        projects = read_json(PROJECTS_FILE, [])
        project_id = slugify(str(data.get("id") or name), "project")
        project = {
            "id": unique_id(project_id, projects),
            "name": name,
            "repo": str(data.get("repo") or ""),
            "url": str(data.get("url") or ""),
            "summary": str(data.get("summary") or ""),
            "status": str(data.get("status") or "active"),
            "updated_at": now_iso(),
            "created_at": now_iso(),
        }
        projects.insert(0, project)
        write_json(PROJECTS_FILE, projects)
        self.reply({"ok": True, "project": project}, HTTPStatus.CREATED)

    def filtered_tasks(self, query: dict[str, list[str]]) -> list[dict[str, Any]]:
        tasks = read_json(TASKS_FILE, [])
        status = (query.get("status") or [""])[0]
        project = (query.get("project") or [""])[0]
        if status:
            tasks = [task for task in tasks if task.get("status") == status]
        if project:
            tasks = [task for task in tasks if task.get("project") == project]
        return tasks

    def create_task(self, data: dict[str, Any]) -> None:
        prompt = str(data.get("prompt") or data.get("message") or "").strip()
        if not prompt:
            raise ApiError(HTTPStatus.BAD_REQUEST, "prompt is required")
        tasks = read_json(TASKS_FILE, [])
        task = {
            "id": unique_id("task-" + datetime.now().strftime("%Y%m%d%H%M%S"), tasks),
            "project": str(data.get("project") or "Video2Mesh"),
            "prompt": prompt,
            "status": "queued",
            "priority": str(data.get("priority") or "normal"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "notes": str(data.get("notes") or ""),
        }
        tasks.insert(0, task)
        write_json(TASKS_FILE, tasks)
        self.reply({"ok": True, "task": task}, HTTPStatus.CREATED)

    def update_task(self, task_id: str, data: dict[str, Any]) -> None:
        tasks = read_json(TASKS_FILE, [])
        for task in tasks:
            if task.get("id") != task_id:
                continue
            for key in ("status", "notes", "result_url", "result_summary"):
                if key in data:
                    task[key] = str(data[key])
            task["updated_at"] = now_iso()
            write_json(TASKS_FILE, tasks)
            self.reply({"ok": True, "task": task})
            return
        raise ApiError(HTTPStatus.NOT_FOUND, "Task not found")

    def create_codex_project(self, data: dict[str, Any]) -> None:
        name = str(data.get("name") or "").strip()
        if not name:
            raise ApiError(HTTPStatus.BAD_REQUEST, "name is required")
        project_id = safe_workspace_id(str(data.get("id") or name), "project")
        project_dir = codex_project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        meta_path = project_dir / "project.json"
        existing = read_codex_json(meta_path, {})
        created_at = str(existing.get("created_at") or now_iso()) if isinstance(existing, dict) else now_iso()
        project = {
            "id": project_id,
            "name": name,
            "summary": str(data.get("summary") or ""),
            "status": str(data.get("status") or "active"),
            "created_at": created_at,
            "updated_at": now_iso(),
        }
        write_codex_json(meta_path, project)
        (project_dir / "sessions").mkdir(exist_ok=True)
        self.reply({"ok": True, "project": codex_project_meta(project_id)}, HTTPStatus.CREATED)

    def create_codex_session(self, project_id: str, data: dict[str, Any]) -> None:
        project_id = safe_workspace_id(project_id, "project")
        title = str(data.get("title") or "New Codex Session").strip()
        session_id = safe_workspace_id(str(data.get("id") or title or datetime.now().strftime("%Y%m%d%H%M%S")), "session")
        session_dir = codex_session_dir(project_id, session_id)
        if session_dir.exists():
            session_id = unique_id(session_id, [{"id": item.get("id")} for item in read_codex_sessions(project_id)])
            session_dir = codex_session_dir(project_id, session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "files").mkdir(exist_ok=True)
        session = {
            "id": session_id,
            "project_id": project_id,
            "title": title,
            "status": str(data.get("status") or "open"),
            "summary": str(data.get("summary") or ""),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        write_codex_json(session_dir / "session.json", session)
        write_codex_json(session_dir / "messages.json", [])
        write_codex_json(session_dir / "files.json", [])
        touch_codex_project(project_id)
        self.reply({"ok": True, "session": session}, HTTPStatus.CREATED)

    def add_codex_message(self, project_id: str, session_id: str, data: dict[str, Any]) -> None:
        project_id = safe_workspace_id(project_id, "project")
        session_id = safe_workspace_id(session_id, "session")
        session_dir = codex_session_dir(project_id, session_id)
        if not session_dir.exists():
            raise ApiError(HTTPStatus.NOT_FOUND, "Codex session not found")
        role = str(data.get("role") or "user").strip().lower()
        if role not in {"user", "assistant", "system", "tool"}:
            raise ApiError(HTTPStatus.BAD_REQUEST, "role must be user, assistant, system, or tool")
        content = str(data.get("content") or data.get("message") or "").strip()
        if not content:
            raise ApiError(HTTPStatus.BAD_REQUEST, "content is required")
        messages = read_codex_json(session_dir / "messages.json", [])
        if not isinstance(messages, list):
            messages = []
        message = {
            "id": unique_id("msg-" + datetime.now().strftime("%Y%m%d%H%M%S"), messages),
            "role": role,
            "content": content,
            "created_at": now_iso(),
        }
        if isinstance(data.get("files"), list):
            message["files"] = data.get("files")
        messages.append(message)
        write_codex_json(session_dir / "messages.json", messages)
        meta = read_codex_json(session_dir / "session.json", {})
        if isinstance(meta, dict):
            meta["updated_at"] = now_iso()
            meta["last_role"] = role
            meta["last_message"] = content[:240]
            write_codex_json(session_dir / "session.json", meta)
        touch_codex_project(project_id)
        task = None
        if role == "user" and data.get("enqueue_task", True):
            task = enqueue_codex_cloud_task(project_id, session_id, content)
        self.reply({"ok": True, "message": message, "task": task}, HTTPStatus.CREATED)

    def add_codex_file(self, project_id: str, session_id: str, data: dict[str, Any]) -> None:
        project_id = safe_workspace_id(project_id, "project")
        session_id = safe_workspace_id(session_id, "session")
        session_dir = codex_session_dir(project_id, session_id)
        if not session_dir.exists():
            raise ApiError(HTTPStatus.NOT_FOUND, "Codex session not found")
        path_value = str(data.get("path") or data.get("name") or "").strip()
        content = str(data.get("content") or "")
        if not path_value:
            raise ApiError(HTTPStatus.BAD_REQUEST, "path is required")
        files_root = codex_files_dir(project_id, session_id)
        target = safe_workspace_path(files_root, path_value)
        if len(content.encode("utf-8")) > 5_000_000:
            raise ApiError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "file content too large")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        files = read_codex_json(session_dir / "files.json", [])
        if not isinstance(files, list):
            files = []
        file_meta = file_meta_for(target, files_root, {
            "summary": str(data.get("summary") or ""),
            "source": str(data.get("source") or "codex"),
        })
        files = [item for item in files if str(item.get("path")) != file_meta["path"]]
        files.insert(0, file_meta)
        write_codex_json(session_dir / "files.json", files)
        meta = read_codex_json(session_dir / "session.json", {})
        if isinstance(meta, dict):
            meta["updated_at"] = now_iso()
            write_codex_json(session_dir / "session.json", meta)
        touch_codex_project(project_id)
        self.reply({"ok": True, "file": file_meta}, HTTPStatus.CREATED)

    def get_codex_file(self, project_id: str, session_id: str, relative_path: str) -> None:
        files_root = codex_files_dir(project_id, session_id)
        target = safe_workspace_path(files_root, relative_path)
        if not target.exists() or not target.is_file():
            raise ApiError(HTTPStatus.NOT_FOUND, "Codex file not found")
        size = target.stat().st_size
        if size > 5_000_000:
            raise ApiError(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "file is too large to preview")
        mime, _encoding = mimetypes.guess_type(target.name)
        raw = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.add_common_headers()
        self.send_header("Content-Type", mime or "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def get_workspace_fs(self, query: dict[str, list[str]]) -> None:
        relative = (query.get("path") or [""])[0]
        include_preview = (query.get("preview") or [""])[0].lower() in {"1", "true", "yes"}
        self.reply(list_workspace_path(relative, include_preview=include_preview))

    def run_workspace_terminal(self, data: dict[str, Any]) -> None:
        command = str(data.get("command") or "").strip()
        if not command:
            raise ApiError(HTTPStatus.BAD_REQUEST, "command is required")
        cwd = safe_workspace_optional_path(CODEX_WORKSPACE, str(data.get("cwd") or ""))
        if not cwd.exists() or not cwd.is_dir():
            raise ApiError(HTTPStatus.BAD_REQUEST, "cwd must be an existing workspace directory")
        try:
            timeout = int(data.get("timeout_seconds") or 12)
        except (TypeError, ValueError):
            raise ApiError(HTTPStatus.BAD_REQUEST, "timeout_seconds must be an integer")
        timeout = max(1, min(timeout, TERMINAL_MAX_TIMEOUT_SECONDS))
        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(
                [TERMINAL_SHELL, "-lc", command],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PWD": str(cwd)},
                check=False,
            )
            returncode = completed.returncode
            stdout = subprocess_text(completed.stdout)
            stderr = subprocess_text(completed.stderr)
        except subprocess.TimeoutExpired as error:
            timed_out = True
            returncode = 124
            stdout = subprocess_text(error.stdout)
            stderr = subprocess_text(error.stderr)
            stderr = (stderr + f"\nCommand timed out after {timeout} seconds.").strip()
        output = stdout + (("\n" + stderr) if stderr else "")
        output, truncated = truncate_text(output, TERMINAL_OUTPUT_LIMIT)
        stdout, stdout_truncated = truncate_text(stdout, TERMINAL_OUTPUT_LIMIT)
        stderr, stderr_truncated = truncate_text(stderr, TERMINAL_OUTPUT_LIMIT)
        self.reply({
            "ok": True,
            "command": command,
            "cwd": workspace_relative_path(cwd),
            "cwd_abs": str(cwd),
            "returncode": returncode,
            "timed_out": timed_out,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout": stdout,
            "stderr": stderr,
            "output": output,
            "truncated": truncated or stdout_truncated or stderr_truncated,
        })


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 10_000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise ApiError(HTTPStatus.CONFLICT, "Could not allocate unique path")


def unique_id(base: str, items: list[dict[str, Any]]) -> str:
    existing = {str(item.get("id")) for item in items}
    if base not in existing:
        return base
    for index in range(2, 10_000):
        candidate = f"{base}-{index}"
        if candidate not in existing:
            return candidate
    raise ApiError(HTTPStatus.CONFLICT, "Could not allocate unique id")


def main() -> int:
    token = ensure_bootstrap_token()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    REMOTE_CONTENT.mkdir(parents=True, exist_ok=True)
    print(f"Video2Mesh docs API listening on http://{HOST}:{PORT}")
    print(f"Bootstrap token: {token}")
    print("Create an admin user with POST /api/auth/setup, then use login session tokens for all Mac control endpoints.")
    print("Do not expose this server to the public internet without HTTPS, a strong password, and access control.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
