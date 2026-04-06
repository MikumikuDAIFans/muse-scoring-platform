import csv
import io
import json


async def generate_csv(rows):
    """异步CSV生成器（流式）"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "image_id", "aesthetic_score", "completeness_score", "submitted_at"])
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)
    for row in rows:
        writer.writerow([row.username, row.image_id, row.aesthetic_score, row.completeness_score, row.submitted_at])
        data = output.getvalue()
        output.seek(0)
        output.truncate(0)
        yield data


async def generate_jsonl(rows):
    """异步JSONL生成器（流式）"""
    for row in rows:
        yield json.dumps({
            "username": row.username,
            "image_id": row.image_id,
            "aesthetic_score": row.aesthetic_score,
            "completeness_score": row.completeness_score,
            "submitted_at": str(row.submitted_at)
        }, ensure_ascii=False) + "\n"
