# 03 数据集

数据集是 `.evalset.json` 文件，含若干 `eval_cases`。理解全部字段才能适配各种场景。

## evalset 顶层

```json
{
  "eval_set_id": "唯一 id（仅 [A-Za-z0-9_]，不含连字符/空格；显示名才可随意）",
  "name": "显示名",
  "description": "说明",
  "eval_cases": [ /* EvalCase */ ]
}
```

## EvalCase 字段

| 字段 | 说明 |
|------|------|
| `eval_id` | 用例 id |
| `eval_mode` | 省略=普通（执行被测 Agent）；`"trace"`=离线（用 `actual_conversation` 直接打分） |
| `conversation` | **期望**对话（参考答案）：Invocation 列表 |
| `actual_conversation` | **实际**对话（trace 模式必填）：被测系统已产生的真实输出 |
| `conversation_scenario` | 模拟用户场景：`{starting_prompt, conversation_plan}`，由 LLM 扮演用户驱动动态多轮。**依赖后端实现“模拟用户”，部分版本仅支持静态多轮 `conversation`**；用前先 `discover.py` 确认 |
| `session_input` | `{app_name, user_id, state}`，预置初始会话状态 |
| `context_messages` | 每轮推理前注入的上下文消息（Content 列表，如 system 提示） |

## Invocation 字段

```json
{
  "invocation_id": "可选",
  "user_content": { "parts": [{ "text": "用户输入" }], "role": "user" },
  "final_response": { "parts": [{ "text": "期望/实际回复" }], "role": "model" },
  "final_response_pattern": "可选：正则，用于按模式匹配回复",
  "final_behavior": "可选：最终行为文本（供行为检查/llm_final_behavior）",
  "final_behavior_match": "可选：单个行为检查函数名",
  "final_behavior_matches": ["可选：多个行为检查函数名，优先级高于 final_behavior_match，得分取平均"],
  "intermediate_data": {
    "tool_uses": [{ "id": "t1", "name": "工具名", "args": { } }],
    "tool_responses": [{ "id": "t1", "name": "工具名", "response": { } }],
    "intermediate_responses": []
  }
}
```

- 一个 case 含多个 Invocation = 多轮，按顺序执行。
- `final_response`（API 简易用例里的 `expected_output`）/ `final_response_pattern` 是 `final_response_avg_score`、
  `llm_final_response`、`llm_rubric_*` 的**比对目标**——没有它，这些指标无从打分。
- `tool_uses` 用于 `tool_trajectory_avg_score`（对比工具名/参数）。
- `tool_responses` 是 `llm_hallucinations` 的 grounding context（逐句核验是否有据）。

> 每个用例至少要带一种**评分依据**（`expected_output`/`final_response_pattern`/`final_behavior*`/`tool_calls`），
> 否则多数指标无法打分（trace 回放或仅靠 prompt 的裁判除外）。`add_case.py` 会在缺失时告警，并提示该用例可配哪类指标。

## 多个行为检查器

expected invocation 可填 `final_behavior_matches: ["check_a","check_b"]`，对每个检查器分别判定、
得分取平均；存在时**优先于** `final_behavior_match`。需配 `final_behavior_avg_score` 指标，
且 `criterion.finalBehavior.allowed_matches` 要列出这些函数名。见 [07](07-scripts-registry.md)。

> 注意区分：`final_behavior` 文本传给 **LLM 裁判** `llm_final_behavior`；而 `final_behavior_match(es)`
> 引用的**行为检查函数收到的是该 invocation 的用户输入文本(user_content)**，不是 `final_behavior`。

## 六种数据来源

