import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import Score, User
from schemas import NextTaskRequest, ScoreRequest, TaskScoreRequest, TurnstileRequest
from turnstile import verify_turnstile

router = APIRouter()

BATCH_SIZE = 10
TASK_EXPIRY_MINUTES = 10
MAX_ACTIVE_TASKS_PER_USER = 2


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _build_image_url(row) -> str:
    if getattr(row, "public_url", None):
        return row.public_url
    if getattr(row, "r2_url", None):
        return row.r2_url

    object_key = getattr(row, "object_key", None)
    public_base = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
    if object_key and public_base:
        return f"{public_base}/{object_key.lstrip('/')}"

    if object_key:
        return f"http://localhost:8080/images/{object_key.lstrip('/')}"

    raise HTTPException(500, "Image URL is not configured")


async def _verify_turnstile_or_reject(token: str, request: Request) -> None:
    ip = request.client.host if request.client else ""
    if not await verify_turnstile(token, ip):
        raise HTTPException(403, "Turnstile verification failed")


async def _verify_turnstile_if_present(token: str, request: Request) -> None:
    if token:
        await _verify_turnstile_or_reject(token, request)


async def _expire_user_tasks(db: AsyncSession, user_id: int) -> None:
    expired_rows = await db.execute(
        text(
            """
            UPDATE annotation_tasks
            SET status = 'expired'
            WHERE user_id = :user_id
              AND status = 'assigned'
              AND expires_at <= NOW()
            RETURNING image_id
            """
        ),
        {"user_id": user_id},
    )
    expired_image_ids = [row.image_id for row in expired_rows.fetchall()]

    if expired_image_ids:
        await db.execute(
            text(
                """
                UPDATE images AS i
                SET status = 'pending'
                WHERE i.id = ANY(:image_ids)
                  AND COALESCE(i.deleted, FALSE) = FALSE
                  AND COALESCE(i.score_count, 0) = 0
                  AND NOT EXISTS (
                      SELECT 1
                      FROM annotation_tasks t
                      WHERE t.image_id = i.id
                        AND t.status = 'assigned'
                        AND t.expires_at > NOW()
                  )
                """
            ),
            {"image_ids": expired_image_ids},
        )
    await db.commit()


async def _normalize_image_statuses(db: AsyncSession) -> None:
    await db.execute(
        text(
            """
            UPDATE images AS i
            SET status = 'pending'
            WHERE COALESCE(i.deleted, FALSE) = FALSE
              AND COALESCE(i.score_count, 0) = 0
              AND COALESCE(i.status, 'pending') <> 'disabled'
              AND NOT EXISTS (
                  SELECT 1
                  FROM annotation_tasks t
                  WHERE t.image_id = i.id
                    AND t.status = 'assigned'
                    AND t.expires_at > NOW()
              )
            """
        )
    )
    await db.execute(
        text(
            """
            UPDATE images
            SET status = 'completed'
            WHERE COALESCE(score_count, 0) > 0
              AND COALESCE(status, 'pending') <> 'disabled'
            """
        )
    )
    await db.commit()


async def _get_active_tasks(db: AsyncSession, user_id: int):
    result = await db.execute(
        text(
            """
            SELECT
                t.id AS task_id,
                t.image_id,
                t.assigned_at,
                t.expires_at,
                i.object_key,
                i.public_url,
                i.r2_url
            FROM annotation_tasks t
            JOIN images i ON i.id = t.image_id
            WHERE t.user_id = :user_id
              AND t.status = 'assigned'
              AND t.expires_at > NOW()
              AND COALESCE(i.deleted, FALSE) = FALSE
            ORDER BY t.assigned_at ASC, t.id ASC
            """
        ),
        {"user_id": user_id},
    )
    return result.fetchall()


async def _assign_new_task(db: AsyncSession, user_id: int):
    image_result = await db.execute(
        text(
            """
            WITH candidate AS (
                SELECT i.id
                FROM images i
                WHERE COALESCE(i.deleted, FALSE) = FALSE
                  AND COALESCE(i.score_count, 0) = 0
                  AND COALESCE(i.status, 'pending') <> 'disabled'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM annotation_tasks t
                      WHERE t.image_id = i.id
                        AND t.status = 'assigned'
                        AND t.expires_at > NOW()
                  )
                ORDER BY RANDOM()
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE images AS i
            SET status = 'assigned'
            FROM candidate
            WHERE i.id = candidate.id
            RETURNING i.id, i.object_key, i.public_url, i.r2_url
            """
        )
    )
    image = image_result.fetchone()
    if not image:
        return None

    expires_at = _now_utc() + timedelta(minutes=TASK_EXPIRY_MINUTES)
    task_result = await db.execute(
        text(
            """
            INSERT INTO annotation_tasks (image_id, user_id, status, assigned_at, expires_at)
            VALUES (:image_id, :user_id, 'assigned', NOW(), :expires_at)
            RETURNING id AS task_id, image_id, assigned_at, expires_at
            """
        ),
        {
            "image_id": image.id,
            "user_id": user_id,
            "expires_at": expires_at,
        },
    )
    task_row = task_result.fetchone()
    await db.commit()

    return {
        "task_id": task_row.task_id,
        "image_id": task_row.image_id,
        "image_url": _build_image_url(image),
        "object_key": image.object_key,
        "assigned_at": task_row.assigned_at,
        "expires_at": task_row.expires_at,
    }


