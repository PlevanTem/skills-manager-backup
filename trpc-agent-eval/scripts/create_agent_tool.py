# -*- coding: utf-8 -*-
"""登记自定义 Agent 工具脚本（供内置 llm Agent 的 config.tools 引用）。

脚本契约：def {name}(query: str) -> str（docstring 作为工具描述，函数名=登记名），
或模块级 TOOLS=[...] 列表。进程内执行（无沙箱）、≤64KB。
登记后在 llm Agent config 的 tools 列表里写该名（内置 read/bash/grep/glob 可直接用）。

用法:
  python3 scripts/create_agent_tool.py --print-template
  python3 scripts/create_agent_tool.py --name my_search --script-file ./my_search.py
  python3 scripts/create_agent_tool.py --name from_disk --script-path /abs/tool.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记自定义 Agent 工具")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", help="登记名 ^[a-z][a-z0-9_]{0,63}$")
    parser.add_argument("--script-file", help="本地 .py，内容上传")
    parser.add_argument("--script-path", help="服务端绝对路径 .py")
    parser.add_argument("--print-template", action="store_true", help="打印脚本骨架后退出")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.print_template:
        tpl = c.get(base, "/api/agent-tools/template")
        print(tpl.get("template") or tpl.get("content") if isinstance(tpl, dict) else tpl)
        return

    body = {"source_kind": "upload"}
    if args.name:
        body["name"] = args.name
    if args.script_file:
        body["content"] = Path(args.script_file).read_text(encoding="utf-8")
    elif args.script_path:
        body["source_kind"] = "path"
        body["script_path"] = args.script_path
    else:
        c.die("需提供 --script-file 或 --script-path（或用 --print-template 查看骨架）")

    resp = c.post(base, "/api/agent-tools", body)
    name = resp.get("name") if isinstance(resp, dict) else args.name
    print(f"[ok] 已登记自定义工具 name={name}")
    print(f"在 llm Agent config.tools 里加 \"{name}\"（内置 read/bash/grep/glob 可直接用）。")


if __name__ == "__main__":
    c.run_entrypoint(main)
