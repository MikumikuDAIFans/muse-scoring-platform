import json
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from database import engine, async_session, redis
from models import Score

logger = logging.getLogger("worker")

BATCH_SIZE = 1000
POLL_INTERVAL = 2  # 秒


async def process_scores():
    """Worker主循环：从Redis队列批量消费并写入PostgreSQL"""
    while True:
        pipe = redis.pipeline()
        await pipe.lrange("score_queue", 0, BATCH_SIZE - 1)
        await pipe.ltrim("score_queue", BATCH_SIZE, -1)
        results = await pipe.execute()
        items = results[0]

        if not items:
            await asyncio.sleep(POLL_INTERVAL)
            continue

        records = [json.loads(i) for i in items]

        try:
            async with async_session() as session:
                # Build raw SQL for batch insert with ON CONFLICT
                values_list = []
                params = {}
                for i, rec in enumerate(records):
                    prefix = f"v{i}_"
                    values_list.append(f"(:{prefix}image_id, :{prefix}user_id, :{prefix}aesthetic_score, :{prefix}completeness_score, NOW())")
                    params[f"{prefix}image_id"] = rec["image_id"]
                    params[f"{prefix}user_id"] = rec["user_id"]
                    params[f"{prefix}aesthetic_score"] = rec["aesthetic_score"]
                    params[f"{prefix}completeness_score"] = rec["completeness_score"]

                values_clause = ", ".join(values_list)
                insert_sql = text(f"""
                    INSERT INTO scores (image_id, user_id, aesthetic_score, completeness_score, submitted_at)
                    VALUES {values_clause}
                    ON CONFLICT (user_id, image_id) DO NOTHING
                    RETURNING image_id
                """)
                result = await session.execute(insert_sql, params)
                inserted_ids = [row[0] for row in result.fetchall()]

                if inserted_ids:
                    # 使用 DISTINCT 防止重试时重复计数
                    await session.execute(
                        text("""
                            UPDATE images
                            SET score_count = COALESCE(score_count, 0) + 1
                            WHERE id IN (SELECT DISTINCT unnest(:ids))
                        """),
                        {"ids": list(set(inserted_ids))}
                    )

                await session.commit()

                pipe = redis.pipeline()
                for r in records:
                    pipe.sadd(f"user:{r['user_id']}:scored", str(r["image_id"]))
                await pipe.execute()

        except Exception as e:
            await redis.lpush("score_queue", *items)
            logger.error(f"DB write failed, items pushed back: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_scores())
