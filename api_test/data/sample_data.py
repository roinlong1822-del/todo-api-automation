"""测试数据与常量集中处。

为什么要单独一个模块:
- conftest.py 是 pytest 的**插件文件**,它里面的变量不会注入到测试模块,`from conftest import X` 是反模式;
- 常量放这里,conftest 和用例都 import 同一份 → 单一来源,不会"改一处忘一处"。
"""

# ---- 接口路径 ----
TODOS_1 = "/todos/1"
TODOS_2 = "/todos/2"

# ---- 假数据(字段名/类型与真实接口一致)----
TODO_1 = {"userId": 1, "id": 1, "title": "delectus aut autem", "completed": False}
TODO_2 = {"userId": 1, "id": 2, "title": "delectus aut autem", "completed": False}
TODO_LIST = [TODO_1, TODO_2]

# ---- 模拟服务端规则 ----
EXISTING_TODO_IDS = {1, 2}  # 只有这两个 id 存在,其余返回 404

# ---- 环境 ----
REMOTE = "https://jsonplaceholder.typicode.com"
