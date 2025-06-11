"""
数据库连接和初始化模块
"""
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# 创建SQLAlchemy实例
db = SQLAlchemy()

def init_db(app):
    """初始化数据库配置"""
    # 设置数据库URL，默认使用SQLite
    database_url = os.getenv('DATABASE_URL', 'sqlite:///vocabulary.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")

def get_db_connection():
    """获取数据库连接"""
    return db.session

def execute_sql(sql_query, params=None):
    """执行SQL查询"""
    try:
        if params:
            result = db.session.execute(text(sql_query), params)
        else:
            result = db.session.execute(text(sql_query))
        db.session.commit()
        return result
    except Exception as e:
        db.session.rollback()
        raise e 