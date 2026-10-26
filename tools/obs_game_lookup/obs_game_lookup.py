"""从 OBS 取游戏画面 → Windows OCR → 服务器查生词 → 写回 OBS 文本源。

用法: python obs_game_lookup.py --source "Switch" --game "Zelda" \
        --server http://192.168.11.23:8007 --region 0.1,0.7,0.9,0.95
"""
import argparse
import base64
import io
import time

import obsws_python as obs
from PIL import Image

from lookup_core import (StableChange, clean_ocr_text, crop_region, format_items,
                         frame_signature, looks_like_dialogue, post_lookup, text_digest)


def grab(client, source, width):
    # 包装方法会把可选字段序列化成 null，OBS 会按类型错误拒绝，所以只发必填项
    data = client.send('GetSourceScreenshot', {
        'sourceName': source, 'imageFormat': 'png', 'imageWidth': width}, raw=True)
    return Image.open(io.BytesIO(base64.b64decode(data['imageData'].split(',', 1)[1])))


def windows_ocr(img):
    import winocr
    return winocr.recognize_pil_sync(img, 'en')['text']


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, help='OBS 里的游戏画面源名称')
    p.add_argument('--text-source', default='LookupText', help='显示释义的文本源名称')
    p.add_argument('--game', default='')
    p.add_argument('--server', default='http://192.168.11.23:8007')
    p.add_argument('--region', help='对白框 left,top,right,bottom 比例，如 0.1,0.7,0.9,0.95')
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=4455)
    p.add_argument('--password', default='')
    p.add_argument('--interval', type=float, default=0.25)
    p.add_argument('--settle', type=float, default=0.4)
    p.add_argument('--once', action='store_true', help='只截一帧并打印 OCR 与查词结果，用于调 --region')
    args = p.parse_args(argv)

    region = tuple(float(x) for x in args.region.split(',')) if args.region else None
    client = obs.ReqClient(host=args.host, port=args.port, password=args.password, timeout=5)
    detector, last_digest = StableChange(args.settle), None

    if args.once:
        frame = crop_region(grab(client, args.source, 960), region)
        frame.save('once_crop.png')
        text = clean_ocr_text(windows_ocr(frame))
        print('OCR:', repr(text))
        print('LOOKUP:', format_items(post_lookup(args.server, text, args.game + '-once')['items']))
        return

    while True:
        frame = crop_region(grab(client, args.source, 960), region)
        if detector.feed(frame_signature(frame), time.monotonic()):
            text = clean_ocr_text(windows_ocr(frame))
            digest = text_digest(text)
            if looks_like_dialogue(text) and digest != last_digest:
                last_digest = digest
                try:
                    result = post_lookup(args.server, text, args.game)
                    shown = format_items(result['items'])
                except Exception as e:
                    shown = f'(查词失败: {e})'
                client.set_input_settings(args.text_source, {'text': shown}, True)
                print(text, '->', shown.replace('\n', ' | '))
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
