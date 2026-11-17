# -*- coding: utf-8 -*-
"""把已完成的评测运行导出为可复跑的 Trace 数据集。

保留真实输出 + tool_uses + tool_responses，生成 eval_mode=trace 数据集
（tag: trace/run_export）。要求 run 已 done 且 expected 含参考信息。
导出后用 trace 模式 Agent + 指标重新评测即可回归。

用法:
  python3 scripts/export_trace_dataset.py --evaluation-id E1 E2 --name-prefix "回归"
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="评测运行导出为 Trace 数据集")
    c.add_base_url_arg(parser)
    parser.add_argument("--evaluation-id", nargs="+", required=True, help="一个或多个已完成评测 id（≤100）")
    parser.add_argument("--storage-dir", help="可选：服务端存放目录")
    parser.add_argument("--name-prefix", help="可选：数据集名前缀")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    body = {"evaluation_ids": args.evaluation_id}
    if args.storage_dir:
        body["storage_dir"] = args.storage_dir
    if args.name_prefix:
        body["name_prefix"] = args.name_prefix

    resp = c.post(base, "/api/datasets/from-evaluation-runs", body)
    created = resp.get("created", []) if isinstance(resp, dict) else []
    failed = resp.get("failed", []) if isinstance(resp, dict) else []
    print(f"[ok] 导出成功 {len(created)} 个，失败 {len(failed)} 个")
    for item in created:
        ds = item.get("dataset", {}) if isinstance(item, dict) else {}
        print(f"  - dataset id={ds.get('id')} name={ds.get('name')} (trace, 可复跑)")
    for f in failed:
        print(f"  ! {f.get('evaluation_id')}: {f.get('error')}")


if __name__ == "__main__":
    c.run_entrypoint(main)
