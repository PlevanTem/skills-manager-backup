# -*- coding: utf-8 -*-
"""登记命名密钥（由用户本人交互输入，Agent 不接触明文）。

值通过 getpass 在终端隐藏输入（不回显），直接 PUT 到本地后端，仅回显掩码。
配置里用 ${SECRET:<名>} 引用，例如 HTTP Agent 的请求头
  "Authorization": "Bearer ${SECRET:MY_TOKEN}"

用法:
  python3 scripts/set_secret.py --name MY_TOKEN
"""
from __future__ import annotations

import argparse
import getpass

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记命名密钥（值由用户本人录入）")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", required=True, help="密钥名，在配置中以 ${SECRET:名} 引用")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    value = getpass.getpass(f"请输入密钥 [{args.name}] 的值（输入不回显）: ")
    if not value:
        c.die("值为空，已取消")
    resp = c.request("PUT", base, f"/api/secrets/{args.name}", body={"value": value})
    masked = resp.get("masked") if isinstance(resp, dict) else c.mask(value)
    print(f"[ok] 已登记密钥 {args.name} -> {masked}")
    print(f"在配置中用 ${{SECRET:{args.name}}} 引用。")


if __name__ == "__main__":
    c.run_entrypoint(main)
