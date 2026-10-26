"""从 OBS 取游戏画面 → Windows OCR → 服务器查生词 → 写回 OBS 文本源。

用法: python obs_game_lookup.py --source "Switch" --game "Zelda" \
        --server http://192.168.11.23:8007 --region 0.1,0.7,0.9,0.95
"""
import argparse
import base64
import io
import os
import sys
import time

import obsws_python as obs
from PIL import Image

from lookup_core import (EdgeTrigger, StableChange, clean_ocr_text, crop_region, format_items,
                         frame_signature, looks_like_dialogue, parse_hotkey, post_lookup,
                         prepare_for_ocr, text_digest)


def grab(client, source, width):
    # 包装方法会把可选字段序列化成 null，OBS 会按类型错误拒绝，所以只发必填项
    data = client.send('GetSourceScreenshot', {
        'sourceName': source, 'imageFormat': 'png', 'imageWidth': width}, raw=True)
    return Image.open(io.BytesIO(base64.b64decode(data['imageData'].split(',', 1)[1])))


def windows_ocr(img):
    import winocr
    return winocr.recognize_pil_sync(img, 'en')['text']


def obs_config_password():
    import json
    path = os.path.expandvars(r'%APPDATA%\obs-studio\plugin_config\obs-websocket\config.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)['server_password']


def connect(host, port, password):
    # 开机自启时 OBS 可能还没起来，等它而不是崩溃
    while True:
        try:
            return obs.ReqClient(host=host, port=port, password=password, timeout=5)
        except Exception as e:
            print(f'等待 OBS WebSocket ({type(e).__name__})...', flush=True)
            time.sleep(5)


def key_down(vk):
    import ctypes
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def show(client, text_source, shown):
    try:
        client.set_input_settings(text_source, {'text': shown}, True)
    except Exception as e:
        print(f'(写回 OBS 文本源 {text_source!r} 失败: {e})')


def lookup_once(client, args, region):
    frame = crop_region(grab(client, args.source, args.width), region)
    text = clean_ocr_text(windows_ocr(prepare_for_ocr(frame)))
    if not looks_like_dialogue(text):
        return text, '(没识别到对白)'
    try:
        shown = format_items(post_lookup(args.server, text, args.game)['items']) or '(没有生词)'
    except Exception as e:
        shown = f'(查词失败: {e})'
    return text, shown


def main(argv=None):
    # 日文 Windows 默认 cp932，打印中文释义会抛 UnicodeEncodeError
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    p = argparse.ArgumentParser()
    p.add_argument('--source', required=True, help='OBS 里的游戏画面源名称')
    p.add_argument('--text-source', default='LookupText', help='显示释义的文本源名称')
    p.add_argument('--game', default='')
    p.add_argument('--server', default='http://192.168.11.23:8007')
    p.add_argument('--region', help='对白框 left,top,right,bottom 比例，如 0.1,0.7,0.9,0.95')
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=4455)
    p.add_argument('--password', default='')
    p.add_argument('--width', type=int, default=1920, help='向 OBS 要的截图宽度，越大 OCR 越准')
    p.add_argument('--auto', action='store_true', help='画面稳定后自动查词，默认改为按热键查词')
    p.add_argument('--hotkey', default='F9', help='手动模式的热键，F1-F12 或单个字母/数字')
    p.add_argument('--clear-after', type=float, default=15, help='结果显示多少秒后清掉，0 为不清')
    p.add_argument('--interval', type=float, default=0.25)
    p.add_argument('--settle', type=float, default=0.4)
    p.add_argument('--once', action='store_true', help='只截一帧并打印 OCR 与查词结果，用于调 --region')
    args = p.parse_args(argv)

    password = args.password or obs_config_password()
    region = tuple(float(x) for x in args.region.split(',')) if args.region else None
    client = connect(args.host, args.port, password)
    detector, last_digest = StableChange(args.settle), None

    if args.once:
        frame = crop_region(grab(client, args.source, args.width), region)
        frame.save('once_crop.png')
        text = clean_ocr_text(windows_ocr(prepare_for_ocr(frame)))
        print('OCR:', repr(text))
        print('LOOKUP:', format_items(post_lookup(args.server, text, args.game + '-once')['items']))
        return

    if not args.auto:
        vk, trigger, shown_at = parse_hotkey(args.hotkey), EdgeTrigger(), None
        print(f'按 {args.hotkey.upper()} 查词，Ctrl+C 退出')
        while True:
            if trigger.pressed(key_down(vk)):
                text, shown = lookup_once(client, args, region)
                show(client, args.text_source, shown)
                shown_at = time.monotonic()
                print(text, '->', shown.replace('\n', ' | '))
            elif shown_at and args.clear_after and time.monotonic() - shown_at > args.clear_after:
                show(client, args.text_source, '')
                shown_at = None
            time.sleep(0.03)

    while True:
        frame = crop_region(grab(client, args.source, args.width), region)
        if detector.feed(frame_signature(frame), time.monotonic()):
            text = clean_ocr_text(windows_ocr(prepare_for_ocr(frame)))
            digest = text_digest(text)
            if looks_like_dialogue(text) and digest != last_digest:
                last_digest = digest
                try:
                    result = post_lookup(args.server, text, args.game)
                    shown = format_items(result['items'])
                except Exception as e:
                    shown = f'(查词失败: {e})'
                show(client, args.text_source, shown)
                print(text, '->', shown.replace('\n', ' | '))
        time.sleep(args.interval)


if __name__ == '__main__':
    main()
