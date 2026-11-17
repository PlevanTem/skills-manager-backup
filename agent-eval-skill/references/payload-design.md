# Payload 设计方法

payload 必须从 agent 实际会产生的数据反推出来，而不是先想一个理想 schema。

如果当前重点问题是“字段到底能不能稳定拿到”“payload 字段会不会拿错来源”“label 是否会因为原始 trace 数据不稳定而误判”，请配合阅读：

- [trace-data-extraction.md](trace-data-extraction.md)

## 核心原则

每个 payload 字段都要回答三个问题：

1. judge 为什么需要它？
2. 它从哪里来？
3. 如果拿不到它，怎么办？

同时还要补两个问题：

4. 它对当前主指标到底有多重要？
5. 它会占用多少上下文预算，超长时怎么处理？

## 字段进入 payload 的优先级判断

不要把“能拿到的字段”几乎全部塞进 payload。

建议先分三层：

| 等级 | 含义 | 典型例子 |
|---|---|---|
| 高价值字段 | 直接支撑主指标，没有它就很难评 | 当前轮用户输入、最终回答、关键 tool step、关键错误信号 |
| 辅助解释字段 | 主要用于解释分数或帮助 judge 理解上下文 | runtime metadata、tool result 摘要、prompt 约束摘要 |
| 条件性字段 | 只在某些标签、agent 类型或专项指标下需要 | retrieval 证据、transfer handoff、人工确认记录 |

推荐顺序：

1. 先保住高价值字段
2. 再根据指标和标签决定辅助解释字段
3. 最后才考虑条件性字段

如果某字段只是“可能有帮助”，但占用大量上下文，就默认不要直接保留原文。

## 默认拆分方式

一般默认拆成两类 payload：

- **Trajectory payload**：评估过程质量
- **E2E payload**：评估最终回答质量

只有在 agent 很简单、过程基本不重要时，才考虑合并。

这不仅是“建议拆两类”，还应视为一条默认硬约束：

- `trajectory payload` 和 `E2E payload` 必须是两套用途明确不同的评判载荷
- 如果两套 payload 的核心评判区块基本相同，只是字段名略有变化，应视为设计失败，需要重新拆分
- 允许存在共享上下文，但共享上下文不应吞掉两边各自的核心评判内容

更推荐的分层是：

1. `shared context`
2. `trajectory-only payload`
3. `e2e-only payload`

其中：

- `shared context` 适合放 trace metadata、少量历史摘要，以及评测编排层自己使用的控制信号
- `trajectory-only payload` 必须围绕 steps、routing、tool choice、params、process signals
- `e2e-only payload` 必须围绕 final output、result quality、result evidence、result errors

这里要特别注意：

- `case_labels` 默认不进入 judge payload
- `flags` 也不应默认进入 judge payload
- 它们更适合作为评测编排层、路由层、skip / gating、结果解释和报告输出使用

只有在极少数场景下，用户明确确认“原始证据不足，且某个中性控制信号确实必须暴露给 judge”时，才考虑例外。

## Trajectory Payload

适用于以下场景：

- tool 选择很重要
- 参数构造很重要
- 中间步骤很多
- transfer、retry、reject 会影响判断

推荐包含这些区块：

- trace metadata
- evaluation scope
- history context
- 当前轮输入
- runtime context
- prompt context
- 归一化后的 trajectory steps

设计时要想清楚：

- 当前轮从哪条消息开始算
- 哪些 tool call / tool result 属于当前轮
- judge 需要看到哪些 runtime 信息
- 哪些 prompt 或 routing 规则必须暴露给 judge
- 哪些步骤用摘要即可，哪些必须保留原文
- 哪些 step 是 trajectory 主分必需，哪些只是解释噪音
- 如果必须让 trajectory judge 知道是否正常结束，是否只放 session 级的 runtime context 摘要，而不是单独的结果字段
- 哪些 labels / flags 只留在评测编排层，不进入 judge payload
- trajectory 的核心区块是否真的和 E2E 明显分开，而不是共用一套同构结构

## Trajectory 是否需要看到最终结果

一般建议：不需要单独放一个结果字段。

原因：

- trajectory 评的是过程质量，不应让最终结果主导评分
- 如果直接暴露完整 final answer，judge 很容易发生结果倒推过程的偏差
- 如果单独再放一个结果摘要字段，也很容易让 judge 过早把注意力放到结果好坏
- 真要补充收尾信息，更适合放进 `runtime_context` 的 session 级摘要里，而不是放成 trajectory 的独立结果区块

