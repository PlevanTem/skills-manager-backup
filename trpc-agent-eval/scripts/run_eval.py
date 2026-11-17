# -*- coding: utf-8 -*-
"""发起评测。

!!! 红线：评测会消耗模型额度与时间，必须在用户显式授权后才运行。!!!
脚本默认要求 --i-am-authorized 标志，缺失时拒绝执行并提示。

两种发起方式：
  - 方案发起：--plan-id（自动创建 batch，pass_k 取自方案）。
  - 直接发起：--agent-id + --dataset-id + --metric-config-id（pass_k 默认=num_runs）。

用法:
  python3 scripts/run_eval.py --plan-id P --i-am-authorized
  python3 scripts/run_eval.py --agent-id A --dataset-id D --metric-config-id M --num-runs 3 --i-am-authorized
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="发起评测（需用户授权）")
    c.add_base_url_arg(parser)
    parser.add_argument("--plan-id", help="按评测方案发起")
    parser.add_argument("--agent-id")
    parser.add_argument("--dataset-id")
    parser.add_argument("--metric-config-id")
    parser.add_argument("--num-runs", type=int, default=1)
    parser.add_argument("--i-am-authorized", action="store_true", help="确认用户已授权发起评测")
    parser.add_argument("--no-check", action="store_true", help="跳过发起前预检（默认会校验绑定对象与 mode↔指标兼容性）")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if not args.i_am_authorized:
        c.die("未授权：发起评测前需用户明确同意。确认后加 --i-am-authorized 重试。")

    if not args.no_check:
        _preflight_and_preview(base, args)

    if args.plan_id:
        resp = c.post(base, f"/api/evaluation-plans/{args.plan_id}/run", {})
    elif args.agent_id and args.dataset_id and args.metric_config_id:
        resp = c.post(base, "/api/evaluations", {
            "agent_id": args.agent_id,
            "dataset_ids": [args.dataset_id],
            "metric_config_id": args.metric_config_id,
            "num_runs": args.num_runs,
        })
    else:
        c.die("需 --plan-id，或同时给 --agent-id/--dataset-id/--metric-config-id")
        return

    eval_id = resp.get("id") if isinstance(resp, dict) else None
    print(f"[ok] 已发起评测 id={eval_id} status={resp.get('status') if isinstance(resp, dict) else '?'}")
    print(f"查看进度/结果: python3 scripts/get_result.py --id {eval_id} --watch")


def _preflight_and_preview(base, args):
    """直接路径/方案路径都做发起前预检，并打印一行成本预览（授权依据）。"""
    if args.plan_id:
        try:
            plan = c.get(base, f"/api/evaluation-plans/{args.plan_id}")
        except c.ApiError:
            c.die(f"评测方案不存在或无法读取：id={args.plan_id}")
        agent_id = plan.get("agent_id")
        dataset_id = (plan.get("dataset_ids") or [None])[0]
        metric_id = plan.get("metric_config_id")
        num_runs = plan.get("num_runs") or 1
    else:
        agent_id, dataset_id, metric_id, num_runs = args.agent_id, args.dataset_id, args.metric_config_id, args.num_runs
        if not (agent_id and dataset_id and metric_id):
            return  # 参数不全，交给后续逻辑报错

    objs = c.preflight_bindings(base, agent_id, dataset_id, metric_id)
    _print_cost_preview(objs, num_runs)


def _print_cost_preview(objs, num_runs):
    dataset = objs.get("dataset") or {}
    metric = objs.get("metric") or {}
    cases = dataset.get("case_count")
    definition = metric.get("definition") or {}
    metrics = definition.get("metrics") if isinstance(definition, dict) else definition
    names = [m.get("metric_name") or m.get("name") for m in (metrics or []) if isinstance(m, dict)]
    uses_llm = any(str(n).startswith("llm_") for n in names)
    total = f"{cases * num_runs}" if isinstance(cases, int) else "?"
    llm_note = "，含 LLM 裁判（消耗模型额度）" if uses_llm else "，无 LLM 裁判（不耗模型额度）"
    print(f"[预览] num_runs={num_runs} × 用例={cases if cases is not None else '?'} ≈ {total} 次被测调用{llm_note}")


if __name__ == "__main__":
    c.run_entrypoint(main)
