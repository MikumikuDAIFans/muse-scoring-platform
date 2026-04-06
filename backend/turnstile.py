import httpx
import os

TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET_KEY", "")
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str, remote_ip: str) -> bool:
    if not TURNSTILE_SECRET:
        return True  # 开发模式跳过验证
    async with httpx.AsyncClient() as client:
        resp = await client.post(VERIFY_URL, data={
            "secret": TURNSTILE_SECRET,
            "response": token,
            "remoteip": remote_ip,
        })
        result = resp.json()
        return result.get("success", False)
