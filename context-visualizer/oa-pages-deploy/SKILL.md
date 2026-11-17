---
name: oa-pages-deploy
description: "在用户明确需要把本地 HTML、图片、CSS、JS 或静态资源部署到 OA Pages 预览站，并生成可分享的内网访问链接时触发。支持单文件部署、目录批量部署、智能目录分类、首次配置引导、部署结果链接返回和已部署文件管理。触发关键词：分享页面、上传到 OA、部署到 OA Pages、生成预览链接、生成访问链接、分享 HTML、内网链接、发给团队。不适用于：仅生成或本地预览 HTML、纯文本说明、代码调试、未明确要求分享/部署、目标仓库或域名不明确、内容包含密钥/token/cookie/个人信息/敏感数据且未确认脱敏授权的场景。"
triggers:
  - 分享页面
  - 上传到 OA
  - 部署到 OA Pages
  - 生成预览链接
  - 生成访问链接
  - 分享 HTML
  - 内网链接
  - 发给团队
  - 静态资源部署
phases: 3
---

# OA Pages Deploy

> 📦 **版本**: 1.0.0  
> 👤 **作者**: wanganming  
> 📅 **更新日期**: 2026-03-30  

将本地文件（HTML、图片、静态资源等）一键部署到 OA Pages 预览站，自动生成可分享的内网访问链接。

---

## 📋 功能概览

| 功能 | 说明 |
|------|------|
| 🚀 **一键部署** | 将本地文件快速推送到 OA Pages |
| 🔗 **自动生成链接** | 部署后立即返回可访问的分享链接 |
| 📁 **智能目录分类** | 根据文件类型自动放置到合适目录 |
| 📂 **批量部署** | 支持整个目录的批量上传 |
| 🗑️ **文件管理** | 支持查看和删除已部署文件 |

---

## 🚫 负向触发规则

以下场景不要触发 `oa-pages-deploy`：

- 用户只要求生成、本地预览或修改 HTML，没有明确要求分享、上传、部署或生成链接。
- 用户只要求纯文本说明、普通问答、代码调试或代码修复。
- 待部署内容包含密钥、token、cookie、个人信息、内部敏感数据或未授权材料时，必须先提醒脱敏并确认授权。
- `PREVIEW_REPO`、`PREVIEW_DOMAIN`、目标路径或目标仓库不明确时，不直接部署，先走配置/确认流程。
- 用户请求部署到不可信、非预期或未授权的地址时，先确认授权范围。

---

## 🔄 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        OA Pages Deploy 流程                      │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
  │  首次    │      │  用户    │      │  AI      │      │  生成    │
  │  配置    │ ───▶ │  请求    │ ───▶ │  部署    │ ───▶ │  链接    │
  └──────────┘      └──────────┘      └──────────┘      └──────────┘
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ 对话引导 │      │ "帮我分享│      │ 复制文件 │      │ 返回URL  │
  │ 收集仓库 │      │  这个HTML│      │ Git推送  │      │ 告知用户 │
  │ 信息     │      │  给团队" │      │ 到仓库   │      │          │
  └──────────┘      └──────────┘      └──────────┘      └──────────┘


  详细部署流程:
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │   本地文件                    OA Pages 仓库                      │
  │   ────────                    ─────────────                      │
  │                                                                 │
  │   /path/to/                   ~/.../preview-repo/               │
  │   └── report.html   ──复制──▶ └── docs/report.html              │
  │                                        │                        │
  │                                        ▼                        │
  │                               ┌─────────────────┐               │
  │                               │   git add       │               │
  │                               │   git commit    │               │
  │                               │   git push      │               │
  │                               └────────┬────────┘               │
  │                                        │                        │
  │                                        ▼                        │
  │                               ┌─────────────────┐               │
  │                               │   OA Pages      │               │
  │                               │   自动构建      │               │
  │                               │   (1-2分钟)     │               │
  │                               └────────┬────────┘               │
  │                                        │                        │
  │                                        ▼                        │
  │                               ┌─────────────────┐               │
  │                               │ https://xxx.    │               │
  │                               │ pages.woa.com/  │               │
  │                               │ docs/report.html│               │
  │                               └─────────────────┘               │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 部署形态（双模式）

本技能支持两种部署形态：

| 形态 | 位置 | 适用场景 |
|------|------|----------|
| **独立 skill** | `~/.workbuddy/skills/oa-pages-deploy/` | 单独使用、跨项目复用 |
| **子技能内嵌** | `<父技能>/oa-pages-deploy/`（如 `context-visualizer/oa-pages-deploy/`） | 与可视化技能联动，"生成即分享" |

两种形态共享同一份 `scripts/deploy.sh` 和 `scripts/list.sh`，脚本会按优先级自动查找配置文件：

