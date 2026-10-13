# testcases/mock/ — mock 服务用例(pytest-httpserver)

这里放的是**阶段 1 的练习用例**:用 `pytest-httpserver` 起一个假服务,练"HTTP 客户端 + mock + 断言信息量"这套基本功。

| 文件 | 测什么 | 数据源 |
|---|---|---|
| `test_mock_practice.py` | 状态码 / Content-Type / 字段值与类型 / 响应耗时 / 列表 / query 参数透传 / 按 id 查询 / 外网契约冒烟 | `mock_api`(本地假服务)、`remote_api`(真外网,`network` 标记) |

**和 `../business/` 的区别(别混)**:

| | `mock/`(这里) | `../business/` |
|---|---|---|
| 被测对象 | **自己造的假服务**,测的是"我的测试代码对不对" | **真实被测系统 `api_server`** |
| 接口形状 | jsonplaceholder 风格(`userId`/`completed`) | 本项目契约(`docs/API_SPEC.md`:`title`/`priority`/`status`) |
| 用哪个通道 | `mock_api` / `remote_api` | `server_api` + `api/` 业务层 |
| 断言重点 | 客户端行为、参数真的发出去了没 | 业务规则、状态流转、双端一致性 |

**保留它的理由**:它是**测试代码自身的练习题** —— mock 匹配不上会返回 500,等于用"请求契约"反过来验证客户端。写新用例时先在这里练"这条断言有没有信息量",再搬到 `business/`。

**运行**:`pytest api_test/testcases/mock -q`(外网那条要加 `-m network` 才会跑)。
