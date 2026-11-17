# 09 端到端场景示例（按功能点）

本章给出覆盖全部功能点的端到端示例。每个场景都是一条可独立运行的最小链路；命令中的
`<A>`/`<D>`/`<M>`/`<P>`/`<E>` 分别代表 Agent / 数据集 / 指标方案 / 评测方案 / 评测运行的 id。
以下命令默认 `--base-url http://127.0.0.1:8080`（可省，走默认值或环境变量 `TRPC_AGENT_EVAL_BACKEND_URL`）。

## 通用前置（运维与探查）

```bash
bash scripts/install.sh                         # 安装发布包（已装则跳过）
bash scripts/serve.sh                           # 启动前后端（已运行则复用）
# 若业务需要远程访问 WebUI，Agent 应主动开放并提供前端地址:
# BACKEND_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 bash scripts/serve.sh
# PUBLIC_HOST=<业务可访问IP或域名> BACKEND_HOST=0.0.0.0 FRONTEND_HOST=0.0.0.0 bash scripts/serve.sh
python3 scripts/doctor.py                        # 健康检查 + 已有对象清单（防重复创建）
python3 scripts/discover.py                      # 探查能力：版本/指标/模式/runtime/模型 Profile
python3 scripts/list_resources.py --type agents  # 查已有对象 id/name 以便绑定
python3 scripts/metric_catalog.py --mode cli     # 选指标前先按 mode 查可用集与依赖
```

## 功能点覆盖矩阵

| 功能点 | 覆盖场景 |
|--------|----------|
| Agent — http 黑盒 | A |
| Agent — cli（arg_mode：stdin/append/placeholder） | B |
| Agent — cli/http + output_protocol（claudecode/codex） | C |
| Agent — 系统内置 llm（含自定义工具） | D |
| Agent — SDK 接入（直接加载 root_agent / Runner） | P |
| Agent — trace 离线 | G、O |
| Agent — managed 托管（worker） | N |
| 探针 probe / 创建自检 / mode 一致性校验 | A、B、N |
| 指标 — final_response_avg_score（全等/包含/正则/JSON） | A |
| 指标 — tool_trajectory_avg_score（顺序/子集/覆盖） | C |
| 指标 — final_behavior_avg_score（行为检查脚本） | H |
| 指标 — llm_final_response | A、D |
| 指标 — llm_rubric_response | D、E |
| 指标 — llm_rubric_critic（严格对齐参考） | E |
| 指标 — llm_rubric_reference_critic（宽松匹配参考） | E |
| 指标 — llm_rubric_knowledge_recall | F |
| 指标 — llm_hallucinations | G |
| 指标 — llm_final_behavior（裁判带工具核实） | H |
| 指标 — llm_judge_template（模板裁判 + 响应解析） | I |
| 裁判 — 内置 judge_model | D、E、F、G |
| 裁判 — 外部 call_judge（指向已建 Agent） | J |
| 裁判 — SDK Agent 作为 call_judge | P、J |
| 裁判 — 多裁判聚合（judge_models/call_judges + aggregator） | J |
| 数据集 — empty + add_case | A |
| 数据集 — 上传 .evalset.json | C、E、F、G、K |
| 数据集 — SDK 普通用例 + trace 混合集 | P |
| 数据集 — 路径登记（path） | L |
| 数据集 — 任意平台 trace 转 EvalSet | Q |
| 数据集 — Langfuse 导入 | L |
| 数据集 — 历史评测运行导出 | L、O |
| 数据集 — 多轮 / 模拟用户 / session_input / context_messages | K |
| 数据集 — grounding（tool_uses + tool_responses） | G |
| 可注册脚本 — 行为检查 | H |
| 可注册脚本 — 自定义 Agent 工具 | D |
| 可注册脚本 — 响应解析器 | I |
| 配置 — 命名密钥 set_secret | A |
| 配置 — 模型 Profile set_model | D、E、F、G |
| 配置 — 工作区环境变量 set_env_var | B |
| 运行 — 方案发起 / 直接发起 | A / M |
| 运行 — num_runs + pass@k / pass^k | A、M |
| 运行 — 批量 batch-run | M |
| 运行 — 取消 cancel | M |
| 运行 — 发起前预检 + 成本预览 | A、M |
| 结果 — 状态 / SSE 进度 / result / report / 明细 | A |
| 回归 — 历史 run 导出为 trace 集再评 | O |
| 迁移 — 已有 SDK 评测接入 WebUI | P |
| 迁移 — 任意 trace / JSONL / OTel / OpenInference 转 WebUI 数据集 | Q |

