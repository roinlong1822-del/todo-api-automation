# test_api.py
import json

import pytest
from werkzeug import Response

from data.sample_data import EXISTING_TODO_IDS, TODO_1, TODO_2, TODOS_1


@pytest.fixture
def todo1_response(httpserver, mock_api):
    """拿到 /todos/1 的响应。

    stub 在这里注册(不放 conftest):谁需要谁声明,避免 fixture 的先注册 stub
    遮住用例里注册的同路径 stub。
    """
    httpserver.expect_request(TODOS_1).respond_with_json(TODO_1)
    return mock_api.get(TODOS_1)


def test_get_todo_status_code(todo1_response):
    assert todo1_response.status_code == 200


def test_get_todo_content_type(todo1_response):
    assert "application/json" in todo1_response.headers["Content-Type"]


def test_get_todo_field_values(todo1_response):
    body = todo1_response.json()
    assert body["id"] == 1
    assert body["userId"] == 1


def test_get_todo_field_types(todo1_response):
    body = todo1_response.json()
    assert isinstance(body["title"], str)
    assert isinstance(body["completed"], bool)


def test_get_todo_response_time(todo1_response):
    assert todo1_response.elapsed.total_seconds() < 1


def test_get_todo_list(mock_api, httpserver):
    httpserver.expect_request("/todos").respond_with_json([TODO_1, TODO_2])

    body = mock_api.get("/todos").json()

    assert isinstance(body, list)
    assert len(body) == 2
    assert all("id" in item for item in body)


def echo_query(request):
    """回显 handler:响应由「服务端收到的请求」推导 → 断言才有信息量。"""
    return Response(
        json.dumps({"q": request.args.get("q")}),
        status=200,
        content_type="application/json",
    )


@pytest.mark.parametrize("q", ["python", "java"], ids=["python", "java"])
def test_query_params_forwarded(mock_api, httpserver, q):
    httpserver.expect_request("/search").respond_with_handler(echo_query)

    body = mock_api.get("/search", params={"q": q}).json()

    assert body["q"] == q


def todo_server(request):
    """模拟服务端规则:id 从【请求】里解析,规则独立于用例参数。"""
    todo_id = int(request.path.rsplit("/", 1)[-1])
    if todo_id in EXISTING_TODO_IDS:
        return Response(json.dumps(TODO_1), status=200, content_type="application/json")
    return Response(json.dumps({"error": "Not Found"}), status=404, content_type="application/json")


def test_get_todo_ids(mock_api, httpserver):
    for path in ("/todos/1", "/todos/2", "/todos/999"):
        httpserver.expect_request(path).respond_with_handler(todo_server)

    r_ok = mock_api.get("/todos/1")
    r_ok2 = mock_api.get("/todos/2")
    r_missing = mock_api.get("/todos/999")

    assert r_ok.status_code == 200
    assert r_ok2.status_code == 200
    assert r_missing.status_code == 404
    # 断言请求本身(信息量最高):客户端确实把 id 拼进了路径
    assert [req.path for req, _ in httpserver.log] == ["/todos/1", "/todos/2", "/todos/999"]
    assert httpserver.handler_errors == [], httpserver.handler_errors


@pytest.mark.network
def test_smoke_remote_contract(remote_api):
    r = remote_api.get(TODOS_1)
    body = r.json()

    assert r.status_code == 200
    required = {"userId", "id", "title", "completed"}
    missing = required - set(body)
    assert not missing, f"响应缺少字段: {missing}"


