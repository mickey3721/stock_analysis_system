#!/bin/bash
# ============================================
# 股票智能分析系统 - Docker部署脚本
# ============================================

set -e

echo "=========================================="
echo "   股票智能分析系统 Docker部署脚本"
echo "=========================================="
echo ""

# 配置GitHub私有仓库访问
echo "[步骤1/5] 配置GitHub访问..."
echo "请输入您的GitHub用户名:"
read GITHUB_USER

echo "请输入您的GitHub Personal Access Token (或密码):"
read -s GITHUB_TOKEN
echo ""

# 设置Git凭证
git config --global credential.helper store
echo "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials

# 创建项目目录
PROJECT_DIR="/opt/stock_analysis_system"
echo ""
echo "[步骤2/5] 克隆项目到 ${PROJECT_DIR}..."
cd /opt

if [ -d "$PROJECT_DIR" ]; then
    echo "目录已存在，更新代码..."
    cd "$PROJECT_DIR"
    git pull
else
    git clone https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/mickey3721/stock_analysis_system.git
    cd stock_analysis_system
fi

# 清理凭证
rm -f ~/.git-credentials

# 安装Docker (如果未安装)
echo ""
echo "[步骤3/5] 检查Docker..."
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker已安装"
fi

# 安装Docker Compose (如果未安装)
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose已安装"
fi

# 构建并启动
echo ""
echo "[步骤4/5] 构建并启动服务..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

# 等待服务启动
echo ""
echo "[步骤5/5] 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "=========================================="
echo "服务状态:"
docker-compose ps

# 获取服务器IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo "  前端地址: http://${SERVER_IP}:3006"
echo "  后端API:  http://${SERVER_IP}:8899"
echo "=========================================="
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
