"""
Tenchage-ppt v3.3 · 伊利 5 大趋势演示 demo
=============================================
混合路线验证：python-pptx 文字（可编辑）+ SVG 图表（高级感）
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pptx import Presentation
from pptx.util import Inches

from tenchage_v32_layouts import (
    SLIDE_W, SLIDE_H,
    layout_chapter_premium,
    layout_data_chart_premium,
    layout_closing_premium,
    C_PRIMARY, C_PRIMARY_DEEP, C_ORANGE,
)


def build_yili_v33(out_path='Tenchage_v33_yili_demo.pptx'):
    pres = Presentation()
    pres.slide_width = Inches(SLIDE_W)
    pres.slide_height = Inches(SLIDE_H)
    blank = pres.slide_layouts[6]

    LOGO = '腾讯智慧零售  Tencent Smart Retail'

    # ---- Slide 1：章扉页 ----
    s = pres.slides.add_slide(blank)
    layout_chapter_premium(s,
        part_no='03',
        chapter_name='数据驱动',
        subtitle='全域消费者运营 · 五大趋势数据洞察',
        page_num=1)

    # ---- Slide 2：漏斗图 - 5 阶段链路 ----
    s = pres.slides.add_slide(blank)
    layout_data_chart_premium(s,
        title='伊利全域消费者运营漏斗',
        subtitle='5 阶段链路 · 从公域触达到口碑传播',
        left_sections=[
            {'label': '① 公域触达',
             'text': '8 大微信生态触点（视频号 / 朋友圈广告 / 搜一搜 / 公众号推荐流 / 看一看 / 支付后页面 / 附近小程序 / 腾讯广告），实现 5000 万人次曝光。',
             'highlight': '5000 万人次'},
            {'label': '② 流量承接',
             'text': '小程序进店 + 视频号直播间留资，承接公域流量约 1200 万，进店转化率 24%。',
             'highlight': '1200 万'},
            {'label': '③ 数据沉淀',
             'text': '会员注册、CDP 用户画像，实现 600 万数据资产沉淀。',
             'highlight': '600 万'},
            {'label': '④ 转化变现',
             'text': '小程序首单 + 视频号成交，180 万订单实现 GMV 突破。',
             'highlight': '180 万'},
        ],
        chart_template='funnel',
        chart_data={
            'title': '5 阶段漏斗',
            'stages': [
                {'label': '公域触达', 'value': '5000万', 'desc': ''},
                {'label': '流量承接', 'value': '1200万', 'desc': ''},
                {'label': '数据沉淀', 'value': '600万', 'desc': ''},
                {'label': '转化变现', 'value': '180万', 'desc': ''},
                {'label': '口碑传播', 'value': '45万', 'desc': ''},
            ],
        },
        chart_render_size=(1100, 1000),
        quote='全域漏斗每收窄一层，就是一次消费者关系的深化',
        logo_text=LOGO, page_num=2)

    # ---- Slide 3：雷达图 - 五大新动能能力评估 ----
    s = pres.slides.add_slide(blank)
    layout_data_chart_premium(s,
        title='伊利全域运营能力雷达',
        subtitle='当前 vs 目标 · 五大新动能维度评估',
        left_sections=[
            {'label': '当前优势',
             'text': '内容生产力 + 渠道融合度领先行业平均水平，在视频号和小程序双端表现亮眼。',
             'highlight': '内容生产力 + 渠道融合度'},
            {'label': '关键短板',
             'text': '公私域联动 + AI 智能化两个维度仍处于探索期，需重点投入资源补齐。',
             'highlight': '公私域联动 + AI 智能化'},
            {'label': '目标差距',
             'text': '6 个月内将整体能力从 3.0 分提升至 4.5 分，重点突破 AI 用户运营场景。',
             'highlight': '3.0 分提升至 4.5 分'},
        ],
        chart_template='radar',
        chart_data={
            'title': '能力评估',
            'axes': ['内容生产', '渠道融合', '公私域联动', 'AI 智能化', '即时零售'],
            'series': [
                {'name': '当前', 'values': [4, 4, 2, 2, 3], 'color': '#1A50D6'},
                {'name': '目标', 'values': [5, 5, 4, 4, 4], 'color': '#FF6A00'},
            ],
            'max': 5,
        },
        chart_render_size=(1000, 1000),
        quote='补齐公私域联动 + AI 短板，是 2026 年伊利全域运营的核心战役',
        logo_text=LOGO, page_num=3)

    # ---- Slide 4：环形进度 - Q1 关键指标 ----
    s = pres.slides.add_slide(blank)
    layout_data_chart_premium(s,
        title='伊利 2026 Q1 全域运营关键指标',
        subtitle='3 大核心指标 · 实时进度跟踪',
        left_sections=[
            {'label': 'GMV 完成率',
             'text': 'Q1 GMV 完成 78%，超出原定 70% 预期，主要驱动来自视频号直播单场破百万的 3 个爆款。',
             'highlight': '78%'},
            {'label': '新客占比',
             'text': '小程序新客占比 45%，环比 +12pp，公域投放 ROI 优于行业基准 30%。',
             'highlight': '45%'},
            {'label': '复购率',
             'text': '会员复购率 62%，企微 1V1 触达 + 社群运营双轮驱动，超额完成 55% 目标。',
             'highlight': '62%'},
        ],
        chart_template='ring_progress',
        chart_data={
            'title': 'Q1 三大指标',
            'rings': [
                {'label': 'GMV 完成率', 'value': 78, 'color': '#1A50D6'},
                {'label': '新客占比', 'value': 45, 'color': '#FF6A00'},
                {'label': '复购率', 'value': 62, 'color': '#0E2F7E'},
            ],
        },
        chart_render_size=(1000, 800),
        quote='三个数字背后，是伊利全域运营的真实增长引擎',
        logo_text=LOGO, page_num=4)

    # ---- Slide 5：阶梯递进 - 五级成熟度 ----
    s = pres.slides.add_slide(blank)
    layout_data_chart_premium(s,
        title='伊利全域运营成熟度路径',
        subtitle='五级跃迁 · 从触点投放到 AI 自营销',
        left_sections=[
            {'label': 'L1-L2 当前位置',
             'text': '伊利已完成基础触点投放和数据采集，处于「使用」级别，需向「整合」级跃迁。',
             'highlight': '使用'},
            {'label': 'L3-L4 6 个月目标',
             'text': '打通 CDP + 视频号 + 小程序数据回流，进入「整合」与「驾驭」阶段。',
             'highlight': '整合 + 驾驭'},
            {'label': 'L5 终局愿景',
             'text': '搭建 AI Agent 自动化运营，实现千人千面的智能营销闭环。',
             'highlight': 'AI Agent 自动化运营'},
        ],
        chart_template='stairs',
        chart_data={
            'title': '5 级成熟度模型',
            'levels': [
                {'label': 'L1', 'name': '尝试', 'desc': '偶尔投放'},
                {'label': 'L2', 'name': '使用', 'desc': '常态化触点'},
                {'label': 'L3', 'name': '整合', 'desc': '数据打通'},
                {'label': 'L4', 'name': '驾驭', 'desc': '组合策略'},
                {'label': 'L5', 'name': '创造', 'desc': 'AI 自营销'},
            ],
        },
        chart_render_size=(1200, 800),
        quote='每一级跃迁背后，都是一次组织能力的重构',
        logo_text=LOGO, page_num=5)

    # ---- Slide 6：封底 ----
    s = pres.slides.add_slide(blank)
    layout_closing_premium(s,
        brand='伊利',
        scenario='全域消费者运营 · 五大趋势数据洞察',
        date='2026.05',
        subtitle='Tenchage-ppt v3.3 · 混合路线（python-pptx + SVG）',
        logo_text=LOGO, page_num=6)

    pres.save(out_path)
    return out_path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'Tenchage_v33_yili_demo.pptx'
    p = build_yili_v33(out)
    print(f'✅ {p}')
    print(f'   文件大小：{os.path.getsize(p)/1024:.1f} KB')
