# -*- coding: utf-8 -*-
"""列举单类资源（含关键字段），用于查询 id/name 以便后续绑定。

用法:
  python3 scripts/list_resources.py --type agents
  python3 scripts/list_resources.py --type datasets --json
"""
from __future__ import annotations

import argparse

import _client as c

TYPE_PATHS = {
    "agents": "/api/agents",
    "datasets": "/api/datasets",
    "metric-configs": "/api/metric-configs",
    "plans": "/api/evaluation-plans",
    "evaluations": "/api/evaluations",
    "models": "/api/models",
    "secrets": "/api/secrets",
    "env-vars": "/api/env-vars",
    "behavior-checks": "/api/behavior-checks",
    "agent-tools": "/api/agent-tools",
    "response-scorers": "/api/response-scorers",
}


def _as_list(resp):
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for key in ("items", "agents", "datasets", "models", "metric_configs",
                    "plans", "evaluations", "checks", "tools", "scorers"):
            if isinstance(resp.get(key), list):
                return resp[key]
        return [{"name": k, "masked": v} for k, v in resp.items()]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="列举单类资源")
    c.add_base_url_arg(parser)
    parser.add_argument("--type", required=True, choices=sorted(TYPE_PATHS), help="资源类型")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    resp = c.get(base, TYPE_PATHS[args.type])
    if args.json:
        c.print_json(resp)
        return
    items = _as_list(resp)
    print(f"{args.type}: {len(items)} 个")
    for it in items:
        if not isinstance(it, dict):
            print(f"  - {it}")
            continue
        ident = it.get("id") or it.get("name") or it.get("eval_id")
        label = it.get("name") or it.get("model_name") or it.get("status") or ""
        print(f"  - {ident}\t{label}")


if __name__ == "__main__":
    c.run_entrypoint(main)
