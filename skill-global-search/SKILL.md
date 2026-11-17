---
name: skill-global-search
description: "从 skills.sh（90,000+ 技能库）、ClawHub（40,000+ 技能市场）和 GitHub 三源搜索、发现并安装 Agent Skills。当用户想查找、搜索、浏览或安装 skill 时触发。常见触发语：有没有skill、找个skill、搜skill、安装skill、install skill、search skill、find skill、skill for、推荐一个skill、推荐适合我的skill、我需要...的能力、有什么好用的skill、recommend skill。不用于与 skill 无关的普通网页搜索。"
---

# Skill 全局搜索

从 skills.sh（90,000+ 技能目录）、ClawHub（40,000+ 技能市场）和 GitHub 三源搜索，发现、评估并安装 Agent Skills。

## 核心规则

- **入口分流**：先判断用户意图——如果有明确搜索关键词 → 走「搜索流程」；如果是泛化推荐请求 → 走「智能推荐功能」
- 搜索分三阶段执行：先 skills.sh CLI（`npx skills find`），再 ClawHub API，再 GitHub。**三阶段都必须执行**，不得因前面阶段有结果而跳过后续阶段
- ClawHub API 搜索与 GitHub 搜索可在同一批次**并行发出**，不增加延迟
- 对 GitHub 搜索结果执行深度抓取以判断是否为真正的 Skill
- 最终输出始终包含四个分区（skills.sh Skill / ClawHub Skill / GitHub Skill / 普通开源项目），无结果的分区用斜体标注
- 输出前对三源结果去重（**同一 skill 只出现一次，优先级：skills.sh > ClawHub > GitHub**）

### 意图分流规则

| 用户输入 | 意图 | 走哪个流程 |
|---------|------|-----------|
| "搜一个 xxx skill" / "find skill for xxx" | 带关键词搜索 | 搜索流程 |
| "推荐适合我的 skill" / "有什么好用的 skill" | 泛化推荐 | 智能推荐功能 |
| "推荐一个 xxx skill" | 带方向的推荐 | 搜索流程（以 xxx 为关键词） |
| 搜索流程无结果时 | 降级推荐 | 智能推荐功能（作为 fallback） |

---

## 搜索流程

### 第一阶段：skills.sh CLI 搜索

构造关键词后发起 skills.sh CLI 搜索。允许 1-2 路搜索（如用不同关键词或同义词扩展）：

```
execute_command: node --version && npx skills find "{关键词A}"
execute_command: npx skills find "{关键词B}"    ← 可选第二路，用同义词或更精确/宽泛的词
```

**关键词构造**：
- 简单核心词优先（`ppt` 优于 `ppt generate`），先粗后细
- 自然语言描述 → 提取 1-2 个英文核心词
- 避免长句（`"review my code for bugs"` → `code review`）

Node.js 不可用时：引导安装（macOS: `brew install node`）。用户拒绝 → 标注 _skills.sh CLI 不可用_，跳到第二阶段。

### 第二阶段：ClawHub API 搜索

skills.sh CLI 搜索完成后，**必须继续执行 ClawHub API 搜索**。ClawHub 是 OpenClaw 的公共技能市场（40,000+ skill），提供向量语义搜索。

**⚠️ 必须使用英文关键词**（中文语义搜索效果差，已验证）。将中文需求翻译为英文核心词后调用：

```
web_fetch:
  url: "https://clawhub.ai/api/v1/search?q={英文关键词}"
  fetchInfo: "搜索 ClawHub 技能市场，提取技能名称、slug、描述"
```

> 此调用与第三阶段 GitHub 搜索在同一批次**并行发出**。

**API 说明**：
- Base URL：`https://clawhub.ai/api/v1/`
- 无需认证，匿名 120 次/分钟
- 搜索 API 返回：`slug`、`displayName`、`summary`、`score`（不含安装量）
- 详情 API（`/api/v1/skills/{slug}`）返回完整 `stats`：`downloads`、`installsCurrent`、`installsAllTime`、`stars`
- 支持语义搜索（向量匹配），不仅是关键词匹配

**ClawHub 不可用时**（API 返回错误或超时）：标注 _ClawHub 不可用_，继续执行第三阶段。

### 第三阶段：GitHub 搜索

**前两阶段完成后，无论是否有结果，必须继续执行以下 GitHub 搜索。** 将中文需求翻译为英文核心词：

```
web_search: "github {英文关键词} repository stars"
web_search: "github awesome-{英文关键词} OR awesome {英文关键词} list"
web_search: "github {工具名} {英文关键词} library collection"
web_search: "{英文关键词} SKILL.md site:github.com"
```

