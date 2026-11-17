#!/usr/bin/env python3
"""
将知识图谱 JSON 转换为 AI 可消费的 Markdown 上下文文档。

此文档专门设计为 AI 读代码和写需求文档时的注入上下文：
- 术语速查表让 AI 能翻译代码变量名
- 实体详解让 AI 理解业务概念和代码位置
- 业务规则让 AI 理解代码逻辑的业务原因
- 业务流程让 AI 理解代码的端到端调用链

用法:
    python kg_to_markdown.py <input.json> <output.md>
"""

import json
import sys


def render_meta(meta):
    lines = []
    lines.append("# {} - AI 业务上下文".format(meta.get("title", "知识图谱")))
    lines.append("")
    if meta.get("description"):
        lines.append("> {}".format(meta["description"]))
        lines.append("")
    lines.append("| 属性 | 值 |")
    lines.append("|------|-----|")
    lines.append("| 领域 | {} |".format(meta.get("domain", "-")))
    lines.append("| 版本 | {} |".format(meta.get("version", "-")))
    lines.append("| 创建日期 | {} |".format(meta.get("createdAt", "-")))
    if meta.get("codeRepos"):
        lines.append("| 代码仓库 | {} |".format(", ".join(meta["codeRepos"])))
    if meta.get("sources"):
        lines.append("| 来源文档 | {} |".format(", ".join(meta["sources"])))
    lines.append("")
    if meta.get("aiUsageHint"):
        lines.append("**AI 使用指引**：{}".format(meta["aiUsageHint"]))
        lines.append("")
    return "\n".join(lines)


def render_glossary(glossary):
    if not glossary:
        return ""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 术语速查表")
    lines.append("")
    lines.append("AI 读代码时的翻译字典——遇到不明变量名/缩写先查此表。")
    lines.append("")
    lines.append("| 代码术语 | 业务含义 | 关联实体 |")
    lines.append("|----------|----------|----------|")
    for term, info in sorted(glossary.items()):
        definition = info.get("definition", "-")
        entity_ref = info.get("entityRef", "-")
        lines.append("| `{}` | {} | {} |".format(term, definition, entity_ref))
    lines.append("")
    return "\n".join(lines)


def render_entities(entities, entity_map):
    if not entities:
        return ""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 核心实体详解")
    lines.append("")
    lines.append("每个实体的业务含义、属性和代码位置。")
    lines.append("")

    type_labels = {
        "core": "核心实体", "attribute": "属性实体", "enum": "枚举",
        "event": "事件", "role": "角色", "process": "流程"
    }

    for entity in entities:
        etype = type_labels.get(entity.get("type", ""), entity.get("type", ""))
        lines.append("### {} ({})".format(entity["name"], etype))
        lines.append("")
        lines.append("**{}**".format(entity.get("description", "")))
        lines.append("")

        if entity.get("synonyms"):
            lines.append("- **别名/代码中的称呼**: {}".format(", ".join("`{}`".format(s) for s in entity["synonyms"])))

        if entity.get("lifecycle"):
            lines.append("- **生命周期**: {}".format(entity["lifecycle"]))

        lines.append("")

        props = entity.get("properties", [])
        if props:
            lines.append("**属性**：")
            lines.append("")
            lines.append("| 属性名 | 类型 | 必填 | 代码字段 | 说明 |")
            lines.append("|--------|------|------|----------|------|")
            for prop in props:
                name = prop.get("name", "")
                ptype = prop.get("type", "")
                if prop.get("enumValues"):
                    ptype += " ({})".format("/".join(prop["enumValues"][:5]))
                required = "是" if prop.get("required") else ""
                code_field = "`{}`".format(prop["codeField"]) if prop.get("codeField") else ""
                if prop.get("dbColumn"):
                    if code_field:
                        code_field += " / "
                    code_field += "`{}`".format(prop["dbColumn"])
                desc = prop.get("description", "")
                if prop.get("constraints"):
                    desc += " [{}]".format(prop["constraints"])
                lines.append("| {} | {} | {} | {} | {} |".format(name, ptype, required, code_field, desc))
            lines.append("")

        cm = entity.get("codeMapping")
        if cm:
            lines.append("**代码位置**：")
            lines.append("")
            if cm.get("modules"):
                lines.append("- 模块: {}".format(", ".join("`{}`".format(m) for m in cm["modules"])))
            if cm.get("files"):
                lines.append("- 文件: {}".format(", ".join("`{}`".format(f) for f in cm["files"])))
            if cm.get("classes"):
                lines.append("- 类: {}".format(", ".join("`{}`".format(c) for c in cm["classes"])))
            if cm.get("functions"):
                lines.append("- 函数: {}".format(", ".join("`{}`".format(f) for f in cm["functions"])))
            if cm.get("dbTables"):
                lines.append("- 数据库表: {}".format(", ".join("`{}`".format(t) for t in cm["dbTables"])))
            if cm.get("apis"):
                lines.append("- API: {}".format(", ".join("`{}`".format(a) for a in cm["apis"])))
            if cm.get("protoMessages"):
                lines.append("- Proto: {}".format(", ".join("`{}`".format(p) for p in cm["protoMessages"])))
            lines.append("")

        transitions = entity.get("stateTransitions")
        if transitions:
            lines.append("**状态迁移**：")
            lines.append("")
            lines.append("| 源状态 | → 目标状态 | 触发条件 |")
            lines.append("|--------|------------|----------|")
            for t in transitions:
                lines.append("| {} | {} | {} |".format(t.get("from", ""), t.get("to", ""), t.get("trigger", "")))
            lines.append("")

    return "\n".join(lines)


