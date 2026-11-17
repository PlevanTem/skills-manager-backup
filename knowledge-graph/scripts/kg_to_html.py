#!/usr/bin/env python3
"""
知识图谱可交互 HTML 可视化生成器 (v2)

读取 kg-entities.yaml + kg-relations.yaml (YAML, 优先)
或 kg-entities.md + kg-relations.md (Markdown 表格, 兼容旧版),
生成基于 ECharts 力导向图的可交互 HTML 页面。

功能:
  - GitHub-dark 主题 (#0d1117)
  - 按业务域着色, 按实体类型区分大小
  - 5层 BFS 高亮 (点击/搜索实体后, 按距离分层高亮, 发光效果)
  - ESC 键退出高亮
  - 枚举值展开/折叠 (详情面板 + 工具栏按钮)
  - 侧边栏域筛选 / 搜索 / 统计卡片
  - 节点详情面板 (属性/备注/枚举值/出入关系, 关系可点击跳转)
  - 箭头边, 关系类型分色, 继承粗线/枚举虚线
  - 底部域图例 (水平滚动)
  - 导出 PNG
  - ECharts 内置 hover adjacency 高亮

设计规范 (保持风格一致):
  - 背景: #0d1117, 侧边栏: #161b22, 边框: #30363d, 卡片: #21262d
  - 文字: #c9d1d9, 弱文字: #8b949e, 强调: #58a6ff, 紫色: #d2a8ff, 链接: #79c0ff
  - 标题栏: linear-gradient(135deg, #1a7f37, #238636)
  - 字体: 'PingFang SC', 'Microsoft YaHei', sans-serif
  - 聚合根/核心实体: 白色 3px 边框, fontSize 11, symbolSize 35/28
  - 枚举类型: fontSize 7, symbolSize 8, 默认隐藏标签
  - 名词类型: fontSize 7, symbolSize 10
  - 标签右置 (position: 'right'), formatter: '{b}'
  - 高亮用发光 (shadowBlur/textShadowBlur), 非加粗
  - 力导向: repulsion 80~200 (按数据量调整), gravity 0.06~0.08, edgeLength [30,160]

用法:
    python3 kg_to_html.py <entities.yaml> <relations.yaml> [output.html]
    python3 kg_to_html.py v7/kg-entities.yaml v7/kg-relations.yaml
"""

import json, os, re, sys
from collections import Counter, OrderedDict, defaultdict

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

DOMAIN_PALETTE = [
    "#7C4DFF","#00C853","#FFD600","#FF1744","#00B0FF",
    "#FFD54F","#FF9100","#26C6DA","#AB47BC","#FF5252",
    "#FF8A80","#69F0AE","#B0BEC5","#E0E0E0","#CE93D8",
    "#4FC3F7","#81C784","#E57373","#FFB74D","#4DB6AC",
    "#BA68C8","#78909C","#F06595","#748ffc","#20c997",
    "#9E9E9E","#FF6E40","#8BC34A","#AED581","#7E57C2",
    "#D4E157","#FFA726","#5C6BC0","#EC407A","#66BB6A",
    "#42A5F5","#FFCA28","#8D6E63","#78909C","#EF5350",
    "#5C6BC0","#26A69A","#D81B60","#43A047","#1E88E5",
    "#FB8C00","#F4511E","#6D4C41","#546E7A","#E53935",
]

TYPE_SIZES = {
    "聚合根":35,"核心实体":28,"枚举":8,"枚举/类型":8,
    "实例":10,"值对象":12,"名词":10,"core":25,"enum":8,
    "event":14,"role":14,"process":16,"attribute":10,
    "引用实体":16,"外围实体":14,
}

