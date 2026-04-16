"""Bulk import images into Cloudflare R2 and sync image metadata into PostgreSQL."""

import asyncio
import os

import asyncpg
import boto3
from botocore.config import Config


def get_r2_client():
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")

    if not all([account_id, access_key_id, secret_access_key]):
        return None

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def build_public_url(object_name: str) -> str:
    public_base = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
    if public_base:
        return f"{public_base}/{object_name}"
    return f"http://localhost:8080/images/{object_name}"


def detect_content_type(object_name: str) -> str:
    lowered = object_name.lower()
    if lowered.endswith(".webp"):
        return "image/webp"
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image/jpeg"
    if lowered.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


def upload_to_r2(r2_client, file_path: str, object_name: str, bucket: str) -> str:
    r2_client.upload_file(
        file_path,
        bucket,
        object_name,
        ExtraArgs={"ContentType": detect_content_type(object_name)},
    )
    return build_public_url(object_name)


async def import_images(folder_path: str, db_url: str):
    conn = await asyncpg.connect(db_url)
    r2_client = get_r2_client()
    r2_bucket = os.getenv("R2_BUCKET", "muse-images")
    use_r2 = r2_client is not None

    if use_r2:
        print("Production mode: uploading images to Cloudflare R2")
    else:
        print("Development mode: using local image URLs")

    image_id = 1

    for filename in sorted(os.listdir(folder_path)):
        if not filename.lower().endswith((".webp", ".jpg", ".jpeg", ".png")):
            continue

        file_path = os.path.join(folder_path, filename)
        object_key = filename
        public_url = (
            upload_to_r2(r2_client, file_path, object_key, r2_bucket)
            if use_r2
            else build_public_url(object_key)
        )

        await conn.execute(
            """
            INSERT INTO images (
                id,
                r2_url,
                object_key,
                public_url,
                status,
                score_count,
                deleted
            )
            VALUES ($1, $2, $3, $4, 'pending', 0, FALSE)
            ON CONFLICT (id) DO UPDATE
            SET r2_url = EXCLUDED.r2_url,
                object_key = EXCLUDED.object_key,
                public_url = EXCLUDED.public_url,
                status = CASE
                    WHEN COALESCE(images.score_count, 0) > 0 THEN 'completed'
                    ELSE 'pending'
                END,
                score_count = COALESCE(images.score_count, 0),
                deleted = COALESCE(images.deleted, FALSE)
            """,
            image_id,
            public_url,
            object_key,
            public_url,
        )
        image_id += 1
        if image_id % 10 == 0:
            print(f"Imported {image_id - 1} images...")

    await conn.close()
    print(f"Done! Total: {image_id - 1} images")
    if use_r2:
        print(f"Uploaded to R2 bucket: {r2_bucket}")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scoring")
    folder = os.getenv("IMAGE_FOLDER", "./images")
    asyncio.run(import_images(folder, db_url))