---

## 场景 A：HTTP 黑盒 + 规则判回复（核心闭环）

适用：被测对象是 HTTP 服务，期望答案可用规则比对（全等 / 包含 / 正则 / JSON）。不消耗模型额度。

```bash
python3 scripts/set_secret.py --name MY_TOKEN                       # 由用户录入 token
# 编辑 templates/agent/http.json：url / body_template(含 ${QUERY}) / response_path / headers(可用 ${SECRET:MY_TOKEN})
python3 scripts/probe_agent.py --mode http --config @templates/agent/http.json
python3 scripts/create_agent.py --name svc --mode http --config @templates/agent/http.json   # 创建后自动探针
python3 scripts/create_dataset.py --source empty --name 冒烟集
python3 scripts/add_case.py --dataset-id <D> --user-text "上海天气" --expected-output "晴"   # 包含匹配
python3 scripts/create_metric.py --source empty --name 规则判 --definition-template final_response_avg_score --for-mode http
python3 scripts/create_plan.py --name 冒烟方案 --agent-id <A> --dataset-id <D> --metric-config-id <M> --num-runs 3 --pass-k 2
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized        # 仅在用户授权后；发起前打印成本预览
python3 scripts/get_result.py --id <E> --watch --result-out r.json --report-out r.html
```

- 模板 `final_response_avg_score.json` 用 `text.match=contains`（若整体留空 criterion，后端默认全文精确匹配）；改 `exact`/`regex` 或并用 `json` 见 [04](04-metrics.md)。
- `num_runs=3 pass_k=2` 即每用例跑 3 次、按 pass@k=2 口径判稳定性；结果含 `pass_at_k`/`pass_hat_k`。

## 场景 B：CLI 黑盒（三种 arg_mode）+ 工作区环境变量

适用：被测对象是本地命令行程序。`arg_mode` 决定用户输入如何传入子进程。

```bash
python3 scripts/set_env_var.py --name CODEBUDDY_API_KEY            # 由用户录入；运行时注入子进程 env
# stdin（默认）：query 经标准输入传入（--config 接受内联 JSON 或 @文件）
python3 scripts/probe_agent.py --mode cli --config '{"command":["my-agent"],"arg_mode":"stdin","cwd":"/abs/work"}'
# append：query 追加为末尾参数
python3 scripts/create_agent.py --name cli-append --mode cli --config '{"command":["my-agent","--once"],"arg_mode":"append"}'
# placeholder：command 为单条文本且含 ${QUERY}，经 bash -lc 执行
python3 scripts/create_agent.py --name cli-ph --mode cli --config '{"command":["my-agent -q \"${QUERY}\""],"arg_mode":"placeholder"}'
```

- 子进程 env 合并顺序：`os.environ` < 工作区环境变量 < Agent `config.env`（后者覆盖前者）。
- cli 评测无超时；`cwd` 必须是已存在的绝对路径。

## 场景 C：CLI/HTTP + 输出协议解锁工具轨迹

适用：被测对象按 ClaudeCode / Codex 的 JSON(L) 流输出，需评测工具调用轨迹。

