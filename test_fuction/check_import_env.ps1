$ErrorActionPreference = "Stop"

Set-Location "e:\MuseProject\backend"

$env:ADMIN_PASSWORD = "muse-scoring-platform-114514"
$env:ADMIN_USERNAME = "muse_admin"
$env:ALLOWED_ORIGINS = "https://muse.displace-ai.top/"
$env:DATABASE_URL = "postgresql://neondb_owner:npg_XPK2uBJVmc0Q@ep-wild-poetry-ancvf66s.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"
$env:JWT_SECRET = "f9b8c7d6e5a4f3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8"
$env:R2_ACCESS_KEY_ID = "60349f056ca38dc63a3ba55dbdca5768"
$env:R2_ACCOUNT_ID = "f77aaa224e2bb71a9406bb1bc0fd70d1"
$env:R2_BUCKET = "muse-images"
$env:R2_PUBLIC_URL = "https://muse-images.displace-ai.top"
$env:R2_SECRET_ACCESS_KEY = "e9fe8bf372f28bbb99a7397459f0ec41356d0e98d49bc893d8adb207379ed4ea"
$env:REDIS_URL = "rediss://default:gQAAAAAAAT4ZAAIncDI3MDIxNTg2MDczN2Q0NGEwYjAwMWFlMTkzNWZjZWI1YXAyODE0MzM@feasible-wren-81433.upstash.io:6379"
$env:TURNSTILE_SECRET_KEY = "0x4AAAAAAC1VSKzByQBgC4B2YdeIcsefK9o"
$env:TURNSTILE_SITE_KEY = "0x4AAAAAAC1VSBUt45AYBPOf"
$env:IMAGE_FOLDER = "e:\MuseProject\images"

@'
import os
import asyncio
import asyncpg
import boto3
from botocore.config import Config

async def check_db():
    db_url = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(db_url)
    try:
        val = await conn.fetchval("SELECT 1")
        print(f"[OK] DATABASE_URL connected, SELECT 1 => {val}")
    finally:
        await conn.close()

def check_folder():
    folder = os.environ["IMAGE_FOLDER"]
    if not os.path.isdir(folder):
        raise RuntimeError(f"Image folder does not exist: {folder}")
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    print(f"[OK] image folder exists: {folder}")
    print(f"[OK] image count: {len(files)}")

def check_r2():
    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key_id = os.environ["R2_ACCESS_KEY_ID"]
    secret_access_key = os.environ["R2_SECRET_ACCESS_KEY"]
    bucket = os.environ["R2_BUCKET"]
    public_url = os.environ["R2_PUBLIC_URL"]

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version="s3v4"),
    )
    client.head_bucket(Bucket=bucket)
    print(f"[OK] R2 bucket reachable: {bucket}")
    print(f"[OK] R2 public url: {public_url}")

async def main():
    check_folder()
    await check_db()
    check_r2()
    print("[OK] All checks passed. You can now run: python import_images.py")

asyncio.run(main())
'@ | python -

Read-Host "Check complete. Press Enter to exit"
