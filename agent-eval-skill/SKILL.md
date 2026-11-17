---
name: agent-eval-skill
description: 用于为 AI agent 设计或搭建评测体系，尤其适合需要从本地代码、现有 tracing / 评测平台或 trace 文件中梳理可评测性、设计 trajectory 和 E2E 指标、定义 payload 与标签、并决定评分输出方式的场景。
---

# Agent 评测 Skill

## 概述

这个 skill 用来把 agent 代码和 trace 数据整理成一套真正可落地的评测设计。

默认定位是“以落地为目标，以多轮对齐为前提”，不是一上来就盲目写评测代码，也不是只给泛泛指导就结束。

默认还要假设用户可能是测评和代码双小白：不熟悉指标、payload、标签，也未必会自己写实现代码。所以每个关键步骤都要尽量解释清楚，再让用户做选择。

## 何时使用

- 用户想做 agent 评测、judge、评分上报、trajectory 评估或 E2E 回答评估。
- 用户手上有本地 agent 代码、上传代码、Langfuse trace、导出 trace 文件，或这些来源的组合。
- 用户还不确定该选哪些指标、标签、payload 字段和输出方式。
- 用户在判断是否接入 Langfuse score、evaluator prompt，或者仅先产出设计文档。

不要把这个 skill 用在纯 BI 看板、产品数据分析，或没有 agent 代码和 trace 结构的通用模型 benchmark 上。

## 默认职责边界

这个 skill 默认是 **前置对齐优先，落地次序后置**：

1. 先把评测项目位置、配置位置、代码落点、数据入口这些前提问清楚。
2. 再先盘点用户原有评测项目里哪些组件、契约和输出形态可以复用。
3. 再判断当前条件是否足以进入完整评测设计，还是只能停在 reduced-scope discovery。
4. 只有关键前提确认后，才和用户一起设计维度、payload、标签、输出路径和实现顺序。
5. 只有设计稳定后，才先进入评测方案文档 / spec，再进入计划和开发。

在前置对齐没有完成前，不要直接跳到 evaluator 代码实现，也不要替用户擅自定好评测方案。

## 硬性规则

