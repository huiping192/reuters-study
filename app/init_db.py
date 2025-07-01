#!/usr/bin/env python3
"""
数据库初始化脚本
用于在服务器部署时初始化数据库，避免数据库文件冲突问题
"""

import os
import sys
from flask import Flask
from models.database import init_db, db
from utils.session_manager import SessionManager

def init_database():
    """初始化数据库"""
    app = Flask(__name__)
    
    # 配置session
    SessionManager.set_session_config(app)
    
    # 初始化数据库
    init_db(app)
    
    with app.app_context():
        # 确保数据目录存在
        if hasattr(app.config, 'SQLALCHEMY_DATABASE_URI'):
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri.replace('sqlite:///', '')
                data_dir = os.path.dirname(db_path)
                if data_dir and not os.path.exists(data_dir):
                    os.makedirs(data_dir)
                    print(f"创建数据目录: {data_dir}")
        
        # 创建所有表
        db.create_all()
        print("数据库表初始化完成")

if __name__ == '__main__':
    init_database()