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
    
    # 如果使用SQLite，确保数据目录存在
    if database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"创建数据库目录: {db_dir}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print(f"数据库初始化完成: {database_url}")

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