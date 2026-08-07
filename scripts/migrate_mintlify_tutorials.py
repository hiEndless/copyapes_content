#!/usr/bin/env python3
"""Migrate Mintlify copyapes docs into copyapes_content tutorials."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

SRC_ROOT = Path("/Users/lichaoyuan/Desktop/docs")
SRC_DOCS = SRC_ROOT / "copyapes"
SRC_IMAGES = SRC_ROOT / "images" / "copyapes"
CONTENT_ROOT = Path("/Users/lichaoyuan/Desktop/copytrade/copyapes/copyapes_content")
OUT_DIR = CONTENT_ROOT / "zh-CN" / "tutorials"
IMG_OUT = CONTENT_ROOT / "assets" / "images" / "shared" / "tutorials"
MANIFEST_PATH = CONTENT_ROOT / "assets" / "manifests" / "images.json"
INDEX_PATH = CONTENT_ROOT / "content_index.json"

# From docs.json "跟单猿使用教程" navigation
NAV_PAGES = [
    "protocol",
    "step",
    "task-info",
    "exchange/okx",
    "exchange/binance",
    "exchange/gate",
    "exchange/add",
    "okx/open",
    "okx/person",
    "binance/open",
    "binance/close",
    "vip/bicoin",
    "vip/hot",
    "vip/cookie",
    "vip/ws",
    "other/add-cookie",
    "other/grab",
    "other/partner",
]

TAG_BY_PREFIX = {
    "exchange": "exchange",
    "okx": "okx",
    "binance": "binance",
    "vip": "vip",
    "other": "other",
}


def extract_title(raw: str, fallback: str) -> str:
    m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', raw, re.M)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return fallback


def strip_frontmatter(raw: str) -> str:
    if not raw.startswith("---"):
        return raw
    end = raw.find("\n---", 3)
    if end == -1:
        return raw
    return raw[end + 4 :].lstrip("\n")


def convert_body(body: str) -> str:
    # Internal links
    body = body.replace("](/copyapes/", "](/docs/")
    body = re.sub(r"\]\(/docs/copyapes/", "](/docs/", body)

    # Markdown images
    body = re.sub(
        r"!\[([^\]]*)\]\(/images/copyapes/([^)]+)\)",
        r"![\1](@asset:tutorials/\2)",
        body,
    )

    # JSX img src
    body = re.sub(
        r'src="/images/copyapes/([^"]+)"',
        r'src="@asset:tutorials/\1"',
        body,
    )

    # Mintlify callouts
    body = body.replace("<Tip>", '<Note title="提示" type="note">')
    body = body.replace("</Tip>", "</Note>")
    body = body.replace("<Info>", '<Note title="说明" type="note">')
    body = body.replace("</Info>", "</Note>")
    body = body.replace("<Warning>", '<Note title="注意" type="warning">')
    body = body.replace("</Warning>", "</Note>")

    # iframe protocol-relative -> https
    body = body.replace('src="//', 'src="https://')

    return body


def convert_steps_carefully(body: str) -> str:
    """Convert Mintlify Steps/Step to our Step/StepItem."""

    def repl_steps(match: re.Match[str]) -> str:
        inner = match.group(1)
        inner = re.sub(r"<Step(\s[^>]*)?>", r"<StepItem\1>", inner)
        inner = inner.replace("</Step>", "</StepItem>")
        return f"<Step>\n{inner}\n</Step>"

    return re.sub(r"<Steps>([\s\S]*?)</Steps>", repl_steps, body)


def build_frontmatter(slug: str, title: str, order: int) -> str:
    prefix = slug.split("/", 1)[0]
    tag = TAG_BY_PREFIX.get(prefix, "getting-started")
    # Keep nav order when sorting by published_at desc: earlier pages newer
    published = date(2026, 8, 20) - timedelta(days=order)
    desc = title
    return f"""---
slug: {slug}
title: "{title}"
description: "{desc}"
category: tutorial
tags:
  - {tag}
source_locale: zh-CN
translation_status: source
published_at: {published.isoformat()}
updated_at: {published.isoformat()}
status: published
---
"""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def migrate_images() -> dict:
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    for img in sorted(SRC_IMAGES.iterdir()):
        if not img.is_file() or img.name.startswith("."):
            continue
        dest = IMG_OUT / img.name
        shutil.copy2(img, dest)
        key = f"shared/tutorials/{img.name}"
        local_path = f"assets/images/shared/tutorials/{img.name}"
        ctype = mimetypes.guess_type(img.name)[0] or "application/octet-stream"
        manifest[key] = {
            "local_path": local_path,
            "r2_key": f"content/images/{local_path.removeprefix('assets/images/')}",
            "url": "",
            "sha256": file_sha256(dest),
            "size": dest.stat().st_size,
            "content_type": ctype,
            "updated_at": date.today().isoformat(),
        }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def migrate_pages() -> list[dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = []

    for order, rel in enumerate(NAV_PAGES):
        src = SRC_DOCS / f"{rel}.mdx"
        if not src.exists():
            print(f"SKIP missing: {src}")
            continue

        raw = src.read_text(encoding="utf-8")
        title = extract_title(raw, rel.split("/")[-1])
        body = strip_frontmatter(raw)
        body = convert_steps_carefully(body)
        body = convert_body(body)

        out_path = OUT_DIR / f"{rel}.mdx"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(build_frontmatter(rel, title, order) + "\n" + body.lstrip() + "\n", encoding="utf-8")

        items.append(
            {
                "type": "tutorials",
                "slug": rel,
                "path": f"tutorials/{rel}.mdx",
                "locales": {"zh-CN": "published"},
            }
        )
        print(f"OK {rel} -> {out_path.relative_to(CONTENT_ROOT)}")

    return items


def update_index(tutorial_items: list[dict]) -> None:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    # Remove old tutorials entries
    index["items"] = {k: v for k, v in index["items"].items() if not k.startswith("tutorials/")}
    for item in tutorial_items:
        index["items"][f"tutorials/{item['slug']}"] = item
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {INDEX_PATH} with {len(tutorial_items)} tutorials")


def main() -> None:
    migrate_images()
    items = migrate_pages()
    update_index(items)
    print(f"Done. pages={len(items)}")


if __name__ == "__main__":
    main()
