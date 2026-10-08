"""业务异常:统一错误响应体 {"code": "...", "message": "..."}。

用例断言 `code`(稳定),不断言 `message` 文案(会改)。
"""


class ApiError(Exception):
    """带 HTTP 状态码的业务异常。"""

    def __init__(self, code: str, http_status: int, message: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.message = message or code


def invalid_param(message: str = "参数不合法") -> ApiError:
    return ApiError("INVALID_PARAM", 400, message)


def unauthorized(message: str = "未认证或 token 无效") -> ApiError:
    return ApiError("UNAUTHORIZED", 401, message)


def invalid_credentials() -> ApiError:
    return ApiError("INVALID_CREDENTIALS", 401, "用户名或密码错误")


def account_locked() -> ApiError:
    return ApiError("ACCOUNT_LOCKED", 403, "账号已锁定,请联系管理员")


def not_found(message: str = "资源不存在") -> ApiError:
    return ApiError("NOT_FOUND", 404, message)


def forbidden(message: str = "无权访问该资源") -> ApiError:
    return ApiError("FORBIDDEN", 403, message)