- 优先使用本地仓库，不要默认只靠零散代码片段。如果用户在纯聊天环境里操作，可以建议先把 agent 代码放到 IDE 工作区。
- 数据源优先级默认是：**Langfuse DB** > **Langfuse SDK 或 API** > **导出 trace 文件**。
- 进入设计和计划前，必须先确认：评测项目位置、配置位置、代码落点、trace 数据入口、数据库或 SDK 可用性、评测单元、ground truth 策略、输出目标。
- 在设计新评测链路前，必须先读取用户原有评测项目中可复用的组件、配置和契约；不要默认从零新建整套体系。
- 只要某项关键信息不能从用户消息、代码、trace 或明确配置中直接证明，就视为“不确定”；不确定信息必须先问用户，不能由 agent 私自猜测、补全或默认采用。
- 只允许三种信息状态：`已确认`、`待用户确认`、`用户明确接受的临时方案`。不要把 agent 自己的推测写成已确认事实。
- **readiness 结论只用于判断是否继续 discovery，不等于可以开始计划。**
- discovery 阶段允许且鼓励多轮提问；必要时问题数量可以超过 10 个。每一轮只推进 1 到 2 个关键未决项，不要一次把所有问题砸给用户。
- 在上述关键前提未确认前，不得擅自给出指标定稿、标签定稿、payload 定稿或开发计划。
- 指标必须从代码里真实可观测的事实反推，不能在没看 prompt、tool、routing、trace 字段和输出结构前先拍脑袋定义。
- 默认优先使用模型评判（LLM judge / evaluator）来完成评分；不要在没有向用户确认的情况下，直接把规则匹配、关键词匹配、硬编码阈值或 `Simple Criteria` / `Answer Critic` 一类规则判定当成第一优先级。
- 在产出评测 spec、实现计划或开发 checklist 前，必须先向用户简要展示：当前平台内置 / 可复用指标、基于 agent 流程特色与关键风险推荐的 trajectory / E2E 指标集合，并要求用户明确回答“接受 / 删除 / 新增 / 哪些只观察不进总分”。
- 如果后续需要构建 judge prompt / rubric，不能只写一段泛泛的总说明；必须对每个纳入评分的指标或维度分别说明：它在评什么、主要看哪些证据、什么情况高分、什么情况低分或不可评。
- 不能只让模型“参考出几个指标名”就开始打分；每个纳入评分的小指标都必须有足够具体的 prompt 口径或 rubric 片段，让模型能区分这些指标到底在评什么，而不是把不同指标打成一片。
- 对复杂、高风险、边界模糊、容易彼此混淆、容易被结果倒推污染，或用户明确要求高一致性的指标，必须补 1 到 2 个 few-shot 或正反例；不要让模型只靠指标名和一句短说明自行脑补。
- 设计 judge 时，优先按“指标视角”组织证据，而不是把一整份 payload 原样丢给所有指标做整体印象分析。更好的默认做法是：每个指标都有自己的主要证据块或关键字段集合，只共享少量必要上下文。
- 不要把“所有指标共用同一份完整 payload，只靠 rubric 名字区分”当成默认设计；如果多个指标看到的核心证据完全一样、口径又没有明显区分，通常说明指标拆分还不够好，容易出现分数一起高、一起低。
- 这条更适合作为推荐优先采用的默认设计原则，而不是要求每个指标绝对独享字段；少数强耦合维度允许共享较多上下文，但仍要把各自主要证据和评判口径分开写清楚。
- 在产出评测 spec、实现计划或开发 checklist 前，必须先向用户明确说明是否需要对特殊标签做额外区分，并要求用户明确回答“接受 / 删除 / 新增 / 合并哪些标签，以及哪些标签会抑制评分”。
- 在产出评测 spec、实现计划或开发 checklist 前，必须先按 trajectory / E2E 逐块列出 payload，并为每个区块标注字段、来源、可获取性和 fallback；用户未明确确认或编辑前，不得进入计划。
- 在正式 judge、批量评测或评分回写前，优先要求支持“单条 trace 的 payload inspect / preview 模式”；至少要能让用户或 agent 看见关键字段的来源、取值状态、fallback、关键 flags 和 presence logging。没有这一步，不要把 payload 已正确落地当成事实。
- payload 不是字段越多越好；每个字段都要说明它为什么值得进入 judge 上下文，并标清它是在支撑主指标、辅助解释，还是只在特定标签 / agent 类型下需要。
- 当用户明显不熟悉测评概念时，必须用简短自然语言解释：指标是在评什么、payload 是 judge 会看到的输入、标签是在标记特殊情况；解释后再继续让用户做选择。
- 推荐标签时，既可以从当前文档里已有的常见标签出发，也可以根据 agent 特性头脑风暴新的候选标签；但任何新增标签都要先向用户解释用途和边界，再请用户确认是否保留。
- 在推荐指标、payload、标签时，尽量用 1 到 3 句话向用户解释“为什么这么推荐”，不要只给结论。
- 标签推荐尽量使用结构化表格展示；如果需要说明某个 case 是否执行 trajectory / E2E，可直接给出 case 矩阵表。
- 只要内容适合结构化表达，就尽量图文并茂：例如 agent 分类、组件关系、trace 到 score 的链路，都可以补一张简单图；分析 agent 结构时可优先给简图说明其类别和主要分支。
- 必须先讨论特殊标签，再锁定评分逻辑。标签边界不清，后面 trajectory 和 E2E 很容易打架。
- trace 数据不完整时可以继续推进，但 reduced-scope、fallback、临时替代都必须先让用户接受，不能由 agent 单方面决定；同时要给出当前 best-effort 方案，并明确告诉用户下次该补哪些 trace / metadata / 配置。
- 如果 prompt、routing 规则、metadata 会影响评判，就要和用户确认这些内容是否进入 payload。
- 对任何可能很长的 payload 字段，都要提前设计压缩策略、长度预算和超预算处理。默认顺序是：裁剪 / 摘要 -> 大上下文兜底模型 -> 跳过样本；后两者都必须由用户明确接受。
- 如果用户暂时无法提供配置，可以建议短期硬编码或占位方案；但只能在用户明确同意后使用，并且必须标记为 `TEMP` 和后续替换条件。
- 如果本地 DB 查询环境不可用，不能直接默认继续、默认改走别的路径，或默认让用户手动查库。必须显式询问用户在这三种路径里选哪一种：`手动改配置并查库验证关键字段`、`先接受风险延后验证再继续搭建体系`、`改走 SDK/API/导出文件做 reduced-scope`。
- 如果考虑使用规则判定作为门禁、补充项或 fallback，必须先和用户确认：为什么模型评判不适合、规则判定覆盖什么边界、它是主判分还是辅助门禁；未经确认，不得私自把规则判定顶替模型评判。
- 在进入正式 Plan 或实现前，必须先生成一份给用户查看并确认的评测方案文档 / spec；后续 Plan 和实现都要以这份文档为依据，而不是绕过文档直接进入计划。
- 如果真的开始写代码，使用 **REQUIRED SUB-SKILL:** `superpowers:test-driven-development`；如果该 skill 不可用，也必须坚持最小 TDD 流程：先写 payload/label/judge 输出相关 failing tests，再写实现。
- 如果真的开始写代码，还要主动遵守用户当前环境里已有的代码规范，例如用户配置的 rules、相关 skill 约束、语言 / 项目级代码风格和校验要求；不要只满足评测流程本身，而忽略代码规范。

