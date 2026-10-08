import requests


class HttpClient:
    def __init__(self, base_url: str, timeout: float = 5, session: requests.Session = None):
        self.base_url = base_url.rstrip("/")  # Remove trailing slash if present
        self.timeout = timeout
        self.session = session if session else requests.Session()

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.request(method, url, **kwargs)
        print(f"[HTTP] {method} {response.url} -> {response.status_code} "
              f"{response.elapsed.total_seconds():.2f}s")
        return response

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)