RELATION_COLORS = {
    "关联":"#74c0fc","继承":"#ff6b6b","泛化(继承)":"#ff6b6b",
    "组合":"#ffd43b","聚合":"#69db7c","枚举归属":"#868e96",
    "层级归属":"#da77f2","支持":"#748ffc","定向关联":"#20c997",
    "属于概念":"#ff922b","属于":"#adb5bd","自引用":"#da77f2",
    "实现":"#748ffc","跨域引用":"#ff922b","桥接":"#20c997",
    "对齐映射":"#adb5bd","抽象映射":"#868e96",
    "引用关联":"#fab005","镜像映射":"#c0eb75",
    "驱动关联":"#f06595","扩展映射":"#be4bdb",
    "contains":"#69db7c","belongs_to":"#adb5bd",
    "associates":"#74c0fc","generalizes":"#ff6b6b",
    "triggers":"#ff922b","depends_on":"#ffd43b",
    "references":"#868e96","manages":"#748ffc","precedes":"#20c997",
}


# ─── Parsing ───────────────────────────────────────────────

def parse_entities_yaml(filepath):
    if not HAS_YAML:
        raise ImportError("PyYAML required: pip3 install pyyaml")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entities, entity_map = [], {}
    for e in (data or {}).get("entities", []):
        ent = {
            "id": e.get("id",""), "name": e.get("name",""),
            "type": e.get("type","实体"), "domain": e.get("domain","未分类"),
            "desc": str(e.get("description",""))[:300],
            "source": e.get("source",""),
            "properties": [p.get("key","") for p in e.get("properties",[])],
            "notes": e.get("notes",[]),
            "enum_values": e.get("enum_values",[]),
        }
        entities.append(ent)
        entity_map[ent["id"]] = ent
    return entities, entity_map


def parse_relations_yaml(filepath, entity_map):
    if not HAS_YAML:
        raise ImportError("PyYAML required: pip3 install pyyaml")
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    relations = []
    for r in (data or {}).get("relations", []):
        head, tail = r.get("head",""), r.get("tail","")
        if head in entity_map and tail in entity_map:
            relations.append({
                "head": head,
                "type": r.get("relation_type", r.get("type","关联")),
                "tail": tail,
                "desc": str(r.get("description",""))[:200],
            })
    return relations


def parse_entities_md(filepath):
    entities, entity_map, current_domain = [], {}, None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("## ") and s != "## 统计概览":
                m = re.match(r"^## (.+?)(?:[（(]\d+[)）])?$", s)
                if m:
                    current_domain = m.group(1).strip()
                continue
            if not current_domain or not s.startswith("| "):
                continue
            parts = [p.strip() for p in s.split("|")]
            if len(parts) < 6:
                continue
            eid = parts[1]
            if not eid or eid == "ID" or "---" in eid:
                continue
            e = {
                "id": eid, "name": parts[2] if len(parts)>2 else "",
                "type": parts[3] if len(parts)>3 else "实体",
                "domain": current_domain,
                "desc": (parts[4] if len(parts)>4 else "")[:300],
                "source": parts[5] if len(parts)>5 else "",
                "properties": [], "notes": [], "enum_values": [],
            }
            entities.append(e)
            entity_map[eid] = e
    return entities, entity_map


def parse_relations_md(filepath, entity_map):
    relations = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("| "):
                continue
            parts = [p.strip() for p in s.split("|")]
            if len(parts) < 7:
                continue
            head = parts[1]
            if not head or "---" in head or head == "head_id":
                continue
            tail = parts[4] if len(parts) > 4 else ""
            if head in entity_map and tail in entity_map:
                relations.append({
                    "head": head,
                    "type": parts[3] if len(parts)>3 else "关联",
                    "tail": tail,
                    "desc": (parts[6] if len(parts)>6 else "")[:200],
                })
    return relations


# ─── HTML Generation ───────────────────────────────────────

def safe_js(s, maxlen=200):
    if not s:
        return ""
    return s[:maxlen].replace("\\","\\\\").replace("'","\\'").replace('"','\\"').replace("\n"," ").replace("\r","")