## 主流程

### 第一阶段：前置对齐 / Discovery

这一阶段的目标不是出方案，而是把关键前提问清楚。

#### 第一步：确认评测项目落位

- 优先本地仓库。
- 先问清楚评测项目本身在哪个仓库或目录。
- 再问清楚相关配置在哪：环境变量、judge 配置、trace 接入配置、CI 配置分别放在哪里。
- 再问清楚新的评测代码应该落在哪里：现有评测仓库、agent 仓库内部，还是新建 `eval/` / `evaluation/` 目录。
- 如果用户上传代码，至少要能看清 entrypoint、prompt、tool、trace 上报点和最终输出出口。
- 如果代码不完整，要说明缺了什么，但不要直接停下，先给部分指导。

#### 第二步：确认数据获取路径和接入条件

先阅读 [references/langfuse-readiness.md](references/langfuse-readiness.md)。

默认按这个优先级判断：

| 优先级 | 来源 | 默认动作 |
|---|---|---|
| 1 | Langfuse DB | 围绕 traces、observations、prompt 版本和 score 回写设计整体方案 |
| 2 | Langfuse SDK 或 API | 先确认是否还能恢复出足够的 payload 字段 |
| 3 | 导出 trace 文件 | 把它当成离线重放材料使用，字段不全时缩小范围 |

这一阶段要继续追问：

- 数据是从 DB、API、SDK 还是导出文件获取？
- 数据库配置现在是否可用？
- 如果数据库配置拿不到，用户是否能补到？
- 如果补不到，是否可以改走 SDK / API 路线？
- 如果连 SDK / API 也不可用，是否只能退到 trace 文件或 observability backlog？
- 当前默认 judge 模型是什么？
- 是否配置大上下文兜底模型？
- 模型或 judge 请求的超时阈值是多少？
- 超时后是重试、切兜底模型、降并发，还是直接失败？
- 如果没有兜底模型，用户接受哪种降级策略？

#### 第三步：如果没有现成评测项目，先做最小初始化选型

如果用户没有现成评测项目，不要直接进入指标、payload 或实现计划。

先确认：

- 目标语言 / 运行时
- 框架或最小实现方式（例如 `trpc` 或其他）
- 同仓 / 异仓策略
- 最小 runner 的入口形态
- 配置承载方式

默认原则是尽量用最小实现完成第一版，但“最小”也要先和用户确认，而不是由 agent 自己拍板。

#### 第四步：扫描 agent 代码

先阅读 [references/agent-classification.md](references/agent-classification.md)。

重点识别：

- 入口和请求结构
- prompt 加载方式和 prompt 名
- tool 声明以及 client/server 分工
- interrupt、resume、retry、transfer
- 写入 trace 的 metadata
- 最终回答或最终结果的出口

