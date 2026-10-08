# api_server/ — 被测系统(项目 A)

**定位**:配套被测对象。**不是简历主体**,但它是"可控、可注入故障、可做双端校验"的前提。

## 职责
- 提供 6 个 REST 接口(登录 / 当前用户 / 待办的增删查 + 分页搜索)
- SQLite 持久化(经 SQLAlchemy);种子数据一键初始化
- **故障注入开关**(Header `X-Inject-Bug: write_fail` 或 query `?inject_bug=write_fail`):
  让写接口"返回 200 但库里没写",用于演示"双端校验能抓住这类缺陷"
- 自动生成 OpenAPI 文档:`http://127.0.0.1:8000/docs`

## 启动(待实现后)
```bash
pip install -r requirements.txt
python -m api_server.app.seed            # 初始化种子数据
uvicorn api_server.app.main:app --reload --port 8000
```

## 目录
- `app/` 应用代码(FastAPI 入口、DB、模型、鉴权)
- `app/routers/` 路由(按业务分文件)

## 不做什么
不做前端 UI、不做分布式、不做完整权限体系、不部署生产。
