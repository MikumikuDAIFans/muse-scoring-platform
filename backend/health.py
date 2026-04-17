from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import time
from database import get_db

router = APIRouter()
start_time = time.time()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - start_time,
    }


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(503, f"Not ready: {e}")
