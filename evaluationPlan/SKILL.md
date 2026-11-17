---
name: evaluationPlan
description: 业务评测流程路由器。只负责与用户对话完成阶段判定，并路由到对应阶段执行参考；阶段细节与输出模板统一在 references 中维护。
---

## 角色定位（仅路由）

本文件不承载阶段执行细节，只做两件事：

1. 与用户对话，判定所处阶段
2. 将用户路由到对应 `references` 文件并按该文件执行

## 触发场景

当用户表达以下诉求时触发：

- 要做业务评测但不确定怎么推进
- 已有评测思路但卡在数据集构建
- 方案与数据集已完成，需要定义指标并实施

## 路由总流程（必须遵守）

1. **先读取 `evaluation_sop.png`**（使用图片读取工具加载该图），对其三段主线（阶段一/二/三）形成简要心智图，作为后续阶段判定与执行的视觉锚点；本步骤为强制项，不可跳过。
2. 加载 `references/stage_identification.md`
3. 基于该文件完成对话问诊与阶段判定
4. 按判定结果路由：
   - 阶段一 → `references/stage1_execution.md`
   - 阶段二 → `references/stage2_execution.md`
   - 阶段三 → `references/stage3_execution.md`
5. 输出当前阶段“要做的事情”时，严格以对应阶段文件为准，并对照步骤 1 中已加载的 `evaluation_sop.png` 主线进行核验

## 输出约束

- 只输出当前阶段相关内容，不跨阶段展开。
- 每轮输出必须包含：
  1) 当前阶段
  2) 判定依据
  3) 当前阶段要做的事情
  4) 下一步动作（最多 3 条）
- 禁止输出大段泛化理论或无执行价值内容。

## 规则优先级

- 阶段判定规则：以 `references/stage_identification.md` 为准
- 阶段执行内容：以 `references/stage{n}_execution.md` 为准
- 若本文件与 references 冲突，以 references 为准

## 资源索引

- 阶段判定：`references/stage_identification.md`
- 阶段一执行：`references/stage1_execution.md`
- 阶段二执行：`references/stage2_execution.md`
- 阶段三执行：`references/stage3_execution.md`
- 评测方法论配图（**必读，路由流程第 1 步加载**）：`evaluation_sop.png`

## 最小工作原则

- 先判阶段，再执行阶段内容。
- 本文件始终保持“只路由，不承载执行细节”。
