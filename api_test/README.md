# api_test/ — 接口自动化测试框架(项目 B · 简历主体)

**定位**:简历主体。目标是一条命令跑完全部用例、换环境只改一处、失败可追溯、push 自动跑。

## 目录职责
| 目录 | 放什么 |
|---|---|
| `config/` | 多环境配置(base_url、超时、账号来源) |
| `data/` | 测试数据与常量(含后续的 yaml 参数表) |
| `utils/` | 通用能力:HTTP 客户端、日志、断言封装 |
| `api/` | **业务接口层**:一个接口一个方法(`todo_api.create_todo(...)`) |
| `testcases/` | 用例(冒烟放 `testcases/smoke/`) |
| `logs/` | 运行日志(本地,不进 git) |
| `scratch/` | 实验探针(本地,不进 git) |
| `archive/` | 学习阶段的练习代码(本地,不进 git) |

## 运行
```bash
cd projects/project1/api_test
~/study/test/.venv/bin/python -m pytest -m "not network" -v     # 本地稳定用例
~/study/test/.venv/bin/python -m pytest -v                      # 全量(含外网冒烟)
~/study/test/.venv/bin/python -m pytest testcases/smoke -v      # 只跑冒烟
```

## 当前进度
🟡 阶段 B 前:封装层(`utils/http_client.py`)已完成;待做 = 多环境配置、yaml 数据驱动、业务接口层、双端校验、日志、Allure。