```bash
# 模板 cli.claudecode.json / cli.codex.json，先把 cwd 改为真实绝对路径
python3 scripts/create_agent.py --name claude --mode cli --config @my_cli_cc.json   # config 含 output_protocol:"claudecode"
python3 scripts/metric_catalog.py --mode cli --output-protocol claudecode           # 确认 tool_trajectory_avg_score 已解锁
python3 scripts/create_metric.py --source empty --name 轨迹 --definition-template tool_trajectory_avg_score --for-mode cli --output-protocol claudecode
# 数据集需含期望 tool_uses（add_case 无对应字段）→ 用 --case JSON 或上传完整 evalset
python3 scripts/create_dataset.py --source upload --name 轨迹集 --file ./traj.evalset.json
python3 scripts/create_plan.py --name 轨迹方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

- `tool_trajectory` 支持 `order_sensitive`（按序）、`subset_matching`（允许多调但期望项须命中）、`overrides`（按工具名覆盖比对规则），见 [04](04-metrics.md)。

## 场景 D：系统内置 llm Agent + 自定义工具 + 语义判回复

适用：让系统直接用模型驱动一个带工具的 Agent，并用 LLM 裁判判回复质量。

```bash
python3 scripts/set_model.py --name my_judge --model-name <model> --base-url-model <endpoint>   # api_key getpass 录入
python3 scripts/create_agent_tool.py --print-template --name my_search                          # 查看工具脚本骨架
python3 scripts/create_agent_tool.py --name my_search --script-file ./my_search.py              # 登记自定义工具
# 编辑 templates/agent/llm.json：model_profile_id=my_model、tools=["my_search","read"]、instruction
python3 scripts/create_agent.py --name builtin --mode llm --config @my_llm.json
python3 scripts/create_metric.py --source empty --name 语义判 --definition-template llm_final_response --for-mode llm
# 把指标 JSON 里的 ${MODEL:glm_flash} 占位符替换为你的裁判 Profile（如 ${MODEL:my_judge}）
python3 scripts/create_dataset.py --source empty --name 问答集
python3 scripts/add_case.py --dataset-id <D> --user-text "解释什么是 tRPC" --expected-output "一个 RPC 框架"
python3 scripts/create_plan.py --name 内置方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

- 内置工具 `read`/`bash`/`grep`/`glob` 可直接写入 `tools`，无需登记；自定义工具进程内执行（无沙箱），见 [07](07-scripts-registry.md)。

## 场景 E：rubric 家族（多维 / 严格对齐 / 宽松匹配）

适用：同一回复需按多条标准打分，或区分「必须严格对齐参考」与「语义达标即可」。

```bash
python3 scripts/set_model.py --name my_judge --model-name <model> --base-url-model <endpoint>
python3 scripts/create_dataset.py --source upload --name rubric集 --file ./set.evalset.json   # 用例含 expected_output 作参考
# 多维打分：逐条 rubric 给分
python3 scripts/create_metric.py --source empty --name 多维 --definition-template llm_rubric_response --for-mode llm
# 严格对齐参考（事实型，漏答/错答/偏离均不通过）
python3 scripts/create_metric.py --source empty --name 严格 --definition-template llm_rubric_critic --for-mode llm
# 宽松匹配参考（创作/对话型，语义等价可通过）
python3 scripts/create_metric.py --source empty --name 宽松 --definition-template llm_rubric_reference_critic --for-mode llm
# 三个指标分别建方案发起，或合并到一个指标方案的 definition 数组里一次评
```

- `llm_rubric_critic` 与 `llm_rubric_reference_critic` **都需要参考答案**，区别是严格 vs 宽松（名称反直觉），以 `metric_catalog.py` 的 `when_to_use` 为准。

## 场景 F：知识召回（检索是否覆盖关键事实）

适用：Agent 先检索再回答，需核验「检索到的内容是否覆盖回答该用到的关键事实」。

```bash
python3 scripts/set_model.py --name my_judge --model-name <model> --base-url-model <endpoint>
# 被测须能记录检索过程：内置 llm 带检索工具，或 trace 回放，或 HTTP/CLI 实跑并记录
python3 scripts/create_agent.py --name kb --mode llm --config @my_llm_with_search.json
python3 scripts/create_metric.py --source empty --name 知识召回 --definition-template llm_rubric_knowledge_recall --for-mode llm
# 指标 criterion.llmJudge.knowledge_tool_names 默认 ["knowledge_search"]，按实际检索工具名调整
python3 scripts/create_dataset.py --source upload --name 召回集 --file ./recall.evalset.json
python3 scripts/create_plan.py --name 召回方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

## 场景 G：幻觉检测（trace 离线，grounding 逐句核验）

适用：核验回复是否「编造」——逐句对照 Agent 实际工具调用与返回判断是否有据。

```bash
# actual_conversation 必含 tool_uses + tool_responses → 必须上传完整 evalset
python3 scripts/create_dataset.py --source upload --name 幻觉集 --file templates/dataset/hallucination.evalset.json
python3 scripts/create_agent.py --name replay --mode trace                       # trace 无 config、无探针
python3 scripts/set_model.py --name my_judge --model-name <model> --base-url-model <endpoint>
python3 scripts/create_metric.py --source empty --name 幻觉 --definition-template llm_hallucinations --for-mode trace
python3 scripts/create_plan.py --name 幻觉方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

