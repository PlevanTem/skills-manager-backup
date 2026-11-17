# -*- coding: utf-8 -*-
"""创建数据集（empty / path / upload）。

- empty：创建空数据集，之后用 add_case.py 追加用例（仅适合 API 能力边界内的简单用例）。
- path：登记服务端已存在的绝对路径 .evalset.json（不复制）。
- upload：上传本地 .evalset.json（≤16MB），适合含 tool_responses/多轮/模拟用户等复杂字段。
Langfuse 导入字段较多，请直接调 POST /api/datasets/import/langfuse（见 references/03-datasets.md）。

用法:
  python3 scripts/create_dataset.py --source empty --name 冒烟集
  python3 scripts/create_dataset.py --source path --name 线上集 --source-path /abs/x.evalset.json
  python3 scripts/create_dataset.py --source upload --name 幻觉集 --file ./hallucination.evalset.json
"""
from __future__ import annotations

import argparse
from pathlib import Path

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="创建数据集")
    c.add_base_url_arg(parser)
    parser.add_argument("--source", required=True, choices=["empty", "path", "upload"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--source-path", help="source=path 时的服务端绝对路径")
    parser.add_argument("--file", help="source=upload 时的本地 .evalset.json")
    parser.add_argument("--storage-dir", help="可选：服务端存放目录（empty/upload）")
    parser.add_argument("--tags", nargs="*", default=[])
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    if args.source == "upload":
        if not args.file:
            c.die("source=upload 需要 --file")
        path = Path(args.file)
        if not path.name.endswith(".evalset.json"):
            c.die("上传文件名必须以 .evalset.json 结尾")
        content = path.read_bytes()
        # name/storage_dir 通过 multipart form 一并提交较复杂；此处用 query 不可行，
        # 故直接构造带 name 字段的 multipart：复用 upload_multipart 仅传 file，name 走 form。
        resp = _upload_with_name(base, path.name, content, args.name, args.storage_dir)
    elif args.source == "path":
        if not args.source_path:
            c.die("source=path 需要 --source-path（服务端绝对路径）")
        resp = c.post(base, "/api/datasets", {
            "name": args.name, "source_kind": "path",
            "source_path": args.source_path, "tags": args.tags,
        })
    else:
        body = {"name": args.name, "source_kind": "empty", "tags": args.tags}
        if args.storage_dir:
            body["storage_dir"] = args.storage_dir
        resp = c.post(base, "/api/datasets", body)

    ds_id = resp.get("id") if isinstance(resp, dict) else None
    print(f"[ok] 已创建数据集 id={ds_id} name={args.name}")
    if args.source == "empty":
        print(f"加用例: python3 scripts/add_case.py --dataset-id {ds_id} --template case.normal")


def _upload_with_name(base, filename, content, name, storage_dir):
    """multipart 同时带 name/storage_dir 文本字段与 file。"""
    import urllib.request
    boundary = "----trpcEvalSkillDS"
    fields = [("name", name)]
    if storage_dir:
        fields.append(("storage_dir", storage_dir))
    parts = []
    for fname, fval in fields:
        parts += [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="{fname}"'.encode(),
            b"", fval.encode(),
        ]
    parts += [
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
        b"Content-Type: application/octet-stream", b"", content,
        f"--{boundary}--".encode(), b"",
    ]
    data = b"\r\n".join(parts)
    req = urllib.request.Request(
        base + "/api/datasets/import/upload", data=data, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"},
    )
    import json
    import urllib.error
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw
        raise c.ApiError(exc.code, str(detail), base + "/api/datasets/import/upload") from None


if __name__ == "__main__":
    c.run_entrypoint(main)
