# -*- coding: utf-8 -*-
"""探索当前服务端实际支持的能力（确保后端在运行后的第一步）。

前提：后端**必须已在运行**（本脚本会请求 /api/health、/openapi.json）。
若后端未启动，请先用 `python3 scripts/doctor.py` 探活，必要时执行 `bash scripts/serve.sh`。

聚合打印：版本、/openapi.json 路由、指标 catalog、在线 worker(runtime)、
模型 Profile、各模式可用指标（在已知模式集上逐一探测）、三类脚本模板端点、workdir 路径。

注意：后端未在 openapi 暴露 mode/output_protocol 枚举，故模式清单按已知集探测；
若后端新增了某种 mode/protocol，这里可能不会显示——以 02-agents.md + 实际建对象报错为准。

系统持续演进，文档可能滞后；本脚本的输出才是当前服务端的真实能力。
文档与本输出不一致时，以本输出为准。

用法:
  python3 scripts/discover.py --base-url http://127.0.0.1:8080
  python3 scripts/discover.py --raw-openapi   # 额外打印完整路由表
"""
from __future__ import annotations

import argparse

import _client as c


def _safe(fn, default=None):
    try:
        return fn()
    except c.ApiError as exc:
        return {"_error": str(exc)} if default is None else default


def main() -> None:
    parser = argparse.ArgumentParser(description="探索评测系统当前支持的能力")
    c.add_base_url_arg(parser)
    parser.add_argument("--raw-openapi", action="store_true", help="打印完整路由表")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    print(f"# 服务端能力探索 @ {base}\n")

    health = _safe(lambda: c.get(base, "/api/health"))
    print(f"[health] {health}")

    ws = _safe(lambda: c.get(base, "/api/workspace"))
    if isinstance(ws, dict):
        print(f"[workdir] {ws.get('workdir')}")

    openapi = _safe(lambda: c.get(base, "/openapi.json"))
    if isinstance(openapi, dict):
        info = openapi.get("info", {})
        print(f"[openapi] title={info.get('title')} version={info.get('version')}")
        paths = sorted(openapi.get("paths", {}).keys())
        print(f"[routes] 共 {len(paths)} 条")
        if args.raw_openapi:
            for p in paths:
                methods = ",".join(sorted(m.upper() for m in openapi["paths"][p]))
                print(f"  {methods:20s} {p}")

    print("\n## 指标 catalog（可用指标）")
    catalog = _safe(lambda: c.get(base, "/api/metric-configs/catalog"), default=[])
    items = catalog.get("metrics", catalog) if isinstance(catalog, dict) else catalog
    if isinstance(items, list):
        for m in items:
            if isinstance(m, dict):
                name = m.get("metric_name") or m.get("name")
                kind = m.get("category") or m.get("kind") or ""
                print(f"  - {name}  [{kind}]")

    print("\n## 托管 Agent runtime（worker 注册的 runtime；为空=无在线 worker）")
    runtimes = _safe(lambda: c.get(base, "/api/runtimes"), default=None)
    if isinstance(runtimes, list):
        if runtimes:
            for rt in runtimes:
                if isinstance(rt, dict):
                    print(f"  - id={rt.get('id')} provider={rt.get('provider')} "
                          f"status={rt.get('status')} model={rt.get('model') or ''}")
        else:
            print("  （空：无在线 worker / 未注册 runtime；managed 模式不可用）")
    elif runtimes is None:
        print("  （/api/runtimes 不可用：旧版本不支持 managed 模式）")

    print("\n## 模型 Profile（llm Agent / LLM 裁判类指标需要；用 ${MODEL:名} 引用）")
    models = _safe(lambda: c.get(base, "/api/models"), default=None)
    items = models.get("models", models) if isinstance(models, dict) else models
    if isinstance(items, list) and items:
        for m in items:
            if isinstance(m, dict):
                print(f"  - {m.get('name')}  (model_name={m.get('model_name')})")
    else:
        print("  （空：尚无模型 Profile；如需 LLM，请由用户用 set_model.py 录入）")

    print("\n## 各模式可用指标（在已知模式集上探测；含输出协议解锁）")
    for mode in ("http", "cli", "llm", "trace", "managed", "sdk"):
        allowed = _safe(lambda mode=mode: c.get(base, "/api/metric-configs/allowed", query={"mode": mode}), default=None)
        names = _extract_names(allowed)
        print(f"  [{mode}] {names}")
    for proto in ("claudecode", "codex"):
        allowed = _safe(
            lambda proto=proto: c.get(base, "/api/metric-configs/allowed", query={"mode": "cli", "output_protocol": proto}),
            default=None,
        )
        names = _extract_names(allowed)
        print(f"  [cli + output_protocol={proto}] {names}")

    print("\n## 三类可注册脚本模板（存在即支持该脚本类型）")
    for kind, path in (
        ("behavior-checks", "/api/behavior-checks/template"),
        ("agent-tools", "/api/agent-tools/template"),
        ("response-scorers", "/api/response-scorers/template"),
    ):
        tpl = _safe(lambda path=path: c.get(base, path), default=None)
        has_tpl = isinstance(tpl, dict) and (tpl.get("template") or tpl.get("content"))
        ok = "OK" if has_tpl else "（不可用/旧版本）"
        print(f"  - {kind}: {ok}")

    print("\n提示：若某能力此处未列出，说明当前服务端版本不支持；请勿强行调用。")


def _extract_names(allowed) -> list:
    if not isinstance(allowed, (list, dict)):
        return []
    if isinstance(allowed, dict):
        allowed = allowed.get("metrics", allowed.get("allowed", []))
    out = []
    for m in allowed if isinstance(allowed, list) else []:
        if isinstance(m, str):
            out.append(m)
        elif isinstance(m, dict):
            out.append(m.get("metric_name") or m.get("name"))
    return out


if __name__ == "__main__":
    c.run_entrypoint(main)
