# 02 Agent 接入

被测对象按调用方式选一种 mode。创建用 `POST /api/agents`（`{name, mode, config, tags}`），
脚本：`create_agent.py`；连通性探针：`probe_agent.py`（`POST /api/agent-probe`，trace 不支持）。

鉴权信息不写进 config，用 `${SECRET:名}` 占位符（先 `set_secret.py` 登记）。

## mode=http（黑盒 HTTP 服务）

config 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `url` | 是 | 请求地址 |
| `method` | 否 | 默认 `POST` |
| `headers` | 否 | JSON 对象，值可用 `${SECRET:名}` / `${QUERY}` |
| `body_template` | 是 | JSON 对象，**必须包含 `${QUERY}`**（用户输入注入点） |
| `response_path` | 否 | 点路径取回复文本，如 `choices.0.message.content`；不填则返回整个响应体文本 |
| `output_protocol` | 否 | `claudecode` / `codex`，见下 |

模板：`templates/agent/http.json`。

## mode=cli（黑盒本地命令）

config 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `command` | 是 | 字符串数组，如 `["python","/abs/agent.py"]` |
| `arg_mode` | 否 | `stdin`（默认，query 走标准输入）/ `append`（query 追加为末尾参数）/ `placeholder`（command 为单条文本且含 `${QUERY}`，经 `bash -lc` 执行） |
| `cwd` | 否 | 绝对路径工作目录（必须存在） |
| `env` | 否 | 额外环境变量映射 |
| `output_protocol` | 否 | `claudecode` / `codex` |

子进程 env 合并顺序：`os.environ` < 工作区环境变量（`set_env_var.py`）< `config.env`。
CLI 评测**无超时**（任务可能耗时较长）；进程被取消时会终止整个进程树。
模板：`templates/agent/cli.json`、`cli.claudecode.json`、`cli.codex.json`。

## mode=llm（系统内置 LLM Agent）

由系统直接用模型驱动一个带工具的 Agent。config 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `model_profile_id` | 是 | 模型 Profile 名（先 `set_model.py` 登记） |
| `instruction` | 否 | 系统提示词 |
| `tools` | 否 | 工具名数组；内置 `read`/`bash`/`grep`/`glob`，自定义工具见 [07](07-scripts-registry.md) |
| `generation` | 否 | 生成参数，如 `temperature`/`max_output_tokens` |
| `think` | 否 | 是否开启思考模式 |

模板：`templates/agent/llm.json`。

## mode=sdk（业务 Python SDK Agent，本机直接加载）

适用：用户已经用 tRPC Agent SDK 写好了 Agent，模块里导出 `root_agent` 或其他 Agent 变量，希望不包装 HTTP/CLI，直接迁移接入 WebUI。老项目依赖名可能写作 `trpc-agent-sdk` 或 `trpc-agent-py`，也归入这一类 SDK 接入。server 和被测 Agent 位于同一台机器，后端进程会在运行时 import 业务模块。

config 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `cwd` | 是 | **服务端机器上**的 Agent 项目目录绝对路径，通常是包含 `agent.py`、`agent/`、`src/` 或 `pyproject.toml` 的目录 |
| `module` | 是 | Python import 路径，不是文件路径，如 `agent`、`agent.agent`、`src.my_app.agent` |
| `agent_var` | 否 | 模块里保存 Agent 的变量名；留空默认 `root_agent` |
| `env_vars` | 否 | 已登记工作区环境变量名数组（`set_env_var.py` 登记）；运行时注入后端进程环境，配置不存明文 |

模块变量可以是当前运行环境里 `trpc_agent_sdk.agents.BaseAgent` 或 `trpc_agent_sdk.runners.Runner` 兼容对象：

- 若是 `BaseAgent`，WebUI 会自动包装为 `Runner` 并创建内存 session。
- 若是 `Runner`，WebUI 会直接复用该 Runner。
- `cwd` 会临时加入 `sys.path` 并作为 import 时的当前工作目录；不需要用户手动配置 `PYTHONPATH`。
- 多个 SDK Agent 使用相同模块名（如都叫 `agent`）时，服务端会在导入前清理目标模块缓存，避免串包。
- **不需要** `output_protocol`；SDK 接入直接使用 Runner 事件，工具轨迹与最终回复由 SDK 事件提供。

