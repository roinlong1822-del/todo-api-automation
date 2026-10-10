"""种子数据(★ 任务 4:你来实现,要求幂等 —— 重复执行不产生重复数据)。

要求:
1. 先建表(调用 database.init_db)
2. 三个用户(密码统一 "Passw0rd!",用 auth.hash_password 生成散列):
   - tester        正常账号 → 3 条 todo(2 条 pending、1 条 done)
   - locked_user   locked=True(锁定用例用)
   - other         正常账号 → 1 条 todo(越权用例用)
3. tester 的三条标题:一条英文、一条中文(编码用例用)
4. 幂等:已存在同名用户/同标题待办就跳过

自测:
    python -m api_server.app.seed
    python -c "import sqlite3;c=sqlite3.connect('api_server.db');print(c.execute('select username,locked from users').fetchall());print(c.execute('select count(*) from todos').fetchone())"
    # 期望:三个用户、todos 共 4 条;再跑一次数量不变
"""

import sys

from sqlalchemy.orm import Session

from api_server.app.database import init_db, SessionLocal
from api_server.app import auth
from api_server.app.models import User, Todo
from api_server.app.crud import create_todo


def seed() -> None:
    init_db()
    # TODO(任务 4):插入 3 个用户 + 4 条待办(幂等)
    db = SessionLocal()
    users = [
        {"username": "tester", "password_hash": auth.hash_password("Passw0rd!"), "locked": False},
        {"username": "locked_user", "password_hash": auth.hash_password("Passw0rd!"), "locked": True},
        {"username": "other", "password_hash": auth.hash_password("Passw0rd!"), "locked": False},
    ]
    def create_user_if_not_exists(db: Session, user):
        existing_user = db.query(User).filter(User.username == user["username"]).first()
        if not existing_user:
            new_user = User(**user)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        return existing_user
            # # 添加 todo
            # if new_user.username == "tester":
            #     create_todo(db, new_user.id, "tester todo 1")
            #     create_todo(db, new_user.id, "tester todo 2")
            #     todo_done = create_todo(db, new_user.id, "tester todo 3")
            #     todo_done.status = "done"
            #     db.commit()
            #     db.refresh(todo_done)
            # if new_user.username == "other":
            #     create_todo(db, new_user.id, "other todo 1")

    for user in users:
        db_user = create_user_if_not_exists(db, user)
        # 添加 todo
        if db_user.username == "tester":
            for title, status in [("tester todo 1", "pending"), ("测试待办 2", "pending"), ("tester todo 3", "done")]:
                existing_todo = db.query(Todo).filter(Todo.user_id == db_user.id, Todo.title == title).first()
                if not existing_todo:
                    new_todo = create_todo(db, db_user.id, title)
                    new_todo.status = status
                    db.commit()
                    db.refresh(new_todo)


if __name__ == "__main__":
    sys.exit(seed())
