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

## 运行(推荐在【仓库根】执行,pytest 配置 `pytest.ini` 在根目录)
```bash
cd projects/project1
python -m pytest -m "not network" -v            # 本地稳定用例(CI 用这条)
python -m pytest -v                             # 全量(含外网冒烟)
python -m pytest api_test/testcases/smoke -v    # 只跑冒烟
bash scripts/run_checks.sh                      # 一键验收
```
> 在 `api_test/` 子目录里跑也可以(pytest 会向上找到根配置),结果一致。
> `scratch/`、`archive/` 已通过 `norecursedirs` 排除,不参与自动收集。

## import 写法(统一约定,别写错)

`pythonpath = api_test .` 把 `api_test/` 和仓库根都加进了 `sys.path`,所以**同一个文件有两种 import 写法都能跑**:

```python
from api.todo_api import TodoApi          # ✅ 约定:用这个
from api_test.api.todo_api import TodoApi # ❌ 不要用:能跑,但有害
```

**危害(实测)**:两种写法会产生**两个模块对象、两个类**:

```
api.todo_api is api_test.api.todo_api        → False
api.TodoApi  is api_test.api.TodoApi         → False
isinstance(api.TodoApi(None), api_test.api.TodoApi) → False   ← isinstance 判断会失败
```

后果:类型判断失效、`monkeypatch` 打错了模块、覆盖率统计被拆成两份、排查时"明明是这个类却 isinstance 为 False"。

**规则:一律用短写法** `from api...` / `from config...` / `from data...` / `from utils...`
(仓库根 `.` 只是为了让用例能 `import api_server...` 做双端校验才加的,不是给你换写法用的。)

## 当前进度

🟡 **阶段 B 进行中**

- ✅ `utils/http_client.py` —— 传输层(含 `with_headers()`,给故障注入用的连接级通道)
- ✅ 多环境配置 —— `config/*.yaml` + `loader.py` + `app_config` fixture(`APP_ENV=test pytest` 即切换)
- ✅ 业务接口层 —— `api/auth_api.py`(login/me)、`api/todo_api.py`(create/get/list/delete)
- ✅ 夹具接线 —— `auth_api` / `token` / `todo_api` / `anon_todo_api`
- 🟡 用例 —— mock 练习 8 条已就绪;**业务用例 7 条待写**(`testcases/business/`)
- ⬜ 双端校验(直连 DB)、yaml 数据驱动、日志、Allure、GitHub Actions
