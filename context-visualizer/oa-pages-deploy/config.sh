#!/bin/bash
# OA Pages Deploy 配置文件
# 首次使用时，AI 会通过对话引导你填写以下配置
# 支持两种加载方式：
#   1) 作为独立技能：~/.workbuddy/skills/oa-pages-deploy/config.sh
#   2) 作为 context-visualizer 子技能：<skill>/oa-pages-deploy/config.sh
# 两个脚本 (deploy.sh / list.sh) 会优先读取本文件的配置

# ============ 【必填】本地 OA Pages 仓库路径 ============
# 示例: /Users/yourname/projects/oa-pages-preview
PREVIEW_REPO=""

# ============ 【必填】OA Pages 预览域名（不带末尾斜线） ============
# 示例: https://yourname-preview.pages.woa.com
PREVIEW_DOMAIN=""

# ============ 【可选】远程分支名（默认 oa-pages） ============
REMOTE_BRANCH="oa-pages"

# ============ 【可选】本地分支名（默认 main） ============
LOCAL_BRANCH="main"
