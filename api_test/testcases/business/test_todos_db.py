from api_server.app.models import Todo


def test_created_todo_exists_in_db(todo_api, db, created_todos):
    title = "dbcheck-created"
    r = todo_api.create_todo(title, priority=3)
    assert r.status_code == 201
    tid = r.json()["id"]
    created_todos.append(tid)

    db.expire_all()
    row = db.query(Todo).filter_by(id=tid).first()
    assert row is not None, "接口说创建成功,库里却没有 —— 双端校验抓到了"
    assert (row.title, row.priority, row.status, row.deleted) == (title, 3, "pending", 0)
    assert row.user_id > 0

def test_soft_deleted_todo_row_remains_in_db(todo_api, db, created_todos):
    title = "dbcheck-soft-delete"
    tid = todo_api.create_todo(title).json()["id"]
    created_todos.append(tid)

    db.expire_all()
    assert db.query(Todo).filter_by(id=tid).first().deleted == 0   # ← 新增:删除前先记一笔

    assert todo_api.delete_todo(tid).status_code == 204

    db.expire_all()                                                 # ★ 不刷新会读到上面的旧值
    row = db.query(Todo).filter_by(id=tid).first()
    assert row is not None, "行被物理删除了 —— 契约要求软删除"
    assert row.deleted == 1
    assert todo_api.get_todo(tid).status_code == 404
