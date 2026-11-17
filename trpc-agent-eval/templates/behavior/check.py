# 行为检查脚本模板（确定性验证，配 final_behavior_avg_score 指标）。
#
# 契约：模块级函数名必须等于登记名；签名固定如下；子进程执行、30s 超时、≤64KB。
#
# !!! 重要：入参 user_content 是「该 invocation 的用户输入文本」(actual user_content)，
#     并不是 Agent 的回复或 final_behavior 文本。检查器无法获取 Agent 输出，
#     因此核验真实副作用（如是否真的下单）时，须在函数内自行查询外部系统/数据库。
#
# 返回 (是否通过, 原因说明)。
# 数据集 expected invocation 用 final_behavior_match / final_behavior_matches 引用本函数名，
# 并在 final_behavior_avg_score 指标的 criterion.finalBehavior.allowed_matches 里列出它。


def check_order_created(user_content: str) -> tuple[bool, str]:
    """根据用户请求独立核验订单是否真的创建（示例）。

    user_content 是用户这轮的输入文本（如「帮我下单 SKU123」）。
    这里应解析出关键信息，再去真实系统查询下单结果。下例仅占位返回。
    """
    if not user_content.strip():
        return False, "用户输入为空，无法核验"
    # 真实场景：从 user_content 解析订单意图 → 调用订单系统 API 确认是否创建成功
    order_created = True  # 占位：替换为真实查询结果
    return (order_created, "订单已确认创建" if order_created else "未查到订单")
