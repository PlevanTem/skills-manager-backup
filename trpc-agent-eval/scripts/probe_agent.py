# -*- coding: utf-8 -*-
"""探测 Agent 连通性（创建前先验证 config 可用）。

支持探测一个内联/模板 config，或探测一个已创建的 Agent。
secrets 在输出中会被掩码。

用法:
  python3 scripts/probe_agent.py --mode http --config @my_http.json
  python3 scripts/probe_agent.py --mode cli --template cli.claudecode
  python3 scripts/probe_agent.py --mode sdk --template sdk
  python3 scripts/probe_agent.py --agent-id <id>
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 连通性探针")
    c.add_base_url_arg(parser)
    parser.add_argument("--agent-id", help="探测一个已创建的 Agent")
    parser.add_argument("--mode", choices=["http", "cli", "llm", "managed", "sdk"], help="探测内联/模板 config（trace 不支持探针）")
    parser.add_argument("--config", help="config JSON 字符串或 @文件；可直接传 config 本体或 {mode,config} 外壳")
    parser.add_argument("--template", help="使用 templates/agent/<名>.json 作为 config")
    parser.add_argument("--message", help="自定义测试语（默认后端用「你好」）")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.agent_id:
        agent = c.get(base, f"/api/agents/{args.agent_id}")
        if not isinstance(agent, dict) or not agent.get("mode"):
            c.die(f"无法读取 Agent {args.agent_id} 的 mode/config")
        body = {"mode": agent["mode"], "config": agent.get("config") or {},
                "agent_id": args.agent_id, "name": agent.get("name") or "probe"}
    else:
        if not args.mode:
            c.die("需指定 --agent-id，或 --mode + (--config | --template)")
        if args.template:
            raw = c.load_template("agent", args.template)
            c.assert_mode_matches(raw, args.mode)
            config = c.normalize_agent_config(raw)
        elif args.config:
            raw = c.read_json_arg(args.config)
            c.assert_mode_matches(raw, args.mode)
            config = c.normalize_agent_config(raw)
        else:
            c.die("需提供 --config 或 --template")
        body = {"mode": args.mode, "config": config, "name": "probe"}
    if args.message:
        body["message"] = args.message

    result = c.post(base, "/api/agent-probe", body)
    ok = result.get("ok") if isinstance(result, dict) else None
    print(f"[probe] ok={ok}")
    if isinstance(result, dict):
        if result.get("response") is not None:
            print(f"[response] {result.get('response')}")
        if result.get("elapsed_ms") is not None:
            print(f"[elapsed_ms] {result.get('elapsed_ms')}")
        if result.get("error"):
            print(f"[error] {result.get('error')}")
        if result.get("request_preview"):
            print("[request_preview]（secrets 已掩码）")
            c.print_json(result["request_preview"])


if __name__ == "__main__":
    c.run_entrypoint(main)
