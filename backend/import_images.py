"""批量导入图片到 Cloudflare R2 并记录元数据到 PostgreSQL"""
import asyncio
import asyncpg
import os
import boto3
from botocore.config import Config


def get_r2_client():
    """获取 Cloudflare R2 客户端"""
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    
    if not all([account_id, access_key_id, secret_access_key]):
        return None
    
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
    
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version='s3v4')
    )


def upload_to_r2(r2_client, file_path: str, object_name: str, bucket: str) -> str:
    """上传图片到 R2 并返回公开 URL"""
    public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
    
    r2_client.upload_file(
        file_path,
        bucket,
        object_name,
        ExtraArgs={'ContentType': 'image/webp' if object_name.endswith('.webp') else 
                   'image/jpeg' if object_name.endswith('.jpg') else 'image/png'}
    )
    
    return f"{public_url}/{object_name}"


async def import_images(folder_path: str, db_url: str):
    conn = await asyncpg.connect(db_url)
    r2_client = get_r2_client()
    r2_bucket = os.getenv("R2_BUCKET", "muse-images")
    use_r2 = r2_client is not None
    
    if use_r2:
        print("🚀 生产模式: 图片将上传到 Cloudflare R2")
    else:
        print("⚠️  开发模式: 使用本地 URL (请配置 R2_* 环境变量以启用生产模式)")
    
    image_id = 1

    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(('.webp', '.jpg', '.png')):
            file_path = os.path.join(folder_path, filename)
            
            if use_r2:
                # 生产模式: 上传到 R2
                r2_url = upload_to_r2(r2_client, file_path, filename, r2_bucket)
            else:
                # 开发模式: 使用本地 URL
                r2_url = f"http://localhost:8080/images/{filename}"
            
            await conn.execute(
                """
                INSERT INTO images (id, r2_url, score_count, deleted)
                VALUES ($1, $2, 0, FALSE)
                ON CONFLICT (id) DO UPDATE
                SET r2_url = EXCLUDED.r2_url,
                    score_count = COALESCE(images.score_count, 0),
                    deleted = COALESCE(images.deleted, FALSE)
                """,
                image_id, r2_url,
            )
            image_id += 1
            if image_id % 10 == 0:
                print(f"Imported {image_id - 1} images...")

    await conn.close()
    print(f"Done! Total: {image_id - 1} images")
    if use_r2:
        print(f"✅ 所有图片已上传到 R2 Bucket: {r2_bucket}")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scoring")
    folder = os.getenv("IMAGE_FOLDER", "./images")
    asyncio.run(import_images(folder, db_url))
