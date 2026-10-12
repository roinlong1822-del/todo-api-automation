"""多环境配置加载:YAML + 环境变量覆盖。

优先级(高 → 低):显式参数  >  APP_ENV 环境变量  >  <env>.yaml
<env>.yaml 必须写全 REQUIRED 中的键:缺键直接报错,不做隐式兜底,
避免"键名打错却静默回落到本地地址"这类假绿。
"""

import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent
REQUIRED = ("base_url", "timeout", "mock")


def load_config(env: str | None = None) -> dict:
    env = env or os.getenv("APP_ENV", "dev")
    path = CONFIG_DIR / f"{env}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}(可用 APP_ENV 指定 dev/test)")

    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [k for k in REQUIRED if k not in config]
    if missing:
        raise KeyError(f"{path.name} 缺少必填配置项: {missing}(现有键: {sorted(config)})")

    # 环境变量覆盖:CI/临时调试用,不改文件就能换目标
    if v := os.getenv("API_BASE_URL"):
        config["base_url"] = v
    if v := os.getenv("HTTP_TIMEOUT"):
        config["timeout"] = float(v)

    config["env"] = env  # env 是"选哪份 yaml"的输入,不由 yaml 提供
    return config
