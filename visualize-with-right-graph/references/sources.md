# 来源与规则账本

网页、官方文档及论文在线版本于 2026-11-09 核查。以下“规则”是面向 Agent 的工程转译，编号用于交叉定位。论文类型、产品能力和案例观察分别记录。

## 核查记录

| ID | 来源与定位 | 类型与核查所得 |
| --- | --- | --- |
| S1 | [Tamara Munzner，A Nested Model for Visualization Design and Validation（2009），§2、§3、图 2](https://www.cs.ubc.ca/labs/imager/tr/2009/NestedModel/NestedModel.pdf#page=2) | 设计与验证模型。区分领域问题、抽象、编码/交互、算法；上游错误向下游传导，验证威胁按层区分，§3.2 描述迭代 |
| S2 | [Matthew Brehmer、Tamara Munzner，A Multi-Level Typology of Abstract Visualization Tasks（2013），修正版 §3、图 1](https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/brehmer_infovis13-corrections.pdf#page=3) | 任务分类框架。区分 why/how/what；目标与位置是否已知影响查找，query 可识别、比较、概括。复杂工作可拆成任务序列 |
| S3 | [Edward Segel、Jeffrey Heer，Narrative Visualization: Telling Stories with Data（2010），§3.4、§4.2–4.4、§5](https://vis.stanford.edu/files/2010-Narrative-InfoVis.pdf#page=6) | 案例分析与设计空间。作者引导和读者探索可混合；§4.4 给出先引导后探索、交互幻灯片和下钻故事三种结构。没有为各用途测出通用最优结构 |
| S3a | [Gapminder Human Development Trends，S3 §3.4、图 4–5](https://vis.stanford.edu/files/2010-Narrative-InfoVis.pdf#page=4) | 历史案例观察。案例展示了分节总览、进度指示和可跳转导航。借鉴设计结构，当前运行状态和读者收益未验证 |
| S4 | [Ji Soo Yi、Youn ah Kang、John T. Stasko、Julie A. Jacko，Toward a Deeper Understanding of the Role of Interaction in Information Visualization（2007），§4](https://www.cs.tufts.edu/comp/250VA/papers/yi2007toward.pdf#page=3) | 系统与文献回顾提出按用户意图组织的七类交互。已读取 Tufts 托管的原论文；Duke 镜像返回 403，未用其补写证据。[书目与作者摘要](https://pubmed.ncbi.nlm.nih.gov/17968068/) |
| S5 | [Jeffrey Heer、Michael Bostock，Crowdsourcing Graphical Perception: Using Mechanical Turk to Assess Visualization Design（2010），实验 1A/1B、2、3](https://hci.stanford.edu/publications/2010/crowd-perception/heer-chi2010.pdf#page=2) | 感知实验。以特定比例、面积判断等任务比较编码，另考查网格对比及尺寸/网格间距。结果与刺激、任务及显示条件有关 |
| S6 | [OriginLab Products / Origin，Graphing、Data Exploration、Data Filter](https://www.originlab.com/index.aspx?go=Products/Origin) | 官方产品能力说明。用于寻找可能的绘图和探索能力，能力随版本与配置变化。产品页 cloud 镜像请求返回 502，已核对主站页面 |
| S7 | [OriginLab Data Filter 教程，What you will learn、步骤 2–11](https://docs.originlab.com/tutorials/data-filter/) | 官方能力和示例。列条件筛选可在指定重算配置下更新图和分析。教程的汽车散点与拟合是联动案例，不能证明筛选后的拟合有业务意义 |
| S8 | [OriginLab Graphical Exploration of Data，Data Reader / Data Highlighter](https://docs.originlab.com/user-guide/graphical-exploration-of-data/) | 官方能力。读取选点的坐标和元数据；高亮将图上的点关联到工作表行。编辑工作台中的删除、遮罩、取子集功能是否进入成品须按任务另定 |
| S9 | [OriginLab Plot Details Data Tab，Histogram 与 Box 等](https://docs.originlab.com/origin-help/pd-dialog-data-tab/)；[Creating Box Charts，可用统计定义](https://docs.originlab.com/origin-help/create-box-chart/) | 官方能力。可配置分箱及箱图等。需检查项目的设置，产品支持不能决定正确分箱或胡须定义 |
| S10 | [NIST/SEMATECH EDA Handbook，Histogram](https://www.itl.nist.gov/div898/handbook/eda/section3/histogra.htm)；[Contour Plot](https://www.itl.nist.gov/div898/handbook/eda/section3/eda33a.htm) | 官方技术手册。区分频数与面积归一化；等高线表示同响应水平，非规则网格通常涉及插值。领域选择仍需核查 |
| S11 | [W3C WCAG 2.2，1.1.1、1.4.1、1.4.13、2.1.1、2.4.7、2.5.7](https://www.w3.org/TR/WCAG22/) | Web 标准。非文本替代、用色、悬浮/焦点内容、键盘、焦点可见及拖动替代。一次冒烟检查只覆盖测试过的路径 |

## 决策规则与边界

| 规则 | 采用条件与行动 | 来源和局限 |
| --- | --- | --- |
| R01 上游优先 | 任务与数据含义会改变设计时先确认。发现错误回到最早有问题的层 | S1 模型；顺序、记录字段和回退机制是工程规则，未证实对 Agent 的提升 |
| R02 用操作选表达 | 把“了解情况”拆成要查、找、比或概括的目标。查值可用数或表。图族按主要分析任务检索 | S2 框架；布局和图族映射是工程规则，分类不能直接确定最优图 |
| R03 澄清/证据门槛 | 缺口会改变结论、比较或分母时询问；可逆偏好假设推进；证据不足时限制结论 | S1 领域威胁和上游假设；问答触发、因果和缺口处理是工程与统计规则，需结合业务定义 |
| R04 编码按读图精度取舍 | 精确比较优先共轴位置或显式数值，长度用有意义的零基线。面积可用于粗略份额，点图的非零刻度按可读性验证 | S5 感知实验；刻度、基线和替代方案为工程推导。不能用单项实验给所有图形和读者排序 |
| R05 按用途分配引导 | 解释或决策有证据链时引导，探索提供中性总览与自主路径。仅在多步证据需要时使用序列 | S3 分类，S3a 案例观察；监控、决策及标题策略是工程扩展，需读者测试 |
| R06 交互对应问题 | 先说明读者希望完成的操作，再增加最少控件 | S4 分类；分类不证明某控件更有效，也不要求每类实现 |
| R07 状态和口径同步 | 当选择或过滤影响一个以上的派生视图，从同一范围更新数据及文案，提供复位 | S7、S8 产品能力；标题、分母、空态、导出与复位是成品工程约束，Origin 操作本身没有效果证据 |
| R08 口径和变换可追溯 | 分母、配对、缺失、时间、区间或变换影响判断时，给公式、参数和覆盖。地理、网络及流向编码需有对应数据语义 | S1 数据/抽象分层，S9、S10 配置或技术例子；详细统计门槛和图族条件是工程规则。模型和领域标准另验 |
| R09 分层验收 | 从数据复算到实际渲染、操作与读者验证，分别标证据状态 | S1 分层验证，S5 感知实验方法；验收五层和对照方案是工程设计，不能从模型自检推断读者收益 |
| R10 科学编码需确认算法 | 需要读分布或响应场时核实分箱、归一化、网格、插值和领域约定 | S9 工具能力，S10 技术手册；它们不证明具体参数适合当前数据 |
| R11 交互可达且默认可读 | Web 控件用键盘和触屏可达路径；核心证据有稳定、可导出的入口 | S11 Web 标准，S4 交互框架；静态快照策略是工程扩展，专项合规需要独立审查 |
| R12 区分三种实现状态 | 分别记录设计适合、当前工具支持、成品已经运行；环境受限时保留可读降级 | S1 编码与算法层区分，S6–S9 产品文档；技术路线与降级策略是工程规则，依赖当前环境 |
