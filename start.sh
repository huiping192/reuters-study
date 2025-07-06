#!/bin/bash

# 等待数据库准备就绪
echo "等待数据库准备就绪..."
sleep 5

# 初始化数据库（确保数据库文件和基础结构存在）
echo "初始化数据库..."
python -c "
from app import app
with app.app_context():
    from models.database import init_db
    init_db(app)
    print('数据库初始化完成')
"

# 运行数据库迁移
echo "运行数据库迁移..."
flask db upgrade || {
    echo "迁移失败，标记当前状态为最新版本..."
    flask db stamp head
}

# 启动应用
echo "启动应用..."
flask run --host=0.0.0.0 