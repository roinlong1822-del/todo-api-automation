import time

import pytest
import requests
from werkzeug.wrappers import Response


def test_server_500_not_swallowed(mock_api, httpserver):
    """上游 500:客户端应把 500 原样返回,而不是抛异常或当成功"""
    httpserver.expect_request("/todos").respond_with_data("boom", status=500)
    r = mock_api.get("/todos")
    assert r.status_code == 500
    assert r.text == "boom"


def test_upstream_timeout_raises(mock_api, httpserver):
    """上游慢响应:客户端应抛 Timeout,不是无限等"""
    def slow(request):
        time.sleep(2)
        return Response("", status=200)

    httpserver.expect_request("/slow").respond_with_handler(slow)
    with pytest.raises(requests.exceptions.Timeout):
        mock_api.get("/slow", timeout=0.3)