更推荐给 trajectory judge 的是：

- `runtime_context.session_status`
- `runtime_context.session_outcome_summary`
- `runtime_context.session_end_reason`

而不是：

- 默认直接给完整 `final_answer`
- 在 `current_trace` 或其他专门区块里再单独放结果字段

只有在下面这些情况，才建议让 trajectory 明确参考最终结果：

- 要判断是否正常收尾
- 要判断失败恢复后是否真的解决
- 需要区分“过程大体合理但最后输出缺失”这类边界

即使在这些场景里，也更建议只给 session 级 runtime context 摘要，而不是单独结果字段或全文。

## E2E Payload

适用于：

- 最终回答质量本身是重点
- 想把“过程”和“结果”拆开评

推荐包含：

- trace metadata
- question context
- output.final_answer
- runtime context
- prompt context
- execution context

execution context 一般放：

- tool result 摘要
- retrieval context 摘要
- 会实质影响结果判断的错误或 fallback 摘要

如果 execution context 很长，优先保留：

- 最后影响回答的关键证据
- 直接解释失败或降级的关键信号
- 会改变标签判定的特殊事件

这些“特殊事件”默认应以原始证据或归一化事实进入 execution context，而不是直接把 `case_labels` / `flags` 当成结论喂给 judge。

## 什么叫“分开得不够”

下面这些情况通常说明 trajectory 和 E2E payload 还没有真正拆开：

- 两边都默认带完整 `final_answer`
- 两边都以同样的 `execution_context` 为主，只是 task 名不同
- trajectory 没有独立的 steps / routing / tool / param 信号
- E2E 没有独立的 output / result evidence，只是复用过程摘要

如果出现这些情况，应该回到 payload 设计阶段重新拆，而不是硬着头皮进入实现。

## 字段来源映射

建议给每个 payload 先做一张字段表：

| Payload 字段 | 来源 | 是否必须 | 拿不到时怎么办 |
|---|---|---|---|
| `trace_meta.trace_id` | trace 根对象 | 必须 | 无 |
| `current_trace.user_input` | 当前轮 user message | 必须 | trace input fallback |
| `current_trace.final_answer` | 最终 assistant 内容 | 通常必须 | 选择有依据的替代出口 |
| `runtime_context.*` | metadata / state / 代码恢复 | 可选 | 缺失则省略并说明 |
| `prompt_context.*` | prompt store / 嵌入 prompt / prompt 名 | 条件性需要 | 缺失则省略并说明 |
| `trajectory.steps` | message + observation 归一化 | trajectory 必需 | 缩减版摘要 |

这里最容易踩坑的不是“表格没写”，而是实现时没有真的按来源链去拿字段。

建议额外确认：

- 是否先做了 normalized fields，再做 payload
- 是否给高价值字段写了 fallback 链
- 是否给关键字段加了 presence logging

## Payload 对齐环节

在继续写 spec、checklist 或开发计划前，必须先把 payload 按 block 对齐。

建议至少整理成这张表：

| Payload block | 所含字段 | 每字段用途 | 数据来源 | 获取状态 | fallback |
|---|---|---|---|---|---|
| `trajectory.trace_meta` |  |  |  | 可取 / 假设 / blocked |  |
| `trajectory.runtime_context` |  |  |  | 可取 / 假设 / blocked |  |
| `e2e.output` |  |  |  | 可取 / 假设 / blocked |  |

要求：

- 先按 trajectory / E2E 分块
- 每个 block 都标清字段来源
- 每个 block 都标清获取状态
- 缺失项必须写 fallback

这张表展示给用户前，payload 只能算草案。

## 按指标组织证据视角

除了区分 trajectory / E2E，还建议继续区分“每个评分指标主要看什么证据”。

推荐优先采用下面这种思路：

- 不要让所有指标默认共享整份 payload，然后让 judge 通读全文做整体印象分
- 每个指标至少要有自己的主要证据 block、关键字段集合，或明确的重点证据顺序
- 允许多个指标共享一小部分上下文，但不建议共享完全相同的核心证据视角
- 少数强耦合维度可以共享更多上下文，但仍建议把各自主要证据和评分口径显式拆开

例如：

