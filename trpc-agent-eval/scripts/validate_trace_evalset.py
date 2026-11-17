# -*- coding: utf-8 -*-
"""Validate trace EvalSet files and recommend usable metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _trace_mapping import load_jsonish, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="校验 trace .evalset.json 并输出质量报告")
    parser.add_argument("--file", required=True, help=".evalset.json 文件")
    parser.add_argument("--audit", help="convert_trace_to_evalset.py 生成的 audit JSON")
    parser.add_argument("--json-out", help="输出 JSON 报告")
    args = parser.parse_args()

    data = load_jsonish(Path(args.file))
    audit = load_jsonish(Path(args.audit)) if args.audit else None
    report = validate_evalset(data, audit)
    if args.json_out:
        write_json(Path(args.json_out), report)
    print_report(report)
    if not report["summary"]["loadable"]:
        raise SystemExit(1)


def validate_evalset(data: Any, audit: Any = None) -> dict[str, Any]:
    errors = []
    sdk_error = None
    sdk_loadable = False
    try:
        from trpc_agent_self_evolution import EvalSet  # type: ignore

        EvalSet.model_validate(data)
        sdk_loadable = True
    except Exception as exc:  # pragma: no cover - depends on local SDK install
        sdk_error = str(exc)
    if not isinstance(data, dict):
        errors.append("EvalSet root must be object")
        cases = []
    else:
        cases = data.get("eval_cases") or []
        if not isinstance(cases, list):
            errors.append("eval_cases must be list")
            cases = []
    stats = scan_cases(cases, errors)
    fallback_loadable = not errors
    loadable = sdk_loadable or fallback_loadable
    metrics = recommend_metrics(stats)
    audit_summary = audit.get("summary") if isinstance(audit, dict) else None
    return {
        "summary": {
            "loadable": loadable,
            "sdk_loadable": sdk_loadable,
            "sdk_error": sdk_error if not sdk_loadable else None,
            "case_count": len(cases),
            **stats,
        },
        "errors": errors,
        "audit_summary": audit_summary,
        "recommended_metrics": metrics,
    }


def scan_cases(cases: list[Any], errors: list[str]) -> dict[str, int]:
    stats = {
        "trace_cases": 0,
        "actual_invocations": 0,
        "expected_invocations": 0,
        "final_responses": 0,
        "expected_references": 0,
        "tool_uses": 0,
        "tool_responses": 0,
        "missing_actual_conversation": 0,
    }
    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case[{idx}] must be object")
            continue
        if case.get("eval_mode") != "trace":
            errors.append(f"case[{idx}] eval_mode must be trace")
            continue
        stats["trace_cases"] += 1
        actual = case.get("actual_conversation")
        if not actual:
            stats["missing_actual_conversation"] += 1
            errors.append(f"case[{idx}] missing actual_conversation")
            continue
        if not isinstance(actual, list):
            errors.append(f"case[{idx}] actual_conversation must be list")
            continue
        stats["actual_invocations"] += len(actual)
        expected = case.get("conversation") or []
        if isinstance(expected, list):
            stats["expected_invocations"] += len(expected)
            for invocation in expected:
                if isinstance(invocation, dict) and (invocation.get("final_response") or invocation.get("final_response_pattern")):
                    stats["expected_references"] += 1
        for invocation in actual:
            if not isinstance(invocation, dict):
                continue
            if invocation.get("final_response"):
                stats["final_responses"] += 1
            intermediate = invocation.get("intermediate_data") or {}
            if isinstance(intermediate, dict):
                stats["tool_uses"] += len(intermediate.get("tool_uses") or [])
                stats["tool_responses"] += len(intermediate.get("tool_responses") or [])
    return stats


def recommend_metrics(stats: dict[str, int]) -> dict[str, Any]:
    available: list[str] = []
    unavailable: dict[str, str] = {}
    if stats["expected_references"] > 0 and stats["final_responses"] > 0:
        available.extend(["final_response_avg_score", "llm_final_response", "llm_rubric_response"])
    else:
        unavailable["final_response_avg_score"] = "缺少 expected final_response 或实际 final_response"
        unavailable["llm_final_response"] = "缺少 expected final_response 或实际 final_response"
    if stats["tool_uses"] > 0:
        available.append("tool_trajectory_avg_score")
    else:
        unavailable["tool_trajectory_avg_score"] = "缺少 tool_uses，无法比较工具轨迹"
    if stats["tool_responses"] > 0 and stats["final_responses"] > 0:
        available.extend(["llm_hallucinations", "llm_rubric_knowledge_recall"])
    else:
        unavailable["llm_hallucinations"] = "缺少 tool_responses，无法可靠核验 grounding"
        unavailable["llm_rubric_knowledge_recall"] = "缺少 tool_responses，无法判断检索内容覆盖率"
    return {"available": list(dict.fromkeys(available)), "unavailable": unavailable}


def print_report(report: dict[str, Any]) -> None:
    summary = report["summary"]
    metrics = report["recommended_metrics"]
    print(f"[ok] loadable={summary['loadable']} cases={summary['case_count']} trace_cases={summary['trace_cases']}")
    if metrics["available"]:
        print("[ok] 可用指标: " + ", ".join(metrics["available"]))
    for name, reason in metrics["unavailable"].items():
        print(f"[warn] 不可用 {name}: {reason}")
    for error in report.get("errors") or []:
        print(f"[error] {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
