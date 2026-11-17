# -*- coding: utf-8 -*-
"""健康检查 + 已有对象清单，防止重复创建。

用法:
  python3 scripts/doctor.py --base-url http://127.0.0.1:8080
"""
from __future__ import annotations

import argparse

import _client as c

RESOURCES = [
    ("Agent", "/api/agents", "id", "name"),
    ("数据集", "/api/datasets", "id", "name"),
    ("指标方案", "/api/metric-configs", "id", "name"),
    ("评测方案", "/api/evaluation-plans", "id", "name"),
    ("模型配置", "/api/models", "name", "model_name"),
    ("命名密钥", "/api/secrets", None, None),
    ("环境变量", "/api/env-vars", None, None),
    ("行为检查", "/api/behavior-checks", "name", "description"),
    ("自定义工具", "/api/agent-tools", "name", None),
    ("响应解析", "/api/response-scorers", "name", None),
]


def _as_list(resp):
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for key in ("items", "agents", "datasets", "models", "metric_configs",
                    "plans", "checks", "tools", "scorers"):
            if isinstance(resp.get(key), list):
                return resp[key]
        # secrets / env-vars 是 name->masked 的 map
        return [{"name": k, "_masked": v} for k, v in resp.items()]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="评测系统健康检查与对象清单")
    c.add_base_url_arg(parser)
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    health = c.get(base, "/api/health")
    print(f"[health] {base} -> {health}")
    ws = c.get(base, "/api/workspace")
    if isinstance(ws, dict):
        print(f"[workdir] {ws.get('workdir')}")

    print("\n已存在对象：")
    for label, path, id_key, name_key in RESOURCES:
        try:
            items = _as_list(c.get(base, path))
        except c.ApiError as exc:
            print(f"  {label:8s}: 不可用（{exc.status}）")
            continue
        print(f"  {label:8s}: {len(items)} 个")
        for it in items[:10]:
            if not isinstance(it, dict):
                continue
            ident = it.get(id_key) if id_key else it.get("name")
            extra = it.get(name_key) if name_key and it.get(name_key) else ""
            print(f"      - {ident}  {extra}")
        if len(items) > 10:
            print(f"      ...（其余 {len(items) - 10} 个略）")

    print("\n提示：创建前先在此核对，避免重复。能力探索用 discover.py。")


if __name__ == "__main__":
    c.run_entrypoint(main)