#### 第五步：盘点原有评测项目的可复用部分

如果用户已经有评测项目，必须继续读取并盘点里面可复用的内容。

至少要检查：

- trace 读取或 sample 抽取组件
- payload builder
- label / flag 推导逻辑
- judge prompt 或 judge 调用封装
- score writer
- report / runner
- fixture / golden trace 结构
- config schema

最好整理成一张复用盘点表：

| 组件 / 契约 | 位置 | 当前作用 | 是否可直接复用 | 需要怎样适配 |
|---|---|---|---|---|
|  |  |  |  |  |

#### 第六步：输出 discovery 中间结论

这一轮结束时，只允许输出：

- 已确认事项清单
- 未确认事项清单
- readiness 中间结论
- 下一轮待问的 1 到 2 个关键问题

这一轮**禁止**输出：

- 未经确认的指标定稿
- 未经确认的标签边界定稿
- 未经确认的 payload 定稿
- 未经前提收齐的开发计划

如果信息仍不完整，应继续多轮 discovery，而不是进入计划。

### 第二阶段：设计与计划

只有在以下前提都确认后，才允许进入这一阶段：

- 评测项目位置
- 配置位置
- 代码落点
- 无现成评测项目时的最小项目选型
- trace 数据入口
- DB / SDK / API 的可用路径
- 默认 judge 模型
- 大上下文兜底模型或明确的替代策略
- 超时阈值与超时后的动作
- 平台关键配置（如 project / space、鉴权方式、agent_name 或等价筛选字段）
- 评测单元
- ground truth 策略
- 输出目标
- 推荐指标集合已被用户接受、编辑或显式保留为观察项
- 标签集合及其边界已被用户接受、编辑或显式合并
- payload 区块及字段可得性已被用户接受，缺失项与 fallback 已明确

如果上述任何一项未确认，继续停留在 discovery。

#### 第七步：识别 agent 特色，并用类型作参考

先识别这个 agent 的关键特色：

- 工具选择是模型自由决定，还是代码固定流程决定
- 哪些中间步骤真的值得单独评分
- 是否依赖 retrieval、rerank 或外部知识
- 是否存在 transfer / subagent / handoff
- 是否有人类审批、reject、resume、authorize
- 最终产物是自然语言、结构化结果、动作执行结果，还是混合
- 哪些错误模式最重要，例如幻觉、误路由、错误调用、漏执行、恢复失败

然后再把 agent 类型当作辅助参考，而不是硬性入口。常见参考类型包括：

- ReAct / 自主选工具型
- 固定流程 / 分步骤型
- RAG 型
- transfer / subagent 型
- human-in-the-loop 型

在讨论分数前，先总结“这个 agent 的关键步骤、关键风险、关键约束和关键产物是什么”；类型只用于帮助组织语言，不要把类型映射表当成固定评分公式。

#### 第八步：讨论评测范围和标签边界

在 payload 设计前，先确定：

- 评测目标到底是什么：调试归因、离线验收、平台回写，还是先做指导
- 是否需要 trajectory 评测
- 是否需要 E2E 最终回答评测
- RAG 是否单独拆维度
- 特殊标签有哪些，以及边界怎么划
- Langfuse 里已有的 E2E 指标哪些可以直接复用，哪些才需要自定义补充
- 当前评测单元到底是什么：按 session、turn、trace 还是任务实例评
- 有没有 `ground_truth`、参考答案、参考轨迹，还是只能依赖 judge / rubric
- 默认是模型评判、规则门禁，还是模型主判 + 规则辅助

先阅读 [references/label-taxonomy.md](references/label-taxonomy.md)。

如果用户对测评不熟，先用一句话解释：

- 指标：决定“评什么”
- 标签：决定“这条样本是否有特殊情况，需要特殊解释”
- payload：决定“judge 实际能看到什么输入”

这一轮结束前，必须明确请用户回答：

- 这轮是否接受当前推荐的标签候选集合
- 是否需要对某些特殊标签额外区分
- 是否需要基于 agent 特性补充新的标签候选
- 哪些标签会抑制 E2E 或 trajectory
- 哪些标签只是观察项，不改变评分

