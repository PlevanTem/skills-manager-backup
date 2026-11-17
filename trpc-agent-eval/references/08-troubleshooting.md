# 08 排障对照表

先跑 `python3 scripts/doctor.py`（健康+对象清单）与 `python3 scripts/discover.py`（能力）定位。

## SDK 迁移失败处理

迁移已有 SDK / pytest 评测到 WebUI 时，脚本失败只是诊断信号，不是停止点：

- pytest 失败：读 traceback，区分依赖缺失、import 路径、环境变量、模型配置、数据集路径、SDK API 差异；先恢复原 pytest 入口。
- SDK 探针失败或返回不像本项目：检查 `cwd` 是否项目根、`module` 是否可 import、`agent_var` 是否存在、`env_vars` 是否已登记；优先尝试 `inspect_sdk_migration.py` 的 `recommended_agent_config` 和后续候选，排查同名模块串包。
- WebUI 方案失败：读取后端 `detail`，运行 `metric_catalog.py --mode sdk`，检查数据集字段与指标门控。
- 复杂项目先做最小 wrapper 或最小数据集冒烟，再逐步迁回完整评测；不要因为单个脚本失败就把问题交还给用户。

推荐路径：保留业务 Agent 运行时依赖，让 `root_agent` 先可 import；用户同意时把评测层迁到 `trpc-agent-self-evolution`；跑原 pytest；再接 WebUI。

| 症状 | 可能原因 | 处理 |
|------|----------|------|
| 浏览器打开后端端口只有 JSON | 后端无界面 | 启动前端，用前端地址访问 |
| 前端 502 / `backend unreachable` | 连不上后端 | 查后端是否启动、分机需 `--host 0.0.0.0`、`--backend` 是否正确、防火墙放行端口 |
| `curl /api/health` 失败 | 后端未起/端口错 | `serve.sh` 重启；确认端口未被占用 |
| 端口被占用 | 8080/5173 已用 | 换端口（后端 `--port`，前端 `--port` 并同步 `--backend`） |
| 创建 Agent 后探针失败 | url/命令/鉴权问题 | 看 `probe_agent.py` 的 `error`；http 检查 `${SECRET}` 是否已登记、`body_template` 含 `${QUERY}` |
| SDK 探针 ok 但返回不像该项目 Agent | `cwd/module/agent_var` 选错、同名 Python 模块串包、服务端未重启到新版本 | 用业务问题探活；优先用扫描出的 `recommended_agent_config`，再试下一个 `agent_candidates`；确认服务端版本包含 SDK 导入缓存清理 |
| `密钥未找到: X` | 占位符引用了未登记密钥 | `set_secret.py --name X` 由用户填 |
| `model profile not found` / `has no api_key` | 模型 Profile 缺失或没 key | `set_model.py` 重新登记并填 key |
| 指标校验失败 incompatible/unknown | 指标与 mode 不匹配 | 用 `metric_catalog.py --mode <mode>` 核对；黑盒需 `output_protocol` 解锁 tool/hallucination |
| `llm_hallucinations` 不生效 | 缺 grounding | 数据集 `actual_conversation.intermediate_data` 须含 `tool_uses`+`tool_responses`（用上传，不用 add_case） |
| 行为检查/响应解析报签名错误 | 函数名/签名不符 | 函数名须=登记名，签名严格按 [07](07-scripts-registry.md) |
| 上传数据集 413 | 文件 >16MB | 拆分或用路径登记 `--source path` |
| 脚本 >64KB 被拒 | 脚本过大 | 精简或外置依赖 |
| 评测一直 pending/突然 error“服务重启前未完成” | 后端重启过 | 重新发起评测 |
| 换机器后密钥/模型不可用 | `TRPC_EVAL_UI_SECRET` 不一致 | 用与旧环境相同的主密钥 |
| `路径登记`数据集打开失败 | 目标机器缺该绝对路径 | 确认服务端路径存在可读，或改用上传 |

排障原则：先用 `doctor.py`/`discover.py` 获取事实依据，再查阅后端日志（`--log-file` 指定的文件，
不记录请求 body）。脚本报错时均会回显后端返回的 `detail`。