模板：`templates/agent/sdk.json`。

迁移已有 SDK 评测时，Agent 应先读用户给出的项目目录，并优先运行
`python3 scripts/inspect_sdk_migration.py <目录>` 推断 `cwd`/`module`/`agent_var`/`env_vars`/evalset/metric 候选，并识别 `trpc-agent-sdk` / `trpc-agent-py` 依赖标记与旧 `AgentEvaluator.evaluate(agent_module="...")` 写法，再让用户确认；用户只需回答“目录是哪一个、模块是不是这个、变量名是否默认 root_agent”。确认后再创建并探针。

若用户还保留旧 pytest 评测方式，推荐把**评测层**迁到 `trpc-agent-self-evolution`，这样同一套用例既可继续 pytest，也可迁入 WebUI。用户同意后，Agent 负责修改依赖/测试代码并运行原 pytest 验证；但业务 Agent 的运行时依赖不要盲删，`root_agent` 仍 import `trpc_agent_sdk` 时应保留 `trpc-agent-py` / `trpc-agent-sdk`。

## mode=managed（托管 Agent，远程 worker 执行 ClaudeCode/Codex/Hermes）

系统把 ClaudeCode / Codex / Hermes 这类 CLI Agent 交给一个独立的 **worker 进程**执行（可与 server 不同机器）。
server 不直接起进程，而是下发 task，worker 领取后用本机的 provider runtime 跑，再回传结果与工具调用事件。
前置：必须有 worker 在线并注册了 runtime（见 [01](01-architecture.md)），用 `GET /api/runtimes` / `discover.py` 查。

config 字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `provider` | 是 | `claudecode` / `codex` / `hermes` |
| `runtime_id` | 是 | 取自 `/api/runtimes` 里 `status=online` 且 `provider` 匹配的 runtime id |
| `cwd` | 是 | **worker 机器上**的绝对路径工作目录 |
| `model` | 否 | 覆盖该 runtime 默认模型 |
| `env_vars` | 否 | **已登记环境变量名**数组（`set_env_var.py` 登记）；运行时由 server 解析注入 worker，配置不存明文。保留名（`HOME`/`PATH`/`TRPC_AGENT_EVAL_*`/`CLAUDECODE_*` 等）被拒 |
| `custom_args` | 否 | 传给 provider 的自定义启动参数；会**过滤掉**破坏托管协议的参数（如 `--output-format`/`-p`/`--model`/`--cwd`、codex `app-server` 等） |

**不支持** `output_protocol` / `executable` / `env`（给了会 400）。managed Agent 既可作被测，也可作 `call_judge` 裁判（见 [04](04-metrics.md)）。
模板：`templates/agent/managed.json`。

## mode=trace（离线回放/直接打分）

不调用被测系统，直接对数据集中已采集的真实输出打分。**无 config、无探针**。
数据集需含 `actual_conversation`（`eval_mode=trace`），见 [03](03-datasets.md)。

## output_protocol：把黑盒原始输出解析为结构化轨迹

http/cli Agent 若按 ClaudeCode / Codex 的 JSON(L) 流输出，设 `output_protocol` 后，
系统会解析出 `final_response` / `tool_calls` / `tool_responses` / `intermediate_responses`，
从而**解锁**原本黑盒不可用的 `tool_trajectory_avg_score` 与 `llm_hallucinations`。

- 取值（小写）：`claudecode`、`codex`。
- 默认黑盒（无协议）可用指标见 [04](04-metrics.md) 的门控表；协议解锁集以
  `GET /api/metric-configs/allowed?mode=cli&output_protocol=claudecode` 为准。

## 探针

```bash
python3 scripts/probe_agent.py --mode http --template http        # 探内联/模板 config
python3 scripts/probe_agent.py --agent-id <id>                    # 探已创建 Agent
python3 scripts/probe_agent.py --agent-id <id> --message "1+1=?"  # 自定义测试语（默认「你好」）
```
支持 http / cli / llm / managed / sdk（trace 不支持）。返回 `ok` / `response` / `elapsed_ms` / `error`；
`request_preview` 中 secrets 已掩码。创建后建议立即探针确认连通（trace 除外）。
