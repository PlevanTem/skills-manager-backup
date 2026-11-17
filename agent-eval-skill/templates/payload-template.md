# 评测 Payload 模板

在完成 agent 扫描和 trace 数据源确认后，复制并填写这份模板。

## Trace 来源摘要

- Agent 仓库：
- 评测项目是否已存在：
- 技术栈 / 运行时：
- 框架 / 最小实现方式：
- 入口路径：
- Trace 来源：
- Prompt 来源：
- Tool transcript 来源：
- 最终回答来源：
- 默认 judge 模型：
- 大上下文兜底模型：
- 平台关键配置状态：
- 已知缺失字段：

## Trajectory Payload 草案

```json
{
  "trace_meta": {
    "trace_id": "",
    "session_id": "",
    "agent_name": "",
    "timestamp": "",
    "turn_index": 0
  },
  "evaluation_scope": {
    "task": "trajectory_reasonableness",
    "score_target": "current_trace",
    "history_policy": ""
  },
  "history_context": {
    "history_summary": "",
    "recent_messages": []
  },
  "current_trace": {
    "user_input": ""
  },
  "runtime_context": {
    "session_status": "",
    "session_outcome_summary": "",
    "session_end_reason": ""
  },
  "prompt_context": {},
  "execution_error_summary": "",
  "trajectory": {
    "steps": [],
    "trajectory_text": ""
  }
}
```

## E2E Payload 草案

```json
{
  "trace_meta": {
    "trace_id": "",
    "session_id": "",
    "agent_name": "",
    "timestamp": "",
    "turn_index": 0
  },
  "evaluation_scope": {
    "task": "e2e_answer_quality",
    "score_target": "current_trace",
    "history_policy": ""
  },
  "question_context": {
    "history_summary": "",
    "recent_messages": [],
    "user_input": ""
  },
  "output": {
    "final_answer": ""
  },
  "runtime_context": {},
  "prompt_context": {},
  "execution_context": {
    "tool_results": [],
    "knowledge_inputs": []
  }
}
```

## 字段映射表

要求：

- 这张表不只是示例，至少要覆盖所有高价值字段和所有会影响编排层 signals 的字段
- 如果某个 JSON 草案字段没有单独成行，要在备注里说明为什么可以并入同一类字段
- `主来源`、`fallback` 和 `presence logging` 三列必须一起看，不能只填其中一列

| Payload 字段 | 主来源 | fallback | 是否必须 | 价值等级 | 压缩方式 | 预算占用 | 超预算处理 | presence logging | 关联 flags / labels | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| `trace_meta.trace_id` |  |  | yes | 高 | none | 低 | 无 | `present / missing` |  |  |
| `current_trace.user_input` |  |  | yes | 高 | none |  |  | `present / empty / missing + source` | `invalid_user_query` |  |
| `runtime_context.session_outcome_summary` |  |  | conditional | 低 / 中 | summary |  |  | `present / empty / missing + source` |  | trajectory 只允许 session 级收尾摘要，不单独放结果字段 |
| `runtime_context.*` |  |  | no | 中 / 低 |  |  |  | `present / empty / missing` |  |  |
| `prompt_context.*` |  |  | conditional | 中 |  |  |  | `present / empty / missing` |  |  |
| `trajectory.steps` |  |  | yes for trajectory | 高 |  |  |  | `present / empty / missing + count` | `trajectory_evaluable` |  |
| `execution_context.tool_results` |  |  | no | 中 |  |  |  | `present / empty / missing + count` | `tool_rejected_by_user` |  |
| `execution_context.knowledge_inputs` |  |  | no | 条件性 |  |  |  | `present / empty / missing + count` | `knowledge_retrieval_used` |  |

## 编排层信号（默认不进入 judge payload）

这些内容默认属于评测编排层 / 路由层 / 报告层：

- `case_labels`
- `flags`
- skip / gating 决策
- score metadata 里的标签摘要

只有在用户明确确认的极少数场景下，才允许把某个中性控制信号例外暴露给 judge。

## 压缩策略

| 字段 | 为什么会很长 | 策略 | 限制 | 风险 | 触发下一步动作 |
|---|---|---|---|---|---|
|  |  |  |  |  | 切兜底模型 / 跳过样本 / 继续摘要 |

## 缺字段处理

| 缺失字段 | 临时替代 | 当前是否可接受 | 后续是否必须补 | 状态 |
|---|---|---|---|---|
|  |  |  |  | `待确认` / `用户已接受的 TEMP` |

## Presence Logging 计划

要求：

- 这里列出的字段 / flag，要和上面的字段映射表逐项对齐
- 如果某字段不做 presence logging，要明确写理由，而不是留空

| 字段 / flag | 记录时机 | 最小日志内容 | 不记录什么 | 目的 |
|---|---|---|---|---|
| `user_input` | payload 构建时 | `present / empty / missing` + source + length | 原文全文 | 验证字段真实可得性 |
| `runtime_context.session_outcome_summary` | payload 构建时 | `present / empty / missing` + source + length | 原文全文 | 验证 trajectory 收尾摘要是否稳定 |
| `final_answer` | e2e payload 构建时 | `present / empty / missing` + source + length | 原文全文 | 验证 E2E 结果字段是否稳定 |
| `trajectory.steps` | steps 归一化后 | status + count | 全量 steps | 验证过程证据是否充足 |
| 关键 `flags` | label / gating 推导前 | flag 值 + evidence source | 冗长原始 trace | 验证编排层信号是否成立 |

## Flag / Label 依赖提醒

- 哪些 payload 字段缺失会直接影响 flags：
- 哪些 flags 会直接影响 labels：
- 哪些字段如果长期 `missing`，要先暂停相关 label / metric：
