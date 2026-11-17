# -*- coding: utf-8 -*-
"""共享 HTTP 客户端与工具函数（被其它脚本 import，非入口）。

仅依赖 Python 3 标准库。统一处理 base-url 解析、JSON 编解码、错误回显
（输出后端返回的 `detail`）、敏感值掩码、模板加载。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DEFAULT_BASE_URL = "http://127.0.0.1:8080"
BASE_URL_ENV = "TRPC_AGENT_EVAL_BACKEND_URL"
ALT_BASE_URL_ENV = "TRPC_AGENT_EVAL_API_URL"

# templates/ 与 scripts/ 同级，位于 skill 根目录下
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"


class ApiError(Exception):
    """后端返回非 2xx 时抛出，携带状态码与 detail。"""

    def __init__(self, status: int, detail: str, url: str) -> None:
        self.status = status
        self.detail = detail
        self.url = url
        super().__init__(f"HTTP {status} @ {url}: {detail}")


def resolve_base_url(arg_value: Optional[str]) -> str:
    """命令行 > 环境变量 > 默认；去掉末尾 '/'。"""
    value = (
        arg_value
        or os.environ.get(BASE_URL_ENV)
        or os.environ.get(ALT_BASE_URL_ENV)
        or DEFAULT_BASE_URL
    )
    return value.rstrip("/")


def add_base_url_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"后端地址，默认取 ${BASE_URL_ENV} 或 {DEFAULT_BASE_URL}",
    )


def request(
    method: str,
    base_url: str,
    path: str,
    *,
    body: Optional[Any] = None,
    query: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0,
) -> Any:
    """发起 JSON 请求，返回已解析的响应体。非 2xx 抛 ApiError。"""
    url = base_url + path
    if query:
        clean = {k: v for k, v in query.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        detail = raw
        try:
            parsed = json.loads(raw)
            detail = parsed.get("detail", raw) if isinstance(parsed, dict) else raw
        except json.JSONDecodeError:
            pass
        raise ApiError(exc.code, str(detail), url) from None
    except urllib.error.URLError as exc:
        raise ApiError(0, f"无法连接后端（{exc.reason}）；请确认服务已启动且 --base-url 正确", url) from None


def get(base_url: str, path: str, **kw: Any) -> Any:
    return request("GET", base_url, path, **kw)


def post(base_url: str, path: str, body: Any, **kw: Any) -> Any:
    return request("POST", base_url, path, body=body, **kw)


def upload_multipart(
    base_url: str,
    path: str,
    *,
    field: str,
    filename: str,
    content: bytes,
    timeout: float = 60.0,
) -> Any:
    """上传单文件（multipart/form-data）。"""
    boundary = "----trpcEvalSkill7c1f"
    parts = [
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"'.encode(),
        b"Content-Type: application/octet-stream",
        b"",
        content,
        f"--{boundary}--".encode(),
        b"",
    ]
    data = b"\r\n".join(parts)
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    }
    req = urllib.request.Request(base_url + path, data=data, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("detail", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw
        raise ApiError(exc.code, str(detail), base_url + path) from None
    except urllib.error.URLError as exc:
        raise ApiError(0, f"无法连接后端（{exc.reason}）", base_url + path) from None


def mask(value: Optional[str]) -> str:
    """掩码敏感值：长度 <=12 全星号，否则前 3 + 星号 + 后 3。"""
    if not value:
        return ""
    if len(value) <= 12:
        return "*" * len(value)
    return value[:3] + "*" * (len(value) - 6) + value[-3:]


def load_template(category: str, name: str) -> Any:
    """读取 templates/<category>/<name> 文件（JSON 解析，.py 返回文本）。"""
    candidates = [name, f"{name}.json", f"{name}.py"]
    for cand in candidates:
        path = TEMPLATES_DIR / category / cand
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":
                return json.loads(text)
            return text
    available = sorted(p.name for p in (TEMPLATES_DIR / category).glob("*")) if (TEMPLATES_DIR / category).is_dir() else []
    raise FileNotFoundError(f"模板未找到: {category}/{name}；可选: {available}")


def read_json_arg(value: str) -> Any:
    """参数可以是内联 JSON 字符串，也可以是 @文件路径。"""
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text(encoding="utf-8"))
    return json.loads(value)


def normalize_agent_config(raw: Any) -> Dict[str, Any]:
    """统一取出 Agent 的 config 本体。

    既接受 config 本体 `{"url": ...}` / `{"command": ...}`，也接受
    `{"mode": ..., "config": {...}}` 外壳模板（templates/agent/*.json 即此形态）。
    Agent 的真实 config（http/cli/llm）不含顶层 `config` 键，故据此解包是安全的。
    """
    if isinstance(raw, dict) and isinstance(raw.get("config"), dict):
        return raw["config"]
    return raw if isinstance(raw, dict) else {}


def assert_mode_matches(raw: Any, mode: str) -> None:
    """若 --config/--template 原始 JSON 带了 `mode` 且与 --mode 不一致，立即报错。

    避免 `--mode http --template cli` 这类静默送错配置（外壳里的 mode 会被
    normalize 丢弃，--mode 才是权威），把矛盾在客户端当场拦下。
    """
    if isinstance(raw, dict):
        embedded = raw.get("mode")
        if embedded and mode and embedded != mode:
            die(f"--mode={mode} 与模板/config 内 mode={embedded} 不一致；请确认后重试")


def allowed_metric_names(allowed: Any) -> set:
    """从 /api/metric-configs/allowed 的返回里提取指标名集合（兼容 list/dict 形态）。"""
    if isinstance(allowed, dict):
        allowed = allowed.get("metrics", allowed.get("allowed", []))
    out = set()
    for m in allowed if isinstance(allowed, list) else []:
        if isinstance(m, str):
            out.add(m)
        elif isinstance(m, dict):
            out.add(m.get("metric_name") or m.get("name"))
    return out


def check_placeholder_refs(base_url: str, blob: str) -> None:
    """扫描文本里的 ${MODEL:名}/${SECRET:名}，对未登记的打印告警（不阻断）。"""
    import re
    models = {m.strip() for m in re.findall(r"\$\{MODEL:([^}]+)\}", blob)}
    secrets = {s.strip() for s in re.findall(r"\$\{SECRET:([^}]+)\}", blob)}
    if models:
        try:
            existing = get(base_url, "/api/models")
            have = {m.get("name") for m in existing if isinstance(m, dict)} if isinstance(existing, list) else set()
        except ApiError:
            have = set()
        miss = sorted(m for m in models if m not in have)
        if miss:
            print(f"[提示] 引用了未登记的模型 Profile {miss}；请先 set_model.py 由用户填写（否则发起时会失败）。")
    if secrets:
        try:
            existing = get(base_url, "/api/secrets")
            have = set(existing.keys()) if isinstance(existing, dict) else set()
        except ApiError:
            have = set()
        miss = sorted(s for s in secrets if s not in have)
        if miss:
            print(f"[提示] 引用了未登记的密钥 {miss}；请先 set_secret.py 由用户填写（否则发起时会失败）。")


def _require_object(base_url: str, kind: str, oid: str, label: str) -> Dict[str, Any]:
    try:
        obj = get(base_url, f"/api/{kind}/{oid}")
    except ApiError:
        die(f"{label}不存在或无法读取：id={oid}（请检查 id 是否正确、对象是否已创建）")
    if not isinstance(obj, dict) or not obj.get("id"):
        die(f"{label}不存在或无法读取：id={oid}")
    return obj


def preflight_bindings(base_url: str, agent_id=None, dataset_id=None, metric_config_id=None) -> Dict[str, Any]:
    """发起前预检：① 三个绑定对象是否存在；② 指标在该 Agent mode 下是否可用；③ ${MODEL:}/${SECRET:} 是否登记。

    把绝大多数原本要到发起时才暴露的错误，提前到此当场报清楚。返回解析出的对象供调用方复用。
    """
    agent = _require_object(base_url, "agents", agent_id, "Agent") if agent_id else None
    dataset = _require_object(base_url, "datasets", dataset_id, "数据集") if dataset_id else None
    metric = _require_object(base_url, "metric-configs", metric_config_id, "指标方案") if metric_config_id else None

    if agent and metric:
        mode = agent.get("mode")
        proto = (agent.get("config") or {}).get("output_protocol")
        definition = metric.get("definition") or {}
        metrics = definition.get("metrics") if isinstance(definition, dict) else definition
        names = [m.get("metric_name") or m.get("name") for m in (metrics or []) if isinstance(m, dict)]
        if mode and names and mode != "trace":
            allowed = get(base_url, "/api/metric-configs/allowed", query={"mode": mode, "output_protocol": proto})
            allowed_names = allowed_metric_names(allowed)
            bad = sorted({n for n in names if n and n not in allowed_names})
            if bad:
                tip = f"（输出协议={proto}）" if proto else ""
                die(f"指标 {bad} 在该 Agent mode={mode}{tip} 下不可用；"
                    f"换指标，或给 Agent 配 output_protocol 解锁。可用项见 metric_catalog.py --mode {mode}")
        check_placeholder_refs(base_url, json.dumps(definition, ensure_ascii=False))

    return {"agent": agent, "dataset": dataset, "metric": metric}


def print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(msg: str, code: int = 1) -> None:
    print(f"错误: {msg}", file=sys.stderr)
    sys.exit(code)


def run_entrypoint(fn) -> None:
    """统一入口包装：把 ApiError 友好回显，避免堆栈噪声。"""
    try:
        fn()
    except ApiError as exc:
        die(str(exc), code=2)
    except FileNotFoundError as exc:
        die(str(exc))
    except KeyboardInterrupt:
        die("已取消", code=130)
