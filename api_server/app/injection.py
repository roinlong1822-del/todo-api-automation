"""故障注入(仅测试环境生效,用于演示"接口成功但数据没落库")。

安全约束:
1. 默认关闭
2. 仅当 APP_ENV 属于 {dev, test, local} 时生效(生产禁用)
3. 生效时在响应头回显 X-Bug-Injected,便于测试断言"注入确实起了作用"
"""

import os

from fastapi import Request

INJECT_HEADER = "X-Inject-Bug"
INJECT_QUERY = "inject_bug"
WRITE_FAIL = "write_fail"
ALLOWED_ENVS = {"dev", "test", "local"}


def _injection_enabled() -> bool:
    return os.getenv("APP_ENV", "dev").lower() in ALLOWED_ENVS


async def fault_injection_middleware(request: Request, call_next):
    """把注入意图挂到 request.state,并在响应头回显。"""
    requested = request.headers.get(INJECT_HEADER) or request.query_params.get(INJECT_QUERY)
    request.state.inject_write_fail = bool(requested == WRITE_FAIL and _injection_enabled())

    response = await call_next(request)
    if request.state.inject_write_fail:
        response.headers["X-Bug-Injected"] = WRITE_FAIL
    return response


def write_fail_injected(request: Request) -> bool:
    """本请求是否要求"写操作假装成功"。"""
    return bool(getattr(request.state, "inject_write_fail", False))
