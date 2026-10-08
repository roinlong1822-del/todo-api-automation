# api_test/testcases/ — 用例层

| 文件 | 状态 | 覆盖 |
|---|---|---|
| `test_api.py` | 🟡 阶段 1 产物(mock 版) | 状态码/字段/列表/query 参数/按 id 查询——**待迁移到 api_server** |
| `用例清单.md` | ✅ | 12 条用例的设计清单与验收标准 |
| `test_auth.py`(待建) | ⬜ | 登录:正常/密码错/锁定/参数边界 |
| `test_todos_crud.py`(待建) | ⬜ | 待办 CRUD + 双端校验 + 软删除 |
| `test_todos_query.py`(待建) | ⬜ | 分页/搜索/状态过滤的组合用例 |
| `smoke/` | ⬜ | 冒烟(核心主流程 + `network` 标记的外网契约) |

**约定**:用例名说清"场景 + 预期";断言盯系统行为(见 `docs/约定与隐私.md`)。
