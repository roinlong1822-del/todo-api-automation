from api.auth_api import AuthApi
from data.accounts import TESTER


def test_login_success_returns_token(auth_api):
    r = auth_api.login(TESTER["username"], TESTER["password"])
    assert r.status_code == 200
    body = r.json()
    token = body["token"]
    assert isinstance(token, str), f"token 应为字符串,实际 {type(token).__name__}: {token!r}"
    assert token, "token 不能为空字符串"
    assert body["expires_in"] > 0
    assert "Token-Expires-At" in r.headers


def test_login_unknown_user_returns_401(auth_api):
    r = auth_api.login("unknown_user", "any_password")
    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_CREDENTIALS"


def test_me_without_token_returns_401(auth_api):
    r = auth_api.me()
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"


def test_me_returns_current_user(authed_auth_api):
    r = authed_auth_api.me()
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == TESTER["username"]
    assert isinstance(body["id"], int)


def test_me_with_forged_token_returns_401(server_api):
    r = AuthApi(server_api, "forged.token").me()
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"
