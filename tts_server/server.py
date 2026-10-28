import io
import os
import threading
import wave

import numpy as np
from flask import Flask, Response, jsonify, request
from kokoro_onnx import Kokoro

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')

kokoro = Kokoro(
    os.path.join(MODEL_DIR, 'kokoro-v1.0.onnx'),
    os.path.join(MODEL_DIR, 'voices-v1.0.bin'),
)
# espeak-ng 音素化不是线程安全的,并发请求需要串行
lock = threading.Lock()

app = Flask(__name__)


@app.route('/health')
def health():
    return jsonify({'ok': True})


@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text 不能为空'}), 400

    with lock:
        samples, sample_rate = kokoro.create(
            text,
            voice=data.get('voice', 'af_bella'),
            speed=data.get('speed', 1.0),
            lang='en-us',
        )

    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return Response(buf.getvalue(), mimetype='audio/wav')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('TTS_PORT', '5100')), threaded=True)
