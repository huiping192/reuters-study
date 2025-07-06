"""
数据库连接和初始化模块
"""
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_migrate import upgrade

# 创建SQLAlchemy实例
db = SQLAlchemy()

def init_db(app):
    """初始化数据库表结构"""
    # 从app配置中获取数据库URL
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///vocabulary.db')
    
    # 如果使用SQLite，确保数据目录存在
    if database_url.startswith('sqlite:///'):
        # 处理相对路径和绝对路径
        if database_url.startswith('sqlite:////'):
            # 绝对路径，如 sqlite:////app/data/vocabulary.db
            db_path = database_url.replace('sqlite:///', '')
        else:
            # 相对路径，如 sqlite:///vocabulary.db
            db_path = database_url.replace('sqlite:///', '')
        
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    with app.app_context():
        # 检查是否存在migration配置
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'migrations')
        versions_dir = os.path.join(migrations_dir, 'versions')
        
        if os.path.exists(versions_dir) and os.listdir(versions_dir):
            # 存在migration文件，使用migration管理数据库
            try:
                upgrade()
            except Exception:
                # migration失败时回退到直接创建表
                db.create_all()
        else:
            # 没有migration文件，直接创建所有表
            db.create_all()

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