# 10 可扩展性：系统演进与 skill 自适应

系统持续迭代，可能新增指标、Agent 模式、输出协议、脚本类型、占位符与 API 端点。
本 skill 的设计原则是**发现优先**：运行时探测到的能力为权威，文档仅作带版本的快照。

## 操作前先探查

```bash
python3 scripts/discover.py --base-url <backend>        # 版本/路由/指标/runtime/模型Profile/可用集/协议/脚本模板
python3 scripts/discover.py --raw-openapi               # 查看完整路由表
```

权威运行时入口（始终以它们为准，而非本文档）：

| 能力 | 运行时入口 |
|------|-----------|
| 全部 API 路由 | `GET /openapi.json`（或浏览 `/docs`） |
| 指标全集与元信息 | `GET /api/metric-configs/catalog` |
| 某 mode/协议可用指标 | `GET /api/metric-configs/allowed?mode=&output_protocol=` |
| 三类脚本骨架 | `GET /api/{behavior-checks,agent-tools,response-scorers}/template` |
| 模型 Profile / 在线 runtime | `GET /api/models` / `GET /api/runtimes` |
| 当前 workdir | `GET /api/workspace` |

## 文档与运行时不一致时

- **以运行时为准。** 文档里的枚举（指标名、协议名、聚合器、占位符）是写作时的快照。
- 发现新枚举值（如新指标、新 `output_protocol`、新内置响应解析器）：直接按 catalog/allowed 的返回使用，
  不要被文档里的清单限制。
- 发现新端点：用 `discover.py --raw-openapi` 看签名，再按 REST 习惯调用（多数为 `POST` 建、`GET` 查）。

## 排错的权威阶梯（卡住或疑似静默失败时，逐级升级）

当出现「评测跑通但分数无意义」「指标要什么字段说不清」「行为与文档不符」等问题时，**按下列顺序升级，止于能解释问题的最低一级**：

1. **运行时元数据**（首选）：`discover.py` / `GET /api/metric-configs/catalog`（含 `when_to_use`）/ `allowed?mode=` / `openapi.json` / 各脚本 `--print-template`。多数字段与门控问题在此即可澄清。
2. **实跑验证**（语义是否真生效）：用最小数据集冒烟一次，并加一条「**应当失败**的对照用例」；若该用例未失败，或各用例分数整齐划一/全为 0/满分，多半是数据字段缺失或填错（静默失败），用 `get_result.py` 的逐项 breakdown 定位是哪条、哪个维度。
3. **源码（终极保底，只读）**：前两级都无法解释时，定位已安装包源码查证语义。

   ```bash
   python3 scripts/find_source.py     # 打印 server / SDK 源码目录 + 权威模块地图
   # 再用 Grep/Read 在该目录内按 指标名/criterion键/字段名 查证
   ```

   该脚本跨环境健壮：当前解释器找不到时，会反查后端入口 `trpc-agent-eval-server` 的 shebang
   定位真正装包的解释器（应对 venv / 多 python），再不行则用 `pip show`；全部失败时会打印
   下方同款指引。已安装包为纯 Python 源码（wheel 无二进制扩展），site-packages 下即可读。

   **若 `find_source.py` 不可用（报错 / 不存在 / 跑不起来），手动定位（与脚本逻辑一致）：**

   ```bash
   # ① 找到“真正运行后端的那个 python”——这是跨环境定位的锚点
   head -1 "$(command -v trpc-agent-eval-server)"   # 读入口 shebang，得到该 python
   #   入口不在 PATH 时，用运行中的后端进程反查：
   readlink -f /proc/"$(pgrep -af trpc-agent-eval-server | awk 'NR==1{print $1}')"/exe

   # ② 用“那个 python”（记为 PY）定位包目录（find_spec 不导入整包，只读）
   PY=<上一步得到的 python>
   "$PY" -c "import importlib.util as u;print(u.find_spec('trpc_agent_self_evolution').submodule_search_locations[0])"
   "$PY" -c "import importlib.util as u;print(u.find_spec('trpc_agent_eval_server').submodule_search_locations[0])"
   #   或：用 pip 的 Location（editable→指向仓库；普通安装→.../site-packages）
   "$PY" -m pip show -f trpc-agent-eval-server
   "$PY" -m pip show -f trpc-agent-self-evolution
   ```

   拿到包目录后，用 Grep/Read 按 指标名 / criterion 键 / 字段名 查证。权威模块地图：
   SDK 的 `_eval_metrics.py`（指标输入/打分）、`_evaluator_registry.py`、`_criterion_registry.py`、
   `_llm_judge.py` / `_llm_evaluator.py`（裁判语义）；server 的 `sdk/metric_catalog_meta.py`
   （`when_to_use`/`black_box_allowed`）、`api/`（各对象入参校验）。文件改名时按符号名 Grep。

   **红线：源码只读，严禁修改已安装包内任何文件。** 改它不会进入评测、会污染环境、升级即丢失；
   一切修复都落在 skill 侧（脚本入参、模板、数据集字段）。

> 权威等级：运行时元数据 ＜ 实跑验证 ＜ 源码（后者更权威但成本更高，故作最后手段）。
> **前端 npm 包是压缩构建产物（无 sourcemap），不可作源码依据**；它只是套在 `/api/*` 上的薄 SPA，零评测逻辑。要看前后端交互，读 `openapi.json` 或浏览器 Network。

## 脚本为何能自适应

- 脚本尽量只依赖 base-url 与运行时端点，少硬编码：
  - `create_agent.py --mode` / `discover.py` 的模式清单是**已知模式集**（http/cli/llm/trace/managed/sdk）——因为后端未在 openapi 暴露 mode/output_protocol 枚举，这部分**只能按已知集探测**；若系统新增模式，这里不会自动显示，用 `--config` + 直接调 API 即可，并以建对象时的报错为准。
  - `metric_catalog.py` / `discover.py` 的指标则**动态读取** catalog/allowed，新指标会自动出现。
  - `create_metric.py` 的 `definition` 透传 criterion，新增指标只需新模板或内联 JSON。
  - `create_*` 脚本的 `--print-template` 永远拉服务端最新骨架。
- 因此系统新增功能时多数无需修改脚本：先运行 `discover.py`，再用 `--config`/`--definition` 透传新字段。

## 维护本 skill 的约定

- references 里的枚举/字段表，**标注为快照**，并始终附上对应运行时入口，便于核对。
- 新增模板时与运行时 `--print-template` / catalog 对齐。
- 升级系统后：运行 `discover.py`，对照本目录文档，更新差异处即可（一模块一文档，改动局部化）。