def generate_html(entities, relations, entity_map, title="知识图谱", version="",
                   rules=None, flows=None):
    all_ids = set(e["id"] for e in entities)
    adj = defaultdict(set)
    for r in relations:
        adj[r["head"]].add(r["tail"])
        adj[r["tail"]].add(r["head"])
    visited = set()
    if all_ids:
        start = next(iter(all_ids & set(adj.keys())), next(iter(all_ids)))
        visited = {start}
        q = [start]
        while q:
            c = q.pop(0)
            for nb in adj.get(c, set()):
                if nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    conn_pct = len(visited)/len(all_ids)*100 if all_ids else 0

    domains = list(OrderedDict.fromkeys(e["domain"] for e in entities))
    dc = {d: DOMAIN_PALETTE[i%len(DOMAIN_PALETTE)] for i, d in enumerate(domains)}

    n_ent = len(entities)
    force_repulsion = 200 if n_ent < 500 else (120 if n_ent < 1500 else 80)
    force_gravity = 0.06 if n_ent < 500 else 0.08
    force_edge_min = 40 if n_ent < 500 else 30
    force_edge_max = 160 if n_ent < 500 else 120

    entity_rules = defaultdict(list)
    for r in (rules or []):
        for eid in r.get("involvedEntities", []):
            entity_rules[eid].append({"id": r.get("id",""), "name": r.get("name",""),
                                       "type": r.get("type",""), "condition": safe_js(r.get("condition",""),120)})

    entity_flows = defaultdict(list)
    for f in (flows or []):
        for eid in f.get("involvedEntities", []):
            entity_flows[eid].append({"id": f.get("id",""), "name": f.get("name","")})

    echart_nodes = []
    for e in entities:
        color = dc.get(e["domain"], "#888")
        tp = e["type"]
        sz = 15
        for k, v in TYPE_SIZES.items():
            if k in tp:
                sz = v
                break
        is_root = "聚合根" in tp or "核心实体" in tp or tp == "core"
        is_enum = "枚举" in tp or tp == "enum"
        nd = {
            "id": e["id"], "name": e["name"], "symbolSize": sz, "category": e["domain"],
            "itemStyle": {"color": color,
                          "borderColor": "#fff" if is_root else "rgba(255,255,255,0.2)",
                          "borderWidth": 3 if is_root else 1},
            "label": {"show": not is_enum,
                      "fontSize": 11 if is_root else (7 if is_enum or tp == "名词" else 8),
                      "color": "#c9d1d9", "position": "right", "formatter": "{b}"},
            "_domain": e["domain"], "_type": tp,
            "_properties": e.get("properties", []),
            "_notes": e.get("notes", []),
            "_desc": safe_js(e.get("desc", ""), 100),
        }
        if e.get("enum_values"):
            nd["_enum_values"] = e["enum_values"]
        if entity_rules.get(e["id"]):
            nd["_rules"] = entity_rules[e["id"]]
        if entity_flows.get(e["id"]):
            nd["_flows"] = entity_flows[e["id"]]
        echart_nodes.append(nd)

    echart_edges = []
    for i, r in enumerate(relations):
        rt = r["type"]
        color = RELATION_COLORS.get(rt, "#555")
        is_enum_rel = rt in ("枚举归属","层级归属","属于","belongs_to")
        is_inherit = "继承" in rt or "泛化" in rt or rt == "generalizes"
        echart_edges.append({
            "source": r["head"], "target": r["tail"],
            "lineStyle": {"color": color,
                          "type": "dotted" if is_enum_rel else "solid",
                          "width": 0.4 if is_enum_rel else (2 if is_inherit else 0.8),
                          "opacity": 0.2 if is_enum_rel else 0.5,
                          "curveness": 0.08 + (i % 5) * 0.02},
            "label": {"show": False},
            "_rt": rt, "_desc": safe_js(r.get("desc", ""), 80),
        })

    categories = [{"name": d} for d in domains]
    display_title = (title + " " + version).strip()

    # Use TEMPLATE with %%PLACEHOLDER%% to avoid brace conflicts
    html_template = _get_html_template()
    
    replacements = {
        "%%TITLE%%": display_title,
        "%%NUM_ENTITIES%%": str(len(entities)),
        "%%NUM_RELATIONS%%": str(len(relations)),
        "%%NUM_RULES%%": str(len(rules or [])),
        "%%NUM_FLOWS%%": str(len(flows or [])),
        "%%NUM_DOMAINS%%": str(len(domains)),
        "%%CONN_PCT%%": f"{conn_pct:.0f}",
        "%%NODES_JSON%%": json.dumps(echart_nodes, ensure_ascii=False),
        "%%EDGES_JSON%%": json.dumps(echart_edges, ensure_ascii=False),
        "%%CATS_JSON%%": json.dumps(categories, ensure_ascii=False),
        "%%DOMAINS_JSON%%": json.dumps(domains, ensure_ascii=False),
        "%%DC_JSON%%": json.dumps(dc, ensure_ascii=False),
        "%%REPULSION%%": str(force_repulsion),
        "%%GRAVITY%%": str(force_gravity),
        "%%EDGE_MIN%%": str(force_edge_min),
        "%%EDGE_MAX%%": str(force_edge_max),
    }
    
    result = html_template
    for k, v in replacements.items():
        result = result.replace(k, v)
    return result


