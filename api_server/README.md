# api_server/ — 被测系统(项目 A)

**定位**:配套被测对象。不是简历主体,但它是"可控、能注入故障、能做双端校验"的前提。

**已实现**:6 个接口 + 鉴权 + 统一错误码 + **故障注入** + OpenAPI 文档(契约冒烟 **43/43 通过**)。
**待你实现**:数据库层(4 个文件)—— 见下面「你的任务」。

---

## 快速开始

```bash
cd ~/study/test/projects/project1
PY=/home/roin/study/test/.venv/bin/python

$PY -m pip install -r api_server/requirements.txt
$PY -m api_server.app.seed                    # 建表 + 种子数据(任务 4 完成后可用)
$PY -m uvicorn api_server.app.main:app --reload --port 8000
# 浏览器打开 http://127.0.0.1:8000/docs  → 6 个接口可交互
```

---

## 现状:什么已完成,什么是你的任务

| 文件 | 状态 | 说明 |
|---|---|---|
| `app/main.py` | ✅ 已完成 | 应用入口、统一异常处理(校验失败 → 400 `INVALID_PARAM`)、故障注入中间件 |
| `app/schemas.py` | ✅ 已完成 | Pydantic 模型 = 契约即代码(title 1–100、priority 1–3、size ≤50) |
| `app/auth.py` | ✅ 已完成 | PBKDF2 口令散列 + HMAC 签名 token + `get_current_user` 依赖 |
| `app/injection.py` | ✅ 已完成 | 故障注入中间件(仅 `APP_ENV ∈ {dev,test,local}` 生效) |
| `app/errors.py` | ✅ 已完成 | 业务异常与统一错误响应体 |
| `app/routers/*.py` | ✅ 已完成 | 6 个路由(含越权判断、软删除、注入分支) |
| **`app/database.py`** | ⬜ **任务 1** | engine / SessionLocal / get_db / init_db |
| **`app/models.py`** | ⬜ **任务 2** | User / Todo 两张表的 ORM 模型 |
| **`app/crud.py`** | ⬜ **任务 3** | 8 个数据访问函数(+1 个聚合练习) |
| **`app/seed.py`** | ⬜ **任务 4** | 幂等的种子数据 |

---

## 你的 4 个任务(按顺序做,每个都有自测命令)

### 任务 1 · `database.py` — 连接层
```bash
python -c "from api_server.app.database import init_db, Base; init_db(); print(sorted(Base.metadata.tables))"
# 期望:['todos', 'users']
```
要点:sqlite 必须 `connect_args={"check_same_thread": False}`;`get_db()` 用 `yield` + `finally: close()`。

### 任务 2 · `models.py` — ORM 模型
```bash
python -c "from api_server.app.models import User, Todo; print(User.__tablename__, Todo.__tablename__)"
python -c "from sqlalchemy import inspect; from api_server.app.database import init_db, engine; init_db(); print([c['name'] for c in inspect(engine).get_columns('todos')])"
# 期望:['id', 'user_id', 'title', 'priority', 'status', 'deleted', 'created_at']
```
要点:**`deleted` 是软删除标记**(默认 0),后面所有查询都要过它。

### 任务 3 · `crud.py` — 数据访问层(面试重点)
要点:
- **写操作自己 `commit`**,读操作不要 commit
- `get_todo` 与 `list_todos` **必须带 `deleted == 0`**
- `list_todos` 返回 `(total, items)`,**total 是过滤后的总数**(不是当前页条数)
- `count_by_status` 是 ★ 额外练习:`GROUP BY` 聚合(做完可在路由里加 `GET /todos/stats`)

### 任务 4 · `seed.py` — 种子数据(幂等)
```bash
python -m api_server.app.seed && python -m api_server.app.seed   # 连跑两次
python -c "import sqlite3;c=sqlite3.connect('api_server.db');print(c.execute('select count(*) from users').fetchone(), c.execute('select count(*) from todos').fetchone())"
# 期望:(3,) (4,)  —— 跑两次数量不变
```

### 端到端验收(4 个任务都完成后)
```bash
# 终端 1
$PY -m uvicorn api_server.app.main:app --port 8000
# 终端 2(冒烟脚本在本地目录,不入 git)
$PY api_test/scratch/stage_a_smoke.py
# 期望:汇总:43/43 通过
```

---

## 三个检查点(做完一个就跑一次,别攒着)

| 检查点 | 怎么验 | 期望 |
|---|---|---|
| CP1 建表成功 | 任务 1 的自测命令 | `['todos', 'users']` |
| CP2 种子幂等 | seed 跑两次 + 查数量 | users=3, todos=4 |
| CP3 服务可用 | 起服务 → `/docs` → 登录拿 token → 建一条待办 | 201 且返回 `id` |

---

## SQLAlchemy 速查(本项目够用的部分)

| 概念 | 写法 | 说明 |
|---|---|---|
| 建引擎 | `create_engine("sqlite:///./api_server.db", connect_args={"check_same_thread": False})` | sqlite 单文件;换 MySQL 只改 URL |
| 会话工厂 | `sessionmaker(bind=engine, autoflush=False, autocommit=False)` | 每个请求一个会话 |
| 基类 | `class Base(DeclarativeBase): pass` | 模型继承它 |
| 模型字段 | `id: Mapped[int] = mapped_column(Integer, primary_key=True)` | 2.0 风格 |
| 建表 | `Base.metadata.create_all(bind=engine)` | 幂等,已存在不会重建 |
| 查主键 | `db.get(Todo, 1)` | 比 filter 快 |
| 条件查询 | `.filter(Todo.user_id == uid, Todo.deleted == 0)` | 多条件即 AND |
| 模糊匹配 | `.filter(Todo.title.like(f"%{kw}%"))` | `%` 通配 |
| 分页 | `.order_by(Todo.id.asc()).offset((page-1)*size).limit(size)` | 排序保证结果稳定可断言 |
| 计数 | `query.count()` | 过滤后的总数 |
| 聚合 | `db.query(Todo.status, func.count(Todo.id)).group_by(Todo.status)` | ★ 练习 |
| 新增 | `db.add(obj); db.commit(); db.refresh(obj)` | refresh 取回自增 id |
| 事务 | `db.commit()` / `db.rollback()` | 测试做数据隔离时用 rollback |
| 软删除 | `todo.deleted = 1; db.commit()` | 不物理删除 |

---

## 常见坑(踩了就长记性)

1. **软删除没过滤** → "删除后再查"应该是 404,却还查得到
2. **忘记 commit** → 接口返回 201 但库里没有(和故障注入的现象一模一样,靠肉眼分不出来 → 所以要双端校验)
3. **sqlite 跨线程** → 少 `check_same_thread=False` 会报 `SQLite objects created in a thread…`
4. **seed 不幂等** → `username` 有唯一约束,重复插入抛 `IntegrityError`
5. **`total` 算错** → 用 `len(items)` 当总数,分页用例立刻失败

---

## 参考实现(卡住再看)

已完成版本在 **`api_test/archive/stage_a_reference/`**(本地目录,不进 git)。
建议:**自己卡住 30 分钟以上再看**;看的时候只找"差在哪",看完关掉,凭记忆重写一遍。

---

## 不做什么

不做前端 UI、不做分布式、不做完整权限体系(只做最小鉴权)、不部署生产。