1. 环境变量 `$OA_PAGES_CONFIG` 指定的路径
2. 脚本所在 skill 目录下的 `config.sh`（子技能内嵌形态）
3. `~/.workbuddy/skills/oa-pages-deploy/config.sh`（独立形态）

### 首次配置（对话引导）

**加载 skill 后，首先检查配置状态：**

```bash
# 通用检查：优先查找子技能内嵌配置，再查找独立 skill 配置
SKILL_DIR="$(dirname "$(realpath "$0" 2>/dev/null || echo "$BASH_SOURCE")")"
CANDIDATES=(
    "${SKILL_DIR}/config.sh"
    "$HOME/.workbuddy/skills/oa-pages-deploy/config.sh"
)
CONFIG_FILE=""
for c in "${CANDIDATES[@]}"; do
    [ -f "$c" ] && CONFIG_FILE="$c" && break
done

if [ -z "$CONFIG_FILE" ]; then
    echo "NEED_CONFIG"
else
    source "$CONFIG_FILE"
    if [ -z "$PREVIEW_REPO" ] || [ -z "$PREVIEW_DOMAIN" ]; then
        echo "NEED_CONFIG"
    else
        echo "CONFIGURED"
    fi
fi
```

### 如果输出 `NEED_CONFIG`，执行交互式配置引导

> ⚠️ **不要让用户手动编辑文件！通过对话收集信息，自动写入配置。**

#### 配置流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                      首次配置流程                                │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ 加载 Skill   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     是      ┌──────────────┐
  │ 检查配置文件 │ ──────────▶ │ 正常使用     │
  │ 是否完整？   │             └──────────────┘
  └──────┬───────┘
         │ 否
         ▼
  ┌──────────────────────────────────────────┐
  │ 🔧 首次配置 OA Pages Deploy              │
  │                                          │
  │ 我需要你的 OA Pages 仓库信息。           │
  │ 如果还没有创建，请先：                   │
  │                                          │
  │ 1. 打开工蜂创建一个新仓库                │
  │ 2. 仓库设置 → OA Pages → 启用            │
  │ 3. 把仓库 clone 到本地                   │
  │                                          │
  │ 请告诉我：                               │
  │ • 本地仓库的完整路径                     │
  │ • OA Pages 的预览域名                    │
  └──────────────────────────────────────────┘
         │
         ▼ 用户提供信息
  ┌──────────────────────────────────────────┐
  │ 用户：路径是 /Users/xxx/my-preview       │
  │      域名是 https://xxx-preview.pages... │
  └──────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │ AI 自动写入  │
  │ config.sh    │
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────────┐
  │ ✅ 配置完成！                            │
  │                                          │
  │ 已保存到 config.sh                       │
  │ • 本地仓库：/Users/xxx/my-preview        │
  │ • 预览域名：https://xxx-preview.pages... │
  │                                          │
  │ 现在可以开始部署文件了！                 │
  └──────────────────────────────────────────┘
```

#### 配置参数说明

| 配置项 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `PREVIEW_REPO` | ✅ | 本地仓库路径 | `/Users/xxx/projects/my-preview` |
| `PREVIEW_DOMAIN` | ✅ | OA Pages 域名 | `https://xxx-preview.pages.woa.com` |
| `REMOTE_BRANCH` | ❌ | 远程分支名（默认 `oa-pages`） | `oa-pages` |
| `LOCAL_BRANCH` | ❌ | 本地分支名（默认 `main`） | `main` |

#### 写入配置文件

收集到信息后，**自动生成并写入配置文件**。根据 skill 实际位置选择写入路径：

```bash
# 优先写入 skill 自身目录（子技能内嵌形态或独立 skill 皆可）
# SKILL_DIR 为本 SKILL.md 所在目录
CONFIG_FILE="${SKILL_DIR}/config.sh"
# 若 SKILL_DIR 不可写或未设置，回退到：
#   CONFIG_FILE="$HOME/.workbuddy/skills/oa-pages-deploy/config.sh"

mkdir -p "$(dirname "$CONFIG_FILE")"
cat > "$CONFIG_FILE" << 'EOF'
#!/bin/bash
# OA Pages Deploy 配置文件

# 【必填】本地仓库路径
PREVIEW_REPO="<用户提供的路径>"

# 【必填】预览域名
PREVIEW_DOMAIN="<用户提供的域名>"

# 【可选】远程分支名
REMOTE_BRANCH="oa-pages"

# 【可选】本地分支名
LOCAL_BRANCH="main"
EOF
```

---

## 📁 目录结构

### Skill 文件结构

```
<skill_root>/                       # 独立 skill 时：~/.workbuddy/skills/oa-pages-deploy/
                                    # 子技能内嵌时：<父技能>/oa-pages-deploy/
├── SKILL.md              # 技能说明文档（本文件）
├── config.sh             # 用户配置文件（PREVIEW_REPO / PREVIEW_DOMAIN）
└── scripts/
    ├── deploy.sh         # 部署脚本
    └── list.sh           # 列表脚本
```

