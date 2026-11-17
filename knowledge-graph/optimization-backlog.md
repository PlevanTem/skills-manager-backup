# knowledge-graph Skill 优化清单

> 来源：2026-04-10 本体化审视 + 五层信息架构分析
> 初始版本：v5.1.0 → 当前版本：v6.0.0（P0/P1/P2 已全部实施）

---

## 一、已完成的修复（v5.1.0）

| # | 问题 | 修复内容 | 影响文件 |
|---|------|---------|---------|
| ✅ 1 | 六大组件幻影承诺（P1） | header 修正为"YAML 主管道 2 + JSON 扩展 4"的诚实声明 | `SKILL.md`、`USAGE.md` |
| ✅ 2 | reference 文件宿主绑定残留（P2） | 去除 `avatar/` 路径和 `Knot` 引用 | `role-matrix.md`、`validation-rules.yaml` |
| ✅ 3 | 文档同步规则覆盖不全（P2） | 新增第 3 条：references/ 文件同步扫描条款 | `SKILL.md` |
| ✅ 4 | kg_validate.py 校验不足（P2） | 新增同名唯一性、影子实体、枚举归属 3 项检查（5→8 项） | `kg_validate.py` |

---

## 二、待实施优化（按优先级排序）

### P0 — 五层知识架构：把断开的管道接回来

> 核心问题：`kg_schema.md` 和 `extraction_guide.md` 已设计好五层 Schema 和提取策略，但 YAML 主管道只串联了 entities + relations 两层。
> 改造本质：不是新设计，是把已有设计接回主管道。

#### P0-1：规则层回归主管道

| 项目 | 内容 |
|------|------|
| **问题** | businessRules 有完整 Schema（`kg_schema.md`）和提取信号词（`extraction_guide.md` 段C），但主管道不产出 |
| **改造范围** | Stage 2 增加规则提取 → Stage 3 输出 `kg-rules.yaml` → Stage 4 校验规则引用有效性 → Stage 5 纳入评分 |
| **输出物** | `kg-rules.yaml`（主输出）、`kg-rules.md`（衍生表格） |
| **校验项** | involvedEntities 中的实体 ID 必须存在；condition/action 非空；type 为合法枚举值 |
| **输入要求** | 需求文档/PRD 或用例规约（含"不能超过/必须/只有...才能"等信号词的文档） |

#### P0-2：流程层回归主管道

| 项目 | 内容 |
|------|------|
| **问题** | businessFlows 有完整 Schema 和提取策略，但主管道不产出 |
| **改造范围** | Stage 2 增加流程提取 → Stage 3 输出 `kg-flows.yaml` → Stage 4 校验 steps.ruleRef/entityRef 引用有效性 → Stage 5 纳入评分 |
| **输出物** | `kg-flows.yaml`（主输出）、`kg-flows.md`（衍生表格） |
| **校验项** | involvedEntities 中的实体 ID 必须存在；steps.ruleRef 引用的规则 ID 必须存在于 `kg-rules.yaml`；steps 有序且非空 |
| **输入要求** | 用例规约或含流程描述的需求文档（含"第一步...第二步/先...然后...最后"等信号词的文档） |

#### P0-3：术语层回归主管道

| 项目 | 内容 |
|------|------|
| **问题** | glossary 有 Schema 定义，`extraction_guide.md` 说"在识别实体时顺带完成"，但主管道不产出 |
| **改造范围** | Stage 2 从实体 enName/synonyms 和代码扫描中自动生成术语 → Stage 3 输出 `kg-glossary.yaml` → Stage 4 校验 entityRef 有效性 |
| **输出物** | `kg-glossary.yaml`（主输出）、`kg-glossary.md`（衍生表格） |
| **校验项** | entityRef 引用的实体 ID 必须存在；term 非空且无重复 |
| **输入要求** | 代码仓库（最佳）；无代码时从实体 enName+synonyms 降级自动生成 |

---

### P1 — 信息准确性：强化语义校验

> 核心问题：当前校验只检查结构正确性（引用存在、ID 唯一），不检查语义正确性（方向、约束、描述质量）。

