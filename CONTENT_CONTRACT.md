# CopyApeS 内容契约

前端从 GitHub 仓库 `hiEndless/copyapes_content` 读取长内容。新增/修改内容必须遵守本契约与 `schemas/*.schema.json`。

## 1. 仓库与读取约定

| 项 | 约定 |
|----|------|
| 源仓库 | `hiEndless/copyapes_content`（本地可推 Gitee，镜像同步到 GitHub） |
| 默认分支 | `main` |
| 正文扩展名 | `.mdx`（唯一） |
| 默认源语言 | `zh-CN` |
| 前端 locale 映射 | `zh→zh-CN`、`zh-TW→zh-TW`、`en→en-US`、`ja→ja-JP`、`ko→ko-KR` |
| 缺语言回退 | 当前 locale 缺失时回退 `zh-CN` |
| 仅渲染状态 | `status: published` |

路径规则：

```text
{locale}/{blog|tutorials|legal}/{slug}.mdx
{locale}/tutorials/{nested/slug}.mdx   # 教程允许子路径
```

对应前端路由：

| 内容类型 | 内容路径示例 | 前端路由 |
|----------|--------------|----------|
| blog | `en-US/blog/ai-changing-product-teams.mdx` | `/blog/ai-changing-product-teams` |
| tutorials | `zh-CN/tutorials/step.mdx` | `/docs/step` |
| tutorials | `zh-CN/tutorials/vip/bicoin.mdx` | `/docs/vip/bicoin` |
| legal | `zh-CN/legal/privacy.mdx` | `/privacy` |
| legal | `zh-CN/legal/terms.mdx` | `/terms` |

## 2. 类型必填矩阵

| 字段 | blog | tutorials | legal |
|------|:----:|:---------:|:-----:|
| slug / title / description | 必填 | 必填 | 必填 |
| category | `blog` | `tutorial` | `legal` |
| status / published_at / updated_at | 必填 | 必填 | 必填 |
| cover_image | **必填** | 建议 | 可选 |
| tags | **必填** | 建议 | 可选 |
| keywords | 建议 | 可选 | 可选 |
| featured | 可选（首页 Hero） | - | - |
| author.name | 建议 | 可选 | - |
| author.picture | 可选 | - | - |
| read_time | 建议 | 可选 | - |
| version | - | - | **必填** |
| source_locale / translation_status | 建议 | 建议 | 建议 |

## 3. Frontmatter 模板

见 `templates/`：

- `templates/blog.example.mdx`
- `templates/tutorial.example.mdx`
- `templates/legal.example.mdx`

字段以 `schemas/frontmatter.schema.json` 为准。禁止使用旧字段：`publishedAt`、`image`、`readTime`。

## 4. 封面与正文图片

- blog **必须**提供 `cover_image`。
- 优先：`cover_image: "@asset:blog/xxx-cover.webp"`。
- 正文图片：`![说明](@asset:tutorials/xxx-01.webp)`。
- 禁止在正文写死 Cloudflare/CDN URL；由 `assets/manifests/images.json` 解析。
- 无文字/多语言通用图放 `assets/images/shared/...`。
- 含文字截图放对应 locale 目录。
- 推荐 webp；需要透明通道可用 png。

解析优先级：当前语言目录 > shared > zh-CN。

## 5. 发布清单

1. 在 `zh-CN` 写源文（`.mdx`）并填 frontmatter。
2. 补齐封面/步骤图，引用 `@asset:`。
3. 生成其他语言，**同名路径**。
4. 更新 `content_index.json` 登记 slug / path / locales 状态。
5. 图片上传 R2 后更新 `assets/manifests/images.json`。
6. 用 schema 校验；仅将审核通过的条目设为 `published`。

## 6. 索引登记格式

`content_index.json` 的 `items` key 使用 `{typeDir}/{slug}`：

```json
{
  "blog/ai-changing-product-teams": {
    "type": "blog",
    "slug": "ai-changing-product-teams",
    "path": "blog/ai-changing-product-teams.mdx",
    "featured": true,
    "locales": {
      "en-US": "published",
      "zh-CN": "draft"
    }
  }
}
```
