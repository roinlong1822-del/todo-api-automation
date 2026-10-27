"""api_test 全局 fixture:数据源与客户端。

原则:
1. fixture 只提供「资源/通道」,**具体 stub 由用例自己注册**
   (fixture 先执行,它注册的同路径 stub 会遮住用例里注册的 stub)
2. 作用域:无共享可变状态 → `session`;会产生数据变更 → `function`
3. 地址/超时等环境相关值一律来自 config/,本文件不出现任何硬编码地址
"""
import logging
from pathlib import Path

import pytest

from api.auth_api import AuthApi
from api.todo_api import TodoApi
from api_server.app.database import SessionLocal, engine  # 顶部 import
from api_server.app.models import Todo
from config.loader import load_config
from data.accounts import TESTER
from data.sample_data import REMOTE
from utils.http_client import HttpClient

LOG_DIR = Path(__file__).parent / "logs"

# 第三方 logger:它们的访问日志会淹没我们自己的请求日志,统一压到 WARNING。
NOISY_LOGGERS = ("werkzeug", "urllib3", "http.client")

case_logger = logging.getLogger("testcase")


@pytest.fixture(autouse=True)
def _log_case_boundary(request):
    """每条用例前后各打一行,让 run.log 变成可回溯的时间线。"""
    case_logger.info(">>> %s", request.node.name)
    yield
    case_logger.info("<<< %s", request.node.name)


def pytest_configure(config):
    """pytest 启动时配一次日志:同时写文件和控制台。"""
    LOG_DIR.mkdir(exist_ok=True)
    root = logging.getLogger()
    if root.handlers:  # 防重复:重复挂 handler 会让每条日志打印多遍
        return
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s | %(message)s", datefmt="%H:%M:%S"
    )
    file_handler = logging.FileHandler(LOG_DIR / "run.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler()  # 默认写 stderr
    console_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # mock 用例走 pytest-httpserver(werkzeug),同一个请求会被客户端和服务端各记一遍,
    # 服务端那行还带 ANSI 颜色码 —— 重复且污染日志文件。
    for name in NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def app_config():
    """当前环境配置(由 APP_ENV 决定读哪份 yaml),整个会话只读一次。"""
    return load_config()


@pytest.fixture(scope="session")
def server_api(app_config):
    """指向自建被测服务(api_server):地址与超时来自 config/,不硬编码。"""
    return HttpClient(app_config["base_url"], timeout=app_config["timeout"])


@pytest.fixture
def mock_api(httpserver):
    """指向本地 mock 服务的客户端:每条用例一份干净的假服务。"""
    return HttpClient(httpserver.url_for(""), timeout=5)


@pytest.fixture(scope="session")
def remote_api():
    """真实外网通道:只给 @pytest.mark.network 的契约冒烟用例使用。"""
    return HttpClient(REMOTE, timeout=5)


@pytest.fixture(scope="session")
def auth_api(server_api) -> AuthApi:
    """**未鉴权**通道:登录接口用它(`/login` 是唯一不需要凭证的认证接口)。"""
    return AuthApi(server_api)


@pytest.fixture(scope="session")
def token(auth_api) -> str:
    """tester 的 token,整个会话只登录一次。"""
    r = auth_api.login(TESTER["username"], TESTER["password"])
    assert r.status_code == 200, f"登录失败,后续用例无法进行: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def authed_auth_api(server_api, token) -> AuthApi:
    """**已鉴权**通道:`/users/me` 的成功用例用它。

    它和 `auth_api` 的区别就是"带不带凭证":`auth_api` 调 `me()` 必然 401。
    想验"带着 token 能查到自己",用这个夹具 —— **不要在用例里给夹具赋 token**。
    """
    return AuthApi(server_api, token)


@pytest.fixture(scope="session")
def todo_api(server_api, token) -> TodoApi:
    """已鉴权通道:绝大多数待办用例用它。"""
    return TodoApi(server_api, token)


@pytest.fixture
def anon_todo_api(server_api) -> TodoApi:
    """未鉴权通道:401 用例用它。"""
    return TodoApi(server_api, None)

@pytest.fixture(scope="session", autouse=True)
def _check_db_target():
    """防呆:sqlite 路径是相对 cwd 的,必须从仓库根运行 pytest。"""
    if engine.url.get_backend_name() == "sqlite":
        db_file = Path(engine.url.database).resolve()
        assert db_file.exists(), (
            f"数据库文件不存在: {db_file}\n"
            "双端校验必须在【仓库根】运行 pytest,否则会连到另一个空库。"
        )


@pytest.fixture
def db():
    """直连数据库的 Session:只用于**校验与清理**,不拿它造业务数据。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def created_todos(db):
    """登记本用例创建的 id,结束时【物理删除】,保证种子数据不被污染。"""
    ids: list[int] = []
    yield ids
    for todo_id in ids:
        row = db.query(Todo).filter_by(id=todo_id).first()
        if row:
            db.delete(row)
    db.commit()
