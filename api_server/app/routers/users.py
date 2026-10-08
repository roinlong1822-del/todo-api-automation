"""GET /users/me —— 当前登录用户。"""

from fastapi import APIRouter, Depends

from api_server.app.auth import get_current_user
from api_server.app.schemas import UserOut

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserOut, summary="获取当前用户")
def read_me(current_user=Depends(get_current_user)):
    return current_user
