# CopyApeS Content Repository

这是 CopyApeS 独立内容仓库，用于维护用户协议、教程、博客、SEO 内容和长内容图片资产。

## 使用方式

1. 在对应语言目录下新增 MDX 内容。
2. 遵守 `AI_WRITING_GUIDE.md` 的写作和翻译规范。
3. 图片源文件放入 `assets/images/`。
4. Cloudflare R2/CDN 上传结果写入 `assets/manifests/images.json`。
5. 发布前校验 `schemas/` 下的 schema。

## 支持语言

- `zh-CN`：简体中文，默认源语言。
- `zh-TW`：繁体中文。
- `en-US`：英文。
- `ja-JP`：日语。
- `ko-KR`：韩语。