这 4 路 GitHub 搜索在同一批次并行发出。详见 `references/search_templates.md`。

### 步骤 B：深度抓取与分类

GitHub 搜索有结果时，选择 1-3 个高价值仓库执行 `web_fetch`（GitHub 搜索全部无相关结果时跳过）：

```
web_fetch:
  url: "https://github.com/{owner}/{repo}"
  fetchInfo: "获取仓库描述、stars、主要功能、是否包含 SKILL.md 文件"
```

优先顺序：含 SKILL.md 的仓库 > 高 stars 仓库 > awesome- 合集 > 相关专业仓库。

**Skill 判断标准（满足任一即为 Skill）：**
- 仓库包含 SKILL.md 文件
- 仓库路径包含 `.claude/skills/`、`.codebuddy/skills/` 或 `skills/` 目录结构
- 仓库在 skills.sh 索引中（来自 skills.sh CLI 搜索结果）
- README 明确说明是 "Claude Code Skill" 或 "Agent Skill"

不满足以上条件的归类为"相关开源项目"。

**去重**：`owner/repo` 相同的仓库只在 skills.sh 分区展示，GitHub 分区排除。

### 步骤 B-2：ClawHub 详情补全

三源去重后，对 ClawHub 分区中**最终保留的每个 skill** 并行调用详情 API 获取安装量等指标：

```
web_fetch:
  url: "https://clawhub.ai/api/v1/skills/{slug}"
  fetchInfo: "获取 ClawHub 技能详情：安装量、下载量、stars、owner"
```

> 去重后 ClawHub 分区通常只剩 3-5 个，全部并行调用不会增加显著延迟。如果详情 API 调用失败，安装量列显示 `-`，不影响其他输出。

### 步骤 C：输出结果

**输出前校验**：四个分区均存在 | 编号跨分区连续 | 每条有说明和超链接 | skills.sh 含安装量 | ClawHub 含下载量和安装量 | 三源已去重 | 包含环境检测

**必须**按以下格式输出：

```markdown
找到 N 个关于 "{关键词}" 的资源：

## 📦 来自 skills.sh - 可直接安装

| # | Skill | 说明 | 近7日安装 |
|---|-------|-----|------|
| 1 | [{名称}](https://skills.sh/s/{id}) | {一句话描述} | 🔥 {N}次 |

## 🐾 来自 ClawHub - 可直接安装

| # | Skill | 说明 | 下载 | 安装 |
|---|-------|-----|------|------|
| 2 | [{名称}](https://clawhub.ai/skills/{slug}) | {一句话描述} | {downloads} | {installsCurrent} |

## ✅ GitHub 上的 Skill - 可直接安装

| # | 项目 | ⭐ Stars | 说明 |
|---|-----|---------|------|
| 3 | [{owner/repo}](https://github.com/{owner}/{repo}) | ⭐ {N} | {一句话描述} |

## 🔗 相关开源项目 - 非 Skill（可封装）

| # | 项目 | ⭐ Stars | 说明 | 封装建议 |
|---|-----|---------|------|---------|
| 4 | [{owner/repo}](url) | ⭐ {N} | {一句话描述} | 输入"帮我把 {repo} 封装成 skill" |

### 💡 推荐

**最佳匹配：#{编号} {名称}**
- ✅ {匹配理由1}
- ✅ {匹配理由2}

🖥️ 检测到当前运行在 **{平台名称}** 中，安装将默认仅安装到 {平台名称}。如需一次性安装到所有平台，请说"全平台安装 #编号"。

需要我帮你安装某个 Skill 吗？告诉我编号即可（如"安装 #1"或"全平台安装 #2"）。
```

**环境检测**：根据 system prompt 或工作区路径识别当前平台（CodeBuddy / Claude Code / Kiro 等），无法识别时省略 🖥️ 行。

---

## 安装流程

当用户选择安装某个 Skill 时，直接执行安装。

**默认方式 — 使用安装脚本（必须）：**
```bash
bash scripts/install_skill.sh {github_url} {skill-name}
```
安装脚本自动完成：克隆仓库 → 安全扫描（13 项检测） → 定位 SKILL.md → 复制到 `.codebuddy/skills/{name}/` → 验证。

扫描发现风险时脚本会中止并输出详情，按 `references/security_audit.md` 中的规则向用户解释风险。用户确认后可加 `--skip-audit` 跳过扫描重装。

**ClawHub 来源的 Skill — 根据当前平台自动决策：**

AI 根据当前运行平台自动选择安装方式，**无需询问用户**：

