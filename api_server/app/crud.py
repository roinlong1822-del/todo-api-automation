"""数据访问层(★ 任务 3:你来实现 —— 面试问"事务/查询"就问这一层)。

约定:
- 每个"写"函数**自己 commit**(事务边界在这一层)
- 所有"查待办"的查询**必须带 `deleted == 0`**
- `list_todos` 返回 `(total, items)`:total 是**过滤后的总数**,不是当前页条数
- 顺带想清楚:为什么查询要用 `.filter()` 而不是把数据全取出来在 Python 里筛?(索引与数据量)

函数清单(签名固定,路由层已调用,别改名字):
"""

from sqlalchemy.orm import Session

from api_server.app.models import Todo, User


def get_user_by_username(db: Session, username: str) -> User | None:
    """按用户名查用户;不存在返回 None。"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """按主键查用户。提示:db.get(User, user_id) 比 filter 更快(走主键缓存)。"""
    return db.get(User, user_id)


def reset_login_failures(db: Session, user: User) -> None:
    """登录成功:把 failed_attempts 归零、解除 locked,并 commit。"""
    login_user = db.get(User, user.id)
    if login_user:
        login_user.failed_attempts = 0
        login_user.locked = False
        db.commit()
    return None


def record_login_failure(db: Session, user: User, max_attempts: int = 3) -> bool:
    """登录失败:failed_attempts += 1;达到 max_attempts 就置 locked=True。
    返回:是否因此被锁定。commit 由本函数负责。
    """
    login_user = db.get(User, user.id)
    if login_user:
        login_user.failed_attempts += 1
        if login_user.failed_attempts >= max_attempts:
            login_user.locked = True
        db.commit()
        return login_user.locked
    return False


def create_todo(db: Session, user_id: int, title: str, priority: int = 1) -> Todo:
    """插入一条待办:status="pending"、deleted=0;commit 后 refresh 拿到自增 id。"""
    add_todo = Todo(user_id=user_id, title=title, priority=priority)
    db.add(add_todo)
    db.commit()
    db.refresh(add_todo)
    return add_todo


def get_todo(db: Session, todo_id: int) -> Todo | None:
    """按 id 查未删除的待办(★ 必须带 deleted == 0,否则软删除用例会失败)。"""
    return db.query(Todo).filter(Todo.id == todo_id, Todo.deleted == 0).first()


def list_todos(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 10,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[int, list[Todo]]:
    """分页查询:只查自己的、未删除的;keyword 走标题模糊匹配;status 精确过滤。
    排序:按 id 升序(保证分页结果稳定、可断言)。
    返回 (total, items)。
    """
    query = db.query(Todo).filter(Todo.user_id == user_id, Todo.deleted == 0)
    if keyword:
        query = query.filter(Todo.title.like(f"%{keyword}%"))
    if status:
        query = query.filter(Todo.status == status)
    total = query.count()
    items = query.order_by(Todo.id.asc()).offset((page - 1) * size).limit(size).all()
    return total, items


def soft_delete_todo(db: Session, todo_id: int) -> bool:
    """软删除:把 deleted 置 1;记录不存在或已删除返回 False。"""
    delete_todo = db.query(Todo).filter(Todo.id == todo_id, Todo.deleted == 0).first()
    if delete_todo:
        delete_todo.deleted = 1
        db.commit()
        db.refresh(delete_todo)
        return True
    return False


def count_by_status(db: Session, user_id: int) -> dict[str, int]:
    """★ 额外练习(做完前面 8 个再做):用 GROUP BY 统计各状态数量。

    期望:{"pending": 2, "done": 1}
    提示:`from sqlalchemy import func` + `db.query(Todo.status, func.count(Todo.id)).group_by(Todo.status)`
    完成后在 routers/todos.py 加一个 `GET /todos/stats` 路由把它暴露出来(自己写路由,3 行)。
    """
    raise NotImplementedError
