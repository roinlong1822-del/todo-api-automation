# api_test/api/ — 业务接口层

把「HTTP 细节」翻译成「业务语义」。**一个接口一个方法**。

```python
todo_api.create_todo("买牛奶", priority=1)  # 用例里看到的是业务意图
server_api.post("/todos", json={...})  # ← 这才是本层要消灭的写法
```

---

## 1. 三层职责边界(唯一判据:接口变了,哪个文件要改?)

| 层 | 文件 | 知道什么 | 不知道什么 |
|---|---|---|---|
| 传输层 | `utils/http_client.py` | base_url 拼接、timeout、Session、默认头、日志 | **完全不懂业务**:不知道 `/todos` 是什么 |
| **业务层** | `api/*.py` | 资源路径、请求体字段名、`Bearer` 格式、分页参数怎么拼 | 不知道断言是什么、不知道测试数据从哪来 |
| 用例层 | `testcases/**` | 业务场景、预期结果、断言 | **不出现路径、不出现 requests、不 new 客户端** |

**判据**:接口改了(比如 `priority` 改名 `level`)→ 只有 `api/` 和契约文档要改,**用例一行都不用动**。改完用例如果也要改,说明分层没做干净。

---

## 2. 文件与类

```
api/
├── __init__.py
├── auth_api.py          AuthApi  : login / me                        ← 你写(任务一)
├── todo_api.py          TodoApi  : create / get / list / delete      ← 你写(任务二)
├── README.md            本文件:规格与验收点
└── 任务清单_业务层.md   工序单:每一步写什么 / 怎么自查 / 期望输出
```

**暂时不要写基类**。两个类的公共代码只有 3 行(`__init__` 存 client/token)。等出现**第 3 个资源**、或**第 2 处重复逻辑**时再抽 `ApiBase` —— 提前抽象只会让你多维护一层。

---

## 3. 要实现的方法(签名即骨架,照抄即可)

```python
# api/auth_api.py
import requests

from utils.http_client import HttpClient


class AuthApi:
    def __init__(self, client: HttpClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def login(self, username: str, password: str) -> requests.Response:
        """POST /login → 200 {token, expires_in}"""

    def me(self) -> requests.Response:
        """GET /users/me → 200 {id, username};无 token → 401"""
```

```python
# api/todo_api.py
import requests

from utils.http_client import HttpClient


class TodoApi:
    def __init__(self, client: HttpClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def create_todo(self, title: str, priority: int = 1) -> requests.Response:
        """POST /todos → 201 todo 对象;title 空/超长、priority 越界 → 400"""

    def get_todo(self, todo_id: int | str) -> requests.Response:
        """GET /todos/{id} → 200 / 404 / 403"""

    def list_todos(
        self,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        status: str | None = None,
    ) -> requests.Response:
        """GET /todos?page=&size=&keyword=&status= → 200 {total, page, size, items}"""

    def delete_todo(self, todo_id: int | str) -> requests.Response:
        """DELETE /todos/{id} → 204 无 body / 404"""
```

### 三个签名细节,都是故意的

1. **`todo_id: int | str`,不是 `int`** —— API_SPEC §4 要求「id 为非数字 → 400」,参数边界用例得能传 `"abc"`。类型放宽是为了让**非法输入用例**能走业务层。
2. **`keyword` / `status` 默认 `None`,且为 `None` 时不发这个 query 参数** —— `?keyword=`(空字符串)和「不传 keyword」在服务端是**两种语义**,可能匹配失败。用 dict 推导过滤掉 None:
   ```python
   params = {
       k: v
       for k, v in {"page": page, "size": size, "keyword": keyword, "status": status}.items()
       if v is not None
   }
   ```
3. **`list_todos` 每次请求都发全部 4 个参数中的非 None 值,不做默认值填充** —— 让用例能测「`size` 不传时服务端默认 10」这类契约。

`AuthApi` 和 `TodoApi` 都接 `token: str | None = None`:**不传 token 的实例就是未鉴权通道**,401/403 用例直接用它,不需要在用例里手搓 header。

---

## 4. 四条铁律(踩了就等于没分层)