推荐标签时，尽量给一张类似下面的矩阵表：

| case | trajectory | e2e | 备注 |
|---|---|---|---|
| `invalid_user_query` | 不执行 | 不执行 | 问题本身不具备评测意义 |
| `tool_rejected_by_user` | 执行 | 执行 | 需要按特殊边界解释 |
| `no_final_answer` | 执行 | 不执行 | 没有稳定最终结果 |

#### 第九步：推荐指标并让用户确认

先阅读：

- [references/langfuse-e2e-metrics.md](references/langfuse-e2e-metrics.md)
- [references/trajectory-metrics.md](references/trajectory-metrics.md)

这一轮至少要做三件事：

- 简要列出当前平台内置 / 可复用指标，以及它们分别在评什么
- 基于当前 agent 的流程特色、关键风险、关键产物和可观测字段给出一组 trajectory / E2E 推荐指标，区分主指标、辅助指标、观察项
- 第一版默认优先推荐少量更细粒度的核心指标：E2E 通常先推 2 到 4 个，trajectory 通常先推 3 到 5 个；不要默认先给一长串泛化大指标，特殊场景如 RAG、安全、拒答、结构化产物，再补专项扩展
- 推荐时优先从“关键成功条件、关键失败模式、关键边界风险”出发定制指标名；Langfuse 或平台已有指标更适合作为基础指标族、prompt 素材和对照参考，而不是默认直接照搬成第一版指标名
- 明确请用户确认、拒绝或编辑这组指标
- 用简短自然语言说明每组推荐背后的理由

这一轮结束时，只允许输出：

- 平台已有指标清单
- 推荐指标集合
- 指标集合的取舍理由
- 若将来要写 judge prompt，则每个指标的评分口径摘要，以及哪些指标后续必须补 few-shot / 正反例
- 等待用户确认的明确问题

这一轮**禁止**输出：

- 把推荐指标当成已定稿指标
- 在没有逐指标评分口径前，让模型直接按指标名开评
- 默认把 `Correctness`、`Helpfulness`、`Relevance` 这类大指标堆成第一版核心包，而没有先细化成更贴近当前 agent 风险和产物的指标
- 在用户未确认前开始写实现计划

#### 第十步：设计 payload，并逐块让用户确认

先阅读：

- [references/payload-design.md](references/payload-design.md)
- [references/trace-data-extraction.md](references/trace-data-extraction.md)

每个 evaluator 都要明确：

- 有哪些 payload block
- 需要哪些字段
- 哪些字段是高价值字段，哪些只是辅助解释
- 字段分别来自哪里
- 字段拿不到时怎么办
- 是否要附带 prompt context
- 如果 trajectory judge 确实需要知道是否正常结束，是否只通过 `runtime_context` 里的 session 级收尾摘要弱暴露，而不是单独放结果字段
- trajectory 和 E2E 是否真的拆成了两套核心评判载荷，而不是共用一套近似同构结构
- 长上下文如何压缩或摘要
- 每类长字段的长度预算是多少
- 超过预算时是切兜底模型、继续压缩，还是直接跳过样本
- fixture 将来怎么落盘，供本地测试和 CI 使用

每个 block 都要标清：

- block 名
- block 内字段
- 每字段用途
- 每字段价值等级
- 数据来源
- 获取状态：可取 / 假设 / blocked
- fallback

这张表展示给用户确认前，payload 只能算草案，不能进入计划。

同时要简要解释：

- 为什么需要这些 block
- 哪些 block 是为了支持某个指标
- 哪些 block 缺失会导致某个指标降级或不可评
- 哪些 session 级收尾信息可以放进 `runtime_context` 做极弱暴露，避免结果倒推过程
- 哪些字段属于共享上下文，哪些字段必须只属于 trajectory 或只属于 E2E
- 哪些长字段会成为上下文预算风险
- 超预算时的处理顺序和用户确认结果

如果 trajectory 和 E2E 的核心评判区块基本一样，只是字段名略有不同，应视为 payload 设计失败，先重新拆分，再进入计划。

如果某些字段在 discovery 阶段只能推测“理论上可取”，但无法在当前环境里直接证明，就要把“运行时验证这些字段是否真能取到”列进实现前置条件。

