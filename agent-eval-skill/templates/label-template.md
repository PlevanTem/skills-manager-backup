# 标签定义模板

在实现 judge 之前，先把这张表填完整。

## 标签矩阵摘要

先给用户一张更容易快速理解的矩阵表：

| case | trajectory | e2e | 备注 |
|---|---|---|---|
| `invalid_user_query` | 不执行 | 不执行 |  |
| `user_aborted` |  |  |  |
| `tool_rejected_by_user` |  |  |  |
| `no_final_answer` |  |  |  |
| `execution_error` |  |  |  |
| `knowledge_retrieval_used` |  |  |  |

## 标签表

要求：

- 每个标签都要能回链到 `依赖 flags`
- 每个标签都要能回链到至少一类 `原始证据来源`
- 如果某标签当前不可稳定判断，就不要硬填“纳入 / 排除”，而要明确写进 `不可判条件`

| 标签 | 依赖 flags | 原始证据来源 | 何时纳入 | 何时排除 | 不可判条件 | 是否影响 trajectory | 是否影响 E2E | 重叠规则 |
|---|---|---|---|---|---|---|---|---|
| `normal` |  |  |  |  |  |  |  |  |
| `invalid_user_query` |  |  |  |  |  |  |  |  |
| `no_final_answer` |  |  |  |  |  |  |  |  |
| `execution_error` |  |  |  |  |  |  |  |  |
| `tool_rejected_by_user` |  |  |  |  |  |  |  |  |
| `user_aborted` |  |  |  |  |  |  |  |  |
| `transferred_to_subagent` |  |  |  |  |  |  |  |  |
| `knowledge_retrieval_used` |  |  |  |  |  |  |  |  |

## Flag 表

要求：

- 每个被标签依赖的 flag，都要在这里有定义
- `原始来源`、`fallback 证据` 和 `被哪些标签使用` 三列要能互相对上
- 填完后最好做一次自检：标签表中的 `依赖 flags` 是否都能在这里找到

| Flag | 原始来源 | fallback 证据 | 布尔规则 | presence logging | 被哪些标签使用 |
|---|---|---|---|---|---|
|  |  |  |  | `value + evidence source` |  |

## 不可判 / 冲突处理

| 场景 | 默认处理 | 是否需要用户确认 | 备注 |
|---|---|---|---|
| 原始证据缺失 | 先不打标签 / 标记不可判 | 是 |  |
| 原始证据延迟落库 | 重试后再判 | 是 |  |
| 多个 flags 冲突 | 按优先级规则处理 | 是 |  |
| payload 字段长期 missing | 暂停相关标签 | 是 |  |

## 冲突说明

- 哪些标签会抑制 E2E：
- 哪些标签仍允许 trajectory：
- 哪些标签可以共存：
- 哪些标签同时出现时要有优先级：
- 哪些标签需要先验证 flags，再允许进入 judge：

## 需要和用户确认的问题

- 