def render_relations(relations, entity_map):
    if not relations:
        return ""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 实体关系图谱")
    lines.append("")
    lines.append("实体间的业务关系。AI 可据此理解代码模块间的关联。")
    lines.append("")
    lines.append("| 关系 | 源实体 | → | 目标实体 | 基数 | 业务含义 |")
    lines.append("|------|--------|---|----------|------|----------|")
    for rel in relations:
        src_name = entity_map.get(rel.get("source", ""), {}).get("name", rel.get("source", ""))
        tgt_name = entity_map.get(rel.get("target", ""), {}).get("name", rel.get("target", ""))
        label = rel.get("label", "")
        cardinality = rel.get("cardinality", "")
        desc = rel.get("description", "")
        lines.append("| {} | {} | → | {} | {} | {} |".format(label, src_name, tgt_name, cardinality, desc))
    lines.append("")

    has_data_path = any(r.get("dataPath") for r in relations)
    if has_data_path:
        lines.append("**数据层关联路径**：")
        lines.append("")
        for rel in relations:
            if rel.get("dataPath"):
                src_name = entity_map.get(rel.get("source", ""), {}).get("name", "?")
                tgt_name = entity_map.get(rel.get("target", ""), {}).get("name", "?")
                lines.append("- {} → {}: `{}`".format(src_name, tgt_name, rel["dataPath"]))
        lines.append("")

    return "\n".join(lines)


def render_business_rules(rules, entity_map):
    if not rules:
        return ""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 业务规则清单")
    lines.append("")
    lines.append("AI 读代码时用来理解「为什么代码这样写」。")
    lines.append("")

    type_labels = {
        "validation": "校验", "constraint": "约束", "calculation": "计算",
        "permission": "权限", "flow_control": "流程控制"
    }

    for rule in rules:
        rtype = type_labels.get(rule.get("type", ""), rule.get("type", ""))
        priority = rule.get("priority", "")
        priority_badge = ""
        if priority == "critical":
            priority_badge = " [关键]"
        elif priority == "major":
            priority_badge = " [重要]"

        lines.append("### {} ({}{})".format(rule.get("name", ""), rtype, priority_badge))
        lines.append("")
        lines.append(rule.get("description", ""))
        lines.append("")

        involved = rule.get("involvedEntities", [])
        if involved:
            names = [entity_map.get(eid, {}).get("name", eid) for eid in involved]
            lines.append("- **涉及实体**: {}".format(", ".join(names)))

        if rule.get("condition"):
            lines.append("- **条件**: `{}`".format(rule["condition"]))
        if rule.get("action"):
            lines.append("- **满足时**: {}".format(rule["action"]))
        if rule.get("exception"):
            lines.append("- **不满足时**: {}".format(rule["exception"]))
        if rule.get("codeLocation"):
            lines.append("- **代码位置**: `{}`".format(rule["codeLocation"]))
        lines.append("")

    return "\n".join(lines)


