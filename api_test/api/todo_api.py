"""todo 接口封装: 创建、查询、删除 todo 项"""

import requests

from utils.http_client import HttpClient


class TodoApi:
    def __init__(self, client: HttpClient, token: str | None = None) -> None:
        self.client = client
        self.token = token

    def create_todo(self, title: str, priority: int = 1) -> requests.Response:
        """POST /todos → 201 todo 对象;title 空/超长、priority 越界 → 400"""
        return self.client.post(
            "/todos", json={"title": title, "priority": priority}, headers=self._headers()
        )

    def get_todo(self, todo_id: int | str) -> requests.Response:
        """GET /todos/{id} → 200 / 404 / 403"""
        return self.client.get(f"/todos/{todo_id}", headers=self._headers())

    def list_todos(
        self,
        page: int = 1,
        size: int = 10,
        keyword: str | None = None,
        status: str | None = None,
    ) -> requests.Response:
        """GET /todos?page=&size=&keyword=&status= → 200 {total, page, size, items}"""
        params = {"page": page, "size": size}
        if keyword is not None:
            params["keyword"] = keyword
        if status is not None:
            params["status"] = status
        return self.client.get("/todos", params=params, headers=self._headers())

    def delete_todo(self, todo_id: int | str) -> requests.Response:
        """DELETE /todos/{id} → 204 无 body / 404"""
        return self.client.delete(f"/todos/{todo_id}", headers=self._headers())

    def _headers(self) -> dict[str, str]:
        """Bearer 前缀是业务知识,留在本层。"""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
