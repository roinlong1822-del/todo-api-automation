# todo-api-automation · 待办服务接口自动化测试框架

[![CI](https://github.com/roinlong1822-del/todo-api-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/roinlong1822-del/todo-api-automation/actions/workflows/ci.yml)

> 一个从零搭建的**接口自动化测试框架**(项目 B),配套一个**自建被测服务**(项目 A)。
> 目的:演示"可控被测对象 + 分层框架 + 数据驱动 + **双端校验** + **故障注入** + CI"的完整工程实践。

**当前状态**:🟢 **阶段 A–C 完成** —— 6 接口 + 鉴权 + 统一错误码 + 故障注入;框架四层;14 条业务用例 + 9 条 mock 用例;契约冒烟 45/45;CI 就绪。

**亮点(评审者 30 秒能看完的部分)**

| 能力 | 证据 |
|---|---|
| 分层框架,用例里零 HTTP 细节 | `grep -rnE "requests\|timeout\|http" api_test/testcases/business/` → 0;裸路径 → 0 |
| **双端校验**:不只断言状态码,还直连数据库核对落库 | `testcases/business/test_todos_db.py`(含软删除 `deleted=1` 验证) |
| **故障注入**证明测试有效 | `testcases/business/test_injection.py`:接口返回 201 但库里没有,双端校验当场抓住 |
| 用 `xfail(strict=True)` 自证"单端断言会被骗过" | 同上文件第 3 条用例 |
| 多环境切换 | `APP_ENV=test pytest`;配置缺键直接报错,不静默回落 |
| 用例幂等 | 跑前/跑后 DB 行数一致(11→11 / 4→4) |
| mock 与真实服务分离 | `testcases/mock/`(练客户端行为) vs `testcases/business/`(测项目契约) |

---

## 一、快速开始

```bash
# 1) 装依赖 + 起被测服务(终端 1,保持不关)
pip install -r requirements-dev.txt      # 运行时 + 测试依赖
python -m api_server.app.seed            # 初始化种子数据(幂等,可重复跑)
python -m uvicorn api_server.app.main:app --port 8000 --reload
# 浏览器打开 http://127.0.0.1:8000/docs 可交互

# 2) 跑测试(终端 2,必须在【仓库根】执行 —— sqlite 路径相对 cwd)
pytest -q -m "not network"               # 本地稳定用例(CI 用这条)
pytest -q                                # 全量(含外网 network 标记,本机常连不上)
pytest -q -m network                     # 只跑外网契约冒烟
pytest api_test/testcases/business -q    # 只跑业务用例

# 3) 三道验收
bash scripts/run_checks.sh               # 分层检查 + 用例 + ruff(违规即失败)
python scripts/contract_smoke.py         # 独立契约冒烟 45 项(支持 API_BASE 指向任意实例)
ruff check .                             # 代码规范
```

---

## 二、🧭 环境与架构确认表(开发前冻结,避免后期歧义)

> 这张表是**开发契约**:动手前先确认;中途要改,先改这张表和 `docs/API_SPEC.md`,再改代码。

### A. 环境确认表

| 项 | 选定 | 说明 |
|---|---|---|
| 操作系统 | Linux(开发)/ `ubuntu-latest`(CI) | — |
| Python | **3.12.3** | 虚拟环境:本机 `~/study/test/.venv`;CI 里独立创建 |
| 依赖管理 | `pip` + `requirements.txt` | 不引入 poetry/uv(降低认知负担) |
| 测试框架 | **pytest 9.1.1** + pytest-httpserver 1.1.5 | mock 第三方依赖用 |
| HTTP 客户端 | **requests 2.34**(经自研 `HttpClient` 封装) | 用例层不直接用 requests |
| 被测服务 | **FastAPI 0.142.4 + Uvicorn 0.54.0** | 自动生成 `/docs`;依赖见 `api_server/requirements.txt` |
| ORM / 数据库 | **SQLAlchemy 2.1.4 + SQLite**(`api_server.db`) | 换 MySQL 只改 `DATABASE_URL` |
| 配置 | **PyYAML + `.env`** | 环境变量覆盖 yaml;`.env` 不入库 |
| 日志 | 标准库 `logging` | 落文件 + 脱敏 |
| 报告 | `allure-pytest` | 阶段 D 接入 |
| 代码规范 | **ruff 0.16.8**(检查 + 格式化) | 保存时自动跑 |
| 版本控制 | **Git 2.43 + GitHub** | 公开前过一遍隐私清单 |
| 被测服务端口 | **8000** | 可用环境变量覆盖 |
| pytest rootdir | 仓库根(`pytest.ini`),`pythonpath = api_test .` | `api_test` 让用例能 `from api...`;`.` 让用例能 `import api_server...`(双端校验用) |

### B. 架构确认表

**两个项目的角色与依赖方向**

```
                ┌──────────────────────────────┐
                │  docs/API_SPEC.md(接口契约) │ ← 先冻结契约,再写代码
                └───────────────┬──────────────┘
                                │ 实现
                ┌───────────────▼──────────────┐
                │  api_server/  被测系统(项目A)│  FastAPI + SQLAlchemy + SQLite
                │  6 接口 / 种子数据 / 故障注入 │
                └───────────────▲──────────────┘
                                │ HTTP
                ┌───────────────┴──────────────┐
                │  api_test/  测试框架(项目B) │ ← 简历主体
                └──────────────────────────────┘
```

**`api_test/` 内部分层(依赖只能自上而下)**

| 层 | 目录 | 职责 | 允许依赖 |
|---|---|---|---|
| 用例层 | `testcases/` | 写断言,表达业务预期 | `api/`、`utils/`、`data/` |
| 业务接口层 | `api/` | 一个接口一个方法,翻译成业务语义 | `utils/` |
| 通用能力层 | `utils/` | HttpClient / 日志 / 断言封装 / DB | 无(最底层) |
| 横切 | `config/`、`data/` | 环境配置、测试数据 | — |

**红线**:
- 用例里**不出现** URL、超时字面量、裸路径、`requests`(由 `scripts/run_checks.sh` 第 1 步强制,违规即失败)
- `utils/` 与 `api/` **不写断言**(只搬事实,判断留给用例)
- 被测服务的业务逻辑**只通过 HTTP 交互**;唯一例外是**双端校验**时用例可**只读** `api_server.app.models` 直连数据库核对数据(不拿它造业务数据)

### C. 接口契约摘要(详见 [`docs/API_SPEC.md`](docs/API_SPEC.md))

| 方法 | 路径 | 成功 | 关键异常 |
|---|---|---|---|
| POST | `/login` | 200 `{token, expires_in}` | 400 参数缺失 / 401 密码错 / 403 锁定 |
| GET | `/users/me` | 200 `{id, username}` | 401 无 token / 过期 |
| POST | `/todos` | **201** `{id, title, priority, status}` | 400 title 空或超长、priority 越界 / 401 |
| GET | `/todos/{id}` | 200 todo | 404 不存在 / 403 越权 |
| GET | `/todos` | 200 `{total, page, size, items[]}` | 400 size>50、page<1 |
| GET | `/todos/stats` | 200 `{pending, done}`(两键始终存在) | 401 |
| DELETE | `/todos/{id}` | **204** 无 body | 404 不存在(含重复删除) |
| ★ | 写接口 + `X-Inject-Bug: write_fail` | 201 / 204(**库里没写**) | 仅非生产环境生效,响应头回显 `X-Bug-Injected` |

### D. 约定

| 项 | 约定 |
|---|---|
| 命名 | 类 `CapWords`;函数/变量 `snake_case`;常量 `UPPER_CASE`;测试 `test_*` |
| 用例名 | `test_<对象>_<场景>_<预期>`,失败时报告自带说明 |
| 错误码 | 响应体统一 `{"code": "...", "message": "..."}`;**断言 `code`**,不断言 `message` 文案 |
| 语言 | 路径/字段全英文;中文只出现在 `message` 与种子数据 |
| 分支 | `main` 保绿;功能分支 `feat/xxx`;修 bug `fix/xxx` |
| 提交信息 | `feat: …` / `fix: …` / `docs: …` / `test: …` / `chore: …` |
| README | **每个目录都必须有 README**,说明"放什么、谁负责、怎么跑" |

### E. 隐私与开源红线(提交前必查)

**绝不提交**:

| 类别 | 例子 | 防护 |
|---|---|---|
| 密钥 | API key、`SECRET_KEY`、token | 走 `.env` / CI Secrets;`.gitignore` 已排除 `.env` |
| 账号密码 | 数据库口令、测试账号真实密码 | `.env.example` 只放占位符 |
| 个人信息 | 真实姓名/学号/手机号/邮箱/身份证 | 提交身份用 GitHub **noreply** 邮箱 |
| 本机路径 | `/home/roin`、主机名 | `logs/`、`scratch/`、`archive/` 已排除 |
| 业务敏感数据 | 实习公司内部接口/数据 | 公开仓库只放自建服务的假数据 |

**提交前三件事**:① `git status` 看有没有意外文件 ② `git diff --cached` 逐行看 ③ 确认 `.env`、`*.db`、`logs/` 不在暂存区。

### F. 已确认

- [x] 仓库名 **`todo-api-automation`**
- [x] 提交身份:`user.name=roin`、`user.email=roinlong1822-del@users.noreply.github.com`(**noreply 邮箱**,不暴露真实邮箱)
- [x] 被测服务端口 **8000**
- [x] 数据库:项目内用 SQLite;MySQL 可切换已实测("只改 `DATABASE_URL`、代码零改动")
- [x] `scratch/`、`archive/`、`logs/` 本地不入库(已验证 `git ls-files` 为空)
- [x] 故障注入开关:**Header 为主 + query 为辅,默认关闭,仅非生产生效**

---

## 三、里程碑与进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| A | 被测服务 `api_server`(6 接口 + 鉴权 + 统一错误码 + 故障注入) | ✅ **完成**(契约冒烟 45/45) |
| B | 框架分层:config 多环境 / `api/` 业务层 / 用例按被测对象分层 | ✅ **完成** |
| C | logging + **双端校验** + 数据清理 + **故障注入用例** | ✅ **完成**(13 passed + 1 xfailed,用例幂等) |
| D | Allure 报告 | ⬜ 推迟到 11 月 |
| E | GitHub Actions CI + README 完善 | 🟡 CI 配置已就绪(`.github/workflows/ci.yml`),待推仓库 |
| F | (11 月)yaml 数据驱动 / Docker / Playwright / Locust | ⬜ |

**当前用例规模**:业务用例 **14 条**(认证 5 / CRUD 往返 1 / 分页信封 1 / 双端校验 2 / 统计 2 / 故障注入 3)+ mock 练习 **9 条** + 外网契约 1 条(`network` 标记,默认排除)。
**质量门禁**:`pytest -m "not network"` 全绿 · 契约冒烟 45/45 · `ruff check .` 通过 · 分层检查(裸路径/requests 计数为 0)。

---

## 四、目录导航

```
project1/
├── README.md                 ← 本文件(环境 & 架构确认表)
├── .env.example              ← 环境变量模板(真实值放 .env,不入库)
├── docs/                     ← 契约、架构、约定(每份都有 README)
├── api_server/               ← 被测系统(项目 A)
├── api_test/                 ← 测试框架(项目 B · 简历主体)
└── scripts/                  ← 一键验收脚本
```

每个目录下都有自己的 `README.md`,说明"放什么、谁负责、怎么跑"。
