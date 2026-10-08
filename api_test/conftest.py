"""api_test 全局 fixture:数据源与客户端。

原则:
1. fixture 只提供「资源/通道」,**具体 stub 由用例自己注册**
   (fixture 先执行,它注册的同路径 stub 会遮住用例里注册的 stub)
2. 作用域:无共享可变状态 → `session`;会产生数据变更 → `function`
"""

import pytest

from data.sample_data import REMOTE
from utils.http_client import HttpClient

# 自建被测服务(api_server)的默认地址。
# 阶段 B 会改成从 config/ 读取,支持多环境切换。
LOCAL_SERVER = "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def server_api():
    """指向自建被测服务(api_server):只读通道,整个会话共用一个客户端。"""
    return HttpClient(LOCAL_SERVER, timeout=5)


@pytest.fixture
def mock_api(httpserver):
    """指向本地 mock 服务的客户端:每条用例一份干净的假服务。"""
    return HttpClient(httpserver.url_for(""), timeout=5)


@pytest.fixture(scope="session")
def remote_api():
    """真实外网通道:只给 @pytest.mark.network 的契约冒烟用例使用。"""
    return HttpClient(REMOTE, timeout=5)
