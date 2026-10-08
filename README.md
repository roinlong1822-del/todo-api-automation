# todo-api-automation · 待办服务接口自动化测试框架

> 一个从零搭建的**接口自动化测试框架**(项目 B),配套一个**自建被测服务**(项目 A)。
> 目的:演示"可控被测对象 + 分层框架 + 数据驱动 + 双端校验 + CI"的完整工程实践。

**当前状态**:🟡 阶段 B 前 —— 封装层与管理骨架就绪,待做多环境配置 / yaml 数据驱动 / 业务接口层 / 双端校验 / Allure / CI。

---

## 一、快速开始(全部实现后)

```bash
# 1) 起被测服务
pip install -r api_server/requirements.txt
python -m api_server.app.seed                      # 初始化种子数据
uvicorn api_server.app.main:app --reload --port 8000
# 浏览器打开 http://127.0.0.1:8000/docs 可交互

# 2) 跑测试
cd api_test
~/study/test/.venv/bin/python -m pytest -m "not network" -v      # 本地稳定用例
~/study/test/.venv/bin/python -m pytest -v                       # 全量(含外网冒烟)
~/study/test/.venv/bin/python -m pytest testcases/smoke -v       # 只跑冒烟
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
| 被测服务 | **FastAPI + Uvicorn** | 自动生成 `/docs` |
| ORM / 数据库 | **SQLAlchemy + SQLite**(`api_server.db`) | 换 MySQL 只改 `DATABASE_URL` |
| 配置 | **PyYAML + `.env`** | 环境变量覆盖 yaml;`.env` 不入库 |
| 日志 | 标准库 `logging` | 落文件 + 脱敏 |
| 报告 | `allure-pytest` | 阶段 D 接入 |
| 代码规范 | **ruff 0.16.8**(检查 + 格式化) | 保存时自动跑 |
| 版本控制 | **Git 2.43 + GitHub** | 公开前过一遍隐私清单 |
| 被测服务端口 | **8000** | 可用环境变量覆盖 |
| pytest rootdir | `api_test/`(`pythonpath = .`) | 保证 `from utils...` 可导入 |

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
- 用例里**不出现** URL、超时字面量、裸路径、`requests`
- `utils/` 与 `api/` **不写断言**(只搬事实,判断留给用例)
- 被测服务与测试框架**互不 import**(只通过 HTTP 交互)

### C. 接口契约摘要(详见 [`docs/API_SPEC.md`](docs/API_SPEC.md))

| 方法 | 路径 | 成功 | 关键异常 |
|---|---|---|---|
| POST | `/login` | 200 `{token, expires_in}` | 400 参数缺失 / 401 密码错 / 403 锁定 |
| GET | `/users/me` | 200 `{id, username}` | 401 无 token / 过期 |
| POST | `/todos` | **201** `{id, title, status}` | 400 title 空或超长 / 401 |
| GET | `/todos/{id}` | 200 todo | 404 不存在 / 400 id 非数字 |
| GET | `/todos` | 200 `{total, page, items[]}` | 400 size>50 |
| DELETE | `/todos/{id}` | 204 | 404 不存在 |
| ★ | 任意写接口 + `X-Inject-Bug: write_fail` | 200(**库里没写**) | 仅非生产环境生效 |

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

### F. 待你确认(打勾后开工)

- [ ] 仓库名用 **`todo-api-automation`**(GitHub 上可随时改)
- [ ] 提交身份:`user.name=roin`、`user.email=roin@users.noreply.github.com`(⚠️ **占位值,上线前换成你的 GitHub 用户名与 noreply 邮箱**)
- [ ] 被测服务端口 **8000**
- [ ] 数据库:项目内用 SQLite;**另做一次 MySQL 可切换验证**(1.5 小时)
- [ ] `scratch/`、`archive/`、`logs/` 保持本地不入库
- [ ] 故障注入开关:**Header 为主 + query 为辅,默认关闭,仅非生产生效**

---

## 三、里程碑与进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| A | 被测服务 `api_server`(6 接口 + SQLite + 种子 + 故障注入) | ⬜ 待开始 |
| B | 框架分层:config / data(yaml) / api 业务层 + 用例迁移 | 🟡 进行中(封装层已完成) |
| C | logging + 断言封装 + **双端校验** + 数据清理 | ⬜ |
| D | Allure 报告 | ⬜ |
| E | GitHub Actions CI + README 完善 | ⬜ |
| F | (11 月)Docker / Playwright / Locust | ⬜ |

**已完成**:`utils/http_client.py`(统一 base_url / 超时 / Session / 请求日志,返回 `Response`)、12 条用例设计清单、确定性 mock 与断言方法论沉淀在 `docs/`。

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