def render_business_flows(flows, entity_map, rule_map):
    if not flows:
        return ""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 业务流程")
    lines.append("")
    lines.append("端到端的业务流程，AI 可据此理解代码的调用链路。")
    lines.append("")

    for flow in flows:
        lines.append("### {}".format(flow.get("name", "")))
        lines.append("")
        lines.append("**目的**: {}".format(flow.get("description", "")))
        lines.append("")
        lines.append("**触发条件**: {}".format(flow.get("triggerCondition", "")))
        lines.append("")

        if flow.get("happyPath"):
            lines.append("**主成功路径**: {}".format(flow["happyPath"]))
            lines.append("")

        steps = flow.get("steps", [])
        if steps:
            lines.append("**详细步骤**：")
            lines.append("")
            lines.append("| # | 执行者 | 动作 | 实体 | 规则 | 代码入口 |")
            lines.append("|---|--------|------|------|------|----------|")
            for step in steps:
                order = step.get("order", "")
                actor = step.get("actor", "")
                action = step.get("action", "")
                entity_ref = step.get("entityRef", "")
                if entity_ref:
                    entity_ref = entity_map.get(entity_ref, {}).get("name", entity_ref)
                rule_ref = step.get("ruleRef", "")
                if rule_ref:
                    rule_ref = rule_map.get(rule_ref, {}).get("name", rule_ref)
                code_entry = "`{}`".format(step["codeEntry"]) if step.get("codeEntry") else ""
                lines.append("| {} | {} | {} | {} | {} | {} |".format(
                    order, actor, action, entity_ref, rule_ref, code_entry))
            lines.append("")

        errors = flow.get("errorScenarios", [])
        if errors:
            lines.append("**异常场景**：")
            lines.append("")
            for err in errors:
                lines.append("- {}".format(err))
            lines.append("")

    return "\n".join(lines)


def kg_to_markdown(kg_data):
    meta = kg_data.get("meta", {})
    glossary = kg_data.get("glossary", {})
    entities = kg_data.get("entities", [])
    relations = kg_data.get("relations", [])
    rules = kg_data.get("businessRules", [])
    flows = kg_data.get("businessFlows", [])

    entity_map = {e["id"]: e for e in entities}
    rule_map = {r["id"]: r for r in rules}

    parts = [
        render_meta(meta),
        render_glossary(glossary),
        render_entities(entities, entity_map),
        render_relations(relations, entity_map),
        render_business_rules(rules, entity_map),
        render_business_flows(flows, entity_map, rule_map),
    ]

    return "\n".join(part for part in parts if part)


def main():
    if len(sys.argv) != 3:
        print("用法: python {} <input.json> <output.md>".format(sys.argv[0]))
        print("示例: python {} kg_payment.json kg_payment_context.md".format(sys.argv[0]))
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        kg_data = json.load(f)

    markdown = kg_to_markdown(kg_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)

    stats = {
        "entities": len(kg_data.get("entities", [])),
        "relations": len(kg_data.get("relations", [])),
        "glossary": len(kg_data.get("glossary", {})),
        "rules": len(kg_data.get("businessRules", [])),
        "flows": len(kg_data.get("businessFlows", [])),
    }
    print("转换完成 → {}".format(output_file))
    print("  {} 个实体, {} 条关系, {} 条术语, {} 条规则, {} 个流程".format(
        stats["entities"], stats["relations"], stats["glossary"], stats["rules"], stats["flows"]))


if __name__ == "__main__":
    main()
