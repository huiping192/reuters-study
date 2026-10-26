"""用假 OBS WebSocket 服务器 + 假 OCR + 假查词服务器，把 main() 主循环真正跑一遍。"""
import base64
import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from PIL import Image, ImageDraw
from websockets.sync.server import serve

import obs_game_lookup


def png_data_uri(box):
    im = Image.new('RGB', (1280, 720), (20, 20, 20))
    if box:
        ImageDraw.Draw(im).rectangle(box, fill=(255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


class FakeOBS:
    def __init__(self):
        self.requests, self.text_updates = [], []
        self.frames_served = 0
        self.server = serve(self._handle, '127.0.0.1', 0)
        self.port = self.server.socket.getsockname()[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def _handle(self, ws):
        ws.send(json.dumps({'op': 0, 'd': {'obsWebSocketVersion': '5.5.0', 'rpcVersion': 1}}))
        ws.recv()
        ws.send(json.dumps({'op': 2, 'd': {'negotiatedRpcVersion': 1}}))
        for raw in ws:
            d = json.loads(raw)['d']
            data, rtype = d.get('requestData', {}), d['requestType']
            self.requests.append((rtype, data))
            body, ok = {}, True
            if rtype == 'GetSourceScreenshot':
                # 真 OBS 会拒绝 null 的可选字段
                ok = all(v is not None for v in data.values())
                self.frames_served += 1
                body = {'imageData': png_data_uri((100, 500, 1180, 700) if self.frames_served > 1 else None)}
            elif rtype == 'SetInputSettings':
                self.text_updates.append(data['inputSettings']['text'])
            ws.send(json.dumps({'op': 7, 'd': {
                'requestType': rtype, 'requestId': d['requestId'],
                'requestStatus': {'result': ok, 'code': 100 if ok else 400},
                'responseData': body}}))


class LookupHandler(BaseHTTPRequestHandler):
    posted = []

    def do_POST(self):
        LookupHandler.posted.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        body = json.dumps({'items': [{'surface': 'vowed', 'translation': 'n. 誓约\nvi. 起誓'}]}).encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class MainLoopTest(unittest.TestCase):
    def test_dialogue_appears_then_translation_written_to_obs(self):
        obs = FakeOBS()
        http = HTTPServer(('127.0.0.1', 0), LookupHandler)
        threading.Thread(target=http.serve_forever, daemon=True).start()

        clock = {'t': 0.0}
        ticks = {'n': 0}

        def fake_sleep(dt):
            clock['t'] += dt
            ticks['n'] += 1
            if ticks['n'] > 12:
                raise KeyboardInterrupt

        argv = ['--source', 'Switch', '--game', 'itest', '--port', str(obs.port),
                '--server', f'http://127.0.0.1:{http.server_port}', '--region', '0.05,0.65,0.95,1.0']
        with mock.patch.object(obs_game_lookup, 'windows_ocr', return_value='The magistrate\nvowed to leave.'), \
                mock.patch.object(obs_game_lookup.time, 'sleep', fake_sleep), \
                mock.patch.object(obs_game_lookup.time, 'monotonic', lambda: clock['t']):
            with self.assertRaises(KeyboardInterrupt):
                obs_game_lookup.main(argv)

        self.assertEqual(LookupHandler.posted, [{'text': 'The magistrate vowed to leave.', 'game': 'itest'}])
        self.assertEqual(obs.text_updates, ['vowed  n. 誓约'])
        self.assertTrue(any(r[0] == 'GetSourceScreenshot' for r in obs.requests))


if __name__ == '__main__':
    unittest.main()