- 黑盒 http/cli 若配 `output_protocol`，也能产生 grounding 并实跑该指标（见 [04](04-metrics.md) 门控表）。

## 场景 H：行为校验（确定性脚本 + 裁判式核实）

适用：不仅看文字回复，还要确认 Agent「真的做了事」。两种手段：

```bash
# 手段一：确定性行为检查脚本（不调 LLM）
python3 scripts/create_behavior_check.py --print-template --name check_order_created   # 查看骨架（入参=用户输入文本）
python3 scripts/create_behavior_check.py --name check_order_created --script-file ./check_order_created.py --description "校验下单成功"
python3 scripts/create_metric.py --source empty --name 行为 --definition-template final_behavior_avg_score --for-mode cli
# 指标 criterion.finalBehavior.allowed_matches 改为 ["check_order_created"]；
# 数据集 expected invocation 用 final_behavior_match / final_behavior_matches 引用该函数名

# 手段二：裁判带工具在环境里核实（调 LLM）
python3 scripts/create_metric.py --source empty --name 裁判核实 --definition-template llm_final_behavior --for-mode cli
# 指标 criterion.llmJudge.tool_instruction 告诉裁判如何用工具核验
```

- 行为检查脚本契约 `def {name}(user_content: str) -> tuple[bool, str]`，入参是**用户输入文本**而非 Agent 回复，见 [07](07-scripts-registry.md)。

## 场景 I：自定义模板裁判 + 响应解析

适用：内置裁判都不合适，需自写评测 prompt 并指定如何从裁判回复中读出分数。

```bash
python3 scripts/create_response_scorer.py --print-template --name contains_pass    # 查看骨架
python3 scripts/create_response_scorer.py --name contains_pass --script-file ./contains_pass.py
python3 scripts/create_metric.py --source empty --name 模板裁判 --definition-template llm_judge_template --for-mode cli
# 指标 criterion.llmJudge.template.prompt 用 {user_input}/{actual_response}/{expected_response} 占位符；
# template.response_scorer_name 设为 "contains_pass"（或内置 single_score / final_response / rubric_scores）
```

## 场景 J：外部裁判 call_judge 与多裁判聚合

适用：用一个**已创建的 Agent**（http/cli/llm/managed/sdk，不能是 trace）当裁判，或同时用多个裁判聚合。

```bash
# 先建好充当裁判的 Agent（示例：一个内置 llm 裁判 Agent），拿到其 id 作为 <judge_agent_id>
python3 scripts/create_agent.py --name judge-agent --mode llm --config @judge_llm.json
# 单外部裁判：模板 llm_call_judge.json，把 <judge_agent_id> 换成真实 id
python3 scripts/create_metric.py --source empty --name 外部裁判 --definition-template llm_call_judge --for-mode cli
# 多裁判聚合：在指标 JSON 内同时给 judge_models:[...] 与 call_judges:[{"name":id},...]，
#   并设 models_aggregator（all_pass/any_pass/majority_pass/avg/weighted_avg/weighted_majority）
```

- 混用内置与外部裁判时两边都必须用**列表形式**（`judge_models` + `call_judges`）；加权类聚合需各 `weight` 之和 > 0，见 [04](04-metrics.md)。

## 场景 K：多轮对话（静态 / 动态模拟用户 / 会话状态）

适用：评测多轮交互；动态模拟用户由 LLM 扮演用户即时生成多轮。

