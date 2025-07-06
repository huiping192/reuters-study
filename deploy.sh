#!/bin/bash

# Reuters Study 部署脚本
# 使用方法: ./deploy.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 开始部署
print_info "开始部署 Reuters Study 应用..."
echo

# 检查是否在git仓库中
if [ ! -d ".git" ]; then
    print_error "当前目录不是git仓库！"
    print_info "请在项目根目录下运行此脚本"
    exit 1
fi

# 检查docker和docker-compose是否可用
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装或不可用！"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose 未安装或不可用！"
    exit 1
fi

# 显示当前分支和最新commit
print_info "当前git状态:"
git branch --show-current
git log --oneline -1
echo

# 拉取最新代码
print_info "拉取最新代码..."
if git pull origin main; then
    print_success "代码更新成功"
else
    print_error "代码拉取失败！"
    exit 1
fi
echo

# 停止现有容器
print_info "停止现有容器..."
docker-compose down

# 重新构建并启动
print_info "重新构建并启动应用..."
if docker-compose up --build -d; then
    print_success "应用启动成功！"
else
    print_error "应用启动失败！"
    exit 1
fi
echo

# 等待几秒让应用完全启动
print_info "等待应用完全启动..."
sleep 5

# 检查容器状态
print_info "检查容器状态..."
docker-compose ps

# 显示应用日志（最后20行）
echo
print_info "最新应用日志:"
docker-compose logs --tail=20 app

# 检查应用是否正常响应
echo
print_info "检查应用健康状态..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8007 | grep -q "200"; then
    print_success "应用正常运行！"
    print_info "访问地址: http://localhost:8007"
else
    print_warning "应用可能还在启动中，请稍等片刻后手动检查"
fi

echo
print_success "部署完成！"
print_info "使用 'docker-compose logs -f app' 查看实时日志"
print_info "使用 'docker-compose down' 停止应用"