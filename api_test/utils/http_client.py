import logging

import requests

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 5,
        session: requests.Session | None = None,
        default_headers: dict[str, str] | None = None,
    ):
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.timeout = timeout
        self.session = session if session else requests.Session()
        # 每条请求都会带上的头(token、故障注入开关等)
        self.default_headers = dict(default_headers or {})

    def with_headers(self, **headers: str) -> "HttpClient":
        """返回共享同一 Session、但多带若干默认头的新客户端。

        用途:故障注入等**测试专用开关**,不动业务层方法签名。
        """
        return HttpClient(
            self.base_url,
            self.timeout,
            self.session,
            {**self.default_headers, **headers},
        )

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        # 默认头 < 调用方显式 headers(显式优先)
        headers = {**self.default_headers, **(kwargs.pop("headers", None) or {})}
        if headers:
            kwargs["headers"] = headers
        response = self.session.request(method, url, **kwargs)
        logger.info(
            "[HTTP] %s %s -> %s %.2fs",
            method,
            response.url,
            response.status_code,
            response.elapsed.total_seconds()
        )
        return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
