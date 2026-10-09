"""数据库连接层。

★ 四个核心对象(名字要记住,项目里到处用):
    Base         : 所有 ORM 模型的父类。继承它 = 把这张表"登记"到 Base.metadata
    Base.metadata: 登记簿(表名 → Table 对象 的字典),未导入模型的表不在里面
    engine       : 连接引擎(管连接池、SQL 方言)。create_all 和 Session 都要用它
    SessionLocal : 会话工厂。调它得到 Session = 一次数据库对话(查询 + 事务)

关系图:
    模型类 ──继承──▶ Base ──登记到──▶ Base.metadata ──create_all(engine)──▶ 数据库中的表
                                                              ▲
    SessionLocal() ──▶ Session ──用 engine 连接───────────────┘  读写这些表
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api_server.db")

# ① 引擎:换 MySQL 只改 DATABASE_URL,代码不动
engine = create_engine(
    DATABASE_URL,
    # sqlite 特有:默认禁止连接跨线程使用,而 uvicorn 是多线程的
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# ② 会话工厂:每个请求/每个测试用例从这里取一个 Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类(类体里不用写任何东西,继承它就够了)。"""


# ③ FastAPI 依赖:请求进来给一个 Session,请求结束关掉
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ④ 建表:把 Base.metadata 里登记的所有表建到数据库
def init_db() -> None:
    # ★ 必须先导入 models,否则表还没被登记,create_all 建出来是空的
    from api_server.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
