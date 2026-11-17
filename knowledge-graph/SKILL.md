---
name: knowledge-graph
description: >-
  从业务文档/代码/类图中提取实体、关系、业务规则、业务流程和术语，构建五层结构化知识图谱（BFS验证零孤立节点）。
  五层产出：entities（概念层）+ relations（结构层）+ rules（规则层）+ flows（流程层）+ glossary（翻译层）。
  支持全量构建、增量更新、名词扩展、质量自检、评分、知识查询六种模式。
  触发词：知识图谱、生成知识图谱、业务概念关系、实体关系图、概念网络、
  名词关系梳理、业务理解、代码业务分析、ontology、GraphRAG、KG。
  不适用于：纯数据字典整理（用名词库）、单个API文档编写（用契约工具）、流程图绘制（用drawio-diagrams）、领域建模（用domain-modeling）。
---

# 知识图谱 Skill

端到端知识图谱建设、自检、评分、维护的执行引擎。
**五层 YAML 主管道输出**（完整字段定义见 `references/kg_schema.md`）：

| 层 | 产出文件 | 作用 |
|----|---------|------|
| 概念层 | `kg-entities.yaml` | 业务概念 + 属性 + 代码映射 |
| 结构层 | `kg-relations.yaml` | 概念间关系 + 基数 + 数据路径 |
| 规则层 | `kg-rules.yaml` | 业务约束/校验/计算/权限 |
| 流程层 | `kg-flows.yaml` | 业务流程步骤 + 规则引用 |
| 翻译层 | `kg-glossary.yaml` | 代码符号 → 业务概念映射 |

**输入物分层**（与原有设计一致）：

| 层级 | 来源 | 定位 | 产出贡献 |
|------|------|------|---------|
| **基准信息** | 类图 + 领域模型文档 | 骨架，100% 覆盖 | entities + relations |
| **补充信息** | 名词库（xnoun 或等价接口） | 标准化命名 + 定义补全 | entities 定义 + synonyms |
| **辅助信息** | 代码仓库、需求文档/PRD、用例规约 | 丰富规则/流程/映射 | rules + flows + glossary + codeMapping |

规则/模板/示例见 `references/`，HTML 页面模板资产见 `scripts/`，本文件只保留主流程和决策点。
文中 `<skill-root>` 表示当前 Skill 根目录，可替换为相对路径、工作区路径或宿主环境提供的等价变量。

## 目录

