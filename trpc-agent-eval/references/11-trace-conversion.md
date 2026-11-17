# 11 任意 Trace 转 EvalSet

目标：把任意平台 trace、JSONL 运行日志、OpenInference/OTel spans、厂内导出文件、用户自定义事件格式快速转换为完整 `.evalset.json`，并尽量不漏字段。不为每个平台写死 Adapter；Agent 的核心能力是快速找出转换方法：分类结构、生成语义 mapping、审计未映射字段，复杂格式再生成一次性 normalizer。

## 固定流程

```bash
python3 scripts/inspect_trace_shape.py --input /abs/trace_or_dir --json-out trace_shape.json
# 先读 trace_shape.json.recommended_strategy，再复制并修改最接近模板
python3 scripts/convert_trace_to_evalset.py --input /abs/trace_or_dir --mapping trace_mapping.json --output converted.evalset.json --audit-out conversion_audit.json
python3 scripts/validate_trace_evalset.py --file converted.evalset.json --audit conversion_audit.json --json-out validation_report.json
python3 scripts/create_dataset.py --source upload --name 线上Trace集 --file converted.evalset.json
```

用户只需要提供 trace 样例、导出文件或目录；Agent 负责读文件、判断转换路线、生成 mapping 或 normalizer、dry-run、读审计/验证报告、修复并重跑。

## 快速找转换方法

拿到未知 trace 后，Agent 按这个顺序判断：

1. **messages / events / turns 流**：存在数组，元素里有 `role/actor/speaker/author` 和 `content/payload/text`。用 `generic.messages.json`，把自定义角色写进 `user_roles`、`assistant_roles`、`tool_roles`；工具调用事件用 `tool_call_when` 和 `tool_call_*` 字段声明。
2. **spans / tree**：存在 `span_id/parent_span_id/openinference.span.kind/gen_ai.*`。用 `generic.spans.json` 或 `openinference.json`，重点找 AGENT/TOOL span、input/output、tool id/name/args/result。
3. **flat request log**：一行或一个对象就是一次请求，有 `prompt/query/input` 和 `response/output/answer`。用 `flat-jsonl.json`。
4. **跨文件、流式 chunk、字段需 join/排序/聚合**：不要硬套 mapping，写一次性 `normalizer.py`，输出为 messages/spans/flat 中一种，再跑通用转换。

`inspect_trace_shape.py` 会输出 `recommended_strategy.kind/template/next_steps`，但这只是路线建议；Agent 必须结合样例值确认语义。

## Mapping 语义

mapping 绑定语义，不绑定平台名：

| 字段 | 含义 |
|------|------|
| `kind` | `messages` / `spans` / `flat` |
| `record_selector` | 一条 trace、请求或会话所在位置 |
| `trace_id` / `session_id` / `user_id` | trace、会话、用户标识 |
| `user_input` / `final_response` | 用户输入与最终回复 |
| `expected_final_response` | 可选参考答案、ground truth、reference |
| `tool_calls` / `tool_responses` | flat 格式下的工具调用与工具返回数组 |
| `messages.path` | messages 数组位置 |
| `messages.user_roles` / `assistant_roles` / `tool_roles` | 自定义事件角色，如 client/agent/tooling |
| `messages.tool_call_when` | 判断某条 assistant/agent 事件是否是工具调用 |
| `messages.tool_call_id/name/arguments` | 自定义工具调用字段 |
| `spans.path` | spans/tree 数组位置 |
| `tool_call_id` / `tool_name` / `tool_arguments` / `tool_result` | span 格式下工具字段 |

路径支持 `$.a.b`、`$[*]`、`$.items[*].x`；对 `attributes` 中带点号的 key（如 `openinference.span.kind`、`tool_call.id`）会做宽松匹配。

## 模板选择

- `generic.messages.json`：OpenAI/LangChain 风格 messages 数组，role=user/assistant/tool。
- `generic.spans.json`：通用 span/tree，AGENT/CHAIN span 提供输入输出，TOOL span 提供工具调用与返回。
- `openinference.json`：OpenInference/OTel 语义字段优先，如 `openinference.span.kind`、`input.value`、`output.value`、`tool_call.*`、`session.id`、`user.id`。
- `flat-jsonl.json`：一行一请求，常见字段为 `prompt/query/input`、`response/output/answer`、`tool_calls`、`tool_responses`。

## 质量报告怎么读

`conversion_audit.json` 关注转换过程：

- `degradations`：缺失或降级原因，如 `missing_tool_responses`、`missing_expected_reference`。
- `unmatched_tool_uses` / `unmatched_tool_responses`：工具调用和返回 id 对不齐。
- `tool_uses` / `tool_responses`：每个 case 保留下来的工具轨迹数量。
- `raw_paths_total` / `unmapped_paths`：原始 trace 叶子字段数量和未被 mapping 覆盖的字段路径。未映射不等于错误，但 Agent 必须判断是否有评测相关字段漏掉。

`validation_report.json` 关注评测可用性：

- `loadable=true`：EvalSet 可加载，trace case 合法。
- `recommended_metrics.available`：当前数据可直接用的指标。
- `recommended_metrics.unavailable`：不可用指标及原因。

默认策略是“保留并降级”：缺 expected 或 tool_responses 不阻断转换，但必须明确告诉用户哪些指标不能可靠使用。

## 指标可用性

| 数据条件 | 推荐指标 |
|----------|----------|
| 有 actual final_response + expected final_response | `final_response_avg_score`、`llm_final_response`、`llm_rubric_response` |
| 有 tool_uses | `tool_trajectory_avg_score` |
| 有 tool_responses + final_response | `llm_hallucinations`、`llm_rubric_knowledge_recall` |
| 缺 expected | 可做 trace 归档和幻觉/知识类检查；不能可靠做参考答案比对 |
| 缺 tool_responses | 可做工具调用轨迹；不能可靠做 grounding/hallucination |

如果一批 trace 质量差异大，建议拆成两个数据集：高质量集用于正式回归，低质量集保留做覆盖分析或后续补字段。

## 复杂格式处理

声明式 mapping 失败时，不要停止。Agent 应读取原始样例和 validator 报告，选择一条路线：

1. 修改 mapping 路径后重跑。
2. 如果平台字段需要复杂合并、排序、跨文件 join、流式 chunk 合并，在用户工作区生成一次性 `normalizer.py`，把原始数据输出成 messages/spans/flat 中一种，再走通用转换脚本。
3. 如果高频平台已稳定复用，再考虑把经过验证的 mapping/normalizer 提炼成正式 SDK Adapter。

修复时优先保住评测相关字段：用户输入、最终回复、工具调用、工具返回、session/context metadata、expected/rubric 来源。

交付前检查清单：

- `converted.evalset.json` 可被 validator 加载。
- 每个 trace case 都是 `eval_mode="trace"` 且有 `actual_conversation`。
- tool call/result 能对齐；不能对齐时 audit 有原因。
- `unmapped_paths` 已人工判断：评测相关字段已补映射，非评测字段可说明保留在 raw/source 或安全忽略。
- 推荐指标和不可用指标原因已经解释给用户。