| # | 铁律 | 为什么 |
|---|---|---|
| 1 | **本层绝不 `assert`、不 `raise_for_status()`** | 401/404/400 用例也要走业务层。封装里一 assert,异常用例就只能绕过你 → 分层作废 |
| 2 | **绝不校验业务参数**(不写 `if not title: raise`) | 空 title、超长 title、`priority=0` 正是要测的边界值。校验了就没法测 |
| 3 | **不 try/except 吞异常** | 连接失败要原样抛出并指向真问题,不要包装成看不懂的自定义异常 |
| 4 | **方法名用业务动词**(`create_todo`),不是 HTTP 动词(`post_todo`) | 换协议(POST→PUT)时方法名不该变 |

> 注意:类型注解**运行时不做拦截**。想测「`priority` 传字符串」,直接传 `"1"`,Python 不报错、服务端报 400。注解是给人看和静态检查用的。

---

## 5. 返回什么:`requests.Response` 原样返回

不包装成 `dict`,也不包装成自定义 `ApiResult`。理由:

- 状态码、响应头、body **全都在**。测开必须断言状态码(401/403/404 是核心场景),包装层会把它们挡在门外。
- 零新概念。用例写 `r.status_code == 201`、`r.json()["id"]`、`r.headers["Location"]`,人人都看得懂。
- 需要断言响应头时(如 `X-Bug-Injected`、`Token-Expires-At`)不用额外开后门。

**升级触发条件**(现在别做):当发现**每个用例都在重复同一段断言/取值**时,再引入断言层或薄包装。到那时你会知道该包什么 —— 现在猜是瞎猜。

---

## 6. 鉴权:`Authorization: Bearer <token>`

`Bearer ` 前缀是**业务知识**,留在本层:

```python
def _headers(self) -> dict[str, str]:
    return {"Authorization": f"Bearer {self.token}"} if self.token else {}
```

每个请求都合并进去(`headers=self._headers()`)。未鉴权用例 = 不传 token 的实例。

---

## 7. 故障注入:能力挂在「连接」上,不挂在「方法」上

### 先分清:故障注入 ≠ 异常用例

| | 异常用例(negative test) | **故障注入(fault injection)** |
|---|---|---|
| 做法 | 给系统**喂错东西** | 给系统**下毒** |
| 本项目 | `create_todo(title="")` → 期望 400 | `X-Inject-Bug: write_fail` → 服务端**返回 201 但故意不写库** |
| 测的是 | **被测系统的错误处理对不对** | **我的测试能不能发现这个缺陷** |
| 失败含义 | 系统返回 200 → 系统错 | 系统"假成功"了而用例**没报错** → **测试太弱** |

关键链路:

```
POST /todos + X-Inject-Bug: write_fail
  → 服务端返回 201(系统"以为"自己成功了)
  → 用例若只断言 status_code == 201 → 【全绿放行,缺陷漏过】
  → 只有双端校验(接口说成功 + 数据库里查一下)才能抓到
```

所以本项目的故障注入**不是"测错误处理"**,而是**给测试自己出的考题**:故意制造一个变异,测试仍然全绿就说明测试不够强。这正是**变异测试(mutation testing)** 的思路 —— 面试里比"我写了 200 条用例"有力得多。

> 另一半用法(故障注入的常规含义):往依赖里注入故障(下游超时、数据库报错),看**被测系统**能否重试/降级 —— 那测的是系统的**容错能力**。本项目属于**前者**(测测试的有效性),被问到时别说错方向。

### 那这个开关该放哪?

**每层只装该层的东西。** 业务层是"被测系统对外能力的说明书",它不该知道"测试想怎么撬动系统"。所以:

- ❌ **不能进业务方法签名** —— `create_todo(..., inject_bug=...)` 会让业务接口混入与业务无关的参数;而且每个写方法都要加一遍,参数会扩散。
- ❌ **也不能让用例绕开业务层裸调 client** —— 用例就得自己拼路径和请求头,**接口一改就漏改这处**;别人照抄这个"例外",分层就名存实亡。
- ✅ **挂在连接对象上**(`with_headers`),和 token 同一个位置。

```python
inject_api = TodoApi(server_api.with_headers(**{"X-Inject-Bug": "write_fail"}), token=token)
r = inject_api.create_todo("这条不该落库")  # 业务方法原样调用,签名零污染
```

**锚点:业务数据走方法参数,连接级开关走连接默认头。**

