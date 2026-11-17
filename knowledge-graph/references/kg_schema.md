# 知识图谱数据 Schema

面向 AI 消费的业务知识图谱字段定义。适用于 YAML（主管道输出格式）和 JSON 序列化。

## 顶层结构

```yaml
meta: {}
glossary: {}
entities: []
relations: []
businessRules: []
businessFlows: []
```

---

## meta

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 图谱标题 |
| domain | string | 是 | 业务领域 |
| version | string | 是 | 版本号 `x.y` |
| createdAt | string | 是 | `YYYY-MM-DD` |
| updatedAt | string | 否 | 最后更新日期 |
| description | string | 否 | 覆盖范围描述 |
| sources | string[] | 否 | 来源文档 |
| codeRepos | string[] | 否 | 代码仓库路径 |
| aiUsageHint | string | 否 | AI 使用指引 |

---

## glossary

代码术语 → 业务概念的翻译字典。Key 为术语字符串。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| definition | string | 是 | 业务含义 |
| entityRef | string | 否 | 关联实体 ID |

```json
{ "mchid": { "definition": "商户号，唯一标识", "entityRef": "E001" } }
```

---

## entities

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | `E{三位数字}` 或 `E_{DOMAIN}_{NAME}`（多域场景）或 `E_NOUN_{五位数字}`（名词扩展） |
| name | string | 是 | 中文名 |
| enName | string | 否 | PascalCase 英文名（名词扩展模式可省略） |
| type | string | 是 | `core`/`enum`/`event`/`role`/`process`（领域模型模式）；`noun`/`rule`（名词扩展模式）。不符合实体标准的概念应建为 Property，不使用 `attribute` 类型 |
| description | string | 是 | 业务语义（2-3 句，含是什么/为什么/角色） |
| source | string | 是 | `名词库`/文档名/`代码分析` |
| properties | Property[] | 否 | 属性列表 |
| codeMapping | CodeMapping | 否 | 代码位置 |
| synonyms | string[] | 否 | 代码/文档中的别名 |
| lifecycle | string | 否 | 生命周期描述 |
| stateTransitions | StateTransition[] | 否 | 状态迁移（有状态时填） |
| tags | string[] | 否 | 分组标签 |
| status | string | 否 | `confirmed`/`pending` |

### Property

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 中文名 |
| enName | string | 否 | camelCase |
| type | string | 是 | `string`/`int`/`decimal`/`boolean`/`date`/`datetime`/`enum`/自定义 |
| description | string | 否 | |
| required | boolean | 否 | |
| enumValues | string[] | 否 | enum 取值 |
| constraints | string | 否 | 约束 |
| codeField | string | 否 | 代码字段名 |
| dbColumn | string | 否 | 数据库列名 |
| dbTable | string | 否 | 数据库表名 |

### CodeMapping

| 字段 | 类型 | 说明 |
|------|------|------|
| modules | string[] | 模块/服务名 |
| files | string[] | 代码文件路径 |
| classes | string[] | 类/结构体 |
| functions | string[] | 函数/方法 |
| dbTables | string[] | 数据库表 |
| apis | string[] | API 路径 |
| protoMessages | string[] | Protobuf Message |
| configKeys | string[] | 配置项 |

### StateTransition

| 字段 | 类型 | 必填 |
|------|------|------|
| from | string | 是 |
| to | string | 是 |
| trigger | string | 是 |
| description | string | 否 |

---

## relations

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 格式见下方 ID 规则 |
| head | string | 是 | 源实体 ID（别名: source） |
| tail | string | 是 | 目标实体 ID（别名: target） |
| relation_type | string | 是 | 见下方关系类型表（别名: type） |
| label | string | 否 | 中文标签 |
| description | string | 否 | 业务含义 |
| cardinality | string | 否 | `1:1`/`1:N`/`N:1`/`N:M` |
| weight | float | 否 | 关系权重 0~1（noun_extension 模式必填） |
| domain | string | 否 | 关系所属业务域 |
| evidence | string | 否 | 文档依据 |
| codeEvidence | string | 否 | 代码依据 |
| dataPath | string | 否 | 数据关联路径（如 `t_a.Fid → t_b.Fid`） |
| bridge_source | string | 否 | 跨域桥接来源 ID（多域合并时） |
| status | string | 否 | |

### 关系类型

**核心类型（full/incremental 模式）：**

