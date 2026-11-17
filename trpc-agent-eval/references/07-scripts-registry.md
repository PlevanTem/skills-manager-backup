# 07 脚本注册与转换工具

系统支持登记三类用户脚本。共同约束：名 `^[a-z][a-z0-9_]{0,63}$`、单文件 ≤64KB、
`source_kind` 可为 `upload`（上传内容）或 `path`（服务端绝对路径）。建议先查阅骨架再编写：
各 `create_*` 脚本均提供 `--print-template` 以拉取服务端权威骨架。

## 1) 行为检查脚本（确定性）

- 端点：`/api/behavior-checks`；脚本：`create_behavior_check.py`；模板：`templates/behavior/check.py`。
- 契约：`def {name}(user_content: str) -> tuple[bool, str]`，**函数名=登记名**；子进程执行、30s 超时。
- **入参 `user_content` 是该 invocation 的「用户输入文本」(actual user_content)，不是 Agent 回复，也不是 `final_behavior` 文本。** 检查器无法获取 Agent 输出；如需核验真实副作用，须在函数内自行查询外部系统。（依据：SDK `_final_behavior_evaluator` 传入 `user_content_to_str(actual)`。）
- 用法：数据集 expected invocation 填 `final_behavior_match="{name}"` 或 `final_behavior_matches=[...]`；
  指标用 `final_behavior_avg_score`，`criterion.finalBehavior.allowed_matches` 列出允许的函数名。
- 可选 `description`（`GET /api/behavior-checks` 可见）。

## 2) 自定义 Agent 工具（供内置 llm Agent）

- 端点：`/api/agent-tools`；脚本：`create_agent_tool.py`；模板：`templates/agent-tool/tool.py`。
- 契约：`def {name}(query: str) -> str`，docstring 作为工具描述给 LLM；或模块级 `TOOLS=[fn,...]`。
- 执行：**进程内（无沙箱）**，注意安全。
- 用法：llm Agent 的 `config.tools` 里写该函数名；内置 `read`/`bash`/`grep`/`glob` 可直接用。

## 3) 响应解析脚本（供 llm_judge_template）

- 端点：`/api/response-scorers`；脚本：`create_response_scorer.py`；模板：`templates/response-scorer/scorer.py`。
- 契约：`def {name}(response_text: str) -> tuple[float | bool, str]`；子进程执行、30s 超时。
  第一返回值 float 会 clamp 到 [0,1]，bool→1.0/0.0；第二为原因。
- 入参 `response_text`：AI 裁判模型的原始回复。
- 内置无需登记：`single_score` / `final_response` / `rubric_scores`。
- 用法：`llm_judge_template` 指标的 `criterion.llmJudge.template.response_scorer_name="{name}"`；
  运行时注册为 `llm_judge_template:{name}`。

## 执行隔离提醒

行为检查与响应解析在子进程执行并限时；自定义工具在主进程执行。生产环境建议后端以低权限/容器
运行，避免脚本访问敏感资源。脚本内容上传后存于 workdir 对应子目录。

## 4) Trace 转换辅助脚本（不注册到后端）

这三类脚本只在 Agent/用户工作区本地运行，用于把任意平台 trace 转成完整 `.evalset.json` 后再上传：

- `inspect_trace_shape.py`：只读分析 JSON/JSONL/目录，输出字段路径、样例值和 user/final/tool/session 等候选语义。
- `convert_trace_to_evalset.py`：读取原始 trace 与 `templates/trace-mapping/*.json` 风格的 mapping，生成完整 `eval_mode="trace"` 数据集，并输出 `conversion_audit.json`。
- `validate_trace_evalset.py`：校验 EvalSet 可加载、trace case 合法、工具调用/返回完整性，并推荐可用指标。

这些脚本不消耗模型额度，不创建后端对象；真正进入 WebUI 时仍用 `create_dataset.py --source upload --file <converted.evalset.json>`。
