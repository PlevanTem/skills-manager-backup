# -*- coding: utf-8 -*-
"""登记工作区环境变量（值由用户本人交互输入）。

评测/探测/脚本执行时注入子进程环境（合并顺序：os.environ < workspace env < agent config.env）。
适合 cli Agent 子进程需要的鉴权变量。名须 ^[A-Z][A-Z0-9_]{0,127}$。

用法:
  python3 scripts/set_env_var.py --name CODEBUDDY_API_KEY
"""
from __future__ import annotations

import argparse
import getpass

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记工作区环境变量（值由用户本人录入）")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", required=True, help="变量名，须大写字母开头 ^[A-Z][A-Z0-9_]{0,127}$")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    value = getpass.getpass(f"请输入环境变量 [{args.name}] 的值（输入不回显）: ")
    if not value:
        c.die("值为空，已取消（环境变量不允许空值）")
    resp = c.request("PUT", base, f"/api/env-vars/{args.name}", body={"value": value})
    masked = resp.get("masked") if isinstance(resp, dict) else c.mask(value)
    print(f"[ok] 已登记环境变量 {args.name} -> {masked}")
    print("评测/探测 cli Agent 时会自动注入到子进程环境。")


if __name__ == "__main__":
    c.run_entrypoint(main)
