# 04 指标方案

指标方案 = 指标项数组。每个指标项：

```json
{ "metric_name": "<指标名>", "threshold": 1.0, "criterion": { /* 见下 */ } }
```

创建：`create_metric.py`（`POST /api/metric-configs`，`definition` 即指标项数组；或上传 `.metric.json`）。
选型前先查阅 catalog：`python3 scripts/metric_catalog.py`。**指标全集以 `/api/metric-configs/catalog` 运行时为准**。

## 指标（按类别；下列为当前快照，全集以 catalog 为准）

### 规则类（确定性）

| 指标 | criterion 键 | 说明 |
|------|--------------|------|
| `final_response_avg_score` | `finalResponse` | 回复文本/JSON 与期望比对 |
| `tool_trajectory_avg_score` | `toolTrajectory` | 工具调用轨迹（名/参数）比对 |
| `final_behavior_avg_score` | `finalBehavior` | 用注册的行为检查函数判定最终副作用 |

### LLM 裁判类（criterion 键统一为 `llmJudge`）

| 指标 | 用途 |
|------|------|
| `llm_final_response` | 裁判判定回复是否满足期望 |
| `llm_rubric_response` | 按 rubric 逐项给回复打分 |
| `llm_rubric_critic` | 按 rubric **严格**对齐参考答案（reference 为权威目标；事实型，漏答/错答/语义偏离均判不通过） |
| `llm_rubric_reference_critic` | 按 rubric **宽松**匹配参考答案（reference 为质量锚点；对话/创作型，语义等价的不同表述可通过） |
| `llm_rubric_knowledge_recall` | 知识召回（结合检索工具结果） |
| `llm_hallucinations` | 基于 grounding context 逐句裁定是否幻觉 |
| `llm_final_behavior` | 裁判（可调工具）核验最终行为是否达成 |
| `llm_judge_template` | 自定义 prompt 模板 + 响应解析器 |

> 命名提示（反直觉，易错）：`llm_rubric_critic` 与 `llm_rubric_reference_critic` **都需要参考答案**，
> 区别在严格程度——`critic` 把 reference 当**权威目标**（严格），`reference_critic` 把 reference 当**质量锚点**（宽松）。
> 以运行时 `metric_catalog.py` 的 `when_to_use` 为准。

## criterion 结构

### finalResponse（`final_response_avg_score`）
```json
{ "finalResponse": { "text": { "match": "exact|contains|regex", "case_insensitive": false },
                     "json": { "ignore_tree": {"id": true}, "number_tolerance": 1e-6 } } }
```
`text` 与 `json` 可单用或并用（并用须都通过）。

### toolTrajectory（`tool_trajectory_avg_score`）
```json
{ "toolTrajectory": {
    "order_sensitive": false,
    "subset_matching": false,
    "default":   { "name": {"match":"exact"}, "arguments": {"match":"exact","number_tolerance":1e-6} },
    "overrides": { "工具名": { "arguments": {"ignore_tree": {"request_id": true}} } } } }
```
`name` 用 TextCriterion，`arguments` 用 JSONCriterion；`overrides` 按工具名覆盖 `default`。
`subset_matching=true` 时实际可多调工具但期望项都须命中；`order_sensitive` 控制是否按序。
黑盒模式默认不可用，需 cli/http + `output_protocol` 解锁。

### finalBehavior（`final_behavior_avg_score`）
```json
{ "finalBehavior": { "allowed_matches": ["check_order_created", "check_email_sent"] } }
```
`allowed_matches` 必须是已登记的行为检查函数名；数据集用 `final_behavior_match(es)` 引用。

### llmJudge（所有 LLM 裁判指标）
```json
{ "llmJudge": {
    "judge_model": {
      "provider_name": "openai",
      "model_name": "${MODEL:glm_flash}",
      "base_url":  "${MODEL:glm_flash}",
      "api_key":   "${MODEL:glm_flash}",
      "generation_config": { "temperature": 0.0 },
      "num_samples": 1, "weight": 1.0, "think": false
    },
    "models_aggregator": "all_pass",
    "rubrics": [ { "id":"acc","content":{"text":"是否准确"},"description":"准确性","type":"FINAL_RESPONSE_QUALITY" } ],
    "knowledge_tool_names": ["knowledge_search"],
    "tool_instruction": "（仅 llm_final_behavior）告诉裁判如何用工具核验",
    "template": { "prompt": "...{user_input}...{actual_response}...{expected_response}...",
                  "response_scorer_name": "single_score" } }
}
```