- [铁律](#铁律)
- [执行模式（入口）](#执行模式入口)
- [Stage 1: 规划](#stage-1-规划-planner)
- [Stage 2: 提取](#stage-2-提取-extractor)
- [Stage 3: 生成](#stage-3-生成-generator)
- [Stage 4: 自检](#stage-4-自检-validator)
- [Stage 5: 评分](#stage-5-评分-scorer)
- [Stage 6: 增量更新](#stage-6-增量更新-guardian)
- [多轮迭代](#多轮迭代)
- [执行保护](#执行保护内置)
- [工具脚本](#工具脚本)
- [文档职责](#文档职责与同步规则)
- [使用反馈](#使用反馈)

## 铁律

1. **忠于原文**：禁止捏造概念。无据可查的标注「待确认」。
2. **先查后问**：先用可用的名词库接口、全文搜索和文件读取能力自行获取信息。只问用户才知道的事。
3. **AI-first 表达**：description 写清「是什么 + 为什么 + 角色」，AI 无需额外上下文即可理解。
4. **本体化建模**：业务概念建模为具有独立身份、属性和关系的本体对象，而非扁平化数据字典。
5. **名词库优先**：名词以 xnoun 或等价名词库接口的查询结果为标准定义，保持与组织名词库一致。
6. **尊重用户边界**：用户明确指定了知识源范围时，严格在该范围内提取，不主动扩展或补充范围外的实体信息。
7. **全连通网络**：`full`/`incremental` 模式下，最终图谱必须是单连通分量——不允许存在孤立节点或断连子图。每个实体至少有一条边。生成后必须 BFS 验证。`noun_extension` 模式例外：骨架实体（v1）必须 100% 连通，名词实体允许断连（标注为独立名词节点），因精度-覆盖率 trade-off 不应为了连通率制造垃圾关系。
8. **版本化输出**：每次全量/增量生成输出到独立版本文件夹（如 `v7/`），不覆盖历史版本。
9. **同名实体唯一**：同一业务概念（按名称判定）在全域知识图谱中只允许存在**一个**权威实体，由概念归属的领域拥有。其他领域需使用该概念时，通过跨域依赖关系（`depends_on`）直接引用权威实体 ID，**禁止**创建"引用实体"、"影子副本"或带 `cross_domain_ref` 的重复实体。Stage 4 必须强制校验。

---

## 执行模式（入口）

根据用户意图选择模式（默认 `full`）：

| 用户意图 | 模式 | 执行路径 |
|---------|------|---------|
| 全量构建知识图谱 | `full` | Stage 1→2→3→4→5 |
| 文件变更后更新 | `incremental` | Stage 6→2→3→4→5 |
| 基于名词列表扩展已有图谱 | `noun_extension` | Stage 1→2(段D)→3→4→5 |
| 检查现有图谱质量 | `validate` | Stage 4 |
| 对图谱打分 | `score` | Stage 5 |
| 查询图谱中的知识 | `query` | 直接读取 KG 数据文件回答 |

---

## Stage 1: 规划 (Planner)

1. **盘点知识源**：扫描用户指定的目录/文件，逐文件统计数据条目数，识别结构化数据源链接（如 XWatt URL）
2. **知识源分类**：按内容特征自动标注每个文件的层级和贡献

| 层级 | 文件特征 | 分类 | 贡献层 |
|------|---------|------|-------|
| **基准信息** | 含"聚合根/值对象/实体"等建模术语 | 领域模型 | entities, relations |
| **基准信息** | 类图 URL 或 XWatt 链接 | 结构化数据源 | entities, relations |
| **补充信息** | 名词库查询结果 | 名词库 | entities 定义 + synonyms |
| **辅助信息** | 含"必须/不能超过/只有...才能"等约束表述 | 需求文档/PRD | rules, entities |
| **辅助信息** | 含"主成功路径/前置条件/扩展步骤"等用例结构 | 用例规约 | flows, rules |
| **辅助信息** | `.cpp` / `.py` / `.proto` / `.sql` 等代码文件 | 代码 | glossary, codeMapping |

3. **领域划分 + 版本文件夹**：识别子域边界，创建输出目录（如 `v7/`）
4. **定义能力问题**：≥20 个 KG 必须能回答的问题（P0/P1/P2），覆盖"是什么""怎么关联""有什么约束""怎么流转"四类
5. **生成执行计划**：明确知识源 100% 覆盖清单 + 补充数据源清单
6. **输入完整度评估**：根据已有知识源分类，输出五层产出预估和建议补充的输入源

**输出物**：`execution-plan.md`（含 source_classification 段）+ `competency-questions.yaml`

---

## Stage 2: 提取 (Extractor)

**核心原则**：基准信息（类图+领域模型）= 骨架（100% 覆盖），补充信息（名词库）= 标准化命名，辅助信息（代码/需求/用例）= 丰富规则/流程/映射。根据 Stage 1 的知识源分类，对不同层级文件选择不同提取策略。

### 三段并行提取（按 Stage 1 分类结果驱动）

```
┌─ 段A：骨架提取（基准信息）────────────┐
│  类图/领域模型 → 实体+关系+属性        │  ← 100% 覆盖
├─ 段B：规则与流程（辅助信息）──────────┤  ← 与段A并行
│  需求文档/用例规约 → 规则+流程         │
├─ 段C：术语与映射（辅助信息）──────────┤  ← 与段A/B并行
│  代码/Proto/DDL → 术语表+codeMapping  │
└──────────────────────────────────────┘
  + 补充信息（名词库）并行查询标准化命名
         ↓ 合并 → 去重消歧 → ID 互引校验
```

**段A — 实体+关系**（基准信息：领域模型/类图 + 补充信息：名词库）：

| 知识源特征 | 骨架提取 | 补充连接手段 |
|-----------|---------|-------------|
| 纯文档 | 逐文件提取实体+关系+枚举 | 文档中的 UML 文本/关系段落 |
| 文档 + 类图链接 | 文档提取枚举/配置 | 调用类图结构化接口（详见 `references/xwatt-extract-protocol.md`） |
| 文档 + 代码 | 文档提取概念 | 代码引用/外键/调用链 |

**段B — 规则+流程**（辅助信息：需求文档/PRD/用例规约）：

| 信号词 | 提取为 | 规则类型 |
|--------|-------|---------|
| "不能超过/必须/不得/至少/最多" | businessRule | `validation` |
| "只有...才能/当...时" | businessRule | `constraint` |
| "等于/=A+B/按照...计算" | businessRule | `calculation` |
| "有权限/才能操作" | businessRule | `permission` |
| "先...后.../审批通过后" | businessRule | `flow_control` |
| "第一步...第二步/先...然后...最后" | businessFlow | — |

规则 description 三要素：**是什么 + 为什么 + 违反后果**。流程每步记录：actor + action + entityRef + ruleRef。

**段C — 术语+映射**（辅助信息：代码仓库/Proto/DDL）：
- 从实体 enName + synonyms → 自动生成 glossary 条目
- 代码搜索 `class {enName}` / `t_{name}` / `message {enName}` → 填充 codeMapping
- 属性 codeField / dbColumn → 自动生成 glossary 条目

### 并行任务（按可用性启动）

1. **知识源扫描**（必选）：逐文件按分类提取实体+关系+规则+流程
2. **名词查询**（有 xnoun 或等价名词库接口时）：并行查询，合并去重
3. **类图结构化提取**（有类图 URL 时）：并行获取原始 JSON（节点+边）
4. **代码扫描**（有代码时）：搜索类名、表名、Proto、API → 填充 codeMapping + glossary

**段D — 名词扩展**（`noun_extension` 模式专用）：

当用户提供大规模名词列表（数千~数万条）要求扩展已有 KG 时触发。**不是纯文本匹配**，必须使用三信号融合算法：

| 信号 | 权重 | 方法 | 作用 |
|------|------|------|------|
| name_jaccard | 0.30 | jieba 词性分词 → token 集合 Jaccard | 名称概念重叠 |
| tfidf_cosine | 0.55 | TF-IDF 向量化 + 余弦相似度矩阵 | 描述语义相似（核心信号） |
| mention_boost | 0.15 | 名词解释中扫描已有实体名 (0/1) | 显式引用（二值辅助信号，降权防偶然提及过度放大） |

必须配套的优化（缺一不可，阈值经四维质量评估验证）：
1. **高频实体软降权**（RAGAS 风格改进）：Top-5% 高频实体在 Jaccard/mention 信号中乘以 0.3 惩罚系数（不再硬屏蔽为 0，避免切断唯一连接）
2. **阈值控制**：融合分 >= **0.15** 才建立关系，不再使用 candidate_associates 层
3. **度中心性剪枝**（KGTrimmer 风格）：单个实体最大被关联数 <= 300
4. **二次图推理**（Stage 4h）：对断连名词 jieba 全切分 + 域前缀 + 名称子串 + 枚举值匹配 → v1 桥接实体 → 渐进 5 跳邻居 → TF-IDF 验证 → `graph_inferred` 关系
5. **词根泛化**（Stage 4i）：剩余断连名词提取词根（域前缀关键词），通过人工定义的 IS-A/PART-OF 映射（20 条）连接到 v1 概念 → `generalized_associates` 关系。实测最终覆盖率 **100%**

详细算法、阈值配置和质量验收标准见 `references/noun-extension-algorithm.md`。

**环境要求**（`noun_extension` 模式专用）：`python3.9+` + `scikit-learn` + `jieba` + `numpy`。如环境中没有，先执行 `pip3 install scikit-learn jieba numpy`。

### 关键规则

- **枚举必连**：每个枚举值 → `枚举归属` → 父类型实体；树形枚举用 `层级归属`
- **规则必引实体**：每条 businessRule 的 involvedEntities 必须引用已提取的实体 ID
- **流程必引规则**：businessFlow 的 steps.ruleRef 必须引用已提取的规则 ID（无规则时留空）
- **归并记录**：多源同一概念不同名称时，知识源名称为准，记录到 `kg-entity-mapping.md`
- **冲突优先级**：xnoun 名词库 > 知识源文档 > 补充数据源 > 用户口述

详细规则见 `references/extraction-rules.yaml`

**输出物**：`kg-triples-raw.yaml`（含实体、关系、规则、流程、术语五类原始数据）

---

## Stage 3: 生成 (Generator)

1. **多域合并**（多域场景必须执行）：
   - 读取跨域桥接文件（如 `跨域桥接关系.yaml`），识别"同一实体"桥接
   - 按铁律9消除影子实体，关系重定向到权威实体 ID
   - 桥接关系类型保真（仅"同一实体"转 `depends_on`，其余保留原类型）
   - 同名实体去重，输出 `kg-entity-mapping.md` 记录归并映射
2. **名词扩展集成**（`noun_extension` 模式）：段D 的输出在此步骤合并到主实体/关系集合，确保后续步骤统一校验
3. 实体/关系去重规范化（ID 格式见 `references/kg_schema.md` ID 规则表。常用：实体 `E_{DOMAIN}_{NAME}`、关系 `R_{NNN}` / `R_BRIDGE_{NNN}` / `R_NOUN_{NNN}`、规则 `BR_{NNN}`、流程 `BF_{NNN}`）
4. **BFS 全连通验证**（构建邻接表 → BFS → 对比 → 补桥）
5. **ID 互引校验**：rules.involvedEntities → entities；flows.steps.ruleRef → rules；flows.steps.entityRef → entities；glossary.entityRef → entities
6. 社区检测：按关系密度识别子域社区
7. 合并输出五层文件（每个 YAML 文件头部包含 `meta` 段：title/domain/version/createdAt，字段定义见 `references/kg_schema.md`）

### BFS 全连通验证（必须执行）

构建无向邻接表 → 从任意节点 BFS → 对比可达集 vs 全量集。连通率 < 100% 时：
- 识别断连子图/孤立节点
- 逐项检查跨域桥接边是否缺失（清单见 `references/bridge-checklist.md`）
- 从补充数据源或文档文本中查找缺失边
- 仍无法连通 → 记录到 `kg-unconnected.md`

### 确认策略

| 规模 | 行为 |
|------|------|
| ≤ 5 实体 | 跳过确认 |
| 6-15 实体 | 精简清单 |
| > 15 实体 | 完整清单，等用户确认 |

### 输出物

**主输出（YAML，机器可读，五层）**：

| 文件 | 内容 | 必选条件 |
|------|------|---------|
| `kg-entities.yaml` | 全量实体（含 properties、codeMapping、stateTransitions） | 始终必选 |
| `kg-relations.yaml` | 全量关系（含 cardinality、dataPath） | 始终必选 |
| `kg-rules.yaml` | 业务规则（condition + action + exception + involvedEntities） | 有需求文档/用例时必选 |
| `kg-flows.yaml` | 业务流程（steps + ruleRef + entityRef + codeEntry） | 有用例规约时必选 |
| `kg-glossary.yaml` | 术语表（code term → definition + entityRef） | 有代码或实体 synonyms 时必选 |

**衍生输出（从 YAML 自动生成）**：

| 文件 | 内容 | 生成方式 |
|------|------|---------|
| `kg-entities.md` | 全量实体的人类可读 Markdown 表格 | 从 `kg-entities.yaml` 渲染 |
| `kg-relations.md` | 全量关系的人类可读 Markdown 表格 | 从 `kg-relations.yaml` 渲染 |
| `kg-rules.md` | 全量规则的人类可读 Markdown 表格 | 从 `kg-rules.yaml` 渲染 |
| `kg-flows.md` | 全量流程的人类可读 Markdown 表格 | 从 `kg-flows.yaml` 渲染 |
| `kg-glossary.md` | 术语表的人类可读 Markdown 表格 | 从 `kg-glossary.yaml` 渲染 |
| `knowledge-graph.html` | **可交互可视化图谱**（必选） | 从 YAML 自动生成，见下方 |
| `kg-unconnected.md` | 孤立节点清单（全连通时写"无孤立节点"）| — |
| `kg-entity-mapping.md` | 多源归并映射（无冲突时写"无归并映射"）| — |
| `kg-synonym-groups.md` | 同义概念归类清单，供用户审查合并是否正确 | — |

### 可视化 HTML 生成（必须执行）

`kg-entities.yaml` + `kg-relations.yaml` 完成后，**必须**运行脚本自动生成可交互 HTML：

```bash
python3 <skill-root>/scripts/kg_to_html.py <版本目录>/kg-entities.yaml <版本目录>/kg-relations.yaml [--rules kg-rules.yaml] [--flows kg-flows.yaml]
```

脚本运行时依赖 `scripts/kg_html_template.html` 作为页面模板；样式和交互调优规范见 `references/html-style-guide.md`。

脚本自动从 YAML 解析实体和关系（也兼容旧版 Markdown 表格输入），生成包含以下交互功能的 HTML 页面：
- ECharts 力导向图，按业务域着色、按实体类型区分大小
- 侧边栏域/类型勾选筛选
- 搜索定位
- 节点点击查看详情（含出入关系列表）
- 枚举/名词节点显隐切换
- 导出 PNG
- BFS 连通率统计面板

输出格式见 `references/output-formats.yaml`，示例见 `examples/example_kg.md`

---

## Stage 4: 自检 (Validator)

**结构层检查（entities + relations）：**

| 检查项 | 通过标准 | 失败处理 |
|-------|---------|---------|
| 用户知识源覆盖率 | **= 100%** | 逐文件对比条目数，列出缺失项，回 Stage 2 补充 |
| **BFS 全连通** | `full`/`incremental`: **= 100%**；`noun_extension`: 骨架实体 100%，名词实体记录断连数 | 回 Stage 3 执行桥接检查清单，补充边直至连通 |
| **同名实体唯一** | **0 重名**（按 name 字段跨文件去重） | 保留权威实体，删除影子副本 |
| 关系引用正确性 | 0 无效引用 | 所有 relation 的 head/tail 必须在 entity 集合中 |
| 枚举归属完整性 | 每个枚举实体有 ≥1 条归属关系 | 补充缺失的 `枚举归属` 边 |
| 影子实体检查 | 0 个 `type: 引用实体` 或 `cross_domain_ref` | 删除影子实体 |

**规则层检查（rules，有需求文档时）：**

| 检查项 | 通过标准 | 失败处理 |
|-------|---------|---------|
| involvedEntities 引用有效性 | 所有引用的实体 ID 存在于 entities 中 | 修正 ID 或补充实体 |
| condition/action 非空 | 每条规则必须有 condition 和 action | 回 Stage 2 从知识源补充 |
| type 合法性 | 必须为 validation/constraint/calculation/permission/flow_control | 修正 type |

**流程层检查（flows，有用例规约时）：**

| 检查项 | 通过标准 | 失败处理 |
|-------|---------|---------|
| steps.entityRef 引用有效性 | 引用的实体 ID 存在于 entities 中 | 修正 ID |
| steps.ruleRef 引用有效性 | 引用的规则 ID 存在于 rules 中 | 修正 ID 或补充规则 |
| steps 有序且非空 | 至少 1 个步骤，order 连续 | 补充步骤 |

**术语层检查（glossary，有术语时）：**

| 检查项 | 通过标准 | 失败处理 |
|-------|---------|---------|
| entityRef 引用有效性 | 引用的实体 ID 存在于 entities 中 | 修正 ID |
| term 唯一性 | 无重复 term | 合并重复条目 |

**综合检查：**

| 检查项 | 通过标准 | 失败处理 |
|-------|---------|---------|
| 能力问题(P0) | 100% 可回答（含规则类和流程类问题） | 补充缺失路径/规则/流程 |
| 跨域桥接完整性 | 桥接检查清单每项至少 1 条边 | 查补充源或文档文本补充 |

**`noun_extension` 模式附加检查（四维评估）：**

| 检查项 | 方法 | 合格线 |
|-------|------|--------|
| P0 稀疏度 | 关系类型数/总边数 | < 0.01 |
| P1 Judge Precision | 分层抽样 100 条，LLM 判断（不可用规则模拟） | >= 0.70 |
| P2 加权 Precision | CrIs 分层抽样 200 条 | 95%CI 下界 >= 0.60 |
| P3 AUC-PR | 正样本(人工确认) vs 负样本(corrupted) | >= 0.60 |

详见 `references/noun-extension-algorithm.md` 的进阶指标章节。

**剪枝步骤**（评估不达标时触发）：
1. 提高 SCORE_THRESHOLD（从 0.15 逐步提高到 0.20/0.25）
2. 移除低 Precision 的关系层（如 candidate_associates）
3. 度中心性剪枝（降低 MAX_DEGREE）
4. 重新运行评估，直到 P1 Precision >= 0.70

**脚本辅助**：`python3 <skill-root>/scripts/kg_validate.py <entities.yaml> <relations.yaml> [rules.yaml] [flows.yaml] [glossary.yaml]`

详细规则见 `references/validation-rules.yaml`

**输出物**：`kg-validation.yaml`（格式见 `references/report-templates.yaml`）；`noun_extension` 模式额外输出 `kg-quality-evaluation.md`

---

## Stage 5: 评分 (Scorer)

**`full`/`incremental` 模式**：KG 质量(40%) + 消费质量(40%) + 维护质量(20%)，等级 S(≥90)/A(80-89)/B(70-79)/C(60-69)/D(<60)。消费质量中，规则覆盖率和流程覆盖率作为新增指标纳入评分（有需求文档/用例时计入，无则跳过）。详见 `references/scoring-rubric.yaml`。

**`noun_extension` 模式**：除上述三维评分外，追加四维质量评估（P0~P3）结果。评分维度增加「名词扩展质量」：关系 Precision × 覆盖率的调和平均。

**输出物**：`kg-score.yaml`；`noun_extension` 模式额外输出 `kg-quality-evaluation.md`

---

## Stage 6: 增量更新 (Guardian)

变更检测 → 影响分析 → 增量提取 → 合并更新 → 冲突解决 → 增量验证 → 记录日志。更新前自动备份(保留 3 版)，`.kg-lock` 防并发。详见 `references/protection-config.yaml`。

---

## 多轮迭代

每轮 Stage 2→3→4→5。质量分 < 80 或覆盖率/连通率未达标 → 继续；连续 2 轮提升 < 2 分 → 收敛停止，最多 20 轮。

**收敛条件**（全部满足方可停止）：
- 用户知识源覆盖率 = 100%
- **BFS 连通率**：`full`/`incremental` = 100%（无孤立节点）；`noun_extension` = 骨架实体 100% + 名词覆盖率 > 50%（含图推理）
- 关系引用正确率 = 100%（0 无效引用）
- **跨层引用正确率 = 100%**（rules→entities、flows→rules、flows→entities、glossary→entities）
- 质量分 ≥ 80

---

## 执行保护（内置）

每 Stage 完成后**必须**持久化到检查点文件，绝不依赖对话上下文。

| Stage | 检查点 |
|-------|--------|
| 1 | `execution-plan.md` |
| 2 | `kg-triples-raw.yaml`（含五类原始数据，大规模按子域拆分） |
| 3 | `kg-entities.yaml` + `kg-relations.yaml` + `kg-rules.yaml` + `kg-flows.yaml` + `kg-glossary.yaml` + 对应 `.md` 衍生文件 + `kg-unconnected.md` + `kg-entity-mapping.md` + `kg-synonym-groups.md` + `knowledge-graph.html` |
| 4 | `kg-validation.yaml` |
| 5 | `kg-score.yaml` |

**启用条件**：知识源 ≥ 10 文件 / 实体 ≥ 50 / ≥ 3 子域 → 任一命中即启用。
**分批**：Stage 2 按子域分批，每批工具调用 ≤ 15 次。
**Stage 内保护**：Stage 3/4 在实体 > 100、关系 > 200 或 ≥ 3 子域时，每完成 1 个子域或每新增 50 个实体/关系，必须在当前版本目录内刷新一次草稿文件（`kg-entities.yaml`、`kg-relations.yaml`、`kg-rules.yaml`、`kg-flows.yaml`、`kg-glossary.yaml`、`kg-validation.yaml`）并追加 `kg-progress.md` 进度摘要，禁止等到 Stage 结束后一次性落盘。
**上下文阈值保护**：单轮工具调用接近 15 次、输出明显变长或上下文接近上限时，先写 `kg-progress.md` 总结当前已完成子域、剩余问题和下一批计划，再继续执行。
**中断恢复**：读已有检查点 → 从未完成 Stage 继续。
**失败升级**：第1次重试 → 第2次换策略 → 第3次标记待确认 → 连续3+暂停请求用户决策。

---

## 内联决策规则

- **实体 vs 属性**：有独立 ID / 独立生命周期 / 被多个概念引用 → 实体。否则 → 属性。
- **实体类型**：`core`(有ID+生命周期) / `enum`(有限选项) / `event`(动作产物) / `role`(角色) / `process`(流程)；`noun_extension` 模式额外支持: `noun`(名词实体) / `rule`(规则类名词)
- **关系类型**：包含→`contains` | 属于→`belongs_to` | 关联→`associates` | 继承→`generalizes` | 组合/聚合 | 枚举→`枚举归属` | 层级→`层级归属` | 触发/依赖/引用/管理/前置 | 跨域依赖→`depends_on`
- **基数**：一对多→`1:N` | 一对一→`1:1` | 多对多→`N:M` | 不确定→`1:N`+待确认
- **跨域引用**：下游域使用上游域的概念时 → 直接引用上游实体 ID，建立 `depends_on` 关系。**禁止**创建 `type: 引用实体` 的影子副本。例：退款域的退款单关联交易订单 → `head=E_RF_交易退款单, relation=depends_on, tail=E_TRADE_交易订单`
- **桥接关系类型保真**：跨域桥接关系合并时，仅 `同一实体` 类型转为 `depends_on`（因影子已删除）。其他类型（`语义等价`/`子集关系`/`对齐映射`/`镜像映射`/`引用关联`/`驱动关联`/`实例关系`/`扩展映射`）**必须保留原始 relation_type**，不得一刀切转为 `depends_on`（反模式 AP009）

- **规则类型**：校验→`validation` | 约束→`constraint` | 计算→`calculation` | 权限→`permission` | 流程控制→`flow_control`
- **规则 description 三要素**：是什么 + 为什么 + 违反后果

详细速判表见 `references/extraction_guide.md`

---

## 工具脚本

`scripts/kg_validate.py`(Stage 4 自检) | `scripts/kg_to_html.py`(Stage 3 生成 `knowledge-graph.html`，依赖 `scripts/kg_html_template.html`) | `scripts/kg_to_drawio.py`(辅助导出 drawio，输入为 schema-compatible JSON) | `scripts/kg_to_markdown.py`(辅助导出 AI 上下文 Markdown，输入为 schema-compatible JSON)

---

## 文档职责与同步规则

| 文档 | 单一事实来源 |
|------|-------------|
| `SKILL.md` | 模式路由、Stage 定义、输出文件名、脚本入口、资源索引 |
| `USAGE.md` | 首次上手说明、示例对话、环境要求、常用命令镜像 |
| `CHANGELOG.md` | 完整版本历史 |
| `evaluation-report.md` | 某次评审时点的质量快照，不作为运行规范 |
| 版本目录/`kg-score.yaml` | Stage 5 评分结果（每次构建的质量快照） |
| 版本目录/`kg-quality-evaluation.md` | `noun_extension` 模式的四维评估报告（P0~P3） |

**修改顺序（必须遵守）**：
1. 工作流、输出文件名、脚本入口或资源索引发生变化时，先修改 `SKILL.md`
2. 同一提交内同步检查 `USAGE.md` 的 `2.2`、`3.1`、`5.2`、`5.3`、`5.4`
3. 涉及宿主路径、外部接口名称、平台术语的变更，必须同步扫描全部 `references/` 文件（尤其 `role-matrix.md`、`validation-rules.yaml`、`protection-config.yaml`），确保零宿主绑定残留
4. 变更落地后只在 `CHANGELOG.md` 记录完整历史；`SKILL.md` 仅保留最近关键变更摘要

---

## 资源（按需读取）

### 必读（首次执行任何模式前）

| 路径 | 何时读 |
|------|--------|
| `references/kg_schema.md` | 首次生成 or 字段不确定时 |
| `references/extraction-rules.yaml` | Stage 2 提取规则 |
| `references/anti-patterns.yaml` | 遇到问题时（含 12 条实战反模式 AP001~AP012） |

### 按模式读取

| 路径 | 适用模式 | 何时读 |
|------|---------|--------|
| `references/extraction_guide.md` | full/incremental | 复杂实体/关系判定时 |
| `references/bridge-checklist.md` | full（多域） | Stage 3 BFS 发现断连时 |
| `references/output-formats.yaml` | 全部 | Stage 2/3 输出格式 |
| `references/validation-rules.yaml` | 全部 | Stage 4 |
| `references/scoring-rubric.yaml` | 全部 | Stage 5 |
| `references/noun-extension-algorithm.md` | **noun_extension** | 三信号融合算法、阈值、四维评估、质量验收 |
| `references/protection-config.yaml` | incremental | Stage 6 |

### 按需读取（特定场景）

| 路径 | 何时读 |
|------|--------|
| `references/xwatt-extract-protocol.md` | 知识源含 XWatt 类图 URL 时 |
| `references/html-style-guide.md` | Stage 3 HTML 生成时 |
| `references/report-templates.yaml` | Stage 4/5 报告格式 |
| `references/role-matrix.md` | 查看 6 角色分工时 |
| `references/wxpay-ontology.md` | 微信支付领域提取时（领域专用） |
| `references/wxpay-kg-visual.md` | 需要可视化参考时（领域专用） |
| `references/wxpay-kg-data.md` | 术语和三元组参考（领域专用） |
| `examples/example_kg.md` | 想看 full 模式完整输出样例时 |
| `USAGE.md` | 详细使用说明 |
| `CHANGELOG.md` | 完整版本变更历史 |

---

## 常见卡壳及解法

| 卡壳场景 | 根因 | 解法 |
|---------|------|------|
| BFS 发现大量孤立节点 | 枚举值未连到父类型 | 检查每个枚举是否有 `枚举归属` 边 |
| 两个子域完全断连 | 缺少跨域桥接边 | 查 `references/bridge-checklist.md` 逐项补边 |
| 类图 MD 文本提取的边比实际少 | 人工文档遗漏 | 用结构化数据源（XWatt/代码外键）补充 |
| 同一概念重复出现为两个实体 | 多源命名不一致 | 归并为一个，记录到 `kg-entity-mapping.md` |
| 下游域创建了"引用实体"影子副本 | 误用 `type: 引用实体` + `cross_domain_ref` | 删除影子副本，关系改为 `depends_on` 引用权威实体 ID（铁律 9） |
| 交易服务类型实例全部孤立 | 父聚合根名称匹配失败（如多余空格） | 模糊匹配类图节点名，trim 后比对 |
| 生成脚本太大上下文溢出 | 数据量超500实体 | 启用分段保护，按子域分批生成 |
| 名词扩展后92%关系是噪声 | 阈值太低(0.08~0.10) + 只用文本匹配 | 三信号融合 + 阈值>=0.15 + 高频去噪；注意精度-覆盖率trade-off（AP008/AP012） |
| 桥接关系"语义等价"变成"depends_on" | 合并时一刀切转换 | 仅"同一实体"转depends_on，其余保留原类型（AP009） |
| 单个v1实体被500+名词关联 | 高频词未去噪 | Top-5%高频去噪 + 度中心性剪枝MAX_DEGREE=300（AP010） |
| 桥接relation_type与description矛盾 | 人工标注不一致 | 交叉校验，以description实际语义为准（AP011） |

---

## 协作 Skill

`drawio-diagrams`(可视化) | `xwatt-class-diagram-export`(类图) | `user-story-to-prd`(需求文档) | `usecase`(用例编写) | `personal-kb-builder-experimental`(知识库闭环，本 Skill 为其"关系网络"层) | `unified-knowledge-pipeline`(知识提取管道，提取结果可通过本 Skill 规整) | `domain-modeling`(语义骨架，约束本 Skill 的概念标准名和合法关系) | `staged-task-guard`(大规模构建时的分段执行防护) | `pua-debugging`(连续失败时的升级策略)

---

## 使用反馈

优先使用结构化提问、表单或等价交互能力收集以下反馈；若宿主环境不支持，则按相同问题顺序对话收集，驱动此 Skill 持续进化：

| 问题 | 选项 |
|------|------|
| 触发准确性：说"知识图谱""生成知识图谱"时是否触发？ | 准确触发 / 偶尔漏触发 / 偶尔误触发 / 经常不准确 |
| 执行效果：生成的实体/关系是否准确？连通率是否达标？ | 完全符合 / 基本符合 / 需人工修正 / 不符合预期 |
| 使用体验：6 个 Stage 的串联执行是否顺畅？ | 流畅 / 偶尔卡壳 / 经常卡壳 / 无法完成 |
| 综合评分 | 9-10优秀 / 7-8良好 / 5-6一般 / 1-4较差 |

收集的反馈将用于持续改进此 Skill。

---

## CHANGELOG

最近关键变更：
- **名词扩展模式 + 图推理 + 词根泛化**（v7.2.0）：三信号融合 + 高频软降权 + 图推理(Stage 4h: 5跳+枚举匹配) + 词根泛化(Stage 4i: 20条IS-A/PART-OF映射)。覆盖率从 33% → 89.5% → **100%**。详见 `references/noun-extension-algorithm.md`。
- **桥接关系类型保真**：跨域桥接合并时保留原始 relation_type（语义等价/子集关系/对齐映射等），仅"同一实体"转为 depends_on。
- **五层知识架构**（v6.0.0）：YAML 主管道从 entities+relations 扩展为五层（+ rules + flows + glossary），Stage 1 新增知识源自动分类，Stage 2 三段并行提取，Stage 3/4/5 全面支持五层产出/校验/评分
- **输入智能化**：Stage 1 按文件特征自动识别领域模型/需求文档/用例规约/代码，驱动 Stage 2 选择对应提取策略
- **跨层引用校验**：rules→entities、flows→rules、flows→entities、glossary→entities 的 ID 引用完整性作为 Stage 4 必检项和收敛条件

完整变更历史见 `CHANGELOG.md`。
