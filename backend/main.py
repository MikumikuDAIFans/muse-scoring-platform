import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from database import engine, async_session
from models import Base
from auth import hash_password
from auth_routes import router as auth_router
from routes import router as main_router
from admin_routes import router as admin_router
from export_routes import router as export_router
from health import router as health_router
from middleware import register_exception_handlers
from redis_worker import process_scores

app = FastAPI(title="Muse Scoring Platform")

# CORS
# 生产环境通过 ALLOWED_ORIGINS 环境变量配置允许的域名，逗号分隔
# 默认值仅用于本地开发，生产环境务必设置具体域名
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 注册异常处理器
register_exception_handlers(app)

# 注册路由
app.include_router(auth_router)
app.include_router(main_router)
app.include_router(admin_router)
app.include_router(export_router)
app.include_router(health_router)


@app.on_event("startup")
async def startup():
    """启动时初始化数据库和默认管理员，并启动Redis Worker"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    admin_user = os.getenv("ADMIN_USERNAME")
    admin_pass = os.getenv("ADMIN_PASSWORD")
    if admin_user and admin_pass:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT id FROM users WHERE username = :name"),
                {"name": admin_user}
            )
            if not result.first():
                await session.execute(
                    text("INSERT INTO users (username, password_hash, role) VALUES (:name, :hash, 'admin')"),
                    {"name": admin_user, "hash": hash_password(admin_pass)}
                )
                await session.commit()
                print(f"Admin user '{admin_user}' created.")

    # Start Redis Worker as background task
    asyncio.create_task(process_scores())
    print("Redis Worker started as background task.")


@app.on_event("shutdown")
async def shutdown():
    """优雅关闭"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down, closing connections...")
    await engine.dispose()
    from database import redis
    await redis.close()
    logger.info("Shutdown complete.")
