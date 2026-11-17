# 自定义 Agent 工具脚本模板（供内置 llm Agent 调用）。
#
# 契约：def {name}(query: str) -> str，函数名=登记名；docstring 会作为工具描述展示给 LLM。
# 进程内执行（无沙箱），≤64KB。登记后在 llm Agent 的 config.tools 列表里写该函数名。
# 也可定义模块级 TOOLS = [fn1, fn2] 一次登记多个工具。


def my_search(query: str) -> str:
    """根据查询关键词返回知识库片段。query 为用户/Agent 传入的检索词。"""
    # 在此实现真实检索逻辑；以下为占位返回。
    return f"未接入真实检索后端，回显查询: {query}"