def _get_html_template():
    return open(os.path.join(os.path.dirname(__file__), 'kg_html_template.html'), 'r', encoding='utf-8').read()



def detect_format(filepath):
    return "yaml" if os.path.splitext(filepath)[1].lower() in (".yaml",".yml") else "md"

def main():
    if len(sys.argv) < 3:
        print(f"用法: python3 {sys.argv[0]} <entities.yaml|md> <relations.yaml|md> [--rules rules.yaml] [--flows flows.yaml] [output.html]")
        sys.exit(1)

    args = sys.argv[1:]
    ent_file, rel_file = args[0], args[1]
    rest = args[2:]

    rules_file, flows_file, out_file = None, None, None
    i = 0
    while i < len(rest):
        if rest[i] == "--rules" and i+1 < len(rest):
            rules_file = rest[i+1]; i += 2
        elif rest[i] == "--flows" and i+1 < len(rest):
            flows_file = rest[i+1]; i += 2
        else:
            out_file = rest[i]; i += 1

    if not out_file:
        out_file = os.path.join(os.path.dirname(os.path.abspath(ent_file)), "knowledge-graph.html")

    fmt = detect_format(ent_file)
    if fmt == "yaml":
        entities, entity_map = parse_entities_yaml(ent_file)
    else:
        entities, entity_map = parse_entities_md(ent_file)

    if not entities:
        print(f"未从 {ent_file} 解析到实体"); sys.exit(1)

    if fmt == "yaml":
        relations = parse_relations_yaml(rel_file, entity_map)
    else:
        relations = parse_relations_md(rel_file, entity_map)

    title, version = "知识图谱", ""
    if fmt == "yaml" and HAS_YAML:
        with open(ent_file, "r", encoding="utf-8") as f:
            meta = (yaml.safe_load(f) or {}).get("meta", {})
        title = meta.get("title", "知识图谱")
        version = meta.get("version", "")

    rules_data, flows_data = None, None
    if rules_file and os.path.exists(rules_file) and HAS_YAML:
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_data = (yaml.safe_load(f) or {}).get("rules", [])
    if flows_file and os.path.exists(flows_file) and HAS_YAML:
        with open(flows_file, "r", encoding="utf-8") as f:
            flows_data = (yaml.safe_load(f) or {}).get("flows", [])

    html = generate_html(entities, relations, entity_map, title=title, version=version,
                         rules=rules_data, flows=flows_data)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML 生成 → {out_file}")
    dom_count = len(set(e["domain"] for e in entities))
    extra = ""
    if rules_data:
        extra += f", 规则: {len(rules_data)}"
    if flows_data:
        extra += f", 流程: {len(flows_data)}"
    print(f"  实体: {len(entities)}, 关系: {len(relations)}, 域: {dom_count}{extra}")

if __name__ == "__main__":
    main()
