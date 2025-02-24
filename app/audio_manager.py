import os
import uuid
from replicate.client import Client

from config import config


def generate_audio(text: str, dir: str) -> str:
    """生成音频文件并返回相对路径"""
    replicate = Client(
        api_token=config.REPLICATE_API_TOKEN,
        headers={"User-Agent": "my-app/1.0"}
    )

    try:
        output = replicate.run(
            "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
            input={"text": text, "voice": "af_bella", "speed": 1}
        )

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(dir, filename)

        # 保存音频文件
        with open(filepath, 'wb') as f:
            f.write(output.read())

        return filename
    except Exception as e:
        print(f"TTS生成失败: {str(e)}")
        raise