如果当前依赖 Langfuse 文档、表结构或代码扫描来推断字段来源，要明确告诉用户：

- 这些信息只能帮助判断“理论上去哪拿”
- 不能证明当前实现“已经拿对了”

所以在正式 judge 前，优先要求至少具备以下其中一种：

1. 单条 trace 的 payload inspect / preview
2. 关键字段的人工查库 / 查 API 验证
3. 关键字段的 presence logging + 用户接受的延后验证方案

如果用户担心 payload 字段拿错、拿空、拿晚，或者标签会因为原始 trace 数据不稳定而误判，优先回到：

- 字段来源链
- fallback 链
- inspect / preview 输出
- presence logging
- raw evidence -> flags -> labels 这一层

不要直接跳去改 judge prompt 或分数聚合。

推荐做法是：

- 对关键 payload 字段增加轻量日志
- 只记录“拿到 / 为空 / 缺失”以及长度、条数等摘要
- 不打印原文全文，避免日志过重或泄露敏感信息

这样即使环境隔离，用户也可以通过服务器或测试环境日志回传证据，帮助判断字段是否真实可取。

#### 第十一步：确认输出方式

在讨论输出方式前，必须继续确认：

- 默认 judge 模型是什么
- 是否配置大上下文兜底模型
- 模型或 judge 请求的超时阈值是多少，例如多少分钟算超时
- 如果没有兜底模型，用户是选择跳过、加强压缩，还是采用别的降级策略
- 如果发生超时，是重试、切兜底模型、降并发，还是直接失败
- 如果依赖 Langfuse，project / space、base URL（如适用）、鉴权方式、密钥状态、agent_name 或等价筛选字段是否都已确认

这些信息没确认前，不得假定 trace 范围或回写目标。

先阅读 [references/output-strategies.md](references/output-strategies.md)。

默认优先级：

1. Langfuse score 回写
2. Langfuse evaluator / judge prompt 方案
3. 报告或数据库输出
4. 如果用户暂时不实现，就只产出设计文档

如果用户已经在 Langfuse 上做 E2E 评测，优先检查平台现成指标是否可直接复用，再讨论是否补自定义指标，以及最终是保留分项分数、做简单平均，还是做加权聚合。

这一轮还要讨论：

- 这套评测是否需要对外暴露接口，还是只保留内部 runner / 脚本
- 如果需要暴露接口，要先确认是“单条 trace 评测接口”还是“按时间范围 / 条件批量评测接口”
- 只要涉及批量评测，不管入口是接口、runner、脚本还是定时任务，都必须继续确认每条 trace / sample 是否允许并行、并行量上限是多少、顺序和资源约束是什么
- 如果需要暴露接口，测试前必须明确告诉用户测试接口、调用方式和预期输入输出
- 如果不暴露接口，第一版由哪个本地入口或内部命令承接

#### 第十二步：补足实现前置条件

在进入实现前，再确认这些事情：

- 评测代码最终落在哪个目录
- 配置最终由哪个仓库 / 目录承接
- 本地最小运行链路是什么：trace 获取 -> payload 生成 -> judge 执行 -> score 输出
- 本地或测试环境具体怎么执行，必要时是否使用 `dtools` 或等价工具
- 正式 judge 前是否有单条 trace 的 payload inspect / preview 入口
- 如果本地 DB 不可查，用户是选择手动查库验证关键字段、带风险延后验证，还是改走 SDK/API/导出文件
- 只要存在批量评测执行，就必须确认并行单位、并发上限、限流方式和失败策略
- 执行后日志从哪里拿，环境隔离时由谁复制日志、复制哪些关键片段
- 哪些关键 payload 字段需要靠运行时日志验证“是否真能取到”
- judge 是走 Langfuse evaluator、本地服务，还是离线脚本
- 本地 fixture 和 golden trace 放哪里
- 本地验证和 CI 验证分别跑什么
- 报错后的修理顺序是什么，修完后最小重跑集是什么
- 执行后准备抽样分析哪几条评测结果，并据此判断是否要优化 payload / rubric / labels

