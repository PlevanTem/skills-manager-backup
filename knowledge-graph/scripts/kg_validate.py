#!/usr/bin/env python3
"""
知识图谱自检脚本 — 对应 SKILL.md Stage 4 (Validator)

五层知识图谱校验（entities + relations + rules + flows + glossary）：
  结构层: 实体必填属性、关系引用、孤立节点(BFS)、重复ID、继承环、同名唯一(铁律9)、影子实体、枚举归属
  规则层: involvedEntities引用有效性、condition/action非空、type合法性
  流程层: steps.entityRef引用、steps.ruleRef引用、steps非空有序
  翻译层: entityRef引用有效性、term唯一性

用法:
    python3 kg_validate.py <entities.yaml> <relations.yaml> [rules.yaml] [flows.yaml] [glossary.yaml]
    python3 kg_validate.py v7/kg-entities.yaml v7/kg-relations.yaml v7/kg-rules.yaml v7/kg-flows.yaml v7/kg-glossary.yaml

缺失的可选文件会跳过对应层校验。
输出: 验证结果摘要（PASS/FAIL/WARNING），可重定向到 kg-validation.yaml
"""

import os
import re
import sys
from collections import defaultdict

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


ENTITY_MANDATORY = {"id", "name", "type", "domain", "description", "source"}
RELATION_MANDATORY = {"head", "tail", "relation_type", "description", "source"}


def parse_yaml_blocks(filepath, block_key):
    """从 Markdown 文件中提取 YAML 代码块里的条目。"""
    items = []
    current = {}
    in_yaml = False

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("```yaml"):
                in_yaml = True
                continue
            if stripped == "```" and in_yaml:
                if current:
                    items.append(current)
                    current = {}
                in_yaml = False
                continue
            if not in_yaml:
                continue

            if stripped.startswith("- id:") or stripped.startswith("- head:"):
                if current:
                    items.append(current)
                current = {}

            match = re.match(r'-?\s*(\w+):\s*"?(.+?)"?\s*$', stripped)
            if match:
                key, val = match.group(1), match.group(2).strip('"').strip("'")
                current[key] = val

    if current:
        items.append(current)
    return items


def parse_table_rows(filepath):
    """从 Markdown 表格中提取行数据。"""
    items = []
    headers = []
    in_table = False

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith("|"):
                in_table = False
                headers = []
                continue

            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if not in_table:
                headers = [c.lower().replace(" ", "_") for c in cells]
                in_table = True
                continue

            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue

            if len(cells) == len(headers):
                row = dict(zip(headers, cells))
                items.append(row)

    return items


def load_yaml_file(filepath, key):
    """从纯 YAML 文件加载数据。"""
    if not HAS_YAML:
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = (data or {}).get(key, [])
    return [dict(item) for item in items] if items else []


def load_entities(filepath):
    """自动检测格式解析实体文件：.yaml > yaml代码块 > Markdown表格。"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".yaml", ".yml"):
        entities = load_yaml_file(filepath, "entities")
        if entities:
            return entities
    entities = parse_yaml_blocks(filepath, "entities")
    if not entities:
        entities = parse_table_rows(filepath)
    return entities


def load_relations(filepath):
    """自动检测格式解析关系文件：.yaml > yaml代码块 > Markdown表格。"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".yaml", ".yml"):
        relations = load_yaml_file(filepath, "relations")
        if relations:
            return relations
    relations = parse_yaml_blocks(filepath, "relations")
    if not relations:
        relations = parse_table_rows(filepath)
    return relations


RULE_TYPES = {"validation", "constraint", "calculation", "permission", "flow_control"}


def validate_rules(rules, entity_ids):
    """校验规则层：involvedEntities 引用、condition/action 非空、type 合法。"""
    errors, warnings = [], []
    rule_ids = set()
    for r in rules:
        rid = r.get("id", "")
        if rid in rule_ids:
            errors.append("重复规则 ID: {}".format(rid))
        rule_ids.add(rid)

        if not r.get("condition"):
            errors.append("规则 {} 缺少 condition".format(rid or "?"))
        if not r.get("action"):
            warnings.append("规则 {} 缺少 action".format(rid or "?"))

        rtype = r.get("type", "")
        if rtype and rtype not in RULE_TYPES:
            warnings.append("规则 {} 的 type「{}」不在合法枚举中".format(rid, rtype))

        for eid in r.get("involvedEntities", []):
            if eid not in entity_ids:
                errors.append("规则 {} 引用了不存在的实体: {}".format(rid, eid))

    return rule_ids, errors, warnings


