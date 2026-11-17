# 实现契约参考

这份文档用于把“讨论结果”变成实现层面可测试、可对齐的契约。

如果当前问题更偏向“字段来源怎么落到代码里”“payload / label 为什么在真实 trace 上失真”，建议配合阅读：

- [trace-data-extraction.md](trace-data-extraction.md)

## 目标

统一这几类契约：

- fixture 长什么样
- payload 长什么样
- judge 输出长什么样
- 失败时如何降级

如果这些契约不先写清楚，后面即使有 spec，也很容易边写边漂。

## 一、评测样本契约

先定义“一个评测样本是什么”。

推荐最少包含：

```json
{
  "sample_id": "",
  "trace_id": "",
  "unit_type": "session|turn|trace|task",
  "source": "langfuse_db|langfuse_api|trace_export",
  "input": {},
  "runtime_context": {},
  "messages": [],
  "observations": [],
  "ground_truth": null,
  "expected_labels": [],
  "metadata": {}
}
```

说明：

- `sample_id`：本地 fixture 的稳定标识
- `trace_id`：回链 Langfuse 或原始 trace
- `unit_type`：评测单元
- `ground_truth`：没有就允许为 `null`
- `expected_labels`：用于标签测试

## 二、Trajectory Payload 契约

建议至少保证这些字段稳定：

```json
{
  "trace_meta": {},
  "evaluation_scope": {},
  "history_context": {},
  "current_trace": {},
  "runtime_context": {},
  "prompt_context": {},
  "trajectory": {
    "steps": [],
    "trajectory_text": ""
  }
}
```

最重要的不是字段多，而是字段来源和缺省规则稳定。

注意：

- `case_labels` 默认不属于 judge payload 契约
- `flags` 也默认不属于 judge payload 契约
- 它们更适合留在评测编排层，用于 skip / gating / 报告 / metadata

## 三、E2E Payload 契约

建议至少保证：

```json
{
  "trace_meta": {},
  "evaluation_scope": {},
  "question_context": {},
  "output": {
    "final_answer": ""
  },
  "runtime_context": {},
  "prompt_context": {},
  "execution_context": {}
}
```

同样地：

- 不要默认把 `case_labels` 当成 E2E judge 输入
- 不要默认把 `flags` 当成 E2E judge 输入
- 如果确实要暴露某个控制信号给 judge，必须先在 spec 里写清原因和例外范围

## 四、Judge 输出契约

在定义 judge 输出之前，先把 judge prompt / rubric 自身写清楚。

最低要求不是“一段总说明”，而是对每个纳入评分的指标或维度分别写清：

- 它在评什么
- 主要看哪些证据
- 什么情况给高分
- 什么情况给低分
- 什么情况应标记为不可评

如果这些内容没有逐指标写出来，后面的 judge 输出即使结构稳定，也容易变成“字段齐了但语义很空”。

### Trajectory Judge

如果是多维 trajectory，推荐至少约定：

```json
{
  "scores": {
    "logical_coherence": 0,
    "task_progress": 0,
    "efficiency": 0,
    "context_usage": 0,
    "routing_constraint_following": 0,
    "tool_selection": 0,
    "parameter_construction": 0
  },
  "score": 0,
  "label": "",
  "summary": "",
  "reason": ""
}
```

### E2E Judge

如果是多维 E2E，推荐至少约定：

```json
{
  "scores": {},
  "score": 0,
  "label": "",
  "summary": "",
  "reason": ""
}
```

注意：

- `scores` 可以为空对象，但字段存在更利于统一解析
- `summary` 和 `reason` 至少有一个可用
- `score` 如果允许缺省，必须有统一 fallback 规则

## 四点五、Judge Prompt / Rubric 最低说明

最低要求不只是“有一张表”，而是每个纳入评分的指标 / 维度都要有足够具体的 prompt 口径。

至少要整理成下面这张表，再去写 prompt：

| 指标 / 维度 | 在评什么 | 主要证据 | 高分信号 | 低分信号 | 不可评条件 | prompt 口径片段 | 是否必须 few-shot | few-shot / 正反例摘要 |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

要求：

- 不要只给指标名和一句模糊解释
- `prompt 口径片段` 至少要能让模型理解该指标和其他指标的区别
- 对复杂、高风险、边界模糊、容易混淆、容易被结果倒推污染的指标，`是否必须 few-shot` 必须填 `是`
- few-shot 不一定很长，但至少要有 1 到 2 个正例 / 反例或边界案例摘要
- 推荐继续补一层：为每个指标标清“主要证据 block / 关键字段集合”，不要让所有指标默认共享整份 payload 做整体印象分析
- 如果多个指标依赖完全相同的核心证据，却没有明显不同的评判口径，通常说明指标拆分或 payload 设计还需要回炉

## 五、失败降级契约

### judge 输出解析失败

推荐顺序：

1. 尝试修正常见 JSON 结构问题
2. 若仍失败，记录原始输出
3. 标记该条样本为解析失败
4. 不要伪造正常分数

### 字段缺失

推荐顺序：

1. 用 spec 中约定的 fallback 补齐
2. 若无法补齐，记录“该维度不可评”
3. 不要默认用 0 冒充真实分

在进入这一步前，最好先分清：

- 是稳定缺失
- 还是数据延迟导致的暂时缺失
- 是 payload 字段没取到
- 还是 label 依赖的 flags 推导错误

### score 回写失败

推荐顺序：

1. 记录待回写结果
2. 落本地结果文件
3. 允许后续重试回写

## 六、先写哪些 failing tests

推荐第一批测试顺序：

1. payload 提取测试
2. label 推导测试
3. trajectory / E2E 聚合测试
4. judge 输出解析测试
5. score 输出格式测试

## 七、Fixture 建议

第一版至少准备三类 fixture：

| 类型 | 作用 |
|---|---|
| 正常成功样本 | 验证主链路 |
| 缺字段样本 | 验证 fallback |
| 特殊标签样本 | 验证 reject / transfer / no_final_answer 等边界 |

如果是 RAG，再加：

- 一个高质量检索样本
- 一个检索内容明显不足的样本

## 八、完成实现前应满足的契约检查

- fixture 结构稳定
- payload schema 稳定
- judge 输出 schema 稳定
- fallback 规则写入 spec
- score metadata 字段写入 spec
