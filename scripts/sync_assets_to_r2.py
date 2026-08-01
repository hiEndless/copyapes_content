#!/usr/bin/env python3
"""Upload copyapes_content assets/images to Cloudflare R2 and update images.json.

Uses stdlib only (SigV4). No boto3 required.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import mimetypes
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT / "assets" / "images"
MANIFEST_PATH = ROOT / "assets" / "manifests" / "images.json"
R2_KEY_PREFIX = "content/images"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def require_env(*keys: str) -> dict[str, str]:
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        raise SystemExit(f"Missing env: {', '.join(missing)}")
    return {key: os.environ[key] for key in keys}


def content_type_for(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def iter_image_files() -> list[Path]:
    return sorted(
        path
        for path in IMAGES_DIR.rglob("*")
        if path.is_file() and path.name != ".gitkeep" and not path.name.startswith(".")
    )


def relative_asset_key(path: Path) -> str:
    return path.relative_to(IMAGES_DIR).as_posix()


def r2_key_for(asset_key: str) -> str:
    return f"{R2_KEY_PREFIX}/{asset_key}"


def public_url(public_base: str, key: str) -> str:
    return f"{public_base.rstrip('/')}/{key}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def signing_key(secret: str, datestamp: str, region: str, service: str) -> bytes:
    k_date = sign(("AWS4" + secret).encode("utf-8"), datestamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    return sign(k_service, "aws4_request")


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        if os.environ.get("CF_SSL_INSECURE") == "1":
            context = ssl._create_unverified_context()
            return context
        return ssl.create_default_context()


def put_object(
    *,
    endpoint: str,
    bucket: str,
    key: str,
    body: bytes,
    content_type: str,
    access_key: str,
    secret_key: str,
    region: str = "auto",
) -> None:
    host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    # Path-style: /bucket/key
    url = f"https://{host}/{bucket}/{key}"
    amz_date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    datestamp = amz_date[:8]
    payload_hash = sha256_hex(body)

    canonical_uri = f"/{bucket}/{key}"
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(
        [
            "PUT",
            canonical_uri,
            "",
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    credential_scope = f"{datestamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            sha256_hex(canonical_request.encode("utf-8")),
        ]
    )
    signature = hmac.new(
        signing_key(secret_key, datestamp, region, "s3"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    authorization = (
        "AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    request = urllib.request.Request(
        url,
        data=body,
        method="PUT",
        headers={
            "Content-Type": content_type,
            "Host": host,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
            "Authorization": authorization,
        },
    )

    try:
        with urllib.request.urlopen(request, context=ssl_context()) as response:
            if response.status not in (200, 201):
                raise SystemExit(f"Upload failed ({response.status}) for {key}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Upload failed ({exc.code}) for {key}: {detail}") from exc
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" in str(exc) and os.environ.get("CF_SSL_INSECURE") != "1":
            raise SystemExit(
                "SSL certificate verify failed. Fix macOS certs, or retry with CF_SSL_INSECURE=1"
            ) from exc
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync assets/images to Cloudflare R2")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional dotenv file (e.g. Strapi .env). Only fills missing env vars.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file)
    else:
        load_dotenv(ROOT / ".env")
        load_dotenv(ROOT / ".env.local")

    cfg = require_env(
        "CF_ACCESS_KEY_ID",
        "CF_ACCESS_SECRET",
        "CF_ENDPOINT",
        "CF_BUCKET",
        "CF_PUBLIC_ACCESS_URL",
    )

    files = iter_image_files()
    if not files:
        print("No images under assets/images/")
        return 0

    manifest = load_manifest()
    today = dt.date.today().isoformat()
    uploaded = 0
    skipped = 0

    for path in files:
        asset_key = relative_asset_key(path)
        local_path = f"assets/images/{asset_key}"
        key = r2_key_for(asset_key)
        digest = sha256_file(path)
        size = path.stat().st_size
        ctype = content_type_for(path)
        url = public_url(cfg["CF_PUBLIC_ACCESS_URL"], key)

        existing = manifest.get(asset_key, {})
        if (
            not args.force
            and existing.get("sha256") == digest
            and existing.get("url") == url
            and existing.get("r2_key") == key
        ):
            print(f"skip  {asset_key}")
            skipped += 1
            continue

        print(f"{'dry' if args.dry_run else 'put '} {local_path} -> s3://{cfg['CF_BUCKET']}/{key}")
        if not args.dry_run:
            put_object(
                endpoint=cfg["CF_ENDPOINT"],
                bucket=cfg["CF_BUCKET"],
                key=key,
                body=path.read_bytes(),
                content_type=ctype,
                access_key=cfg["CF_ACCESS_KEY_ID"],
                secret_key=cfg["CF_ACCESS_SECRET"],
            )

        manifest[asset_key] = {
            "local_path": local_path,
            "r2_key": key,
            "url": url,
            "sha256": digest,
            "size": size,
            "content_type": ctype,
            "updated_at": today,
        }
        uploaded += 1

    if not args.dry_run:
        save_manifest(manifest)

    print(f"done uploaded={uploaded} skipped={skipped} manifest={MANIFEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
