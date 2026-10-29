import pytest

from api_server.app.models import Todo


def test_injected_create_returns_201_but_writes_nothing(inject_api, db):
    title = "inject-不该落库"
    r = inject_api.create_todo(title)

    # ① 单端视角:一切正常(这正是它可怕的地方)
    assert r.status_code == 201
    assert r.headers["X-Bug-Injected"] == "write_fail"   # 证明注入确实生效

    # ② 双端视角:库里根本没有
    db.expire_all()
    assert db.query(Todo).filter_by(title=title).first() is None, "库里有行,说明注入没生效"


def test_injected_delete_keeps_row_alive(todo_api, inject_api, db, created_todos):
    tid = todo_api.create_todo("inject-删不掉").json()["id"]
    created_todos.append(tid)

    r = inject_api.delete_todo(tid)
    assert r.status_code == 204                          # 假装删成功
    assert r.headers["X-Bug-Injected"] == "write_fail"

    db.expire_all()
    assert db.query(Todo).filter_by(id=tid).first().deleted == 0   # 实际没删
    assert todo_api.get_todo(tid).status_code == 200               # 接口上还查得到


@pytest.mark.xfail(strict=True, reason="单端断言会漏掉静默失败 —— 这正是双端校验存在的理由")
def test_single_end_assertion_is_fooled(inject_api, db):
    title = "inject-xfail-单端会漏"
    assert inject_api.create_todo(title).status_code == 201            # 单端:通过
    db.expire_all()
    assert db.query(Todo).filter_by(title=title).first() is not None   # 双端:必然失败
