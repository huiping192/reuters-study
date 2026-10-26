import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from PIL import Image, ImageDraw

from lookup_core import (StableChange, clean_ocr_text, crop_region, format_items,
                         frame_signature, frames_differ, looks_like_dialogue, post_lookup)


def img(shade, box=None):
    im = Image.new('RGB', (320, 180), (shade,) * 3)
    if box:
        ImageDraw.Draw(im).rectangle(box, fill=(255, 255, 255))
    return im


class CoreTests(unittest.TestCase):
    def test_identical_frames_do_not_differ(self):
        s = frame_signature(img(10))
        self.assertFalse(frames_differ(s, frame_signature(img(10))))

    def test_text_box_appearing_differs(self):
        self.assertTrue(frames_differ(frame_signature(img(10)),
                                      frame_signature(img(10, (20, 120, 300, 170)))))

    def test_fires_once_after_settle(self):
        d = StableChange(settle=0.4)
        a, b = frame_signature(img(10)), frame_signature(img(10, (20, 120, 300, 170)))
        self.assertFalse(d.feed(a, 0.0))
        self.assertFalse(d.feed(b, 1.0))       # 刚变化
        self.assertFalse(d.feed(b, 1.2))       # 还没稳定够久
        self.assertTrue(d.feed(b, 1.5))        # 稳定，触发
        self.assertFalse(d.feed(b, 2.0))       # 不重复触发

    def test_typewriter_effect_keeps_waiting(self):
        d = StableChange(settle=0.4)
        fired = [d.feed(frame_signature(img(10, (20, 120, 20 + 30 * i, 170))), 0.1 * i)
                 for i in range(1, 8)]
        self.assertFalse(any(fired))

    def test_crop_region(self):
        self.assertEqual(crop_region(img(0), (0.0, 0.5, 0.5, 1.0)).size, (160, 90))
        self.assertEqual(crop_region(img(0), None).size, (320, 180))

    def test_clean_ocr_text(self):
        self.assertEqual(clean_ocr_text("I can't be-\nlieve  you\nare here."),
                         "I can't believe you are here.")

    def test_dialogue_filter(self):
        self.assertTrue(looks_like_dialogue("Hello there"))
        self.assertFalse(looks_like_dialogue("A 12 ▶"))

    def test_format_items(self):
        out = format_items([{'surface': 'vowed', 'translation': 'n. 誓约\nvi. 起誓'}])
        self.assertEqual(out, 'vowed  n. 誓约')

    def test_post_lookup_roundtrip(self):
        got = {}

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                got['path'] = self.path
                got['body'] = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                body = json.dumps({'items': []}).encode()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        srv = HTTPServer(('127.0.0.1', 0), H)
        threading.Thread(target=srv.handle_request, daemon=True).start()
        r = post_lookup(f'http://127.0.0.1:{srv.server_port}', 'Hi there', 'g')
        self.assertEqual(r, {'items': []})
        self.assertEqual(got['path'], '/api/game/lookup')
        self.assertEqual(got['body'], {'text': 'Hi there', 'game': 'g'})


if __name__ == '__main__':
    unittest.main()