```bash
# 静态多轮（参考答案逐轮给定，普遍支持）
python3 scripts/create_dataset.py --source upload --name 多轮集 --file templates/dataset/multiturn.evalset.json
# 动态模拟用户（conversation_scenario）——依赖后端实现，部分版本未提供，先确认
python3 scripts/discover.py                       # 确认运行时是否支持模拟用户
python3 scripts/set_model.py --name sim_user --model-name <model> --base-url-model <endpoint>
python3 scripts/create_dataset.py --source upload --name 模拟用户集 --file templates/dataset/user_sim.evalset.json
```

- 预置初始会话状态用 `session_input.state`；每轮注入上下文用 `context_messages`——这两者及 `conversation_scenario`、`tool_responses` 都**仅支持上传完整 evalset**（`add_case` 不支持），见 [03](03-datasets.md)。

## 场景 L：数据集来源全集（path / Langfuse / 运行导出）

适用：复用服务端已有大文件、从线上 trace 拉取、或把历史评测转成数据集。

```bash
# 路径登记（服务端已存在的绝对路径，不复制；目标机须可读该路径）
python3 scripts/create_dataset.py --source path --name 线上集 --source-path /abs/data/x.evalset.json
# Langfuse 导入（先登记 public/secret key 为命名密钥）
python3 scripts/set_secret.py --name LF_PUBLIC
python3 scripts/set_secret.py --name LF_SECRET
#   字段较多，直接调 API（见 03-datasets.md「Langfuse 导入要点」）：
curl -s -X POST http://127.0.0.1:8080/api/datasets/import/langfuse \
  -H 'Content-Type: application/json' \
  -d '{"name":"lf集","host":"https://cloud.langfuse.com","public_key_secret":"LF_PUBLIC","secret_key_secret":"LF_SECRET","fetch_mode":"query","limit":50}'
# 历史评测运行导出（见场景 O）
python3 scripts/export_trace_dataset.py --evaluation-id <E1> <E2> --name-prefix 回归
```

## 场景 M：稳定性、直接发起、批量与取消

适用：测稳定性（pass@k / pass^k）、临时直接发起、一次跑多方案、以及中途取消。

```bash
# 直接发起（不建方案；pass_k 默认=num_runs）——同样需要授权，且发起前预检+预览
python3 scripts/run_eval.py --agent-id <A> --dataset-id <D> --metric-config-id <M> --num-runs 5 --i-am-authorized
#   结果中 pass_at_k=至少一次通过的口径（看上限）；pass_hat_k=k 次全通过的口径（看稳定性）
# 批量发起多个方案（API；plan_ids ≤10）
curl -s -X POST http://127.0.0.1:8080/api/evaluation-plans/batch-run \
  -H 'Content-Type: application/json' -d '{"plan_ids":["<P1>","<P2>"]}'
# 取消进行中的评测（仅 pending/running 可取消）
curl -s -X POST http://127.0.0.1:8080/api/evaluations/<E>/cancel
```

## 场景 N：托管 Agent（managed，远程 worker 执行 ClaudeCode/Codex/Hermes）

适用：被测是 ClaudeCode / Codex / Hermes 这类 provider CLI，由独立 worker 执行。

