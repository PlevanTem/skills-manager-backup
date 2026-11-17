# -*- coding: utf-8 -*-
"""Shared helpers for arbitrary trace -> EvalSet conversion scripts."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


Json = dict[str, Any] | list[Any] | str | int | float | bool | None


def load_jsonish(path: Path) -> Any:
    if path.is_dir():
        items: list[Any] = []
        for child in sorted(path.rglob("*")):
            if child.suffix.lower() not in {".json", ".jsonl"}:
                continue
            loaded = load_jsonish(child)
            if isinstance(loaded, list):
                for item in loaded:
                    if isinstance(item, dict):
                        item.setdefault("_source_file", str(child))
                    items.append(item)
            else:
                if isinstance(loaded, dict):
                    loaded.setdefault("_source_file", str(child))
                items.append(loaded)
        return items
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                item.setdefault("_source_line", line_no)
            rows.append(item)
        return rows
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def path_segments(path: str) -> list[str]:
    path = path.strip()
    if path == "$":
        return []
    if path.startswith("$."):
        path = path[2:]
    elif path.startswith("$"):
        path = path[1:].lstrip(".")
    path = path.replace("[*]", ".*")
    return [part for part in path.split(".") if part]


def values_at(node: Any, path: str) -> list[Any]:
    return _resolve(node, path_segments(path))


def first_value(node: Any, paths: list[str] | str | None, default: Any = None) -> Any:
    if not paths:
        return default
    if isinstance(paths, str):
        paths = [paths]
    for path in paths:
        values = [v for v in values_at(node, path) if v is not None]
        if values:
            return values[0]
    return default


def first_text(node: Any, paths: list[str] | str | None) -> str | None:
    value = first_value(node, paths)
    if value is None:
        return None
    return content_to_text(value)


def _resolve(node: Any, segments: list[str]) -> list[Any]:
    if not segments:
        return [node]
    seg = segments[0]
    rest = segments[1:]
    out: list[Any] = []
    if isinstance(node, list):
        if seg in {"*", "[]"}:
            for item in node:
                out.extend(_resolve(item, rest))
            return out
        if seg.isdigit():
            idx = int(seg)
            if 0 <= idx < len(node):
                return _resolve(node[idx], rest)
        for item in node:
            out.extend(_resolve(item, segments))
        return out
    if isinstance(node, dict):
        if seg == "*":
            for value in node.values():
                out.extend(_resolve(value, rest))
            return out
        if seg in node:
            out.extend(_resolve(node[seg], rest))
        # Many trace formats store semantic keys with dots, e.g. "tool_call.id".
        for i in range(len(segments), 0, -1):
            joined = ".".join(segments[:i])
            if joined in node:
                out.extend(_resolve(node[joined], segments[i:]))
                break
        return out
    return []


def select_records(root: Any, paths: list[str] | None) -> list[Any]:
    if not paths:
        return root if isinstance(root, list) else [root]
    records: list[Any] = []
    for path in paths:
        if path in {"$[*]", "$.*"} and not isinstance(root, list):
            continue
        records.extend(values_at(root, path))
    if not records and isinstance(root, list):
        return root
    if not records and isinstance(root, dict):
        return [root]
    return records


def content_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(content_to_text(item["content"]))
            else:
                parts.append(str(item))
        if parts:
            return "\n".join(parts)
    return json.dumps(value, ensure_ascii=False)


def parse_args_value(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {"value": parsed}
        except json.JSONDecodeError:
            return {"value": value}
    return {"value": value}


def make_content(text: Any, role: str) -> dict[str, Any]:
    return {"parts": [{"text": content_to_text(text)}], "role": role}


def make_invocation(
    *,
    invocation_id: str,
    user_input: Any,
    final_response: Any = None,
    tool_uses: list[dict[str, Any]] | None = None,
    tool_responses: list[dict[str, Any]] | None = None,
    intermediate_responses: list[Any] | None = None,
) -> dict[str, Any]:
    invocation: dict[str, Any] = {
        "invocation_id": invocation_id,
        "user_content": make_content(user_input, "user"),
        "creation_timestamp": time.time(),
    }
    if final_response is not None:
        invocation["final_response"] = make_content(final_response, "model")
    intermediate: dict[str, Any] = {}
    if tool_uses:
        intermediate["tool_uses"] = tool_uses
    if tool_responses:
        intermediate["tool_responses"] = tool_responses
    if intermediate_responses:
        intermediate["intermediate_responses"] = intermediate_responses
    if intermediate:
        invocation["intermediate_data"] = intermediate
    return invocation


def flatten_paths(node: Any, prefix: str = "$", limit: int = 2000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if len(rows) >= limit:
            return
        if isinstance(value, dict):
            if not value:
                rows.append({"path": path, "type": "object", "sample": {}})
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            if not value:
                rows.append({"path": path, "type": "array", "sample": []})
            else:
                walk(value[0], f"{path}[*]")
        else:
            rows.append({"path": path, "type": type(value).__name__, "sample": value})

    walk(node, prefix)
    return rows


def mapping_paths(mapping: Any) -> list[str]:
    paths: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            if value.startswith("$"):
                paths.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for key, child in value.items():
                walk(key)
                walk(child)

    walk(mapping)
    return list(dict.fromkeys(paths))


def summarize_sample(value: Any, max_len: int = 120) -> str:
    text = content_to_text(value)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def stable_id(value: Any, fallback: str) -> str:
    text = str(value or fallback)
    keep = [ch if ch.isalnum() or ch == "_" else "_" for ch in text]
    normalized = "".join(keep).strip("_")
    return normalized or fallback
