@echo off
chcp 65001 >nul
title 股票智能分析系统 - Docker部署脚本

echo ==========================================
echo    股票智能分析系统 Docker部署脚本
echo ==========================================
echo.

:: 配置GitHub私有仓库访问
echo [步骤1/5] 配置GitHub访问...
set /p GITHUB_USER=请输入您的GitHub用户名: 
set /p GITHUB_TOKEN=请输入您的GitHub Personal Access Token: 

:: 创建项目目录
echo.
echo [步骤2/5] 克隆项目...

if exist "C:\stock_analysis_system" (
    echo 目录已存在，更新代码...
    cd /d C:\stock_analysis_system
    git pull
) else (
    git clone https://%GITHUB_USER%:%GITHUB_TOKEN%@github.com/mickey3721/stock_analysis_system.git C:\stock_analysis_system
    cd /d C:\stock_analysis_system
)

:: 检查Docker
echo.
echo [步骤3/5] 检查Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo 安装后重新运行此脚本。
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo 请确保Docker Compose已安装。
    pause
    exit /b 1
)

:: 构建并启动
echo.
echo [步骤4/5] 构建并启动服务...
docker-compose down
docker-compose up -d --build

:: 等待服务启动
echo.
echo [步骤5/5] 等待服务启动...
timeout /t 15

:: 显示状态
echo.
echo ==========================================
echo 部署完成!
echo ==========================================
echo 前端地址: http://localhost:3006
echo 后端API:  http://localhost:8899
echo ==========================================
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.

pause
