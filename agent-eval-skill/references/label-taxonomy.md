# 标签体系设计

标签要先于评分设计。标签负责说明“这个 trace 处于什么特殊状态”，而不是模糊地代替分数。

## 基本规则

标签回答的问题应该是：

“这条 trace 发生了什么特殊情况，以至于会影响我们如何解释它？”

不要把标签当成“分数低所以贴个标签”。

## 推荐区分

- **Flags**：从 trace 中直接推导出的底层布尔信号
- **Labels**：基于 flags 总结出的、对人更友好的类别

例如：

- flag: `user_rejected_tool = true`
- label: `tool_rejected_by_user`

## 常见标签

这些标签是默认参考集合，不是唯一答案。

使用时可以走两步：

1. 先从这里挑一批已经比较通用、容易理解的候选标签
2. 再结合当前 agent 特性头脑风暴是否还需要补充新的候选标签

如果要补新标签，建议优先从这些方向想：

- 当前 agent 是否会出现特殊成功路径
- 当前 agent 是否会出现容易误判的失败路径
- 当前 agent 是否有独特的交互机制、风险动作或路由行为
- 当前 agent 是否有某些业务上必须单独观察的状态

但要注意：不是想到什么都加。新增标签前，必须先解释它在区分什么边界、为什么不能被已有标签覆盖。

### `normal`

没有特殊处理逻辑时使用。

### `invalid_user_query`

用户问题本身过空、无意义，或者不具备可评测性时使用。

不要因为 query 很短就机械打这个标签。如果 runtime context 很丰富，短 query 一样可以评。

### `no_final_answer`

当前评测范围内没有稳定最终结果时使用。

以下情况不要直接打这个标签：

- 合法 transfer 后当前 agent 结束，但这是设计内行为
- 某个 tool 结果在设计上就是最终结果

### `execution_error`

工具、工作流节点或系统路径发生错误，并且这个错误实质影响了结果时使用。

如果只是中间重试但最终恢复了，不一定需要这个标签。

### `tool_rejected_by_user`

用户明确拒绝、取消或不授权某个工具动作时使用。

边界说明：

- 它描述的是“用户批准状态”
- 它不等于“工具自己执行失败”
- 它通常仍允许 trajectory 继续评

### `user_aborted`

用户主动结束会话，或者 trace 以不完整状态结束时使用。

不要把它和 `tool_rejected_by_user` 混成一个标签。工具被拒绝后仍可能有合理 fallback。

### `transferred_to_subagent`

当前 agent 有意把执行转交给子 agent 或子流程时使用。

边界说明：

- 这个标签本身不必然意味着失败
- 关键是后面如何定义当前评测范围是否结束

### `knowledge_retrieval_used`

检索在回答中起了实质作用时使用。

不要因为代码里有 retrieval 工具就打这个标签。

### `human_approval_required`

可选标签。适合把“人类确认”本身视为重要产品机制的场景。

## 边界表

| 标签 | 什么时候打 | 什么时候不要打 |
|---|---|---|
| `no_final_answer` | 当前范围内没有稳定最终结果 | 合法 transfer 或有合理替代最终产物 |
| `execution_error` | 运行错误影响结果 | 中间错误已完全恢复 |
| `tool_rejected_by_user` | 用户拒绝了提议动作 | 工具自己失败 |
| `user_aborted` | 用户主动终止或会话中断 | 用户拒绝工具但仍给出有效 fallback |
| `transferred_to_subagent` | 明确发生了子流程转交 | 内部 helper 调用不改变评测范围 |
| `knowledge_retrieval_used` | 检索内容实质影响回答 | 只是存在 retrieval 能力但未实际使用 |

## 重叠规则

建议默认规则：

1. `invalid_user_query` 往往直接抑制多数评分。
2. `tool_rejected_by_user` 可以和 `normal` 或 `knowledge_retrieval_used` 共存。
3. 已知是用户主动终止时，`user_aborted` 比 `no_final_answer` 更强。
4. `transferred_to_subagent` 可以和 `knowledge_retrieval_used` 共存。
5. `execution_error` 可以和其他标签共存，但不应该掩盖主标签。

## 必须和用户确认的问题

- 这轮推荐给用户的标签候选集合里，哪些接受、哪些删除、哪些新增？
- 这轮是否需要对某些特殊情况做额外标签区分？
- 哪些标签可以合并，哪些必须单独保留？
- 标签是否允许多选？
- 哪些标签会抑制 E2E 评分？
- 哪些标签仍允许 trajectory 评分？
- transfer 是成功路径的一部分，还是一种特殊异常路径？
- 用户拒绝行为在业务上应被视为失败、中性状态，还是独立情形？

在这些问题没有得到用户明确答复前，标签只能算候选集合，不应进入开发计划。

## 最低产出要求

标签设计不能只停留在口头讨论，必须落成一张完整的标签表。
