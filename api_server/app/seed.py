"""种子数据(★ 任务 4:你来实现,要求幂等 —— 重复执行不产生重复数据)。

要求:
1. 先建表(调用 database.init_db)
2. 三个用户(密码统一 "Passw0rd!",用 auth.hash_password 生成散列):
   - tester        正常账号 → 3 条 todo(2 条 pending、1 条 done)
   - locked_user   locked=True(锁定用例用)
   - other         正常账号 → 1 条 todo(越权用例用)
3. tester 的三条标题:一条英文、一条中文(编码用例用)
4. 幂等:已存在同名用户/同标题待办就跳过

自测:
    python -m api_server.app.seed
    python -c "import sqlite3;c=sqlite3.connect('api_server.db');print(c.execute('select username,locked from users').fetchall());print(c.execute('select count(*) from todos').fetchone())"
    # 期望:三个用户、todos 共 4 条;再跑一次数量不变
"""

import sys

from api_server.app.database import init_db


def seed() -> None:
    init_db()
    # TODO(任务 4):插入 3 个用户 + 4 条待办(幂等)
    raise NotImplementedError("实现 seed():建表 → 插用户 → 插待办,重复执行不重复插入")


if __name__ == "__main__":
    sys.exit(seed())
