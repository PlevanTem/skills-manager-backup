# CHANGELOG

## v6.0.0 (2026-04-10)

### Changed — 五层知识架构
- **YAML 主管道从 2 层扩展为 5 层**：entities + relations 基础上，新增 rules（规则层）、flows（流程层）、glossary（翻译层）三个主管道输出组件
- **Stage 1 新增知识源自动分类**：按文件内容特征自动识别领域模型/需求文档/用例规约/代码，标注 contributes_to 和输入完整度评估
- **Stage 2 三段并行提取**：段A（实体+关系，领域模型/类图）+ 段B（规则+流程，需求文档/用例）+ 段C（术语+映射，代码），根据 Stage 1 分类结果驱动
- **Stage 3 输出 5 个 YAML 主文件**：kg-entities.yaml、kg-relations.yaml、kg-rules.yaml、kg-flows.yaml、kg-glossary.yaml + 对应 .md 衍生文件
- **Stage 4 五层校验**：新增规则层（involvedEntities 引用、condition 非空、type 合法）、流程层（steps.ruleRef/entityRef 引用）、术语层（entityRef 引用、term 唯一）校验；新增跨层引用正确率作为收敛条件
- **Stage 5 评分扩展**：消费质量维度新增规则覆盖率和流程覆盖率（条件计入）
- **kg_validate.py 五层校验**：支持 `python3 kg_validate.py entities.yaml relations.yaml [rules.yaml] [flows.yaml] [glossary.yaml]`，缺失文件跳过对应层

### Added
- `extraction-rules.yaml`：新增 rule_business_rule、rule_business_flow、rule_glossary_entry 三组提取规则
- `output-formats.yaml`：新增 kg-rules/kg-flows/kg-glossary 的 YAML+MD 输出格式定义
- `validation-rules.yaml`：新增规则层/流程层/术语层校验规则
- `scoring-rubric.yaml`：消费质量新增规则覆盖率、流程覆盖率指标
- `protection-config.yaml`：Stage 3 检查点补充 rules/flows/glossary 文件

---

## v5.1.0 (2026-04-10)

### Fixed
- **修正六大组件幻影承诺**（P1）：SKILL.md 和 USAGE.md 原声称"六大输出组件"，但 YAML 主管道（提取规则/输出格式/验证规则/脚本）只处理 entities+relations。现已明确标注：YAML 主管道输出 entities+relations，JSON 扩展 Schema 的 glossary/businessRules/businessFlows/codeMapping 为辅助导出工具可选组件
- **清理 reference 文件宿主绑定残留**（P2）：`role-matrix.md` 去除 `avatar/业务知识/` 路径和 "Knot 业架业务知识库" 引用；`validation-rules.yaml` 去除 "Knot 知识库" 引用（v5.0.2 清理遗漏项）
- **扩展文档同步规则**（P2）：SKILL.md 文档修改顺序新增第 3 条，要求涉及宿主路径/外部接口变更时同步扫描全部 `references/` 文件
- **增强 kg_validate.py 校验**（P2）：新增同名实体唯一性检查（铁律 9）、影子实体检查（禁止 type=引用实体/cross_domain_ref）、枚举归属完整性检查（每个枚举实体 ≥1 条归属关系），校验项从 5 项提升至 8 项

---

## v5.0.3 (2026-04-07)

### Fixed
- **收敛版本历史来源**：`SKILL.md` 不再内联完整版本表，只保留最近关键变更摘要，完整编号历史统一保留在 `CHANGELOG.md`
- **新增文档同步约束**：明确 `SKILL.md` 是运行规范的单一事实来源，`USAGE.md` 作为上手说明镜像，并规定需要同步检查的章节

---

## v5.0.2 (2026-04-07)

### Fixed
- **去除宿主绑定表述**：将 `SKILL.md`、`USAGE.md`、`evaluation-report.md` 中的旧平台路径和专属占位符统一改为宿主无关的 `<skill-root>` 与通用大模型环境描述
- **收敛工具命名依赖**：将强平台语义改写为全文搜索、文件读取、结构化提问、外部接口等能力表述

---

## v5.0.1 (2026-04-07)

### Fixed
- **同步使用说明**：`USAGE.md` 对齐当前主规范，Stage 3 主输出改为 `kg-entities.yaml` + `kg-relations.yaml`，`knowledge-graph.html` 明确为必选衍生输出
- **补齐脚本依赖说明**：记录 `scripts/kg_to_html.py` 依赖 `scripts/kg_html_template.html` 页面模板，避免后续清理时误删
- **澄清辅助导出路径**：`kg_to_drawio.py` 与 `kg_to_markdown.py` 明确为 schema-compatible JSON 辅助导出工具，不直接消费 Stage 3 的 YAML 主输出
- **恢复角色速查引用**：`references/role-matrix.md` 重新作为可选索引资源保留，用于快速查看 Planner/Extractor/Generator/Validator/Scorer/Guardian 的职责分工
- **增强大规模保护**：文档层面明确 Stage 3/4 的阶段内落盘和 `kg-progress.md` 进度摘要规则

---

## v5.0.0 (2026-04-01)

### Changed
- **整合两个 Skill**：将 `knowledge-graph-generator` (v3) 和 `wxpay-knowledge-graph` (v4) 合并为统一 Skill
- 架构：v4 的 6 阶段流水线骨架 + v3 的内联决策规则 + 两者全部脚本和参考资料

### Added (from v3)
- **内联决策规则速查表**：实体 vs 属性、实体类型、关系类型、基数、规则类型的快速判定表
- **可执行脚本**：`kg_to_drawio.py`（JSON → draw.io 可视化）、`kg_to_markdown.py`（JSON → AI 上下文 Markdown）
- **完整示例**：`examples/example_kg.md`（商户/门店/订单/退款/结算 完整 JSON 输出）
- **Schema 定义**：`references/kg_schema.md`（六大组件完整字段定义）
- **提取决策指南**：`references/extraction_guide.md`（三段流水线、隐含关系识别、去重消歧）
- **规模自适应确认策略**（≤5 跳过/6-15 精简/15+ 完整清单）
- **xnoun 名词库并行查询指导**

### Kept (from v4)
- 6 阶段流水线（Planner→Extractor→Generator→Validator→Scorer→Guardian）
- 5 种执行模式（full/incremental/validate/score/query）
- 量化自检指标 + 三维评分体系
- 增量更新保护机制（检查点/回滚/并发锁/溢出保护）
- 多轮迭代收敛策略
- YAML 规则配置（extraction-rules, validation-rules, scoring-rubric 等）
- `kg_validate.py` 验证脚本
- `anti-patterns.yaml` 反模式记录

### Removed
- `knowledge-graph-generator/` 目录（已合并到本 Skill）
- `references/role-matrix.md`（角色职责已内嵌到各 Stage 描述中）

---

## v4.1.0 (2026-04-01)

### Fixed
- `SKILLmd` → `SKILL.md` 文件名修正
- 协作 Skill 引用修正（替换不存在的引用）

### Added
- `scripts/kg_validate.py`、`references/anti-patterns.yaml`、`CHANGELOG.md`

---

## v4.0.0 (2026-03)

### Changed
- 合并三个独立 Skill 为统一 6 阶段流水线
- 引入 composite pattern + 5 种执行模式
- 主文件精简至 169 行，规则外置到 10 个 reference 文件
- 新增多轮迭代收敛策略 + 三维评分体系 + 增量更新保护