#### P1-1：关系 domain/range 约束

| 项目 | 内容 |
|------|------|
| **问题** | 12 种关系类型只定义了名称和信号词，没有约束"谁能连谁"。`交易订单 contains 商户管理员` 语义荒谬但不会被拦截 |
| **改造** | 在 `extraction-rules.yaml` 或新文件中定义每种关系的 domain（允许的头实体类型集合）和 range（允许的尾实体类型集合） |
| **校验** | `kg_validate.py` 新增 domain/range 违规检查，违规报 WARNING |

#### P1-2：实体关系字段补全

| 项目 | 内容 |
|------|------|
| **问题** | `kg-entities.yaml` 的 codeMapping 和 stateTransitions 字段 Schema 已定义但实际常缺失；`kg-relations.yaml` 缺 dataPath 和 codeEvidence |
| **改造** | Stage 2 有代码仓库时，按 `extraction_guide.md` 的"代码映射查找策略"并行搜索填充 codeMapping；有数据库 DDL 时提取 dataPath |
| **校验** | 有代码仓库时，core 类型实体若无 codeMapping 报 WARNING |

#### P1-3：description 语义质量检查

| 项目 | 内容 |
|------|------|
| **问题** | 铁律 3 要求 description 写"是什么+为什么+角色"，但只有 ≥10 字的长度检查，无语义质量校验。`anti-patterns.yaml` AP001 已识别此问题但无机器拦截 |
| **改造** | `kg_validate.py` 对 core 类型实体的 description 检查：长度 ≥ 30 字 + 不能只是名词库定义的复制（匹配名词库原文占比 > 80% 则报 WARNING） |

---

### P2 — 输入智能化：自动分类知识源

> 核心问题：Stage 1 只按"文件数/条目数"盘点知识源，不区分文件类型，导致 Stage 2 只能用统一策略提取，遗漏规则和流程。

#### P2-1：Stage 1 知识源自动分类

| 项目 | 内容 |
|------|------|
| **问题** | 所有知识源文件一视同仁，不区分领域模型、需求文档、用例规约、代码文件 |
| **改造** | Stage 1 扫描后自动分类每个文件，标注 `contributes_to: [entities, relations, rules, flows, glossary]` |
| **分类策略** | 按文件名模式 + 内容信号词（含"聚合根/值对象"→ 领域模型；含"必须/不能超过"→ 需求文档；含"主成功路径/前置条件"→ 用例规约；`.cpp/.py/.proto` → 代码） |
| **输出** | `execution-plan.md` 新增 `source_classification` 段 |

#### P2-2：Stage 2 按分类选择提取策略

| 项目 | 内容 |
|------|------|
| **问题** | Stage 2 对所有文件用同一套实体+关系提取策略 |
| **改造** | 根据 Stage 1 的分类结果：领域模型 → 段A+B（实体+关系）；需求文档 → 段C（规则+流程）+ 段A（补充实体）；用例规约 → 段C（流程+规则）；代码 → 术语+映射 |

#### P2-3：输入完整度提示

| 项目 | 内容 |
|------|------|
| **问题** | 用户只提供领域模型文档时，Skill 默默产出不完整的图谱，用户不知道还缺什么 |
| **改造** | Stage 1 规划完成后，根据已有输入类型输出"产出预估"和"建议补充的输入源" |

---

### P2 — 脚本与工具增强

#### P2-4：kg_validate.py 支持五层校验

| 项目 | 内容 |
|------|------|
| **当前** | 只校验 entities + relations（8 项检查） |
| **改造** | 新增 rules 校验（involvedEntities 引用、condition 非空）、flows 校验（steps.ruleRef 引用、entityRef 引用）、glossary 校验（entityRef 引用、term 唯一） |
| **调用方式** | `python3 kg_validate.py <entities.yaml> <relations.yaml> [rules.yaml] [flows.yaml] [glossary.yaml]`，缺失文件跳过对应检查 |

#### P2-5：kg_to_html.py 可视化增强

