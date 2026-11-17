# -*- coding: utf-8 -*-
"""列出可用指标（catalog），辅助选型。可按 mode/输出协议过滤可用集。

每条指标带「前置依赖标记」：是否需要 LLM 模型/密钥、是否需要数据集含 tool_uses、
是否需要 trace/工具记录等——在选指标当下就暴露依赖，避免建数据集/发起时才报错。

用法:
  python3 scripts/metric_catalog.py                              # 全集（建议先定 mode）
  python3 scripts/metric_catalog.py --mode cli                   # 仅列出 cli 可用指标
  python3 scripts/metric_catalog.py --mode sdk                   # 仅列出 SDK 接入可用指标
  python3 scripts/metric_catalog.py --mode cli --output-protocol claudecode
"""
from __future__ import annotations

import argparse

import _client as c

# 前置依赖：judge 类一律需模型+密钥（由 category 推导）；下表为额外静态增补。
# 未知的新指标会优雅降级为仅显示 category，不会报错。
_EXTRA_DEPS = {
    "final_response_avg_score": "规则比对（含/正则/全等）·无需 LLM/密钥",
    "final_behavior_avg_score": "需 behavior-check 脚本·无需 LLM",
    "tool_trajectory_avg_score": "需数据集含期望 tool_uses·Agent 须能记录工具调用",
    "llm_rubric_knowledge_recall": "额外需 trace 或可记录检索的实跑",
    "llm_hallucinations": "额外需 trace 或可记录工具调用+返回的实跑",
    "llm_final_behavior": "裁判 Agent 带工具核实副作用",
}


def _deps(name: str, category: str) -> str:
    parts = []
    if category == "judge":
        parts.append("需模型 Profile(${MODEL:})+密钥")
    extra = _EXTRA_DEPS.get(name)
    if extra:
        parts.append(extra)
    return " · ".join(parts)


def _print_item(m: dict) -> None:
    name = m.get("metric_name") or m.get("name")
    kind = m.get("category") or m.get("kind") or ""
    when = m.get("when_to_use") or m.get("description") or ""
    deps = _deps(name, kind)
    head = f"- {name} [{kind}]"
    if deps:
        head += f"  ⟨依赖：{deps}⟩"
    print(head)
    if when:
        print(f"    {when}")


def _names(allowed) -> set:
    if isinstance(allowed, dict):
        allowed = allowed.get("metrics", allowed.get("allowed", []))
    out = set()
    for m in allowed if isinstance(allowed, list) else []:
        if isinstance(m, str):
            out.add(m)
        elif isinstance(m, dict):
            out.add(m.get("metric_name") or m.get("name"))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="指标 catalog 与可用集")
    c.add_base_url_arg(parser)
    parser.add_argument("--mode", choices=["http", "cli", "llm", "trace", "managed", "sdk"], help="按 Agent 模式查可用指标")
    parser.add_argument("--output-protocol", choices=["claudecode", "codex"], help="配合 --mode cli 查协议解锁的指标")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    catalog = c.get(base, "/api/metric-configs/catalog")
    items = catalog.get("metrics", catalog) if isinstance(catalog, dict) else catalog
    items = [m for m in items if isinstance(m, dict)] if isinstance(items, list) else []

    if not args.mode:
        if args.json:
            c.print_json(catalog)
            return
        print("# 指标 catalog（全集）")
        print("提示：未指定 --mode，以下为全部指标。建议先定 Agent mode，再 `--mode <m>` 只看可用项。\n")
        for m in items:
            _print_item(m)
        return

    allowed = c.get(
        base,
        "/api/metric-configs/allowed",
        query={"mode": args.mode, "output_protocol": args.output_protocol},
    )
    if args.json:
        c.print_json(allowed)
        return
    allowed_names = _names(allowed)
    suffix = f" + {args.output_protocol}" if args.output_protocol else ""
    print(f"# mode={args.mode}{suffix} 可用指标（仅显示该模式允许的）\n")
    shown = 0
    for m in items:
        name = m.get("metric_name") or m.get("name")
        if name in allowed_names:
            _print_item(m)
            shown += 1
    if shown == 0:
        print("（该模式下无可用指标，或 allowed 端点返回为空）")
    # allowed 里有、但 catalog 未收录的（极少见，版本错位时提示）
    extra = sorted(allowed_names - {m.get("metric_name") or m.get("name") for m in items})
    if extra:
        print("\n（allowed 含 catalog 未描述的指标：" + ", ".join(str(e) for e in extra) + "）")


if __name__ == "__main__":
    c.run_entrypoint(main)
