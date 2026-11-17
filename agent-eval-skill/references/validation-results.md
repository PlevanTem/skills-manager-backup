# Skill 验证结果

> 说明：这份文档记录的是 `agent-eval-skill` 这个 skill 的自测结果，用来帮助维护 skill，不是用户本地评测项目的运行结果模板。

## RED：没有 Skill 时的基线表现

在两个基线场景里，通用回答主要有这些不足：

- 更容易先谈泛化的评测框架，而不是先判断 trace readiness
- 没有先按数据可恢复度判断最该优先走的数据路径
- 标签和边界讨论偏弱
- payload 设计不够模板化
- 对数据缺失的 fallback 路径不够稳定

## GREEN：引入 Skill 后的表现

写完 skill 和参考文档后，又跑了两类验证场景。

### 场景 A：本地代码 + Langfuse DB

观察到的改善：

- 在这个场景里明确优先走 Langfuse DB 路径
- 在谈指标前先识别 agent 流程特色，再把类型当作辅助参考
- 默认拆分 trajectory 和 E2E
- 标签讨论前置到评分前
- 会主动留下模板和可复用产物

### 场景 B：本地代码 + 导出 trace 文件

观察到的改善：

- 会主动切到 reduced-scope 路径，而不是直接卡住
- 缺失字段会配平替方案
- 会显式记录 prompt 缺失和 trace 缺口
- 输出自然转向 spec / 报告型产物

## 结论

这个 skill 已经能把默认回答方向拉到预期状态：

- 更稳定的数据路径优先级意识
- 更强的 payload 和 label 纪律
- 更好的 reduced-scope fallback
- 更明确的产物导向

如果后续再扩展，建议补测：

- transfer 很重的场景
- human approval / reject 很重的场景
