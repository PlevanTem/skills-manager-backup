# -*- coding: utf-8 -*-
"""定位已安装后端/SDK 的源码目录——**最后保底的排错手段，且只读**。

仅当「运行时元数据（discover/catalog/allowed/openapi）」与「实跑验证（冒烟用例）」
都无法解释某指标/字段/打分行为时，才用本脚本定位源码，再用 Grep/Read 查证。

⚠ 红线：
  - 源码**只读**，用于查证语义。**严禁修改**已安装包内任何文件（改了不会进评测、
    且会污染环境、升级即丢失）。修复永远落在 skill 的脚本/模板/数据集侧。
  - 前端 npm 包是压缩构建产物（无 sourcemap），**不可作源码依据**；前端只是套在
    /api/* 上的薄 SPA，零评测逻辑。要看前后端交互请读 openapi 或浏览器 Network。

跨环境定位策略（逐级兜底，应对「agent 用的 python ≠ 装后端的 python」）：
  1) 当前解释器 importlib.find_spec（零导入、毫秒级）；
  2) 反查后端入口 `trpc-agent-eval-server` 的 shebang → 装包的真正解释器 → 用它再定位；
  3) `pip show` 的 Location 字段；
  4) 全部失败时，打印「如何自己找」手把手指引，并以非零码退出。

用法:
  python3 scripts/find_source.py
"""
from __future__ import annotations

import importlib.util as _u
import json
import os
import shutil
import subprocess
import sys

# 权威模块地图：想确认什么 → 读哪个文件（相对各自包根）。
# 这些是写作时的快照；若文件改名，按符号名在包目录内 Grep 即可。
_SDK_MAP = [
    ("指标需要哪些输入 / 打分逻辑", "_eval_metrics.py"),
    ("指标↔评估器注册与分发", "_evaluator_registry.py"),
    ("criterion 结构与键名", "_criterion_registry.py"),
    ("LLM 裁判输入与 rubric 语义", "_llm_judge.py"),
    ("LLM 评估器装配（judge_model/call_judge）", "_llm_evaluator.py"),
]
_SERVER_MAP = [
    ("指标 UI 元信息（when_to_use/black_box_allowed）", "sdk/metric_catalog_meta.py"),
    ("各对象 REST 入参/校验", "api/"),
]

# (展示名, import 模块名, pip 分发名, 模块地图)
_PKGS = [
    ("后端 server", "trpc_agent_eval_server", "trpc-agent-eval-server", _SERVER_MAP),
    ("SDK（评测核心）", "trpc_agent_self_evolution", "trpc-agent-self-evolution", _SDK_MAP),
]

_ENTRYPOINT = "trpc-agent-eval-server"

# 让子解释器吐出多个模块路径的探针（find_spec 不执行模块体，零副作用）。
_PROBE = (
    "import importlib.util as u, json, sys\n"
    "out = {}\n"
    "for m in sys.argv[1:]:\n"
    "    try:\n"
    "        s = u.find_spec(m)\n"
    "    except Exception:\n"
    "        s = None\n"
    "    locs = list(s.submodule_search_locations) if (s and s.submodule_search_locations) else []\n"
    "    out[m] = locs[0] if locs else None\n"
    "print(json.dumps(out))\n"
)


def _from_spec(module: str) -> str | None:
    """① 当前解释器定位。"""
    try:
        spec = _u.find_spec(module)
    except (ImportError, ValueError, ModuleNotFoundError):
        return None
    if spec is None:
        return None
    if spec.submodule_search_locations:
        return list(spec.submodule_search_locations)[0]
    if spec.origin and spec.origin not in ("built-in", "namespace"):
        return os.path.dirname(spec.origin)
    return None


def _python_from_entrypoint() -> str | None:
    """② 反查后端入口的解释器：读 console_script 的 shebang。"""
    entry = shutil.which(_ENTRYPOINT)
    if not entry:
        return None
    try:
        with open(entry, "rb") as f:
            first = f.readline()
    except OSError:
        return None
    if not first.startswith(b"#!"):
        return None  # 可能是二进制 launcher，无法读 shebang
    line = first[2:].decode("utf-8", "replace").strip()
    parts = line.split()
    if not parts:
        return None
    # 形如 `/usr/bin/env python3` → 取 env 解析后的 python；否则取首段绝对路径
    if os.path.basename(parts[0]) == "env" and len(parts) > 1:
        return shutil.which(parts[1])
    return parts[0] if os.path.exists(parts[0]) else shutil.which(os.path.basename(parts[0]))


