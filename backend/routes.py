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
        WHERE deleted = FALSE
        AND score_count = 0
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
    # 原子性地标记已打分，防止并发重复提交
    scored_key = f"user:{user.id}:scored"
    was_added = await r.sadd(scored_key, str(req.image_id))
    if not was_added:
        raise HTTPException(409, "Already scored this image")

    # 设置过期时间，防止僵尸key
    await r.expire(scored_key, 86400 * 7)

    payload = {
        "image_id": req.image_id,
        "user_id": user.id,
        "aesthetic_score": req.aesthetic_score,
        "completeness_score": req.completeness_score,
    }
    await r.lpush("score_queue", json.dumps(payload))
    await r.setex(f"dedup:submit:{user.id}:{req.image_id}", 10, "1")

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
