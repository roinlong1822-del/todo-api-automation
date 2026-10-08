"""数据库连接层(★ 任务 1:你来实现)。

必须提供(名字固定,路由层与 seed 已按此调用):
    DATABASE_URL : 从环境变量读,默认 "sqlite:///./api_server.db"
    Base         : DeclarativeBase 子类,供 models 继承(已给出,别改名)
    engine       : create_engine(DATABASE_URL, ...)
                   sqlite 需要 connect_args={"check_same_thread": False}
    SessionLocal : sessionmaker(bind=engine, autoflush=False, autocommit=False)
    get_db()     : FastAPI 依赖,产出一个 Session,请求结束务必 close
    init_db()    : 建表(create_all);表已存在时不会重复建

最小知识(这几行就够跑起来):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import DeclarativeBase, sessionmaker
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

自测(改完数据库层就能跑):
    python -c "from api_server.app.database import init_db, Base; init_db(); print(sorted(Base.metadata.tables))"
    # 期望输出 ['todos', 'users']
"""

import os

from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api_server.db")


class Base(DeclarativeBase):
    """所有 ORM 模型的基类(已给出)。"""


# ------------------------------------------------------------------
# TODO(任务 1):把下面三个补完
# ------------------------------------------------------------------
engine = None          # ← 替换为 create_engine(...)
SessionLocal = None    # ← 替换为 sessionmaker(...)


def get_db():
    """FastAPI 依赖:每个请求一个 Session。提示:用 yield + finally close。"""
    raise NotImplementedError("实现 get_db():yield Session,finally 里 close")


def init_db() -> None:
    """建表。提示:先 `from api_server.app import models` 注册模型,再 create_all。"""
    raise NotImplementedError("实现 init_db()")
