#!/bin/bash
# deploy.sh - 将文件部署到 OA Pages 预览站
#
# 用法:
#   部署单文件:  ./deploy.sh <源文件路径> [目标文件名] [commit消息]
#   部署目录:    ./deploy.sh --dir <源目录路径> [目标目录名] [commit消息]
#   删除文件:    ./deploy.sh --delete <文件路径> [commit消息]
#
# 示例:
#   ./deploy.sh /path/to/page.html
#   ./deploy.sh /path/to/page.html docs/my-report.html "docs: 添加报告"
#   ./deploy.sh --dir /path/to/dist preview/my-app "feat: 部署应用"
#   ./deploy.sh --delete temp/old-file.html "chore: 清理临时文件"

set -e

# ======================== 加载配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色定义（提前定义，用于配置检查提示）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 查找配置文件（支持两种形态：子技能内嵌 / 独立 skill）
# 优先级：环境变量 > skill 同级 config.sh > ~/.workbuddy/skills/oa-pages-deploy/config.sh
CANDIDATE_CONFIGS=(
    "${OA_PAGES_CONFIG:-}"
    "${SKILL_DIR}/config.sh"
    "${HOME}/.workbuddy/skills/oa-pages-deploy/config.sh"
)

CONFIG_FILE=""
for c in "${CANDIDATE_CONFIGS[@]}"; do
    if [ -n "$c" ] && [ -f "$c" ]; then
        CONFIG_FILE="$c"
        break
    fi
done

