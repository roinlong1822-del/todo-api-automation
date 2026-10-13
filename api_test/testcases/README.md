# api_test/testcases/ — 用例层

按**被测对象**分目录,别混:

| 目录 | 被测对象 | 通道 | 状态 |
|---|---|---|---|
| `mock/` | 自建的假服务(pytest-httpserver) | `mock_api` / `remote_api` | ✅ 阶段 1 产物(8 条练习用例) |
| `business/` | **真实被测系统 `api_server`** | `server_api` + `api/` 业务层 | 🟡 进行中(见该目录 README) |
| `smoke/` | 核心主流程 + 外网契约冒烟 | 全部 | ⬜ |

| 文件 | 说明 |
|---|---|
| `用例清单.md` | 阶段 1(mock 版)的用例设计清单 |
| `用例清单_业务层.md`(待建) | **按 `docs/API_SPEC.md` 重新设计**的业务用例清单与验收标准 |

**约定**:用例名说清"场景 + 预期";断言盯系统行为(见 `docs/约定与隐私.md`);断言 `code`,不断言 `message` 文案。

```bash
pytest api_test/testcases/business -q      # 需先起被测服务
pytest api_test/testcases/mock -q          # 不依赖被测服务
```
