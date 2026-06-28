#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import json
import os
import stat
import sys
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs-blog"
RUNTIME = SITE / "runtime"
SESSION_FILE = RUNTIME / "session_token.txt"
DEFAULT_API_URL = os.environ.get("V2M_API_URL", "http://127.0.0.1:8787").rstrip("/")


class CliError(Exception):
    pass


def request_json(method: str, path: str, payload: dict | None = None, token: str | None = None, api_url: str = DEFAULT_API_URL) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(api_url.rstrip("/") + path, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
    except urlerror.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("error", raw)
        except json.JSONDecodeError:
            detail = raw
        raise CliError(f"{exc.code}: {detail}") from exc
    return json.loads(raw) if raw else {}


def save_session(token: str) -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(token + "\n", encoding="utf-8")
    SESSION_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)


def load_session(required: bool = True) -> str:
    token = os.environ.get("V2M_SESSION_TOKEN", "").strip()
    if token:
        return token
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text(encoding="utf-8").strip()
    if required:
        raise CliError("No session token. Run: python3 docs-blog/codex_queue.py login")
    return ""


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def url_part(value: str) -> str:
    return quote(str(value), safe="")


def cmd_login(args: argparse.Namespace) -> None:
    username = args.username or os.environ.get("V2M_USERNAME") or input("Username: ").strip()
    password = args.password or os.environ.get("V2M_PASSWORD") or getpass.getpass("Password: ")
    data = request_json("POST", "/api/auth/login", {"username": username, "password": password}, api_url=args.api_url)
    token = data.get("session_token")
    if not token:
        raise CliError("Login succeeded but no session_token was returned")
    save_session(str(token))
    print_json({"ok": True, "user": data.get("user"), "session_file": str(SESSION_FILE)})


def cmd_list(args: argparse.Namespace) -> None:
    token = load_session()
    query = f"?status={args.status}" if args.status else ""
    print_json(request_json("GET", f"/api/codex-tasks{query}", token=token, api_url=args.api_url))


def cmd_next(args: argparse.Namespace) -> None:
    token = load_session()
    data = request_json("GET", "/api/codex-tasks?status=queued", token=token, api_url=args.api_url)
    tasks = data.get("tasks") or []
    if not tasks:
        print_json({"ok": True, "task": None})
        return
    task = tasks[-1] if args.oldest else tasks[0]
    print_json({"ok": True, "task": task})


def cmd_add(args: argparse.Namespace) -> None:
    token = load_session()
    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        raise CliError("--prompt or stdin is required")
    payload = {"project": args.project, "prompt": prompt, "priority": args.priority}
    print_json(request_json("POST", "/api/codex-tasks", payload, token=token, api_url=args.api_url))


def cmd_patch(args: argparse.Namespace) -> None:
    token = load_session()
    payload = {"status": args.status}
    if args.summary:
        payload["result_summary"] = args.summary
    if args.notes:
        payload["notes"] = args.notes
    print_json(request_json("PATCH", f"/api/codex-tasks/{args.task_id}", payload, token=token, api_url=args.api_url))


def cmd_cloud_session(args: argparse.Namespace) -> None:
    token = load_session()
    path = f"/api/codex-cloud/projects/{url_part(args.project)}/sessions/{url_part(args.session)}"
    print_json(request_json("GET", path, token=token, api_url=args.api_url))


def cmd_cloud_reply(args: argparse.Namespace) -> None:
    token = load_session()
    content = args.content or sys.stdin.read().strip()
    if not content:
        raise CliError("--content or stdin is required")
    payload = {"role": args.role, "content": content, "enqueue_task": False}
    path = f"/api/codex-cloud/projects/{url_part(args.project)}/sessions/{url_part(args.session)}/messages"
    print_json(request_json("POST", path, payload, token=token, api_url=args.api_url))


def cmd_cloud_file(args: argparse.Namespace) -> None:
    token = load_session()
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    else:
        content = args.content or sys.stdin.read()
    if content == "":
        raise CliError("--content, --file, or stdin is required")
    payload = {
        "path": args.path,
        "summary": args.summary or "",
        "content": content,
        "source": "codex-cli",
    }
    path = f"/api/codex-cloud/projects/{url_part(args.project)}/sessions/{url_part(args.session)}/files"
    print_json(request_json("POST", path, payload, token=token, api_url=args.api_url))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read and update the Video2Mesh Codex task queue.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login")
    login.add_argument("--username")
    login.add_argument("--password")
    login.set_defaults(func=cmd_login)

    list_cmd = sub.add_parser("list")
    list_cmd.add_argument("--status")
    list_cmd.set_defaults(func=cmd_list)

    next_cmd = sub.add_parser("next")
    next_cmd.add_argument("--oldest", action="store_true")
    next_cmd.set_defaults(func=cmd_next)

    add = sub.add_parser("add")
    add.add_argument("--project", default="Video2Mesh")
    add.add_argument("--prompt")
    add.add_argument("--priority", default="normal")
    add.set_defaults(func=cmd_add)

    patch = sub.add_parser("patch")
    patch.add_argument("task_id")
    patch.add_argument("--status", required=True, choices=["queued", "running", "done", "blocked"])
    patch.add_argument("--summary")
    patch.add_argument("--notes")
    patch.set_defaults(func=cmd_patch)

    cloud_session = sub.add_parser("cloud-session")
    cloud_session.add_argument("--project", required=True)
    cloud_session.add_argument("--session", required=True)
    cloud_session.set_defaults(func=cmd_cloud_session)

    cloud_reply = sub.add_parser("cloud-reply")
    cloud_reply.add_argument("--project", required=True)
    cloud_reply.add_argument("--session", required=True)
    cloud_reply.add_argument("--role", default="assistant", choices=["assistant", "system", "tool"])
    cloud_reply.add_argument("--content")
    cloud_reply.set_defaults(func=cmd_cloud_reply)

    cloud_file = sub.add_parser("cloud-file")
    cloud_file.add_argument("--project", required=True)
    cloud_file.add_argument("--session", required=True)
    cloud_file.add_argument("--path", required=True)
    cloud_file.add_argument("--summary")
    cloud_file.add_argument("--content")
    cloud_file.add_argument("--file")
    cloud_file.set_defaults(func=cmd_cloud_file)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