if [ -z "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 未找到配置文件${NC}"
    echo ""
    echo -e "${YELLOW}首次使用需要配置，可用以下任一方式：${NC}"
    echo -e "1. 编辑子技能内嵌配置: ${CYAN}${SKILL_DIR}/config.sh${NC}"
    echo -e "2. 或放到独立 skill 目录: ${CYAN}${HOME}/.workbuddy/skills/oa-pages-deploy/config.sh${NC}"
    echo -e "3. 或通过环境变量指定: ${CYAN}OA_PAGES_CONFIG=/path/to/config.sh${NC}"
    echo ""
    exit 1
fi

# 加载配置
source "$CONFIG_FILE"

# 验证必填配置
check_config() {
    local has_error=0
    
    if [ -z "$PREVIEW_REPO" ] || [ "$PREVIEW_REPO" = "/Users/yourname/projects/my-preview-site" ]; then
        echo -e "${RED}❌ 请配置 PREVIEW_REPO (本地仓库路径)${NC}"
        has_error=1
    fi
    
    if [ -z "$PREVIEW_DOMAIN" ] || [ "$PREVIEW_DOMAIN" = "https://yourname-preview.pages.woa.com" ]; then
        echo -e "${RED}❌ 请配置 PREVIEW_DOMAIN (预览域名)${NC}"
        has_error=1
    fi
    
    if [ $has_error -eq 1 ]; then
        echo ""
        echo -e "${YELLOW}请编辑配置文件: ${CYAN}${CONFIG_FILE}${NC}"
        exit 1
    fi
    
    # 设置默认值
    REMOTE_BRANCH="${REMOTE_BRANCH:-oa-pages}"
    LOCAL_BRANCH="${LOCAL_BRANCH:-main}"
}

check_config

# ======================== 辅助函数 ========================
info()  { echo -e "${BLUE}ℹ️  $1${NC}"; }
ok()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

# ======================== 检查仓库 ========================
check_repo() {
    if [ ! -d "$PREVIEW_REPO/.git" ]; then
        fail "OA Pages 仓库不存在: $PREVIEW_REPO"
    fi
}

# ======================== 删除模式 ========================
delete_file() {
    local FILE_PATH="$1"
    local COMMIT_MSG="${2:-"chore: 删除 ${FILE_PATH}"}"

    check_repo
    cd "$PREVIEW_REPO"

    if [ ! -f "$FILE_PATH" ]; then
        fail "文件不存在: $PREVIEW_REPO/$FILE_PATH"
    fi

    info "正在删除: $FILE_PATH"
    git rm "$FILE_PATH"
    git commit -m "$COMMIT_MSG"
    git push origin ${LOCAL_BRANCH}:${REMOTE_BRANCH}

    echo ""
    ok "文件已删除并推送"
    echo -e "   📄 已删除: ${YELLOW}${FILE_PATH}${NC}"
}

# ======================== 部署目录模式 ========================
deploy_dir() {
    local SOURCE_DIR="$1"
    local TARGET_DIR="${2:-$(basename "$SOURCE_DIR")}"
    local COMMIT_MSG="${3:-"feat: 部署目录 ${TARGET_DIR}"}"

    check_repo

    if [ ! -d "$SOURCE_DIR" ]; then
        fail "源目录不存在: $SOURCE_DIR"
    fi

    info "正在部署目录..."
    echo "   📂 源目录: $SOURCE_DIR"
    echo "   📁 目标: $TARGET_DIR/"

    # 创建目标目录并复制
    mkdir -p "${PREVIEW_REPO}/${TARGET_DIR}"
    cp -r "${SOURCE_DIR}/"* "${PREVIEW_REPO}/${TARGET_DIR}/"
    ok "文件已复制"

    # 提交并推送
    cd "$PREVIEW_REPO"
    git add "${TARGET_DIR}/"
    
    # 检查是否有变更
    if git diff --cached --quiet; then
        warn "没有文件变更，跳过提交"
        return 0
    fi

    git commit -m "$COMMIT_MSG"
    git push origin ${LOCAL_BRANCH}:${REMOTE_BRANCH}

    # 统计文件数
    FILE_COUNT=$(find "${PREVIEW_REPO}/${TARGET_DIR}" -type f | wc -l | tr -d ' ')

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ok "部署成功！共 ${FILE_COUNT} 个文件"
    echo -e "   🔗 访问链接: ${GREEN}${PREVIEW_DOMAIN}/${TARGET_DIR}/${NC}"
    echo -e "   ⏳ OA Pages 自动部署通常 1-2 分钟生效"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ======================== 部署单文件模式 ========================
deploy_file() {
    local SOURCE_FILE="$1"
    local TARGET_NAME="${2:-$(basename "$SOURCE_FILE")}"
    local COMMIT_MSG="${3:-"feat: 部署 ${TARGET_NAME}"}"

    check_repo

    if [ ! -f "$SOURCE_FILE" ]; then
        fail "源文件不存在: $SOURCE_FILE"
    fi

    info "正在部署文件..."
    echo "   📄 源文件: $SOURCE_FILE"
    echo "   🎯 目标: $TARGET_NAME"

    # 如果目标包含子目录，确保目录存在
    TARGET_DIR=$(dirname "$TARGET_NAME")
    if [ "$TARGET_DIR" != "." ]; then
        mkdir -p "${PREVIEW_REPO}/${TARGET_DIR}"
    fi

    # 复制文件
    cp "$SOURCE_FILE" "${PREVIEW_REPO}/${TARGET_NAME}"
    ok "文件已复制"

    # 提交并推送
    cd "$PREVIEW_REPO"
    git add "$TARGET_NAME"

    # 检查是否有变更
    if git diff --cached --quiet; then
        warn "文件内容未变更，跳过提交"
        echo -e "   🔗 现有链接: ${GREEN}${PREVIEW_DOMAIN}/${TARGET_NAME}${NC}"
        return 0
    fi

    git commit -m "$COMMIT_MSG"
    git push origin ${LOCAL_BRANCH}:${REMOTE_BRANCH}

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ok "部署成功！"
    echo -e "   🔗 访问链接: ${GREEN}${PREVIEW_DOMAIN}/${TARGET_NAME}${NC}"
    echo -e "   ⏳ OA Pages 自动部署通常 1-2 分钟生效"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ======================== 主逻辑 ========================
case "${1}" in
    --delete)
        if [ -z "$2" ]; then
            fail "用法: $0 --delete <文件路径> [commit消息]"
        fi
        delete_file "$2" "$3"
        ;;
    --dir)
        if [ -z "$2" ]; then
            fail "用法: $0 --dir <源目录路径> [目标目录名] [commit消息]"
        fi
        deploy_dir "$2" "$3" "$4"
        ;;
    --help|-h)
        echo "OA Pages 部署工具"
        echo ""
        echo "用法:"
        echo "  $0 <源文件路径> [目标文件名] [commit消息]    部署单文件"
        echo "  $0 --dir <源目录> [目标目录名] [commit消息]  部署整个目录"
        echo "  $0 --delete <文件路径> [commit消息]           删除已部署文件"
        echo "  $0 --help                                    显示帮助"
        echo ""
        echo "示例:"
        echo "  $0 ./report.html"
        echo "  $0 ./report.html docs/report.html \"docs: 添加报告\""
        echo "  $0 --dir ./dist preview/my-app \"feat: 部署应用\""
        echo "  $0 --delete temp/old.html \"chore: 清理\""
        echo ""
        echo "当前配置:"
        echo "  站点: ${PREVIEW_DOMAIN}"
        echo "  仓库: ${PREVIEW_REPO}"
        echo "  分支: ${LOCAL_BRANCH} → ${REMOTE_BRANCH}"
        echo ""
        echo "配置文件: ${CONFIG_FILE}"
        ;;
    "")
        fail "缺少参数。运行 '$0 --help' 查看用法"
        ;;
    *)
        deploy_file "$1" "$2" "$3"
        ;;
esac