| type | 中文 | 说明 |
|------|------|------|
| `contains` | 包含 | 整体-部分 |
| `belongs_to` | 属于 | 归属 |
| `depends_on` | 依赖 | 需要（也用于跨域"同一实体"桥接合并后） |
| `associates` | 关联 | 一般关联 |
| `generalizes` | 泛化 | 继承/特化 |
| `triggers` | 触发 | 因果 |
| `produces` | 产生 | 处理结果 |
| `references` | 引用 | 使用但不拥有 |
| `manages` | 管理 | 控制权 |
| `transforms` | 转化 | 形态变化 |
| `precedes` | 前置 | 先后顺序 |
| `constrains` | 约束 | 规则约束 |

**跨域桥接类型（多域合并场景，保留原始语义）：**

| type | 说明 |
|------|------|
| `语义等价` | A ≈ B，同一概念在不同域的不同视角 |
| `子集关系` | A ⊂ B，A 是 B 的一部分 |
| `对齐映射` | A 对齐到 B（扩展关系） |
| `镜像映射` | A 是 B 的镜像/门面 |
| `引用关联` | A 引用 B（间接路径） |
| `驱动关联` | A 执行后驱动 B |
| `实例关系` | A 是 B 的具体实例 |
| `扩展映射` | A 是 B 的扩展 |

**名词扩展类型（noun_extension 模式）：**

| type | 权重区间 | 说明 |
|------|---------|------|
| `strongly_associates` | >= 0.40 | 强关联（三信号融合） |
| `associates` | 0.25~0.40 | 关联（三信号融合） |
| `weakly_associates` | 0.15~0.25 | 弱关联（三信号融合） |
| `graph_inferred` | 按 TF-IDF*0.8 | 图推理关联（Stage 4h，通过 v1 图结构间接发现） |
| `generalized_associates` | 0.10 固定 | 词根泛化关联（Stage 4i，基于领域建模 IS-A/PART-OF 的人工映射） |

---

## businessRules（YAML 文件中顶层 key 为 `businessRules`）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | `BR_{NNN}` |
| name | string | 是 | 规则名 |
| description | string | 是 | 是什么 + 为什么 + 违反后果 |
| type | string | 是 | `validation`/`constraint`/`calculation`/`permission`/`flow_control` |
| involvedEntities | string[] | 是 | 涉及实体 ID |
| condition | string | 是 | 条件（自然语言或伪代码） |
| action | string | 是 | 满足时处理 |
| exception | string | 否 | 不满足时处理 |
| source | string | 否 | 来源 |
| codeLocation | string | 否 | 代码位置 |
| priority | string | 否 | `critical`/`major`/`minor` |

---

## businessFlows（YAML 文件中顶层 key 为 `businessFlows`）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | `BF_{NNN}` |
| name | string | 是 | 流程名 |
| description | string | 是 | 业务目的 |
| triggerCondition | string | 是 | 触发条件 |
| involvedEntities | string[] | 是 | 涉及实体 ID |
| steps | FlowStep[] | 是 | 步骤 |
| happyPath | string | 否 | 主成功路径概述 |
| errorScenarios | string[] | 否 | 异常场景 |

### FlowStep

| 字段 | 类型 | 必填 |
|------|------|------|
| order | int | 是 |
| actor | string | 是 |
| action | string | 是 |
| entityRef | string | 否 |
| ruleRef | string | 否 |
| codeEntry | string | 否 |
| output | string | 否 |

---

## ID 规则

| 类别 | 格式 | 示例 | 适用场景 |
|------|------|------|---------|
| 实体（简单） | `E{三位数字}` | `E001` | 单域小规模 |
| 实体（多域） | `E_{DOMAIN}_{NAME}` | `E_TRADE_交易订单` | 多域合并场景 |
| 实体（名词扩展） | `E_NOUN_{五位数字}` | `E_NOUN_00001` | noun_extension 模式 |
| 关系（简单） | `R{三位数字}` | `R001` | 单域 |
| 关系（多域） | `R_{NNN}` / `RR_{NNN}` / `R_BRIDGE_{NNN}` / `R_NOUN_{NNN}` | `R_001`, `R_NOUN_00001` | 多域/名词扩展 |
| 规则 | `BR_{NNN}` | `BR_001` | — |
| 流程 | `BF_{NNN}` | `BF_001` | — |

增量更新时在已有最大编号基础上递增。同一图谱内 ID 格式应统一。

## 校验规则

1. 所有 ID 各自列表内唯一
2. relations/rules/flows 中引用的实体 ID 必须存在
3. flows.steps[].ruleRef 必须引用存在的规则 ID
4. `core` 实体应有 description ≥ 2 句 + codeMapping（有代码时）
5. synonyms 应覆盖代码中的所有别名
