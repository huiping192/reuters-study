import os
import uuid
from replicate.client import Client

from config import config


def generate_audio(text: str, dir: str) -> str:
    """生成音频文件并返回相对路径"""
    print(f"开始生成音频，文本长度: {len(text)}")
    print(f"音频存储目录: {dir}")
    
    if not config.REPLICATE_API_TOKEN:
        print("错误: REPLICATE_API_TOKEN 未配置")
        raise ValueError("REPLICATE_API_TOKEN 未配置")

    replicate = Client(
        api_token=config.REPLICATE_API_TOKEN,
        headers={"User-Agent": "my-app/1.0"}
    )

    try:
        print("调用 Replicate API...")
        output = replicate.run(
            "jaaari/kokoro-82m:f559560eb822dc509045f3921a1921234918b91739db4bf3daab2169b71c7a13",
            input={"text": text, "voice": "af_bella", "speed": 1}
        )
        print("Replicate API 调用成功")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}.wav"
        filepath = os.path.join(dir, filename)
        print(f"准备保存音频文件: {filepath}")

        # 保存音频文件
        with open(filepath, 'wb') as f:
            f.write(output.read())
        print(f"音频文件保存成功: {filename}")

        return filename
    except Exception as e:
        print(f"TTS生成失败: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise
