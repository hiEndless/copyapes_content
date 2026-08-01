# CopyApeS 内容目录说明

该目录只存放网站长内容资产，包括用户协议、隐私政策、教程、帮助文档、营销博客、SEO 内容，以及这些长内容引用的图片。

项目产品本身使用的图片、图标、前端静态资源仍放在前端项目的 `public/` 目录，不迁移到这里。

正式内容契约见 `CONTENT_CONTRACT.md` 与 `templates/`。

## 设计目标

- 支持 AI 生成内容、自动翻译、多语言人工校对、灰度发布。
- 内容正文、图片源文件、Cloudflare 图片地址、内容索引都可版本化管理。
- 前端可以按 locale + category + slug 稳定读取内容。
- 后续即使接入 CMS，也可以把这里作为源内容仓库或迁移基准。

## 目录结构

```text
copyapes_content/
  README.md
  CONTENT_CONTRACT.md
  AI_WRITING_GUIDE.md
  content_index.json
  templates/
    blog.example.mdx
    tutorial.example.mdx
    legal.example.mdx
  schemas/
    frontmatter.schema.json
    asset_manifest.schema.json
  zh-CN/
    legal/
    tutorials/
    blog/
  zh-TW/
    legal/
    tutorials/
    blog/
  en-US/
    legal/
    tutorials/
    blog/
  ja-JP/
    legal/
    tutorials/
    blog/
  ko-KR/
    legal/
    tutorials/
    blog/
  assets/
    images/
      shared/
        legal/
        tutorials/
        blog/
      zh-CN/
        legal/
        tutorials/
        blog/
      zh-TW/
        legal/
        tutorials/
        blog/
      en-US/
        legal/
        tutorials/
        blog/
      ja-JP/
        legal/
        tutorials/
        blog/
      ko-KR/
        legal/
        tutorials/
        blog/
    manifests/
      images.json
  scripts/
```

## 核心文件

- `CONTENT_CONTRACT.md`：内容创作与前端读取契约（必读）。
- `AI_WRITING_GUIDE.md`：AI 生成、翻译、改写内容时必须遵守的写作规范。
- `content_index.json`：内容总索引，记录支持语言、内容类型和后续发布状态。
- `schemas/frontmatter.schema.json`：MDX frontmatter 字段约束。
- `schemas/asset_manifest.schema.json`：图片 manifest 字段约束。
- `assets/manifests/images.json`：本地图片到 Cloudflare R2/CDN URL 的映射。

## 支持语言

- `zh-CN`：简体中文，默认源语言。
- `zh-TW`：繁体中文。
- `en-US`：英文。
- `ja-JP`：日语。
- `ko-KR`：韩语。

## 内容正文

- 每种语言使用独立 locale 目录，例如 `zh-CN`、`zh-TW`、`en-US`、`ja-JP`、`ko-KR`。
- 同一篇内容在不同语言目录下使用相同文件名，方便前端按当前语言查找。
- 如果某个语言版本缺失，前端建议回退到 `zh-CN`。

示例：

```text
copyapes_content/zh-CN/blog/api-risk-control.mdx
copyapes_content/zh-TW/blog/api-risk-control.mdx
copyapes_content/en-US/blog/api-risk-control.mdx
copyapes_content/ja-JP/blog/api-risk-control.mdx
copyapes_content/ko-KR/blog/api-risk-control.mdx
```

## 内容类型

- `legal/`：用户协议、隐私政策、免责声明、风险提示。
- `tutorials/`：产品教程、API 添加教程、Cookie 获取教程、跟单配置教程。
- `blog/`：营销博客、SEO 内容、行业观点、功能介绍。

## Frontmatter 约定

MDX 内容必须有 frontmatter。建议字段如下：

```md
---
slug: api-risk-control
title: API 风控与安全设置
description: 介绍 CopyApeS API 权限、IP 白名单和跟单安全设置。
category: tutorial
tags:
  - api
  - security
cover_image: "@asset:blog/api-risk-control-cover.webp"
source_locale: zh-CN
translation_status: source
published_at: 2026-07-31
updated_at: 2026-07-31
status: published
---
```

字段说明：

- `slug`：同一篇内容在所有语言中保持一致。
- `category`：使用 `legal`、`tutorial`、`blog`。
- `status`：使用 `draft`、`review`、`published`、`archived`。
- `translation_status`：源文用 `source`，机翻用 `machine`，人工审核后用 `reviewed`。
- `cover_image`：优先使用 `@asset:`，不要直接写死 Cloudflare URL。
- 法律文案建议额外增加 `version`。

