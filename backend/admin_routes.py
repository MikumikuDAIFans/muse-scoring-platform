from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from database import get_db, get_redis
from auth import require_admin
from models import User

router = APIRouter()


@router.get("/api/admin/stats")
async def admin_stats(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_redis),
):
    total_images = (await db.execute(
        text("SELECT COUNT(*) FROM images WHERE deleted = FALSE")
    )).scalar()
    # 已标注的不重复图片数（至少被一个用户打过分的图片）
    annotated_images = (await db.execute(
        text("SELECT COUNT(DISTINCT image_id) FROM scores")
    )).scalar()
    total_scores = (await db.execute(
        text("SELECT COUNT(*) FROM scores")
    )).scalar()
    active_today = (await db.execute(text(
        "SELECT COUNT(DISTINCT user_id) FROM scores WHERE submitted_at >= NOW() - INTERVAL '1 day'"
    ))).scalar()
    today_scores = (await db.execute(text(
        "SELECT COUNT(*) FROM scores WHERE submitted_at >= NOW() - INTERVAL '1 day'"
    ))).scalar()
    queue_len = await r.llen("score_queue")
    return {
        "total_images": total_images,
        "annotated_images": annotated_images,
        "total_scores": total_scores,
        "active_users_today": active_today,
        "today_scores": today_scores,
        "redis_queue_length": queue_len,
    }


@router.get("/api/admin/users")
async def admin_users(
    page: int = 1, page_size: int = 50,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(text("""
        SELECT u.username, u.created_at, u.last_login,
               COUNT(s.id) as total_scores,
               COUNT(CASE WHEN s.submitted_at >= NOW() - INTERVAL '1 day' THEN 1 END) as today_scores
        FROM users u
        LEFT JOIN scores s ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY total_scores DESC
        LIMIT :limit OFFSET :offset
    """), {"limit": page_size, "offset": offset})
    rows = result.fetchall()
    total_result = await db.execute(
        text("SELECT CEIL(COUNT(*)::float / :ps)::int FROM users"),
        {"ps": page_size}
    )
    return {
        "users": [dict(r._mapping) for r in rows],
        "total_pages": total_result.scalar()
    }
