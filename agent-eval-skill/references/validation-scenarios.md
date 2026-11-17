# Skill 验证场景

> 说明：这份文档用于验证 `agent-eval-skill` 这个 skill 自身是否靠谱，不是给最终用户直接照着执行的评测工作流。

用这些场景验证这个 skill 是否真的比通用建议更强。

## 不带 Skill 时的基线缺陷

在基线测试中，通用回答容易出现这些问题：

- 先聊泛泛的评测框架，而不是先查 trace readiness
- 没有把高可恢复度的数据路径优先排到前面，也没先判断最适合当前条件的数据入口
- 标签定义和重叠边界不够具体
- 只给想法，不给 payload、label、spec 这些可复用产物
- 遇到数据缺失时，容易停在高层建议，不够可执行

这个 skill 应该显式修正这些问题。

## 场景 1：理想平台场景

输入条件：

- 有本地 agent 代码
- 有 Langfuse DB
- 有 prompt 名或 prompt 文本
- 有 tool trace
- 有 final answer

期待行为：

- 优先走可恢复度最高的数据路径；在这个场景里应优先走 Langfuse DB
- 先检查代码和 trace 结构，再讨论指标
- 合理拆出 trajectory 和 E2E
- 留下 payload、labels、output strategy 等具体产物

## 场景 2：只有 SDK / API

输入条件：

- 有本地代码
- 只有 Langfuse SDK 或 API
- 没有 DB
- observation 细节不完整

期待行为：

- 不直接阻塞
- 明确缺失字段
- 给出 reduced-scope payload 设计
- 告诉用户下次应补哪些 metadata 或 trace 字段

## 场景 3：只有导出 trace 文件

输入条件：

- 用户提供 trace 导出文件
- 没有在线 Langfuse 访问能力
- prompt 来源不完整

期待行为：

- 把 trace 文件视为 fallback 重放材料
- 缩小评测范围，而不是假装 fidelity 不变
- 仍然产出 payload 和标签草案

## 场景 4：缺 metadata

输入条件：

- 代码里能看到某些重要 runtime 信息
- trace 中没有把这些信息打出来

期待行为：

- 明确指出可观测性缺口
- 建议下次补哪些 metadata
- 仍然给出 best-effort 的当前版本设计

## 场景 5：用户只想要指导

输入条件：

- 用户不打算现在实现评测代码

期待行为：

- 停在 spec、payload、labels、output strategy
- 不强推不必要的编码工作

## 场景 6：用户准备开始构建

输入条件：

- 设计已经确认
- 用户准备开始写评测代码

期待行为：

- 输出实现 checklist
- 推荐测试优先
- 把 payload 和 labels 当成实现契约
