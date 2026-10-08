# api_server/app/routers/ — 路由层

| 文件(待实现) | 内容 |
|---|---|
| `auth.py` | `POST /login` |
| `users.py` | `GET /users/me`(鉴权) |
| `todos.py` | `POST /todos`、`GET /todos/{id}`、`GET /todos`(分页+搜索)、`DELETE /todos/{id}`(软删除) |

**约定**:
- 路由层只做"参数校验 → 调 DB → 组装响应",不写复杂逻辑
- 错误统一返回 `{"code": "...", "message": "..."}`(见 `docs/API_SPEC.md`)
