"""批量导入图片元数据到 PostgreSQL"""
import asyncio
import asyncpg
import os


async def import_images(folder_path: str, db_url: str):
    conn = await asyncpg.connect(db_url)
    image_id = 1

    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(('.webp', '.jpg', '.png')):
            r2_url = f"http://localhost:8080/images/{filename}"
            await conn.execute(
                "INSERT INTO images (id, r2_url) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
                image_id, r2_url
            )
            image_id += 1
            if image_id % 10 == 0:
                print(f"Imported {image_id - 1} images...")

    await conn.close()
    print(f"Done! Total: {image_id - 1} images")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scoring")
    folder = os.getenv("IMAGE_FOLDER", "./images")
    asyncio.run(import_images(folder, db_url))
