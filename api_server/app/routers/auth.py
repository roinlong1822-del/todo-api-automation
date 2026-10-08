"""POST /login —— 登录发 token。"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from api_server.app import crud
from api_server.app.auth import create_token, verify_password
from api_server.app.database import get_db
from api_server.app.errors import account_locked, invalid_credentials
from api_server.app.schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])

MAX_FAILED_ATTEMPTS = 3


@router.post("/login", response_model=TokenResponse, summary="登录获取 token")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, payload.username)

    # 用户名不存在:不暴露"用户是否存在",统一按凭据错误处理
    if user is None:
        raise invalid_credentials()

    if user.locked:
        raise account_locked()

    if not verify_password(payload.password, user.password_hash):
        locked = crud.record_login_failure(db, user, MAX_FAILED_ATTEMPTS)
        if locked:
            raise account_locked()
        raise invalid_credentials()

    crud.reset_login_failures(db, user)
    token, expires_at = create_token(user.id)
    response.headers["Token-Expires-At"] = str(expires_at)
    return TokenResponse(token=token, expires_in=max(0, expires_at - int(__import__("time").time())))
