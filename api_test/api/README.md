# api_test/api/ — 业务接口层

一个接口一个方法,把"HTTP 细节"翻译成"业务语义":

```python
class TodoApi:
    def __init__(self, client): self.client = client
    def create_todo(self, title, priority=1): return self.client.post("/todos", json={...})
    def get_todo(self, todo_id):             return self.client.get(f"/todos/{todo_id}")
    def list_todos(self, page=1, size=10, keyword=None): ...
    def delete_todo(self, todo_id):          return self.client.delete(f"/todos/{todo_id}")
```

**约定**:用例只调本层(`todo_api.create_todo(...)`),不出现裸路径;接口变了只改这里。
