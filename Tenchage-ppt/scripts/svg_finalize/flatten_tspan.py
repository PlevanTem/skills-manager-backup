"""
svg_finalize.flatten_tspan
~────────────────────────────~
将 SVG 中带有 x/y/dy 定位属性的 ``<tspan>`` 元素
提升为独立的 ``<text>`` 元素，使 pptx 转换器能正确处理多行/多列文本布局。

DrawingML 的文本模型不支持在同一个 ``<a:r>``（文本运行）内
跳到新的 x/y 坐标，因此必须把定位型 ``<tspan>`` 拆成独立 ``<text>``。

公有 API
────────────
``flatten_text_with_tspans(tree: ElementTree) -> bool``
  遍历 SVG 元素树，将所有定位型 ``<tspan>`` 替换为独立 ``<text>``，
  返回是否有元素被改写。
"""
from __future__ import annotations

import copy
from xml.etree import ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"


def _is_positional(tspan: ET.Element) -> bool:
    """判断一个 ``<tspan>`` 是否带有定位属性（x / y / dy）。"""
    return any(attr in tspan.attrib for attr in ("x", "y", "dy"))


def _promote_tspan(parent_text: ET.Element, tspan: ET.Element) -> ET.Element:
    """
    将一个 ``<tspan>`` 提升为独立的 ``<text>`` 元素。

    - 继承父 ``<text>`` 的 x / y / 样式属性
    - 用 ``<tspan>`` 自己的 x / y（如有）覆盖
    - 文本内容取 ``<tspan>`` 的 text / tail
    """
    # 新建独立 <text>
    new_text = ET.Element(f"{SVG_NS}text")

    # 继承父 <text> 的属性
    for attr in ("x", "y", "font-family", "font-size",
                 "fill", "text-anchor", "font-weight"):
        if attr in parent_text.attrib:
            new_text.set(attr, parent_text.get(attr))

    # 用 tspan 自己的定位属性覆盖
    for attr in ("x", "y", "dx", "dy"):
        if attr in tspan.attrib:
            new_text.set(attr, tspan.get(attr))

    # 样式属性也覆盖
    for attr in ("font-family", "font-size", "fill",
                 "font-weight", "text-anchor"):
        if attr in tspan.attrib:
            new_text.set(attr, tspan.get(attr))

    # 文本内容
    if tspan.text:
        new_text.text = tspan.text

    return new_text


def flatten_text_with_tspans(tree: ET.ElementTree) -> bool:
    """
    遍历 *tree* 中的所有 ``<tspan>``，将带有定位属性的那些提升为独立 ``<text>``。

    返回 ``True`` 当且仅当有元素被改写。
    """
    root = tree.getroot()
    changed = False

    # 找到所有 <text> 元素
    for parent_text in root.iter(f"{SVG_NS}text"):
        # 收集需要提升的子 <tspan>
        to_promote = [
            child for child in parent_text
            if child.tag == f"{SVG_NS}tspan" and _is_positional(child)
        ]

        if not to_promote:
            continue

        # 逐个提升
        for tspan in to_promote:
            new_text = _promote_tspan(parent_text, tspan)
            # 插入到父 <text> 后面
            parent = parent_text.getparent() if hasattr(parent_text, "getparent") else None
            if parent is not None:
                idx = list(parent).index(parent_text)
                parent.insert(idx + 1, new_text)
            # 从父 <text> 中移除该 <tspan>
            parent_text.remove(tspan)
            changed = True

    return changed
