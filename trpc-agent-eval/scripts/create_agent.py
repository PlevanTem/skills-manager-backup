# -*- coding: utf-8 -*-
"""创建 Agent（http / cli / llm / trace / managed / sdk）。

config 来自模板或内联 JSON。默认创建后会自动探活一次确认连通（trace 除外，--no-probe 可关）。
鉴权信息不应写入 config，应使用 ${SECRET:名} 占位符（先 set_secret.py 登记）。

用法:
  python3 scripts/create_agent.py --name my-http --mode http --template http
  python3 scripts/create_agent.py --name claude --mode cli --template cli.claudecode
  python3 scripts/create_agent.py --name my --mode llm --config @llm.json
  python3 scripts/create_agent.py --name hosted --mode managed --config @managed.json
  python3 scripts/create_agent.py --name sdk-agent --mode sdk --template sdk
  python3 scripts/create_agent.py --name replay --mode trace          # trace 无需 config
"""
from __future__ import annotations

import argparse

import _client as c


def main() -> None:
    parser = argparse.ArgumentParser(description="创建 Agent")
    c.add_base_url_arg(parser)
    parser.add_argument("--name", required=True)
    parser.add_argument("--mode", required=True, choices=["http", "cli", "llm", "trace", "managed", "sdk"])
    parser.add_argument("--template", help="templates/agent/<名>.json（取其 config）")
    parser.add_argument("--config", help="config JSON 字符串或 @文件；可直接传 config 本体或 {mode,config} 外壳")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--no-probe", action="store_true", help="建后不自动探活（默认会探一次确认连通，trace 除外）")
    args = parser.parse_args()
    base = c.resolve_base_url(args.base_url)

    config = {}
    if args.template:
        raw = c.load_template("agent", args.template)
        c.assert_mode_matches(raw, args.mode)
        config = c.normalize_agent_config(raw)
    elif args.config:
        raw = c.read_json_arg(args.config)
        c.assert_mode_matches(raw, args.mode)
        config = c.normalize_agent_config(raw)
    elif args.mode != "trace":
        c.die(f"mode={args.mode} 需要 --template 或 --config")

    if args.mode == "http":
        _validate_http_config(base, config)
    elif args.mode == "sdk":
        _validate_sdk_config(base, config)

    _warn_if_name_exists(base, args.name)

    body = {"name": args.name, "mode": args.mode, "config": config, "tags": args.tags}
    resp = c.post(base, "/api/agents", body)
    agent_id = resp.get("id") if isinstance(resp, dict) else None
    print(f"[ok] 已创建 Agent id={agent_id} name={args.name} mode={args.mode}")

    if args.mode == "trace":
        return
    if args.no_probe:
        print(f"建议探针验证: python3 scripts/probe_agent.py --agent-id {agent_id}")
        return
    _auto_probe(base, agent_id, args.mode, config, args.name)


def _warn_if_name_exists(base, name):
    """同名 Agent 已存在则提示（不强阻，避免无声建出重复对象）。"""
    try:
        agents = c.get(base, "/api/agents")
    except c.ApiError:
        return
    dups = [a.get("id") for a in agents if isinstance(a, dict) and a.get("name") == name]
    if dups:
        print(f"[提示] 已存在同名 Agent name={name}（id={', '.join(str(d) for d in dups)}）；继续会新建一个。")


def _auto_probe(base, agent_id, mode, config, name):
    """建后自动探活一次，对齐「probe 通过」的 Done 标准。"""
    body = {"mode": mode, "config": config, "agent_id": agent_id, "name": name}
    try:
        result = c.post(base, "/api/agent-probe", body)
    except c.ApiError as exc:
        print(f"[probe] 自动探活失败: {exc}（可稍后手动 probe_agent.py --agent-id {agent_id}）")
        return
    ok = result.get("ok") if isinstance(result, dict) else None
    print(f"[probe] ok={ok}")
    if isinstance(result, dict):
        if result.get("response") is not None:
            print(f"[response] {result.get('response')}")
        if result.get("error"):
            print(f"[error] {result.get('error')}")
    if ok is False:
        print(f"[警告] 探活未通过，请检查 config 后重试：probe_agent.py --agent-id {agent_id}")


def _validate_http_config(base, config):
    """http config 客户端前置校验，避免后端因 ValueError 返回笼统 500。"""
    import json
    import re
    if not config.get("url"):
        c.die("http config 缺少 url")
    body_template = config.get("body_template")
    if body_template is None:
        c.die("http config 缺少 body_template")
    blob = json.dumps(body_template, ensure_ascii=False)
    if "${QUERY}" not in blob:
        c.die("body_template 必须包含 ${QUERY}（用户输入注入点）")
    refs = set(re.findall(r"\$\{SECRET:([^}]+)\}", blob + json.dumps(config.get("headers") or {}, ensure_ascii=False)))
    if refs:
        try:
            existing = c.get(base, "/api/secrets")
            names = set(existing.keys()) if isinstance(existing, dict) else set()
        except c.ApiError:
            names = set()
        missing = sorted(n.strip() for n in refs if n.strip() not in names)
        if missing:
            c.die(f"config 引用了未登记的密钥 {missing}；请先运行 set_secret.py 由用户填写")


def _validate_sdk_config(base, config):
    """SDK Agent 客户端前置校验，让迁移错误尽早暴露。"""
    import os
    if config.get("output_protocol"):
        c.die("sdk config 不需要 output_protocol；SDK 接入会直接保留 Runner 事件与工具轨迹")
    cwd = str(config.get("cwd") or "").strip()
    if not cwd:
        c.die("sdk config 缺少 cwd（Agent 项目目录）")
    if not os.path.isabs(cwd):
        c.die("sdk config 的 cwd 必须是服务端机器上的绝对路径")
    if not os.path.isdir(cwd):
        c.die(f"sdk config 的 cwd 不存在或不是目录: {cwd}")
    module = str(config.get("module") or "").strip()
    if not module:
        c.die("sdk config 缺少 module（Agent 所在模块，如 agent 或 agent.agent）")
    agent_var = str(config.get("agent_var") or "").strip()
    if agent_var and not agent_var.isidentifier():
        c.die("sdk config 的 agent_var 必须是有效 Python 标识符；留空则默认 root_agent")
    env_vars = config.get("env_vars") or []
    if not isinstance(env_vars, list):
        c.die("sdk config 的 env_vars 必须是字符串数组，填已登记的工作区环境变量名")
    names = [str(name).strip() for name in env_vars if str(name).strip()]
    if names:
        try:
            existing = c.get(base, "/api/env-vars")
            have = set(existing.keys()) if isinstance(existing, dict) else set()
        except c.ApiError:
            have = set()
        missing = sorted(name for name in names if name not in have)
        if missing:
            c.die(f"config 引用了未登记的工作区环境变量 {missing}；请先运行 set_env_var.py 由用户填写")


if __name__ == "__main__":
    c.run_entrypoint(main)
