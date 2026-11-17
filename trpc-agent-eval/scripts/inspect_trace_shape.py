# -*- coding: utf-8 -*-
"""Inspect arbitrary trace JSON/JSONL files and suggest semantic field paths."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from _trace_mapping import flatten_paths, load_jsonish, select_records, summarize_sample, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="只读分析 trace 字段形状并推荐 mapping 线索")
    parser.add_argument("--input", required=True, help="JSON/JSONL 文件或目录")
    parser.add_argument("--record-selector", action="append", help="可重复指定记录路径，如 '$.traces[*]'")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json-out", help="输出 JSON 报告")
    args = parser.parse_args()

    raw = load_jsonish(Path(args.input))
    records = select_records(raw, args.record_selector)[: args.limit]
    report = inspect_records(records)
    report["input"] = str(Path(args.input))
    if args.json_out:
        write_json(Path(args.json_out), report)
    print_summary(report)


def inspect_records(records: list[Any]) -> dict[str, Any]:
    field_index: dict[str, dict[str, Any]] = {}
    for record in records:
        for row in flatten_paths(record):
            item = field_index.setdefault(row["path"], {"path": row["path"], "type": row["type"], "samples": []})
            if len(item["samples"]) < 3:
                item["samples"].append(row["sample"])
    fields = list(field_index.values())
    candidates = infer_candidates(fields)
    strategy = recommend_strategy(fields, candidates)
    return {
        "summary": {"records_sampled": len(records), "field_paths": len(fields)},
        "fields": fields,
        "candidates": candidates,
        "recommended_strategy": strategy,
    }


def infer_candidates(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for field in fields:
        path = field["path"]
        lower = path.lower()
        samples = [summarize_sample(v) for v in field.get("samples", [])]
        sample_text = " ".join(summarize_sample(v).lower() for v in field.get("samples", []))
        for semantic, score in semantic_scores(lower, sample_text):
            key = (semantic, path)
            best[key] = {"semantic": semantic, "path": path, "confidence": score, "samples": samples}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in best.values():
        grouped[item["semantic"]].append(item)
    out = []
    for semantic, items in grouped.items():
        out.extend(sorted(items, key=lambda item: item["confidence"], reverse=True)[:5])
    return sorted(out, key=lambda item: (item["semantic"], -item["confidence"], item["path"]))


def semantic_scores(path: str, sample_text: str = "") -> list[tuple[str, float]]:
    scores: list[tuple[str, float]] = []
    if any(token in path for token in ["trace_id", ".id"]) and "tool" not in path and "span_id" not in path:
        scores.append(("trace_id", 0.6))
    if "session_id" in path or "session.id" in path or "conversation.id" in path:
        scores.append(("session_id", 0.95))
    if "user_id" in path or "user.id" in path:
        scores.append(("user_id", 0.95))
    if "timestamp" in path or ".time" in path or "start_time" in path:
        scores.append(("timestamp", 0.75))
    if any(token in path for token in ["messages", "events", "turns"]) and any(token in path for token in ["role", "actor", "speaker", "author", "content", "payload", "text"]):
        scores.append(("turn_selector", 0.85))
    if any(token in path for token in ["messages", "events", "turns"]) and any(token in path for token in ["content", "payload", "text"]):
        scores.append(("user_input", 0.65))
        scores.append(("final_response", 0.65))
    if any(token in path for token in ["role", "actor", "speaker", "author"]) and any(token in sample_text for token in ["user", "human", "client", "customer"]):
        scores.append(("user_input", 0.55))
    if any(token in path for token in ["role", "actor", "speaker", "author"]) and any(token in sample_text for token in ["assistant", "model", "ai", "agent", "bot"]):
        scores.append(("final_response", 0.55))
    if ("role" in path and "user" in path) or "prompt" in path or "input.value" in path or "user_input" in path or path.endswith(".input"):
        scores.append(("user_input", 0.8))
    if "response" in path or "answer" in path or "output.value" in path or "final" in path:
        scores.append(("final_response", 0.8))
    if "tool_calls" in path or "tool_call.name" in path or "gen_ai.tool.call.name" in path:
        scores.append(("tool_calls", 0.9))
    if "tool_responses" in path or "tool_call.result" in path or "gen_ai.tool.call.result" in path or "tool.result" in path:
        scores.append(("tool_responses", 0.9))
    if "expected" in path or "reference" in path or "ground_truth" in path:
        scores.append(("expected", 0.75))
    return scores


def recommend_strategy(fields: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    paths = [field["path"].lower() for field in fields]
    candidate_semantics = {item["semantic"] for item in candidates}
    has_messages = any(any(token in path for token in ["messages", "turns", "events"]) for path in paths)
    has_role = any(any(token in path for token in ["role", "actor", "speaker", "author"]) for path in paths)
    has_spans = any(any(token in path for token in ["span", "openinference", "gen_ai"]) for path in paths)
    has_flat_io = {"user_input", "final_response"}.issubset(candidate_semantics)
    has_tools = any("tool" in path for path in paths)
    if has_spans:
        return {
            "kind": "spans",
            "template": "templates/trace-mapping/openinference.json" if any("openinference" in path or "gen_ai" in path for path in paths) else "templates/trace-mapping/generic.spans.json",
            "confidence": 0.85,
            "next_steps": [
                "确认 record_selector 是否指向一条 trace/request",
                "确认 AGENT/TOOL span 的 kind 字段和 input/output 字段",
                "转换后检查 tool_call.id 与 tool_result 是否对齐",
            ],
        }
    if has_messages and has_role:
        return {
            "kind": "messages",
            "template": "templates/trace-mapping/generic.messages.json",
            "confidence": 0.8,
            "next_steps": [
                "把 role/actor/speaker 映射到 user_roles、assistant_roles、tool_roles",
                "把 content/payload/text 映射到 messages.content",
                "如果工具调用和工具返回是独立事件，补 tool_call_when 和 tool_response_* 字段",
            ],
        }
    if has_flat_io:
        return {
            "kind": "flat",
            "template": "templates/trace-mapping/flat-jsonl.json",
            "confidence": 0.7,
            "next_steps": [
                "确认一行或一个对象就是一个请求",
                "映射 user_input/final_response/expected_final_response",
                "有工具字段时补 tool_calls/tool_responses 路径",
            ],
        }
    return {
        "kind": "normalizer",
        "template": None,
        "confidence": 0.45 if has_tools else 0.35,
        "next_steps": [
            "先写一次性 normalizer.py，把原始格式规整成 messages、spans 或 flat",
            "normalizer 必须保留 raw trace_id/session_id/user_id/user/final/tool/expected/metadata 字段",
            "再用 convert_trace_to_evalset.py 转换，并用 audit 检查未映射字段",
        ],
    }


def print_summary(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(f"[ok] sampled={summary['records_sampled']} field_paths={summary['field_paths']}")
    strategy = report.get("recommended_strategy") or {}
    if strategy:
        print(f"[ok] recommended kind={strategy.get('kind')} template={strategy.get('template')} confidence={strategy.get('confidence')}")
        for step in strategy.get("next_steps") or []:
            print(f"  next: {step}")
    for item in report["candidates"][:30]:
        sample = item["samples"][0] if item.get("samples") else ""
        print(f"- {item['semantic']}: {item['path']} confidence={item['confidence']} sample={sample}")


if __name__ == "__main__":
    main()
