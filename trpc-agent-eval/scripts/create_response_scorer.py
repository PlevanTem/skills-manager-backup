# -*- coding: utf-8 -*-
"""登记自定义响应解析脚本（供 llm_judge_template 的 response_scorer_name 使用）。

脚本契约：def {name}(response_text: str) -> tuple[float | bool, str]
（第一元 float 会 clamp 到 [0,1]，bool→1/0；第二元为原因）。子进程执行、30s、≤64KB。
内置 single_score / final_response / rubric_scores 无需登记；自定义名运行时
注册为 llm_judge_template:<name>，在指标 criterion.llm_judge.template.response_scorer_name 引用。

用法:
  python3 scripts/create_response_scorer.py --print-template --name contains_pass
  python3 scripts/create_response_scorer.py --name contains_pass --script-file ./contains_pass.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记响应解析脚本")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", help="登记名 ^[a-z][a-z0-9_]{0,63}$")
    parser.add_argument("--script-file", help="本地 .py，内容上传")
    parser.add_argument("--script-path", help="服务端绝对路径 .py")
    parser.add_argument("--print-template", action="store_true", help="打印脚本骨架后退出")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.print_template:
        tpl = c.get(base, "/api/response-scorers/template", query={"name": args.name})
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

    resp = c.post(base, "/api/response-scorers", body)
    name = resp.get("name") if isinstance(resp, dict) else args.name
    print(f"[ok] 已登记响应解析 name={name}")
    print(f"在 llm_judge_template 指标里设 template.response_scorer_name=\"{name}\"。")


if __name__ == "__main__":
    c.run_entrypoint(main)
