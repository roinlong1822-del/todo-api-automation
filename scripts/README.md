# scripts/ — 便捷脚本

| 文件 | 用途 |
|---|---|
| `run_checks.sh` | 一键验收:检查用例是否"不碰裸路径/URL/超时" + 跑本地用例 + ruff 检查 |

## 用法

```bash
cd projects/project1          # 脚本会自动切到仓库根,但建议从根调用
bash scripts/run_checks.sh
PY=/usr/bin/python3.12 bash scripts/run_checks.sh   # 指定解释器
```

**约定**:
- 脚本里不写死本机绝对路径(用相对路径或 `PY` 环境变量),避免换机器就跑不了
- 验收脚本要能直接进 CI:失败即以非 0 退出
