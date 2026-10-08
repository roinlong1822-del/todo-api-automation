#!/bin/bash

cd ~/study/test/projects/api_test
grep -c "requests" test_api/test_api.py    # 期望 0(用例不直接碰 requests)
grep -c "http"     test_api/test_api.py    # 期望 0(不出现 URL)
grep -c "timeout"  test_api/test_api.py    # 期望 0(超时由客户端兜底)
pytest -m "not network" -v                 # 全绿
pytest -m "not network" -v                 # 连跑两次结果一致
ruff check .                               # 无 error
