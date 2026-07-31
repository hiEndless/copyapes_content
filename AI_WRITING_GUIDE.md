# AI 内容写作规范

该文件用于约束 AI 生成、翻译、改写 CopyApeS 长内容时的输出质量。生成内容前优先读取本文件。

## 基本原则

- 内容必须清晰、克制、可执行，不使用夸大收益或承诺盈利的表达。
- 不得暗示跟单、API 交易、机器人或任何交易策略可以保证盈利。
- 涉及交易、API、Cookie、杠杆、跟单风险时，必须保留风险提示。
- 教程内容以步骤清晰为第一目标，不写营销腔。
- 营销博客可以强调产品价值，但不得弱化风险。
- 法律文案不得随意改写关键责任边界，修改前应保留版本和更新时间。

## 内容类型要求

### legal

- 适用于用户协议、隐私政策、免责声明、风险提示。
- 必须包含 `version` 和 `updated_at`。
- 翻译时保持条款编号、责任边界、金额、日期、主体名称不变。
- 不允许 AI 自行新增法律承诺。

### tutorials

- 适用于产品教程、API 添加教程、Cookie 获取教程、跟单配置教程。
- 推荐结构：
  - 适用对象
  - 前置条件
  - 操作步骤
  - 常见问题
  - 风险提示
- 步骤必须可执行，避免“点击相关按钮”这类模糊描述。

### blog

- 适用于营销博客、SEO 内容、行业观点、功能介绍。
- 必须填写 `title`、`description`、`tags`。
- 内容应围绕一个明确关键词，不要堆砌无关关键词。
- 可以引导用户了解产品，但不得写成承诺收益的广告。

## 多语言翻译规则

- `slug` 在所有语言中保持一致。
- `source_locale` 默认使用 `zh-CN`。
- 当前支持语言为 `zh-CN`、`zh-TW`、`en-US`、`ja-JP`、`ko-KR`。
- 默认从 `zh-CN` 源文生成 `zh-TW`、`en-US`、`ja-JP`、`ko-KR` 草稿。
- 机器翻译后必须标记：

```yaml
status: draft
translation_status: machine
translation_source: zh-CN
```

- 人工审核后才允许改为：

```yaml
status: published
translation_status: reviewed
```

- 翻译必须保留 Markdown/MDX 结构、frontmatter 字段名和 `@asset:` 引用。
- 正文文件扩展名必须为 `.mdx`。
- 不允许把 `@asset:` 替换成 Cloudflare URL。
- 不允许改动代码块、命令、接口路径、环境变量名、错误码。

## 风险表达规范

推荐表达：

- 跟单交易存在亏损风险，请根据自身风险承受能力配置金额。
- API 权限建议仅开启交易和读取权限，不建议开启提现权限。
- Cookie/JWT 失效可能导致任务停止或信号中断。

禁止表达：

- 稳赚
- 保本
- 无风险套利
- 一定盈利
- 官方保证收益
- 自动赚钱

## 图片规范

- 产品静态资源继续放前端 `public/`。
- 长内容图片放 `copyapes_content/assets/images/`。
- 正文使用 `@asset:` 引用图片。
- 图片包含文字时应放到对应语言目录。
- 图片不含文字或所有语言通用时放到 `shared`。

## 输出要求

- 生成新内容时同时补 frontmatter。
- 生成翻译时保留原文所有 `slug`、`category`、`cover_image`、`published_at`。
- 修改内容后需要同步更新 `updated_at`。
- 新增内容后需要更新 `content_index.json`。
