# Trace 数据抽取与 Payload / Label 校验

这份文档解决两个常见问题：

1. payload 设计看起来合理，但真正构建时字段拿错、拿空、拿晚、拿混
2. 标签规则看起来合理，但因为原始 trace 数据不稳定，最后误判

这份文档不是某个具体 agent 的业务文档。

更准确地说，它是从已有 Langfuse / DB 路径实践里抽出来的一套通用方法，重点是：

- 怎么从 trace 数据稳定拿字段
- 怎么把原始数据先归一化成可判断的 signals / flags
- 怎么让 payload 和 label 都建立在稳定层上

## 一、核心原则

不要直接从“原始 trace 原文”一步跳到：

- 最终 payload
- 最终 labels

更稳的流程应该是：

1. 加载原始 trace 与 observations
2. 做排序、去噪、分轮次、主次来源识别
3. 提取归一化字段
4. 生成 flags / signals
5. 再由 flags 生成 labels
6. 再由归一化字段和 labels 生成 payload

推荐的分层：

```text
raw trace / observations
-> normalized fields
-> flags / signals
-> labels
-> trajectory payload / e2e payload
```

这里默认还要补一条边界：

- `flags / signals` 和 `labels` 是评测编排层的重要输入
- 但它们默认不应直接进入 judge payload
- judge payload 更应该基于原始证据和归一化事实，而不是系统已经推导好的结论

这样出问题时，才能判断到底是：

- 数据没拿到
- 数据拿错了
- fallback 选错了
- flags 推错了
- labels 映射错了
- payload 组装错了

## 二、数据来源优先级

如果当前以 Langfuse 为优先路径，建议默认顺序是：

1. Langfuse DB
2. Langfuse SDK / API
3. 导出的 trace 文件

但不要把这个顺序理解为“所有路径字段完整度一样”。

必须默认接受这个现实：

- DB 路径通常细节最多，但可能有落库延迟
- SDK / API 路径更稳定，但 observation 细节可能不全
- 导出文件最容易开始，但字段和结构最不稳定

所以每个高价值字段都要明确：

- 主来源是什么
- 备用来源是什么
- 缺失时是否允许降级
- 是否需要运行时日志再次验证可得性

这里还要特别强调一点：

- 查 Langfuse 文档、表结构、DAO、SQL 或 SDK 调用，只能帮助判断“理论上应该去哪拿”
- 不能证明当前实现“已经把正确的值拿进 payload 了”

所以不要把“看过文档”当成“字段已验证”的替代品。

## 三、关键字段不要只信一个来源

每个高价值字段都建议维护一条最小来源链：

| 字段 | 主来源 | 备用来源 | 缺失时处理 |
|---|---|---|---|
| `user_input` | 当前轮 user message | trace 根输入 | 标记来源并记录为空 / 缺失 |
| `final_answer` | 最终 assistant 消息 | trace 根输出 / 明确 fallback 出口 | 主要供 E2E 使用；若仍缺失，触发 `no_final_output` 类 flags |
| `tool_calls` | 当前轮消息中的 tool call | observation 归一化结果 | 若不稳定，先缩成步骤摘要 |
| `tool_results` | observation 输出 | 结构化摘要字段 | 若超长，只保留关键结果摘要 |
| `runtime_context` | trace metadata / state | 运行时可恢复字段 | 缺失则省略并记录风险 |
| `prompt_context` | prompt store / 固定配置 | 运行时解析出的约束摘要 | 缺失则不要假装存在 |

关键点：

- 不要把 fallback 当成“偷偷补一个差不多的值”
- fallback 也是正式契约的一部分
- 如果来源切换了，最好能在日志里看出来
- `final_answer` 虽然是高价值字段，但默认属于 E2E；trajectory 如果真要补充收尾信息，更适合放 `runtime_context` 的 session 级摘要，而不是再单独放结果字段

## 四、Payload 和 Label 不要直接依赖原始层

最容易出问题的反模式是：

- 直接从某条 observation 文本打 label
- 直接从某个 message 片段拼 payload
- 直接假设“这个字段肯定一直存在”

更稳的做法是：

### 第一步：先做 normalized fields

例如先稳定产出：

- `user_input`
- `final_answer`
- `runtime_context.session_outcome_summary`
- `steps`
- `execution_error_summary`
- `runtime_context`
- `prompt_context`

