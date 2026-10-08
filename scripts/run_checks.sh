#!/usr/bin/env bash
# 一键验收:在【仓库根】执行
#   用法:bash scripts/run_checks.sh
set -uo pipefail
cd "$(dirname "$0")/.."          # 切到仓库根,避免依赖调用位置

PY=${PY:-python3}                # 可用 PY=/path/to/python 覆盖

echo "== 1) 用例里不应出现裸请求细节(期望全为 0)=="
for kw in requests http timeout; do
  printf '  %-9s -> %s\n' "$kw" "$(grep -c "$kw" api_test/testcases/*.py 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')"
done

echo "== 2) 跑本地稳定用例 =="
$PY -m pytest -m "not network" -v || exit 1

echo "== 3) 代码规范 =="
ruff check . || exit 1

echo "== 全部通过 =="