### OA Pages 仓库目录约定

| 目录 | 用途 | URL 示例 |
|------|------|----------|
| `/`（根目录） | 重要/长期页面 | `https://<domain>/xxx.html` |
| `preview/` | 需求交互预览 | `https://<domain>/preview/xxx.html` |
| `docs/` | 文档类页面 | `https://<domain>/docs/xxx.html` |
| `temp/` | 临时文件（可随时清理） | `https://<domain>/temp/xxx.html` |
| `assets/` | 静态资源（图片、CSS、JS） | `https://<domain>/assets/xxx.png` |

### 自动分类规则

当用户未指定目标目录时，按以下规则自动选择：

```
用户请求                          自动放置目录
─────────────────────────────────────────────
"临时分享" / "temp"          ──▶  temp/
"交互预览" / "需求预览"      ──▶  preview/
"文档" / "报告" / "建议"     ──▶  docs/
图片/CSS/JS 等资源           ──▶  assets/
其他/重要内容                ──▶  根目录
```

---

## 🛠️ 使用方法

> 下方示例以"独立 skill"路径 `~/.workbuddy/skills/oa-pages-deploy/scripts/` 为例。
> 若是"子技能内嵌"形态，将路径替换为 `<父技能>/oa-pages-deploy/scripts/` 即可，例如：
> `/Users/houxiangcai/workspace/tnic_docs/context-visualizer/oa-pages-deploy/scripts/deploy.sh`

### 部署单个文件

```bash
# 基本用法
bash <skill_root>/scripts/deploy.sh <源文件路径> [目标文件名] [commit消息]

# 示例（独立 skill 形态）
bash ~/.workbuddy/skills/oa-pages-deploy/scripts/deploy.sh /path/to/report.html
bash ~/.workbuddy/skills/oa-pages-deploy/scripts/deploy.sh /path/to/file.html "docs/my-report.html" "docs: 添加报告"
```

### 部署整个目录

```bash
bash <skill_root>/scripts/deploy.sh --dir <源目录路径> [目标目录名] [commit消息]
```

### 查看已部署文件

```bash
bash <skill_root>/scripts/list.sh
```

### 删除已部署文件

```bash
bash <skill_root>/scripts/deploy.sh --delete <文件路径> [commit消息]
```

### 作为 context-visualizer 子技能被调用

当 `context-visualizer` 生成 HTML 后，可以通过本技能一键部署分享：

```bash
# context-visualizer 生成 HTML 到 /tmp/cv-<timestamp>.html 后
bash <context-visualizer>/oa-pages-deploy/scripts/deploy.sh \
  /tmp/cv-<timestamp>.html \
  "temp/<slug>.html" \
  "share: <标题>"
```

详见 `context-visualizer/SKILL.md` 的「一键分享到 OA Pages」章节。

---

## 💬 常见使用场景

### 场景 1：分享 HTML 页面

```
用户：把这个 HTML 文件分享给团队
AI：执行 deploy.sh → 返回链接
```

### 场景 2：部署需求交互预览

```
用户：把交互预览部署到 OA 上
AI：自动放到 preview/ 目录 → 返回链接
```

### 场景 3：部署临时页面

```
用户：临时分享一下这个页面
AI：自动放到 temp/ 目录 → 返回链接
```

### 场景 4：部署含资源的页面

如果 HTML 引用了本地图片或 CSS：

```
1. 先部署资源文件到 assets/
2. 修改 HTML 中的引用路径为 assets/xxx
3. 再部署 HTML 文件
```

---

## 📤 部署结果

部署成功后，**必须**告知用户：

```
✅ 部署成功！

🔗 访问链接：https://xxx-preview.pages.woa.com/docs/report.html

⏳ OA Pages 自动部署通常 1-2 分钟生效，如果 404 请稍等刷新
```

---

## ⚠️ 注意事项

| 事项 | 说明 |
|------|------|
| 🔒 内网访问 | OA Pages 仅限腾讯内网访问（需 TOF 登录） |
| ⏱️ 生效时间 | 部署后 1-2 分钟生效，404 请稍等刷新 |
| 🗑️ 临时文件 | `temp/` 目录的文件可以定期清理 |
| 📦 容量限制 | 大文件请注意工蜂仓库的容量限制 |
| 🔄 推送失败 | 如果 git push 失败，先执行 `git pull` 同步远程 |

---

## 📜 更新日志

### v1.0.0 (2026-03-30)

- ✨ 初始版本发布
- 🚀 支持单文件和目录部署
- 🔧 支持对话式首次配置引导
- 📁 支持智能目录分类
- 🗑️ 支持文件删除
