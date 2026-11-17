# -*- coding: utf-8 -*-
"""登记行为检查脚本（确定性验证函数，供 final_behavior_avg_score 使用）。

脚本契约：模块级 def {name}(user_content: str) -> tuple[bool, str]（函数名须等于登记名）。
注意 user_content 是该轮的「用户输入文本」，不是 Agent 回复/final_behavior；检查器无法获取
Agent 输出，如需核验真实副作用须自行查询外部系统。子进程执行、30s 超时、≤64KB。登记后在数据集
expected invocation 用 final_behavior_match / final_behavior_matches 引用该函数名。

用法:
  python3 scripts/create_behavior_check.py --print-template --name check_ok   # 查看骨架
  python3 scripts/create_behavior_check.py --name check_ok --script-file ./check_ok.py --description "校验X"
  python3 scripts/create_behavior_check.py --name from_disk --script-path /abs/checker.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记行为检查脚本")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", help="登记名 ^[a-z][a-z0-9_]{0,63}$")
    parser.add_argument("--script-file", help="本地 .py，内容上传（source_kind=upload）")
    parser.add_argument("--script-path", help="服务端绝对路径 .py（source_kind=path）")
    parser.add_argument("--description", help="可选说明")
    parser.add_argument("--print-template", action="store_true", help="打印脚本骨架后退出")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.print_template:
        tpl = c.get(base, "/api/behavior-checks/template", query={"name": args.name})
        print(tpl.get("template") or tpl.get("content") if isinstance(tpl, dict) else tpl)
        return

    body = {"source_kind": "upload"}
    if args.name:
        body["name"] = args.name
    if args.description is not None:
        body["description"] = args.description
    if args.script_file:
        body["content"] = Path(args.script_file).read_text(encoding="utf-8")
    elif args.script_path:
        body["source_kind"] = "path"
        body["script_path"] = args.script_path
    else:
        c.die("需提供 --script-file 或 --script-path（或用 --print-template 查看骨架）")

    resp = c.post(base, "/api/behavior-checks", body)
    name = resp.get("name") if isinstance(resp, dict) else args.name
    print(f"[ok] 已登记行为检查 name={name}")
    print(f"在数据集 expected invocation 用 final_behavior_match=\"{name}\" 引用。")


if __name__ == "__main__":
    c.run_entrypoint(main)
