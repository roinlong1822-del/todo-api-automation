# .github/workflows/ — CI 流水线(阶段 E 实现)

计划:
| 触发 | 动作 |
|---|---|
| push / PR | 启动被测服务 → 跑 `pytest -m "not network"` → 上传 Allure 报告 artifact |
| 定时(每天一次) | 额外跑 `network` 标记的外网冒烟,失败不阻塞主分支 |

**隐私注意**:账号/密钥放 GitHub **Secrets**,不写进 yaml;日志里避免打印 token。
