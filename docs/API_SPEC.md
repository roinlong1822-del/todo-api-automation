# API 契约(被测服务 `api_server`)

> **这份文档是开发契约**:被测服务按它实现,测试用例按它断言。
> 改接口 = 先改这里,再改代码(避免代码与文档不一致)。
> 版本:v1.0 · 冻结日期:2026-10-08

---

## 0. 全局约定

| 项        | 约定                                                     |
| -------- | ------------------------------------------------------ |
| Base URL | `http://127.0.0.1:8000`(可用环境变量覆盖)                      |
| 请求格式     | `Content-Type: application/json`                       |
| 鉴权       | Header `Authorization: Bearer <token>`                 |
| 错误响应体    | `{"code": "<机器可读错误码>", "message": "<人类可读说明>"}`         |
| **断言约定** | **断言 `code`(稳定字段),不对 `message` 文案做精确断言**(文案会改,code 不会) |
| 时间字段     | ISO 8601 UTC,如 `2026-10-08T10:00:00Z`                  |

**错误码总表**

| code | HTTP | 含义 |
|---|---|---|
| `INVALID_PARAM` | 400 | 参数缺失/类型错/超长 |
| `UNAUTHORIZED` | 401 | 未携带 token / token 无效或过期 |
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `ACCOUNT_LOCKED` | 403 | 连续失败被锁定 |
| `NOT_FOUND` | 404 | 资源不存在(含软删除后的资源) |
| `FORBIDDEN` | 403 | 越权访问他人资源 |

---

## 1. `POST /login`

**请求**:`{"username": "tester", "password": "Passw0rd!"}`

| 情况 | HTTP | 响应 |
|---|---|---|
| 成功 | 200 | `{"token": "<str>", "expires_in": 3600}` |
| 参数缺失 | 400 | `{"code": "INVALID_PARAM", ...}` |
| 密码错误 | 401 | `{"code": "INVALID_CREDENTIALS", ...}` |
| 连续失败 ≥3 次 | 403 | `{"code": "ACCOUNT_LOCKED", ...}` |

**业务规则**:同一账号连续 3 次密码错误 → 账号锁定(锁定期间正确密码也返回 403)。
**响应头**:`Token-Expires-At`(便于测试断言,不必解析 body)。

## 2. `GET /users/me`

**请求**:Header `Authorization: Bearer <token>`

| 情况 | HTTP | 响应 |
|---|---|---|
| 成功 | 200 | `{"id": 1, "username": "tester"}` |
| 无 token / 格式错 | 401 | `{"code": "UNAUTHORIZED", ...}` |
| token 过期或伪造 | 401 | `{"code": "UNAUTHORIZED", ...}` |

## 3. `POST /todos`

**请求**:`{"title": "买牛奶", "priority": 1}`(priority 可选,默认 1)

| 情况                | HTTP    | 响应                                                              |
| ----------------- | ------- | --------------------------------------------------------------- |
| 成功                | **201** | `{"id": 7, "title": "买牛奶", "priority": 1, "status": "pending"}` |
| `title` 缺失/为空     | 400     | `INVALID_PARAM`                                                 |
| `title` 长度 > 100  | 400     | `INVALID_PARAM`                                                 |
| `priority` 不在 1–3 | 400     | `INVALID_PARAM`                                                 |
| 未鉴权               | 401     | `UNAUTHORIZED`                                                  |

**边界值**(测试用):`title` 长度 **1 / 100 通过,0 / 101 拒绝**;`priority` **1、3 通过,0、4 拒绝**。

## 4. `GET /todos/{id}`

| 情况 | HTTP | 响应 |
|---|---|---|
| 成功 | 200 | todo 对象 |
| `id` 不存在 | 404 | `NOT_FOUND` |
| `id` 为非数字 | 400 | `INVALID_PARAM`(FastAPI 默认 422,本服务统一转 400) |
| 访问他人的 todo | 403 | `FORBIDDEN` |

## 5. `GET /todos`

**查询参数**:`page`(默认 1,≥1)、`size`(默认 10,1–50)、`keyword`(标题模糊匹配)、`status`(`pending`/`done`)

**响应**:`{"total": 42, "page": 1, "size": 10, "items": [ {...}, ... ]}`

| 情况          | HTTP | 响应                                      |
| ----------- | ---- | --------------------------------------- |
| 成功          | 200  | 上述结构                                    |
| `size > 50` | 400  | `INVALID_PARAM`                         |
| `page < 1`  | 400  | `INVALID_PARAM`                         |
| 无匹配结果       | 200  | `{"total": 0, "items": []}`(**不是 404**) |

**排序约定**:按 `id` 升序,保证分页结果稳定可断言。

## 6. `DELETE /todos/{id}`

| 情况 | HTTP | 响应 |
|---|---|---|
| 成功 | **204** | 无 body |
| 不存在 / 已删除 | 404 | `NOT_FOUND` |
| 重复删除 | 404 | `NOT_FOUND`(幂等性用例) |

**实现约定**:**软删除**(`deleted=1`),因此:
- `GET /todos/{id}` 和列表查询必须带 `deleted = 0` 条件
- **双端校验断言要同时检查 `deleted` 字段与查询结果**

---

## 7. ★ 故障注入(测试专用开关)

| 方式 | 用法 | 说明 |
|---|---|---|
| Header(**主**) | `X-Inject-Bug: write_fail` | 更像真实 feature flag,顺便验证自定义头透传 |
| Query(**辅**) | `?inject_bug=write_fail` | 浏览器演示方便 |

**行为**:写接口(创建/删除)**返回成功状态码,但不写库**。

**安全约束**:
1. 默认关闭
2. **仅 `APP_ENV != "prod"` 时生效**(生产禁用)
3. 使用后在响应头回显 `X-Bug-Injected: write_fail`(便于测试断言"注入确实生效了")

**用途**:演示"接口返回 201 但数据库里没有这条记录"这类缺陷能被**双端校验**抓住 —— 面试可现场演示。

---

## 8. 种子数据(seed)

| 账号 | 密码 | 说明 |
|---|---|---|
| `tester` | `Passw0rd!` | 主测试账号,初始有 3 条 todo |
| `locked_user` | `Passw0rd!` | 预设为锁定状态,用于锁定用例 |
| `other` | `Passw0rd!` | 用于越权用例(有 1 条 todo) |

初始 todo:3 条(2 条 `pending`、1 条 `done`),标题含中英文各一条(用于编码用例)。

## 9. `GET /todos/stats`

统计当前用户各状态待办数量。

**响应**(200):
{"pending": 2, "done": 1}

| 情况  | HTTP | 响应                        |
| --- | ---- | ------------------------- |
| 成功  | 200  | 上述结构                      |
| 无待办 | 200  | {"pending": 0, "done": 0} |
| 未鉴权 | 401  | UNAUTHORIZED              |

**约定**:`pending` 与 `done` **两个键始终存在**,没有该状态时值为 0。
**统计范围**:仅统计 `deleted = 0`(软删除的不计入)。