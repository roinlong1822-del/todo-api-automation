"""待办的增 / 查 / 列表 / 删(软删除)。"""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from api_server.app import crud
from api_server.app.auth import get_current_user
from api_server.app.database import get_db
from api_server.app.errors import forbidden, not_found
from api_server.app.injection import write_fail_injected
from api_server.app.schemas import TodoCreate, TodoListOut, TodoOut

router = APIRouter(tags=["todos"])


@router.post("/todos", response_model=TodoOut, status_code=201, summary="创建待办")
def create_todo(
    payload: TodoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 故障注入:返回"成功"但不写库 —— 只有双端校验能发现
    if write_fail_injected(request):
        return TodoOut(id=0, title=payload.title, priority=payload.priority, status="pending")

    todo = crud.create_todo(db, current_user.id, payload.title, payload.priority)
    return todo


@router.get("/todos", response_model=TodoListOut, summary="查询待办列表(分页/搜索)")
def list_todos(
    page: int = Query(1, ge=1, description="页码,从 1 开始"),
    size: int = Query(10, ge=1, le=50, description="每页条数,最大 50"),
    keyword: str | None = Query(None, max_length=100, description="标题模糊匹配"),
    status: Literal["pending", "done"] | None = Query(None, description="状态过滤"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total, items = crud.list_todos(db, current_user.id, page, size, keyword, status)
    return TodoListOut(total=total, page=page, size=size, items=[TodoOut.model_validate(i) for i in items])


@router.get("/todos/{todo_id}", response_model=TodoOut, summary="查询单条待办")
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    todo = crud.get_todo(db, todo_id)
    if todo is None:
        raise not_found(f"待办 {todo_id} 不存在")
    if todo.user_id != current_user.id:
        raise forbidden("不能访问他人的待办")
    return todo


@router.delete("/todos/{todo_id}", status_code=204, summary="删除待办(软删除)")
def delete_todo(
    todo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    todo = crud.get_todo(db, todo_id)
    if todo is None:
        raise not_found(f"待办 {todo_id} 不存在")
    if todo.user_id != current_user.id:
        raise forbidden("不能删除他人的待办")

    if write_fail_injected(request):
        return Response(status_code=204)          # 假装删成功,其实没写库

    crud.soft_delete_todo(db, todo_id)
    return Response(status_code=204)
