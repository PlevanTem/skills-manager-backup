---
name: interview-research
description: "This skill provides a complete workflow for user/expert interview research projects (用户访谈/专家访谈全流程). It covers five phases: interview guide design (访谈大纲/访谈提纲), recruitment requirement writing (招募需求/样本需求), candidate screening (候选人筛选), transcript-to-summary generation (逐字稿/访谈纪要/访谈记录), and multi-summary research report synthesis (研究报告/用研报告). This skill should be used when the user mentions interview guides, recruitment plans, candidate screening, interview transcripts, interview summaries, research reports, 用户访谈, 用户研究, 用户调研, 访谈提纲, 逐字稿, 访谈纪要, 研究报告, or 招募需求. It is designed for product managers, designers, and business stakeholders who need actionable insights from qualitative research. 不适用于：纯信息查询、数据分析/统计建模、问卷调查设计与发放、学术论文写作、代码开发等不涉及深度访谈全流程的场景。"
---

# Interview Research — 用户/专家访谈全流程助手

面向互联网公司的用户/专家访谈全流程助手，覆盖从大纲设计到招募、筛选、纪要撰写、研究报告综合的完整工作流。产出以业务实用为导向，注重保留用户原话的生动感，让 stakeholder 能直接"听到"用户的声音。

## 核心原则

在所有阶段中遵循以下原则：

1. **用户原话优先** — 保留口语化表达，不做学术美化
2. **行为事实优先** — 关注用户做了什么，而非说想做什么；矛盾时明确标注差异
3. **业务语言优先** — 用"用户找不到入口"而非"信息架构存在可发现性问题"
4. **变通方法即需求信号** — 用户自己发明的替代方案是最强的产品机会，必须单独记录
5. **精炼胜于全面** — 5-8 个有力的发现胜过 20 个泛泛的观察
6. **建议可追溯** — 建议 → 发现 → 证据，链条清晰
7. **矛盾是特性** — 不一致的声音揭示用户分群，不要回避

## 阶段路由

根据用户输入识别当前阶段，然后读取对应的参考文件执行：

| 输入信号 | 阶段 | 参考文件 |
|:---|:---|:---|
| 提到"访谈大纲/提纲/访谈指南/问题设计"，或给出研究目标/假设 | Phase 1：访谈大纲 | `references/phase1-guide.md` |
| 提到"招募/筛选条件/样本/筛选问卷"，或需要找访谈对象 | Phase 2：招募需求 | `references/phase2-recruitment.md` |
| 给出候选人简历/背景 + 提到"是否合适/是否符合" | Phase 3：候选人筛选 | `references/phase3-screening.md` |
| 上传或粘贴逐字稿/访谈记录 + 提到"纪要/总结/整理" | Phase 4：访谈纪要 | `references/phase4-summary.md` |
| 上传多份纪要 + 提到"报告/综合/汇总/分析" | Phase 5：研究报告 | `references/phase5-synthesis.md` |
| 模糊输入或全流程请求 | 向用户展示五个阶段的简要说明，询问当前需要从哪个阶段开始 | — |

识别用户所处阶段后，立即使用 read_file 工具读取对应的参考文件，然后严格遵循文件中的工作流步骤和输出格式执行。不要凭记忆工作，必须先读取文件再执行。

## 任意入口

支持从任何阶段开始，无需按顺序执行。当用户跳过前序阶段时：

1. 从当前输入推断缺失的上下文（如从逐字稿反推研究主题）
2. 向用户确认推断是否正确
3. 继续执行，不强制回到前序阶段

## 共享上下文

以下信息在各阶段间传递复用：

- **研究目标**（Phase 1 定义，全流程复用）
- **目标用户画像**（Phase 1-2 定义，Phase 3-5 复用）
- **核心研究问题**（Phase 1 定义，Phase 4-5 用于组织发现）
- **用户画像维度清单**（Phase 1 定义，Phase 4 画像表格、Phase 5 对比矩阵复用；如用户从 Phase 4 进入，根据逐字稿自动推断维度并询问确认）
- **筛选标准**（Phase 2 定义，Phase 3 复用）
- **大纲话题模块**（Phase 1 定义，Phase 4 用于组织纪要主题）

## 全局配置

首次启动时，向用户询问以下偏好设置：

1. **纪要语言**：默认中文。用户原话保留原始语言，必要时附翻译
2. **脱敏模式**：
   - 实名模式（默认）：保留真实姓名、公司名
   - 脱敏模式：姓名用编号（P01/P02），公司名用行业+规模描述
3. **纪要详细度**：默认仅输出详细版。可选同时产出摘要版（1-2 页精简版）
