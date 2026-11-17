# -*- coding: utf-8 -*-
"""创建评测方案（绑定 Agent + 数据集 + 指标方案 + 运行参数）。

用法:
  python3 scripts/create_plan.py --name 冒烟方案 \
    --agent-id A --dataset-id D --metric-config-id M --num-runs 3 --pass-k 2
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="创建评测方案")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--dataset-id", help="单个数据集 id（方案最多绑定 1 个）")
    parser.add_argument("--metric-config-id")
    parser.add_argument("--num-runs", type=int, default=1, help="1-100")
    parser.add_argument("--pass-k", type=int, help="1-100，默认=num-runs，须 <=num-runs")
    parser.add_argument("--case-parallelism", type=int, default=4, help="1-32")
    parser.add_argument("--case-eval-parallelism", type=int, default=4, help="1-32")
    parser.add_argument("--no-check", action="store_true", help="跳过发起前预检（默认会校验对象存在性与 mode↔指标兼容性）")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.pass_k is not None and args.pass_k > args.num_runs:
        c.die(f"pass_k({args.pass_k}) 不能大于 num_runs({args.num_runs})")

    if not args.no_check:
        c.preflight_bindings(base, args.agent_id, args.dataset_id, args.metric_config_id)

    body = {
        "name": args.name,
        "num_runs": args.num_runs,
        "case_parallelism": args.case_parallelism,
        "case_eval_parallelism": args.case_eval_parallelism,
    }
    if args.agent_id:
        body["agent_id"] = args.agent_id
    if args.dataset_id:
        body["dataset_ids"] = [args.dataset_id]
    if args.metric_config_id:
        body["metric_config_id"] = args.metric_config_id
    if args.pass_k is not None:
        body["pass_k"] = args.pass_k

    resp = c.post(base, "/api/evaluation-plans", body)
    plan_id = resp.get("id") if isinstance(resp, dict) else None
    print(f"[ok] 已创建评测方案 id={plan_id} name={args.name}")
    print(f"发起（需用户授权）: python3 scripts/run_eval.py --plan-id {plan_id}")


if __name__ == "__main__":
    c.run_entrypoint(main)
