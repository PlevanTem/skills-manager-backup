# 输出策略

payload 和标签稳定后，再决定结果最终往哪里输出。

> 说明：这份文档是 E2E 与 trajectory 聚合、score 落地方式的主规则来源。`langfuse-e2e-metrics.md` 和 `trajectory-metrics.md` 中如有聚合建议，应以这里为准，再叠加各自场景的补充说明。

## 默认优先级

1. **平台内 score 回写**
2. **平台内 evaluator / judge prompt 方案**
3. **数据库或报告产物**
4. **仅输出设计文档**

## 策略表

| 策略 | 适用场景 | 主要产物 |
|---|---|---|
| 平台内 score 回写 | 团队已经在现有平台看 trace，希望分数直接挂在 trace 上 | score 名、metadata 结构、回写方案 |
| 平台内 evaluator 指导 | 团队更希望 judge 逻辑留在现有平台体系内 | evaluator prompt / judge prompt 设计 |
| 报告或数据库输出 | 需要给平台外部系统消费 | 表结构、报告格式、导出方案 |
| 仅设计文档 | 当前还没准备好实现，或 trace 条件不够 | spec、payload、labels、下一步建议 |

## 平台内 Score 回写

适合以下情况：

- trace ID 稳定
- 团队本来就在现有平台里 review trace
- 希望能长期累积分数历史

需要明确：

- score 名怎么命名
- 数值型还是分类值
- metadata 里存哪些内容
- score 版本如何区分
- trajectory 和 E2E 是否拆成两类分数

推荐默认做法：

- 每个大维度一条 numeric score
- case labels 单独作为 categorical 或 string score
- metadata 带上 evaluator model、rubric version、分项 breakdown

如果 trajectory 已经拆成多个维度，常见有三种落地方式：

| 方式 | 适用场景 | 建议 |
|---|---|---|
| 只写 `trajectory_score` | 只想看总览趋势 | 第一版最轻，但归因能力弱 |
| 写 `trajectory_score` + metadata breakdown | 想兼顾总览和归因 | 默认最推荐 |
| 每个维度单独写一个 score | 需要按维度长期分析趋势 | 适合成熟阶段 |

trajectory 常见维度可以参考：

- 逻辑连贯性
- 任务推进与收敛
- 效率
- 上下文利用
- 路由与约束遵守
- 工具选择
- 参数构造

详细说明继续参考：

- [trajectory 多维度指标参考](trajectory-metrics.md)

如果当前平台里已经存在现成的 E2E 指标或 evaluator 模板，建议先做一张映射表：

| 平台现成指标 | 语义 | 当前 agent 是否适用 | 是否直接复用 | 是否需要自定义补充 |
|---|---|---|---|---|
|  |  |  |  |  |

优先原则：

- 语义稳定、已经被团队接受的指标优先直接复用
- 只有在业务语义不一致或覆盖不到时，才新增自定义分项
- 不要为同一含义同时维护两套名字不同但本质相同的 E2E 分数

常见可复用的 E2E 指标方向包括：

- `Answer Correctness`
- `Answer Relevance`
- `Faithfulness`
- `Goal Accuracy`
- `Helpfulness`
- `Conciseness`
- `Toxicity`

如果当前 agent 是 RAG 型，也可以额外讨论：

- context precision
- context recall
- context relevance
- context correctness

具体指标名可以和用户当前平台页面上的实际名称对齐，不要求机械照抄这一份列表。

## E2E 聚合方式

当 E2E 分项确定后，要和用户讨论最终怎么聚合：

### 保留分项，不聚合

适合：

- 研发调试期
- 维度之间重要性差异很大
- 当前主要目标是归因，而不是做一个总分

优点：

- 最利于排查问题
- 不会把不同维度的缺陷平均掉

### 简单平均

适合：

- 只是想快速得到一个总体趋势分
- 各维度重要性接近
- 第一版先追求实现简单

注意：

- 简单平均隐含“各维度同权”
- 如果正确性和毒性等重要性差异很大，这种做法容易失真

### 加权平均

适合：

- 业务上明确知道哪些维度更重要
- 团队愿意维护权重版本

建议：

- 权重必须写进 spec 和 metadata
- 不要只存综合分，仍然保留各维度原始分数

### 推荐默认方案

默认建议：

1. 先保留各维度独立分数
2. 如确有展示需要，再额外提供一个综合分
3. 第一版一般优先“分项 + 简单平均”
4. 当业务已经稳定，再升级到“分项 + 加权平均”

综合分不应该替代分项分数，它只适合做总览，不适合做根因分析。

## 平台内 Evaluator / Judge Prompt

适合以下情况：

- 用户希望 judge prompt 也纳入当前平台维护
- 团队能维护 prompt 版本，但还不想单独搭评测服务

需要讨论：

- evaluator payload 放什么
- evaluator prompt 文本存在哪里
- evaluator prompt 和业务 prompt 是否分开版本化
- 是否需要人工抽样校准

## 报告或数据库输出

适合以下情况：

- 结果不仅给研发看，还给其他角色看
- 平台 UI 不够用
- 需要周期性报表或下游分析

可能产物：

- 单条 trace 的评分记录
- markdown 报告
- 汇总表
- 低分样本导出

## 仅设计文档

适合以下情况：

- 用户当前只想要指导
- 可观测性还不够，贸然评分不可信
- 评测实现明确延后

即便如此，也要至少产出：

- readiness 结论
- 指标建议
- payload 草案
- 标签表
- 实现 checklist

## 必须和用户确认的问题

- 分数最终是写回当前平台，写入别的库，还是只出文档？
- 需要按维度拆开看，还是只看总分？
- 当前平台里已有的现成 E2E 指标有哪些可以直接复用？
- 如果要聚合，使用简单平均、加权平均，还是暂时不聚合？
- 用户是否愿意维护 judge prompt 和 score schema？
- 这些结果主要给工程师看，还是也给产品或运营看？
