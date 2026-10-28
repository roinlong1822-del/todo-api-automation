# curl 速查(接口排查第一工具)

> 为什么测开必须会:面试现场让你验接口不会给你 Postman;服务器上通常没有图形界面;
> 复现 bug 时一行命令就能贴给开发。浏览器只能发 GET、改不了 header —— **curl 能构造任意请求**。

---

## 1. 最小语法

```bash
curl [选项] URL
```

不带选项时:`curl http://127.0.0.1:8000/docs` → GET 并打印响应体。

## 2. 常用选项(够用 90% 场景)

| 选项 | 作用 | 例子 |
|---|---|---|
| `-X POST` | 指定方法(默认 GET) | `-X DELETE` |
| `-x http://proxy:port` | **走代理**(不是方法!) | `-x http://127.0.0.1:8888` |
| `-k` | 跳过 HTTPS 证书校验 | 配合代理抓包时常用 |
| `-u user:pass` | HTTP Basic 认证 | `-u tester:Passw0rd!` |
| `-H "K: V"` | 加请求头 | `-H "Authorization: Bearer $T"` |
| `-d '...'` | 请求体(隐含 POST) | `-d '{"title":"x"}'` |
| `-F 'k=v'` | 表单 / 文件上传 | `-F "file=@a.png"` |
| `-i` | 连响应**头**一起显示 | 查 `X-Bug-Injected` 这类自定义头必用 |
| `-I` | 只发 HEAD,拿响应头 | 和大写 `-X` 无关,别记混 |
| `-s` | 静默(不打印进度) | 脚本里必加 |
| `-o /dev/null` | 丢弃响应体 | 只关心状态码时 |
| `-w "%{http_code}"` | 自定义输出 | `-w "\n%{http_code}\n"` |
| `-v` | 详细(含握手/请求头) | 排查"头到底发出去没" |
| `--max-time 5` | 超时秒数 | **永远加上**,否则可能挂死 |
| `-L` | 跟随重定向 | |

### 大小写敏感,别记混(踩过的坑)

| 大写 | 小写 |
|---|---|
| `-X` 指定**方法** | `-x` 指定**代理** |
| `-I` 只拿**响应头**(HEAD) | `-i` **带上**响应头一起输出 |

## 2b. `-x` 代理:什么时候用

| 场景 | 命令 |
|---|---|
| **抓包**(Charles / Fiddler / mitmproxy) | `curl -x http://127.0.0.1:8888 -k https://example.com` |
| 公司网络必须走代理才能出网 | `curl -x http://proxy.corp:8080 http://…` |
| 排查"是不是代理导致的失败" | 加/去 `-x` 各跑一次对比 |

```bash
# 验证 -x 真的生效:指向一个不存在的代理 → 连接代理失败(exit 7)
curl -s -x http://127.0.0.1:9 http://127.0.0.1:8000/docs ; echo "exit=$?"
```

> 也可以用环境变量代替 `-x`:`export http_proxy=... https_proxy=...`
> —— **curl 和 Python 的 requests 都认这两个变量**。所以"明明 curl 能通、requests 不通"时,先查环境变量。

## 3. 本项目三步模板(所有业务接口都要 token)

```bash
BASE=http://127.0.0.1:8000

# ① 登录拿 token(存进 shell 变量)
TOKEN=$(curl -s -X POST $BASE/login \
  -H "Content-Type: application/json" \
  -d '{"username":"tester","password":"Passw0rd!"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

# ② 带 token 请求(看完整响应)
curl -s -i --max-time 5 -H "Authorization: Bearer $TOKEN" $BASE/todos/stats

# ③ 只要状态码(写脚本/CI 用)
curl -s -o /dev/null -w "%{http_code}\n" --max-time 5 \
  -H "Authorization: Bearer $TOKEN" $BASE/todos/stats
```

## 4. 三个必踩的坑

| 坑 | 现象 | 正解 |
|---|---|---|
| `-d` 没加 `Content-Type: application/json` | 服务端按表单解析 → `400 INVALID_PARAM` | 显式加 `-H "Content-Type: application/json"` |
| JSON 用单引号包,里面的中文/撇号出错 | shell 解析异常 | 用单引号包整体;内部别有单引号;中文可先写文件 `-d @file.json` |
| 忘了给 token / `Bearer ` 后少了空格 | `401 UNAUTHORIZED` | 先 `echo $TOKEN` 确认变量非空 |

## 5. 用 curl 排查接口的固定动作

1. **不带参数打一次** → 看错误码是 `400` 还是 `401`(400=参数问题,401=鉴权问题)
2. **加 `-i`** → 看响应头(自定义头、`Content-Type`、`Server`)
3. **加 `-v`** → 看请求头是不是真的发出去了(和你以为的一样吗)
4. **换一个工具对照** → 用 Python requests 再发一次,排除 shell 转义问题

## 6. 常见响应对照

| 状态码 | 本项目 code | 常见原因 |
|---|---|---|
| 400 | `INVALID_PARAM` | 参数缺失/类型错(含**路径参数解析失败**) |
| 401 | `UNAUTHORIZED` / `INVALID_CREDENTIALS` | 没带 token / token 无效 / 密码错 |
| 403 | `FORBIDDEN` / `ACCOUNT_LOCKED` | 越权 / 账号锁定 |
| 404 | `NOT_FOUND` | 资源不存在(含软删除后) |
| 422 | — | FastAPI 默认校验错(本项目已统一转 400,看到 422 说明转换没生效) |
