#!/bin/bash

# 简单部署脚本
# 使用方法: ./deploy-simple.sh

echo "🚀 开始部署..."

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 重新构建并启动
echo "🔨 重新构建并启动应用..."
docker-compose up --build -d

# 显示状态
echo "📊 容器状态:"
docker-compose ps

echo "✅ 部署完成！访问: http://localhost:8007"