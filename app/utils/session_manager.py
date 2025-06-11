"""
简化的会话管理模块 - 单用户版本
"""
from models.user import User

class SessionManager:
    """简化的会话管理器 - 单用户版本"""
    
    # 固定的用户ID，因为只有一个用户
    FIXED_USER_ID = "single_user"
    
    @staticmethod
    def get_current_user():
        """获取当前用户对象（固定用户）"""
        return User.get_or_create_user(SessionManager.FIXED_USER_ID)
    
    @staticmethod
    def get_user_id():
        """获取用户ID（固定返回）"""
        return SessionManager.FIXED_USER_ID
    
    @staticmethod
    def update_user_activity():
        """更新用户活跃时间"""
        user = SessionManager.get_current_user()
        if user:
            user.update_last_active()
            from models.database import db
            db.session.commit()
    
    @staticmethod
    def set_session_config(app):
        """配置Flask session（简化版）"""
        import os
        
        # 设置session密钥
        app.secret_key = os.getenv('SECRET_KEY', 'single-user-secret-key')
        
        # 其他基本配置
        app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False
        app.config['SESSION_COOKIE_HTTPONLY'] = True 