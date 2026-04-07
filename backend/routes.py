from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import json
from database import get_db, get_redis
from auth import get_current_user
from turnstile import verify_turnstile
from models import User
from schemas import TurnstileRequest, ScoreRequest

router = APIRouter()

BATCH_SIZE = 10


@router.post("/api/images/batch")
async def get_image_batch(
    request: Request,
    req: TurnstileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host
    if not await verify_turnstile(req.turnstile_token, ip):
        raise HTTPException(403, "人机验证失败")

    # 获取尚未被任何人打分的图片（score_count = 0 表示无人标注过）
    query = """
        SELECT id, r2_url FROM images
        WHERE COALESCE(deleted, FALSE) = FALSE
        AND COALESCE(score_count, 0) = 0
        ORDER BY RANDOM()
        LIMIT :limit
    """
    result = await db.execute(text(query), {"limit": BATCH_SIZE})
    images = result.fetchall()

    if not images:
        return {"images": [], "message": "所有图片已完成标注，暂无更多图片"}

    return {"images": [{"id": r.id, "url": r.r2_url} for r in images]}


@router.post("/api/score")
async def submit_score(
    req: ScoreRequest,
    user: User = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
):
    # Use a short-lived Redis lock to prevent accidental double clicks.
    # Long-term duplicate protection is enforced by the database unique index.
    dedup_key = f"dedup:submit:{user.id}:{req.image_id}"
    was_locked = await r.set(dedup_key, "1", ex=10, nx=True)
    if not was_locked:
        raise HTTPException(409, "Already scored this image")

    payload = {
        "image_id": req.image_id,
        "user_id": user.id,
        "aesthetic_score": req.aesthetic_score,
        "completeness_score": req.completeness_score,
    }
    await r.lpush("score_queue", json.dumps(payload))

    return {"status": "ok"}


@router.get("/api/my-scores")
async def get_my_scores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT image_id FROM scores WHERE user_id = :uid"),
        {"uid": user.id}
    )
    rows = result.fetchall()
    return {"scored_image_ids": [r.image_id for r in rows]}


@router.get("/api/my-stats")
async def get_my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("""
        SELECT
            COUNT(*) as total_scores,
            COUNT(CASE WHEN submitted_at >= NOW() - INTERVAL '1 day' THEN 1 END) as today_scores
        FROM scores
        WHERE user_id = :uid
    """), {"uid": user.id})
    row = result.fetchone()
    return {
        "total_scores": row.total_scores,
        "today_scores": row.today_scores,
        "username": user.username
    }
