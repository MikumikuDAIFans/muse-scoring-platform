"""Sync existing Cloudflare R2 image objects into the images table in batches."""

import asyncio
import os
from urllib.parse import quote

import asyncpg
import boto3
from botocore.config import Config

IMAGE_SUFFIXES = (".webp", ".jpg", ".jpeg", ".png")
DEFAULT_BATCH_SIZE = 1000


def get_r2_client():
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")

    if not all([account_id, access_key_id, secret_access_key]):
        raise RuntimeError("Missing R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY")

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def is_image_key(key: str) -> bool:
    return key.lower().endswith(IMAGE_SUFFIXES)


def build_public_url(object_key: str) -> str:
    public_base = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
    if not public_base:
        raise RuntimeError("R2_PUBLIC_URL is required for syncing public image links")
    return f"{public_base}/{quote(object_key.lstrip('/'), safe='/')}"


def list_r2_image_keys(r2_client, bucket: str, prefix: str):
    paginator = r2_client.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]
            if is_image_key(key):
                keys.append(key)
    return sorted(keys)


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


async def sync_r2_to_db():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scoring")
    bucket = os.getenv("R2_BUCKET", "muse-images")
    prefix = os.getenv("R2_SYNC_PREFIX", "")
    batch_size = int(os.getenv("R2_SYNC_BATCH_SIZE", str(DEFAULT_BATCH_SIZE)))

    r2_client = get_r2_client()
    object_keys = list_r2_image_keys(r2_client, bucket, prefix)
    if not object_keys:
        print("No image objects found in R2 bucket.")
        return

    conn = await asyncpg.connect(db_url)
    existing_rows = await conn.fetch(
        """
        SELECT id, object_key
        FROM images
        WHERE object_key IS NOT NULL
        """
    )
    existing_by_key = {row["object_key"]: row["id"] for row in existing_rows}

    to_insert = []
    to_update = []

    for object_key in object_keys:
        public_url = build_public_url(object_key)
        existing_id = existing_by_key.get(object_key)

        if existing_id is not None:
            to_update.append((existing_id, public_url))
        else:
            to_insert.append((public_url, object_key, public_url))

    updated = 0
    inserted = 0

    async with conn.transaction():
        for batch in chunked(to_update, batch_size):
            await conn.executemany(
                """
                UPDATE images
                SET r2_url = $2,
                    public_url = $2,
                    status = CASE
                        WHEN COALESCE(score_count, 0) > 0 THEN 'completed'
                        WHEN COALESCE(deleted, FALSE) = TRUE THEN 'disabled'
                        ELSE 'pending'
                    END
                WHERE id = $1
                """,
                batch,
            )
            updated += len(batch)
            print(f"Updated {updated}/{len(to_update)} existing rows...")

        for batch in chunked(to_insert, batch_size):
            await conn.executemany(
                """
                INSERT INTO images (
                    r2_url,
                    object_key,
                    public_url,
                    status,
                    score_count,
                    deleted
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    'pending',
                    0,
                    FALSE
                )
                """,
                batch,
            )
            inserted += len(batch)
            print(f"Inserted {inserted}/{len(to_insert)} new rows...")

    await conn.close()
    print(f"Done. Total objects scanned: {len(object_keys)}")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")


if __name__ == "__main__":
    asyncio.run(sync_r2_to_db())
