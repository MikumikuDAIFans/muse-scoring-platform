import json
import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from database import async_session, redis
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
                insert_sql = (
                    insert(Score)
                    .values(records)
                    .on_conflict_do_nothing(index_elements=["user_id", "image_id"])
                    .returning(Score.image_id)
                )
                result = await session.execute(insert_sql)
                inserted_ids = [row[0] for row in result.fetchall()]

                if inserted_ids:
                    distinct_ids = list(set(inserted_ids))
                    await session.execute(
                        text("""
                            UPDATE images
                            SET score_count = COALESCE(score_count, 0) + 1
                            WHERE id = ANY(:ids)
                        """),
                        {"ids": distinct_ids}
                    )

                await session.commit()

        except Exception as e:
            await redis.lpush("score_queue", *items)
            logger.error(f"DB write failed, items pushed back: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_scores())