def validate_flows(flows, entity_ids, rule_ids):
    """校验流程层：steps 引用、ruleRef/entityRef 有效性、steps 非空。"""
    errors, warnings = [], []
    flow_ids = set()
    for f in flows:
        fid = f.get("id", "")
        if fid in flow_ids:
            errors.append("重复流程 ID: {}".format(fid))
        flow_ids.add(fid)

        steps = f.get("steps", [])
        if not steps:
            errors.append("流程 {} 无任何步骤".format(fid or "?"))

        for eid in f.get("involvedEntities", []):
            if eid not in entity_ids:
                errors.append("流程 {} 引用了不存在的实体: {}".format(fid, eid))

        for s in steps:
            eref = s.get("entityRef", "")
            if eref and eref not in entity_ids:
                warnings.append("流程 {} step{} 引用了不存在的实体: {}".format(
                    fid, s.get("order", "?"), eref))
            rref = s.get("ruleRef", "")
            if rref and rref not in rule_ids:
                warnings.append("流程 {} step{} 引用了不存在的规则: {}".format(
                    fid, s.get("order", "?"), rref))

    return errors, warnings


def validate_glossary(glossary, entity_ids):
    """校验术语层：entityRef 有效性、term 唯一性。"""
    errors, warnings = [], []
    seen_terms = set()
    for g in glossary:
        term = g.get("term", "")
        if term in seen_terms:
            warnings.append("重复术语: {}".format(term))
        seen_terms.add(term)

        eref = g.get("entityRef", "")
        if eref and eref not in entity_ids:
            warnings.append("术语「{}」引用了不存在的实体: {}".format(term, eref))

    return errors, warnings


def validate(entities, relations):
    errors = []
    warnings = []
    stats = {}

    entity_ids = set()
    dup_ids = set()
    for e in entities:
        eid = e.get("id", "")
        if eid in entity_ids:
            dup_ids.add(eid)
        entity_ids.add(eid)

    if dup_ids:
        errors.append("重复实体 ID: {}".format(", ".join(sorted(dup_ids))))

    for e in entities:
        missing = ENTITY_MANDATORY - set(e.keys())
        if missing:
            errors.append("实体 {} 缺少必填属性: {}".format(
                e.get("id", "?"), ", ".join(sorted(missing))))

    referenced = set()
    for r in relations:
        missing = RELATION_MANDATORY - set(r.keys())
        if missing:
            warnings.append("关系 {}→{} 缺少属性: {}".format(
                r.get("head", "?"), r.get("tail", "?"), ", ".join(sorted(missing))))

        head = r.get("head", "")
        tail = r.get("tail", "")
        if head and head not in entity_ids:
            errors.append("关系引用了不存在的头实体: {}".format(head))
        if tail and tail not in entity_ids:
            errors.append("关系引用了不存在的尾实体: {}".format(tail))
        referenced.add(head)
        referenced.add(tail)

    orphans = entity_ids - referenced
    orphan_rate = len(orphans) / max(len(entity_ids), 1) * 100

    if orphans:
        level = errors if orphan_rate > 1 else warnings
        level.append("孤立节点 ({:.1f}%): {}".format(
            orphan_rate, ", ".join(sorted(orphans))))

    inherit_graph = defaultdict(set)
    for r in relations:
        rtype = r.get("relation_type", "").lower()
        if rtype in ("继承", "inheritance", "泛化", "generalization"):
            inherit_graph[r.get("head", "")].add(r.get("tail", ""))

    def has_cycle(node, visited, path):
        if node in path:
            return True
        if node in visited:
            return False
        visited.add(node)
        path.add(node)
        for neighbor in inherit_graph.get(node, []):
            if has_cycle(neighbor, visited, path):
                return True
        path.discard(node)
        return False

    visited = set()
    for node in inherit_graph:
        if has_cycle(node, visited, set()):
            errors.append("继承关系存在环: 涉及节点 {}".format(node))
            break

    # --- Check 6: Same-name uniqueness (铁律 9) ---
    name_groups = defaultdict(list)
    for e in entities:
        name = e.get("name", "").strip()
        if name:
            name_groups[name].append(e.get("id", "?"))
    dup_names = {n: ids for n, ids in name_groups.items() if len(ids) > 1}
    if dup_names:
        for name, ids in sorted(dup_names.items()):
            errors.append("同名实体违反铁律9 — 名称「{}」出现 {} 次: {}".format(
                name, len(ids), ", ".join(ids)))

    # --- Check 7: Shadow entity check ---
    for e in entities:
        etype = e.get("type", "")
        if "引用实体" in etype:
            errors.append("影子实体违规 — {} (type={})，应删除并改用 depends_on 引用权威实体".format(
                e.get("id", "?"), etype))
        if "cross_domain_ref" in e:
            errors.append("影子实体违规 — {} 含 cross_domain_ref 字段，应删除".format(
                e.get("id", "?")))

    # --- Check 8: Enum ownership completeness ---
    enum_ids = set()
    for e in entities:
        etype = e.get("type", "").lower()
        if "枚举" in etype or etype == "enum":
            enum_ids.add(e.get("id", ""))
    enum_with_ownership = set()
    ownership_types = {"枚举归属", "层级归属", "belongs_to", "属于", "generalizes", "泛化"}
    for r in relations:
        rtype = r.get("relation_type", r.get("type", ""))
        head = r.get("head", "")
        if head in enum_ids and rtype in ownership_types:
            enum_with_ownership.add(head)
    orphan_enums = enum_ids - enum_with_ownership
    if orphan_enums:
        warnings.append("枚举实体缺少归属关系 ({}个): {}".format(
            len(orphan_enums), ", ".join(sorted(orphan_enums))))

    domains = defaultdict(int)
    for e in entities:
        domains[e.get("domain", "未分类")] += 1

    stats = {
        "total_entities": len(entities),
        "total_relations": len(relations),
        "unique_entity_ids": len(entity_ids),
        "orphan_count": len(orphans),
        "orphan_rate": "{:.1f}%".format(orphan_rate),
        "duplicate_names": len(dup_names),
        "enum_without_ownership": len(orphan_enums),
        "domains": dict(domains),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }

    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARNING"
    else:
        status = "PASS"

    return status, errors, warnings, stats


