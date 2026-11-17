# -*- coding: utf-8 -*-
"""查询评测状态与结果。

- 默认打印状态行（status / eval_outcome / cases_passed-total / pass@k / 错误信息）。
- --watch：订阅 SSE 进度直到结束（done/error）。
- done 后可 --result-out 保存结果 JSON、--report-out 下载 HTML 报告。

用法:
  python3 scripts/get_result.py --id E
  python3 scripts/get_result.py --id E --watch
  python3 scripts/get_result.py --id E --result-out r.json --report-out r.html
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

import _client as c


def fetch_row(base, eval_id):
    return c.get(base, f"/api/evaluations/{eval_id}")


def print_status(row):
    if not isinstance(row, dict):
        print(row)
        return
    keys = ["status", "eval_outcome", "cases_passed", "cases_total",
            "pass_at_k", "pass_hat_k", "num_runs", "pass_k"]
    line = "  ".join(f"{k}={row.get(k)}" for k in keys if row.get(k) is not None)
    print(f"[status] {line}")
    if row.get("error_message"):
        print(f"[error] {row['error_message']}")
    if row.get("assertion_errors"):
        # 后端在评测内部出现断言时附带此信息；结果通常仍完整（分数/原因齐全），按提示对待即可。
        print(f"[提示] 后端附带断言信息（结果通常仍完整，可正常查看 result）：{row.get('assertion_message', '')}")


def watch_sse(base, eval_id):
    url = f"{base}/api/evaluations/{eval_id}/events"
    req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
    print(f"[watch] 订阅 {url} ...")
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[len("data:"):].strip()
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                etype = event.get("type")
                if etype == "__end__":
                    print("[watch] 结束")
                    return
                if etype == "status":
                    print(f"[event] status -> {event.get('status')}")
                elif etype == "error":
                    print(f"[event] error -> {event.get('error')}")
                elif etype in ("evaluate_case_done", "inference_case_done"):
                    print(f"[event] {etype} case={event.get('eval_case_id')} run={event.get('run_index')}")
    except urllib.error.URLError as exc:
        print(f"[watch] SSE 连接中断（{exc}）；改用状态轮询。")


def main() -> None:
    parser = argparse.ArgumentParser(description="查询评测状态与结果")
    c.add_base_url_arg(parser)
    parser.add_argument("--id", required=True, help="evaluation id")
    parser.add_argument("--watch", action="store_true", help="订阅 SSE 进度直到结束")
    parser.add_argument("--result-out", help="done 后保存结果 JSON 到该路径")
    parser.add_argument("--report-out", help="done 后保存 HTML 报告到该路径")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.watch:
        watch_sse(base, args.id)

    row = fetch_row(base, args.id)
    print_status(row)
    status = row.get("status") if isinstance(row, dict) else None
    if status != "done":
        if status == "error":
            return
        print("评测尚未完成；可加 --watch 跟踪进度。")
        return

    result = c.get(base, f"/api/evaluations/{args.id}/result")
    _print_breakdown(result)
    if args.result_out:
        with open(args.result_out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(f"[result] 已保存 {args.result_out}")
    if args.report_out:
        url = f"{base}/api/evaluations/{args.id}/report"
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                with open(args.report_out, "wb") as fh:
                    fh.write(resp.read())
            print(f"[report] 已保存 {args.report_out}")
        except urllib.error.HTTPError as exc:
            print(f"[report] 下载失败 HTTP {exc.code}")
    if not args.result_out and not args.report_out:
        print(f"结果接口: GET {base}/api/evaluations/{args.id}/result")
        print(f"报告接口: GET {base}/api/evaluations/{args.id}/report")


def _print_breakdown(result):
    """done 后打印「用例 × 指标」得分明细，无需落盘即可看到通过/失败原因。"""
    sets = result.get("results_by_eval_set_id") if isinstance(result, dict) else None
    if not isinstance(sets, dict):
        return
    print("[breakdown] 按用例/指标得分：")
    for set_id, sdata in sets.items():
        cases = (sdata or {}).get("eval_results_by_eval_id") or {}
        for case_id, runs in cases.items():
            for r in runs if isinstance(runs, list) else []:
                run_id = r.get("run_id")
                for m in r.get("overall_eval_metric_results") or []:
                    name, score, thr = m.get("metric_name"), m.get("score"), m.get("threshold")
                    passed = isinstance(score, (int, float)) and isinstance(thr, (int, float)) and score >= thr
                    flag = "PASS" if passed else "FAIL"
                    print(f"  {set_id}/{case_id} run{run_id}: {name} score={score}/thr={thr} -> {flag}")
                    if not passed and m.get("details"):
                        print(f"      details: {str(m.get('details'))[:200]}")
                if r.get("error_message"):
                    print(f"  {set_id}/{case_id} run{run_id}: [error] {r['error_message']}")


if __name__ == "__main__":
    c.run_entrypoint(main)
