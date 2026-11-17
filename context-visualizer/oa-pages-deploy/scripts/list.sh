#!/bin/bash
# list.sh - 列出 OA Pages 站点上已部署的文件
#
# 用法: ./list.sh [目录]
# 示例:
#   ./list.sh           # 列出所有文件
#   ./list.sh preview   # 仅列出 preview 目录
#   ./list.sh temp      # 仅列出 temp 目录

set -e

# ======================== 加载配置 ========================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

# 查找配置文件（支持两种形态：子技能内嵌 / 独立 skill）
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
    echo -e "${YELLOW}请先配置 OA Pages Deploy skill${NC}"
    echo -e "  - ${CYAN}${SKILL_DIR}/config.sh${NC}"
    echo -e "  - 或 ${CYAN}${HOME}/.workbuddy/skills/oa-pages-deploy/config.sh${NC}"
    exit 1
fi

# 加载配置
source "$CONFIG_FILE"

# 验证配置
if [ -z "$PREVIEW_REPO" ] || [ -z "$PREVIEW_DOMAIN" ]; then
    echo -e "${RED}❌ 配置不完整，请编辑: ${CYAN}${CONFIG_FILE}${NC}"
    exit 1
fi

# ======================== 检查仓库 ========================
if [ ! -d "$PREVIEW_REPO/.git" ]; then
    echo -e "${RED}❌ OA Pages 仓库不存在: $PREVIEW_REPO${NC}"
    exit 1
fi

cd "$PREVIEW_REPO"

TARGET_DIR="${1:-.}"

echo ""
echo -e "${BLUE}📚 OA Pages 站点文件列表${NC}"
echo -e "${DIM}   站点: ${PREVIEW_DOMAIN}${NC}"
echo -e "${DIM}   仓库: ${PREVIEW_REPO}${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 遍历文件
find "$TARGET_DIR" -type f \
    ! -path './.git/*' \
    ! -name '.gitignore' \
    ! -name '.DS_Store' \
    | sort \
    | while read -r file; do
    # 去掉开头的 ./
    clean_path="${file#./}"
    
    # 获取文件大小
    FILE_SIZE=$(ls -lh "$file" | awk '{print $5}')
    
    # 获取修改时间
    MOD_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$file" 2>/dev/null || stat --format="%y" "$file" 2>/dev/null | cut -d'.' -f1)

    # 根据目录上色
    case "$clean_path" in
        temp/*)   DIR_COLOR="${YELLOW}" ;;
        preview/*) DIR_COLOR="${CYAN}" ;;
        docs/*)   DIR_COLOR="${GREEN}" ;;
        assets/*) DIR_COLOR="${DIM}" ;;
        *)        DIR_COLOR="${NC}" ;;
    esac

    echo -e "  ${DIR_COLOR}📄 ${clean_path}${NC}"
    echo -e "     ${DIM}${FILE_SIZE} | ${MOD_TIME}${NC}"
    echo -e "     🔗 ${PREVIEW_DOMAIN}/${clean_path}"
    echo ""
done

# 统计
TOTAL=$(find "$TARGET_DIR" -type f ! -path './.git/*' ! -name '.gitignore' ! -name '.DS_Store' | wc -l | tr -d ' ')
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  共 ${GREEN}${TOTAL}${NC} 个文件"
echo ""
