"""本地演示服务的固定测试账号(与 docs/API_SPEC.md §8 种子数据一致)。

这些是【自建演示服务】的公开测试账号,可以入库;
真实环境的凭据必须走 .env / 环境变量,绝不写进代码或仓库。
"""

TESTER = {"username": "tester", "password": "Passw0rd!"}
OTHER = {"username": "other", "password": "Passw0rd!"}
LOCKED = {"username": "locked_user", "password": "Passw0rd!"}