如果到这里还没有先生成并让用户确认评测方案文档 / spec，不要直接开始 Plan、实现计划或开发。

要先明确提示用户：

- 先补一份给用户查看的评测方案文档 / spec
- 让用户确认这份文档
- 再基于该文档进入 Plan / 实现计划

再进入测试优先的实现阶段。

如果这些问题还答不出来，先阅读：

- [references/local-runbook.md](references/local-runbook.md)
- [references/implementation-contracts.md](references/implementation-contracts.md)
- [references/operations.md](references/operations.md)

#### 第十三步：产出落地材料

使用 `templates/` 里的模板，至少产出：

- payload 草案
- 标签定义
- 评测方案文档 / spec
- 开发 checklist

一旦方案文档生成出来，必须立即主动告诉用户：

- 文档的准确路径
- 这份文档是干什么的
- 建议用户先看哪几节

不要等用户自己追问“文档在哪里”。

这份方案文档默认要面向“完全不懂测评”的用户，至少说清楚：

- 这次到底在评什么 / 不评什么
- 为什么选这些核心指标
- 每类指标是拿什么内容去评的
- 结果最终会以什么形式输出
- 后面实现和测试会怎么推进

如果用户接下来要实现，先确认这份方案文档已经被用户接受，再切到测试优先的实现计划，并优先围绕 fixture、payload 提取、label 推导、judge 输出解析写第一批测试。

在准备宣称“可运行”之前，至少还要做两件事：

- 做一次整链路 runnable review，检查是否真的能从 trace 走到 score / report，而不是只有局部代码拼起来
- 用 3 到 5 条代表性样本复盘结果，确认日志、payload、标签、judge 输出和最终分数是否符合预期

如果当前实现提供了测试接口，必须主动告诉用户：

- 接口名称或路径
- 调用方式
- 关键输入输出

如果当前没有对外接口，也必须主动告诉用户：

- 现在只支持哪个 runner / 脚本入口
- 用户该怎么触发第一版验证

如果环境里可用，优先建议再走一次等价于 `verification-before-completion` 和 `requesting-code-review` 的收尾检查。

#### 第十四步：实现后验证与反馈迭代

代码完成后，不得直接把“能跑”当成“评测体系已经完成”。

第十三步里的 runnable review 和样本复盘，不等于这里面向用户的首轮验证闭环；两者不能互相替代。

必须主动带用户进入一轮实现后验证闭环，至少包括：

- 明确告诉用户首轮验证入口是什么
- 明确告诉用户结果落点和日志位置是什么
- 明确告诉用户要先去平台官网或 trace 查看页面确认目标 trace 是否真实存在
- 明确告诉用户要抽检 3 到 5 条代表性 trace，而不是只看总表或平均分
- 明确告诉用户要分别检查 `trajectory`、`e2e`、标签、judge `reason` 和关键字段 presence 日志
- 明确要求用户按结构化模板反馈问题，而不是只说“这个分不对”

必须立即主动告诉用户验证文档：

- 路径是什么
- 这份文档是干什么的
- 建议先看哪几节

不要等用户追问“接下来怎么验”“发现问题怎么反馈”。

默认先阅读：

- [references/post-implementation-validation.md](references/post-implementation-validation.md)

如果用户反馈首轮结果不合理，默认优先按这个顺序排查：

1. trace / 数据层
2. payload 取值与压缩层
3. label 边界
4. rubric / judge prompt
5. 输出与聚合层

不要因为用户一句“感觉不对”就直接整套重写。

要先要求用户提供至少一部分证据，例如：

- trace_id
- 不合理的分数项
- 人工预期
- judge `reason`
- 关键日志片段
- 怀疑的问题层

收到结构化反馈后，再决定下一轮最小优化切片和最小重跑集。

## 需要按需阅读的文件

