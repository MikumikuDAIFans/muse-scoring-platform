from typing import Optional
import json
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, async_session
from models import AuditExport
from auth import require_admin, User
from export_helpers import generate_csv, generate_jsonl

router = APIRouter()


@router.get("/api/export")
async def export_data(
    format: str = "csv",
    start: Optional[str] = None,
    end: Optional[str] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 10000,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    params = {}
    if start:
        conditions.append("s.submitted_at >= :start")
        params["start"] = datetime.fromisoformat(start) if "T" in start else datetime.strptime(start, "%Y-%m-%d")
    if end:
        conditions.append("s.submitted_at <= :end")
        params["end"] = datetime.fromisoformat(end) if "T" in end else datetime.strptime(end, "%Y-%m-%d")
    if user_id:
        conditions.append("s.user_id = :user_id")
        params["user_id"] = user_id

    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    offset = (page - 1) * page_size

    query = f"""
        SELECT u.username, s.image_id, s.aesthetic_score, s.completeness_score, s.submitted_at
        FROM scores s
        JOIN users u ON s.user_id = u.id
        WHERE {where_clause}
        ORDER BY s.submitted_at
        LIMIT :limit OFFSET :offset
    """
    params.update({"limit": page_size, "offset": offset})

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    await db.execute(
        text("""
            INSERT INTO audit_exports (admin_id, export_type, filters, record_count)
            VALUES (:admin_id, :export_type, :filters, :record_count)
        """),
        {
            "admin_id": _admin.id,
            "export_type": format,
            "filters": json.dumps({"start": start, "end": end, "user_id": user_id, "page": page}),
            "record_count": len(rows),
        }
    )
    await db.commit()

    if format == "csv":
        return StreamingResponse(
            generate_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=scores_export_p{page}.csv"}
        )
    else:
        return StreamingResponse(
            generate_jsonl(rows),
            media_type="application/x-jsonlines",
            headers={"Content-Disposition": f"attachment; filename=scores_export_p{page}.jsonl"}
        )
