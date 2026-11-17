# -*- coding: utf-8 -*-
"""Convert arbitrary JSON/JSONL trace exports to full .evalset.json files."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from _trace_mapping import (
    first_text,
    first_value,
    load_jsonish,
    make_content,
    make_invocation,
    parse_args_value,
    select_records,
    stable_id,
    values_at,
    write_json,
    flatten_paths,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="任意 trace 转完整 .evalset.json")
    parser.add_argument("--input", required=True, help="JSON/JSONL 文件或目录")
    parser.add_argument("--mapping", required=True, help="trace mapping JSON")
    parser.add_argument("--output", required=True, help="输出 .evalset.json")
    parser.add_argument("--audit-out", required=True, help="输出 conversion_audit.json")
    parser.add_argument("--eval-set-id", default=f"trace_import_{int(time.time())}")
    parser.add_argument("--name", default="任意 Trace 转换数据集")
    parser.add_argument("--description", default="由 trpc-agent-eval skill 从任意 trace 转换生成")
    args = parser.parse_args()

    raw = load_jsonish(Path(args.input))
    mapping = load_jsonish(Path(args.mapping))
    if not isinstance(mapping, dict):
        raise SystemExit("mapping 必须是 JSON object")

    cases, audit_cases = convert(raw, mapping)
    evalset = {
        "eval_set_id": stable_id(args.eval_set_id, "trace_import"),
        "name": args.name,
        "description": args.description,
        "eval_cases": cases,
        "creation_timestamp": time.time(),
    }
    audit = {
        "input": str(Path(args.input)),
        "mapping": str(Path(args.mapping)),
        "summary": summarize_audit(audit_cases, raw, mapping),
        "cases": audit_cases,
    }
    write_json(Path(args.output), evalset)
    write_json(Path(args.audit_out), audit)
    print(f"[ok] converted cases={len(cases)} output={args.output}")
    print(f"[ok] audit={args.audit_out}")


def convert(raw: Any, mapping: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kind = mapping.get("kind", "flat")
    records = select_records(raw, mapping.get("record_selector") or mapping.get("record_selectors"))
    cases = []
    audits = []
    for index, record in enumerate(records, start=1):
        if kind == "messages":
            case, audit = convert_messages(record, mapping, index)
        elif kind == "spans":
            case, audit = convert_spans(record, mapping, index)
        else:
            case, audit = convert_flat(record, mapping, index)
        cases.append(case)
        audits.append(audit)
    return cases, audits


def convert_messages(record: Any, mapping: dict[str, Any], index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    msg_cfg = mapping.get("messages", {})
    messages = first_value(record, msg_cfg.get("path") or "$.messages", [])
    if not isinstance(messages, list):
        messages = []
    trace_id = first_text(record, mapping.get("trace_id")) or f"trace_{index}"
    session_id = first_text(record, mapping.get("session_id"))
    user_id = first_text(record, mapping.get("user_id"))
    expected_text = first_text(record, mapping.get("expected_final_response"))
    invocations = []
    current: dict[str, Any] | None = None
    tool_responses_by_id: dict[str, dict[str, Any]] = {}
    orphan_responses: list[dict[str, Any]] = []

    for message in messages:
        role = str(first_value(message, msg_cfg.get("role"), "")).lower()
        content = first_value(message, msg_cfg.get("content"))
        user_roles = {str(item).lower() for item in msg_cfg.get("user_roles", ["user", "human"])}
        assistant_roles = {str(item).lower() for item in msg_cfg.get("assistant_roles", ["assistant", "ai", "model"])}
        tool_roles = {str(item).lower() for item in msg_cfg.get("tool_roles", ["tool", "function"])}
        is_tool_call = _matches_when(message, msg_cfg.get("tool_call_when"))
        if role in user_roles:
            if current:
                invocations.append(current)
            current = {
                "id": first_text(message, msg_cfg.get("id")) or f"{trace_id}_turn_{len(invocations) + 1}",
                "user_input": content,
                "final_response": None,
                "tool_uses": [],
                "tool_responses": [],
            }
        elif role in assistant_roles:
            if current is None:
                current = {
                    "id": first_text(message, msg_cfg.get("id")) or f"{trace_id}_turn_{len(invocations) + 1}",
                    "user_input": "",
                    "final_response": None,
                    "tool_uses": [],
                    "tool_responses": [],
                }
            if is_tool_call:
                current["tool_uses"].append(_message_tool_call_from_message(message, msg_cfg, len(current["tool_uses"])))
            else:
                for tool_call in _message_tool_calls(message, msg_cfg):
                    current["tool_uses"].append(tool_call)
            if content not in (None, "", []):
                current["final_response"] = content
        elif role in tool_roles:
            response = _message_tool_response(message, msg_cfg)
            if response:
                tool_responses_by_id[response["id"]] = response
                if current:
                    current["tool_responses"].append(response)
                else:
                    orphan_responses.append(response)

    if current:
        invocations.append(current)
    actual = [
        make_invocation(
            invocation_id=str(turn["id"]),
            user_input=turn["user_input"],
            final_response=turn.get("final_response"),
            tool_uses=turn.get("tool_uses"),
            tool_responses=turn.get("tool_responses"),
        )
        for turn in invocations
    ]
    return build_case(
        trace_id=trace_id,
        actual=actual,
        expected_text=expected_text,
        session_id=session_id,
        user_id=user_id,
        record=record,
        index=index,
        orphan_responses=orphan_responses,
    )


def convert_spans(record: Any, mapping: dict[str, Any], index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    span_cfg = mapping.get("spans", {})
    spans = first_value(record, span_cfg.get("path") or "$.spans", [])
    if not isinstance(spans, list):
        spans = []
    trace_id = first_text(record, mapping.get("trace_id")) or first_text(spans[0], mapping.get("trace_id")) if spans else None
    trace_id = trace_id or f"trace_{index}"
    session_id = first_text(record, mapping.get("session_id")) or _first_from_spans(spans, mapping.get("session_id"))
    user_id = first_text(record, mapping.get("user_id")) or _first_from_spans(spans, mapping.get("user_id"))
    agent_span = _first_span_by_kind(spans, span_cfg.get("agent_kinds", ["AGENT", "CHAIN"]))
    base = agent_span or (spans[0] if spans else record)
    user_input = first_value(base, mapping.get("user_input")) or first_value(record, mapping.get("user_input")) or ""
    final_response = first_value(base, mapping.get("final_response")) or first_value(record, mapping.get("final_response"))
    expected_text = first_text(record, mapping.get("expected_final_response"))
    tool_uses = []
    tool_responses = []
    for span in spans:
        if not _span_kind_in(span, span_cfg.get("tool_kinds", ["TOOL"])):
            continue
        call_id = first_text(span, mapping.get("tool_call_id")) or first_text(span, "$.span_id") or f"tool_{len(tool_uses)}"
        name = first_text(span, mapping.get("tool_name")) or "tool"
        args = parse_args_value(first_value(span, mapping.get("tool_arguments")))
        result = first_value(span, mapping.get("tool_result"))
        tool_uses.append({"id": call_id, "name": name, "args": args})
        if result is not None:
            tool_responses.append({"id": call_id, "name": name, "response": result if isinstance(result, dict) else {"result": result}})
    actual = [
        make_invocation(
            invocation_id=first_text(base, "$.span_id") or f"{trace_id}_turn_1",
            user_input=user_input,
            final_response=final_response,
            tool_uses=tool_uses,
            tool_responses=tool_responses,
        )
    ]
    return build_case(
        trace_id=trace_id,
        actual=actual,
        expected_text=expected_text,
        session_id=session_id,
        user_id=user_id,
        record=record,
        index=index,
        orphan_responses=[],
    )


def convert_flat(record: Any, mapping: dict[str, Any], index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    trace_id = first_text(record, mapping.get("trace_id")) or f"trace_{index}"
    user_input = first_value(record, mapping.get("user_input")) or ""
    final_response = first_value(record, mapping.get("final_response"))
    expected_text = first_text(record, mapping.get("expected_final_response"))
    tool_uses = [_normalize_tool_call(item, len_idx) for len_idx, item in enumerate(values_at(record, mapping.get("tool_calls", "$.tool_calls[*]")))]
    tool_responses = [_normalize_tool_response(item, len_idx) for len_idx, item in enumerate(values_at(record, mapping.get("tool_responses", "$.tool_responses[*]")))]
    actual = [
        make_invocation(
            invocation_id=f"{trace_id}_turn_1",
            user_input=user_input,
            final_response=final_response,
            tool_uses=tool_uses,
            tool_responses=tool_responses,
        )
    ]
    return build_case(
        trace_id=trace_id,
        actual=actual,
        expected_text=expected_text,
        session_id=first_text(record, mapping.get("session_id")),
        user_id=first_text(record, mapping.get("user_id")),
        record=record,
        index=index,
        orphan_responses=[],
    )


def build_case(
    *,
    trace_id: str,
    actual: list[dict[str, Any]],
    expected_text: str | None,
    session_id: str | None,
    user_id: str | None,
    record: Any,
    index: int,
    orphan_responses: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    case: dict[str, Any] = {
        "eval_id": stable_id(trace_id, f"trace_{index}"),
        "eval_mode": "trace",
        "actual_conversation": actual,
        "creation_timestamp": time.time(),
    }
    if expected_text:
        first_actual = actual[0] if actual else {"user_content": make_content("", "user")}
        case["conversation"] = [{
            "invocation_id": f"expected_{case['eval_id']}",
            "user_content": first_actual["user_content"],
            "final_response": make_content(expected_text, "model"),
        }]
    if session_id or user_id:
        case["session_input"] = {"app_name": "trace_import", "user_id": user_id or "unknown", "state": {"session_id": session_id} if session_id else {}}
    audit = audit_case(case, record, orphan_responses)
    return case, audit


def audit_case(case: dict[str, Any], record: Any, orphan_responses: list[dict[str, Any]]) -> dict[str, Any]:
    degradations = []
    all_uses = []
    all_responses = []
    for invocation in case.get("actual_conversation") or []:
        intermediate = invocation.get("intermediate_data") or {}
        all_uses.extend(intermediate.get("tool_uses") or [])
        all_responses.extend(intermediate.get("tool_responses") or [])
        if not invocation.get("user_content", {}).get("parts", [{}])[0].get("text"):
            degradations.append("missing_user_input")
        if not invocation.get("final_response"):
            degradations.append("missing_final_response")
    use_ids = {item.get("id") for item in all_uses}
    response_ids = {item.get("id") for item in all_responses}
    unmatched_tool_uses = sorted(str(item) for item in use_ids - response_ids if item)
    unmatched_tool_responses = sorted(str(item) for item in response_ids - use_ids if item)
    if all_uses and not all_responses:
        degradations.append("missing_tool_responses")
    if not case.get("conversation"):
        degradations.append("missing_expected_reference")
    if unmatched_tool_uses and all_responses:
        degradations.append("unmatched_tool_uses")
    if unmatched_tool_responses or orphan_responses:
        degradations.append("unmatched_tool_responses")
    return {
        "eval_id": case.get("eval_id"),
        "raw_type": type(record).__name__,
        "tool_uses": len(all_uses),
        "tool_responses": len(all_responses),
        "unmatched_tool_uses": unmatched_tool_uses,
        "unmatched_tool_responses": unmatched_tool_responses + [r.get("id", "") for r in orphan_responses],
        "degradations": list(dict.fromkeys(degradations)),
    }


def summarize_audit(cases: list[dict[str, Any]], raw: Any, mapping: dict[str, Any]) -> dict[str, Any]:
    raw_paths = sorted({row["path"] for row in flatten_paths(raw, limit=10000)})
    used_paths = set()
    for path in _semantic_mapping_paths(mapping):
        if values_at(raw, path):
            used_paths.add(path)
    normalized_used = {_normalize_path_pattern(path) for path in used_paths}
    unmapped = [path for path in raw_paths if not any(_path_covered_by_pattern(path, pattern) for pattern in normalized_used)]
    return {
        "cases": len(cases),
        "tool_uses": sum(item.get("tool_uses", 0) for item in cases),
        "tool_responses": sum(item.get("tool_responses", 0) for item in cases),
        "unmatched_tool_uses": sum(len(item.get("unmatched_tool_uses") or []) for item in cases),
        "unmatched_tool_responses": sum(len(item.get("unmatched_tool_responses") or []) for item in cases),
        "degraded_cases": sum(1 for item in cases if item.get("degradations")),
        "raw_paths_total": len(raw_paths),
        "mapped_paths_total": len(used_paths),
        "unmapped_paths": unmapped[:200],
    }


def _message_tool_calls(message: dict[str, Any], msg_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    calls = first_value(message, msg_cfg.get("tool_calls"), [])
    if not isinstance(calls, list):
        return []
    return [_message_tool_call_from_message(item, msg_cfg, idx) for idx, item in enumerate(calls)]


def _message_tool_call_from_message(message: dict[str, Any], msg_cfg: dict[str, Any], idx: int) -> dict[str, Any]:
    if not isinstance(message, dict):
        return _normalize_tool_call(message, idx)
    call_id = first_text(message, msg_cfg.get("tool_call_id")) or first_text(message, ["$.id", "$.tool_call_id", "$.call_id"]) or f"tool_{idx}"
    name = first_text(message, msg_cfg.get("tool_call_name")) or first_text(message, ["$.name", "$.function.name", "$.tool.name"]) or "tool"
    args = first_value(message, msg_cfg.get("tool_call_arguments")) if msg_cfg.get("tool_call_arguments") else first_value(message, ["$.args", "$.arguments", "$.function.arguments", "$.input"])
    return {"id": call_id, "name": name, "args": parse_args_value(args)}


def _message_tool_response(message: dict[str, Any], msg_cfg: dict[str, Any]) -> dict[str, Any] | None:
    call_id = first_text(message, msg_cfg.get("tool_response_id")) or first_text(message, "$.tool_call_id") or first_text(message, "$.id")
    if not call_id:
        return None
    name = first_text(message, msg_cfg.get("tool_response_name")) or first_text(message, "$.name") or "tool"
    response = first_value(message, msg_cfg.get("tool_response_content")) or first_value(message, "$.content")
    return {"id": call_id, "name": name, "response": response if isinstance(response, dict) else {"result": response}}


def _normalize_tool_call(item: Any, idx: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"id": f"tool_{idx}", "name": "tool", "args": {"value": item}}
    call_id = first_text(item, ["$.id", "$.tool_call_id", "$.call_id"]) or f"tool_{idx}"
    name = first_text(item, ["$.name", "$.function.name", "$.tool.name"]) or "tool"
    args = first_value(item, ["$.args", "$.arguments", "$.function.arguments", "$.input"])
    return {"id": call_id, "name": name, "args": parse_args_value(args)}


def _normalize_tool_response(item: Any, idx: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"id": f"tool_{idx}", "name": "tool", "response": {"result": item}}
    call_id = first_text(item, ["$.id", "$.tool_call_id", "$.call_id"]) or f"tool_{idx}"
    name = first_text(item, ["$.name", "$.tool.name"]) or "tool"
    result = first_value(item, ["$.response", "$.result", "$.content", "$.output"])
    return {"id": call_id, "name": name, "response": result if isinstance(result, dict) else {"result": result}}


def _matches_when(message: Any, when: Any) -> bool:
    if not when:
        return False
    if not isinstance(message, dict) or not isinstance(when, dict):
        return False
    for path, expected in when.items():
        actual = first_value(message, path)
        if actual != expected:
            return False
    return True


def _normalize_path_pattern(path: str) -> str:
    return path.replace("[*]", ".*")


def _path_covered_by_pattern(path: str, pattern: str) -> bool:
    raw_parts = path.replace("[*]", ".*").split(".")
    pattern_parts = pattern.split(".")
    if len(pattern_parts) > len(raw_parts):
        return False
    for raw, pat in zip(raw_parts, pattern_parts):
        if pat == "*":
            continue
        if raw != pat:
            return False
    return True


def _semantic_mapping_paths(mapping: dict[str, Any]) -> list[str]:
    ignored_keys = {"record_selector", "record_selectors", "path", "tool_calls", "tool_responses"}
    paths: list[str] = []

    def walk(value: Any, key: str | None = None) -> None:
        if key in ignored_keys:
            return
        if isinstance(value, str):
            if value.startswith("$") and value != "$":
                paths.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif isinstance(value, dict):
            for child_key, child in value.items():
                if isinstance(child_key, str) and child_key.startswith("$") and child_key != "$":
                    paths.append(child_key)
                walk(child, child_key)

    walk(mapping)
    return list(dict.fromkeys(paths))


def _span_kind_in(span: dict[str, Any], kinds: list[str]) -> bool:
    kind = first_text(span, ["$.attributes.openinference.span.kind", "$.attributes.gen_ai.span.kind", "$.kind", "$.span_kind"])
    return bool(kind and kind.upper() in {item.upper() for item in kinds})


def _first_span_by_kind(spans: list[Any], kinds: list[str]) -> dict[str, Any] | None:
    for span in spans:
        if isinstance(span, dict) and _span_kind_in(span, kinds):
            return span
    return None


def _first_from_spans(spans: list[Any], paths: list[str] | str | None) -> str | None:
    for span in spans:
        text = first_text(span, paths)
        if text:
            return text
    return None


if __name__ == "__main__":
    main()
