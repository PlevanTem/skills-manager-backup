# -*- coding: utf-8 -*-
"""登记模型配置 Profile（api_key 由用户本人交互输入）。

llm Agent 用 model_profile_id 引用；LLM 裁判类指标用 ${MODEL:<name>} 引用。
api_key 通过 getpass 输入，只回显掩码。

用法:
  python3 scripts/set_model.py --name glm_flash --model-name glm-4-flash \
    --base-url-model https://open.bigmodel.cn/api/paas/v4
"""
from __future__ import annotations

import argparse
import getpass

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="登记模型 Profile（api_key 由用户本人录入）")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", help="Profile 名（省略则由 model-name 派生）；名须 ^[a-z][a-z0-9_]{0,63}$")
    parser.add_argument("--model-name", required=True, help="实际模型 id，如 glm-4-flash")
    parser.add_argument("--base-url-model", required=True, dest="model_base_url", help="模型 API base_url（OpenAI 兼容端点）")
    parser.add_argument("--no-key", action="store_true", help="不设置 api_key（如本地无鉴权端点）")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    body = {"model_name": args.model_name, "base_url": args.model_base_url}
    if args.name:
        body["name"] = args.name
    if not args.no_key:
        api_key = getpass.getpass(f"请输入模型 [{args.model_name}] 的 API Key（输入不回显，留空则跳过）: ")
        if api_key:
            body["api_key"] = api_key

    resp = c.post(base, "/api/models", body)
    name = resp.get("name") if isinstance(resp, dict) else args.name
    masked = resp.get("api_key_masked", "") if isinstance(resp, dict) else ""
    print(f"[ok] 已登记模型 Profile: {name}  key={masked or '(无)'}")
    print(f"llm Agent 用 model_profile_id={name!r}；裁判指标用 ${{MODEL:{name}}}。")


if __name__ == "__main__":
    c.run_entrypoint(main)