| 当前平台 | 安装方式 | 原因 |
|---------|---------|------|
| **CodeBuddy** | 通过其 GitHub 源地址走 `install_skill.sh` | `npx clawhub install` 装到 `./skills/`（OpenClaw 路径），CodeBuddy 不识别；必须装到 `.codebuddy/skills/` |
| **Claude Code** | 通过其 GitHub 源地址走 `install_skill.sh` | 同理，需装到 `.claude/skills/` |
| **OpenClaw** | `npx clawhub@latest install {slug}` | OpenClaw 原生识别 `./skills/` 路径，直接安装即可 |
| **其他/未知** | 通过 GitHub 源地址走 `install_skill.sh` | 安全兜底，确保装到当前平台的 skill 目录 |

> ClawHub 技能详情页（`https://clawhub.ai/skills/{slug}`）通常包含其 GitHub 源地址，抓取该页面即可获取。
> **依赖**：需要 Node.js（与 skills.sh CLI 相同）。

**全平台安装 — 仅当用户明确说"全平台安装"时：**
```bash
npx skills add {owner/repo} -y
```
> npx 安装不经过安全扫描，安装路径由 npx 决定。仅在用户明确要求全平台安装时使用。

更多命令参考见 `references/commands_and_troubleshooting.md`。

**安装后提示：** Skill 已安装到 `.codebuddy/skills/{name}/`，下次对话中输入相关关键词即可自动触发。

---

## 降级规则

当搜索过程中遇到异常，按以下策略降级处理：

- **skills.sh CLI 不可用（Node.js 未安装且用户拒绝安装）** → 增加一路 `web_search: "skills.sh {关键词}"` 替代，使用 `references/search_templates.md` 中的降级搜索模板
- **ClawHub API 不可用（返回错误/超时/429 限流）** → 标注 _ClawHub 不可用_，跳过该阶段继续后续搜索
- **GitHub 搜索全部无结果** → 扩展关键词（加同义词或相关工具名），最多重试一次
- **web_fetch 抓取失败或超时** → 跳过深度抓取，基于搜索结果摘要进行 Skill/非Skill 分类
- **全部搜索均无结果** → 自动切换到「智能推荐功能」，基于用户画像推荐相关 skill；同时建议：调整关键词、尝试英文搜索、或浏览 https://skills.sh 和 https://clawhub.ai

---

## 智能推荐功能

泛化推荐请求（"推荐适合我的 skill"、"有什么好用的 skill"等）时启用此流程。已安装的 skill 是**用户画像的核心输入信号**，据此推荐互补、增强或上下游的 skill。

所有映射表、角色判定表、排序规则、反模式详见 `references/recommend_templates.md`。

### 步骤 R1：本地环境扫描（并行执行）

并行发起以下 tool call：

```
Tool call 1: execute_command: ls -1 ~/.codebuddy/skills/ 2>/dev/null; echo "---"; ls -1 ~/.claude/skills/ 2>/dev/null
Tool call 2: execute_command: ls -1 .codebuddy/skills/ 2>/dev/null; echo "---"; ls -1 .claude/skills/ 2>/dev/null
Tool call 3: list_dir 工作区根目录（depth=2，仅看结构，不读内容）
Tool call 4: execute_command: for d in ~/.codebuddy/skills/*/; do echo "=== $(basename $d) ==="; head -5 "$d/SKILL.md" 2>/dev/null; done
Tool call 5: read_file README.md（limit=30）    ← 项目定位的第一信号源，必须读取
Tool call 6（代码项目时）: 读取依赖文件前 20 行（如 package.json / requirements.txt）
```

> Tool call 5 是业务领域推断的**最高优先级信号**。README.md 通常在前几行就写明了项目定位（如"XX 管理平台"、"智能 XX 助手"），这比目录名和依赖文件更直接、更准确。
> - 根目录 README.md 不存在时，从 Tool call 3（list_dir）的结果中查找其他项目说明文件（如 `*/README.md`、`ABOUT.md` 等），自行判断是否值得读取
> - 均不存在则跳过，加大 AI 记忆和目录名信号的权重

### 步骤 R2：构建用户画像

1. **采集信号**：已安装 skill（名称+description） → 已有能力和用户倾向；工作区结构 → 工作场景；AI 记忆 → 关注点
2. **推断角色**：综合信号匹配角色判定表（`references/recommend_templates.md`），确定角色搜索词候选池。信号不足时标注"通用用户"
3. **推断业务领域**（代码项目时）：按优先级 README.md 定位 > AI 记忆 > 目录名 > 依赖文件推断项目的**业务领域**（参见 `references/recommend_templates.md` 项目业务领域推断）。产出 1-2 个领域搜索词，记为 `领域词`。核心原则：**README.md 说的业务定位 > 目录名/依赖暗示的技术栈**
4. **识别缺口**：用以下检验问题过滤每个候选缺口——"**这个角色的人，会日常使用 AI 工具做这件事吗？**"
   - ✅ 产品经理 → 竞品分析、用户调研报告、需求优先级排序（产品经理日常工作）
   - ❌ 产品经理 → code review、技术方案评审、API 测试（这是开发者的日常工作，即使产品经理偶尔参与评审，也不会用 AI skill 来做）