### 第二步：再做 flags / signals

例如：

- `no_final_output`
- `user_rejected_tool`
- `transferred`
- `invalid_user_query`
- `trajectory_evaluable`

### 第三步：再由 flags 生成 labels

例如：

- `no_final_answer`
- `tool_rejected_by_user`
- `knowledge_retrieval_used`
- `transfer_happened`

建议把规则写成：

```text
raw evidence -> normalized flag -> case label
```

而不是：

```text
raw evidence -> case label
```

因为后者一旦数据源变化，label 规则会整体失稳。

## 五、Label 规则要有“证据来源”和“不可判条件”

每个 label 至少回答四件事：

1. 它在描述什么情况
2. 它依赖哪些 flags / signals
3. 这些 flags / signals 来自哪些原始证据
4. 什么情况下不能判，必须留空或降级

推荐写成这种表：

| Label | 依赖 flags | 原始证据来源 | 不可判条件 |
|---|---|---|---|
| `no_final_answer` | `no_final_output=true` | final answer 提取链 | 最终输出字段尚未稳定落库 |
| `tool_rejected_by_user` | `user_rejected_tool=true` | tool reject 事件 / message | reject 事件无法稳定识别 |
| `invalid_user_query` | `invalid_user_query=true` | user_input + runtime context | 用户输入本身缺失 |

这样后面用户反馈“标签打错了”时，才知道先查哪层。

## 六、必须做 Presence Logging

理论上“能拿到”的字段，不代表运行时“真的拿到了”。

所以建议在 payload 构建和 label 推导阶段都加轻量日志。

不要打印全文，至少打印：

- `present`
- `empty`
- `missing`
- 长度
- 条数
- 来源

推荐记录的对象：

- `user_input`
- `final_answer`
- `steps`
- `prompt_context`
- `runtime_context`
- 关键 flags
- 最终 labels

推荐日志示例：

```text
trace_id=...
field=user_input
status=present
source=current_message
length=128
```

```text
trace_id=...
flag=no_final_output
value=true
evidence_source=trace_output_fallback
```

Presence logging 的作用不是调试所有细节，而是回答：

- 字段到底有没有拿到
- 是空值，还是完全缺失
- 当前到底走了哪个来源

## 七点五、正式 judge 前优先做 Payload Inspect / Preview

如果当前最大的风险是“payload 里拿到的不是预想字段”，推荐在正式 judge 前优先支持：

- 单条 trace 的 payload inspect / preview
- 单条 trace 的 flags / labels 证据链 inspect

最少要能看到：

- 当前 trace_id
- 关键字段最终用了哪个来源
- 字段状态是 `present / empty / missing`
- fallback 是否触发
- 关键 flags 的值和证据来源
- 最终 labels 是怎么从 flags 推出来的

推荐流程：

```text
single trace
-> payload inspect / preview
-> 人工核对关键字段
-> flags / labels inspect
-> 再决定是否进入正式 judge
```

如果没有这一步，就不要把“payload 已正确落地”当成已被证明的事实。

inspect / preview 时也建议明确区分：

- 哪些内容会进入 judge payload
- 哪些内容只留在编排层，不进入 judge

如果发现 `case_labels` 或明显带结论性的 `flags` 已经进入 judge payload，应优先视为输入污染风险。

## 七点六、如果本地 DB 查不了，怎么继续

如果 agent 本地环境查不了 DB，不代表整套体系必须停住。

但不能默认略过，必须先让用户显式选择：

1. `手动改配置并去数据库验证关键字段`
2. `先接受风险延后验证，再继续搭建体系`
3. `改走 SDK / API / 导出文件，做 reduced-scope`

如果用户选择 `1`：

- agent 应该给出手动验证指令类型
- 明确重点查哪些关键字段
- 明确需要带回哪些截图、结果或日志

如果用户选择 `2`：

- 必须标记为“带风险继续”
- 必须先有 payload inspect / preview 或等价日志方案
- 必须约定回头验证的触发条件

如果用户选择 `3`：

- 立即把字段完整度预期降到 reduced-scope
- 不再把 DB 细粒度 observation 当成默认前提

## 七、要考虑“数据延迟”而不只是“字段缺失”

如果当前走的是 Langfuse DB 或其他异步落库路径，要额外小心：

- 某些 trace 不是没有数据
- 而是数据还没完全落下来