```bash
# 前置：后端与 worker 配同一 TRPC_AGENT_EVAL_WORKER_TOKEN；worker 在线并注册 runtime
#   TRPC_AGENT_EVAL_WORKER_TOKEN=<token> python3 -m trpc_agent_eval_worker.cli connect --server-url http://127.0.0.1:8080
python3 scripts/discover.py                          # 查看「托管 Agent runtime」，获取 runtime_id / provider
# 编辑 templates/agent/managed.json：provider / runtime_id / cwd(worker 机器上的绝对路径) / env_vars(已登记的变量名)
python3 scripts/probe_agent.py --mode managed --config @templates/agent/managed.json
python3 scripts/create_agent.py --name 托管codex --mode managed --config @templates/agent/managed.json
python3 scripts/create_dataset.py --source upload --name 集 --file ./set.evalset.json
python3 scripts/create_metric.py --source empty --name 语义判 --definition-template llm_final_response --for-mode managed
python3 scripts/create_plan.py --name 托管方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

- managed **不支持** `output_protocol`（由 provider 原生上报工具事件，天然可用全部指标）；`env_vars` 填**已登记的变量名**而非明文，见 [02](02-agents.md)。

## 场景 O：把历史评测导出为回归集

适用：将已完成的评测运行固化为可复跑的 trace 数据集，用于回归。

```bash
python3 scripts/export_trace_dataset.py --evaluation-id <E1> <E2> --name-prefix 回归
# 得到 eval_mode=trace 数据集（保留真实输出 + tool_uses + tool_responses）
python3 scripts/create_agent.py --name replay --mode trace
python3 scripts/create_plan.py --name 回归方案 --agent-id <A> --dataset-id <D> --metric-config-id <M>
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
```

## 场景 P：把已有 SDK 评测迁移到 WebUI（重点）

适用：用户已经有 Python SDK Agent 或 SDK 评测示例，例如依赖里出现 `trpc-agent-sdk` / `trpc-agent-py`，
目录里有 `agent.py` / `root_agent` / `AgentEvaluator.evaluate(agent_module="...")` /
`.evalset.json` / metric 或 judge 配置，希望不改核心 Agent、不包装 HTTP/CLI，直接在 WebUI 里创建
Agent、数据集、指标方案、评测方案，并看到运行记录与 HTML 报告。

**交互原则：用户动嘴，Agent 代迁移。** 用户只需要回答路径、确认候选和录入敏感值；Agent 必须负责读文件、
推断映射、解释选择、调用脚本。不要要求用户复制执行命令。

推荐路线：评测层统一使用 `trpc-agent-self-evolution`。如果用户同意，Agent 直接修改依赖和 pytest 评测入口并验证；
这样用户既保留原来的 pytest 运行方式，又能把同一个 Agent / 数据集 / 指标迁到 WebUI。注意：`trpc-agent-py`
或 `trpc-agent-sdk` 可能仍是业务 Agent 的运行时依赖，若 `root_agent` 代码 import `trpc_agent_sdk`，不要盲删。

### 迁移提问顺序

1. **问项目位置**：请用户给已有 SDK 评测或 Agent 示例目录。拿到路径后，Agent 读取目录结构，寻找：
   `agent.py`、`agent/`、`src/`、`root_agent`、`Runner`、`AgentEvaluator.evaluate(agent_module=...)`、
   `trpc-agent-sdk`、`trpc-agent-py`、`.evalset.json`、`.metric.json`、README、评测脚本。
   优先由 Agent 代执行 `inspect_sdk_migration.py <目录>` 生成候选。
2. **问 Agent 映射确认**：Agent 给出候选并让用户确认：
   - `Agent 项目目录(cwd)`：服务端机器上的绝对路径。
   - `Agent 所在模块(module)`：Python import 路径，如 `agent`、`agent.agent`。优先使用 `inspect_sdk_migration.py`
     输出的 `recommended_agent_config`；旧 SDK 评测脚本里的 `agent_module` 值只作为交叉验证线索。
   - `Agent 变量名(agent_var)`：默认 `root_agent`；只有源码里不是这个名字才问用户指定。
3. **问环境变量**：如果源码出现 `TRPC_AGENT_BASE_URL`、`TRPC_AGENT_API_KEY`、`TRPC_AGENT_MODEL` 或其他配置名，
   询问是否登记为工作区环境变量。用户本人通过 `set_env_var.py` 录入值；Agent 只把变量名填到 `env_vars`。
4. **问数据集迁移**：如果已有 `.evalset.json`，优先上传或路径登记；如果评测脚本动态构造 cases，Agent 先抽取
   1–3 条最小冒烟用例给用户确认，再创建数据集。若同时存在普通用例和 trace，可保留为混合集并用 `mode=sdk`。
5. **问指标迁移**：运行 `metric_catalog.py --mode sdk` 后，只展示 SDK 可用指标。根据原 SDK 评测里的 metric / rubric /
   judge 配置，推荐对应 WebUI 指标模板。
6. **问是否升级评测 SDK（推荐）**：告诉用户推荐用 `trpc-agent-self-evolution` 承接评测层。选项：
   - 同意升级并由 Agent 修改验证：Agent 修改依赖/测试代码，跑原 pytest，确认旧入口仍可用。
   - 暂不升级，只做 WebUI SDK 接入：Agent 不改用户项目，只创建 WebUI 对象。
   - 先只分析：Agent 只输出候选映射与风险点。
7. **用户同意升级时的代执行步骤**：Agent 定位 `pyproject.toml`、`requirements*.txt`、`setup.py`、`setup.cfg`、pytest 文件；
   补充或替换评测层依赖为 `trpc-agent-self-evolution[all]`（按项目依赖管理风格落地）；把评测代码迁到
   `from trpc_agent_self_evolution import AgentEvaluator` 等当前 API；保留让 `root_agent` 可 import 的 Agent 运行时依赖；
   执行原 pytest 目标并根据失败继续修复。
8. **探活并核对语义**：用用户项目里的典型问题跑 `probe_agent.py --mode sdk`，不只看 `ok=True`，还要看返回是否像该
   项目的 Agent。若返回不像，优先尝试下一个 `agent_candidates`，再查同名模块、服务端版本、`cwd/module/agent_var`
   和导入缓存问题。
9. **问裁判配置**：LLM judge 需要模型 Profile，用户通过 `set_model.py` 录入；如果用户已有 SDK judge Agent，则先创建
   第二个 `mode=sdk` Agent，再在 `llmJudge.call_judge` 里引用它。
10. **问运行参数并建方案**：逐项确认 `num_runs`、`pass_k`、`case_parallelism`、`case_eval_parallelism`，创建评测方案。
   最后仍推荐“暂不发起”，只有用户明确授权才执行 `run_eval.py --i-am-authorized`。

### Agent 代执行的底层动作

下面命令是 Agent 在用户确认后代执行的动作示例，不是给用户手敲的清单：

```bash
# 0) 只读扫描已有 SDK 评测目录，生成 cwd/module/agent_var/env_vars/evalset/metric 候选
python3 scripts/inspect_sdk_migration.py /abs/path/to/sdk-evaluation