def _locate_via_python(py: str, modules: list[str]) -> dict[str, str | None]:
    """用指定解释器批量定位模块。"""
    try:
        r = subprocess.run([py, "-c", _PROBE, *modules], capture_output=True, text=True, timeout=30)
        return {m: v for m, v in json.loads(r.stdout.strip()).items()} if r.stdout.strip() else {}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}


def _locate_via_pip(py: str | None, dist: str) -> str | None:
    """③ 用 pip show 的 Location 推导包目录。"""
    py = py or sys.executable
    try:
        r = subprocess.run([py, "-m", "pip", "show", dist], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    loc = None
    for ln in r.stdout.splitlines():
        if ln.startswith("Location:"):
            loc = ln.split(":", 1)[1].strip()
            break
    if not loc:
        return None
    cand = os.path.join(loc, dist.replace("-", "_"))
    return cand if os.path.isdir(cand) else None


def _self_help() -> None:
    """④ 全部失败：告诉 agent 如何自己找。"""
    print("\n未能自动定位源码。请按下列方式自行定位（仍为只读查证）：")
    print("-" * 60)
    print("1) 找出运行后端的解释器（入口 shebang 最可靠）：")
    print(f"     command -v {_ENTRYPOINT}        # 入口路径")
    print(f"     head -1 $(command -v {_ENTRYPOINT})   # 读 shebang，得到装包的 python")
    print("   或对运行中的后端进程取解释器：")
    print(f"     pgrep -af {_ENTRYPOINT}         # 拿到 PID（或看 ps 中的 python 进程）")
    print("     readlink -f /proc/<PID>/exe     # 该 PID 的真实解释器")
    print("2) 用那个 <python> 定位包目录：")
    print('     <python> -c "import importlib.util as u;print(u.find_spec(\'trpc_agent_self_evolution\').submodule_search_locations[0])"')
    print('     <python> -c "import importlib.util as u;print(u.find_spec(\'trpc_agent_eval_server\').submodule_search_locations[0])"')
    print("3) 或用 pip 的 Location：")
    print("     <python> -m pip show -f trpc-agent-eval-server   # 看 Location 与文件清单")
    print("     <python> -m pip show -f trpc-agent-self-evolution")
    print("   说明：editable 安装 Location 指向源码仓库；普通安装在 .../site-packages 下。")
    print("4) 若后端装在 venv/conda：先激活该环境，或直接用其 python 绝对路径执行上面命令。")
    print("\n拿到包目录后，用 Grep/Read 按 指标名/criterion键/字段名 查证（只读，勿改）。")


def main() -> int:
    print("源码定位（只读 · 最后保底排错手段）")
    print("=" * 60)
    print("先用 discover/catalog/allowed + 实跑冒烟定位问题；都无法解释时，")
    print("再读下列源码查证语义。严禁修改已安装包内文件。\n")

    modules = [m for _, m, _, _ in _PKGS]
    roots: dict[str, str | None] = {m: _from_spec(m) for m in modules}

    # ② 当前解释器有缺失 → 反查后端入口的解释器补齐
    # 注意：venv 的 python 常是系统 python 的软链，realpath 会归一成同一二进制，
    # 但二者 sys.path 不同（venv 默认不含 user-site）。故按「可执行路径字符串」判异，
    # 不可用 realpath，否则会误判为同一解释器而跳过兜底。
    if any(v is None for v in roots.values()):
        alt = _python_from_entrypoint()
        if alt and alt != sys.executable:
            for m, v in _locate_via_python(alt, [m for m in modules if roots[m] is None]).items():
                if v:
                    roots[m] = v
        # ③ 仍缺失 → pip show 兜底
        for _, m, dist, _ in _PKGS:
            if roots[m] is None:
                roots[m] = _locate_via_pip(alt, dist)

    any_found = False
    for label, module, dist, fmap in _PKGS:
        root = roots.get(module)
        print(f"## {label}  [{module}]")
        if not root:
            print(f"  未定位到（尝试过当前解释器 / 入口 shebang / pip show）。dist={dist}")
            print()
            continue
        any_found = True
        print(f"  源码目录: {root}")
        print("  权威模块地图（想确认什么 → 读哪）:")
        for what, rel in fmap:
            path = os.path.join(root, rel)
            mark = "" if os.path.exists(path) else "  (已改名? 按符号名 Grep)"
            print(f"    - {what}\n        {path}{mark}")
        print()

    print("-" * 60)
    print("查证示例（只读）:")
    print('  grep -rn "llm_rubric_critic" <SDK源码目录>')
    print("  # 然后用 Read 打开命中文件，按需求字段/打分逻辑核对")
    print("\n前端: npm 构建产物，非源码依据。定位（如需）: npm root -g")

    if not any_found:
        _self_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
