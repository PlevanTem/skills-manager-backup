# 05 评测方案、发起与结果

## 评测方案（可复用绑定）

`POST /api/evaluation-plans`（脚本 `create_plan.py`）把 Agent + 数据集 + 指标方案 + 运行参数绑成一个方案：

| 字段 | 默认 | 范围 | 说明 |
|------|------|------|------|
| `name` | — | — | 方案名 |
| `agent_id` | — | — | 被测 Agent |
| `dataset_ids` | `[]` | **最多 1 个** | 绑定的数据集 |
| `metric_config_id` | — | — | 指标方案 |
| `num_runs` | 1 | 1-100 | 每个用例重复运行次数 |
| `pass_k` | =num_runs | 1-100 | pass@k 的 k，须 ≤ num_runs |
| `case_parallelism` | 4 | 1-32 | 用例并发 |
| `case_eval_parallelism` | 4 | 1-32 | 用例内评测并发 |

## 发起（红线：须用户授权）

- 按方案：`POST /api/evaluation-plans/{plan_id}/run`
- 直接发起：`POST /api/evaluations`（`{agent_id, dataset_ids:[d], metric_config_id, num_runs}`，pass_k 默认=num_runs）
- 批量：`POST /api/evaluation-plans/batch-run`（`{plan_ids:[...]}`，≤10）

脚本 `run_eval.py` 默认拒绝执行，须加 `--i-am-authorized`（代表用户已明确同意）。

## 状态机

```
pending → running → done
                 ↘ error
running --cancel--> cancelling → error
```
- 服务重启后仍处于 pending/running 的评测会被标记为 **error**（“服务重启前未完成”），需重新发起。
- 取消：`POST /api/evaluations/{id}/cancel`（仅 pending/running 可取消）。

## 进度（SSE）

`GET /api/evaluations/{id}/events`：`text/event-stream`，每行 `data: {json}`。
事件含 `status` 变更、用例推理/评测完成、`error`、终止哨兵 `{"type":"__end__"}`。
脚本：`get_result.py --id <id> --watch`。

## 结果

- 状态/摘要：`GET /api/evaluations/{id}`，关键字段：`status`、`eval_outcome`(pass/fail)、
  `cases_passed`/`cases_total`、`pass_at_k`、`pass_hat_k`、`num_runs`、`pass_k`；
  失败带 `error_message`，完成可能带 `assertion_errors`/`assertion_message`。
- 完整结果 JSON：`GET /api/evaluations/{id}/result`（敏感字段已脱敏）。
- HTML 报告：`GET /api/evaluations/{id}/report`。
- 方案维度的分页运行历史：`GET /api/evaluation-plans/{plan_id}/runs-page`。

脚本：`get_result.py --id <id> [--watch] [--result-out r.json] [--report-out r.html]`。

## pass@k 与 pass^k

- `num_runs=n`：每用例跑 n 次；`pass_k=k`：取其中 k 次的口径。
- `pass@k`：n 次中“至少有一次通过”的口径（宽松，反映能力上限）。
- `pass^k`：k 次全部通过的口径（严格，反映稳定性）。
- 单次评测（n=1）只有通过/不通过；要测稳定性就把 `num_runs` 调大并设 `pass_k`。

## mode ↔ 指标门控

发起前确保指标方案里的每个指标都在 Agent mode（及 output_protocol）允许集内，否则校验报错。
门控表见 [04](04-metrics.md)，运行时以 `GET /api/metric-configs/allowed` 为准。
