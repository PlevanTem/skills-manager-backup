# 06 模型配置、命名密钥、环境变量

三类配置均用于为评测提供鉴权与模型能力。**其值一律由用户本人通过脚本 `getpass` 录入**，
Agent 仅以占位符引用，不接触明文。

## 命名密钥（`${SECRET:名}`）

- 用途：HTTP Agent 的请求头/请求体里的 token，Langfuse 的 public/secret key 等。
- 登记：`set_secret.py --name MY_TOKEN`（`PUT /api/secrets/{name}`，body `{value}`）。
- 引用：配置里写 `${SECRET:MY_TOKEN}`（如 `"Authorization": "Bearer ${SECRET:MY_TOKEN}"`）。
- 存储：`secrets.enc`，PBKDF2-HMAC-SHA256(600k)+Fernet，主密钥来自 `TRPC_EVAL_UI_SECRET`。
- 列表（仅掩码）：`GET /api/secrets`。

## 模型配置 Profile（`${MODEL:名}` / `model_profile_id`）

- 用途：llm Agent 的驱动模型；LLM 裁判类指标的裁判模型。
- 登记：`set_model.py --name glm_flash --model-name glm-4-flash --base-url-model <endpoint>`
  （`POST /api/models`，字段 `name`/`model_name`/`base_url`/`api_key`；api_key getpass 输入）。
- 名规则：`^[a-z][a-z0-9_]{0,63}$`。
- 引用：
  - llm Agent：`config.model_profile_id = "glm_flash"`。
  - 裁判指标：`judge_model.model_name/base_url/api_key = "${MODEL:glm_flash}"`（按字段名分别解析）。
- 存储：`shared/models/index.json`，api_key 加密。

## 工作区环境变量（`${VAR}` / `$VAR`）

- 用途：cli Agent 子进程、脚本执行所需的环境变量。
- 登记：`set_env_var.py --name CODEBUDDY_API_KEY`（`PUT /api/env-vars/{name}`，不允许空值）。
- 名规则：`^[A-Z][A-Z0-9_]{0,127}$`。
- 存储：`env_vars.enc`，与 `TRPC_EVAL_UI_SECRET` 绑定。

## 占位符与合并规则

| 占位符 | 解析为 | 作用域 |
|--------|--------|--------|
| `${QUERY}` | 当前用户输入 | http body_template/headers、cli placeholder 模式 |
| `${SECRET:名}` | 命名密钥明文 | http headers/body_template |
| `${MODEL:名}` | 模型 Profile 字段（按所在键名 model_name/base_url/api_key） | 指标 criterion 的 judge_model |
| `${VAR}` / `$VAR` | 工作区环境变量 | cli env、脚本执行环境 |

cli 子进程 env 合并顺序（后者覆盖前者）：`os.environ` < 工作区环境变量 < Agent `config.env`。

## 安全要点

- 生产务必设置稳定的 `TRPC_EVAL_UI_SECRET`，否则换机器无法解密已存密钥/模型 key。
- 导出指标方案 JSON 时 `api_key` 会被剔除；结果/探针响应里 secrets 被掩码。
- Agent 切勿读取或粘贴明文凭证；缺凭证时引导用户运行对应 `set_*` 脚本。
