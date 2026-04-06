from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from database import get_db
from auth import (
    get_current_user, check_account_lockout, create_token,
    verify_password, hash_password, validate_username, validate_password
)
from models import User
from schemas import LoginRequest, RegisterRequest
from turnstile import verify_turnstile

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


@router.post("/api/auth/login")
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM users WHERE username = :name"),
        {"name": req.username}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "用户名或密码错误")

    user = User(**row._mapping)

    if user.banned:
        raise HTTPException(403, "账号已被禁用，请联系管理员")

    await check_account_lockout(user)

    if not verify_password(req.password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            await db.execute(
                text("UPDATE users SET failed_attempts = :fa, locked_until = :lu WHERE id = :uid"),
                {"fa": user.failed_attempts, "lu": user.locked_until, "uid": user.id}
            )
            await db.commit()
            raise HTTPException(403, f"连续{MAX_FAILED_ATTEMPTS}次失败，账户已锁定{LOCKOUT_DURATION_MINUTES}分钟")
        await db.execute(
            text("UPDATE users SET failed_attempts = :fa WHERE id = :uid"),
            {"fa": user.failed_attempts, "uid": user.id}
        )
        await db.commit()
        raise HTTPException(401, "用户名或密码错误")

    await db.execute(
        text("UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = :now WHERE id = :uid"),
        {"now": datetime.now(timezone.utc), "uid": user.id}
    )
    await db.commit()

    return {"token": create_token(user.id, user.username, user.role)}


@router.post("/api/auth/register")
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    validate_username(req.username)
    validate_password(req.password)

    existing = await db.execute(
        text("SELECT id FROM users WHERE username = :name"),
        {"name": req.username}
    )
    if existing.first():
        raise HTTPException(409, "用户名已被占用")

    await db.execute(
        text("INSERT INTO users (username, password_hash) VALUES (:name, :hash) RETURNING id, created_at"),
        {"name": req.username, "hash": hash_password(req.password)}
    )
    result = await db.execute(
        text("SELECT * FROM users WHERE username = :name"),
        {"name": req.username}
    )
    row = result.fetchone()
    user = User(**row._mapping)
    await db.commit()

    return {"token": create_token(user.id, user.username, user.role)}
