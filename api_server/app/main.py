"""api_server —— 被测服务入口。

启动(仓库根目录执行):
    uvicorn api_server.app.main:app --reload --port 8000
文档:http://127.0.0.1:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api_server.app import injection
from api_server.app.database import init_db
from api_server.app.errors import ApiError
from api_server.app.routers import auth, todos, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("api_server")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("api_server 启动完成,数据库已建表")
    yield


app = FastAPI(title="todo api server", version="1.0.0", lifespan=lifespan)
app.middleware("http")(injection.fault_injection_middleware)


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content={"code": exc.code, "message": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # 契约:参数校验失败统一 400 INVALID_PARAM(而不是 FastAPI 默认的 422)
    errors = exc.errors()
    detail = errors[0].get("msg") if errors else "参数不合法"
    return JSONResponse(status_code=400, content={"code": "INVALID_PARAM", "message": str(detail)})


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(todos.router)
