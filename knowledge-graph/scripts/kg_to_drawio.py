#!/usr/bin/env python3
"""
将知识图谱 JSON 转换为 draw.io (.drawio) 格式的可视化图表。

用法:
    python kg_to_drawio.py <input.json> <output.drawio>

输入: 符合 kg_schema.md 定义的知识图谱 JSON 文件
输出: 可在 draw.io / VS Code Draw.io 插件中打开的 .drawio 文件
"""

import json
import sys
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

ENTITY_TYPE_COLORS = {
    "core":      {"fill": "#dae8fc", "stroke": "#6c8ebf", "font": "#333333"},
    "attribute": {"fill": "#fff2cc", "stroke": "#d6b656", "font": "#333333"},
    "enum":      {"fill": "#e1d5e7", "stroke": "#9673a6", "font": "#333333"},
    "event":     {"fill": "#d5e8d4", "stroke": "#82b366", "font": "#333333"},
    "role":      {"fill": "#f8cecc", "stroke": "#b85450", "font": "#333333"},
    "process":   {"fill": "#e6f3ff", "stroke": "#4a90d9", "font": "#333333"},
}

RELATION_TYPE_STYLES = {
    "contains":    {"stroke": "#6c8ebf", "dashed": "0", "endArrow": "diamond", "endFill": "1"},
    "belongs_to":  {"stroke": "#6c8ebf", "dashed": "0", "endArrow": "open",    "endFill": "0"},
    "depends_on":  {"stroke": "#d6b656", "dashed": "1", "endArrow": "open",    "endFill": "0"},
    "associates":  {"stroke": "#82b366", "dashed": "0", "endArrow": "open",    "endFill": "0"},
    "generalizes": {"stroke": "#9673a6", "dashed": "0", "endArrow": "block",   "endFill": "0"},
    "triggers":    {"stroke": "#b85450", "dashed": "0", "endArrow": "classic",  "endFill": "1"},
    "produces":    {"stroke": "#82b366", "dashed": "0", "endArrow": "classic",  "endFill": "1"},
    "references":  {"stroke": "#808080", "dashed": "1", "endArrow": "open",    "endFill": "0"},
    "manages":     {"stroke": "#d6b656", "dashed": "0", "endArrow": "classic",  "endFill": "1"},
    "transforms":  {"stroke": "#b85450", "dashed": "1", "endArrow": "classic",  "endFill": "1"},
    "precedes":    {"stroke": "#4a90d9", "dashed": "0", "endArrow": "classic",  "endFill": "1"},
    "constrains":  {"stroke": "#d6b656", "dashed": "1", "endArrow": "diamond",  "endFill": "0"},
}

DEFAULT_COLOR = {"fill": "#f5f5f5", "stroke": "#666666", "font": "#333333"}
DEFAULT_RELATION_STYLE = {"stroke": "#808080", "dashed": "0", "endArrow": "classic", "endFill": "1"}

NODE_WIDTH = 200
NODE_HEIGHT = 80
PROP_ROW_HEIGHT = 20
PADDING_X = 80
PADDING_Y = 60


