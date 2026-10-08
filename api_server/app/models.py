"""ORM 模型(★ 任务 2:你来实现)。

要求两张表(字段名/类型必须一致,契约与用例都按这个断言):

users
  id               主键
  username         String(50) 唯一 + 索引
  password_hash    String(255)
  failed_attempts  Integer 默认 0
  locked           Boolean 默认 False

todos
  id         主键
  user_id    外键 → users.id,索引
  title      String(100)
  priority   Integer 默认 1
  status     String(10) 默认 "pending"    # pending / done
  deleted    Integer 默认 0,索引          # ★ 软删除标记:查询必须过滤 deleted == 0
  created_at  DateTime 默认当前时间(UTC)

最小知识(SQLAlchemy 2.0 风格):
    from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
    from sqlalchemy.orm import Mapped, mapped_column
    class X(Base):
        __tablename__ = "x"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

自测:
    python -c "from api_server.app.models import User, Todo; print(User.__tablename__, Todo.__tablename__)"
"""

from api_server.app.database import Base


class User(Base):
    """用户表。"""

    __tablename__ = "users"

    # TODO(任务 2):定义 5 个字段


class Todo(Base):
    """待办表(软删除:deleted=1 表示已删除)。"""

    __tablename__ = "todos"

    # TODO(任务 2):定义 7 个字段