| 项目 | 内容 |
|------|------|
| **当前** | 只可视化 entities + relations |
| **改造** | 节点点击详情面板增加"关联规则"和"参与流程"列表（从 rules.involvedEntities 和 flows.involvedEntities 反查） |

---

### P3 — 远期增强

#### P3-1：规则间逻辑一致性检查

| 项目 | 内容 |
|------|------|
| **问题** | 约束同一实体的多条规则可能矛盾，当前无检测机制 |
| **改造** | 同 involvedEntities 的规则组内，检测 condition 是否存在逻辑冲突（同一字段的 ≤ 和 ≥ 约束是否自洽） |

#### P3-2：关系方向/基数合理性校验

| 项目 | 内容 |
|------|------|
| **问题** | `anti-patterns.yaml` AP005 已识别"关系方向凭感觉"但无机器校验 |
| **改造** | 参照 `extraction_guide.md` 的方向约定表，检查常见方向错误（如 部分 contains 整体） |

#### P3-3：YAML→JSON 桥接

| 项目 | 内容 |
|------|------|
| **问题** | 辅助导出工具（`kg_to_drawio.py`、`kg_to_markdown.py`）需要 JSON 输入，但主管道产出 YAML |
| **改造** | 补一条 YAML→JSON 转换脚本或在辅助导出工具中内置 YAML 读取能力 |

---

## 三、改造依赖关系

```
P0-1 (规则层) ──────────────┐
P0-2 (流程层) ──┬── 依赖 ──→ P0-1（flows.steps.ruleRef 引用 rules）
P0-3 (术语层) ──┘            │
        ↓                    ↓
P2-4 (五层校验脚本) ←── 依赖全部 P0
P2-5 (可视化增强)   ←── 依赖 P0-1 + P0-2
        ↓
P1-1 (domain/range) ←── 可独立实施
P1-2 (字段补全)     ←── 可独立实施
P1-3 (描述质量)     ←── 可独立实施
        ↓
P2-1 (输入分类)     ←── 依赖 P0（分类结果决定提取策略）
P2-2 (分类提取)     ←── 依赖 P2-1
P2-3 (完整度提示)   ←── 依赖 P2-1
        ↓
P3-* (远期增强)     ←── 依赖 P0 全部完成
```

**建议实施顺序**：P0-1 → P0-2 → P0-3 → P2-4 → P1-1 → P1-2 → P2-1 → P2-2 → 其余

---

## 四、本体化三维度评估（改造前后对比）

| 维度 | 改造前 | P0 完成后 | 全部完成后 |
|------|--------|----------|----------|
| **信息完整**（能覆盖业务问题分析） | ≈ 40% | ≈ 85% | ≈ 95% |
| **表述清晰**（机器+人可理解） | ≈ 60% | ≈ 75% | ≈ 90% |
| **信息准确**（推理可信赖） | ≈ 55% | ≈ 65% | ≈ 85% |

---

## 五、涉及修改的文件清单

| 文件 | P0 改造 | P1 改造 | P2 改造 |
|------|---------|---------|---------|
| `SKILL.md` | Stage 2/3/4/5 补充 rules/flows/glossary 环节 | — | Stage 1 输入分类 |
| `USAGE.md` | 同步更新输出文件清单和使用说明 | — | 同步更新 |
| `references/extraction-rules.yaml` | 补充 rules/flows 提取规则 | domain/range 约束定义 | — |
| `references/output-formats.yaml` | 新增 rules/flows/glossary 输出格式 | — | — |
| `references/validation-rules.yaml` | 新增 rules/flows/glossary 校验规则 | — | — |
| `references/scoring-rubric.yaml` | 评分体系纳入 rules/flows/glossary 覆盖率 | — | — |
| `references/protection-config.yaml` | 检查点新增 rules/flows/glossary 文件 | — | — |
| `scripts/kg_validate.py` | 新增 rules/flows/glossary 校验 | domain/range + description 质量 | — |
| `scripts/kg_to_html.py` | — | — | 详情面板增加规则/流程 |
| `CHANGELOG.md` | 记录 v6.0.0 | 记录增量版本 | 记录增量版本 |