def compute_layout(entities):
    """Use a simple force-directed-ish grid layout based on entity count."""
    n = len(entities)
    if n == 0:
        return {}

    cols = max(1, int(math.ceil(math.sqrt(n))))
    positions = {}
    for i, entity in enumerate(entities):
        row = i // cols
        col = i % cols
        props_count = len(entity.get("properties", []))
        height = NODE_HEIGHT + props_count * PROP_ROW_HEIGHT
        x = 60 + col * (NODE_WIDTH + PADDING_X)
        y = 60 + row * (NODE_HEIGHT + PADDING_Y + props_count * PROP_ROW_HEIGHT // 2)
        positions[entity["id"]] = {"x": x, "y": y, "w": NODE_WIDTH, "h": height}
    return positions


def build_entity_style(entity_type):
    colors = ENTITY_TYPE_COLORS.get(entity_type, DEFAULT_COLOR)
    return (
        f"rounded=1;whiteSpace=wrap;html=1;arcSize=10;"
        f"fillColor={colors['fill']};strokeColor={colors['stroke']};"
        f"fontColor={colors['font']};fontStyle=1;fontSize=13;align=center;verticalAlign=top;"
        f"spacingTop=8;shadow=1;"
    )


def build_property_style(entity_type):
    colors = ENTITY_TYPE_COLORS.get(entity_type, DEFAULT_COLOR)
    return (
        f"text;html=1;align=left;verticalAlign=middle;resizable=0;points=[];"
        f"autosize=1;strokeColor=none;fillColor=none;"
        f"fontColor={colors['font']};fontSize=11;"
    )


def build_relation_style(relation_type):
    style = RELATION_TYPE_STYLES.get(relation_type, DEFAULT_RELATION_STYLE)
    return (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;"
        f"html=1;strokeColor={style['stroke']};strokeWidth=2;"
        f"dashed={style['dashed']};endArrow={style['endArrow']};endFill={style['endFill']};"
        f"fontSize=11;fontColor={style['stroke']};"
    )


def kg_to_drawio(kg_data):
    mxfile = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(mxfile, "diagram", name=kg_data.get("meta", {}).get("title", "Knowledge Graph"))
    graph_model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "1200", "dy": "800", "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1", "pageWidth": "1654",
        "pageHeight": "1169", "math": "0", "shadow": "0",
    })
    root = ET.SubElement(graph_model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    entities = kg_data.get("entities", [])
    relations = kg_data.get("relations", [])
    positions = compute_layout(entities)

    cell_id_counter = 2
    entity_cell_ids = {}

    # Title
    meta = kg_data.get("meta", {})
    title_text = meta.get("title", "知识图谱")
    domain_text = meta.get("domain", "")
    title_label = f"<b>{title_text}</b>"
    if domain_text:
        title_label += f"<br><font style='font-size:11px;color:#666;'>{domain_text}</font>"

    title_cell = ET.SubElement(root, "mxCell", {
        "id": str(cell_id_counter),
        "value": title_label,
        "style": "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];autosize=1;strokeColor=none;fillColor=none;fontSize=18;fontStyle=1;fontColor=#333333;",
        "vertex": "1",
        "parent": "1",
    })
    ET.SubElement(title_cell, "mxGeometry", x="60", y="10", width="400", height="40", **{"as": "geometry"})
    cell_id_counter += 1

    for entity in entities:
        eid = entity["id"]
        pos = positions.get(eid, {"x": 60, "y": 60, "w": NODE_WIDTH, "h": NODE_HEIGHT})
        etype = entity.get("type", "core")
        props = entity.get("properties", [])

        type_badge = {"core": "Core", "attribute": "Attr", "enum": "Enum", "event": "Event", "role": "Role", "process": "Process"}.get(etype, etype)
        label = f"<b>{entity['name']}</b><br><font style='font-size:10px;color:#888;'>«{type_badge}» {entity.get('enName', '')}</font>"

        cell = ET.SubElement(root, "mxCell", {
            "id": str(cell_id_counter),
            "value": label,
            "style": build_entity_style(etype),
            "vertex": "1",
            "parent": "1",
        })
        ET.SubElement(cell, "mxGeometry", x=str(pos["x"]), y=str(pos["y"]),
                       width=str(pos["w"]), height=str(pos["h"]), **{"as": "geometry"})
        entity_cell_ids[eid] = str(cell_id_counter)
        cell_id_counter += 1

        for i, prop in enumerate(props[:8]):
            prop_name = prop.get("name", "")
            prop_type = prop.get("type", "")
            required_mark = " *" if prop.get("required") else ""
            prop_label = f"  {prop_name}: {prop_type}{required_mark}"

            prop_cell = ET.SubElement(root, "mxCell", {
                "id": str(cell_id_counter),
                "value": prop_label,
                "style": build_property_style(etype),
                "vertex": "1",
                "parent": entity_cell_ids[eid],
            })
            prop_y = 40 + i * PROP_ROW_HEIGHT
            ET.SubElement(prop_cell, "mxGeometry", x="5", y=str(prop_y),
                           width=str(NODE_WIDTH - 10), height=str(PROP_ROW_HEIGHT), **{"as": "geometry"})
            cell_id_counter += 1

        if len(props) > 8:
            more_cell = ET.SubElement(root, "mxCell", {
                "id": str(cell_id_counter),
                "value": f"  ... (+{len(props) - 8} more)",
                "style": build_property_style(etype),
                "vertex": "1",
                "parent": entity_cell_ids[eid],
            })
            prop_y = 40 + 8 * PROP_ROW_HEIGHT
            ET.SubElement(more_cell, "mxGeometry", x="5", y=str(prop_y),
                           width=str(NODE_WIDTH - 10), height=str(PROP_ROW_HEIGHT), **{"as": "geometry"})
            cell_id_counter += 1

    for relation in relations:
        src = relation.get("source", "")
        tgt = relation.get("target", "")
        if src not in entity_cell_ids or tgt not in entity_cell_ids:
            continue

        rtype = relation.get("type", "associates")
        label = relation.get("label", "")
        cardinality = relation.get("cardinality", "")
        edge_label = label
        if cardinality:
            edge_label += f"\n[{cardinality}]"

        edge = ET.SubElement(root, "mxCell", {
            "id": str(cell_id_counter),
            "value": edge_label,
            "style": build_relation_style(rtype),
            "edge": "1",
            "parent": "1",
            "source": entity_cell_ids[src],
            "target": entity_cell_ids[tgt],
        })
        ET.SubElement(edge, "mxGeometry", relative="1", **{"as": "geometry"})
        cell_id_counter += 1

    # Legend
    legend_y = max((p["y"] + p["h"] for p in positions.values()), default=200) + 60
    legend_cell = ET.SubElement(root, "mxCell", {
        "id": str(cell_id_counter),
        "value": "<b>图例</b>",
        "style": "text;html=1;align=left;verticalAlign=top;fontSize=12;fontStyle=1;fontColor=#333;strokeColor=none;fillColor=none;",
        "vertex": "1",
        "parent": "1",
    })
    ET.SubElement(legend_cell, "mxGeometry", x="60", y=str(legend_y), width="100", height="25", **{"as": "geometry"})
    cell_id_counter += 1

    for i, (etype, colors) in enumerate(ENTITY_TYPE_COLORS.items()):
        type_label = {"core": "核心实体", "attribute": "属性实体", "enum": "枚举", "event": "事件", "role": "角色", "process": "流程"}.get(etype, etype)
        legend_item = ET.SubElement(root, "mxCell", {
            "id": str(cell_id_counter),
            "value": type_label,
            "style": f"rounded=1;whiteSpace=wrap;html=1;fillColor={colors['fill']};strokeColor={colors['stroke']};fontColor={colors['font']};fontSize=10;align=center;",
            "vertex": "1",
            "parent": "1",
        })
        ET.SubElement(legend_item, "mxGeometry",
                       x=str(60 + i * 100), y=str(legend_y + 30),
                       width="90", height="30", **{"as": "geometry"})
        cell_id_counter += 1

    xml_str = ET.tostring(mxfile, encoding="unicode")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    lines = pretty.split("\n")
    return "\n".join(lines[1:])


def main():
    if len(sys.argv) != 3:
        print(f"用法: python {sys.argv[0]} <input.json> <output.drawio>")
        print(f"示例: python {sys.argv[0]} kg_payment.json kg_payment.drawio")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        kg_data = json.load(f)

    for field in ("entities", "relations"):
        if field not in kg_data:
            print(f"错误: JSON 缺少 '{field}' 字段")
            sys.exit(1)

    drawio_xml = kg_to_drawio(kg_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(drawio_xml)

    entity_count = len(kg_data["entities"])
    relation_count = len(kg_data["relations"])
    print(f"转换完成: {entity_count} 个实体, {relation_count} 条关系 → {output_file}")


if __name__ == "__main__":
    main()