# 0.5) 用户同意升级评测 SDK 后，Agent 在用户项目里修改依赖/pytest 文件并验证
#      目标：pytest 旧入口继续通过；不要盲删 root_agent 仍需要的 trpc-agent-py / trpc-agent-sdk。
pytest <原来的测试文件或测试目录>

# 1) 如需环境变量，由用户本人录入值；Agent 只登记变量名
python3 scripts/set_env_var.py --name TRPC_AGENT_BASE_URL
python3 scripts/set_env_var.py --name TRPC_AGENT_API_KEY
python3 scripts/set_env_var.py --name TRPC_AGENT_MODEL

# 2) 创建前先用业务问题探测 SDK Agent；agent_var 可省略，省略时服务端默认 root_agent。
#    若返回不像该项目的 Agent，不要继续创建，换 inspect 输出的下一个候选继续验证。
python3 scripts/probe_agent.py --mode sdk --config '{"cwd":"/abs/project","module":"agent.agent","agent_var":"root_agent","env_vars":["TRPC_AGENT_BASE_URL","TRPC_AGENT_API_KEY","TRPC_AGENT_MODEL"]}' --message "一个业务典型问题"
python3 scripts/create_agent.py --name sdk被测Agent --mode sdk --config '{"cwd":"/abs/project","module":"agent.agent","agent_var":"root_agent","env_vars":["TRPC_AGENT_BASE_URL","TRPC_AGENT_API_KEY","TRPC_AGENT_MODEL"]}'

# 3) 迁移数据集与指标
python3 scripts/create_dataset.py --source upload --name SDK迁移数据集 --file ./cases.evalset.json
python3 scripts/metric_catalog.py --mode sdk
python3 scripts/create_metric.py --source empty --name SDK迁移指标 --definition-template llm_final_response --for-mode sdk