| 东西 | 例子 | 走哪条路 |
|---|---|---|
| **业务数据** | 标题、优先级、分页参数 | **方法参数** `create_todo("买牛奶", priority=1)` |
| **连接级属性/开关** | token、timeout、base_url、**注入头** | **连接默认头** `server_api.with_headers(...)` |

token 早就是这么挂的 —— **token 挂哪,注入头就挂哪**。用例想进入"故障世界",换一个连接对象即可,业务代码一个字不动。

---

## 8. 验收点(可执行,逐条打勾)

**结构类**

- [ ] `api/` 下只有 `auth_api.py` / `todo_api.py` / `__init__.py` / `README.md`
- [ ] 业务方法数量 == `docs/API_SPEC.md` 里的接口数量 = **6 个**:`login` / `me` / `create_todo` / `get_todo` / `list_todos` / `delete_todo`(不多不少)
- [ ] 每个方法都有**参数和返回值**的类型注解
- [ ] 路径字符串**只出现在 `api/`**,`grep -rn '"/todos\|"/login\|"/users' api_test/api/` 有结果,**在 `testcases/` 下无结果**

**纪律类**

- [ ] 全仓库 `grep -rn "assert" api_test/api/` **无结果**(本层不 assert)
- [ ] `grep -rn "raise_for_status\|try:" api_test/api/` **无结果**
- [ ] 不用业务的默认值兜底:传 `title=""`、`id="abc"` 能原样发出去并拿到 400/404

**行为类**

- [ ] 用例里 `grep -c "requests\|http\|timeout" api_test/testcases/*.py` 三个计数**仍为 0**(`scripts/run_checks.sh` 第 1 步已在查)
- [ ] `ruff check api_test/` → All checks passed
- [ ] `pytest -q` 全绿(含原有 10 条 mock 用例 + 新增业务用例)
- [ ] `python scripts/contract_smoke.py` → 45/45
- [ ] **故障注入用例走的是 `todo_api.create_todo()`,不是裸 client**

---

## 9. 实现顺序(建议 4 段,每段跑一次)

| 段 | 做什么 | 完成标志 |
|---|---|---|
| 1 | `AuthApi.login` + `me`,先在 `scratch/` 里手测 | 打印出 token;不传 token 调 `me()` 拿到 401 |
| 2 | `TodoApi` 四个方法 | scratch 里跑通:创建→查询→列表→删除→再查 404 |
| 3 | `conftest.py` 加 fixture:`token`(session)、`auth_api`、`todo_api` | 用例里能直接写 `def test_x(todo_api)` |
| 4 | 用例分层(见下)+ 更新三份 README | 新增业务用例全绿 |

**第 4 段的用例文件调整**(现有 `test_api.py` 测的是 mock 服务,不是自建服务,两者别混):

```bash
git mv api_test/testcases/test_api.py api_test/testcases/mock/test_mock_practice.py
# 新建(你写):
api_test/testcases/business/test_auth.py          # 登录正常 / 密码错 / 锁定
api_test/testcases/business/test_todos_crud.py    # CRUD + 双端校验 + 软删除
```

每段跑完就 commit,别攒到最后。

---

## 10. 三个决策(已拍板)

| # | 决策 | 结论 | 理由 |
|---|---|---|---|
| D1 | `GET /todos/{id}/status` 保留吗? | ✅ **已删除**(2026-10-10) | 与 `GET /todos/{id}` 信息重复;`response_model=str` 不规范(裸字符串不是 JSON 对象);**不在 `API_SPEC.md` 里** —— 契约外接口 = 被测系统与测试文档不一致,面试会被追问"为什么需要它"。已从 `api_server/app/routers/todos.py` 移除,契约回到 6 个接口 |
| D2 | 业务层返回 `Response` 还是包装类? | ✅ **`requests.Response`** | 见 §5:状态码/头/body 全在,零新概念 |
| D3 | 故障注入怎么给? | ✅ **客户端默认头**(`with_headers`) | 见 §7:业务签名零污染,双端校验用例仍走业务层 |

**纪律**:以后若要新增接口,顺序永远是 **先改 `docs/API_SPEC.md` → 再改 `api_server` → 最后加 `api/` 方法**。反了就会出现契约外接口。