内部画像格式：
```
用户角色 / 工作场景 / 业务领域（如适用） / 技术栈（如适用） / 已覆盖领域 / 用户倾向 / 潜在需求
```

### 步骤 R3：基于画像搜索推荐（并行执行）

**⚠️ 强制规则：角色明确时，必须按以下顺序构造搜索词。不得跳过第 1 步和第 2 步。**

角色明确时，按以下固定顺序执行：

1. **取角色搜索词**：从角色判定表候选池中取出未被已安装 skill 覆盖的第一个词 → 记为 `角色词A`，第二个词 → 记为 `角色词B`
2. **取领域词**：从 R2 第 3 步的业务领域推断中取出最相关的词 → 记为 `领域词`（代码项目必须有此步，非代码项目跳过）
3. **取缺口词**：从 R2 第 4 步的缺口分析中取最相关的词 → 记为 `缺口词`
4. **取场景词**：从工作区特征或 AI 记忆中取 → 记为 `场景词`
5. **分配到搜索位**（有领域词时优先占位）：

在同一批次中**恰好发起以下 tool call，不多不少**：

**代码项目（有领域词）：**
```
Tool call 1: execute_command: npx skills find "{角色词A}"          ← 必须是角色词
Tool call 2: execute_command: npx skills find "{领域词}"           ← 业务领域词（来自 README/目录名）
Tool call 3: web_fetch: "https://clawhub.ai/api/v1/search?q={缺口词}"  ← ClawHub 语义搜索
Tool call 4: web_search: "{角色词B} SKILL.md site:github.com"     ← 必须含角色词
Tool call 5: web_search: "github {缺口词} agent skill"            ← 开发提效/能力缺口词
```
> 共 5 个 tool call，**禁止追加第 6 个**。ClawHub 占 1 路（Tool call 3），与其他 tool call 并行执行。

**非代码项目（无领域词）：**
```
Tool call 1: execute_command: npx skills find "{角色词A}"          ← 必须是角色词
Tool call 2: execute_command: npx skills find "{缺口词}"
Tool call 3: web_fetch: "https://clawhub.ai/api/v1/search?q={场景词}"  ← ClawHub 语义搜索
Tool call 4: web_search: "{角色词B} SKILL.md site:github.com"     ← 必须含角色词
Tool call 5: web_search: "github {场景词} agent skill"
```
> 同样 5 个 tool call。

角色不明确时（"通用用户"），跳过角色词，Tool call 1-2 用领域词/场景词 + 映射表搭配词，Tool call 3 用 ClawHub 搜缺口词，Tool call 4-5 用缺口词 + 记忆痛点。

搜索词构造：简单核心词优先，先粗后细，避免自然语言长句。

### 步骤 R4：输出推荐结果

```markdown
## 🎯 为你智能推荐的 Skill

### 你的环境概览
- **工作场景**：{识别到的场景}
- **业务领域**：{推断出的业务领域，如适用}
- **已安装 {N} 个 skill**：{skill 名称列表}
- **推荐依据**：{一句话说明推荐逻辑}

### 推荐列表

| # | Skill | 推荐理由 | 来源 | 安装命令 |
|---|-------|---------|------|---------|
| 1 | [{名称}](链接) | {基于画像的推荐理由} | skills.sh / ClawHub / GitHub | `npx skills add {id}` |

### 💡 最佳推荐

**#{编号} {名称}** — {推荐理由}
- ✅ 与你已有的 {skill_name} 形成互补
- ✅ {具体场景说明}

需要安装吗？告诉我编号即可。
```

**输出前校验**：推荐列表 2-5 条（超过 5 条必须截断取前 5）| 每条有基于画像的具体理由 | 不含已安装 skill

---

## 相关资源

- 浏览所有 skills: https://skills.sh
- 浏览 ClawHub 技能市场: https://clawhub.ai
- ClawHub HTTP API: https://clawhub.ai/api/v1/ （无需认证，支持语义搜索）
- 创建自己的 skill: 使用 **skill-creator** skill
- 搜索词模板: `references/search_templates.md`
- 推荐策略模板: `references/recommend_templates.md`
- 命令参考与排查: `references/commands_and_troubleshooting.md`
- 安装前安全审查规则: `references/security_audit.md`