# 4) 创建方案；发起仍需用户明确授权
python3 scripts/create_plan.py --name SDK迁移方案 --agent-id <A> --dataset-id <D> --metric-config-id <M> --num-runs 1 --pass-k 1
python3 scripts/run_eval.py --plan-id <P> --i-am-authorized
python3 scripts/get_result.py --id <E> --watch --result-out sdk-migration.result.json --report-out sdk-migration.report.html
```

### 成功判定

- 用户同意升级时，原 pytest 评测入口仍可运行通过，或失败原因已被继续诊断并给出下一步选择。
- WebUI 的 Agent 列表出现 `SDK 接入` Agent，探针通过且返回符合该项目业务预期。
- WebUI 的数据集、指标方案、评测方案都可见且互相绑定。
- `metric_catalog.py --mode sdk` 与创建方案预检通过；SDK Agent 可使用全部指标。
- 若用户授权运行，`get_result.py` 能拿到完成状态、脱敏 result JSON 和 HTML report。

### 失败恢复要点

- pytest 失败：读 traceback，先区分是依赖未安装、import 路径、环境变量、模型配置、数据集文件路径还是 SDK API 差异。
- `probe_agent.py --mode sdk` 失败或返回不像本项目：确认 `cwd` 是项目根目录、`module` 可 import、`agent_var` 是否存在、
  工作区环境变量是否登记；再尝试 `inspect_sdk_migration.py` 的下一个候选，重点排查同名 `agent` 模块串包。
- 指标/方案失败：运行 `metric_catalog.py --mode sdk` 和 `create_plan.py` 预检，按后端 `detail` 调整 metric 或数据集字段。
- 不要停在“脚本执行失败”。复杂迁移允许增加兼容 wrapper、拆分数据集、先跑最小用例，再逐步恢复完整评测。

---

## 场景 Q：任意平台 Trace / JSONL 转 EvalSet（重点）

适用：用户给 LangSmith、Phoenix、OpenTelemetry GenAI、OpenInference、厂内日志或任意 JSON/JSONL trace，包括用户自定义事件格式，希望快速准确转换成 WebUI 可用数据集，并知道哪些指标可用。

**交互原则：用户给样例，Agent 代转换。** 用户不需要理解 EvalSet 全字段；Agent 必须负责字段画像、mapping、dry-run、验证和上传前解释。

```bash
# 1) 只读分析字段形状和语义候选
python3 scripts/inspect_trace_shape.py --input /abs/traces --json-out trace_shape.json

# 2) 先读 recommended_strategy，再复制最接近模板并按 trace_shape.json 修改路径：
#    templates/trace-mapping/generic.messages.json
#    templates/trace-mapping/generic.spans.json
#    templates/trace-mapping/openinference.json
#    templates/trace-mapping/flat-jsonl.json

# 3) 转完整 evalset，并生成审计报告
python3 scripts/convert_trace_to_evalset.py \
  --input /abs/traces \
  --mapping trace_mapping.json \
  --output converted.evalset.json \
  --audit-out conversion_audit.json

# 4) 校验可加载性、字段覆盖和指标可用性；失败则读报告修 mapping 后重跑
python3 scripts/validate_trace_evalset.py \
  --file converted.evalset.json \
  --audit conversion_audit.json \
  --json-out validation_report.json

# 5) 验证报告可解释后，再上传完整 evalset
python3 scripts/create_dataset.py --source upload --name 任意Trace转换集 --file converted.evalset.json
```

成功交付必须包含：`converted.evalset.json`、`conversion_audit.json`、质量摘要、可用指标、不可用指标原因，以及是否建议拆成高质量/低质量数据集。

关键注意：

- 不使用 `add_case.py`，因为简易 API 不保留 `tool_responses`、`session_input.state`、`context_messages` 等字段。
- 用户自定义格式不要求进主仓库写 Adapter；先用 `recommended_strategy` 找 messages/spans/flat/normalizer 路线。
- `conversion_audit.json.summary.unmapped_paths` 必须读；未映射字段要判断是否是评测相关字段，不可静默忽略。
- 缺 `expected` 不阻断转换，但不能可靠跑参考答案比对类指标。
- 缺 `tool_responses` 不阻断转换，但不能可靠跑 `llm_hallucinations` / `llm_rubric_knowledge_recall`。
- 复杂平台格式可以先生成一次性 `normalizer.py` 输出 messages/spans/flat，再走通用转换脚本；不要因为第一次脚本失败就停止。

每步失败时脚本会回显后端返回的 `detail`，按 [08-troubleshooting.md](08-troubleshooting.md) 处理；
发起前的预检与成本预览会拦截大部分配置错误（对象不存在 / mode↔指标不兼容 / 占位符未登记）。