- `parameter_construction` 主要看参数、query、transfer payload、上下文吸收情况
- `tool_selection` 主要看动作类型、调用时机、是否遗漏关键动作
- `groundedness` 主要看回答主张和可见证据之间是否能回链

如果一个 judge 设计成“所有指标都看同一大段 execution context + 同一整份 output”，虽然表面上字段齐全，但很容易出现：

- 不同指标分数一起升降
- judge reason 总在重复同一组事实
- 某个指标名虽然不同，实际仍在评整体好坏

出现这些现象时，优先回到 payload / rubric 设计阶段，继续拆清各指标的主证据视角，而不是先去调模型温度或 prompt 语气。

用户至少需要明确表达下面其中一种态度：

- 同意
- 不同意
- 要改哪些 block / 字段
- 接受哪些字段缺失及 fallback

在用户未确认前，不得进入开发计划。

## Prompt Context 何时必须进 payload

下列情况建议进入 payload：

- prompt 明确限制了工具边界
- prompt 明确限制了回答格式
- prompt 明确要求知识型回答必须基于召回内容
- prompt 限定了角色或场景边界

如果 prompt 只是通用口吻或品牌语气，一般不必放。

## 长上下文压缩原则

默认不要假设 judge 能吃下原始长上下文。

每个字段都要选一种压缩策略：

- 保留原文
- 只截前部
- 前后截断
- 确定性摘要
- 模型摘要

推荐顺序：

1. 优先复用 agent 自己已经整理过的结构化结果
2. 其次用确定性的 head-tail 压缩
3. 最后才是模型摘要

## 上下文预算与降级策略

除了“怎么压缩”，还要先想清楚“预算怎么分”。

建议至少做一张预算表：

| 区块 / 字段 | 价值等级 | 预算建议 | 超预算时先做什么 | 仍超预算时怎么办 |
|---|---|---|---|---|
| `current_trace.user_input` | 高 | 尽量保留原文 | head-tail trim | 必要时切兜底模型 |
| `trajectory.steps` | 高 | 保留关键 steps | 先归一化再摘要 | 用户确认后跳过超长样本 |
| `prompt_context` | 中 | 只保留关键约束 | 提取约束摘要 | 省略原文并说明 |
| `runtime_context` | 中 / 低 | 只保留会影响评判的字段 | 结构化压缩 | 省略并记录风险 |

默认顺序：

1. 先裁剪或摘要
2. 如果仍然超预算，再切到大上下文兜底模型
3. 如果没有兜底模型或成本不可接受，再由用户决定是否跳过样本

其中后两步都不能由 agent 自己决定，必须先和用户确认。

## 语义风险提示

压缩不只是长度问题，还会带来语义风险。

至少要标清：

- 哪些字段压缩后会影响 trajectory 判断
- 哪些字段压缩后会影响 groundedness / correctness
- 哪些字段压缩后只影响解释性，不影响主分
- 哪些字段一旦被截断就不适合继续评

每个被压缩字段都要写清楚：

- 原始来源
- 压缩方法
- 长度限制
- 是否有语义丢失风险
- 超预算后的下一步动作

## 建议的长字段策略

| 字段类型 | 默认策略 |
|---|---|
| 用户环境信息 | head-tail trim |
| 当前标签页 / 代码上下文 | head-tail trim |
| tool 输出 | 先按工具做摘要，再 trim |
| 检索文档 | 文档摘要 + 来源信息 |
| prompt 文本 | 短则保留，长则只保留关键约束段 |

## 特殊情况

### RAG

如果 agent 涉及检索：

- 检索证据和最终回答要分开存
- 要能看出“检索到了什么”和“最终回答如何使用”
- 可以给 E2E 增加 retrieval 相关维度

### Transfer

如果 agent 会转交：

- 明确 transfer 是不是一个 trajectory step
- 明确子流程是黑盒还是继续展开
- capture transfer input 或 handoff 摘要

### 用户拒绝 / 未授权

如果 agent 会先提议工具再等用户确认：

- trajectory 里应尽量保留“被提议的动作”本身
- 同时记录 reject / unauthorized 标签
- 如被拒后有 fallback，也应进入 payload

## 设计完成后的最低产出

payload 设计结束后，至少要交付：

- 一张字段来源表
- 一张 payload block 对齐表
- 一套压缩策略
- 一张字段价值 / 预算表
- 一份缺字段说明
- trajectory payload 草案
- E2E payload 草案

只有在这些内容被用户确认或编辑后，才允许继续做实现计划。
