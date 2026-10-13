#!/usr/bin/env bash
# 一键验收:在【仓库根】执行
#   用法:bash scripts/run_checks.sh
set -uo pipefail
cd "$(dirname "$0")/.."          # 切到仓库根,避免依赖调用位置

PY=${PY:-python3}                # 可用 PY=/path/to/python 覆盖

echo "== 1) 用例里不应出现裸请求细节(期望全为 0)=="
# 注意:用例按被测对象分了子目录(mock/ business/),glob 必须递归,否则会【静默地】
# 一条都匹配不到、永远打印 0 —— 比报错更危险。
for kw in requests http timeout; do
  printf '  %-9s -> %s\n' "$kw" "$(grep -rc "$kw" api_test/testcases --include="*.py" 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')"
done

echo "== 2) 跑本地稳定用例 =="
$PY -m pytest -m "not network" -v || exit 1

echo "== 3) 代码规范(全仓库,含 api_server/)=="
ruff check . || exit 1

echo "== 全部通过 =="
