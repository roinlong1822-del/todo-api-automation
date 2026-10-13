# testcases/business/ — 业务层用例(打真实被测系统)

这里放**正经的接口测试**:通过 `api/` 业务层调用自建服务 `api_server`,断言**业务规则与数据一致性**。

## 铁律

1. **只用 `api/` 业务层** —— 不出现裸路径、不出现 `requests`、不出现 `timeout`、不 new 客户端。
2. **断言盯系统行为**,不盯实现细节(见 `docs/约定与隐私.md`)。
3. **断言 `code` 字段,不断言 `message` 文案** —— 文案会改,code 不会(见 `docs/API_SPEC.md` §0)。
4. **不硬编码 id** —— 自己创建的 id 从响应里取;种子数据的 id 通过列表接口发现。硬编码的 id 会在重 seed 后失效。

## 可用 fixture(来自 `api_test/conftest.py`)

| fixture | 是什么 | 用来测 |
|---|---|---|
| `server_api` | 指向 `api_server` 的 `HttpClient`(地址来自 `config/`) | 底层通道,业务用例一般不直接用 |
| `app_config` | 当前环境配置(`base_url`/`timeout`/`mock`/`env`) | 需要感知环境时 |
| `auth_api` | 未鉴权的 `AuthApi` | 登录接口 |
| `token` | `tester` 账号的 token(session 级,只登录一次) | —— |
| `todo_api` | **已鉴权**的 `TodoApi` | 绝大多数待办用例 |
| `anon_todo_api` | **未鉴权**的 `TodoApi` | 401 用例 |
| `inject_api` | 带 `X-Inject-Bug: write_fail` 的 `TodoApi` | 双端校验 / 故障注入 |

## 待办数据(种子,见 `docs/API_SPEC.md` §8)

`tester` 初始 3 条:`tester todo 1`(pending)、`测试待办 2`(pending)、`tester todo 3`(done);`other` 有 1 条。

## ★ 已知陷阱

- **不要把 `tester` 当"错误密码"的试验品**:连续 3 次密码错误会**锁定账号**(`MAX_FAILED_ATTEMPTS = 3`),之后所有业务用例都会拿到 403 `ACCOUNT_LOCKED`。
  恢复:`rm api_server.db && python -m api_server.app.seed`
- **`list_todos` 的 `total` 与 `len(items)` 不是一回事**:`total` 是符合条件的总数,`items` 只是当前页。
- **软删除**:删掉的记录 `deleted=1`,所以 `GET /todos/{id}` 返回 404,但数据库里那行还在 —— 双端校验时要注意这个区别。

## 运行

```bash
pytest api_test/testcases/business -q          # 需先起被测服务(uvicorn ... --port 8000)
```