def _try_load(filepath, key):
    """尝试加载 YAML 文件中的指定 key，文件不存在返回空列表。"""
    if not filepath or not os.path.exists(filepath):
        return []
    return load_yaml_file(filepath, key)


def main():
    if len(sys.argv) < 3:
        print("用法: python3 {} <entities.yaml|md> <relations.yaml|md> [rules.yaml] [flows.yaml] [glossary.yaml]".format(sys.argv[0]))
        sys.exit(1)

    entities_file = sys.argv[1]
    relations_file = sys.argv[2]
    rules_file = sys.argv[3] if len(sys.argv) > 3 else None
    flows_file = sys.argv[4] if len(sys.argv) > 4 else None
    glossary_file = sys.argv[5] if len(sys.argv) > 5 else None

    try:
        entities = load_entities(entities_file)
        relations = load_relations(relations_file)
    except FileNotFoundError as e:
        print("文件不存在: {}".format(e))
        sys.exit(1)

    if not entities:
        print("WARNING: 未从 {} 解析到任何实体数据".format(entities_file))
        sys.exit(1)

    status, errors, warnings, stats = validate(entities, relations)

    entity_ids = set(e.get("id", "") for e in entities)

    rules = _try_load(rules_file, "rules")
    flows = _try_load(flows_file, "flows")
    glossary = _try_load(glossary_file, "glossary")

    rule_ids = set()
    if rules:
        rule_ids, r_err, r_warn = validate_rules(rules, entity_ids)
        errors.extend(r_err)
        warnings.extend(r_warn)
        stats["total_rules"] = len(rules)

    if flows:
        f_err, f_warn = validate_flows(flows, entity_ids, rule_ids)
        errors.extend(f_err)
        warnings.extend(f_warn)
        stats["total_flows"] = len(flows)

    if glossary:
        g_err, g_warn = validate_glossary(glossary, entity_ids)
        errors.extend(g_err)
        warnings.extend(g_warn)
        stats["total_glossary"] = len(glossary)

    stats["error_count"] = len(errors)
    stats["warning_count"] = len(warnings)
    if errors:
        status = "FAIL"
    elif warnings and status == "PASS":
        status = "WARNING"

    print("=" * 50)
    print("知识图谱自检报告（五层校验）")
    print("=" * 50)
    print("状态: {}".format(status))
    print()
    print("统计:")
    print("  实体数: {}".format(stats["total_entities"]))
    print("  关系数: {}".format(stats["total_relations"]))
    if "total_rules" in stats:
        print("  规则数: {}".format(stats["total_rules"]))
    if "total_flows" in stats:
        print("  流程数: {}".format(stats["total_flows"]))
    if "total_glossary" in stats:
        print("  术语数: {}".format(stats["total_glossary"]))
    print("  孤立节点: {} ({})".format(stats["orphan_count"], stats["orphan_rate"]))
    print("  同名实体组: {}".format(stats["duplicate_names"]))
    print("  枚举缺归属: {}".format(stats["enum_without_ownership"]))
    print("  业务域分布: {}".format(stats["domains"]))
    print()

    if not rules and not flows and not glossary:
        print("提示: 未提供 rules/flows/glossary 文件，仅执行结构层校验。")
        print("完整校验: python3 {} entities.yaml relations.yaml rules.yaml flows.yaml glossary.yaml".format(sys.argv[0]))
        print()

    if errors:
        print("ERRORS ({})".format(len(errors)))
        for e in errors:
            print("  [E] {}".format(e))
        print()

    if warnings:
        print("WARNINGS ({})".format(len(warnings)))
        for w in warnings:
            print("  [W] {}".format(w))
        print()

    if status == "PASS":
        print("All checks passed.")

    sys.exit(0 if status != "FAIL" else 1)


if __name__ == "__main__":
    main()
