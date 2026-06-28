---
title: 本机 API、用户登录与手机远程控制
category: Guide
summary: 先登录本机 API，再让 Codex 或手机把 Markdown、项目记录和任务队列同步进网站。
tags:
  - API
  - Codex
  - Remote
---

# 本机 API、用户登录与手机远程控制

这个网站本身仍然是 GitHub Pages 静态站。动态能力由本机侧边 API 提供：它运行在这台电脑上，负责登录鉴权、写入 Markdown、记录多个项目、接收 Codex 任务队列。

## 启动 API

```bash
./docs-blog/run_api.sh
```

默认监听：

```text
http://127.0.0.1:8787
```

第一次启动时会生成 bootstrap token。它只用于首次创建管理员账号：

```bash
cat docs-blog/runtime/api_token.txt
```

如果想固定配置，可以创建 `docs-blog/.env`：

```env
V2M_API_TOKEN=change-this-long-random-token
V2M_API_HOST=127.0.0.1
V2M_API_PORT=8787
V2M_SESSION_TTL_SECONDS=604800
V2M_GITHUB_ALLOWED_LOGINS=Interstellar6
```

## 首次创建管理员

账号建议使用：

```text
Interstellar6
```

创建管理员：

```bash
export V2M_BOOTSTRAP_TOKEN="$(cat docs-blog/runtime/api_token.txt)"

curl -H "Authorization: Bearer $V2M_BOOTSTRAP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"Interstellar6","password":"替换成强密码"}' \
  http://127.0.0.1:8787/api/auth/setup
```

返回里的 `session_token` 是登录会话 token。以后访问 Mac 控制接口都用这个会话 token，而不是 bootstrap token。

## 普通登录

```bash
export V2M_SESSION_TOKEN="$(
  curl -s -H "Content-Type: application/json" \
    -d '{"username":"Interstellar6","password":"替换成强密码"}' \
    http://127.0.0.1:8787/api/auth/login \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["session_token"])'
)"
```

检查当前登录用户：

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  http://127.0.0.1:8787/api/auth/me
```

## GitHub 授权登录

先在 GitHub 创建一个 OAuth App，Authorization callback URL 填：

```text
http://127.0.0.1:8787/api/auth/github/callback
```

然后在 `docs-blog/.env` 里配置：

```env
V2M_GITHUB_CLIENT_ID=你的_client_id
V2M_GITHUB_CLIENT_SECRET=你的_client_secret
V2M_GITHUB_REDIRECT_URI=http://127.0.0.1:8787/api/auth/github/callback
V2M_GITHUB_ALLOWED_LOGINS=Interstellar6
```

重启 API 后，管理员界面 `#/admin` 里的“GitHub 授权登录”会打开 GitHub OAuth。API 会校验 GitHub 登录名必须在 `V2M_GITHUB_ALLOWED_LOGINS` 里，默认只允许 `Interstellar6`。

## 管理员界面

公开首页只展示文档，不显示 Mac 控制台。需要远程控制时，打开：

```text
#/admin
```

例如本地预览是：

```text
http://127.0.0.1:8000/docs-blog/#/admin
```

线上个人主页是：

```text
https://interstellar6.github.io/#/admin
```

## 让 Codex 同步一篇文档

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Codex Remote Note",
    "category": "Remote",
    "tags": ["Codex", "Remote"],
    "markdown": "# Codex Remote Note\n\n这篇文档来自本机 API。"
  }' \
  http://127.0.0.1:8787/api/docs
```

API 会把文件写入：

```text
docs-blog/content/remote/
```

然后自动运行：

```bash
python3 docs-blog/build_site.py
```

## 多项目记录

添加项目：

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Video2Mesh",
    "repo": "/Users/zhangyuxiang/Desktop/worksplace/Video2Mesh",
    "summary": "文档站、远程 API 和任务队列"
  }' \
  http://127.0.0.1:8787/api/projects
```

读取项目：

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  http://127.0.0.1:8787/api/projects
```

## Codex 任务队列

手机端或网页端可以把工作请求写入队列：

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project": "Video2Mesh",
    "prompt": "请 Codex 调研如何把 3DGS 场景转成可交互游戏关卡。"
  }' \
  http://127.0.0.1:8787/api/codex-tasks
```

本机 Codex 可以读取：

```bash
curl -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  http://127.0.0.1:8787/api/codex-tasks
```

也可以用本机辅助脚本登录并读取队列：

```bash
python3 docs-blog/codex_queue.py login --username Interstellar6
python3 docs-blog/codex_queue.py next
python3 docs-blog/codex_queue.py list --status queued
```

执行后更新状态：

```bash
curl -X PATCH \
  -H "Authorization: Bearer $V2M_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"done","result_summary":"已完成并同步到网站。"}' \
  http://127.0.0.1:8787/api/codex-tasks/task-id
```

或者：

```bash
python3 docs-blog/codex_queue.py patch task-id --status done --summary "已完成并同步到网站。"
```

## 手机怎么连

局域网内调试可以临时改成：

```env
V2M_API_HOST=0.0.0.0
```

然后手机访问同一个网站的管理员界面 `#/admin`，在 API 地址里填：

```text
http://这台电脑的局域网IP:8787
```

公网访问建议走 Cloudflare Tunnel、Tailscale Funnel、ngrok 或自建 HTTPS 反代，并且只暴露给自己使用。

如果网站通过 `https://relumeow.top` 打开，浏览器通常会拦截页面调用普通 `http://` API。手机远程控制时，API 地址最好也是 HTTPS 隧道地址，或者在局域网调试时用普通 HTTP 页面打开网站。

## 安全边界

- API 不提供任意 shell 执行接口。
- 远程控制只进入任务队列，由本机 Codex 读取后人工或半自动执行。
- token 不提交到 git；默认保存在 `docs-blog/runtime/api_token.txt`。
- GitHub Pages 只能托管静态站，不能直接运行这个 API。

这个边界能让手机远程“派活”，但不把电脑变成一个公网命令执行入口。
