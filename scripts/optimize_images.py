#!/usr/bin/env python3
"""Optimize images from assets/inbox into assets/images as webp.

Usage:
  pip install -r scripts/requirements.txt
  # put files under assets/inbox/... mirroring final path, e.g.
  #   assets/inbox/shared/blog/my-post-cover.jpg
  # then:
  python scripts/optimize_images.py
  python scripts/optimize_images.py --keep-original
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Missing Pillow. Install with: pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
INBOX_DIR = ROOT / "assets" / "inbox"
IMAGES_DIR = ROOT / "assets" / "images"
ORIGINALS_DIR = ROOT / "assets" / "originals"

COVER_SIZE = (1200, 630)
MAX_EDGE = 1600
WEBP_QUALITY = 80
WEBP_METHOD = 6
COVER_MAX_BYTES = 300 * 1024
BODY_MAX_BYTES = 200 * 1024

INPUT_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".bmp"}
SKIP_NAMES = {".gitkeep", ".DS_Store"}


def is_cover(path: Path) -> bool:
    return bool(re.search(r"(^|[-_])cover(\.|$)", path.stem, flags=re.IGNORECASE))


def iter_inbox_files() -> list[Path]:
    if not INBOX_DIR.exists():
        return []
    files: list[Path] = []
    for path in sorted(INBOX_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES or path.name.startswith("."):
            continue
        if path.suffix.lower() not in INPUT_SUFFIXES:
            continue
        files.append(path)
    return files


def output_path_for(inbox_file: Path) -> Path:
    relative = inbox_file.relative_to(INBOX_DIR)
    return (IMAGES_DIR / relative).with_suffix(".webp")


def load_image(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image


def to_rgb_or_rgba(image: Image.Image) -> Image.Image:
    if image.mode in ("RGB", "RGBA"):
        return image
    if image.mode == "P":
        return image.convert("RGBA" if "transparency" in image.info else "RGB")
    if image.mode in ("LA", "L"):
        return image.convert("RGBA" if image.mode == "LA" else "RGB")
    if image.mode == "CMYK":
        return image.convert("RGB")
    return image.convert("RGBA" if "A" in image.mode else "RGB")


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_max_edge(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    longest = max(width, height)
    if longest <= max_edge:
        return image
    scale = max_edge / float(longest)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def save_webp(image: Image.Image, dest: Path, *, quality: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    params = {
        "format": "WEBP",
        "quality": quality,
        "method": WEBP_METHOD,
    }
    if image.mode == "RGBA":
        params["lossless"] = False
    image.save(dest, **params)


def compress_to_budget(image: Image.Image, dest: Path, *, max_bytes: int) -> int:
    quality = WEBP_QUALITY
    save_webp(image, dest, quality=quality)
    size = dest.stat().st_size

    while size > max_bytes and quality > 50:
        quality -= 5
        save_webp(image, dest, quality=quality)
        size = dest.stat().st_size

    return quality


def archive_original(path: Path) -> Path:
    relative = path.relative_to(INBOX_DIR)
    target = ORIGINALS_DIR / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    path.replace(target)
    return target


def optimize_one(path: Path, *, keep_original: bool, dry_run: bool) -> str:
    dest = output_path_for(path)
    cover = is_cover(path)
    kind = "cover" if cover else "body"

    if dry_run:
        return f"dry  [{kind}] {path.relative_to(ROOT)} -> {dest.relative_to(ROOT)}"

    image = to_rgb_or_rgba(load_image(path))
    if cover:
        image = fit_cover(image, COVER_SIZE)
        budget = COVER_MAX_BYTES
    else:
        image = fit_max_edge(image, MAX_EDGE)
        budget = BODY_MAX_BYTES

    quality = compress_to_budget(image, dest, max_bytes=budget)
    out_size = dest.stat().st_size

    if keep_original:
        archived = archive_original(path)
        trailing = f", archived {archived.relative_to(ROOT)}"
    else:
        path.unlink(missing_ok=True)
        trailing = ", removed inbox original"

    return (
        f"ok   [{kind}] {dest.relative_to(ROOT)} "
        f"{image.size[0]}x{image.size[1]} q={quality} {out_size}B{trailing}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize assets/inbox images into webp under assets/images")
    parser.add_argument("--keep-original", action="store_true", help="Move originals to assets/originals/")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = iter_inbox_files()
    if not files:
        print(f"No images in {INBOX_DIR.relative_to(ROOT)}/")
        print("Put files like: assets/inbox/shared/blog/my-post-cover.jpg")
        return 0

    ok = 0
    for path in files:
        try:
            print(optimize_one(path, keep_original=args.keep_original, dry_run=args.dry_run))
            ok += 1
        except Exception as exc:  # noqa: BLE001 - report and continue batch
            print(f"fail {path.relative_to(ROOT)}: {exc}", file=sys.stderr)

    print(f"done processed={ok}/{len(files)}")
    if not args.dry_run and ok:
        print("Next: python scripts/sync_assets_to_r2.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
