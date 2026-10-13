"""认证接口封装:登录、查询当前用户。"""

import requests

from utils.http_client import HttpClient


class AuthApi:
    def __init__(self, client: HttpClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def login(self, username: str, password: str) -> requests.Response:
        """POST /login → 200 {token, expires_in};密码错 401;锁定 403。"""
        return self.client.post("/login", json={"username": username, "password": password})

    def me(self) -> requests.Response:
        """GET /users/me → 200 {id, username};无 token / token 无效 → 401。"""
        return self.client.get("/users/me", headers=self._headers())

    def _headers(self) -> dict[str, str]:
        """Bearer 前缀是业务知识,留在本层。"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
