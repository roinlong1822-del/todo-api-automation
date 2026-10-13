"""ORM 模型:把 Python 类映射成数据库表。

关键概念:
- `__tablename__`      : 对应数据库里的表名
- `Mapped[int]`        : 类型注解(SQLAlchemy 2.0 用它推断列类型);`Mapped[str]`/`Mapped[bool]`/`Mapped[datetime]`
- `mapped_column(...)` : 列的定义(类型、主键、默认值、索引、外键)
- 只要类继承 Base 并设置了 __tablename__,这张表就自动登记进 Base.metadata
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api_server.app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)          # 主键(自增)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # 唯一 + 索引
    password_hash: Mapped[str] = mapped_column(String(255))             # PBKDF2 散列,不存明文
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)    # 连续失败次数
    locked: Mapped[bool] = mapped_column(Boolean, default=False)        # 是否锁定


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # 属于谁
    title: Mapped[str] = mapped_column(String(100))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(10), default="pending")   # pending / done
    # ★ 软删除标记:0=未删除,1=已删除。所有查询都要带 deleted == 0
    deleted: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)             # 插入时自动填
    )