def _serialize_task(row) -> dict:
    return {
        "task_id": row.task_id,
        "image_id": row.image_id,
        "image_url": _build_image_url(row),
        "object_key": getattr(row, "object_key", None),
        "assigned_at": row.assigned_at,
        "expires_at": row.expires_at,
    }


async def _select_task_for_user(db: AsyncSession, user_id: int, current_task_id: int | None):
    await _expire_user_tasks(db, user_id)
    await _normalize_image_statuses(db)
    active_tasks = await _get_active_tasks(db, user_id)

    if current_task_id is not None:
        for task in active_tasks:
            if task.task_id != current_task_id:
                return _serialize_task(task)
        if len(active_tasks) < MAX_ACTIVE_TASKS_PER_USER:
            return await _assign_new_task(db, user_id)
        for task in active_tasks:
            if task.task_id == current_task_id:
                return _serialize_task(task)
        return None

    if active_tasks:
        return _serialize_task(active_tasks[0])

    return await _assign_new_task(db, user_id)


async def _persist_score(db: AsyncSession, payload: dict, *, mark_task_submitted: bool) -> None:
    insert_sql = (
        insert(Score)
        .values(payload)
        .on_conflict_do_nothing(index_elements=["user_id", "image_id"])
        .returning(Score.image_id)
    )
    result = await db.execute(insert_sql)
    inserted = result.fetchone()
    if not inserted:
        await db.rollback()
        raise HTTPException(409, "Already scored this image")

    image_id = payload["image_id"]

    await db.execute(
        text(
            """
            UPDATE images
            SET score_count = COALESCE(score_count, 0) + 1,
                status = 'completed'
            WHERE id = :image_id
            """
        ),
        {"image_id": image_id},
    )

    if mark_task_submitted and payload.get("task_id") is not None:
        await db.execute(
            text(
                """
                UPDATE annotation_tasks
                SET status = 'submitted', submitted_at = NOW()
                WHERE id = :task_id
                """
            ),
            {"task_id": payload["task_id"]},
        )

    await db.commit()


@router.post("/api/tasks/next")
async def get_next_task(
    request: Request,
    req: NextTaskRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_turnstile_if_present(req.turnstile_token, request)
    task = await _select_task_for_user(db, user.id, req.current_task_id)
    if not task:
        return {"task": None, "message": "All images have been annotated"}
    return {"task": task}


@router.post("/api/tasks/{task_id}/submit")
async def submit_task_score(
    task_id: int,
    req: TaskScoreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task_result = await db.execute(
        text(
            """
            SELECT image_id, status, expires_at
            FROM annotation_tasks
            WHERE id = :task_id AND user_id = :user_id
            """
        ),
        {"task_id": task_id, "user_id": user.id},
    )
    task_row = task_result.fetchone()
    if not task_row:
        raise HTTPException(404, "Task not found")
    if task_row.status != "assigned":
        raise HTTPException(409, "Task is no longer assignable")
    if task_row.expires_at <= _now_utc():
        await db.execute(
            text("UPDATE annotation_tasks SET status = 'expired' WHERE id = :task_id"),
            {"task_id": task_id},
        )
        await db.commit()
        raise HTTPException(409, "Task has expired")
    if task_row.image_id != req.image_id:
        raise HTTPException(400, "Image does not match task")

    payload = {
        "task_id": task_id,
        "image_id": req.image_id,
        "user_id": user.id,
        "aesthetic_score": req.aesthetic_score,
        "completeness_score": req.completeness_score,
    }
    await _persist_score(db, payload, mark_task_submitted=True)
    return {"status": "ok"}


@router.post("/api/images/batch")
async def get_image_batch(
    request: Request,
    req: TurnstileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _verify_turnstile_or_reject(req.turnstile_token, request)
    await _normalize_image_statuses(db)

    result = await db.execute(
        text(
            """
            SELECT id, object_key, public_url, r2_url
            FROM images
            WHERE COALESCE(deleted, FALSE) = FALSE
              AND COALESCE(score_count, 0) = 0
              AND COALESCE(status, 'pending') <> 'disabled'
            ORDER BY RANDOM()
            LIMIT :limit
            """
        ),
        {"limit": BATCH_SIZE},
    )
    images = result.fetchall()

    if not images:
        return {"images": [], "message": "All images have been annotated"}

    return {"images": [{"id": row.id, "url": _build_image_url(row)} for row in images]}


@router.post("/api/score")
async def submit_score(
    req: ScoreRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = {
        "task_id": None,
        "image_id": req.image_id,
        "user_id": user.id,
        "aesthetic_score": req.aesthetic_score,
        "completeness_score": req.completeness_score,
    }
    await _persist_score(db, payload, mark_task_submitted=False)
    return {"status": "ok"}


@router.get("/api/my-scores")
async def get_my_scores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT image_id FROM scores WHERE user_id = :uid"),
        {"uid": user.id},
    )
    rows = result.fetchall()
    return {"scored_image_ids": [r.image_id for r in rows]}


@router.get("/api/my-stats")
async def get_my_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_scores,
                COUNT(CASE WHEN submitted_at >= NOW() - INTERVAL '1 day' THEN 1 END) AS today_scores
            FROM scores
            WHERE user_id = :uid
            """
        ),
        {"uid": user.id},
    )
    row = result.fetchone()
    return {
        "total_scores": row.total_scores,
        "today_scores": row.today_scores,
        "username": user.username,
    }
