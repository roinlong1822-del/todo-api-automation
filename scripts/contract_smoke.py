"""被测服务契约冒烟(对照 docs/API_SPEC.md;需先启动 api_server)。

import requests

BASE = "http://127.0.0.1:8000"
results = []


def check(name, got, want):
    ok = got == want
    results.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<46} got={got!r} want={want!r}")


s = requests.Session()

# ---------- 登录 ----------
r = s.post(f"{BASE}/login", json={"username": "tester", "password": "Passw0rd!"}, timeout=5)
check("POST /login 正确凭据 -> 200", r.status_code, 200)
token = r.json().get("token", "")
check("login 返回 token 非空", bool(token), True)
check("login 返回 Token-Expires-At 头", "Token-Expires-At" in r.headers, True)
H = {"Authorization": f"Bearer {token}"}

r = s.post(f"{BASE}/login", json={"username": "tester"}, timeout=5)
check("POST /login 缺 password -> 400", r.status_code, 400)
check("  code=INVALID_PARAM", r.json().get("code"), "INVALID_PARAM")

r = s.post(f"{BASE}/login", json={"username": "tester", "password": "wrong"}, timeout=5)
check("POST /login 密码错 -> 401", r.status_code, 401)
check("  code=INVALID_CREDENTIALS", r.json().get("code"), "INVALID_CREDENTIALS")

r = s.post(f"{BASE}/login", json={"username": "no_such_user", "password": "x"}, timeout=5)
check("POST /login 用户不存在 -> 401(不暴露存在性)", r.status_code, 401)

r = s.post(f"{BASE}/login", json={"username": "locked_user", "password": "Passw0rd!"}, timeout=5)
check("POST /login 已锁定账号 -> 403", r.status_code, 403)
check("  code=ACCOUNT_LOCKED", r.json().get("code"), "ACCOUNT_LOCKED")

# ---------- 鉴权 ----------
r = s.get(f"{BASE}/users/me", timeout=5)
check("GET /users/me 无 token -> 401", r.status_code, 401)
r = s.get(f"{BASE}/users/me", headers=H, timeout=5)
check("GET /users/me 带 token -> 200", r.status_code, 200)
check("  username=tester", r.json().get("username"), "tester")
r = s.get(f"{BASE}/users/me", headers={"Authorization": "Bearer bad.token"}, timeout=5)
check("GET /users/me 伪造 token -> 401", r.status_code, 401)

# ---------- 创建 + 边界 ----------
r = s.post(f"{BASE}/todos", json={"title": "新任务"}, headers=H, timeout=5)
check("POST /todos -> 201", r.status_code, 201)
new_id = r.json().get("id")
check("  返回 id 非空", bool(new_id), True)
check("  status=pending", r.json().get("status"), "pending")

check("POST /todos title 为空 -> 400",
      s.post(f"{BASE}/todos", json={"title": ""}, headers=H, timeout=5).status_code, 400)
check("POST /todos title=101 位 -> 400",
      s.post(f"{BASE}/todos", json={"title": "x" * 101}, headers=H, timeout=5).status_code, 400)
check("POST /todos title=1 位 -> 201",
      s.post(f"{BASE}/todos", json={"title": "x"}, headers=H, timeout=5).status_code, 201)
check("POST /todos title=100 位 -> 201",
      s.post(f"{BASE}/todos", json={"title": "x" * 100}, headers=H, timeout=5).status_code, 201)
check("POST /todos priority=4 -> 400",
      s.post(f"{BASE}/todos", json={"title": "ok", "priority": 4}, headers=H, timeout=5).status_code, 400)
check("POST /todos priority=0 -> 400",
      s.post(f"{BASE}/todos", json={"title": "ok", "priority": 0}, headers=H, timeout=5).status_code, 400)

# ---------- 查询单条 ----------
check("GET /todos/{id} -> 200", s.get(f"{BASE}/todos/{new_id}", headers=H, timeout=5).status_code, 200)
check("GET /todos/999999 -> 404", s.get(f"{BASE}/todos/999999", headers=H, timeout=5).status_code, 404)
check("GET /todos/abc -> 400(不是 422)", s.get(f"{BASE}/todos/abc", headers=H, timeout=5).status_code, 400)

# ---------- 列表 / 分页 / 搜索 ----------
r = s.get(f"{BASE}/todos", headers=H, timeout=5)
check("GET /todos -> 200", r.status_code, 200)
check("  返回 total/page/size/items", sorted(r.json().keys()), ["items", "page", "size", "total"])
check("GET /todos?size=2 -> items 长度 2",
      len(s.get(f"{BASE}/todos", params={"size": 2}, headers=H, timeout=5).json()["items"]), 2)
check("GET /todos?size=51 -> 400",
      s.get(f"{BASE}/todos", params={"size": 51}, headers=H, timeout=5).status_code, 400)
check("GET /todos?page=0 -> 400",
      s.get(f"{BASE}/todos", params={"page": 0}, headers=H, timeout=5).status_code, 400)
check("GET /todos?keyword=周报 -> total=1",
      s.get(f"{BASE}/todos", params={"keyword": "周报"}, headers=H, timeout=5).json()["total"], 1)
check("GET /todos?status=done -> total>=1",
      s.get(f"{BASE}/todos", params={"status": "done"}, headers=H, timeout=5).json()["total"] >= 1, True)
r = s.get(f"{BASE}/todos", params={"keyword": "不存在的关键字xyz"}, headers=H, timeout=5)
check("GET /todos 无匹配 -> 200 且 total=0", (r.status_code, r.json()["total"]), (200, 0))

# ---------- 越权 ----------
r = s.post(f"{BASE}/login", json={"username": "other", "password": "Passw0rd!"}, timeout=5)
H2 = {"Authorization": f"Bearer {r.json()['token']}"}
r = s.get(f"{BASE}/todos/{new_id}", headers=H2, timeout=5)
check("他人访问我的 todo -> 403", r.status_code, 403)
check("  code=FORBIDDEN", r.json().get("code"), "FORBIDDEN")

# ---------- 软删除 ----------
check("DELETE /todos/{id} -> 204", s.delete(f"{BASE}/todos/{new_id}", headers=H, timeout=5).status_code, 204)
check("删除后再查 -> 404", s.get(f"{BASE}/todos/{new_id}", headers=H, timeout=5).status_code, 404)
check("重复删除 -> 404(幂等)", s.delete(f"{BASE}/todos/{new_id}", headers=H, timeout=5).status_code, 404)

# ---------- 故障注入(双端校验的关键) ----------
before = s.get(f"{BASE}/todos", headers=H, timeout=5).json()["total"]
r = s.post(f"{BASE}/todos", json={"title": "注入的任务"},
           headers={**H, "X-Inject-Bug": "write_fail"}, timeout=5)
check("注入后 POST /todos 仍返回 201", r.status_code, 201)
check("  响应头回显 X-Bug-Injected", r.headers.get("X-Bug-Injected"), "write_fail")
after = s.get(f"{BASE}/todos", headers=H, timeout=5).json()["total"]
check("  但列表总数没变(数据没落库)", after, before)
r = s.get(f"{BASE}/todos", params={"inject_bug": "write_fail"}, headers=H, timeout=5)
check("  query 形式注入也可用", r.headers.get("X-Bug-Injected"), "write_fail")

print(f"\n汇总:{sum(results)}/{len(results)} 通过")
raise SystemExit(0 if all(results) else 1)
