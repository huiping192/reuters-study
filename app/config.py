# config.py
import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """集中式配置管理类"""

    def __init__(self):
        # 加载.env文件（开发环境）
        load_dotenv(override=True)

        # API密钥配置
        self.REPLICATE_API_TOKEN: str = self._get_required('REPLICATE_API_TOKEN')
        self.OPENAI_API_KEY: str = self._get_required('OPENAI_API_KEY')
        self.OPENAI_BASE_URL: str = self._get_optional('OPENAI_BASE_URL', 'https://api.openai.com/v1')

    def _get_required(self, key: str) -> str:
        """获取必需的环境变量"""
        value = os.getenv(key)
        if not value:
            raise EnvironmentError(f"缺少必需的环境变量: {key}")
        return value

    def _get_optional(self, key: str, default: Optional[str] = None) -> str:
        """获取可选的环境变量"""
        return os.getenv(key, default)


# 初始化配置实例
config = Config()
