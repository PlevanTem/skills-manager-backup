# -*- coding: utf-8 -*-
"""向数据集追加一个用例（POST /api/datasets/{id}/cases）。

API 用例只支持有限字段：user_text / expected_output / actual_output /
tool_calls / final_behavior / final_behavior_match(es) / final_response_pattern。
需要 tool_responses、多轮 session_input.state、conversation_scenario、context_messages
的复杂场景，请改用完整 .evalset.json 通过 create_dataset.py --source upload 上传。

用法:
  python3 scripts/add_case.py --dataset-id <id> --template case.normal
  python3 scripts/add_case.py --dataset-id <id> --case @mycase.json
  python3 scripts/add_case.py --dataset-id <id> --user-text "你好" --expected-output "您好"
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="向数据集追加用例")
    c.add_base_url_arg(parser)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--template", help="templates/dataset/<名>.json（CaseCreate 结构）")
    parser.add_argument("--case", help="CaseCreate JSON 字符串或 @文件")
    # 单 invocation 简易构造
    parser.add_argument("--eval-id")
    parser.add_argument("--user-text")
    parser.add_argument("--expected-output")
    parser.add_argument("--final-response-pattern")
    parser.add_argument("--final-behavior")
    parser.add_argument("--final-behavior-match", help="单个行为检查器名")
    parser.add_argument("--final-behavior-matches", nargs="*", help="多个行为检查器名")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.template:
        body = c.load_template("dataset", args.template)
    elif args.case:
        body = c.read_json_arg(args.case)
    elif args.user_text:
        inv = {"user_text": args.user_text}
        for key in ("expected_output", "final_response_pattern", "final_behavior", "final_behavior_match"):
            val = getattr(args, key)
            if val is not None:
                inv[key] = val
        if args.final_behavior_matches:
            inv["final_behavior_matches"] = args.final_behavior_matches
        body = {"invocations": [inv]}
        if args.eval_id:
            body["eval_id"] = args.eval_id
    else:
        c.die("需提供 --template / --case / --user-text 之一")

    _warn_case_shape(body)

    resp = c.post(base, f"/api/datasets/{args.dataset_id}/cases", body)
    case = (resp.get("case") if isinstance(resp, dict) else None) or resp
    eval_id = case.get("eval_id") if isinstance(case, dict) else None
    print(f"[ok] 已追加用例 eval_id={eval_id}")
    _print_usable_metrics(body)


# 用例字段 → 可被哪类指标使用（帮助在加用例当下就对齐指标，避免发起时才失败）
_RESP_SIGNALS = ("expected_output", "final_response_pattern")
_BEHAVIOR_SIGNALS = ("final_behavior", "final_behavior_match", "final_behavior_matches")
_TRAJ_SIGNALS = ("tool_calls",)
_ALL_SIGNALS = _RESP_SIGNALS + _BEHAVIOR_SIGNALS + _TRAJ_SIGNALS


def _invocations(body):
    invs = body.get("invocations") if isinstance(body, dict) else None
    return [i for i in invs if isinstance(i, dict)] if isinstance(invs, list) else []


def _warn_case_shape(body):
    invs = _invocations(body)
    if not invs:
        return
    def has_signal(inv):
        return any(inv.get(k) for k in _ALL_SIGNALS)
    if not all(has_signal(i) for i in invs):
        print("[提示] 有 invocation 缺少评分依据（expected_output / final_response_pattern / "
              "final_behavior* / tool_calls）；多数指标将无法对它打分（trace 回放或仅靠 prompt 的裁判除外）。")


def _print_usable_metrics(body):
    invs = _invocations(body)
    present = {k for inv in invs for k in _ALL_SIGNALS if inv.get(k)}
    if not present:
        return
    usable = []
    if present & set(_RESP_SIGNALS):
        usable.append("final_response_avg_score / llm_final_response / llm_rubric_*")
    if present & set(_BEHAVIOR_SIGNALS):
        usable.append("final_behavior_avg_score / llm_final_behavior")
    if present & set(_TRAJ_SIGNALS):
        usable.append("tool_trajectory_avg_score")
    if usable:
        print("[可用指标] 据本用例字段，可配：" + "；".join(usable))


if __name__ == "__main__":
    c.run_entrypoint(main)