这类问题常见现象是：

- 刚跑完时 `final_answer` 为空
- 过一会儿又能拿到了
- 某些 observations 第一次查询不存在，重试后出现

所以要先区分：

1. 稳定缺失
2. 延迟缺失

如果怀疑是延迟缺失，建议明确：

- 最大重试次数
- 退避时间
- 最大等待窗口
- 超时后是报错、跳过，还是 reduced-scope

不要把所有“拿不到字段”都直接归因成 schema 设计错了。

## 八、Payload 组装前先做字段映射表

在真正实现 payload 前，建议先做一张表：

| 字段 | 用于 payload 还是 label | 主来源 | fallback | 运行时验证 | 风险 |
|---|---|---|---|---|---|
| `user_input` | payload + label | 当前轮消息 | trace input | 要 | 当前轮切分错误 |
| `final_answer` | payload + flags | 最终 assistant | trace output | 要 | 落库延迟 |
| `steps` | trajectory payload | message + observation | 摘要版 steps | 要 | observation 不全 |
| `execution_error_summary` | payload | error observations | state summary | 要 | 错误事件被吞 |
| `user_rejected_tool` | label | reject signal | 无 | 要 | 误把普通中断当 reject |

没有这张表时，最容易出现两种坏结果：

- payload 设计很好看，但实现时字段来源乱掉
- label 规则很好看，但落地后全靠猜

如果当前用户已经明确表示“不想现在查库”，这张表和 inspect / preview 就更重要，因为它们会变成后续回头排障时的第一手依据。

## 九、常见故障应该怎么排

### 1. judge `reason` 像在说别的样本

优先查：

- payload 字段来源是否混了历史轮次
- 当前轮切分是否错了
- fallback 是否取到了错误出口

### 2. `trajectory` 评分明显被最终结果绑架

优先查：

- trajectory payload 是否暴露了过多最终结果
- 过程 steps 是否太弱，只剩 final answer
- trajectory / E2E payload 是否实际上用了同一套核心内容

### 3. label 经常误打

优先查：

- raw trace -> flags 这层
- 不要先改 label 名字
- 不要先改 judge prompt

### 4. 同一条 trace 有时可评、有时不可评

优先查：

- 数据延迟
- 查询时间窗口
- DB / API 路径差异
- presence logging 是否显示来源变化

### 5. 某字段理论上可取，但线上总缺

优先查：

- 是否只是代码里“以为能取到”
- 是否只在某条平台路径可取
- 是否被压缩 / 截断前就为空

如果当前之前选择的是“带风险继续”，这里应优先回到：

- payload inspect / preview 输出
- presence logging
- 是否已经到了约定的回头验证触发条件

## 十、Langfuse 路径下可以参考什么经验

如果当前用户走的是 Langfuse-first 路径，可以优先借鉴这些经验：

- trace 与 observation 分开加载，不要只信 trace 根对象
- observation 先按时间排序，再做消息快照提取
- `user_input`、`final_answer` 这类高价值字段要有 fallback 链
- label 不要直接从原始 observation 打，先做 flags
- 对关键字段和关键 flags 都做 presence logging
- 对 DB 路径要讨论延迟和重试窗口

但要注意：

- 这些经验是“参考实现模式”
- 不是说其他平台必须长成 Langfuse 这样

如果不是 Langfuse，也依然可以沿用同样的方法论：

- 原始数据 -> 归一化字段 -> flags -> labels -> payload

## 十一、什么时候该补这份文档

出现下面任一情况时，建议主动阅读这份文档：

- payload 已经选完，但字段来源还不稳定
- label 边界已经定了，但证据来源还不稳定
- 用户担心“代码里拿到的不是设计时想要的那个字段”
- 当前平台可能存在 DB 延迟或 observation 不完整
- 用户反馈“分数不对”，但暂时分不清是 payload 问题还是 label 问题

## 十二、默认建议

默认优先做法：

1. 先把高价值字段的来源链写清楚
2. 先准备单条 trace 的 payload inspect / preview
3. 再把关键 flags 的推导链写清楚
4. 再设计 labels
5. 再组装 trajectory / E2E payload
6. 实现时加 presence logging
7. 首轮验证时优先看字段可得性和 flag 正确性

如果这些事情还没做完，就不要急着把“payload 已设计完成”或“label 已设计完成”当成真。
