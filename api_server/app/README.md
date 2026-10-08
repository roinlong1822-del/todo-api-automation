# api_server/app/ — 应用代码

| 文件(待实现) | 职责 | 谁来写 |
|---|---|---|
| `main.py` | FastAPI 应用入口、路由注册、故障注入中间件 | 骨架由 AI 提供 |
| `database.py` | engine / SessionLocal / Base / get_db 依赖 | **你写**(SQLAlchemy 基础) |
| `models.py` | ORM 模型:User / Todo(含 `deleted` 软删除标记) | **你写** |
| `schemas.py` | Pydantic 请求/响应模型(契约即代码) | 骨架 + 你补 |
| `auth.py` | 生成/校验 token(简化版,不接第三方) | 骨架 |
| `seed.py` | 初始化种子数据(默认账号、若干待办) | **你写** |
| `routers/` | 路由实现 | 骨架 + 你补业务规则 |

> **约定**:DB 层(Model + 查询 + 事务)必须自己写 —— 这是面试必问的部分(Session/commit/rollback/连接池)。
