# 响应解析脚本模板（供 llm_judge_template 指标解析裁判原始输出）。
#
# 契约：def {name}(response_text: str) -> tuple[float | bool, str]，函数名=登记名；
# 子进程执行、30s 超时、≤64KB。第一返回值 float 会 clamp 到 [0,1]，bool→1.0/0.0；
# 第二返回值为原因。登记后在 llm_judge_template 指标的
# criterion.llmJudge.template.response_scorer_name 里引用该名。
# 内置 single_score / final_response / rubric_scores 无需登记。
#
# response_text 为 AI 裁判模型的原始回复文本，由本函数解析为分数。


def contains_pass(response_text: str) -> tuple[float | bool, str]:
    """裁判回复中包含 PASS 视为通过（示例）。"""
    text = (response_text or "").strip().upper()
    if "PASS" in text:
        return True, "裁判判定通过"
    return False, "裁判未判定通过"