| 来源 | 方式 | 脚本/接口 | 适用 |
|------|------|-----------|------|
| 空集 + 逐条加 | `source_kind=empty` 后 `POST /{id}/cases` | `create_dataset.py --source empty` + `add_case.py` | 简单用例（见下方能力边界） |
| 上传文件 | `POST /api/datasets/import/upload`（multipart，文件名 `*.evalset.json`，≤16MB） | `create_dataset.py --source upload --file` | 复杂字段（tool_responses/多轮/模拟用户） |
| 路径登记 | `source_kind=path` | `create_dataset.py --source path --source-path` | 服务端已有大文件，不复制 |
| 任意 trace 转换 | 先转完整 `.evalset.json` 后上传 | `inspect_trace_shape.py` + `convert_trace_to_evalset.py` + `validate_trace_evalset.py` + `create_dataset.py --source upload` | 任意平台 trace / JSONL / 厂内日志 |
| Langfuse 导入 | `POST /api/datasets/import/langfuse` | 见下 | 从线上 trace 拉取 |
| 评测运行导出 | `POST /api/datasets/from-evaluation-runs` | `export_trace_dataset.py` | 把已完成 run 转成可复跑 trace 集 |

## 普通用例与 trace 混合集

一个数据集里既有普通用例（省略 `eval_mode`，需要实际调用 Agent）又有 `eval_mode="trace"` 的离线轨迹时，
应选择能同时处理实跑和轨迹的 Agent mode。目前优先使用 `sdk` 或 `llm`；黑盒 `http`/`cli` 与 `managed`
通常不适合混合集。迁移已有 SDK 评测时，如果用户同时有手写 eval cases 和历史 trace，推荐保留为一个混合集，
并用 `mode=sdk` Agent 创建评测方案。

### API 加用例的能力边界（重要）

`add_case.py` / `POST /{id}/cases`（CaseCreate）的 Invocation 只支持：
`user_text` / `expected_output` / `actual_output` / `final_response_pattern` /
`tool_calls`（仅 id/name/args）/ `final_behavior` / `final_behavior_match` / `final_behavior_matches`。

**不支持** `tool_responses`、`session_input.state`、`context_messages`、`conversation_scenario`、
`intermediate_responses`。需要这些字段时，**必须改用完整 `.evalset.json` 上传**（`--source upload`）。
任意 trace 转换场景一律走完整文件上传，避免把工具返回、session/context metadata 或多轮轨迹丢掉。

## 任意 trace 转换要点

任意平台 trace、OpenInference/OTel 导出、厂内 JSONL 运行日志不要直接写平台 Adapter。先把字段映射到语义：
`record_selector`、`user_input`、`final_response`、`tool_calls`、`tool_responses`、`session_id`、`trace_id`、
`user_id`、`expected`。转换流程：

```bash
python3 scripts/inspect_trace_shape.py --input /abs/traces --json-out trace_shape.json
# 复制 templates/trace-mapping/*.json 中最接近的模板，按 trace_shape.json 修改路径
python3 scripts/convert_trace_to_evalset.py --input /abs/traces --mapping trace_mapping.json --output converted.evalset.json --audit-out conversion_audit.json
python3 scripts/validate_trace_evalset.py --file converted.evalset.json --audit conversion_audit.json --json-out validation_report.json
python3 scripts/create_dataset.py --source upload --name 线上Trace集 --file converted.evalset.json
```

`conversion_audit.json` 会记录缺失字段、无法对齐的工具返回和降级原因；`validation_report.json` 会给出可用/不可用指标。
缺字段时默认“保留并降级”：生成可用数据集，但报告中说明哪些指标不能可靠使用。

### Langfuse 导入要点

`POST /api/datasets/import/langfuse`，关键字段：`name`、`host`、
`public_key_secret` / `secret_key_secret`（命名密钥名，先 `set_secret.py` 登记）、
`fetch_mode`（`query` / `trace_ids`）、可选 `trace_ids`/`session_id`/`start`/`end`/`tags`/`user_id`/`limit`(≤2000)/`merge_session`。

## 模板

- 简单用例（API）：`templates/dataset/case.normal.json`、`case.trace.json`
- 完整文件（上传）：`templates/dataset/{normal,multiturn,trace,hallucination,user_sim}.evalset.json`
  （上传文件名**必须以 `.evalset.json` 结尾**，后端强制校验）
- 任意 trace mapping：`templates/trace-mapping/{generic.messages,generic.spans,openinference,flat-jsonl}.json`
