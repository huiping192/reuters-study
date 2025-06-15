#!/bin/bash

# 等待数据库准备就绪
echo "等待数据库准备就绪..."
sleep 5

# 运行数据库迁移
echo "运行数据库迁移..."
flask db upgrade

# 启动应用
echo "启动应用..."
flask run --host=0.0.0.0 