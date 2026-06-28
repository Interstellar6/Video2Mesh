#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import parse_qs, urlencode, urlparse


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
    "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:8787,http://localhost:8787,https://relumeow.top,http://relumeow.top",
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
        return "http://127.0.0.1:8000/docs-blog/"
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
