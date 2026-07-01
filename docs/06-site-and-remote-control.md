---
title: relumeow.top 文档站与远程控制
category: Site
summary: Markdown 文档站的构建、内容收录、登录、API 和安全边界。
tags:
  - relumeow.top
  - Docs Site
  - API
---

# relumeow.top 文档站与远程控制

## 文档站定位

`docs-blog/` 是 relumeow.top 的静态文档站和本机 API 管理界面。当前项目主文档来自：

```text
README.md
docs/*.md
docs-blog/content/*.md
```

项目长期主文档应放在 `docs/`。`docs-blog/content/` 只保留网站或临时内容，不再放项目主报告。

## 构建网站

在仓库根目录运行：

```bash
python3 docs-blog/build_site.py
```

输出：

```text
docs-blog/site-data.js
docs-blog/_public/
docs-blog/CNAME
```

`docs-blog/_public/` 是静态发布目录，已被 Git 忽略。

## 新增文档

1. 把项目主文档放到 `docs/`。
2. 在文件顶部加 front matter：

```markdown
---
title: 文档标题
category: Research
summary: 一句话摘要。
tags:
  - 3DGS
  - Mesh
---
```

3. 运行：

```bash
python3 docs-blog/build_site.py
```

4. 打开 `docs-blog/index.html` 本地检查。

## Markdown 支持

文档站支持：

- 标题。
- 表格。
- 代码块。
- 本地图片。
- 网络图片。
- task list。
- 折叠块。
- Obsidian 风格内部链接。

本地图片建议放在文档旁边或 `docs-blog/content/assets/`。构建脚本会复制可解析的本地图片。

网络图片可以直接写在 Markdown 里：

```markdown
![SuGaR pipeline](https://anttwo.github.io/sugar/results/full_teaser.png "图注文字")
```

图片单独占一行时，页面会渲染成带图注和来源域名的 figure。外链图片会保留原图链接，点击可打开来源。

## 本机 API

默认 API URL：

```text
https://api.relumeow.top
```

本地开发时可运行：

```bash
python3 docs-blog/api_server.py
```

管理界面在：

```text
docs-blog/admin/index.html
```

API 负责：

- 用户登录和 session。
- 管理员创建。
- GitHub OAuth 登录。
- 在线编辑和同步 Markdown。
- 多项目记录。
- Codex 任务队列。
- 工作区文件浏览。
- 管理员终端。

## 安全边界

远程控制功能必须保持以下边界：

- 管理员功能需要登录。
- workspace terminal 只能对可信用户开放。
- runtime secrets 不进 Git。
- `.env`、`docs-blog/runtime/`、密钥文件已被 `.gitignore` 排除。
- 网站静态发布目录不应包含 runtime state。

## Codex 同步文档

推荐流程：

```text
edit docs/*.md
  -> python3 docs-blog/build_site.py
  -> inspect docs-blog/site-data.js / index.html
  -> deploy static site
```

不要直接手写 `site-data.js`。它是构建产物。
