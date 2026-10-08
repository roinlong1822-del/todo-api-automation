"""极简鉴权:PBKDF2 口令散列 + HMAC 签名的自包含 token。

生产请换 bcrypt/argon2 + JWT;这里为了"零外部依赖"用标准库实现。
"""

import base64
import hashlib
import hmac
import os
import time

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from api_server.app import crud
from api_server.app.database import get_db
from api_server.app.errors import unauthorized

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-real-env")
TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))
PBKDF2_ROUNDS = 100_000


# ---------- 口令 ----------
def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, rounds, salt, expected = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(dk.hex(), expected)
    except (ValueError, AttributeError):
        return False


# ---------- token ----------
def create_token(user_id: int, ttl: int = TOKEN_TTL_SECONDS) -> tuple[str, int]:
    """返回 (token, 过期时间戳)。"""
    expires_at = int(time.time()) + ttl
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()
    return token, expires_at


def decode_token(token: str) -> int:
    """解析 token 返回 user_id;签名错/格式错/过期都抛 UNAUTHORIZED。"""
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        user_id_str, expires_at_str, signature = raw.split(":")
        payload = f"{user_id_str}:{expires_at_str}"
        expected = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        if int(expires_at_str) < int(time.time()):
            raise ValueError("expired")
        return int(user_id_str)
    except Exception as exc:  # noqa: BLE001 - 统一转成 401
        raise unauthorized("token 无效或已过期") from exc


# ---------- FastAPI 依赖 ----------
def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """从 Authorization: Bearer <token> 解析当前用户。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized("缺少 Bearer token")
    user_id = decode_token(authorization.split(" ", 1)[1].strip())
    user = crud.get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized("token 对应的用户不存在")
    return user
