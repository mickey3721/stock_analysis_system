#!/bin/bash
# ============================================
# 股票智能分析系统 - Docker部署脚本
# ============================================
# 使用说明：
# 1. 修改下方 GITHUB_USER 和 GITHUB_TOKEN
# 2. 执行: sudo bash deploy.sh
# ============================================

# ============ 请修改以下配置 ============
GITHUB_USER="你的GitHub用户名"
GITHUB_TOKEN="你的GitHub Personal Access Token"
PROJECT_DIR="/opt/stock_analysis_system"
# ======================================

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   股票智能分析系统 Docker部署脚本${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# 检查配置
if [ "$GITHUB_USER" = "你的GitHub用户名" ] || [ -z "$GITHUB_USER" ]; then
    echo -e "${YELLOW}[错误] 请先修改脚本中的 GITHUB_USER 变量${NC}"
    exit 1
fi

if [ "$GITHUB_TOKEN" = "你的GitHub Personal Access Token" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}[错误] 请先修改脚本中的 GITHUB_TOKEN 变量${NC}"
    exit 1
fi

echo -e "${GREEN}[1/5] 配置GitHub访问...${NC}"
echo "用户: $GITHUB_USER"

# 设置Git凭证
git config --global credential.helper store
echo "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials 2>/dev/null || true

# 克隆项目
echo ""
echo -e "${GREEN}[2/5] 克隆项目到 ${PROJECT_DIR}..."
cd /opt

if [ -d "$PROJECT_DIR" ]; then
    echo "目录已存在，更新代码..."
    cd "$PROJECT_DIR"
    git pull https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/mickey3721/stock_analysis_system.git 2>/dev/null || git pull
else
    git clone https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/mickey3721/stock_analysis_system.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# 清理凭证
rm -f ~/.git-credentials

# 安装Docker
echo ""
echo -e "${GREEN}[3/5] 检查Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker已安装: $(docker --version)"
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose已安装: $(docker-compose --version)"
fi

# 构建并启动
echo ""
echo -e "${GREEN}[4/5] 构建并启动服务...${NC}"
docker-compose down 2>/dev/null || true
docker-compose up -d --build

# 等待服务启动
echo ""
echo -e "${GREEN}[5/5] 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo ""
echo "=========================================="
echo "服务状态:"
docker-compose ps

# 获取服务器IP
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  部署完成!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo -e "  前端地址: http://${SERVER_IP}:3006"
echo -e "  后端API:  http://${SERVER_IP}:8899"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
