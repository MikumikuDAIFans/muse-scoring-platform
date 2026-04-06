import re
import os
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User

# JWT_SECRET 必须在生产环境中设置，不允许使用默认值
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    import warnings
    warnings.warn(
        "JWT_SECRET 环境变量未设置！使用不安全的默认值。生产环境请务必配置强随机密钥。",
        RuntimeWarning,
        stacklevel=1
    )
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
WEAK_PASSWORDS = {'password', '123456', '12345678', 'qwerty', 'admin123', 'password123'}


def validate_username(username: str) -> None:
    if not USERNAME_PATTERN.match(username):
        raise HTTPException(400, "用户名仅允许字母、数字、下划线，3-20位")


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(400, "密码至少8位")
    if password.lower() in WEAK_PASSWORDS:
        raise HTTPException(400, "密码过于简单，请更换")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, username: str, role: str = "user") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "username": username, "role": role, "exp": expire}, SECRET_KEY, ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(401, "无效的认证令牌")
    result = await db.execute(text("SELECT * FROM users WHERE id = :uid"), {"uid": user_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(401, "用户不存在")
    user = User(**row._mapping)
    return user


async def check_account_lockout(user: User) -> None:
    """检查账户是否被锁定"""
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(403, f"账户已锁定，请{remaining}分钟后再试")


async def require_admin(user: User = Depends(get_current_user)):
    """验证用户是否为管理员"""
    if user.role != "admin":
        raise HTTPException(403, "需要管理员权限")
    if getattr(user, 'banned', False):
        raise HTTPException(403, "账号已被禁用")
    return user
