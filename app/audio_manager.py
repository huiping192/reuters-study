import os
import uuid

import requests

from config import config


def generate_audio(text: str, dir: str) -> str:
    """调用局域网内 Mac 上的 kokoro TTS 服务生成音频，返回文件名"""
    if not config.TTS_SERVER_URL:
        raise ValueError("TTS_SERVER_URL 未配置")

    # 连接超时设短：Mac 关机时尽快失败，前端好退回浏览器朗读
    response = requests.post(
        f"{config.TTS_SERVER_URL}/tts",
        json={"text": text, "voice": "af_bella", "speed": 1},
        timeout=(3, 120)
    )
    response.raise_for_status()

    filename = f"{uuid.uuid4().hex}.wav"
    with open(os.path.join(dir, filename), 'wb') as f:
        f.write(response.content)
    return filename
