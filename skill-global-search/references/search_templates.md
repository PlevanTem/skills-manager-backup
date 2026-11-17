# 搜索词模板参考

## skills.sh CLI 查询词构造（信任 CLI 语义理解）

skills.sh CLI（`npx skills find`）已具备英文语义理解和模糊匹配能力，**不要做同义词扩展**。

| 搜索意图 | 用户输入示例 | CLI 查询词 |
|---------|------------|-----------|
| **精确名称** | "找 find-skills 这个 skill" | `find-skills` |
| **自然语言** | "自动生成饮食计划" | `generate meal plan automatically` |
| **自然语言** | "帮我做 PR review" | `help me review pull requests` |
| **领域关键词** | "react testing" | `react testing` |
| **模糊需求** | "竞品分析" | `competitor analysis` |
| **复合意图** | "把 md 材料生成 PPT" | `markdown to presentation slides` |

**识别精确名称的信号**：用户说"这个 skill"、"叫 xxx 的"、提供了含连字符的名称（如 `health-coach`）。

**skills.sh CLI 无结果时降级**：可尝试一次同义词扩展后重试，如 `meal plan` → `meal plan diet`，最多重试一次。

## GitHub 搜索词模板（4 路并行）

GitHub 搜索是纯文本匹配（不具备语义理解），适度使用同义词扩展。

| 策略 | 搜索词模板 | 说明 |
|------|-----------|------|
| 精确搜 | `github {关键词} repository stars` | 找高星仓库 |
| 合集搜 | `github awesome-{关键词} OR awesome {关键词} list` | 找 awesome 合集 |
| 工具搜 | `github {工具名} {关键词} library collection` | 找工具生态 |
| Skill 搜 | `"{关键词}" "SKILL.md" site:github.com` | 找真正的 Skill 仓库 |

## ClawHub API 搜索模板

ClawHub（https://clawhub.ai）是 OpenClaw 的公共技能市场（40,000+ skill），提供基于向量的语义搜索。

**Base URL**：`https://clawhub.ai/api/v1/`

**⚠️ 必须使用英文关键词**（中文语义搜索效果极差，已验证返回为空）。

### 搜索端点

| 功能 | 方法与路径 | 认证 | 说明 |
|------|-----------|------|------|
| 关键词搜索 | `GET /api/v1/search?q={英文关键词}` | 否 | 语义向量搜索，返回 slug/displayName/summary/score |
| 获取技能详情 | `GET /api/v1/skills/{slug}` | 否 | 获取完整信息，含 stats（downloads/installs/stars）和 owner |
| 浏览技能列表 | `GET /api/v1/skills?sort={排序}` | 否 | 支持排序：`trending`/`rating`/`installs`/`updated` |
| 获取版本列表 | `GET /api/v1/skills/{slug}/versions` | 否 | 查看历史版本 |

### 调用方式

**第二阶段搜索**——使用搜索 API：

```
web_fetch:
  url: "https://clawhub.ai/api/v1/search?q={英文关键词}"
  fetchInfo: "搜索 ClawHub 技能市场，提取技能名称、slug、描述"
```

**步骤 B-2 详情补全**——对去重后保留的每个 ClawHub skill 并行调用详情 API：

```
web_fetch:
  url: "https://clawhub.ai/api/v1/skills/{slug}"
  fetchInfo: "获取 ClawHub 技能详情：安装量、下载量、stars、owner"
```

### 响应格式

**搜索 API**（`/search?q=`）：
```json
{
  "results": [
    {
      "slug": "skill-slug",
      "displayName": "Skill Name",
      "summary": "一句话描述...",
      "score": 3.57,
      "updatedAt": 1774934409968
    }
  ]
}
```

**详情 API**（`/skills/{slug}`）：
```json
{
  "skill": {
    "slug": "skill-slug",
    "displayName": "Skill Name",
    "summary": "一句话描述...",
    "stats": {
      "downloads": 3210,
      "installsCurrent": 49,
      "installsAllTime": 51,
      "stars": 1,
      "comments": 0
    }
  },
  "owner": {
    "handle": "username",
    "displayName": "Username"
  }
}
```

### 速率限制

| 类型 | 匿名用户（按 IP） | 认证用户 |
|------|-----------------|---------|
| 读取 | 120/分钟 | 600/分钟 |
| 下载 | 20/分钟 | 120/分钟 |

超出限制时返回 429，响应头包含 `Retry-After` 秒数。

### 关键词构造示例

| 用户输入 | ClawHub 查询词 |
|---------|---------------|
| 视频剪辑 | `video editing` |
| 数据分析 | `data analysis` |
| 代码审查 | `code review` |
| 自动化测试 | `automated testing` |
| PPT 生成 | `presentation slides` |
| 竞品分析 | `competitor analysis` |

### 降级规则

ClawHub API 不可用时（返回非 200 状态码、超时、或 429 限流），标注 _ClawHub 不可用_，跳过该阶段，继续执行 GitHub 搜索。

## 示例

| 用户输入 | 精确搜 | 合集搜 | 工具搜 | Skill 搜 |
|---------|--------|--------|--------|----------|
| 提示词 | github prompt repository stars | github awesome-prompts OR awesome prompt list | github chatgpt prompt library collection | "prompt" "SKILL.md" site:github.com |
| SQL | github sql repository stars | github awesome-sql OR awesome sql list | github sql query builder library | "sql" "SKILL.md" site:github.com |
| 视频剪辑 | github video editing repository stars | github awesome-video OR awesome video-editing list | github ffmpeg video editor library | "video" "SKILL.md" site:github.com |
| 数据可视化 | github data visualization repository stars | github awesome-dataviz OR awesome data-visualization list | github d3 echarts visualization library | "visualization" "SKILL.md" site:github.com |
| API 测试 | github api testing repository stars | github awesome-api-testing OR awesome api test list | github postman api testing library | "api testing" "SKILL.md" site:github.com |

## 降级搜索（无 Node.js 时替代 skills.sh CLI）

| # | 搜索词模板 | 说明 |
|---|-----------|------|
| 1 | `skills.sh {英文关键词} skill` | 通过网页搜索 skills.sh 索引 |
| 2 | `github claude code skill {英文关键词}` | 搜索 Claude Code 生态 |
| 3 | `github awesome-{关键词} list` | 搜索 awesome 合集 |
| 4 | `clawhub.ai {英文关键词} skill` | 通过网页搜索 ClawHub 索引（ClawHub API 也不可用时的兜底） |
