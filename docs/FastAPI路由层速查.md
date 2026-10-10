# FastAPI 路由层速查(读 `routers/*.py` 用)

---

## 1. "参数校验 → 调 DB → 组装响应"到底指什么

| 步骤 | 谁做 | 说明 |
|---|---|---|
| ① 参数校验 | **框架自动做**(在函数体之前) | 类型/范围/必填由 `schemas.py`(Pydantic)与 `Query(...)` 声明;失败直接返回错误,**函数体一行都不执行** |
| ② 调 DB | 你写的 `crud.xxx()` | 用 `Depends(get_db)` 注入进来的 `db` |
| ③ 组装响应 | **框架自动做** | 用装饰器里的 `response_model` 把返回值序列化成 JSON,并设 `status_code` |

**实测证据**(小实验:请求非法参数时看服务端打印)

```
① 合法 q=3  → 依赖执行 + 函数体执行 → {"q":3,...}
② 越界 q=99 → 依赖执行,但【函数体没执行】→ 422 校验错误
③ 类型错 q=abc → 依赖执行,但【函数体没执行】→ 422 校验错误

服务端打印:依赖执行 3 次,函数体只执行 1 次
```

结论:**"参数校验"不是你在函数里写 `if` 判断,而是声明式的** —— 声明对了,框架替你把关。

---

## 2. 响应格式从哪看(四个地方)

1. **`api_server/app/schemas.py`** —— 真身。实测 `TodoOut` 的 OpenAPI 定义:
   ```json
   {"properties": {"id": int, "title": str, "priority": int,
                   "status": {"enum": ["pending", "done"]}},
    "required": ["id", "title", "priority", "status"]}
   ```
2. **浏览器 `/docs`**(Swagger UI)—— 可交互,能直接试
3. **`/openapi.json`** —— 机器可读;测试可以拿它做"文档与实现一致性"校验
4. **实际响应体** —— `curl`/用例里看到的 JSON

---

## 3. 装饰器 `@router.post("/todos", response_model=TodoOut, status_code=201, summary="创建待办")`

**不是注释**,是**装饰器**:把下面的函数"注册成接口"并附带配置。

| 参数 | 作用 |
|---|---|
| `"/todos"` | 路径 |
| `response_model=TodoOut` | 用哪个模型**序列化返回值 + 生成文档 + 过滤多余字段** |
| `status_code=201` | 成功时的默认状态码 |
| `summary=` | 文档里显示的标题 |

> 删掉它,这个函数就只是个普通函数,不再是对外接口。

**发现的一个不一致(待修)**:OpenAPI 里声明的响应码只有 `['201', '422']`,但实现会返回 400/401/403/404。
原因:我们用全局异常处理器把 422 转成了 400,而装饰器没声明这些码。
→ 待办:给装饰器补 `responses={400: {...}, 401: {...}, 403: {...}, 404: {...}}`,让**文档与实现一致**(这正是"契约/文档校验"能抓到的缺陷)。

---

## 4. 常用参数来源一览

| 写法 | 参数来自哪里 | 例 |
|---|---|---|
| `payload: TodoCreate` | **请求体 JSON**(Pydantic 模型) | `{"title": "x", "priority": 1}` |
| `q: int = Query(1, ge=1, le=5)` | **查询参数**(URL `?q=1`) | 带约束 + 文档 |
| `todo_id: int`(在路径里) | **路径参数** | `/todos/{todo_id}` |
| `authorization: str \| None = Header(None)` | **请求头** | `Authorization: Bearer …` |
| `db: Session = Depends(get_db)` | **依赖**:先调 `get_db()` 再注入 | 见下 |
| `request: Request` | **原始请求对象** | 读中间件写的 `request.state`、自定义头 |

---

## 5. `Depends` 是什么

**依赖注入**:告诉 FastAPI"调这个函数前,先执行 `get_db()`,把它 `yield` 的值作为 `db` 传进来"。

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # ← 这个值被注入到路由函数的 db 参数
    finally:
        db.close()        # ← 请求结束自动执行(资源清理)
```

好处:① 每请求一个 Session ② 自动清理 ③ 测试可替换(override 依赖)④ 校验逻辑与业务解耦。

**关键顺序**:依赖在**函数体之前**执行;即使参数校验失败,依赖也可能已经跑过(实测 ②③ 都留下了依赖的打印)。

---

## 6. `payload` / `request` / `Query` 分别是什么

- **`payload`**:函数参数名(可叫 body/data),类型是 Pydantic 模型 → 框架把**请求体**解析校验后填进去。`payload.title` 即请求体里的 title;字段缺失/超长在进入函数前就被拦下。
- **`request: Request`**:FastAPI/Starlette 的**原始请求对象**。我们用它读 `request.state.inject_write_fail`(故障注入中间件写入的标记);其他场景:读自定义头、原始 body、客户端 IP 等。
  ⚠️ 它和之前测试用的 **werkzeug `Request`(服务端 mock)** 不是同一个类。
- **`Query(...)`**:声明**查询参数**的默认值/约束/文档。实测它的约束会出现在 OpenAPI 里:
  ```
  page  : {"minimum": 1, "default": 1}
  size  : {"maximum": 50, "minimum": 1, "default": 10}
  keyword: {"maxLength": 100, "nullable"}
  status : {"enum": ["pending","done"], "nullable"}
  ```
  → 所以**约束写在 Query 上就等于同时做了三件事**:校验、文档、示例。