- 可评测性检查：[references/langfuse-readiness.md](references/langfuse-readiness.md)
- agent 分类：[references/agent-classification.md](references/agent-classification.md)
- payload 设计：[references/payload-design.md](references/payload-design.md)
- trace 数据抽取与 payload / label 校验：[references/trace-data-extraction.md](references/trace-data-extraction.md)
- 标签边界：[references/label-taxonomy.md](references/label-taxonomy.md)
- trajectory 多维度指标参考：[references/trajectory-metrics.md](references/trajectory-metrics.md)
- 输出策略：[references/output-strategies.md](references/output-strategies.md)
- 本地运行指引：[references/local-runbook.md](references/local-runbook.md)
- 实现后验证与反馈迭代：[references/post-implementation-validation.md](references/post-implementation-validation.md)
- 实现契约参考：[references/implementation-contracts.md](references/implementation-contracts.md)
- 运行期注意事项：[references/operations.md](references/operations.md)
- E2E 指标参考：[references/langfuse-e2e-metrics.md](references/langfuse-e2e-metrics.md)
- 指标 Prompt 附录：[references/langfuse-metric-prompts.md](references/langfuse-metric-prompts.md)
- payload 模板：[templates/payload-template.md](templates/payload-template.md)
- 标签模板：[templates/label-template.md](templates/label-template.md)
- 开发 checklist：[templates/eval-dev-checklist.md](templates/eval-dev-checklist.md)
- 评测 spec 模板：[templates/eval-spec-template.md](templates/eval-spec-template.md)

## Skill 自测材料

以下文件用于验证这个 skill 本身，不是用户默认工作流的一部分：

- 自测场景：[references/validation-scenarios.md](references/validation-scenarios.md)
- 自测结果：[references/validation-results.md](references/validation-results.md)

## 快速参考

| 情况 | 应该怎么做 |
|---|---|
| 用户还没说评测项目在哪 | 先问评测仓库、配置位置和代码落点，不要急着谈指标 |
| 本地代码 + Langfuse DB | 做完整 readiness 检查，从代码和 trace 反推 payload，优先选 Langfuse score 输出 |
| 本地代码 + Langfuse API | 降低对 observation 细节的依赖，先确认能导出什么 |
| 只有导出 trace | 围绕已有字段设计，明确记录缺失项，优先产出文档型材料 |
| Langfuse 已有现成 E2E 指标 | 先做指标映射表，再给推荐指标组合，等用户确认后再继续 |
| 只有本地代码，暂无可运行评测链路 | 先明确项目落位、评测单元、ground truth 策略和本地最小运行链路，再进入实现 |
| 缺 metadata 或 prompt context | 说明下次该补哪些 trace 字段，并继续做 reduced-scope 设计 |
| 用户只想要指导 | 到 spec、payload、labels 和输出建议为止，不强推实现 |
| 用户准备开始构建 | 产出实现 checklist，然后切到 TDD 驱动开发 |

## 常见错误

- 从指标名字出发，而不是从 agent 真实可观测结构出发
- 还没问评测项目位置、配置位置和代码落点，就直接开始讨论方案
- 还没查 DB、SDK、API、trace 文件，就过早把 Langfuse 当成可有可无
- 还没让用户确认推荐指标，就直接把指标写进计划
- 还没让用户确认标签是否需要特别区分，就直接把标签写进计划
- 标签和评分规则混在一起，但边界没有定清楚
- 用户明显不懂测评概念时，没有先解释指标、payload、标签分别是什么
- 误以为 judge 能看到未经压缩的原始长上下文
- 忽略了 prompt 或 routing 对“什么算正确行为”的约束
- 明明 Langfuse 平台已有可复用的 E2E 指标，却从零重新造一套同义分数
- 还没让用户确认 payload 区块、字段来源和 fallback，就直接开始规划实现
- readiness 还只是中间结论，就提前替用户生成计划
- 用户还没有 plan/spec，就直接进入开发
- 已经产出了 spec，但没有定义评测单元、fixture 和 judge 输出契约，就直接开始写代码
- 数据不完整就停住，而不是先给 reduced-scope 方案和缺口列表

## 默认输出标准

默认至少要给用户留下六样东西：

1. 一份简洁的 readiness 结论
2. 一份已确认事项与未确认事项清单
3. 一组已展示给用户的推荐指标集合
4. 一份已展示给用户确认的 payload 和 label 草案
5. 一份可给用户审阅细节的评测方案文档
6. 一个明确的下一步：继续 discovery、开始实现、先补可观测性，或者先停留在设计层
