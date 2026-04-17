import csv
import io
import json


async def generate_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["r2_url", "aesthetic_score", "completeness_score"])
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    for row in rows:
        writer.writerow([row.r2_url, row.aesthetic_score, row.completeness_score])
        data = output.getvalue()
        output.seek(0)
        output.truncate(0)
        yield data


async def generate_jsonl(rows):
    for row in rows:
        yield json.dumps(
            {
                "r2_url": row.r2_url,
                "aesthetic_score": row.aesthetic_score,
                "completeness_score": row.completeness_score,
            },
            ensure_ascii=False,
        ) + "\n"