**`${MODEL:<profile>}` 占位符**：放在 `model_name`/`base_url`/`api_key` 上，系统按字段名分别解析为
模型 Profile 的对应值（api_key 解密注入、不落明文）。先用 `set_model.py` 登记 Profile。
> 模板里的 `glm_flash` 只是**占位示例**，多数环境并不存在。请换成你自己的 Profile 名（`discover.py` 会列出现有 Profile）。
> `create_metric.py` 建指标时会扫描 `${MODEL:}`/`${SECRET:}`，引用了未登记的会**当场告警**；加 `--for-mode <mode>` 还会复核该指标在此模式下是否可用。

**字段按指标取用**：
- `rubrics`：`llm_rubric_*` 用；其余可省。
- `knowledge_tool_names`：`llm_rubric_knowledge_recall`（默认 `["knowledge_search"]`）。
- `tool_instruction`：`llm_final_behavior`。
- `template`：`llm_judge_template` 必填，其余忽略。
- `llm_hallucinations`：只需 `judge_model`，grounding 来自数据集 `tool_responses`。

### 多裁判与聚合
裁判分两种，都放在 `llmJudge` 内：
- **内置裁判 `judge_model`**：直接配模型 Profile（`${MODEL:<profile>}`），见上。
- **外部裁判 `call_judge`**：`{"name": "<agent_id>"}`，`name` 指向一个**已创建的 Agent id**（http/cli/llm/managed/sdk，
  **不能是 trace**）；评测前系统自动把该 Agent 注册为裁判闭包，以其回复作为裁判输出。形态见
  `templates/metric/llm_call_judge.json`（把 `<judge_agent_id>` 换成真实 Agent id）。

单/多写法：
- 单内置：`judge_model`；单外部：`call_judge: {"name": ...}`。
- 多内置：`judge_models: [...]`；多外部：`call_judges: [{"name": ...}, ...]`；
  混用须**两边都用列表**（`judge_models`+`call_judges`）。
- 同类单/列表互斥（不能同时给 `judge_model` 和 `judge_models`）。
- `models_aggregator`：`all_pass`(默认)/`any_pass`/`majority_pass`/`avg`/`weighted_avg`/`weighted_majority`；
  加权类需各 `weight` 之和 > 0。`parallel` 控制是否并发跑多裁判。

## llm_judge_template：prompt 占位符 + 响应解析器

`template.prompt` 用 Python `str.format` 占位符。基础占位符：`{user_input}`、`{actual_response}`、
`{expected_response}`（可省；省略则该指标不要求期望对话）。运行时可能支持更多占位符
（如 `{actual_tool_calls}`、`{final_behavior}`），**以服务端为准**。

`template.response_scorer_name` 路由裁判输出的解析方式：
- 内置 `single_score`（取 [0,1] 数值）/ `final_response`（二元通过）/ `rubric_scores`（按 rubric）。
- 自定义解析器先用 `create_response_scorer.py` 登记，再在此填其名，见 [07](07-scripts-registry.md)。

## mode ↔ 指标门控

| Agent mode | 可用指标 |
|------------|----------|
| `llm` / `trace` / `managed` / `sdk` | 全部 catalog 指标 |
| `http` / `cli`（黑盒，无协议） | `final_response_avg_score`、`final_behavior_avg_score`、`llm_final_response`、`llm_final_behavior`、`llm_rubric_response`、`llm_rubric_critic`、`llm_rubric_reference_critic`、`llm_judge_template` |
| `http`/`cli` + `output_protocol` | 上面 + `tool_trajectory_avg_score`、`llm_hallucinations` |

创建方案前用 `metric_catalog.py --mode <mode> [--output-protocol ...]` 核对，避免门控报错。
门控随版本变化，**始终以 `/api/metric-configs/allowed` 为准**。

SDK Agent 是白盒 Runner 接入，能保留 SDK 事件、工具调用与最终回复；迁移已有 SDK 评测时优先用
`metric_catalog.py --mode sdk` 展示可用指标，再把原评测脚本里的 metric / judge / rubric 映射为 WebUI 指标方案。

## 创建形态（数组 vs 对象）

- `create_metric.py --source empty` 的 `definition` 是**指标项数组** `[ {metric_name,threshold,criterion}, ... ]`。
- `--source upload` 的 `.metric.json` 必须是**对象** `{ "metrics": [ ...指标项... ], "num_runs": 1, "metric_id": "可选" }`；
  上传时 id 取自 `metric_id` 字段或文件名 `<id>.metric.json`（`--name` 仅作显示名）。
  显式 id（`metric_id`、评测方案 `--id` 等）一律只允许 `[A-Za-z0-9_]`，不含连字符/空格。

模板：单指标项 `templates/metric/<指标名>.json`；组合数组(empty 源) `metric_config.example.json`；
可直接上传的对象形 `metric_config.upload.metric.json`。
