"""api_test 全局 fixture:数据源与客户端。

原则:
1. fixture 只提供「资源/通道」,**具体 stub 由用例自己注册**
   (fixture 先执行,它注册的同路径 stub 会遮住用例里注册的 stub)
2. 作用域:无共享可变状态 → `session`;会产生数据变更 → `function`
3. 地址/超时等环境相关值一律来自 config/,本文件不出现任何硬编码地址
"""

import pytest

from config.loader import load_config
from data.sample_data import REMOTE
from utils.http_client import HttpClient


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
