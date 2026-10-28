# testcases/business/test_todos_stats.py

def test_stats_counts_match_list_total(todo_api, db, created_todos):
    """stats 的 pending+done 应该等于列表接口的 total —— 两个接口互相校验。"""
    before = todo_api.get_stats().json()

    tid = todo_api.create_todo("stats-探针").json()["id"]
    created_todos.append(tid)

    after = todo_api.get_stats().json()
    assert after["pending"] + after["done"] == before["pending"] + before["done"] + 1
    assert after["pending"] == before["pending"] + 1          # 新建的是 pending
    assert todo_api.list_todos().json()["total"] == after["pending"] + after["done"]


def test_stats_requires_auth(anon_todo_api):
    r = anon_todo_api.get_stats()          # 未鉴权通道走同一个业务方法
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"
