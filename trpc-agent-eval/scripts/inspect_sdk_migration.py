# -*- coding: utf-8 -*-
"""扫描已有 SDK Agent / 评测目录，生成迁移到 WebUI 的候选映射。

该脚本只读用户项目，不创建任何 WebUI 对象。用于迁移向导的第一步：
Agent 拿到用户给的路径后先运行本脚本，再把候选 cwd/module/agent_var/env_vars/
evalset/metric 文件展示给用户确认。

用法:
  python3 scripts/inspect_sdk_migration.py /abs/path/to/examples/evaluation/llm_final_response
  python3 scripts/inspect_sdk_migration.py /abs/path --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描 SDK 评测迁移候选")
    parser.add_argument("path", help="已有 SDK Agent / 评测示例目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON，便于 Agent 二次处理")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"错误: 目录不存在或不是目录: {root}")

    result = inspect(root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print_human(result)


def inspect(root: Path) -> dict[str, Any]:
    py_files = list(_iter_files(root, ".py"))
    agent_candidates = _agent_candidates(root, py_files)
    env_vars = _env_vars(py_files)
    evalsets = sorted(str(p) for p in _iter_named(root, ".evalset.json"))
    metrics = sorted(str(p) for p in _iter_named(root, ".metric.json"))
    readmes = sorted(str(p) for p in _iter_readmes(root))
    scripts = sorted(str(p) for p in py_files if _looks_like_eval_script(p))
    dependency_markers = _sdk_dependency_markers(root)
    migration_hint = _migration_hint(dependency_markers, py_files)
    evaluator_modules = _evaluator_agent_modules(py_files)
    recommended_config = _recommended_agent_config(str(root), agent_candidates, evaluator_modules)

    return {
        "cwd": str(root),
        "agent_candidates": agent_candidates,
        "evaluator_agent_modules": evaluator_modules,
        "recommended_agent_config": recommended_config,
        "sdk_dependency_markers": dependency_markers,
        "recommended_eval_sdk": "trpc-agent-self-evolution",
        "migration_hint": migration_hint,
        "env_vars": env_vars,
        "evalset_files": evalsets,
        "metric_files": metrics,
        "readme_files": readmes,
        "possible_eval_scripts": scripts,
        "next_questions": [
            "确认 Agent 项目目录是否就是 cwd。",
            "确认使用哪个 module 与 agent_var；优先用 recommended_agent_config，旧 agent_module 只作交叉验证。",
            "确认 env_vars 中哪些需要登记为工作区环境变量。",
            "确认 evalset_files / metric_files 是否直接迁移到 WebUI。",
            "询问用户是否同意把评测层迁到 trpc-agent-self-evolution；同意后由 Agent 修改并跑 pytest 验证。",
            "用业务问题探活；若返回不像该项目的 Agent，换下一个候选并继续诊断。",
        ],
    }


def _iter_files(root: Path, suffix: str) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            path = base / name
            if path.name.endswith(suffix):
                out.append(path)
    return sorted(out)


def _iter_named(root: Path, suffix: str) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            path = base / name
            if path.name.endswith(suffix):
                out.append(path)
    return out


def _iter_readmes(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            if name.lower().startswith("readme"):
                out.append(base / name)
    return out


def _agent_candidates(root: Path, py_files: list[Path]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in py_files:
        text = _read_text(path)
        if not _looks_like_agent_module(path, text):
            continue
        vars_found = _agent_vars(text)
        if not vars_found:
            vars_found = ["root_agent"] if "root_agent" in text else [""]
        for var in vars_found:
            module = _module_name(root, path)
            key = (module, var)
            if key in seen:
                continue
            seen.add(key)
            score = _confidence_score(path, text, var)
            candidates.append({
                "module": module,
                "agent_var": var,
                "file": str(path),
                "confidence": _confidence_label(score),
                "_score": score,
            })
    sorted_candidates = sorted(candidates, key=lambda item: item["_score"], reverse=True)
    for item in sorted_candidates:
        item.pop("_score", None)
    return sorted_candidates


def _looks_like_agent_module(path: Path, text: str) -> bool:
    if path.name.startswith("test_") and "root_agent" not in text:
        return False
    if path.name in {"agent.py", "__init__.py"} and "root_agent" in text:
        return True
    markers = (
        "LlmAgent",
        "BaseAgent",
        "Runner",
        "trpc_agent_sdk",
        "trpc-agent-sdk",
        "trpc-agent-py",
        "root_agent",
    )
    return any(marker in text for marker in markers)


def _agent_vars(text: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\s*=", text):
        name = match.group(1)
        if name == "root_agent" or name.endswith("_agent") or name.endswith("_runner"):
            names.append(name)
    return sorted(set(names), key=lambda name: (name != "root_agent", name))


def _module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(part for part in parts if part)


def _confidence_score(path: Path, text: str, var: str) -> int:
    score = 0
    if var == "root_agent":
        score += 3
    if path.name == "agent.py":
        score += 2
    if (
        "trpc_agent_sdk" in text
        or "trpc-agent-sdk" in text
        or "trpc-agent-py" in text
        or "LlmAgent" in text
        or "Runner" in text
    ):
        score += 2
    return score


def _confidence_label(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _recommended_agent_config(
    cwd: str,
    candidates: list[dict[str, str]],
    evaluator_modules: list[dict[str, str]],
) -> dict[str, Any] | None:
    if candidates:
        best = candidates[0]
        return {
            "cwd": cwd,
            "module": best.get("module") or "",
            "agent_var": best.get("agent_var") or "root_agent",
            "source": "agent_candidates",
            "reason": (
                "优先选择直接扫描到 root_agent / Agent 定义的高置信候选；"
                "旧评测脚本中的 agent_module 只作为交叉验证。"
            ),
        }
    if evaluator_modules:
        best = evaluator_modules[0]
        return {
            "cwd": cwd,
            "module": best.get("module") or "",
            "agent_var": "root_agent",
            "source": "evaluator_agent_modules",
            "reason": "未扫描到明确 Agent 定义，暂用旧评测脚本 agent_module 作为候选。",
        }
    return None


def _env_vars(py_files: list[Path]) -> list[str]:
    names: set[str] = set()
    patterns = [
        r"os\.environ\.get\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]",
        r"os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]+)['\"]",
        r"os\.environ\[\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\]",
        r"['\"](TRPC_AGENT_[A-Z0-9_]+)['\"]",
    ]
    for path in py_files:
        text = _read_text(path)
        for pattern in patterns:
            names.update(re.findall(pattern, text))
    return sorted(names)


def _looks_like_eval_script(path: Path) -> bool:
    text = _read_text(path)
    markers = ("AgentEvaluator", "agent_module", "EvalSet", "eval_cases", "metric", "evaluate")
    return any(marker in text for marker in markers)


def _evaluator_agent_modules(py_files: list[Path]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    pattern = re.compile(r"agent_module\s*=\s*['\"]([^'\"]+)['\"]")
    for path in py_files:
        text = _read_text(path)
        for module in pattern.findall(text):
            key = (module, str(path))
            if key in seen:
                continue
            seen.add(key)
            out.append({"module": module, "file": str(path)})
    return out


def _sdk_dependency_markers(root: Path) -> list[dict[str, str]]:
    names = (
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
        "README.md",
        "README.rst",
    )
    markers = ("trpc-agent-sdk", "trpc-agent-py", "trpc_agent_sdk")
    out: list[dict[str, str]] = []
    for path in _iter_dependency_files(root, names):
        text = _read_text(path)
        for marker in markers:
            if marker in text:
                out.append({"marker": marker, "file": str(path)})
    return out


def _migration_hint(markers: list[dict[str, str]], py_files: list[Path]) -> dict[str, Any]:
    marker_names = {item["marker"] for item in markers}
    imports_self_evolution = any("trpc_agent_self_evolution" in _read_text(path) for path in py_files)
    imports_agent_runtime = any("trpc_agent_sdk" in _read_text(path) for path in py_files)
    return {
        "recommendation": "use trpc-agent-self-evolution for the evaluation layer",
        "already_uses_trpc_agent_self_evolution": imports_self_evolution,
        "keep_agent_runtime_dependency": imports_agent_runtime or bool(marker_names & {"trpc-agent-sdk", "trpc-agent-py", "trpc_agent_sdk"}),
        "note": (
            "Do not blindly remove trpc-agent-py/trpc-agent-sdk if the business agent imports trpc_agent_sdk; "
            "those packages may still be required to import root_agent. Migrate pytest evaluation code to "
            "trpc-agent-self-evolution, then verify pytest and WebUI SDK probe."
        ),
    }


def _iter_dependency_files(root: Path, names: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            if name in names or name.startswith("requirements") and name.endswith(".txt"):
                out.append(base / name)
    return sorted(out)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def print_human(result: dict[str, Any]) -> None:
    print(f"# SDK 评测迁移候选\n")
    print(f"[cwd] {result['cwd']}")
    print("\n## Agent 候选")
    if result["agent_candidates"]:
        for item in result["agent_candidates"]:
            agent_var = item["agent_var"] or "（未识别，通常填 root_agent）"
            print(f"- module={item['module']} agent_var={agent_var} confidence={item['confidence']}")
            print(f"  file={item['file']}")
    else:
        print("（未找到明显 root_agent / Runner / LlmAgent，请人工确认模块）")
    print("\n## 旧评测脚本里的 agent_module 候选")
    if result["evaluator_agent_modules"]:
        for item in result["evaluator_agent_modules"]:
            print(f"- module={item['module']} file={item['file']}")
    else:
        print("（未发现）")
    print("\n## 推荐 WebUI SDK 配置")
    recommended = result.get("recommended_agent_config")
    if recommended:
        print(f"- cwd={recommended['cwd']}")
        print(f"- module={recommended['module']}")
        print(f"- agent_var={recommended['agent_var']}")
        print(f"- 依据: {recommended['reason']}")
    else:
        print("（未能自动推荐，请人工确认 cwd/module/agent_var）")
    print("\n## SDK 依赖标记")
    if result["sdk_dependency_markers"]:
        for item in result["sdk_dependency_markers"]:
            print(f"- {item['marker']}  ({item['file']})")
    else:
        print("（未在依赖/README 中发现 trpc-agent-sdk / trpc-agent-py）")
    print("\n## 推荐迁移")
    hint = result["migration_hint"]
    print(f"- 评测层推荐: {result['recommended_eval_sdk']}")
    print(f"- 已使用 trpc_agent_self_evolution: {hint['already_uses_trpc_agent_self_evolution']}")
    print(f"- 保留 Agent 运行时依赖: {hint['keep_agent_runtime_dependency']}")
    print(f"- 说明: {hint['note']}")
    print("\n## 可能需要登记的工作区环境变量")
    print(", ".join(result["env_vars"]) if result["env_vars"] else "（未发现）")
    print("\n## 可迁移数据集")
    _print_list(result["evalset_files"])
    print("\n## 可迁移指标文件")
    _print_list(result["metric_files"])
    print("\n## 可能的评测脚本")
    _print_list(result["possible_eval_scripts"])
    print("\n## 下一步提问")
    for question in result["next_questions"]:
        print(f"- {question}")


def _print_list(items: list[str]) -> None:
    if not items:
        print("（未发现）")
        return
    for item in items:
        print(f"- {item}")


if __name__ == "__main__":
    main()
