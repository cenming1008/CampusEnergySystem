#!/bin/bash
# 日志清理脚本
# 清理超过指定天数的日志文件

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录的项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🧹 日志清理工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查日志目录是否存在
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}⚠️  日志目录不存在: $LOG_DIR${NC}"
    exit 0
fi

# 默认保留天数
DEFAULT_DAYS=7

# 解析参数
DAYS=${1:-$DEFAULT_DAYS}

echo -e "${YELLOW}📁 日志目录: $LOG_DIR${NC}"
echo -e "${YELLOW}📅 保留天数: $DAYS 天${NC}"
echo ""

# 统计日志文件
TOTAL_FILES=$(find "$LOG_DIR" -name "*.log" -type f 2>/dev/null | wc -l | xargs)
TOTAL_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)

echo -e "${BLUE}📊 当前状态：${NC}"
echo -e "   日志文件数: $TOTAL_FILES 个"
echo -e "   占用空间: $TOTAL_SIZE"
echo ""

# 查找超过指定天数的日志文件
OLD_FILES=$(find "$LOG_DIR" -name "*.log" -type f -mtime +$DAYS 2>/dev/null)
OLD_COUNT=$(echo "$OLD_FILES" | grep -c "\.log" 2>/dev/null || echo "0")

if [ "$OLD_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ 没有需要清理的日志文件${NC}"
    exit 0
fi

echo -e "${YELLOW}🗑️  发现 $OLD_COUNT 个超过 $DAYS 天的日志文件：${NC}"
echo ""
echo "$OLD_FILES" | while read -r file; do
    if [ -n "$file" ]; then
        FILE_SIZE=$(du -h "$file" 2>/dev/null | cut -f1)
        FILE_DATE=$(stat -f "%Sm" -t "%Y-%m-%d" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d' ' -f1)
        echo -e "   ${RED}❌${NC} $(basename "$file") ($FILE_SIZE, $FILE_DATE)"
    fi
done
echo ""

# 确认删除
read -p "$(echo -e ${YELLOW}是否删除这些文件？[y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}💡 已取消清理${NC}"
    exit 0
fi

# 执行删除
echo ""
echo -e "${YELLOW}🗑️  正在删除旧日志文件...${NC}"
DELETED=0
echo "$OLD_FILES" | while read -r file; do
    if [ -n "$file" ] && [ -f "$file" ]; then
        rm -f "$file"
        echo -e "   ${GREEN}✓${NC} 已删除: $(basename "$file")"
        ((DELETED++)) || true
    fi
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 清理完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 显示清理后的状态
NEW_FILES=$(find "$LOG_DIR" -name "*.log" -type f 2>/dev/null | wc -l | xargs)
NEW_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)

echo -e "${BLUE}📊 清理后状态：${NC}"
echo -e "   日志文件数: $NEW_FILES 个"
echo -e "   占用空间: $NEW_SIZE"
echo ""
