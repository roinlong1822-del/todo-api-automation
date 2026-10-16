def test_create_get_delete_roundtrip(todo_api):
    # create
    r = todo_api.create_todo("test_create_get_delete_roundtrip", priority=2)
    assert r.status_code == 201
    todo = r.json()
    assert todo["title"] == "test_create_get_delete_roundtrip"
    assert todo["priority"] == 2
    assert todo["status"] == "pending"

    id = todo["id"]
    # get
    r = todo_api.get_todo(id)
    assert r.status_code == 200
    todo = r.json()
    assert todo["id"] == id
    assert todo["title"] == "test_create_get_delete_roundtrip"

    # delete
    r = todo_api.delete_todo(id)
    assert r.status_code == 204
    assert r.content == b""

    # get again
    r = todo_api.get_todo(id)
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
