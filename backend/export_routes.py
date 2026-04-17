import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import User, require_admin
from database import get_db
from export_helpers import generate_csv, generate_jsonl

router = APIRouter()


@router.get("/api/export")
async def export_data(
    format: str = "csv",
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    export_format = format.lower()
    if export_format not in {"csv", "jsonl"}:
        raise HTTPException(400, "Unsupported export format")

    result = await db.execute(
        text(
            """
            SELECT
                COALESCE(i.public_url, i.r2_url) AS r2_url,
                s.aesthetic_score,
                s.completeness_score
            FROM scores s
            JOIN images i ON i.id = s.image_id
            ORDER BY s.submitted_at ASC, s.id ASC
            """
        )
    )
    rows = result.fetchall()

    await db.execute(
        text(
            """
            INSERT INTO audit_exports (admin_id, export_type, filters, record_count)
            VALUES (:admin_id, :export_type, :filters, :record_count)
            """
        ),
        {
            "admin_id": _admin.id,
            "export_type": export_format,
            "filters": json.dumps({"mode": "all_annotated"}),
            "record_count": len(rows),
        },
    )
    await db.commit()

    if export_format == "csv":
        return StreamingResponse(
            generate_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=scored_data.csv"},
        )

    return StreamingResponse(
        generate_jsonl(rows),
        media_type="application/x-jsonlines",
        headers={"Content-Disposition": "attachment; filename=scored_data.jsonl"},
    )
