# 可视化输出规范

本文档定义upward-reporting-coach-v2技能第二阶段的可视化输出标准。

---

## HTML一页纸汇报生成规范

### 设计理念

采用"编辑杂志风"设计语言，参考《哈佛商业评论》《经济学人》等专业刊物的内页风格，强调：
- 信息层级清晰
- 排版克制专业
- 避免AI感和过度装饰
- 适合快速阅读和打印

### 视觉规范

**色彩系统：**
- 底色：米白色 `#FAFAF8`
- 主文字：深墨色 `#1A1A1A`
- 标题：纯黑 `#000000`
- 强调色：砖红色 `#C1503D`（仅用于关键数字、重点标签）
- 辅助灰：`#6B6B6B`（用于次要信息）

**字体系统：**
- 标题字体：`'Noto Serif SC', 'Source Han Serif SC', serif`（衬线，传递权威感）
- 正文字体：`system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif`（无衬线，现代易读）
- 数字字体：`'SF Mono', 'Consolas', 'Monaco', monospace`（等宽，突出数据）

**字号层级：**
- 主标题：28-32px
- 核心结论：18-20px
- 数据标签：24px（加粗）
- 正文：14-16px
- 说明文字：12px

### HTML结构模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{汇报标题}} - 一页纸汇报</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #FAFAF8;
            color: #1A1A1A;
            font-family: system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            padding: 40px;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            border-bottom: 3px solid #C1503D;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
            font-size: 32px;
            font-weight: 700;
            color: #000;
            margin-bottom: 10px;
        }
        
        .header .meta {
            font-size: 14px;
            color: #6B6B6B;
        }
        
        .conclusion {
            background: #F5F5F3;
            border-left: 4px solid #C1503D;
            padding: 20px 24px;
            margin-bottom: 30px;
            font-size: 18px;
            font-weight: 500;
        }
        
        .data-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border: 1px solid #E5E5E5;
            padding: 20px;
            border-radius: 4px;
        }
        
        .card .number {
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 28px;
            font-weight: 700;
            color: #C1503D;
            margin-bottom: 8px;
        }
        
        .card .label {
            font-size: 14px;
            color: #6B6B6B;
        }
        
        .section {
            margin-bottom: 24px;
        }
        
        .section h2 {
            font-family: 'Noto Serif SC', 'Source Han Serif SC', serif;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #000;
        }
        
        .section p {
            font-size: 15px;
            line-height: 1.7;
            margin-bottom: 10px;
        }
        
        .action-box {
            background: #FFF9F5;
            border: 2px solid #C1503D;
            padding: 16px 20px;
            margin-top: 30px;
        }
        
        .action-box h3 {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #C1503D;
        }
        
        .action-box ul {
            list-style: none;
            padding-left: 0;
        }
        
        .action-box li::before {
            content: "▸ ";
            color: #C1503D;
        }
        
        @media print {
            body {
                padding: 20px;
            }
            .action-box {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{汇报标题}}</h1>
        <div class="meta">{{汇报人}} · {{日期}} · {{场景类型}}汇报</div>
    </div>
    
    <div class="conclusion">
        {{核心结论一句话}}
    </div>
    
    <div class="data-cards">
        <div class="card">
            <div class="number">{{关键数据1}}</div>
            <div class="label">{{数据1说明}}</div>
        </div>
        <div class="card">
            <div class="number">{{关键数据2}}</div>
            <div class="label">{{数据2说明}}</div>
        </div>
        <!-- 重复卡片结构，3-5个数据点 -->
    </div>
    
    <div class="section">
        <h2>{{模块标题1}}</h2>
        <p>{{模块内容}}</p>
    </div>
    
    <!-- 重复section结构 -->
    
    <div class="action-box">
        <h3>下一步行动</h3>
        <ul>
            <li>{{行动项1}}</li>
            <li>{{行动项2}}</li>
            <li>{{行动项3}}</li>
        </ul>
    </div>
</body>
</html>
```

### 内容组织规则

**必须包含的元素：**
1. 标题（汇报主题）
2. 元数据（汇报人、日期、场景类型）
3. 核心结论（一句话，20-30字）
4. 关键数据卡片（3-5个）
5. 主体内容（2-4个模块）
6. 下一步行动（如有）

**数据卡片提取原则：**
从话术中挑选3-5个最有冲击力的数据点，优先级：
1. 完成率/达成率
2. 同比/环比增长
3. 排名/占比变化
4. 风险指标
5. 资源效率指标

每个数据卡片包含：数字本身（大字体）+ 简短说明（小字体）

**主体内容组织：**
将话术中的主体部分按逻辑拆分成2-4个模块，每个模块：
- 标题：提炼模块主题（5-8字）
- 内容：保留What-So What-Now What结构，用自然段落呈现（去掉节奏标记）

---

## 专业信息图生成规范

### 调用baoyu-infographic的流程

**第1步：内容分析**

从话术中提取信息图所需的核心素材：
- 关键数据点（3-8个）
- 逻辑关系（时间顺序/因果关系/对比关系/层级关系）
- 核心结论（1-2句）
- 适合的图表类型（折线图/柱状图/饼图/流程图）

**第2步：布局选择**

根据内容特征选择合适的布局类型（baoyu-infographic支持21种布局），常用匹配：

| 内容特征 | 推荐布局 |
|---------|---------|
| 项目时间线、发展历程 | timeline（时间线布局） |
| 新旧对比、方案对比 | comparison（对比布局） |
| 流程说明、操作步骤 | process（流程布局） |
| 多维数据展示 | data-visualization（数据可视化布局） |
| 成果总结、多点呈现 | grid（网格布局） |
| 单一核心数据凸显 | hero-number（英雄数字布局） |

**第3步：风格选择**

根据汇报场景和受众选择视觉风格（baoyu-infographic支持20种风格），常用匹配：

| 汇报场景 | 推荐风格 |
|---------|---------|
| 高层汇报、正式述职 | professional-business（专业商务） |
| 项目汇报、进展同步 | flat-modern（扁平现代） |
| 数据密集型汇报 | minimalist-charts（简约图表） |
| 技术方案汇报 | gradient-tech（渐变科技） |
| 创新项目汇报 | creative-abstract（创意抽象） |

**第4步：调用技能生成**

构造调用指令：
```
请使用baoyu-infographic技能，基于以下内容生成信息图：

布局类型：{{选定的布局}}
视觉风格：{{选定的风格}}

内容要素：
- 标题：{{汇报主题}}
- 核心结论：{{一句话结论}}
- 数据点：
  1. {{数据点1}}：{{说明}}
  2. {{数据点2}}：{{说明}}
  ...
- 逻辑关系：{{描述内容之间的逻辑关系}}
```

**第5步：输出说明**

生成后告诉用户：
```
✅ 信息图已生成完毕。

📊 生成参数：
   - 布局：{{布局名称}}（适合{{场景说明}}）
   - 风格：{{风格名称}}（{{风格特点}}）
   
💡 使用建议：
   - 适合嵌入PPT作为封面页或总结页
   - 适合单独传播（如发送给领导预览、会后分享）
   - 建议下载为高分辨率PNG格式
```

### 信息图质量标准

**必须满足：**
- 标题清晰（汇报主题一目了然）
- 数据准确（与话术中的数据一致）
- 逻辑连贯（布局能清晰表达内容之间的关系）
- 视觉专业（不过度装饰、避免卡通感）

**避免：**
- 信息过载（超过8个数据点）
- 字体过小（关键信息难以识别）
- 颜色混乱（超过4种主题色）
- 布局与内容不匹配（如用时间线布局展示对比数据）

---

## 输出文件命名规范

**HTML一页纸汇报：**
`{{汇报主题}}_一页纸汇报_{{日期}}.html`

示例：`项目进展汇报_一页纸汇报_20260417.html`

**信息图：**
`{{汇报主题}}_信息图_{{日期}}.png`

示例：`Q1总结_信息图_20260417.png`

---

## 用户选择引导话术

当第一阶段完成后，用以下话术引导用户选择可视化类型：

```
💡 需要可视化版本吗？我可以基于这份话术生成：

1️⃣ HTML一页纸汇报（10秒）
   - 适合会前快速过目
   - 可打印成A4纸随身携带
   - 专业杂志风排版，信息层级清晰

2️⃣ 专业信息图（20-30秒）
   - 适合配套材料或会后传播
   - 可嵌入PPT作为封面/总结页
   - 21种布局×20种风格，自动匹配最佳组合

3️⃣ 两个都要

如需可视化，请直接告诉我选择哪一项，或描述你的具体需求（如"我要一张能展示时间线的信息图"）。
```

---

## 最佳实践建议

### 何时推荐HTML一页纸
- 汇报内容较多（超过5个模块）
- 需要纸质材料随身携带
- 领导习惯提前审阅材料

### 何时推荐信息图
- 核心数据点少而精（3-5个）
- 需要视觉冲击力
- 用于会后传播或内部分享

### 何时推荐两个都生成
- 重要汇报场景（述职、方案决策）
- 有充足的准备时间
- 需要多种材料形式应对不同场景

---

## 技术实现注意事项

### HTML生成
- 使用内联CSS，确保离线打开也能正常显示
- 避免外部依赖（字体、图片、脚本）
- 测试主流浏览器兼容性（Chrome/Safari/Edge）
- 确保打印样式正常（使用@media print）

### 信息图生成
- 调用baoyu-infographic前必须先分析内容特征
- 不要盲目使用默认布局和风格
- 如果第一次生成效果不佳，可调整布局/风格重新生成
- 生成后向用户说明选择该布局和风格的理由

---

本文档最后更新：2026-04-17 by upward-reporting-coach-v2
