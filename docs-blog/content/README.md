---
title: 上传 Markdown 更新网站
category: Guide
summary: 把新的 .md 文件放进这个目录，重新构建后就会出现在博客网站中。
---

# 上传 Markdown 更新网站

这个目录是博客网站的可追加内容入口。

## 怎么新增文章

1. 把新的 `.md` 文件放到 `docs-blog/content/`。
2. 如果 Markdown 引用了图片，把图片放到 `docs-blog/content/assets/` 或文档旁边。
3. 在仓库根目录运行：

```bash
python3 docs-blog/build_site.py
```

4. 打开 `docs-blog/index.html` 查看。

## 怎么在线编辑

1. 打开文章后点“编辑 Markdown”，左侧改源码，右侧会实时预览。
2. 点“保存草稿”后，修改会保存在当前浏览器的本地草稿里，刷新页面也还在。
3. 文章里的任务勾选框可以直接点，勾选状态会同步回 Markdown 草稿。
4. 点“下载 md”可以导出当前 Markdown；要永久进入网站，把导出的文件放进 `docs-blog/content/` 后重新构建。
5. 点“撤销草稿”可以回到构建出来的原始版本。

## 支持的 Markdown 能力

- `#` 到 `######` 标题。
- 表格。
- 代码块。
- 图片：`![说明](./assets/example.png)`。
- 任务勾选：`- [ ] todo` 和 `- [x] done`。
- 折叠块：

```markdown
:::details 标题
这里是可折叠内容。
:::
```

- Obsidian 风格内部链接：`[[Video2Mesh 当前流水线]]`。

## 真实交互示例

- [x] 已经支持从构建脚本收录仓库 Markdown。
- [ ] 上传一篇新的 Markdown 测试临时预览。
- [ ] 把图片和 Markdown 一起选中，验证本地图片展示。

:::details 点开查看 Obsidian 风格链接示例
这里有一个内部链接：[[Video2Mesh 当前流水线]]。

如果目标标题存在，网站会把它渲染成站内文章链接。
:::

## 可选 Front Matter

```markdown
---
title: 文章标题
category: Surveys
summary: 文章摘要
tags:
  - 3DGS
  - Scene Graph
---
```

不写也可以，网站会自动从一级标题里提取标题。
