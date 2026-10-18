#!/usr/bin/env bash
# 一键验收:在【仓库根】执行
#   用法:bash scripts/run_checks.sh
set -uo pipefail
cd "$(dirname "$0")/.."          # 切到仓库根,避免依赖调用位置

PY=${PY:-python3}                # 可用 PY=/path/to/python 覆盖

echo "== 1) 业务用例里不应出现裸请求细节(期望全为 0)=="
# 只查 business/:
#   - mock/ 用例天生要跟 httpserver 打交道(注册 stub、断言 log),"http" 只会命中 fixture 名,
#     裸路径在那边是【被测对象】,不算违规;
#   - 递归 + --include="*.py",避免命中 __pycache__ 的 .pyc 和 .md 里的讲解文字。
BIZ=api_test/testcases/business
bad=0
for kw in requests timeout http; do
  n=$(grep -rc "$kw" "$BIZ" --include="*.py" 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')
  printf '  %-9s -> %s\n' "$kw" "$n"
  [ "${n:-0}" -eq 0 ] || bad=1
done
n=$(grep -rEc '"/todos|"/login|"/users' "$BIZ" --include="*.py" 2>/dev/null | awk -F: '{s+=$2} END{print s+0}')
printf '  %-9s -> %s\n' "裸路径" "${n:-0}"
[ "${n:-0}" -eq 0 ] || bad=1
[ "$bad" -eq 0 ] || { echo "  ❌ 分层被破坏:业务用例里出现了 HTTP 细节或裸路径(应走 api/ 业务层)"; exit 1; }

echo "== 2) 跑本地稳定用例(network 标记的外网用例默认排除)=="
$PY -m pytest -m "not network" -v || exit 1

echo "== 3) 代码规范(全仓库,含 api_server/)=="
ruff check . || exit 1

echo "== 全部通过 =="
