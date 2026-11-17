# -*- coding: utf-8 -*-
"""创建指标方案（empty / path / upload）。

- empty：用 --definition 提供「指标项数组」(可基于 templates/metric/ 组合)。
- path：登记服务端绝对路径 .metric.json。
- upload：上传本地 .metric.json（≤16MB）。
先用 metric_catalog.py 查看可用指标与各模式门控，再选型。

注意两种形态不同：
- empty 的 --definition / --definition-template 是「数组」[ {metric_name,threshold,criterion}, ... ]。
- upload 的 .metric.json 必须是「对象」{ "metrics": [ ...同上... ], "num_runs": 1, "metric_id": "可选" }；
  id 取自文件内 metric_id 或文件名 <id>.metric.json（不取 --name；--name 仅作显示名）。
  可直接用 templates/metric/metric_config.upload.metric.json。

用法:
  python3 scripts/create_metric.py --source empty --name 回复质量 --definition @def.json
  python3 scripts/create_metric.py --source empty --name 工具轨迹 --definition-template metric_config.example
  python3 scripts/create_metric.py --source upload --name x --file templates/metric/metric_config.upload.metric.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="创建指标方案")
    c.add_base_url_arg(parser)
    parser.add_argument("--source", required=True, choices=["empty", "path", "upload"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--definition", help="指标项数组 JSON 字符串或 @文件（source=empty）")
    parser.add_argument("--definition-template", help="templates/metric/<名>.json，单项或数组（source=empty）")
    parser.add_argument("--source-path", help="source=path 时的服务端绝对路径")
    parser.add_argument("--file", help="source=upload 时的本地 .metric.json")
    parser.add_argument("--for-mode", choices=["http", "cli", "llm", "trace", "managed", "sdk"],
                        help="建前复核所选指标在该 Agent mode 下是否可用（强烈建议）")
    parser.add_argument("--output-protocol", choices=["claudecode", "codex"],
                        help="配合 --for-mode cli 复核协议解锁指标")
    parser.add_argument("--tags", nargs="*", default=[])
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.source == "upload":
        if not args.file:
            c.die("source=upload 需要 --file")
        path = Path(args.file)
        if not path.name.endswith(".metric.json"):
            c.die("上传文件名必须以 .metric.json 结尾")
        content = path.read_bytes()
        _precheck(base, args, _metrics_from_upload(content), content.decode("utf-8", errors="replace"))
        resp = _upload_with_name(base, path.name, content, args.name)
    elif args.source == "path":
        if not args.source_path:
            c.die("source=path 需要 --source-path")
        resp = c.post(base, "/api/metric-configs", {
            "name": args.name, "source_kind": "path",
            "source_path": args.source_path, "tags": args.tags,
        })
    else:
        definition = _load_definition(args)
        _precheck(base, args, definition, json.dumps(definition, ensure_ascii=False))
        resp = c.post(base, "/api/metric-configs", {
            "name": args.name, "source_kind": "empty",
            "definition": definition, "tags": args.tags,
        })

    cfg_id = resp.get("id") if isinstance(resp, dict) else None
    print(f"[ok] 已创建指标方案 id={cfg_id} name={args.name}")


def _metrics_from_upload(content):
    """从 upload 的 .metric.json 内容里尽力解析出 metrics 数组（失败则空，不阻断）。"""
    try:
        obj = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    metrics = obj.get("metrics") if isinstance(obj, dict) else obj
    return [m for m in metrics if isinstance(m, dict)] if isinstance(metrics, list) else []


def _precheck(base, args, metrics, blob):
    """建前护栏：① 指标在目标 mode 下是否可用；② ${MODEL:}/${SECRET:} 是否已登记。"""
    names = [m.get("metric_name") or m.get("name") for m in metrics if isinstance(m, dict)]
    if args.for_mode and names:
        allowed = c.get(base, "/api/metric-configs/allowed",
                        query={"mode": args.for_mode, "output_protocol": args.output_protocol})
        allowed_names = c.allowed_metric_names(allowed)
        bad = sorted({n for n in names if n and n not in allowed_names})
        if bad:
            suffix = f" --output-protocol {args.output_protocol}" if args.output_protocol else ""
            c.die(f"指标 {bad} 在 mode={args.for_mode} 下不可用；"
                  f"用 metric_catalog.py --mode {args.for_mode}{suffix} 查可用项")
    c.check_placeholder_refs(base, blob)


def _load_definition(args):
    if args.definition:
        data = c.read_json_arg(args.definition)
    elif args.definition_template:
        data = c.load_template("metric", args.definition_template)
    else:
        c.die("source=empty 需要 --definition 或 --definition-template")
        return []
    return data if isinstance(data, list) else [data]


def _upload_with_name(base, filename, content, name):
    import urllib.error
    import urllib.request
    boundary = "----trpcEvalSkillMC"
    parts = [
        f"--{boundary}".encode(),
        b'Content-Disposition: form-data; name="name"', b"", name.encode(),
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
        b"Content-Type: application/octet-stream", b"", content,
        f"--{boundary}--".encode(), b"",
    ]
    data = b"\r\n".join(parts)
    req = urllib.request.Request(
        base + "/api/metric-configs/import/upload", data=data, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw
        raise c.ApiError(exc.code, str(detail), req.full_url) from None


if __name__ == "__main__":
    c.run_entrypoint(main)
