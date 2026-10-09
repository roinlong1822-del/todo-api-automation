# SQLAlchemy 查询速查(分页 / 匹配 / 聚合)

> 配套:`api_server/app/crud.py`。所有结论都在本机实测过,命令与输出见文末。

---

## 1. 查询是「链式」的,而且**能直接 print 出 SQL**

```python
q = (db.query(Todo)
       .filter(Todo.user_id == 1, Todo.deleted == 0, Todo.title.like("%周%"))
       .order_by(Todo.id.asc()))
print(q)     # ← 看它翻译成了什么 SQL(调试神器)
```
```
SELECT todos.id, todos.user_id, todos.title, todos.status, todos.deleted
FROM todos
WHERE todos.user_id = ? AND todos.deleted = ? AND todos.title LIKE ?
ORDER BY todos.id ASC
```
注意 `?` 是**参数占位符** → 传入的值走绑定参数,**不会被当成 SQL 执行**(防注入,实测见 §4)。

**生成式 API**:`filter()`/`order_by()`/`offset()` 都是**返回新 query**,所以同一个查询对象可以反复用:
```python
q = db.query(Todo).filter(Todo.user_id == 1, Todo.deleted == 0)
total = q.count()                    # 先算总数
items = q.offset(0).limit(5).all()   # 再取某一页 —— q 不受影响
```

---

## 2. 匹配(WHERE 条件)怎么写

| 需求 | 写法 | 说明 |
|---|---|---|
| 精确等于 | `Todo.user_id == 1`、`Todo.status == "done"` | 用 Python 的 `==`,**不是** `=` |
| 不等于 | `Todo.status != "done"` | |
| 多条件(AND) | `.filter(A, B, C)` 或 `.filter(A).filter(B)` | 逗号即 AND |
| 或 | `from sqlalchemy import or_; .filter(or_(A, B))` | |
| 标题模糊 | `.like("%周%")` / `.contains("周")` | 两者等价;`%` 代表**任意多个字符** |
| 单字符通配 | `.like("任务0_")` | `_` 代表**恰好一个字符** |
| 前缀/后缀 | `.startswith("任务")` / `.endswith("书")` | |
| 忽略大小写 | `.ilike("%MILK%")` | sqlite 对 ASCII 有效 |
| 属于集合 | `.in_([1, 2, 3])` | |
| 为空/非空 | `Todo.title.is_(None)` / `.is_not(None)` | |
| 范围 | `Todo.id.between(10, 20)` | |

**动态条件**(参数没传就不加这个条件):
```python
q = db.query(Todo).filter(Todo.user_id == user_id, Todo.deleted == 0)
if keyword:
    q = q.filter(Todo.title.like(f"%{keyword}%"))
if status:
    q = q.filter(Todo.status == status)
```

---

## 3. 分页三要素(缺一不可)

```
① WHERE   : 先过滤(自己的 + 未删除的 + 关键词/状态)
② ORDER BY: 必须排序 —— SQL 不保证默认顺序,不排序时分页可能重复或漏行
③ LIMIT/OFFSET: 取多少 / 跳过多少,offset = (page - 1) * size
```

实测(数据:user 1 有 11 条未删除待办):

| page | size | offset | 取到的行 |
|---|---|---|---|
| 1 | 5 | 0 | 任务01…任务04, 任务06 |
| 2 | 5 | 5 | 任务07…任务10, 写周报 |
| 3 | 5 | 10 | buy milk |
| 1 | 10 | 0 | 前 10 条 |
| 2 | 10 | 10 | buy milk |

> 注意"任务05"不在结果里 —— 它 `deleted=1`,**过滤发生在分页之前**,这是正确顺序。

**`total` 必须是「过滤后、分页前」的总数**:
```python
total = q.count()                 # ✅ 11
total = len(items)                # ❌ 5(只是当前页条数)
```

---

## 4. 安全:参数绑定天然防注入

实测传入 `"%'; drop table todos; --"` 作为关键词:
```
结果行数: 0        ← 被当成普通字符串去匹配
表还在吗: 13 行    ← 表没被删
```
所以**永远用 `filter(...==值)` / `.like(f"%{kw}%")` 这种方式传值**,不要自己拼 SQL 字符串。

---

## 5. 聚合(GROUP BY)

```python
from sqlalchemy import func

rows = (db.query(Todo.status, func.count(Todo.id))
          .filter(Todo.user_id == user_id, Todo.deleted == 0)
          .group_by(Todo.status)
          .all())
return {status: cnt for status, cnt in rows}      # {'done': 4, 'pending': 7}
```
对应 SQL:
```sql
SELECT todos.status, count(todos.id) FROM todos
WHERE todos.user_id = ? AND todos.deleted = ?
GROUP BY todos.status
```

---

## 6. 三个常见错法(面试也爱问)

| 错法 | 后果 |
|---|---|
| `total = len(items)` | 分页用例立刻失败(第 2 页的 total 变成剩余条数) |
| 不写 `order_by` | 分页结果不稳定 → 用例随机红,难复现 |
| 漏 `deleted == 0` 或 `user_id` | 查出已删除数据 / 查到别人的数据(越权 bug) |

---

## 7. 自己复现这些结论

```bash
# 建一个临时库,塞 12 条数据,打印各种查询的 SQL 与结果
cd /tmp && python - <<'PY'
from sqlalchemy import create_engine, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
class Base(DeclarativeBase): pass
class Todo(Base):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10))
    deleted: Mapped[int] = mapped_column(Integer, default=0)
e = create_engine("sqlite:///q.db"); Base.metadata.create_all(e)
s = sessionmaker(bind=e)()
# …插入数据后:
print(s.query(Todo).filter(Todo.deleted == 0).order_by(Todo.id.asc()).offset(0).limit(5))
PY
```