## 图片存放规则

长内容图片放在 `assets/images/`，按“是否区分语言 + 内容类型”分层。

不区分语言的图片放：

```text
copyapes_content/assets/images/shared/blog/api-risk-control-cover.webp
copyapes_content/assets/images/shared/tutorials/api-permission-01.webp
```

区分语言的图片放：

```text
copyapes_content/assets/images/zh-CN/tutorials/api-permission-01.webp
copyapes_content/assets/images/zh-TW/tutorials/api-permission-01.webp
copyapes_content/assets/images/en-US/tutorials/api-permission-01.webp
copyapes_content/assets/images/ja-JP/tutorials/api-permission-01.webp
copyapes_content/assets/images/ko-KR/tutorials/api-permission-01.webp
```

允许同一张图片同时存在公共版本和语言版本。读取优先级建议：

```text
当前语言版本 > shared 公共版本 > 内容正文 fallback 语言
```

例如当前语言是 `en-US`，正文引用：

```md
![API permissions](@asset:tutorials/api-permission-01.webp)
```

解析顺序建议为：

```text
assets/images/en-US/tutorials/api-permission-01.webp
assets/images/shared/tutorials/api-permission-01.webp
assets/images/zh-CN/tutorials/api-permission-01.webp
```

## 图片引用约定

MDX 正文建议引用稳定 asset key，不直接写死 Cloudflare URL：

```md
![API 权限示例](@asset:tutorials/api-permission-01.webp)
![风险控制封面](@asset:blog/api-risk-control-cover.webp)
```

后续构建或前端解析时，通过 `assets/manifests/images.json` 把 `@asset:` 替换为 Cloudflare R2/CDN URL。

## Manifest 约定

`assets/manifests/images.json` 用于记录本地图片和 Cloudflare 地址的对应关系，后续增量上传脚本维护该文件。

建议结构：

```json
{
  "shared/blog/api-risk-control-cover.webp": {
    "local_path": "assets/images/shared/blog/api-risk-control-cover.webp",
    "r2_key": "content/images/shared/blog/api-risk-control-cover.webp",
    "url": "https://r2.lichaoyuan.com/content/images/shared/blog/api-risk-control-cover.webp",
    "sha256": "",
    "size": 0,
    "content_type": "image/webp",
    "updated_at": ""
  }
}
```

## 内容生产流程

建议按以下流程迭代：

1. 在 `zh-CN` 下创建源文 MDX，填写 frontmatter。
2. 按 `AI_WRITING_GUIDE.md` 生成初稿，状态设为 `draft`。
3. 补充或上传长内容图片，正文使用 `@asset:` 引用。
4. 更新 `content_index.json`，登记内容 slug、category、locale 状态。
5. 生成 `zh-TW`、`en-US`、`ja-JP`、`ko-KR` 翻译，保持 slug 和文件名一致。
6. 人工审核翻译后，将 `translation_status` 改为 `reviewed`。
7. 发布前用 schema 校验 frontmatter 和图片 manifest。
8. 运行 `python scripts/sync_assets_to_r2.py` 上传图片并回填 `assets/manifests/images.json`。

## 脚本

- `scripts/sync_assets_to_r2.py`：增量上传 `assets/images/**` 到 Cloudflare R2（公网 `https://r2.lichaoyuan.com`，前缀 `content/images/`），并更新 `images.json`。使用内容仓 `.env` 中的 `CF_*` 环境变量。
- 后续建议补充：
  - `validate_content.py`：校验 frontmatter、语言目录、slug 一致性、图片引用是否存在。
  - `translate_content.py`：读取源文并生成多语言草稿。
  - `build_content_index.py`：扫描 MDX 自动生成或校验 `content_index.json`。

## 命名建议

- 内容文件使用英文短横线 slug：`api-risk-control.mdx`。
- 图片文件使用英文短横线，按用途编号：`api-permission-01.webp`。
- 优先使用 `webp`，需要透明背景时使用 `png`。
- 图片内含文字时，优先放到对应语言目录；不含文字或各语言通用时，放到 `shared`。

## 上线建议

- 当前阶段先用 MDX + manifest 管理内容，不急着接重型 CMS。
- SEO URL 建议由前端拼语言前缀，例如 `/en/blog/api-risk-control`。
- 图片正式上线走 Cloudflare R2/CDN，GitHub 只作为源文件和 manifest 的版本管理。
- 发布流程不要依赖人工记忆，后续应逐步收敛到脚本校验和 CI 守卫。
