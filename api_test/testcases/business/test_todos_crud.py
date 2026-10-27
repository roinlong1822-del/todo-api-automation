def test_create_get_delete_roundtrip(todo_api, created_todos):
    # create
    r = todo_api.create_todo("test_create_get_delete_roundtrip", priority=2)
    assert r.status_code == 201
    todo = r.json()
    assert todo["title"] == "test_create_get_delete_roundtrip"
    assert todo["priority"] == 2
    assert todo["status"] == "pending"

    todo_id = todo["id"]
    # 登记:软删除会留下 deleted=1 的行,靠夹具在用例结束时物理清掉
    created_todos.append(todo_id)

    # get
    r = todo_api.get_todo(todo_id)
    assert r.status_code == 200
    todo = r.json()
    assert todo["id"] == todo_id
    assert todo["title"] == "test_create_get_delete_roundtrip"

    # delete
    r = todo_api.delete_todo(todo_id)
    assert r.status_code == 204
    assert r.content == b""

    # get again
    r = todo_api.get_todo(todo_id)
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


def test_list_returns_pagination_envelope(todo_api):
    r = todo_api.list_todos(size=2)
    body = r.json()
    assert r.status_code == 200
    assert body["page"] == 1
    assert body["size"] == 2
    assert len(body["items"]) <= 2
    assert body["total"] >= len(body["items"])
